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
# Copyright (c) 2004 Kenneth J. Pronovici.
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
# Purpose  : Provides image writer-related objects.
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# This file was created with a width of 132 characters, and NO tabs.

########################################################################
# Module documentation
########################################################################

"""
Provides image writer-related objects.
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
from CedarBackup2.util import executeCommand, convertSize, UNIT_SECTORS, UNIT_BYTES, UNIT_KBYTES, UNIT_MBYTES


########################################################################
# Module-wide constants and variables
########################################################################

logger = logging.getLogger("CedarBackup2.writer")

MEDIA_CDRW_74  = 1
MEDIA_CDR_74   = 2
MEDIA_CDRW_80  = 3
MEDIA_CDR_80   = 4

CDRECORD_CMD = [ "cdrecord", ]
EJECT_CMD    = [ "eject", ]


########################################################################
# MediaDefinition class definition
########################################################################

class MediaDefinition(object):

   """
   Class encapsulating information about media definitions.

   The following media types are accepted:

      - C{MEDIA_CDR_74}: 74-minute CD-R media (650 MB capacity)
      - C{MEDIA_CDRW_74}: 74-minute CD-RW media (650 MB capacity)
      - C{MEDIA_CDR_80}: 80-minute CD-R media (700 MB capacity)
      - C{MEDIA_CDRW_80}: 80-minute CD-RW media (700 MB capacity)

   Note that all of the capacities associated with a media definition are in
   terms of ISO sectors (C{util.ISO_SECTOR_SIZE)}.

   @ivar rewritable: Boolean indicating whether the media is rewritable.
   @ivar initialLeadIn: Initial lead-in required for first image written to media.
   @ivar leadIn: Lead-in required on successive images written to media.
   @ivar capacity: Total capacity of the media before any required lead-in.
   """

   def __init__(self, mediaType):
      """
      Creates a media definition for the indicated media type.
      @param mediaType: Type of the media, as discussed above.
      @raise ValueError: If the media type is unknown or unsupported.      
      """
      if mediaType not in [MEDIA_CDR_74, MEDIA_CDRW_74, MEDIA_CDR_80, MEDIA_CDRW_80]:
         raise ValueError("Invalid media type %d." % mediaType)
      self.mediaType = mediaType
      self.initialLeadIn = 11400    # per cdrecord's documentation
      self.leadIn = 6900            # per cdrecord's documentation
      if mediaType == MEDIA_CDR_74:
         self.rewritable = False
         self.capacity = convertSize(650, UNIT_MBYTES, UNIT_SECTORS)
      elif mediaType == MEDIA_CDRW_74:
         self.rewritable = True
         self.capacity = convertSize(650, UNIT_MBYTES, UNIT_SECTORS)
      elif mediaType == MEDIA_CDR_80:
         self.rewritable = False
         self.capacity = convertSize(700, UNIT_MBYTES, UNIT_SECTORS)
      elif mediaType == MEDIA_CDRW_80:
         self.rewritable = True
         self.capacity = convertSize(700, UNIT_MBYTES, UNIT_SECTORS)


########################################################################
# MediaCapacity class definition
########################################################################

class MediaCapacity(object):

   """
   Class encapsulating information about media capacity.

   Space used includes the required media lead-in (unless the disk is unused).
   Space available attempts to provide a picture of how many bytes are
   available for data storage, including any required lead-in.  

   The boundaries value is either C{None} (if multisession discs are not
   supported) or in exactly the form provided by C{cdrecord -msinfo}.  It can
   be passed as-is to the C{IsoImage} class.

   @ivar bytesUsed: Space used on disc, in bytes.
   @ivar bytesAvailable: Space available on disc, in bytes.
   @ivar boundaries: Session disc boundaries, in terms of ISO sectors
   """

   def __init__(self, bytesUsed, bytesAvailable, boundaries):
      self.bytesUsed = bytesUsed
      self.bytesAvailable = bytesAvailable
      self.boundaries = boundaries


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

      The public methods other than the constructor are part of an "image writer"
      interface that will be shared with other future classes which write other
      kinds of media.  

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

   @ivar device: Filesystem device name for this writer, i.e. C{/dev/cdrw}.
   @ivar scsiId: SCSI id for the device, in the form C{[ATA:]scsibus,target,lun}.
   @ivar driveSpeed: Speed at which the drive writes, i.e. C{2} for 2x device, etc.
   @ivar media: Definition of media that is expected to be in the device.
   @ivar deviceType: Type of the device, as returned from C{cdrecord -prcap}.
   @ivar deviceVendor: Vendor of the device, as returned from C{cdrecord -prcap}.
   @ivar deviceId: Device identification, as returned from C{cdrecord -prcap}.
   @ivar deviceBufferSize: Size of the device's write buffer, in bytes.
   @ivar deviceSupportsMulti: Indicates whether device supports multisession discs.
   @ivar deviceHasTray: Indicates whether the device has a tray to hold its media. 
   @ivar deviceCanEject: Indicates whether the device supports ejecting its media.
   """

   ##############
   # Constructor
   ##############

   def __init__(self, device, scsiId, driveSpeed=None, mediaType=MEDIA_CDRW_74, unittest=False):
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

      The device and SCSI id are both required because some commands (like
      C{eject}) need the device, and other commands (like C{cdrecord}) need the
      SCSI id.  It's also nice to be able to track both of them in once place
      for reference by other pieces of functionality outside of this module.

      @note: The C{unittest} parameter should never be set to C{True}
      outside of Cedar Backup code.  It is intended for use in unit testing
      Cedar Backup internals and has no other sensible purpose.

      @param device: Filesystem device associated with this writer.
      @type device: Absolute path to a filesystem device, i.e. C{/dev/cdrw}

      @param scsiId: SCSI id for the device.
      @type scsiId: SCSI id in the form C{[ATA:]scsibus,target,lun}

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
      self.device = CdWriter._validateDevice(device, unittest)
      self.scsiId = CdWriter._validateScsiId(scsiId)
      self.driveSpeed = CdWriter._validateDriveSpeed(driveSpeed)
      self.media = MediaDefinition(mediaType)
      if not unittest:
         (self.deviceType,
          self.deviceVendor,
          self.deviceId,
          self.deviceBufferSize,
          self.deviceSupportsMulti,
          self.deviceHasTray,
          self.deviceCanEject) = self._retrieveProperties()

   def _validateDevice(device, unittest):
      """
      Validates configured device.
      The device must be an absolute path, must exist, and must be writable.
      The self.unittest flag turns off validation of the device on disk.
      @param device: Filesystem device associated with this writer.
      @param unittest: Indicates whether we're unit testing.
      @return: Device as a string, suitable for assignment to self.device.
      @raise ValueError: If the device value is invalid.
      """
      if not os.path.isabs(device):
         raise ValueError("Device must be an absolute path.")
      if not unittest and not os.path.exists(device):
         raise ValueError("Device must exist on disk.")
      if not unittest and not os.access(device, os.W_OK):
         raise ValueError("Device is not writable by the current user.")
      return device
   _validateDevice = staticmethod(_validateDevice)

   def _validateScsiId(scsiId):
      """
      Validates configured SCSI id.
      SCSI id must be a string in the form C{[ATA:]scsibus,target,lun}.
      @param scsiId: SCSI id for the device.
      @return: SCSI id as a string, suitable for assignment to self.scsiId.
      @raise ValueError: If the SCSI id value is invalid.
      """
      ataPattern = re.compile(r"^\s*ATA:[0-9][0-9]*\s*,\s*[0-9][0-9]*\s*,\s*[0-9][0-9]*\s*$")
      normalPattern = re.compile(r"^\s*[0-9][0-9]*\s*,\s*[0-9][0-9]*\s*,\s*[0-9][0-9]*\s*$")
      if not ataPattern.search(scsiId) and not normalPattern.search(scsiId):
         raise ValueError("SCSI id must be in the form '[ATA:]scsibus,target,lun'.")
      return scsiId
   _validateScsiId = staticmethod(_validateScsiId)

   def _validateDriveSpeed(driveSpeed):
      """
      Validates configured drive speed.
      Drive speed must be an integer which is >= 1.
      @param driveSpeed: Speed at which the drive writes.
      @return: Drive speed as an integer, suitable for assignment to self.driveSpeed.
      @raise ValueError: If the drive speed value is invalid.
      """
      if driveSpeed is None:
         return None
      try:
         intSpeed = int(driveSpeed)
      except TypeError:
         raise ValueError("Drive speed must be an integer >= 1.")
      if intSpeed < 1:
         raise ValueError("Drive speed must an integer >= 1.")
      return intSpeed
   _validateDriveSpeed = staticmethod(_validateDriveSpeed)


   #################################################
   # Methods related to device and media attributes
   #################################################

   def isRewritable(self):
      """Indicates whether the media is rewritable per configuration."""
      return self.media.rewritable

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
      args = CdWriter._buildPropertiesArgs(self.scsiId)
      (result, output) = executeCommand(CDRECORD_CMD, args, returnOutput=True, ignoreStderr=True)
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
      C{None}.  Otherwise, the capacity (including the boundaries) will
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
      return CdWriter._calculateCapacity(self.media, boundaries)

   def _getBoundaries(self, entireDisc=False, useMulti=True):
      """
      Gets the ISO boundaries for the media.

      If C{entireDisc} is passed in as C{True} the boundaries will be C{0,0},
      as if the disc were to be rewritten from scratch.  If the drive does not
      support writing multisession discs, the returned value will be C{None}.
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
      if not self.deviceSupportsMulti:
         return None
      elif not useMulti:
         return None
      elif entireDisc:
         return (0, 0)
      else:
         args = CdWriter._buildBoundariesArgs(self.scsiId)
         (result, output) = executeCommand(CDRECORD_CMD, args, returnOutput=True, ignoreStderr=True)
         if result != 0:
            raise IOError("Error (%d) executing cdrecord command to get capacity." % result)
         return CdWriter._parseBoundariesOutput(output)

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
      if boundaries is None or boundaries[0] == 0:
         sectorsAvailable = media.capacity - media.initialLeadIn
         bytesUsed = 0
         bytesAvailable = convertSize(sectorsAvailable, UNIT_SECTORS, UNIT_BYTES)
      else:
         sectorsAvailable = media.capacity - boundaries[1] - media.leadIn
         bytesUsed = convertSize(boundaries[1], UNIT_SECTORS, UNIT_BYTES)
         bytesAvailable = convertSize(sectorsAvailable, UNIT_SECTORS, UNIT_BYTES)
      return MediaCapacity(bytesUsed, bytesAvailable, boundaries)
   _calculateCapacity = staticmethod(_calculateCapacity)


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
      if self.deviceHasTray and self.deviceCanEject:
         args = CdWriter._buildOpenTrayArgs(self.device)
         result = executeCommand(EJECT_CMD, args)[0]
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
      if self.deviceHasTray and self.deviceCanEject:
         args = CdWriter._buildCloseTrayArgs(self.device)
         result = executeCommand(EJECT_CMD, args)[0]
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

   def writeImage(self, imagePath, newDisc=False, writeMulti=True):
      """
      Writes an ISO image to the media in the device.  

      If C{newDisc} is passed in as C{True}, we assume that the entire disc
      will be overwritten, and the media will be blanked before writing it if
      possible (i.e. if the media is rewritable).  

      If C{writeMulti} is passed in as C{True}, then a multisession disc will
      be written if possible (i.e. if the drive supports writing multisession
      discs.  

      By default, we assume that the disc can be written multisession and that
      we should append to the current contents of the disc.  In any case, the
      ISO image must be generated appropriately (must take into account any
      existing session boundaries, etc.)

      @param imagePath: Path to an ISO image on disk.
      @type imagePath: String representing a path on disk

      @param newDisc: Indicates whether the entire disc will overwritten.
      @type newDisc: Boolean true/false.

      @param writeMulti: Indicates whether a multisession disc should be written, if possible.
      @type writeMulti: Boolean true/false

      @raise ValueError: If the image path is not absolute.
      @raise IOError: If the media could not be written to for some reason.
      """
      if not os.path.isabs(imagePath):
         raise ValueError("Image path must be absolute.")
      if newDisc:
         self._blankMedia()
      args = CdWriter._buildWriteArgs(self.scsiId, imagePath, self.driveSpeed, writeMulti and self.deviceSupportsMulti)
      result = executeCommand(CDRECORD_CMD, args)[0]
      if result != 0:
         raise IOError("Error (%d) executing command to write disc." % result)
      self.refreshMedia()

   def _blankMedia(self):
      """
      Blanks the media in the device, if the media is rewritable.
      @raise IOError: If the media could not be written to for some reason.
      """
      if self.isRewritable():
         args = CdWriter._buildBlankArgs(self.scsiId)
         result = executeCommand(CDRECORD_CMD, args)[0]
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
      executing the C{cdrecord} command that generates output for this method.

      The results are returned as a tuple of (lower, upper) as needed by the
      C{IsoImage} class.  Note that these values are in terms of ISO sectors,
      not bytes.  Clients should generally consider the boundaries value
      opaque, however.

      @param output: Output from a C{cdrecord -msinfo} command.

      @return: Boundaries tuple as described above.
      @raise IOError: If there is problem parsing the output.
      """
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

   def _buildPropertiesArgs(scsiId):
      """
      Builds a list of arguments to be passed to a C{cdrecord} command.

      The arguments will cause the C{cdrecord} command to ask the device
      for a list of its capacities via the C{-prcap} switch.

      @param scsiId: SCSI id for the device, in the form C{[ATA:]scsibus,target,lun}.

      @return: List suitable for passing to L{util.executeCommand} as C{args}.
      """
      args = []
      args.append("-prcap")
      args.append("dev=%s" % scsiId)
      return args
   _buildPropertiesArgs = staticmethod(_buildPropertiesArgs)

   def _buildBoundariesArgs(scsiId):
      """
      Builds a list of arguments to be passed to a C{cdrecord} command.

      The arguments will cause the C{cdrecord} command to ask the device for
      the current multisession boundaries of the media using the C{-msinfo}
      switch.

      @param scsiId: SCSI id for the device, in the form C{[ATA:]scsibus,target,lun}.

      @return: List suitable for passing to L{util.executeCommand} as C{args}.
      """
      args = []
      args.append("-msinfo")
      args.append("dev=%s" % scsiId)
      return args
   _buildBoundariesArgs = staticmethod(_buildBoundariesArgs)

   def _buildBlankArgs(scsiId, driveSpeed=None):
      """
      Builds a list of arguments to be passed to a C{cdrecord} command.

      The arguments will cause the C{cdrecord} command to blank the media in
      the device identified by C{scsiId}.  No validation is done by this method
      as to whether the action makes sense (i.e. to whether the media even can
      be blanked).

      @param scsiId: SCSI id for the device, in the form C{[ATA:]scsibus,target,lun}.
      @param driveSpeed: Speed at which the drive writes.

      @return: List suitable for passing to L{util.executeCommand} as C{args}.
      """
      args = []
      args.append("-v")
      args.append("blank=fast")
      if driveSpeed is not None:
         args.append("speed=%d" % driveSpeed)
      args.append("dev=%s" % scsiId)
      return args
   _buildBlankArgs = staticmethod(_buildBlankArgs)

   def _buildWriteArgs(scsiId, imagePath, driveSpeed=None, writeMulti=True):
      """
      Builds a list of arguments to be passed to a C{cdrecord} command.

      The arguments will cause the C{cdrecord} command to write the indicated
      ISO image (C{imagePath}) to the media in the device identified by
      C{scsiId}.  The C{writeMulti} argument controls whether to write a
      multisession disc.  No validation is done by this method as to whether
      the action makes sense (i.e. to whether the device even can write
      multisession discs, for instance).

      @param scsiId: SCSI id for the device, in the form C{[ATA:]scsibus,target,lun}.
      @param imagePath: Path to an ISO image on disk.
      @param driveSpeed: Speed at which the drive writes.
      @param writeMulti: Indicates whether to write a multisession disc.

      @return: List suitable for passing to L{util.executeCommand} as C{args}.
      """
      args = []
      args.append("-v")
      if driveSpeed is not None:
         args.append("speed=%d" % driveSpeed)
      args.append("dev=%s" % scsiId)
      if writeMulti:
         args.append("-multi")
      args.append("-data")
      args.append(imagePath) 
      return args
   _buildWriteArgs = staticmethod(_buildWriteArgs)

