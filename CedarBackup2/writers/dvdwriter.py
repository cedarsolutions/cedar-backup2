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
# Copyright (c) 2007 Kenneth J. Pronovici.
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
# Purpose  : Provides functionality related to DVD writer devices.
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

########################################################################
# Module documentation
########################################################################

"""
Provides functionality related to DVD writer devices.

@sort: MediaDefinition, DvdWriter, MEDIA_DVDPLUSR, MEDIA_DVDPLUSRW

@var MEDIA_DVDPLUSR: Constant representing DVD+R media.
@var MEDIA_DVDPLUSRW: Constant representing DVD+RW media.

@author: Kenneth J. Pronovici <pronovic@ieee.org>
"""

########################################################################
# Imported modules
########################################################################

# System modules
import os
import re
import logging

# Cedar Backup modules
from CedarBackup2.filesystem import BackupFileList
from CedarBackup2.writers.util import IsoImage
from CedarBackup2.util import resolveCommand, executeCommand
from CedarBackup2.util import convertSize, displayBytes, encodePath
from CedarBackup2.util import UNIT_SECTORS, UNIT_BYTES, UNIT_GBYTES
from CedarBackup2.writers.util import validateDevice, validateDriveSpeed


########################################################################
# Module-wide constants and variables
########################################################################

logger = logging.getLogger("CedarBackup2.log.writers.dvdwriter")

MEDIA_DVDPLUSR  = 1
MEDIA_DVDPLUSRW = 2

GROWISOFS_COMMAND = [ "growisofs", ]
EJECT_COMMAND     = [ "eject", ]
MEDIAINFO_COMMAND = [ "dvd+rw-mediainfo", ]


########################################################################
# MediaDefinition class definition
########################################################################

class MediaDefinition(object):

   """
   Class encapsulating information about DVD media definitions.

   The following media types are accepted:

         - C{MEDIA_DVDPLUSR}: DVD+R media (4.4 GB capacity)
         - C{MEDIA_DVDPLUSRW}: DVD+RW media (4.4 GB capacity)

   Note that the capacity attribute returns capacity in terms of ISO sectors
   (C{util.ISO_SECTOR_SIZE)}.  This is for compatibility with the CD writer
   functionality.

   The capacities are 4.4 GB because Cedar Backup deals in "true" gigabytes
   of 1024*1024*1024 bytes per gigabyte.

   @sort: __init__, mediaType, rewritable, capacity
   """

   def __init__(self, mediaType):
      """
      Creates a media definition for the indicated media type.
      @param mediaType: Type of the media, as discussed above.
      @raise ValueError: If the media type is unknown or unsupported.
      """
      self._mediaType = None
      self._rewritable = False
      self._capacity = 0.0
      self._setValues(mediaType)

   def _setValues(self, mediaType):
      """
      Sets values based on media type.
      @param mediaType: Type of the media, as discussed above.
      @raise ValueError: If the media type is unknown or unsupported.
      """
      if mediaType not in [MEDIA_DVDPLUSR, MEDIA_DVDPLUSRW, ]:
         raise ValueError("Invalid media type %d." % mediaType)
      self._mediaType = mediaType
      if self._mediaType == MEDIA_DVDPLUSR:
         self._rewritable = False
         self._capacity = convertSize(4.4, UNIT_GBYTES, UNIT_SECTORS)   # 4.4 "true" GB = 4.7 "marketing" GB
      elif self._mediaType == MEDIA_DVDPLUSRW:
         self._rewritable = True
         self._capacity = convertSize(4.4, UNIT_GBYTES, UNIT_SECTORS)   # 4.4 "true" GB = 4.7 "marketing" GB

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

   def _getCapacity(self):
      """
      Property target used to get the capacity value.
      """
      return self._capacity

   mediaType = property(_getMediaType, None, None, doc="Configured media type.")
   rewritable = property(_getRewritable, None, None, doc="Boolean indicating whether the media is rewritable.")
   capacity = property(_getCapacity, None, None, doc="Total capacity of media in 2048-byte sectors.")


########################################################################
# MediaCapacity class definition
########################################################################

class MediaCapacity(object):

   """
   Class encapsulating information about DVD media capacity.

   Space used and space available do not include any information about media
   lead-in or other overhead.

   @sort: __init__, bytesUsed, bytesAvailable
   """

   def __init__(self, bytesUsed, bytesAvailable):
      """
      Initializes a capacity object.
      @raise ValueError: If the bytes used and available values are not floats.
      """
      self._bytesUsed = float(bytesUsed)
      self._bytesAvailable = float(bytesAvailable)

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

   bytesUsed = property(_getBytesUsed, None, None, doc="Space used on disc, in bytes.")
   bytesAvailable = property(_getBytesAvailable, None, None, doc="Space available on disc, in bytes.")


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
      self.entries = None     # dict mapping path to graft point


########################################################################
# DvdWriter class definition
########################################################################

class DvdWriter(object):

   ######################
   # Class documentation
   ######################

   """
   Class representing a device that knows how to write some kinds of DVD media.

   Summary
   =======

      This is a class representing a device that knows how to write some kinds
      of DVD media.  It provides common operations for the device, such as
      ejecting the media and writing data to the media.

      This class is implemented in terms of the C{eject}, C{growisofs} and
      C{dvd+rw-mediainfo} utilities, all of which should be available on most
      UN*X platforms.

   Image Writer Interface
   ======================

      The following methods make up the "image writer" interface shared
      with other kinds of writers::

         __init__
         initializeImage()
         addImageEntry()
         writeImage()

      Only these methods will be used by other Cedar Backup functionality
      that expects a compatible image writer.

      Unlike the C{CdWriter}, the C{DvdWriter} can only operate in terms of
      filesystem devices, not SCSI devices.  So, although the constructor
      interface accepts a SCSI device parameter for the sake of compatibility,
      it's not used.

   Media Types
   ===========

      This class knows how to write to DVD+R and DVD+RW media, represented
      by the following constants:

         - C{MEDIA_DVDPLUSR}: DVD+R media (4.4 GB capacity)
         - C{MEDIA_DVDPLUSRW}: DVD+RW media (4.4 GB capacity)

      The difference is that DVD+RW media can be rewritten, while DVD+R media
      cannot be (although at present, C{DvdWriter} does not really
      differentiate between rewritable and non-rewritable media).

      The capacities are 4.4 GB because Cedar Backup deals in "true" gigabytes
      of 1024*1024*1024 bytes per gigabyte.

      The underlying C{growisofs} utility does support other kinds of media
      (including DVD-R, DVD-RW and BlueRay) which work somewhat differently
      than standard DVD+R and DVD+RW media.  I don't support these other kinds
      of media because I haven't had any opportunity to work with them.  The
      same goes for dual-layer media of any type.

   Device Attributes vs. Media Attributes
   ======================================

      As with the cdwriter functionality, a given dvdwriter instance has two
      different kinds of attributes associated with it.  I call these device
      attributes and media attributes.

      Device attributes are things which can be determined without looking at
      the media.  Media attributes are attributes which vary depending on the
      state of the media.  In general, device attributes are available via
      instance variables and are constant over the life of an object, while
      media attributes can be retrieved through method calls.

      Compared to cdwriters, dvdwriters have very few attributes.  This is due
      to differences between the way C{growisofs} works relative to
      C{cdrecord}.

   Media Capacity
   ==============

      One major difference between the C{cdrecord}/C{mkisofs} utilities used by
      the cdwriter class and the C{growisofs} utility used here is that the
      process of estimating remaining capacity and image size is more
      straightforward with C{cdrecord}/C{mkisofs} than with C{growisofs}.

      In this class, remaining capacity is calculated by asking
      C{dvd+rw-mediainfo} for the "READ CAPACITY" of the disc (which seems to
      be more-or-less the size of the data written previously to the disc), and
      subtracting that from the capacity on the C{MediaDefinition}.  Image size
      is estimated by asking the C{IsoImage} class for an estimate and then
      adding on a "fudge factor" determined through experimentation.

   Device Tray
   ===========

      It does not seem to be possible to get C{growisofs} to indicate whether a
      given writer device has a tray.  I am not quite sure what to do about
      this.  I haven't actually seen a DVD writer without a tray, so for the
      time being I am going to assume a tray open/close operation is generally
      safe; the C{deviceHasTray} and C{deviceCanEject} attributes are always
      defaulted to C{True}. 

   Testing
   =======

      It's rather difficult to test this code in an automated fashion, even if
      you have access to a physical DVD writer drive.  It's even more difficult
      to test it if you are running on some build daemon (think of a Debian
      autobuilder) which can't be expected to have any hardware or any media
      that you could write to.

      Because of this, some of the implementation below is in terms of static
      methods that are supposed to take defined actions based on their
      arguments.  Public methods are then implemented in terms of a series of
      calls to simplistic static methods.  This way, we can test as much as
      possible of the "difficult" functionality via testing the static methods,
      while hoping that if the static methods are called appropriately, things
      will work properly.  It's not perfect, but it's much better than no
      testing at all.

   @sort: __init__, isRewritable, openTray, closeTray, refreshMedia, 
          initializeImage, addImageEntry, writeImage, 
          _writeImage, _getEstimatedImageSize, _searchForOverburn, _buildWriteArgs,
          device, scsiId, hardwareId, driveSpeed, media, deviceHasTray, deviceCanEject
   """

   ##############
   # Constructor
   ##############

   def __init__(self, device, scsiId=None, driveSpeed=None, mediaType=MEDIA_DVDPLUSRW, unittest=False):
      """
      Initializes a DVD writer object.

      Since C{growisofs} can only address devices using the device path (i.e.
      C{/dev/dvd}), the hardware id will always be set based on the device.  If
      passed in, it will be saved for reference purposes only.

      @note: The C{unittest} parameter should never be set to C{True}
      outside of Cedar Backup code.  It is intended for use in unit testing
      Cedar Backup internals and has no other sensible purpose.

      @param device: Filesystem device associated with this writer.
      @type device: Absolute path to a filesystem device, i.e. C{/dev/dvd}

      @param scsiId: SCSI id for the device (optional, for reference only).
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
      """
      if scsiId is not None:
         logger.warn("SCSI id [%s] will be ignored by DvdWriter.")
      self._image = None  # optionally filled in by initializeImage()
      self._device = validateDevice(device, unittest)
      self._scsiId = scsiId  # not validated, because it's just for reference
      self._driveSpeed = validateDriveSpeed(driveSpeed)
      self._media = MediaDefinition(mediaType)
      self._deviceHasTray = True   # just default it
      self._deviceCanEject = True  # just default it


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
      return self._device

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
   scsiId = property(_getScsiId, None, None, doc="SCSI id for the device (saved for reference only).")
   hardwareId = property(_getHardwareId, None, None, doc="Hardware id for this writer (always the device path).");
   driveSpeed = property(_getDriveSpeed, None, None, doc="Speed at which the drive writes.")
   media = property(_getMedia, None, None, doc="Definition of media that is expected to be in the device.")
   deviceHasTray = property(_getDeviceHasTray, None, None, doc="Indicates whether the device has a media tray.")
   deviceCanEject = property(_getDeviceCanEject, None, None, doc="Indicates whether the device supports ejecting its media.")


   #################################################
   # Methods related to device and media attributes
   #################################################

   def isRewritable(self):
      """Indicates whether the media is rewritable per configuration."""
      return self._media.rewritable

   def retrieveCapacity(self, entireDisc=False):
      """
      Retrieves capacity for the current media in terms of a C{MediaCapacity}
      object.

      If C{entireDisc} is passed in as C{True}, the capacity will be for the
      entire disc, as if it were to be rewritten from scratch.  Otherwise, the
      capacity will be calculated by subtracting the "READ CAPACITY" (reported
      by C{dvd+rw-mediainfo}) from the total capacity of the disc.

      @note: This is only an estimate, because C{growisofs} does not provide a
      good way to calculate the capacity precisely.  In practice, you might
      expect slightly less data to fit on the media than indicated by this
      method.

      @param entireDisc: Indicates whether to return capacity for entire disc.
      @type entireDisc: Boolean true/false

      @return: C{MediaCapacity} object describing the capacity of the media.
      @raise IOError: If the media could not be read for some reason.
      """
      sectorsUsed = 0
      if not entireDisc:
         command = resolveCommand(MEDIAINFO_COMMAND)
         args = [ self.hardwareId, ]
         (result, output) = executeCommand(command, args, returnOutput=True)
         if result != 0:
            raise IOError("Error (%d) reading media capacity." % result)
         sectorsUsed = DvdWriter._getReadCapacity(output)
      sectorsAvailable = self._media.capacity - sectorsUsed  # both are in sectors
      bytesUsed = convertSize(sectorsUsed, UNIT_SECTORS, UNIT_BYTES)
      bytesAvailable = convertSize(sectorsAvailable, UNIT_SECTORS, UNIT_BYTES)
      return MediaCapacity(bytesUsed, bytesAvailable)


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
      @type newDisc: Boolean true/false

      @param tmpdir: Temporary directory to use if needed
      @type tmpdir: String representing a directory path on disk
      """
      self._image = _ImageProperties()
      self._image.newDisc = newDisc
      self._image.tmpdir = encodePath(tmpdir)
      self._image.entries = {} # mapping from path to graft point (if any)

   def addImageEntry(self, path, graftPoint):
      """
      Adds a filepath entry to the writer's associated ISO image.

      The contents of the filepath -- but not the path itself -- will be added
      to the image at the indicated graft point.  If you don't want to use a
      graft point, just pass C{None}.
      
      @note: Before calling this method, you must call L{initializeImage}.

      @param path: File or directory to be added to the image
      @type path: String representing a path on disk

      @param graftPoint: Graft point to be used when adding this entry
      @type graftPoint: String representing a graft point path, as described above

      @raise ValueError: If initializeImage() was not previously called
      @raise ValueError: If the path is not a valid file or directory
      """
      if self._image is None:
         raise ValueError("Must call initializeImage() before using this method.")
      if not os.path.exists(path):
         raise ValueError("Path [%s] does not exist." % path)
      self._image.entries[path] = graftPoint


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
         command = resolveCommand(EJECT_COMMAND)
         args = [ self.device, ]
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
         command = resolveCommand(EJECT_COMMAND)
         args = [ self.device, ]
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
      will be re-created from scratch.  Note that unlike C{CdWriter},
      C{DvdWriter} does not blank rewritable media before reusing it; however,
      C{growisofs} is called such that the media will be re-initialized as
      needed.

      If C{imagePath} is passed in as C{None}, then the existing image
      configured with C{initializeImage()} will be used.  Under these
      circumstances, the passed-in C{newDisc} flag will be ignored and the
      value passed in to C{initializeImage()} will apply instead.

      The C{writeMulti} argument is ignored.  It exists for compatibility with
      the Cedar Backup image writer interface.

      @note: The image size indicated in the log ("Image size will be...") is
      only an estimate.  If C{growisofs} fails with a a capacity problem, the
      image size indicated in that error message might differ from the image
      size that was initially logged.

      @param imagePath: Path to an ISO image on disk, or C{None} to use writer's image
      @type imagePath: String representing a path on disk

      @param newDisc: Indicates whether the disc should be re-initialized
      @type newDisc: Boolean true/false.

      @param writeMulti: Unused
      @type writeMulti: Boolean true/false

      @raise ValueError: If the image path is not absolute.
      @raise ValueError: If some path cannot be encoded properly.
      @raise IOError: If the media could not be written to for some reason.
      @raise ValueError: If no image is passed in and initializeImage() was not previously called
      """
      if not writeMulti:
         logger.warn("writeMulti value of [%s] ignored." % writeMulti)
      if imagePath is None:
         if self._image is None:
            raise ValueError("Must call initializeImage() before using this method with no image path.")
         size = DvdWriter._getEstimatedImageSize(self._image.entries)
         logger.info("Image size will be %s (estimated)." % displayBytes(size))
         self._writeImage(self._image.newDisc, None, self._image.entries)
      else:
         if not os.path.isabs(imagePath):
            raise ValueError("Image path must be absolute.")
         imagePath = encodePath(imagePath)
         self._writeImage(newDisc, imagePath, None)


   ##################################################################
   # Utility methods for dealing with growisofs and dvd+rw-mediainfo
   ##################################################################

   def _writeImage(self, newDisc, imagePath, entries):
      """
      Writes an image to disc using either an entries list or an ISO image on
      disk.

      Callers are assumed to have done validation on paths, etc. before calling
      this method.

      A dry run is done before actually writing the image, to be sure it fits
      on the media.  If the dry run yields an error, we try to parse out the
      error message.

      @param newDisc: Indicates whether the disc should be re-initialized
      @param imagePath: Path to an ISO image on disk, or c{None} to use C{entries}
      @param entries: Mapping from path to graft point, or C{None} to use C{imagePath}

      @raise IOError: If the media could not be written to for some reason.
      """
      command = resolveCommand(GROWISOFS_COMMAND)
      args = DvdWriter._buildWriteArgs(newDisc, self.hardwareId, self._driveSpeed, imagePath, entries, dryRun=True)
      (result, output) = executeCommand(command, args, returnOutput=True)
      if result != 0:
         DvdWriter._searchForOverburn(output) # throws own exception if overburn condition is found
         raise IOError("Error (%d) executing dry run to check media capacity." % result)
      logger.debug("Dry run succeeded, so image size should be OK.")
      args = DvdWriter._buildWriteArgs(newDisc, self.hardwareId, self._driveSpeed, imagePath, entries, dryRun=False)
      result = executeCommand(command, args)[0]
      if result != 0:
         raise IOError("Error (%d) executing command to write disc." % result)
      self.refreshMedia()

   def _getEstimatedImageSize(entries):
      """
      Gets the estimated size of a set of image entries.

      This is implemented in terms of the C{IsoImage} class.  The returned
      value is calculated by adding a "fudge factor" to the value from
      C{IsoImage}.  This fudge factor was determined by experimentation and is
      conservative -- the actual image could be as much as 400 blocks smaller
      under some circumstances.

      @param entries: Dictionary mapping path to graft point.

      @return: Total estimated size of image, in bytes.

      @raise ValueError: If there are no entries in the dictionary
      @raise ValueError: If any path in the dictionary does not exist
      @raise IOError: If there is a problem calling C{mkisofs}.
      """
      FUDGE_FACTOR = 2450.0  # determined through experimentation
      if len(entries.keys()) == 0:
         raise ValueError("Must add at least one entry with addImageEntry().")
      image = IsoImage()
      for path in entries.keys():
         image.addEntry(path, entries[path], override=False, contentsOnly=True)
      estimatedSize = image.getEstimatedSize() + FUDGE_FACTOR
      return estimatedSize
   _getEstimatedImageSize = staticmethod(_getEstimatedImageSize)

   def _getReadCapacity(output):
      """
      Parse "READ CAPACITY" in sectors out of C{dvd+rw-mediainfo} output.

      The "READ CAPACITY" line looks like this::

         READ CAPACITY:          30592*2048=62652416

      The first value is the number of sectors used, the second value is the
      sector size (which should be standard at 2048 bytes) and the third value
      is the number of bytes.  This method returns the number of sectors.

      If the "READ CAPACITY" line is not found or does not make sense, then
      zero will be returned.

      @return: Read capacity of media in sectors, as a float.
      """
      if output is not None:
         pattern = re.compile(r"(^)(READ CAPACITY:\s*)([0-9]*)([*])([0-9]*)(=)([0-9]*)")
         for line in output:
            match = pattern.search(line)
            if match is not None:
               return float(match.group(3).strip())
      return 0.0
   _getReadCapacity = staticmethod(_getReadCapacity)

   def _searchForOverburn(output):
      """
      Search for an "overburn" error message in C{growisofs} output.
      
      The C{growisofs} command returns a non-zero exit code and puts a message
      into the output -- even on a dry run -- if there is not enough space on
      the media.  This is called an "overburn" condition.

      The error message looks like this::

         :-( /dev/cdrom: 894048 blocks are free, 2033746 to be written!

      This method looks for the overburn error message anywhere in the output.
      If a matching error message is found, an C{IOError} exception is raised
      containing relevant information about the problem.  Otherwise, the method
      call returns normally.

      @param output: List of output lines to search, as from C{executeCommand}

      @raise IOError: If an overburn condition is found.
      """
      if output is None:
         return
      pattern = re.compile(r"(^)(:-[(])(\s*.*:\s*)(.* )(blocks are free, )(.* )(to be written!)")
      for line in output:
         match = pattern.search(line)
         if match is not None:
            try:
               available = convertSize(float(match.group(4).strip()), UNIT_SECTORS, UNIT_BYTES)
               size = convertSize(float(match.group(6).strip()), UNIT_SECTORS, UNIT_BYTES)
               logger.error("Image [%s] does not fit in available capacity [%s]." % (displayBytes(size), displayBytes(available)))
            except ValueError: 
               logger.error("Image does not fit in available capacity (no useful capacity info available).")
            raise IOError("Media does not contain enough capacity to store image.")
   _searchForOverburn = staticmethod(_searchForOverburn)
         
   def _buildWriteArgs(newDisc, hardwareId, driveSpeed, imagePath, entries, dryRun=False):
      """
      Builds a list of arguments to be passed to a C{growisofs} command.

      The arguments will either cause C{growisofs} to write the indicated image
      file to disc, or will pass C{growisofs} a list of directories or files
      that should be written to disc.  

      The disc will always be written with Rock Ridge extensions (-r).

      @param newDisc: Indicates whether the disc should be re-initialized
      @param hardwareId: Hardware id for the device 
      @param driveSpeed: Speed at which the drive writes.
      @param imagePath: Path to an ISO image on disk, or c{None} to use C{entries}
      @param entries: Mapping from path to graft point, or C{None} to use C{imagePath}
      @param dryRun: Says whether to make this a dry run (for checking capacity)

      @return: List suitable for passing to L{util.executeCommand} as C{args}.

      @raise ValueError: If caller does not pass one or the other of imagePath or entries.
      """
      args = []
      if (imagePath is None and entries is None) or (imagePath is not None and entries is not None):
         raise ValueError("Must use either imagePath or entries.")
      if dryRun:
         args.append("--dry-run")
      if driveSpeed is not None:
         args.append("-speed=%d" % driveSpeed)
      if newDisc:
         args.append("-Z")
      else:
         args.append("-M")
      if imagePath is not None:
         args.append("%s=%s" % (hardwareId, imagePath))
      else:
         args.append(hardwareId)
         args.append("-r")    # Rock Ridge extensions with sane ownership and permissions
         args.append("-graft-points")
         keys = entries.keys()
         keys.sort() # just so we get consistent results
         for key in keys:
            # Same syntax as when calling mkisofs in IsoImage
            if entries[key] is None:
               args.append(key)
            else:
               args.append("%s/=%s" % (entries[key].strip("/"), key))
      return args
   _buildWriteArgs = staticmethod(_buildWriteArgs)

