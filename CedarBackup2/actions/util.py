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
# Copyright (c) 2007,2010 Kenneth J. Pronovici.
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
# Language : Python (>= 2.5)
# Project  : Cedar Backup, release 2
# Revision : $Id$
# Purpose  : Implements action-related utilities
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

########################################################################
# Module documentation
########################################################################

"""
Implements action-related utilities
@sort: findDailyDirs
@author: Kenneth J. Pronovici <pronovic@ieee.org>
"""


########################################################################
# Imported modules
########################################################################

# System modules
import os
import time
import tempfile
import logging

# Cedar Backup modules
from CedarBackup2.filesystem import FilesystemList
from CedarBackup2.util import changeOwnership
from CedarBackup2.util import deviceMounted
from CedarBackup2.writers.util import readMediaLabel
from CedarBackup2.writers.cdwriter import CdWriter
from CedarBackup2.writers.dvdwriter import DvdWriter
from CedarBackup2.writers.cdwriter import MEDIA_CDR_74, MEDIA_CDR_80, MEDIA_CDRW_74, MEDIA_CDRW_80
from CedarBackup2.writers.dvdwriter import MEDIA_DVDPLUSR, MEDIA_DVDPLUSRW
from CedarBackup2.config import DEFAULT_MEDIA_TYPE, DEFAULT_DEVICE_TYPE, REWRITABLE_MEDIA_TYPES
from CedarBackup2.actions.constants import INDICATOR_PATTERN


########################################################################
# Module-wide constants and variables
########################################################################

logger = logging.getLogger("CedarBackup2.log.actions.util")
MEDIA_LABEL_PREFIX   = "CEDAR BACKUP"


########################################################################
# Public utility functions
########################################################################

###########################
# findDailyDirs() function
###########################

def findDailyDirs(stagingDir, indicatorFile):
   """
   Returns a list of all daily staging directories that do not contain
   the indicated indicator file.

   @param stagingDir: Configured staging directory (config.targetDir)

   @return: List of absolute paths to daily staging directories.
   """
   results = FilesystemList()
   yearDirs = FilesystemList()
   yearDirs.excludeFiles = True
   yearDirs.excludeLinks = True
   yearDirs.addDirContents(path=stagingDir, recursive=False, addSelf=False)
   for yearDir in yearDirs:
      monthDirs = FilesystemList()
      monthDirs.excludeFiles = True
      monthDirs.excludeLinks = True
      monthDirs.addDirContents(path=yearDir, recursive=False, addSelf=False)
      for monthDir in monthDirs:
         dailyDirs = FilesystemList()
         dailyDirs.excludeFiles = True
         dailyDirs.excludeLinks = True
         dailyDirs.addDirContents(path=monthDir, recursive=False, addSelf=False)
         for dailyDir in dailyDirs:
            if os.path.exists(os.path.join(dailyDir, indicatorFile)):
               logger.debug("Skipping directory [%s]; contains %s." % (dailyDir, indicatorFile))
            else:
               logger.debug("Adding [%s] to list of daily directories." % dailyDir)
               results.append(dailyDir) # just put it in the list, no fancy operations
   return results


###########################
# createWriter() function
###########################

def createWriter(config):
   """
   Creates a writer object based on current configuration.

   This function creates and returns a writer based on configuration.  This is
   done to abstract action functionality from knowing what kind of writer is in
   use.  Since all writers implement the same interface, there's no need for
   actions to care which one they're working with.

   Currently, the C{cdwriter} and C{dvdwriter} device types are allowed.  An
   exception will be raised if any other device type is used.

   This function also checks to make sure that the device isn't mounted before
   creating a writer object for it.  Experience shows that sometimes if the
   device is mounted, we have problems with the backup.  We may as well do the
   check here first, before instantiating the writer.

   @param config: Config object.

   @return: Writer that can be used to write a directory to some media.

   @raise ValueError: If there is a problem getting the writer.
   @raise IOError: If there is a problem creating the writer object.
   """
   devicePath = config.store.devicePath
   deviceScsiId = config.store.deviceScsiId
   driveSpeed = config.store.driveSpeed
   noEject = config.store.noEject
   refreshMediaDelay = config.store.refreshMediaDelay
   deviceType = _getDeviceType(config)
   mediaType = _getMediaType(config)
   if deviceMounted(devicePath):
      raise IOError("Device [%s] is currently mounted." % (devicePath))
   if deviceType == "cdwriter":
      return CdWriter(devicePath, deviceScsiId, driveSpeed, mediaType, noEject, refreshMediaDelay)
   elif deviceType == "dvdwriter":
      return DvdWriter(devicePath, deviceScsiId, driveSpeed, mediaType, noEject, refreshMediaDelay)
   else:
      raise ValueError("Device type [%s] is invalid." % deviceType)


################################
# writeIndicatorFile() function
################################

def writeIndicatorFile(targetDir, indicatorFile, backupUser, backupGroup):
   """
   Writes an indicator file into a target directory.
   @param targetDir: Target directory in which to write indicator
   @param indicatorFile: Name of the indicator file
   @param backupUser: User that indicator file should be owned by
   @param backupGroup: Group that indicator file should be owned by
   @raise IOException: If there is a problem writing the indicator file
   """
   filename = os.path.join(targetDir, indicatorFile)
   logger.debug("Writing indicator file [%s]." % filename)
   try:
      open(filename, "w").write("")
      changeOwnership(filename, backupUser, backupGroup)
   except Exception, e:
      logger.error("Error writing [%s]: %s" % (filename, e))
      raise e


############################
# getBackupFiles() function
############################

def getBackupFiles(targetDir):
   """
   Gets a list of backup files in a target directory.

   Files that match INDICATOR_PATTERN (i.e. C{"cback.store"}, C{"cback.stage"},
   etc.) are assumed to be indicator files and are ignored.

   @param targetDir: Directory to look in

   @return: List of backup files in the directory

   @raise ValueError: If the target directory does not exist
   """
   if not os.path.isdir(targetDir):
      raise ValueError("Target directory [%s] is not a directory or does not exist." % targetDir)
   fileList = FilesystemList()
   fileList.excludeDirs = True
   fileList.excludeLinks = True
   fileList.excludeBasenamePatterns = INDICATOR_PATTERN
   fileList.addDirContents(targetDir)
   return fileList


####################
# checkMediaState()
####################

def checkMediaState(storeConfig):
   """
   Checks state of the media in the backup device to confirm whether it has
   been initialized for use with Cedar Backup.

   We can tell whether the media has been initialized by looking at its media
   label.  If the media label starts with MEDIA_LABEL_PREFIX, then it has been
   initialized.

   The check varies depending on whether the media is rewritable or not.  For
   non-rewritable media, we also accept a C{None} media label, since this kind
   of media cannot safely be initialized.

   @param storeConfig: Store configuration

   @raise ValueError: If media is not initialized.
   """
   mediaLabel = readMediaLabel(storeConfig.devicePath)
   if storeConfig.mediaType in REWRITABLE_MEDIA_TYPES:
      if mediaLabel is None:
         raise ValueError("Media has not been initialized: no media label available")
      elif not mediaLabel.startswith(MEDIA_LABEL_PREFIX):
         raise ValueError("Media has not been initialized: unrecognized media label [%s]" % mediaLabel)
   else:
      if mediaLabel is None:
         logger.info("Media has no media label; assuming OK since media is not rewritable.")
      elif not mediaLabel.startswith(MEDIA_LABEL_PREFIX):
         raise ValueError("Media has not been initialized: unrecognized media label [%s]" % mediaLabel)


#########################
# initializeMediaState()
#########################

def initializeMediaState(config):
   """
   Initializes state of the media in the backup device so Cedar Backup can
   recognize it.

   This is done by writing an mostly-empty image (it contains a "Cedar Backup"
   directory) to the media with a known media label.

   @note: Only rewritable media (CD-RW, DVD+RW) can be initialized.  It
   doesn't make any sense to initialize media that cannot be rewritten (CD-R,
   DVD+R), since Cedar Backup would then not be able to use that media for a
   backup.

   @param config: Cedar Backup configuration

   @raise ValueError: If media could not be initialized.
   @raise ValueError: If the configured media type is not rewritable
   """ 
   if not config.store.mediaType in REWRITABLE_MEDIA_TYPES:
      raise ValueError("Only rewritable media types can be initialized.")
   mediaLabel = buildMediaLabel()
   writer = createWriter(config)
   writer.initializeImage(True, config.options.workingDir, mediaLabel) # always create a new disc
   tempdir = tempfile.mkdtemp(dir=config.options.workingDir)
   try:
      writer.addImageEntry(tempdir, "CedarBackup")
      writer.writeImage()
   finally:
      if os.path.exists(tempdir):
         try:
            os.rmdir(tempdir)
         except: pass


####################
# buildMediaLabel()
####################

def buildMediaLabel():
   """
   Builds a media label to be used on Cedar Backup media.
   @return: Media label as a string.
   """
   currentDate = time.strftime("%d-%b-%Y").upper()
   return "%s %s" % (MEDIA_LABEL_PREFIX, currentDate)


########################################################################
# Private attribute "getter" functions
########################################################################

############################
# _getDeviceType() function
############################

def _getDeviceType(config):
   """
   Gets the device type that should be used for storing.

   Use the configured device type if not C{None}, otherwise use
   L{config.DEFAULT_DEVICE_TYPE}.

   @param config: Config object.
   @return: Device type to be used.
   """
   if config.store.deviceType is None:
      deviceType = DEFAULT_DEVICE_TYPE
   else:
      deviceType = config.store.deviceType
   logger.debug("Device type is [%s]" % deviceType)
   return deviceType


###########################
# _getMediaType() function
###########################

def _getMediaType(config):
   """
   Gets the media type that should be used for storing.

   Use the configured media type if not C{None}, otherwise use
   C{DEFAULT_MEDIA_TYPE}.

   Once we figure out what configuration value to use, we return a media type
   value that is valid in one of the supported writers::

      MEDIA_CDR_74
      MEDIA_CDRW_74
      MEDIA_CDR_80
      MEDIA_CDRW_80
      MEDIA_DVDPLUSR
      MEDIA_DVDPLUSRW

   @param config: Config object.

   @return: Media type to be used as a writer media type value.
   @raise ValueError: If the media type is not valid.
   """
   if config.store.mediaType is None:
      mediaType = DEFAULT_MEDIA_TYPE
   else:
      mediaType = config.store.mediaType
   if mediaType == "cdr-74":
      logger.debug("Media type is MEDIA_CDR_74.")
      return MEDIA_CDR_74
   elif mediaType == "cdrw-74":
      logger.debug("Media type is MEDIA_CDRW_74.")
      return MEDIA_CDRW_74
   elif mediaType == "cdr-80":
      logger.debug("Media type is MEDIA_CDR_80.")
      return MEDIA_CDR_80
   elif mediaType == "cdrw-80":
      logger.debug("Media type is MEDIA_CDRW_80.")
      return MEDIA_CDRW_80
   elif mediaType == "dvd+r":
      logger.debug("Media type is MEDIA_DVDPLUSR.")
      return MEDIA_DVDPLUSR
   elif mediaType == "dvd+rw":
      logger.debug("Media type is MEDIA_DVDPLUSRW.")
      return MEDIA_DVDPLUSRW
   else:
      raise ValueError("Media type [%s] is not valid." % mediaType)

