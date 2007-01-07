# -*- coding: iso-8859-1 -*-
# vim: set ft=python ts=3 sw=3 expandtab:
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
#              C E D A R
#          S O L U T I O N S       "Software done right."
#           S O F T W A R E
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# Copyright (c) 2004-2007 Kenneth J. Pronovici.
# All rights reserved.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License,
# Version 2, as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# Copies of the GNU General Public License are available from
# the Free Software Foundation website, http://www.gnu.org/.
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# Author   : Kenneth J. Pronovici <pronovic@ieee.org>
# Language : Python (>= 2.3)
# Project  : Cedar Backup, release 2
# Revision : $Id$
# Purpose  : Provides functionality related to CD writer devices.
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

########################################################################
# Module documentation
########################################################################

"""
Provides functionality related to CD writer devices.

@sort: MediaDefinition, MediaCapacity, CdWriter, IsoImage,
       MEDIA_CDRW_74, MEDIA_CDR_74, MEDIA_CDRW_80, MEDIA_CDR_80

@var MEDIA_CDRW_74: Constant representing 74-minute CD-RW media.
@var MEDIA_CDR_74: Constant representing 74-minute CD-R media.
@var MEDIA_CDRW_80: Constant representing 80-minute CD-RW media.
@var MEDIA_CDR_80: Constant representing 80-minute CD-R media.

@author: Kenneth J. Pronovici <pronovic@ieee.org>
"""

########################################################################
# Imported modules
########################################################################

# System modules
import os
import re
import logging
import tempfile

# Cedar Backup modules
from CedarBackup2.filesystem import FilesystemList
from CedarBackup2.util import resolveCommand, executeCommand
from CedarBackup2.util import convertSize, displayBytes, encodePath
from CedarBackup2.util import UNIT_SECTORS, UNIT_BYTES, UNIT_KBYTES, UNIT_MBYTES
from CedarBackup2.util import validateDevice, validateScsiId, validateDriveSpeed


########################################################################
# Module-wide constants and variables
########################################################################

logger = logging.getLogger("CedarBackup2.log.writers.cdwriter")

MEDIA_CDRW_74  = 1
MEDIA_CDR_74   = 2
MEDIA_CDRW_80  = 3
MEDIA_CDR_80   = 4

CDRECORD_COMMAND = [ "cdrecord", ]
EJECT_COMMAND    = [ "eject", ]
MKISOFS_COMMAND  = [ "mkisofs", ]


########################################################################
# MediaDefinition class definition
########################################################################

class MediaDefinition(object):

   """
   Class encapsulating information about CD media definitions.

   The following media types are accepted:

      - C{MEDIA_CDR_74}: 74-minute CD-R media (650 MB capacity)
      - C{MEDIA_CDRW_74}: 74-minute CD-RW media (650 MB capacity)
      - C{MEDIA_CDR_80}: 80-minute CD-R media (700 MB capacity)
      - C{MEDIA_CDRW_80}: 80-minute CD-RW media (700 MB capacity)

   Note that all of the capacities associated with a media definition are in
   terms of ISO sectors (C{util.ISO_SECTOR_SIZE)}.

   @sort: __init__, mediaType, rewritable, initialLeadIn, leadIn, capacity
   """

   def __init__(self, mediaType):
      """
      Creates a media definition for the indicated media type.
      @param mediaType: Type of the media, as discussed above.
      @raise ValueError: If the media type is unknown or unsupported.      
      """
      self._mediaType = None
      self._rewritable = False
      self._initialLeadIn = 0.
      self._leadIn = 0.0
      self._capacity = 0.0
      self._setValues(mediaType)

   def _setValues(self, mediaType):
      """
      Sets values based on media type.
      @param mediaType: Type of the media, as discussed above.
      @raise ValueError: If the media type is unknown or unsupported.      
      """
      if mediaType not in [MEDIA_CDR_74, MEDIA_CDRW_74, MEDIA_CDR_80, MEDIA_CDRW_80]:
         raise ValueError("Invalid media type %d." % mediaType)
      self._mediaType = mediaType
      self._initialLeadIn = 11400.0   # per cdrecord's documentation
      self._leadIn = 6900.0           # per cdrecord's documentation
      if self._mediaType == MEDIA_CDR_74:
         self._rewritable = False
         self._capacity = convertSize(650.0, UNIT_MBYTES, UNIT_SECTORS)
      elif self._mediaType == MEDIA_CDRW_74:
         self._rewritable = True
         self._capacity = convertSize(650.0, UNIT_MBYTES, UNIT_SECTORS)
      elif self._mediaType == MEDIA_CDR_80:
         self._rewritable = False
         self._capacity = convertSize(700.0, UNIT_MBYTES, UNIT_SECTORS)
      elif self._mediaType == MEDIA_CDRW_80:
         self._rewritable = True
         self._capacity = convertSize(700.0, UNIT_MBYTES, UNIT_SECTORS)

   def _getMediaType(self):
      """
      Property target used to get the media type value.
      """
      return self._mediaType

   def _getRewritable(self):
      """
      Property target used to get the rewritable flag value.
      """
      return self._rewritable

   def _getInitialLeadIn(self):
      """
      Property target used to get the initial lead-in value.
      """
      return self._initialLeadIn

   def _getLeadIn(self):
      """
      Property target used to get the lead-in value.
      """
      return self._leadIn

   def _getCapacity(self):
      """
      Property target used to get the capacity value.
      """
      return self._capacity

   mediaType = property(_getMediaType, None, None, doc="Configured media type.")
   rewritable = property(_getRewritable, None, None, doc="Boolean indicating whether the media is rewritable.")
   initialLeadIn = property(_getInitialLeadIn, None, None, doc="Initial lead-in required for first image written to media.")
   leadIn = property(_getLeadIn, None, None, doc="Lead-in required on successive images written to media.")
   capacity = property(_getCapacity, None, None, doc="Total capacity of the media before any required lead-in.")


########################################################################
# MediaCapacity class definition
########################################################################

class MediaCapacity(object):

   """
   Class encapsulating information about CD media capacity.

   Space used includes the required media lead-in (unless the disk is unused).
   Space available attempts to provide a picture of how many bytes are
   available for data storage, including any required lead-in.  

   The boundaries value is either C{None} (if multisession discs are not
   supported or if the disc has no boundaries) or in exactly the form provided
   by C{cdrecord -msinfo}.  It can be passed as-is to the C{IsoImage} class.

   @sort: __init__, bytesUsed, bytesAvailable, boundaries
   """

   def __init__(self, bytesUsed, bytesAvailable, boundaries):
      """
      Initializes a capacity object.
      @raise IndexError: If the boundaries tuple does not have enough elements.
      @raise ValueError: If the boundaries values are not integers.
      @raise ValueError: If the bytes used and available values are not floats.
      """
      self._bytesUsed = float(bytesUsed)
      self._bytesAvailable = float(bytesAvailable)
      if boundaries is None:
         self._boundaries = None
      else:
         self._boundaries = (int(boundaries[0]), int(boundaries[1]))

   def _getBytesUsed(self):
      """
      Property target used to get the bytes-used value.
      """
      return self._bytesUsed

   def _getBytesAvailable(self):
      """
      Property target available to get the bytes-available value.
      """
      return self._bytesAvailable

   def _getBoundaries(self):
      """
      Property target available to get the boundaries tuple.
      """
      return self._boundaries

   bytesUsed = property(_getBytesUsed, None, None, doc="Space used on disc, in bytes.")
   bytesAvailable = property(_getBytesAvailable, None, None, doc="Space available on disc, in bytes.")
   boundaries = property(_getBoundaries, None, None, doc="Session disc boundaries, in terms of ISO sectors.")


########################################################################
# _ImageProperties class definition
########################################################################

class _ImageProperties(object):
   """
   Simple value object to hold image properties for C{DvdWriter}.
   """
   def __init__(self):
      self.newDisc = False
      self.tmpdir = None
      self.capacity = None
      self.image = None


########################################################################
# CdWriter class definition
########################################################################

class CdWriter(object):

   ######################
   # Class documentation
   ######################

   """
   Class representing a device that knows how to write CD media.

   Summary
   =======

      This is a class representing a device that knows how to write CD media.  It
      provides common operations for the device, such as ejecting the media,
      writing an ISO image to the media, or checking for the current media
      capacity.  It also provides a place to store device attributes, such as
      whether the device supports writing multisession discs, etc.

      This class is implemented in terms of the C{eject} and C{cdrecord}
      programs, both of which should be available on most UN*X platforms.

   Image Writer Interface
   ======================

      The following methods make up the "image writer" interface shared
      with other kinds of writers (such as DVD writers)::

         __init__
         initializeImage()
         addImageEntry()
         writeImage()

      Only these methods will be used by other Cedar Backup functionality
      that expects a compatible image writer.

   Media Types
   ===========

      This class knows how to write to two different kinds of media, represented
      by the following constants:

         - C{MEDIA_CDR_74}: 74-minute CD-R media (650 MB capacity)
         - C{MEDIA_CDRW_74}: 74-minute CD-RW media (650 MB capacity)
         - C{MEDIA_CDR_80}: 80-minute CD-R media (700 MB capacity)
         - C{MEDIA_CDRW_80}: 80-minute CD-RW media (700 MB capacity)

      Most hardware can read and write both 74-minute and 80-minute CD-R and
      CD-RW media.  Some older drives may only be able to write CD-R media.
      The difference between the two is that CD-RW media can be rewritten
      (erased), while CD-R media cannot be.  

      I do not support any other configurations for a couple of reasons.  The
      first is that I've never tested any other kind of media.  The second is
      that anything other than 74 or 80 minute is apparently non-standard.

   Device Attributes vs. Media Attributes
   ======================================

      A given writer instance has two different kinds of attributes associated
      with it, which I call device attributes and media attributes.  Device
      attributes are things which can be determined without looking at the
      media, such as whether the drive supports writing multisession disks or
      has a tray.  Media attributes are attributes which vary depending on the
      state of the media, such as the remaining capacity on a disc.  In
      general, device attributes are available via instance variables and are
      constant over the life of an object, while media attributes can be
      retrieved through method calls.

   Talking to Hardware
   ===================

      This class needs to talk to CD writer hardware in two different ways:
      through cdrecord to actually write to the media, and through the
      filesystem to do things like open and close the tray.

      Historically, CdWriter has interacted with cdrecord using the scsiId
      attribute, and with most other utilities using the device attribute.
      This changed somewhat in Cedar Backup 2.9.0.

      When Cedar Backup was first written, the only way to interact with
      cdrecord was by using a SCSI device id.  IDE devices were mapped to
      pseudo-SCSI devices through the kernel.  Later, extended SCSI "methods"
      arrived, and it became common to see C{ATA:1,0,0} or C{ATAPI:0,0,0} as a
      way to address IDE hardware.  By late 2006, C{ATA} and C{ATAPI} had
      apparently been deprecated in favor of just addressing the IDE device
      directly by name, i.e. C{/dev/cdrw}.

      Because of this latest development, it no longer makes sense to require a
      CdWriter to be created with a SCSI id -- there might not be one.  So, the
      passed-in SCSI id is now optional.  Also, there is now a hardwareId
      attribute.  This attribute is filled in with either the SCSI id (if
      provided) or the device (otherwise).  The hardware id is the value that
      will be passed to cdrecord in the C{dev=} argument.

   Testing
   =======

      It's rather difficult to test this code in an automated fashion, even if
      you have access to a physical CD writer drive.  It's even more difficult
      to test it if you are running on some build daemon (think of a Debian
      autobuilder) which can't be expected to have any hardware or any media
      that you could write to.

      Because of this, much of the implementation below is in terms of static
      methods that are supposed to take defined actions based on their
      arguments.  Public methods are then implemented in terms of a series of
      calls to simplistic static methods.  This way, we can test as much as
      possible of the functionality via testing the static methods, while
      hoping that if the static methods are called appropriately, things will
      work properly.  It's not perfect, but it's much better than no testing at
      all.

   @sort: __init__, isRewritable, _retrieveProperties, retrieveCapacity, _getBoundaries,
          _calculateCapacity, openTray, closeTray, refreshMedia, writeImage,
          _blankMedia, _parsePropertiesOutput, _parseBoundariesOutput, 
          _buildOpenTrayArgs, _buildCloseTrayArgs, _buildPropertiesArgs, 
          _buildBoundariesArgs, _buildBlankArgs, _buildWriteArgs,
          device, scsiId, hardwareId, driveSpeed, media, deviceType, deviceVendor, 
          deviceId, deviceBufferSize, deviceSupportsMulti, deviceHasTray, deviceCanEject,
          initializeImage, addImageEntry, writeImage
   """

   ##############
   # Constructor
   ##############

   def __init__(self, device, scsiId=None, driveSpeed=None, mediaType=MEDIA_CDRW_74, unittest=False):
      """
      Initializes a CD writer object.

      The current user must have write access to the device at the time the
      object is instantiated, or an exception will be thrown.  However, no
      media-related validation is done, and in fact there is no need for any
      media to be in the drive until one of the other media attribute-related
      methods is called.

      The various instance variables such as C{deviceType}, C{deviceVendor},
      etc. might be C{None}, if we're unable to parse this specific information
      from the C{cdrecord} output.  This information is just for reference.

      The SCSI id is optional, but the device path is required.  If the SCSI id
      is passed in, then the hardware id attribute will be taken from the SCSI
      id.  Otherwise, the hardware id will be taken from the device.

      @note: The C{unittest} parameter should never be set to C{True}
      outside of Cedar Backup code.  It is intended for use in unit testing
      Cedar Backup internals and has no other sensible purpose.

      @param device: Filesystem device associated with this writer.
      @type device: Absolute path to a filesystem device, i.e. C{/dev/cdrw}

      @param scsiId: SCSI id for the device (optional).
      @type scsiId: If provided, SCSI id in the form C{[<method>:]scsibus,target,lun}

      @param driveSpeed: Speed at which the drive writes.
      @type driveSpeed: Use C{2} for 2x device, etc. or C{None} to use device default.

      @param mediaType: Type of the media that is assumed to be in the drive.
      @type mediaType: One of the valid media type as discussed above.

      @param unittest: Turns off certain validations, for use in unit testing.
      @type unittest: Boolean true/false

      @raise ValueError: If the device is not valid for some reason.
      @raise ValueError: If the SCSI id is not in a valid form.
      @raise ValueError: If the drive speed is not an integer >= 1.
      @raise IOError: If device properties could not be read for some reason.
      """
      self._image = None  # optionally filled in by initializeImage()
      self._device = validateDevice(device, unittest)
      self._scsiId = validateScsiId(scsiId)
      self._driveSpeed = validateDriveSpeed(driveSpeed)
      self._media = MediaDefinition(mediaType)
      if not unittest:
         (self._deviceType,
          self._deviceVendor,
          self._deviceId,
          self._deviceBufferSize,
          self._deviceSupportsMulti,
          self._deviceHasTray,
          self._deviceCanEject) = self._retrieveProperties()


   #############
   # Properties
   #############

   def _getDevice(self):
      """
      Property target used to get the device value.
      """
      return self._device

   def _getScsiId(self):
      """
      Property target used to get the SCSI id value.
      """
      return self._scsiId

   def _getHardwareId(self):
      """
      Property target used to get the hardware id value.
      """
      if self._scsiId is None:
         return self._device
      return self._scsiId

   def _getDriveSpeed(self):
      """
      Property target used to get the drive speed.
      """
      return self._driveSpeed

   def _getMedia(self):
      """
      Property target used to get the media description.
      """
      return self._media

   def _getDeviceType(self):
      """
      Property target used to get the device type.
      """
      return self._deviceType

   def _getDeviceVendor(self):
      """
      Property target used to get the device vendor.
      """
      return self._deviceVendor

   def _getDeviceId(self):
      """
      Property target used to get the device id.
      """
      return self._deviceId

   def _getDeviceBufferSize(self):
      """
      Property target used to get the device buffer size.
      """
      return self._deviceBufferSize

   def _getDeviceSupportsMulti(self):
      """
      Property target used to get the device-support-multi flag.
      """
      return self._deviceSupportsMulti

   def _getDeviceHasTray(self):
      """
      Property target used to get the device-has-tray flag.
      """
      return self._deviceHasTray

   def _getDeviceCanEject(self):
      """
      Property target used to get the device-can-eject flag.
      """
      return self._deviceCanEject

   device = property(_getDevice, None, None, doc="Filesystem device name for this writer.")
   scsiId = property(_getScsiId, None, None, doc="SCSI id for the device, in the form C{[<method>:]scsibus,target,lun}.")
   hardwareId = property(_getHardwareId, None, None, doc="Hardware id for this writer, either SCSI id or device path.");
   driveSpeed = property(_getDriveSpeed, None, None, doc="Speed at which the drive writes.")
   media = property(_getMedia, None, None, doc="Definition of media that is expected to be in the device.")
   deviceType = property(_getDeviceType, None, None, doc="Type of the device, as returned from C{cdrecord -prcap}.")
   deviceVendor = property(_getDeviceVendor, None, None, doc="Vendor of the device, as returned from C{cdrecord -prcap}.")
   deviceId = property(_getDeviceId, None, None, doc="Device identification, as returned from C{cdrecord -prcap}.")
   deviceBufferSize = property(_getDeviceBufferSize, None, None, doc="Size of the device's write buffer, in bytes.")
   deviceSupportsMulti = property(_getDeviceSupportsMulti, None, None, doc="Indicates whether device supports multisession discs.")
   deviceHasTray = property(_getDeviceHasTray, None, None, doc="Indicates whether the device has a media tray.")
   deviceCanEject = property(_getDeviceCanEject, None, None, doc="Indicates whether the device supports ejecting its media.")


   #################################################
   # Methods related to device and media attributes
   #################################################

   def isRewritable(self):
      """Indicates whether the media is rewritable per configuration."""
      return self._media.rewritable

   def _retrieveProperties(self):
      """
      Retrieves properties for a device from C{cdrecord}.

      The results are returned as a tuple of the object device attributes as
      returned from L{_parsePropertiesOutput}: C{(deviceType, deviceVendor,
      deviceId, deviceBufferSize, deviceSupportsMulti, deviceHasTray,
      deviceCanEject)}.

      @return: Results tuple as described above.
      @raise IOError: If there is a problem talking to the device.
      """
      args = CdWriter._buildPropertiesArgs(self.hardwareId)
      command = resolveCommand(CDRECORD_COMMAND)
      (result, output) = executeCommand(command, args, returnOutput=True, ignoreStderr=True)
      if result != 0:
         raise IOError("Error (%d) executing cdrecord command to get properties." % result)
      return CdWriter._parsePropertiesOutput(output)
      
   def retrieveCapacity(self, entireDisc=False, useMulti=True):
      """
      Retrieves capacity for the current media in terms of a C{MediaCapacity}
      object.

      If C{entireDisc} is passed in as C{True} the capacity will be for the
      entire disc, as if it were to be rewritten from scratch.  If the drive
      does not support writing multisession discs or if C{useMulti} is passed
      in as C{False}, the capacity will also be as if the disc were to be
      rewritten from scratch, but the indicated boundaries value will be
      C{None}.  The same will happen if the disc cannot be read for some
      reason.  Otherwise, the capacity (including the boundaries) will
      represent whatever space remains on the disc to be filled by future
      sessions.

      @param entireDisc: Indicates whether to return capacity for entire disc.
      @type entireDisc: Boolean true/false

      @param useMulti: Indicates whether a multisession disc should be assumed, if possible.
      @type useMulti: Boolean true/false

      @return: C{MediaCapacity} object describing the capacity of the media.
      @raise IOError: If the media could not be read for some reason.
      """
      boundaries = self._getBoundaries(entireDisc, useMulti)
      return CdWriter._calculateCapacity(self._media, boundaries)

   def _getBoundaries(self, entireDisc=False, useMulti=True):
      """
      Gets the ISO boundaries for the media.

      If C{entireDisc} is passed in as C{True} the boundaries will be C{None},
      as if the disc were to be rewritten from scratch.  If the drive does not
      support writing multisession discs, the returned value will be C{None}.
      The same will happen if the disc can't be read for some reason.
      Otherwise, the returned value will be represent the boundaries of the
      disc's current contents.

      The results are returned as a tuple of (lower, upper) as needed by the
      C{IsoImage} class.  Note that these values are in terms of ISO sectors,
      not bytes.  Clients should generally consider the boundaries value
      opaque, however.

      @param entireDisc: Indicates whether to return capacity for entire disc.
      @type entireDisc: Boolean true/false

      @param useMulti: Indicates whether a multisession disc should be assumed, if possible.
      @type useMulti: Boolean true/false

      @return: Boundaries tuple or C{None}, as described above.
      @raise IOError: If the media could not be read for some reason.
      """
      if not self._deviceSupportsMulti:
         logger.debug("Device does not support multisession discs; returning boundaries None.")
         return None
      elif not useMulti:
         logger.debug("Use multisession flag is False; returning boundaries None.")
         return None
      elif entireDisc:
         logger.debug("Entire disc flag is True; returning boundaries None.")
         return None
      else:
         args = CdWriter._buildBoundariesArgs(self.hardwareId)
         command = resolveCommand(CDRECORD_COMMAND)
         (result, output) = executeCommand(command, args, returnOutput=True, ignoreStderr=True)
         if result != 0:
            raise IOError("Error (%d) executing cdrecord command to get capacity." % result)
         boundaries = CdWriter._parseBoundariesOutput(output)
         if boundaries is None:
            logger.debug("Returning disc boundaries: None")
         else:
            logger.debug("Returning disc boundaries: (%d, %d)" % (boundaries[0], boundaries[1]))
         return boundaries

   def _calculateCapacity(media, boundaries):
      """
      Calculates capacity for the media in terms of boundaries.

      If C{boundaries} is C{None} or the lower bound is 0 (zero), then the
      capacity will be for the entire disc minus the initial lead in.
      Otherwise, capacity will be as if the caller wanted to add an additional
      session to the end of the existing data on the disc.

      @param media: MediaDescription object describing the media capacity.
      @param boundaries: Session boundaries as returned from L{_getBoundaries}.

      @return: C{MediaCapacity} object describing the capacity of the media.
      """
      if boundaries is None or boundaries[1] == 0:
         logger.debug("Capacity calculations are based on a complete disc rewrite.")
         sectorsAvailable = media.capacity - media.initialLeadIn
         if sectorsAvailable < 0: sectorsAvailable = 0
         bytesUsed = 0
         bytesAvailable = convertSize(sectorsAvailable, UNIT_SECTORS, UNIT_BYTES)
      else:
         logger.debug("Capacity calculations are based on a new ISO session.")
         sectorsAvailable = media.capacity - boundaries[1] - media.leadIn
         if sectorsAvailable < 0: sectorsAvailable = 0
         bytesUsed = convertSize(boundaries[1], UNIT_SECTORS, UNIT_BYTES)
         bytesAvailable = convertSize(sectorsAvailable, UNIT_SECTORS, UNIT_BYTES)
      logger.debug("Used [%s], available [%s]." % (displayBytes(bytesUsed), displayBytes(bytesAvailable)))
      return MediaCapacity(bytesUsed, bytesAvailable, boundaries)
   _calculateCapacity = staticmethod(_calculateCapacity)


   #######################################################
   # Methods used for working with the internal ISO image
   #######################################################

   def initializeImage(self, newDisc, tmpdir):
      """
      Initializes the writer's associated ISO image.

      This method initializes the C{image} instance variable so that the caller
      can use the C{addImageEntry} method.  Once entries have been added, the
      C{writeImage} method can be called with no arguments.

      @param newDisc: Indicates whether the disc should be re-initialized
      @type newDisc: Boolean true/false.

      @param tmpdir: Temporary directory to use if needed
      @type tmpdir: String representing a directory path on disk
      """
      self._image = _ImageProperties()
      self._image.newDisc = newDisc
      self._image.tmpdir = encodePath(tmpdir)
      self._image.capacity = self.retrieveCapacity(entireDisc=newDisc)
      logger.debug("Media capacity: %s" % displayBytes(self._image.capacity.bytesAvailable))
      self._image.image = IsoImage(self.device, self._image.capacity.boundaries)  

   def addImageEntry(self, path, graftPoint):
      """
      Adds a filepath entry to the writer's associated ISO image.

      Underneath, this calls L{IsoImage.addEntry} with the C{override=False}
      and C{contentsOnly=True} arguments.  Using these arguments, the contents
      of the passed-in path -- but not the path itself -- will be added to the
      ISO image.

      See the documentation by L{IsoImage.addEntry} for more information on how
      a graft point path is defined.

      @note: Before calling this method, you must call L{initializeImage}.

      @param path: File or directory to be added to the image
      @type path: String representing a path on disk

      @param graftPoint: Graft point to be used when adding this entry
      @type graftPoint: String representing a graft point path, as described above

      @raise ValueError: If initializeImage() was not previously called
      """
      if self._image is None:
         raise ValueError("Must call initializeImage() before using this method.")
      self._image.image.addEntry(path, graftPoint, override=False, contentsOnly=True)


   ######################################
   # Methods which expose device actions
   ######################################

   def openTray(self):
      """
      Opens the device's tray and leaves it open.

      This only works if the device has a tray and supports ejecting its media.
      We have no way to know if the tray is currently open or closed, so we
      just send the appropriate command and hope for the best.  If the device
      does not have a tray or does not support ejecting its media, then we do
      nothing.

      @raise IOError: If there is an error talking to the device.
      """
      if self._deviceHasTray and self._deviceCanEject:
         args = CdWriter._buildOpenTrayArgs(self._device)
         command = resolveCommand(EJECT_COMMAND)
         result = executeCommand(command, args)[0]
         if result != 0:
            raise IOError("Error (%d) executing eject command to open tray." % result)

   def closeTray(self):
      """
      Closes the device's tray.

      This only works if the device has a tray and supports ejecting its media.
      We have no way to know if the tray is currently open or closed, so we
      just send the appropriate command and hope for the best.  If the device
      does not have a tray or does not support ejecting its media, then we do
      nothing.

      @raise IOError: If there is an error talking to the device.
      """
      if self._deviceHasTray and self._deviceCanEject:
         args = CdWriter._buildCloseTrayArgs(self._device)
         command = resolveCommand(EJECT_COMMAND)
         result = executeCommand(command, args)[0]
         if result != 0:
            raise IOError("Error (%d) executing eject command to close tray." % result)

   def refreshMedia(self):
      """
      Opens and then immediately closes the device's tray, to refresh the 
      device's idea of the media.

      Sometimes, a device gets confused about the state of its media.  Often,
      all it takes to solve the problem is to eject the media and then
      immediately reload it.  

      This only works if the device has a tray and supports ejecting its media.
      We have no way to know if the tray is currently open or closed, so we
      just send the appropriate command and hope for the best.  If the device
      does not have a tray or does not support ejecting its media, then we do
      nothing.

      @raise IOError: If there is an error talking to the device.
      """
      self.openTray()
      self.closeTray()

   def writeImage(self, imagePath=None, newDisc=False, writeMulti=True):
      """
      Writes an ISO image to the media in the device.  

      If C{newDisc} is passed in as C{True}, we assume that the entire disc
      will be overwritten, and the media will be blanked before writing it if
      possible (i.e. if the media is rewritable).  

      If C{writeMulti} is passed in as C{True}, then a multisession disc will
      be written if possible (i.e. if the drive supports writing multisession
      discs).

      if C{imagePath} is passed in as C{None}, then the existing image
      configured with C{initializeImage} will be used.  Under these
      circumstances, the passed-in C{newDisc} flag will be ignored.

      By default, we assume that the disc can be written multisession and that
      we should append to the current contents of the disc.  In any case, the
      ISO image must be generated appropriately (i.e. must take into account
      any existing session boundaries, etc.)

      @param imagePath: Path to an ISO image on disk, or C{None} to use writer's image
      @type imagePath: String representing a path on disk

      @param newDisc: Indicates whether the entire disc will overwritten.
      @type newDisc: Boolean true/false.

      @param writeMulti: Indicates whether a multisession disc should be written, if possible.
      @type writeMulti: Boolean true/false

      @raise ValueError: If the image path is not absolute.
      @raise ValueError: If some path cannot be encoded properly.
      @raise IOError: If the media could not be written to for some reason.
      @raise ValueError: If no image is passed in and initializeImage() was not previously called
      """
      if imagePath is None:
         if self._image is None:
            raise ValueError("Must call initializeImage() before using this method with no image path.")
         try:
            imagePath = self._createImage()
            self._writeImage(imagePath, writeMulti, self._image.newDisc)
         finally:
            if imagePath is not None and os.path.exists(imagePath):
               try: os.unlink(imagePath)
               except: pass
      else:
         imagePath = encodePath(imagePath)
         if not os.path.isabs(imagePath):
            raise ValueError("Image path must be absolute.")
         self._writeImage(imagePath, writeMulti, newDisc)

   def _createImage(self):
      """
      Creates an ISO image based on configuration in self._image.
      @return: Path to the newly-created ISO image on disk.
      @raise IOError: If there is an error writing the image to disk.
      @raise ValueError: If there are no filesystem entries in the image
      @raise ValueError: If a path cannot be encoded properly.
      """
      path = None
      size = self._image.image.getEstimatedSize()
      logger.info("Image size will be %s." % displayBytes(size))
      available = self._image.capacity.bytesAvailable
      if size > available:
         logger.error("Image [%s] does not fit in available capacity [%s]." % (displayBytes(size), displayBytes(available)))
         raise IOError("Media does not contain enough capacity to store image.")
      try:
         (handle, path) = tempfile.mkstemp(dir=self._image.tmpdir)
         try: os.close(handle)
         except: pass
         self._image.image.writeImage(path)
         logger.debug("Completed creating image [%s]." % path)
         return path
      except Exception, e:
         if path is not None and os.path.exists(path):
            try: os.unlink(path)
            except: pass
         raise e

   def _writeImage(self, imagePath, writeMulti, newDisc):
      """
      Write an ISO image to disc using cdrecord.
      The disc is blanked first if C{newDisc} is C{True}.
      @param imagePath: Path to an ISO image on disk
      @param writeMulti: Indicates whether a multisession disc should be written, if possible.
      @param newDisc: Indicates whether the entire disc will overwritten.
      """
      if newDisc: 
         self._blankMedia()
      args = CdWriter._buildWriteArgs(self.hardwareId, imagePath, self._driveSpeed, writeMulti and self._deviceSupportsMulti)
      command = resolveCommand(CDRECORD_COMMAND)
      result = executeCommand(command, args)[0]
      if result != 0:
         raise IOError("Error (%d) executing command to write disc." % result)
      self.refreshMedia()

   def _blankMedia(self):
      """
      Blanks the media in the device, if the media is rewritable.
      @raise IOError: If the media could not be written to for some reason.
      """
      if self.isRewritable():
         args = CdWriter._buildBlankArgs(self.hardwareId)
         command = resolveCommand(CDRECORD_COMMAND)
         result = executeCommand(command, args)[0]
         if result != 0:
            raise IOError("Error (%d) executing command to blank disc." % result)
         self.refreshMedia()

      
   #######################################
   # Methods used to parse command output
   #######################################

   def _parsePropertiesOutput(output):
      """
      Parses the output from a C{cdrecord} properties command.

      The C{output} parameter should be a list of strings as returned from
      C{executeCommand} for a C{cdrecord} command with arguments as from
      C{_buildPropertiesArgs}.  The list of strings will be parsed to yield
      information about the properties of the device.

      The output is expected to be a huge long list of strings.  Unfortunately,
      the strings aren't in a completely regular format.  However, the format
      of individual lines seems to be regular enough that we can look for
      specific values.  Two kinds of parsing take place: one kind of parsing
      picks out out specific values like the device id, device vendor, etc.
      The other kind of parsing just sets a boolean flag C{True} if a matching
      line is found.  All of the parsing is done with regular expressions.

      Right now, pretty much nothing in the output is required and we should
      parse an empty document successfully (albeit resulting in a device that
      can't eject, doesn't have a tray and doesnt't support multisession
      discs).   I had briefly considered erroring out if certain lines weren't
      found or couldn't be parsed, but that seems like a bad idea given that
      most of the information is just for reference.  

      The results are returned as a tuple of the object device attributes:
      C{(deviceType, deviceVendor, deviceId, deviceBufferSize,
      deviceSupportsMulti, deviceHasTray, deviceCanEject)}.

      @param output: Output from a C{cdrecord -prcap} command.

      @return: Results tuple as described above.
      @raise IOError: If there is problem parsing the output.
      """
      deviceType = None
      deviceVendor = None
      deviceId = None
      deviceBufferSize = None
      deviceSupportsMulti = False
      deviceHasTray = False
      deviceCanEject = False
      typePattern   = re.compile(r"(^Device type\s*:\s*)(.*)(\s*)(.*$)")
      vendorPattern = re.compile(r"(^Vendor_info\s*:\s*'\s*)(.*?)(\s*')(.*$)")
      idPattern     = re.compile(r"(^Identifikation\s*:\s*'\s*)(.*?)(\s*')(.*$)")
      bufferPattern = re.compile(r"(^\s*Buffer size in KB:\s*)(.*?)(\s*$)")
      multiPattern  = re.compile(r"^\s*Does read multi-session.*$")
      trayPattern   = re.compile(r"^\s*Loading mechanism type: tray.*$")
      ejectPattern  = re.compile(r"^\s*Does support ejection.*$")
      for line in output:
         if typePattern.search(line):
            deviceType =  typePattern.search(line).group(2)
            logger.info("Device type is [%s]." % deviceType)
         elif vendorPattern.search(line):
            deviceVendor = vendorPattern.search(line).group(2)
            logger.info("Device vendor is [%s]." % deviceVendor)
         elif idPattern.search(line):
            deviceId = idPattern.search(line).group(2)
            logger.info("Device id is [%s]." % deviceId)
         elif bufferPattern.search(line):
            try:
               sectors = int(bufferPattern.search(line).group(2))
               deviceBufferSize = convertSize(sectors, UNIT_KBYTES, UNIT_BYTES)
               logger.info("Device buffer size is [%d] bytes." % deviceBufferSize)
            except TypeError: pass
         elif multiPattern.search(line):
            deviceSupportsMulti = True
            logger.info("Device does support multisession discs.")
         elif trayPattern.search(line):
            deviceHasTray = True
            logger.info("Device has a tray.")
         elif ejectPattern.search(line):
            deviceCanEject = True
            logger.info("Device can eject its media.")
      return (deviceType, deviceVendor, deviceId, deviceBufferSize, deviceSupportsMulti, deviceHasTray, deviceCanEject)
   _parsePropertiesOutput = staticmethod(_parsePropertiesOutput)

   def _parseBoundariesOutput(output):
      """
      Parses the output from a C{cdrecord} capacity command.

      The C{output} parameter should be a list of strings as returned from
      C{executeCommand} for a C{cdrecord} command with arguments as from
      C{_buildBoundaryArgs}.  The list of strings will be parsed to yield
      information about the capacity of the media in the device.

      Basically, we expect the list of strings to include just one line, a pair
      of values.  There isn't supposed to be whitespace, but we allow it anyway
      in the regular expression.  Any lines below the one line we parse are
      completely ignored.  It would be a good idea to ignore C{stderr} when
      executing the C{cdrecord} command that generates output for this method,
      because sometimes C{cdrecord} spits out kernel warnings about the actual
      output.

      The results are returned as a tuple of (lower, upper) as needed by the
      C{IsoImage} class.  Note that these values are in terms of ISO sectors,
      not bytes.  Clients should generally consider the boundaries value
      opaque, however.

      @note: If the boundaries output can't be parsed, we return C{None}.

      @param output: Output from a C{cdrecord -msinfo} command.

      @return: Boundaries tuple as described above.
      @raise IOError: If there is problem parsing the output.
      """
      if len(output) < 1:
         logger.warn("Unable to read disc (might not be initialized); returning full capacity.")
         return None
      boundaryPattern = re.compile(r"(^\s*)([0-9]*)(\s*,\s*)([0-9]*)(\s*$)")
      parsed = boundaryPattern.search(output[0])
      if not parsed:
         raise IOError("Unable to parse output of boundaries command.")
      try:
         boundaries = ( int(parsed.group(2)), int(parsed.group(4)) )
      except TypeError:
         raise IOError("Unable to parse output of boundaries command.")
      return boundaries
   _parseBoundariesOutput = staticmethod(_parseBoundariesOutput)


   #################################
   # Methods used to build commands
   #################################

   def _buildOpenTrayArgs(device):
      """
      Builds a list of arguments to be passed to a C{eject} command.

      The arguments will cause the C{eject} command to open the tray and
      eject the media.  No validation is done by this method as to whether
      this action actually makes sense.

      @param device: Filesystem device name for this writer, i.e. C{/dev/cdrw}.

      @return: List suitable for passing to L{util.executeCommand} as C{args}.
      """
      args = []
      args.append(device)
      return args
   _buildOpenTrayArgs = staticmethod(_buildOpenTrayArgs)

   def _buildCloseTrayArgs(device):
      """
      Builds a list of arguments to be passed to a C{eject} command.

      The arguments will cause the C{eject} command to close the tray and reload
      the media.  No validation is done by this method as to whether this
      action actually makes sense.

      @param device: Filesystem device name for this writer, i.e. C{/dev/cdrw}.

      @return: List suitable for passing to L{util.executeCommand} as C{args}.
      """
      args = []
      args.append("-t")
      args.append(device)
      return args
   _buildCloseTrayArgs = staticmethod(_buildCloseTrayArgs)

   def _buildPropertiesArgs(hardwareId):
      """
      Builds a list of arguments to be passed to a C{cdrecord} command.

      The arguments will cause the C{cdrecord} command to ask the device
      for a list of its capacities via the C{-prcap} switch.

      @param hardwareId: Hardware id for the device (either SCSI id or device path)

      @return: List suitable for passing to L{util.executeCommand} as C{args}.
      """
      args = []
      args.append("-prcap")
      args.append("dev=%s" % hardwareId)
      return args
   _buildPropertiesArgs = staticmethod(_buildPropertiesArgs)

   def _buildBoundariesArgs(hardwareId):
      """
      Builds a list of arguments to be passed to a C{cdrecord} command.

      The arguments will cause the C{cdrecord} command to ask the device for
      the current multisession boundaries of the media using the C{-msinfo}
      switch.

      @param hardwareId: Hardware id for the device (either SCSI id or device path)

      @return: List suitable for passing to L{util.executeCommand} as C{args}.
      """
      args = []
      args.append("-msinfo")
      args.append("dev=%s" % hardwareId)
      return args
   _buildBoundariesArgs = staticmethod(_buildBoundariesArgs)

   def _buildBlankArgs(hardwareId, driveSpeed=None):
      """
      Builds a list of arguments to be passed to a C{cdrecord} command.

      The arguments will cause the C{cdrecord} command to blank the media in
      the device identified by C{hardwareId}.  No validation is done by this method
      as to whether the action makes sense (i.e. to whether the media even can
      be blanked).

      @param hardwareId: Hardware id for the device (either SCSI id or device path)
      @param driveSpeed: Speed at which the drive writes.

      @return: List suitable for passing to L{util.executeCommand} as C{args}.
      """
      args = []
      args.append("-v")
      args.append("blank=fast")
      if driveSpeed is not None:
         args.append("speed=%d" % driveSpeed)
      args.append("dev=%s" % hardwareId)
      return args
   _buildBlankArgs = staticmethod(_buildBlankArgs)

   def _buildWriteArgs(hardwareId, imagePath, driveSpeed=None, writeMulti=True):
      """
      Builds a list of arguments to be passed to a C{cdrecord} command.

      The arguments will cause the C{cdrecord} command to write the indicated
      ISO image (C{imagePath}) to the media in the device identified by
      C{hardwareId}.  The C{writeMulti} argument controls whether to write a
      multisession disc.  No validation is done by this method as to whether
      the action makes sense (i.e. to whether the device even can write
      multisession discs, for instance).

      @param hardwareId: Hardware id for the device (either SCSI id or device path)
      @param imagePath: Path to an ISO image on disk.
      @param driveSpeed: Speed at which the drive writes.
      @param writeMulti: Indicates whether to write a multisession disc.

      @return: List suitable for passing to L{util.executeCommand} as C{args}.
      """
      args = []
      args.append("-v")
      if driveSpeed is not None:
         args.append("speed=%d" % driveSpeed)
      args.append("dev=%s" % hardwareId)
      if writeMulti:
         args.append("-multi")
      args.append("-data")
      args.append(imagePath) 
      return args
   _buildWriteArgs = staticmethod(_buildWriteArgs)


########################################################################
# IsoImage class definition
########################################################################

class IsoImage(object):

   ######################
   # Class documentation
   ######################

   """
   Represents an ISO filesystem image for use with CD recording operations.

   Summary
   =======

      This object represents an ISO 9660 filesystem image.  It is implemented
      in terms of the C{mkisofs} program, which has been ported to many
      operating systems and platforms.  A "sensible subset" of the C{mkisofs}
      functionality is made available through the public interface, allowing
      callers to set a variety of basic options such as publisher id,
      application id, etc. as well as specify exactly which files and
      directories they want included in their image.

      By default, the image is created using the Rock Ridge protocol (using the
      C{-r} option to C{mkisofs}) because Rock Ridge discs are generally more
      useful on UN*X filesystems than standard ISO 9660 images.  However,
      callers can fall back to the default C{mkisofs} functionality by setting
      the C{useRockRidge} instance variable to C{False}.  Note, however, that
      this option is not well-tested.

   Where Files and Directories are Placed in the Image
   ===================================================

      Although this class is implemented in terms of the C{mkisofs} program,
      its standard "image contents" semantics are slightly different than the original
      C{mkisofs} semantics.  The difference is that files and directories are
      added to the image with some additional information about their source
      directory kept intact.  

      As an example, suppose you add the file C{/etc/profile} to your image and
      you do not configure a graft point.  The file C{/profile} will be created
      in the image.  The behavior for directories is similar.  For instance,
      suppose that you add C{/etc/X11} to the image and do not configure a
      graft point.  In this case, the directory C{/X11} will be created in the
      image, even if the original C{/etc/X11} directory is empty.  I{This
      behavior differs from the standard C{mkisofs} behavior!}

      If a graft point is configured, it will be used to modify the point at
      which a file or directory is added into an image.  Using the examples
      from above, let's assume you set a graft point of C{base} when adding
      C{/etc/profile} and C{/etc/X11} to your image.  In this case, the file
      C{/base/profile} and the directory C{/base/X11} would be added to the
      image.  

      I feel that this behavior is more consistent than the original C{mkisofs}
      behavior.  However, to be fair, it is not quite as flexible, and some
      users might not like it.  For this reason, the C{contentsOnly} parameter
      to the L{addEntry} method can be used to revert to the original behavior
      if desired.

   @sort: __init__, addEntry, getEstimatedSize, _getEstimatedSize, writeImage, 
          _buildDirEntries _buildGeneralArgs, _buildSizeArgs, _buildWriteArgs,
          device, boundaries, graftPoint, useRockRidge, applicationId,
          biblioFile, publisherId, preparerId, volumeId
   """

   ##############
   # Constructor
   ##############

   def __init__(self, device=None, boundaries=None, graftPoint=None):
      """
      Initializes an empty ISO image object.

      Only the most commonly-used configuration items can be set using this
      constructor.  If you have a need to change the others, do so immediately
      after creating your object.

      The device and boundaries values are both required in order to write
      multisession discs.  If either is missing or C{None}, a multisession disc
      will not be written.  The boundaries tuple is in terms of ISO sectors, as
      built by an image writer class and returned in a L{writer.MediaCapacity}
      object.

      @param device: Name of the device that the image will be written to
      @type device: Either be a filesystem path or a SCSI address

      @param boundaries: Session boundaries as required by C{mkisofs}
      @type boundaries: Tuple C{(last_sess_start,next_sess_start)} as returned from C{cdrecord -msinfo}, or C{None}

      @param graftPoint: Default graft point for this page.
      @type graftPoint: String representing a graft point path (see L{addEntry}).
      """
      self._device = None
      self._boundaries = None
      self._graftPoint = None
      self._useRockRidge = True
      self._applicationId = None
      self._biblioFile = None
      self._publisherId = None
      self._preparerId = None
      self._volumeId = None
      self.entries = { }
      self.device = device
      self.boundaries = boundaries
      self.graftPoint = graftPoint
      self.useRockRidge = True
      self.applicationId = None
      self.biblioFile = None
      self.publisherId = None
      self.preparerId = None
      self.volumeId = None
      logger.debug("Created new ISO image object.")


   #############
   # Properties
   #############

   def _setDevice(self, value):
      """
      Property target used to set the device value.
      If not C{None}, the value can be either an absolute path or a SCSI id.
      @raise ValueError: If the value is not valid
      """
      try:
         if value is None:
            self._device = None
         else:
            if os.path.isabs(value):
               self._device = value
            else:
               self._device = validateScsiId(value)
      except ValueError:
         raise ValueError("Device must either be an absolute path or a valid SCSI id.")

   def _getDevice(self):
      """
      Property target used to get the device value.
      """
      return self._device

   def _setBoundaries(self, value):
      """
      Property target used to set the boundaries tuple.
      If not C{None}, the value must be a tuple of two integers.
      @raise ValueError: If the tuple values are not integers.
      @raise IndexError: If the tuple does not contain enough elements.
      """
      if value is None:
         self._boundaries = None
      else:
         self._boundaries = (int(value[0]), int(value[1]))

   def _getBoundaries(self):
      """
      Property target used to get the boundaries value.
      """
      return self._boundaries

   def _setGraftPoint(self, value):
      """
      Property target used to set the graft point.
      The value must be a non-empty string if it is not C{None}.
      @raise ValueError: If the value is an empty string.
      """
      if value is not None:
         if len(value) < 1:
            raise ValueError("The graft point must be a non-empty string.")
      self._graftPoint = value

   def _getGraftPoint(self):
      """
      Property target used to get the graft point.
      """
      return self._graftPoint

   def _setUseRockRidge(self, value):
      """
      Property target used to set the use RockRidge flag.
      No validations, but we normalize the value to C{True} or C{False}.
      """
      if value:
         self._useRockRidge = True
      else:
         self._useRockRidge = False

   def _getUseRockRidge(self):
      """
      Property target used to get the use RockRidge flag.
      """
      return self._useRockRidge

   def _setApplicationId(self, value):
      """
      Property target used to set the application id.
      The value must be a non-empty string if it is not C{None}.
      @raise ValueError: If the value is an empty string.
      """
      if value is not None:
         if len(value) < 1:
            raise ValueError("The application id must be a non-empty string.")
      self._applicationId = value

   def _getApplicationId(self):
      """
      Property target used to get the application id.
      """
      return self._applicationId

   def _setBiblioFile(self, value):
      """
      Property target used to set the biblio file.
      The value must be a non-empty string if it is not C{None}.
      @raise ValueError: If the value is an empty string.
      """
      if value is not None:
         if len(value) < 1:
            raise ValueError("The biblio file must be a non-empty string.")
      self._biblioFile = value

   def _getBiblioFile(self):
      """
      Property target used to get the biblio file.
      """
      return self._biblioFile

   def _setPublisherId(self, value):
      """
      Property target used to set the publisher id.
      The value must be a non-empty string if it is not C{None}.
      @raise ValueError: If the value is an empty string.
      """
      if value is not None:
         if len(value) < 1:
            raise ValueError("The publisher id must be a non-empty string.")
      self._publisherId = value

   def _getPublisherId(self):
      """
      Property target used to get the publisher id.
      """
      return self._publisherId

   def _setPreparerId(self, value):
      """
      Property target used to set the preparer id.
      The value must be a non-empty string if it is not C{None}.
      @raise ValueError: If the value is an empty string.
      """
      if value is not None:
         if len(value) < 1:
            raise ValueError("The preparer id must be a non-empty string.")
      self._preparerId = value

   def _getPreparerId(self):
      """
      Property target used to get the preparer id.
      """
      return self._preparerId

   def _setVolumeId(self, value):
      """
      Property target used to set the volume id.
      The value must be a non-empty string if it is not C{None}.
      @raise ValueError: If the value is an empty string.
      """
      if value is not None:
         if len(value) < 1:
            raise ValueError("The volume id must be a non-empty string.")
      self._volumeId = value

   def _getVolumeId(self):
      """
      Property target used to get the volume id.
      """
      return self._volumeId

   device = property(_getDevice, _setDevice, None, "Device that image will be written to (device path or SCSI id).")
   boundaries = property(_getBoundaries, _setBoundaries, None, "Session boundaries as required by C{mkisofs}.")
   graftPoint = property(_getGraftPoint, _setGraftPoint, None, "Default image-wide graft point (see L{addEntry} for details).")
   useRockRidge = property(_getUseRockRidge, _setUseRockRidge, None, "Indicates whether to use RockRidge (default is C{True}).")
   applicationId = property(_getApplicationId, _setApplicationId, None, "Optionally specifies the ISO header application id value.")
   biblioFile = property(_getBiblioFile, _setBiblioFile, None, "Optionally specifies the ISO bibliographic file name.")
   publisherId = property(_getPublisherId, _setPublisherId, None, "Optionally specifies the ISO header publisher id value.")
   preparerId = property(_getPreparerId, _setPreparerId, None, "Optionally specifies the ISO header preparer id value.")
   volumeId = property(_getVolumeId, _setVolumeId, None, "Optionally specifies the ISO header volume id value.")


   #########################
   # General public methods
   #########################

   def addEntry(self, path, graftPoint=None, override=False, contentsOnly=False):
      """
      Adds an individual file or directory into the ISO image.

      The path must exist and must be a file or a directory.  By default, the
      entry will be placed into the image at the root directory, but this
      behavior can be overridden using the C{graftPoint} parameter or instance
      variable.

      You can use the C{contentsOnly} behavior to revert to the "original"
      C{mkisofs} behavior for adding directories, which is to add only the
      items within the directory, and not the directory itself.

      @note: Things get I{odd} if you try to add a directory to an image that
      will be written to a multisession disc, and the same directory already
      exists in an earlier session on that disc.  Not all of the data gets
      written.  You really wouldn't want to do this anyway, I guess.

      @note: An exception will be thrown if the path has already been added to
      the image, unless the C{override} parameter is set to C{True}.

      @note: The method C{graftPoints} parameter overrides the object-wide
      instance variable.  If neither the method parameter or object-wide value
      is set, the path will be written at the image root.  The graft point
      behavior is determined by the value which is in effect I{at the time this
      method is called}, so you I{must} set the object-wide value before
      calling this method for the first time, or your image may not be
      consistent.  

      @note: You I{cannot} use the local C{graftPoint} parameter to "turn off"
      an object-wide instance variable by setting it to C{None}.  Python's
      default argument functionality buys us a lot, but it can't make this
      method psychic. :)

      @param path: File or directory to be added to the image
      @type path: String representing a path on disk

      @param graftPoint: Graft point to be used when adding this entry
      @type graftPoint: String representing a graft point path, as described above

      @param override: Override an existing entry with the same path.
      @type override: Boolean true/false

      @param contentsOnly: Add directory contents only (standard C{mkisofs} behavior).
      @type contentsOnly: Boolean true/false

      @raise ValueError: If path is not a file or directory, or does not exist.
      @raise ValueError: If the path has already been added, and override is not set.
      @raise ValueError: If a path cannot be encoded properly.
      """
      path = encodePath(path)
      if not override:
         if path in self.entries.keys():
            raise ValueError("Path has already been added to the image.")
      if os.path.islink(path):
         raise ValueError("Path must not be a link.") 
      if os.path.isdir(path):
         if graftPoint is not None:
            if contentsOnly:
               self.entries[path] = graftPoint
            else:
               self.entries[path] = os.path.join(graftPoint, os.path.basename(path))
         elif self.graftPoint is not None: 
            if contentsOnly:
               self.entries[path] = self.graftPoint
            else:
               self.entries[path] = os.path.join(self.graftPoint, os.path.basename(path))
         else:
            if contentsOnly:
               self.entries[path] = None
            else:
               self.entries[path] = os.path.basename(path)
      elif os.path.isfile(path):
         if graftPoint is not None:
            self.entries[path] = graftPoint
         elif self.graftPoint is not None:
            self.entries[path] = self.graftPoint
         else:
            self.entries[path] = None
      else:
         raise ValueError("Path must be a file or a directory.")

   def getEstimatedSize(self):
      """
      Returns the estimated size (in bytes) of the ISO image.

      This is implemented via the C{-print-size} option to C{mkisofs}, so it
      might take a bit of time to execute.  However, the result is as accurate
      as we can get, since it takes into account all of the ISO overhead, the
      true cost of directories in the structure, etc, etc.

      @return: Estimated size of the image, in bytes.

      @raise IOError: If there is a problem calling C{mkisofs}.
      @raise ValueError: If there are no filesystem entries in the image
      """
      if len(self.entries.keys()) == 0:
         raise ValueError("Image does not contain any entries.")
      return self._getEstimatedSize(self.entries)

   def _getEstimatedSize(self, entries):
      """
      Returns the estimated size (in bytes) for the passed-in entries dictionary.
      @return: Estimated size of the image, in bytes.
      @raise IOError: If there is a problem calling C{mkisofs}.
      """
      args = self._buildSizeArgs(entries)
      command = resolveCommand(MKISOFS_COMMAND)
      (result, output) = executeCommand(command, args, returnOutput=True, ignoreStderr=True)
      if result != 0:
         raise IOError("Error (%d) executing mkisofs command to estimate size." % result)
      if len(output) != 1:
         raise IOError("Unable to parse mkisofs output.")
      try:
         sectors = float(output[0])
         size = convertSize(sectors, UNIT_SECTORS, UNIT_BYTES)
         return size
      except: 
         raise IOError("Unable to parse mkisofs output.")

   def writeImage(self, imagePath):
      """
      Writes this image to disk using the image path.

      @param imagePath: Path to write image out as
      @type imagePath: String representing a path on disk

      @raise IOError: If there is an error writing the image to disk.
      @raise ValueError: If there are no filesystem entries in the image
      @raise ValueError: If a path cannot be encoded properly.
      """
      imagePath = encodePath(imagePath)
      if len(self.entries.keys()) == 0:
         raise ValueError("Image does not contain any entries.")
      args = self._buildWriteArgs(self.entries, imagePath)
      command = resolveCommand(MKISOFS_COMMAND)
      (result, output) = executeCommand(command, args, returnOutput=False)
      if result != 0:
         raise IOError("Error (%d) executing mkisofs command to build image." % result)


   #########################################
   # Methods used to build mkisofs commands
   #########################################

   def _buildDirEntries(entries):
      """
      Uses an entries dictionary to build a list of directory locations for use
      by C{mkisofs}.

      We build a list of entries that can be passed to C{mkisofs}.  Each entry is
      either raw (if no graft point was configured) or in graft-point form as
      described above (if a graft point was configured).  The dictionary keys
      are the path names, and the values are the graft points, if any.

      @param entries: Dictionary of image entries (i.e. self.entries)

      @return: List of directory locations for use by C{mkisofs}
      """
      dirEntries = []
      for key in entries.keys():
         if entries[key] is None:
            dirEntries.append(key)
         else:
            dirEntries.append("%s/=%s" % (entries[key].strip("/"), key))
      return dirEntries
   _buildDirEntries = staticmethod(_buildDirEntries)

   def _buildGeneralArgs(self):
      """
      Builds a list of general arguments to be passed to a C{mkisofs} command.

      The various instance variables (C{applicationId}, etc.) are filled into
      the list of arguments if they are set.
      By default, we will build a RockRidge disc.  If you decide to change
      this, think hard about whether you know what you're doing.  This option
      is not well-tested.

      @return: List suitable for passing to L{util.executeCommand} as C{args}.
      """
      args = []
      if self.applicationId is not None:
         args.append("-A")
         args.append(self.applicationId)
      if self.biblioFile is not None:
         args.append("-biblio")
         args.append(self.biblioFile)
      if self.publisherId is not None:
         args.append("-publisher")
         args.append(self.publisherId)
      if self.preparerId is not None:
         args.append("-p")
         args.append(self.preparerId)
      if self.volumeId is not None:
         args.append("-V")
         args.append(self.volumeId)
      return args

   def _buildSizeArgs(self, entries):
      """
      Builds a list of arguments to be passed to a C{mkisofs} command.

      The various instance variables (C{applicationId}, etc.) are filled into
      the list of arguments if they are set.  The command will be built to just
      return size output (a simple count of sectors via the C{-print-size} option),
      rather than an image file on disk.

      By default, we will build a RockRidge disc.  If you decide to change
      this, think hard about whether you know what you're doing.  This option
      is not well-tested.

      @param entries: Dictionary of image entries (i.e. self.entries)

      @return: List suitable for passing to L{util.executeCommand} as C{args}.
      """
      args = self._buildGeneralArgs()
      args.append("-print-size")
      args.append("-graft-points")
      if self.useRockRidge:
         args.append("-r")
      if self.device is not None and self.boundaries is not None:
         args.append("-C")
         args.append("%d,%d" % (self.boundaries[0], self.boundaries[1]))
         args.append("-M")
         args.append(self.device)
      args.extend(self._buildDirEntries(entries))
      return args

   def _buildWriteArgs(self, entries, imagePath):
      """
      Builds a list of arguments to be passed to a C{mkisofs} command.

      The various instance variables (C{applicationId}, etc.) are filled into
      the list of arguments if they are set.  The command will be built to write
      an image to disk.

      By default, we will build a RockRidge disc.  If you decide to change
      this, think hard about whether you know what you're doing.  This option
      is not well-tested.

      @param entries: Dictionary of image entries (i.e. self.entries)

      @param imagePath: Path to write image out as
      @type imagePath: String representing a path on disk

      @return: List suitable for passing to L{util.executeCommand} as C{args}.
      """
      args = self._buildGeneralArgs()
      args.append("-graft-points")
      if self.useRockRidge:
         args.append("-r")
      args.append("-o")
      args.append(imagePath)
      if self.device is not None and self.boundaries is not None:
         args.append("-C")
         args.append("%d,%d" % (self.boundaries[0], self.boundaries[1]))
         args.append("-M")
         args.append(self.device)
      args.extend(self._buildDirEntries(entries))
      return args

