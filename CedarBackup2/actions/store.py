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
# Purpose  : Implements the standard 'store' action.
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

########################################################################
# Module documentation
########################################################################

"""
Implements the standard 'store' action.
@sort: executeStore, createWriter, writeImage, writeStoreIndicator, consistencyCheck
@author: Kenneth J. Pronovici <pronovic@ieee.org>
"""


########################################################################
# Imported modules
########################################################################

# System modules
import sys
import os
import logging
import datetime
import tempfile

# Cedar Backup modules
from CedarBackup2.filesystem import compareContents
from CedarBackup2.util import isStartOfWeek, getUidGid, changeOwnership
from CedarBackup2.util import deviceMounted, mount, unmount
from CedarBackup2.writers.cdwriter import CdWriter
from CedarBackup2.writers.cdwriter import MEDIA_CDR_74, MEDIA_CDR_80, MEDIA_CDRW_74, MEDIA_CDRW_80
from CedarBackup2.writers.dvdwriter import DvdWriter
from CedarBackup2.writers.dvdwriter import MEDIA_DVDPLUSR, MEDIA_DVDPLUSRW
from CedarBackup2.actions.constants import DIR_TIME_FORMAT, STAGE_INDICATOR, STORE_INDICATOR
from CedarBackup2.config import DEFAULT_MEDIA_TYPE, DEFAULT_DEVICE_TYPE


########################################################################
# Module-wide constants and variables
########################################################################

logger = logging.getLogger("CedarBackup2.log.actions.store")


########################################################################
# Public functions
########################################################################

##########################
# executeStore() function
##########################

def executeStore(configPath, options, config):
   """
   Executes the store backup action.

   @note: The rebuild action and the store action are very similar.  The
   main difference is that while store only stores a single day's staging
   directory, the rebuild action operates on multiple staging directories.

   @note: When the store action is complete, we will write a store indicator to
   the daily staging directory we used, so it's obvious that the store action
   has completed.  

   @param configPath: Path to configuration file on disk.
   @type configPath: String representing a path on disk.

   @param options: Program command-line options.
   @type options: Options object.

   @param config: Program configuration.
   @type config: Config object.

   @raise ValueError: Under many generic error conditions
   @raise IOError: If there are problems reading or writing files.
   """
   logger.debug("Executing store action.")
   if sys.platform == "darwin":
      logger.warn("Warning: the store action is not fully supported on Mac OS X.")
      logger.warn("See the Cedar Backup software manual for further information.")
   if config.options is None or config.store is None:
      raise ValueError("Store configuration is not properly filled in.")
   rebuildMedia = options.full
   logger.debug("Rebuild media flag [%s]" % rebuildMedia)
   todayIsStart = isStartOfWeek(config.options.startingDay)
   newDisc = rebuildMedia or todayIsStart
   logger.debug("New disc flag [%s]" % newDisc)
   stagingDirs = _findCorrectDailyDir(options, config)
   writeImage(config, newDisc, stagingDirs)
   if config.store.checkData:
      if sys.platform == "darwin":
         logger.warn("Warning: consistency check cannot be run successfully on Mac OS X.")
         logger.warn("See the Cedar Backup software manual for further information.")
      else:
         logger.debug("Running consistency check of media.")
         consistencyCheck(config, stagingDirs)
   writeStoreIndicator(config, stagingDirs)
   logger.info("Executed the 'store' action successfully.")


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
   deviceType = _getDeviceType(config)
   mediaType = _getMediaType(config)
   if deviceMounted(devicePath):
      raise IOError("Device [%s] is currently mounted." % (devicePath))
   if deviceType == "cdwriter":
      return CdWriter(devicePath, deviceScsiId, driveSpeed, mediaType, noEject)
   elif deviceType == "dvdwriter":
      return DvdWriter(devicePath, deviceScsiId, driveSpeed, mediaType, noEject)
   else:
      raise ValueError("Device type [%s] is invalid." % deviceType)


########################
# writeImage() function
########################

def writeImage(config, newDisc, stagingDirs):
   """
   Builds and writes an ISO image containing the indicated stage directories.

   The generated image will contain each of the staging directories listed in
   C{stagingDirs}.  The directories will be placed into the image at the root by
   date, so staging directory C{/opt/stage/2005/02/10} will be placed into the
   disc at C{/2005/02/10}.

   @param config: Config object.
   @param newDisc: Indicates whether the disc should be re-initialized
   @param stagingDirs: Dictionary mapping directory path to date suffix.

   @raise ValueError: Under many generic error conditions
   @raise IOError: If there is a problem writing the image to disc.
   """
   writer = createWriter(config)
   writer.initializeImage(newDisc, config.options.workingDir)
   for stageDir in stagingDirs.keys():
      logger.debug("Adding stage directory [%s]." % stageDir)
      dateSuffix = stagingDirs[stageDir]
      writer.addImageEntry(stageDir, dateSuffix)
   writer.writeImage()


#################################
# writeStoreIndicator() function
#################################

def writeStoreIndicator(config, stagingDirs):
   """
   Writes a store indicator file into staging directories.

   The store indicator is written into each of the staging directories when
   either a store or rebuild action has written the staging directory to disc.

   @param config: Config object.
   @param stagingDirs: Dictionary mapping directory path to date suffix.
   """
   for stagingDir in stagingDirs.keys():
      filename = os.path.join(stagingDir, STORE_INDICATOR)
      logger.debug("Writing store indicator [%s]." % filename)
      try:
         open(filename, "w").write("")
         changeOwnership(filename, config.options.backupUser, config.options.backupGroup)
      except Exception, e:
         logger.error("Error writing store indicator: %s" % e)


##############################
# consistencyCheck() function
##############################

def consistencyCheck(config, stagingDirs):
   """
   Runs a consistency check against media in the backup device.

   It seems that sometimes, it's possible to create a corrupted multisession
   disc (i.e. one that cannot be read) although no errors were encountered
   while writing the disc.  This consistency check makes sure that the data
   read from disc matches the data that was used to create the disc.

   The function mounts the device at a temporary mount point in the working
   directory, and then compares the indicated staging directories in the
   staging directory and on the media.  The comparison is done via
   functionality in C{filesystem.py}.

   If no exceptions are thrown, there were no problems with the consistency
   check.  A positive confirmation of "no problems" is also written to the log
   with C{info} priority.

   @warning: The implementation of this function is very UNIX-specific.

   @param config: Config object.
   @param stagingDirs: Dictionary mapping directory path to date suffix.

   @raise ValueError: If the two directories are not equivalent.
   @raise IOError: If there is a problem working with the media.
   """
   logger.debug("Running consistency check.")
   mountPoint = tempfile.mkdtemp(dir=config.options.workingDir)
   try:
      mount(config.store.devicePath, mountPoint, "iso9660")
      for stagingDir in stagingDirs.keys():
         discDir = os.path.join(mountPoint, stagingDirs[stagingDir])
         logger.debug("Checking [%s] vs. [%s]." % (stagingDir, discDir))
         compareContents(stagingDir, discDir, verbose=True)
         logger.info("Consistency check completed for [%s].  No problems found." % stagingDir)
   finally:
      unmount(mountPoint, True, 5, 1)  # try 5 times, and remove mount point when done


########################################################################
# Private utility functions
########################################################################

#########################
# _findCorrectDailyDir()
#########################

def _findCorrectDailyDir(options, config):
   """
   Finds the correct daily staging directory to be written to disk.

   In Cedar Backup v1.0, we assumed that the correct staging directory matched
   the current date.  However, that has problems.  In particular, it breaks
   down if collect is on one side of midnite and stage is on the other, or if
   certain processes span midnite.

   For v2.0, I'm trying to be smarter.  I'll first check the current day.  If
   that directory is found, it's good enough.  If it's not found, I'll look for
   a valid directory from the day before or day after I{which has not yet been
   staged, according to the stage indicator file}.  The first one I find, I'll
   use.  If I use a directory other than for the current day I{and}
   C{config.store.warnMidnite} is set, a warning will be put in the log.

   There is one exception to this rule.  If the C{options.full} flag is set,
   then the special "span midnite" logic will be disabled and any existing
   store indicator will be ignored.  I did this because I think that most users
   who run C{cback --full store} twice in a row expect the command to generate
   two identical discs.  With the other rule in place, running that command
   twice in a row could result in an error ("no unstored directory exists") or
   could even cause a completely unexpected directory to be written to disc (if
   some previous day's contents had not yet been written).

   @note: This code is probably longer and more verbose than it needs to be,
   but at least it's straightforward.

   @param options: Options object.
   @param config: Config object.

   @return: Correct staging dir, as a dict mapping directory to date suffix.
   @raise IOError: If the staging directory cannot be found.
   """
   oneDay = datetime.timedelta(days=1)
   today = datetime.date.today()
   yesterday = today - oneDay;
   tomorrow = today + oneDay;
   todayDate = today.strftime(DIR_TIME_FORMAT);
   yesterdayDate = yesterday.strftime(DIR_TIME_FORMAT);
   tomorrowDate = tomorrow.strftime(DIR_TIME_FORMAT);
   todayPath = os.path.join(config.stage.targetDir, todayDate)
   yesterdayPath = os.path.join(config.stage.targetDir, yesterdayDate)
   tomorrowPath = os.path.join(config.stage.targetDir, tomorrowDate)
   todayStageInd = os.path.join(todayPath, STAGE_INDICATOR)
   yesterdayStageInd = os.path.join(yesterdayPath, STAGE_INDICATOR)
   tomorrowStageInd = os.path.join(tomorrowPath, STAGE_INDICATOR)
   todayStoreInd = os.path.join(todayPath, STORE_INDICATOR)
   yesterdayStoreInd = os.path.join(yesterdayPath, STORE_INDICATOR)
   tomorrowStoreInd = os.path.join(tomorrowPath, STORE_INDICATOR)
   if options.full:
      if os.path.isdir(todayPath) and os.path.exists(todayStageInd):
         logger.info("Store process will use current day's stage directory [%s]" % todayPath)
         return { todayPath:todayDate }
      raise IOError("Unable to find staging directory to store (only tried today due to full option).")
   else:
      if os.path.isdir(todayPath) and os.path.exists(todayStageInd) and not os.path.exists(todayStoreInd):
         logger.info("Store process will use current day's stage directory [%s]" % todayPath)
         return { todayPath:todayDate }
      elif os.path.isdir(yesterdayPath) and os.path.exists(yesterdayStageInd) and not os.path.exists(yesterdayStoreInd):
         logger.info("Store process will use previous day's stage directory [%s]" % yesterdayPath)
         if config.store.warnMidnite:
            logger.warn("Warning: store process crossed midnite boundary to find data.")
         return { yesterdayPath:yesterdayDate }
      elif os.path.isdir(tomorrowPath) and os.path.exists(tomorrowStageInd) and not os.path.exists(tomorrowStoreInd):
         logger.info("Store process will use next day's stage directory [%s]" % tomorrowPath)
         if config.store.warnMidnite:
            logger.warn("Warning: store process crossed midnite boundary to find data.")
         return { tomorrowPath:tomorrowDate }
      raise IOError("Unable to find unused staging directory to store (tried today, yesterday, tomorrow).")


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
      return MEDIA_DVDPLUSR
   else:
      raise ValueError("Media type [%s] is not valid." % mediaType)

