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
# Copyright (c) 2004-2005 Kenneth J. Pronovici.
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
# Purpose  : Provides process-related objects.
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# This file was created with a width of 132 characters, and NO tabs.

########################################################################
# Module documentation
########################################################################

"""
Provides process-related objects.

The command-line interface is mostly implemented in terms of these process
functions.  There is one process function for each high-level backup action
(collect, stage, store, purge, rebuild).  In turn, each of the process
functions is mostly implemented in terms of lower-level functionality in the
other Cedar Backup modules.  This is mostly "glue" code.

@sort: executeCollect, executeStage, executeStore, executePurge, executeRebuild

@author: Kenneth J. Pronovici <pronovic@ieee.org>
"""


########################################################################
# Imported modules
########################################################################

# System modules
import os
import time
import re
import logging
import pickle

# Cedar Backup modules
from CedarBackup2.filesystem import BackupFileList


########################################################################
# Module-wide constants and variables
########################################################################

logger = logging.getLogger("CedarBackup2.log.process")

COLLECT_INDICATOR = "cback.collect"
STAGE_INDICATOR   = "cback.stage"
DIGEST_EXTENSION  = ".sha"

MEDIA_VOLUME_NAME = "Cedar Backup"    # must be 32 or fewer characters long


########################################################################
# Utility functions
########################################################################

###########################
# _getDayOfWeek() function
###########################

def _getDayOfWeek(dayName):
   """
   Converts English day name to numeric day of week as from C{time.localtime}.

   For instance, the day C{monday} would be converted to the number C{0}.

   @param dayName: Day of week to convert
   @type dayName: string, i.e. C{"monday"}, C{"tuesday"}, etc.

   @returns: Day of week convered to integer (C{0}=C{"monday"}, C{6}=C{"sunday"})
   """
   if dayName.lower() == "monday":
      return 0
   elif dayName.lower() == "tuesday":
      return 1
   elif dayName.lower() == "wednesday":
      return 2
   elif dayName.lower() == "thursday":
      return 3
   elif dayName.lower() == "friday":
      return 4
   elif dayName.lower() == "saturday":
      return 5
   elif dayName.lower() == "sunday":
      return 6
   else:
      return -1  # What else can we do??


###########################
# _todayIsStart() function
###########################

def _todayIsStart(startingDay):
   """
   Indicates whether "today" is the backup starting day per configuration.

   If the current day's English name matches the indicated starting day, then
   today is a starting day.

   @param startingDay: Configured starting day.
   @type startingDay: string, i.e. C{"monday"}, C{"tuesday"}, etc.

   @return: Boolean indicating whether today is the starting day.
   """
   return time.localtime().tm_wday == _getDayOfWeek(startingDay)


################################
# _getNormalizedPath() function
################################

def _getNormalizedPath(absPath):
   """
   Returns a "normalized" path based on an absolute path.

   A "normalized" path has its leading C{'/'} character removed, and then
   converts all remaining whitespace and C{'/'} characters to the C{'_'}
   character.  

   @param absPath: Absolute path

   @return: Normalized path.
   """
   normalized = absPath
   normalized = re.sub("^\/", "", normalized)
   normalized = re.sub("\/", "-", normalized)
   normalized = re.sub("\s", "_", normalized)
   return normalized


########################################################################
# Public functions
########################################################################

############################
# executeCollect() function
############################

def executeCollect(config, fullBackup=False):
   """
   Executes the collect backup action.

   If the C{fullBackup} argument is passed in as C{True}, then all files and
   directories will be backed up, regardless of whether they are flagged as
   daily, weekly or incremental.  This would most often be used to implement a
   "do a full backup now" override switch (i.e. "--full").

   @param config: Program configuration.
   @type config: Config object.

   @param fullBackup: Indicates whether full backup should be performed.
   @type fullBackup: Boolean value.

   @raise ValueError: Under many generic error conditions
   @raise TarError: If there is a problem creating the tar file
   """
   if config.options is None or config.collect is None:
      raise ValueError("Configuration is not properly filled in.")
   todayIsStart = _todayIsStart(config.options.startingDay)
   resetDigest = fullBackup or todayIsStart
   if config.collect.collectDirs is not None:
      for collectDir in config.collect.collectDirs:
         collectMode = _getCollectMode(collectDir, config.collect)
         archiveMode = _getArchiveMode(collectDir, config.collect)
         digestPath = _getDigestPath(collectDir, config.options.workingDir)
         tarfilePath = _getTarfilePath(collectDir, archiveMode, config.collect.targetDir)
         if fullBackup or collectMode in ['daily', 'incr', ] or (collectMode == 'weekly' and todayIsStart):
            _collectDirectory(collectDir.absolutePath, tarfilePath, collectMode, archiveMode, resetDigest, digestPath)
         logger.info("Completed collecting directory: %s" % collectDir.absolutePath)
   _writeCollectIndicator(config.collect.targetDir)
   logger.info("Executed the 'collect' action successfully.")

def _getCollectMode(collectDir, collectConfig):
   """
   Gets the collect mode that should be used for a collect directory.
   @param collectDir: Collect directory object.
   @param collectConfig: Collect configuration object.
   @return: Collect mode to use.
   """
   if collectDir.collectMode is None:
      return collectConfig.collectMode
   return collectDir.collectMode

def _getArchiveMode(collectDir, collectConfig):
   """
   Gets the archive mode that should be used for a collect directory.
   @param collectDir: Collect directory object.
   @param collectConfig: Collect configuration object.
   @return: Archive mode to use.
   """
   if collectDir.archiveMode is None:
      return collectConfig.archiveMode
   return collectDir.archiveMode

def _getDigestPath(collectDir, workingDir):
   """
   Gets the digest path associated with a collect directory.
   @param collectDir: Collect directory object.
   @param workingDir: Configured working directory.
   @return: Absolute path to the digest associated with the collect directory.
   """
   normalized = _getNormalizedPath(collectDir.absolutePath)
   filename = "%s.%s" % (normalized, DIGEST_EXTENSION)
   return os.path.join(workingDir, filename)

def _getTarfilePath(collectDir, archiveMode, targetDir):
   """
   Gets the tarfile path (including correct extension) associated with a collect directory.
   @param collectDir: Collect directory object.
   @param archiveMode: Archive mode to use for this tarfile.
   @param targetDir: Configured target directory
   @return: Absolute path to the tarfile associated with the collect directory.
   """
   extension = ""
   if archiveMode == 'tar':
      extension = ".tar"
   elif archiveMode == 'targz':
      extension = ".tar.gz"
   elif archiveMode == 'tarbz2':
      extension = ".tar.bz2"
   normalized = _getNormalizedPath(collectDir.absolutePath)
   filename = "%s%s" % (normalized, extension)
   return os.path.join(targetDir, filename)

def _collectDirectory(absolutePath, tarfilePath, collectMode, archiveMode, resetDigest, digestPath):
   """
   Collects a directory.
   
   The indicated collect directory is collected into the indicated tarfile.
   For directories that are collected incrementally, we'll use the indicated
   digest path and pay attention to the reset digest flag (basically, the reset
   digest flag ignores any existing digest, but a new digest is always
   rewritten).

   The caller must decide what the collect and archive modes are, since they
   can be on both the collect configuration and the collect directory itself.
   The passed-in values are always used rather than looking on the collect
   directory.

   @param absolutePath: Absolute path of directory to collect.
   @param tarfilePath: Path to tarfile that should be created.
   @param collectMode: Collect mode to use
   @param archiveMode: Archive mode to use
   @param resetDigest: Reset digest flag
   @param digestPath: Path to digest file on disk, if needed.
   """
   backupList = BackupFileList()
   backupList.addDirContents(absolutePath)
   if collectMode != 'incr':
      backupList.generateTarfile(tarfilePath, archiveMode, True)
   else:
      digest = {}
      if not resetDigest:
         digest = _loadDigest(digestPath)
         backupList.removeUnchanged(digest)
      backupList.generateTarfile(tarfilePath, archiveMode, True)
      digest = backupList.generateDigestMap()
      _writeDigest(digest, digestPath)

def _loadDigest(digestPath):
   """
   Loads the indicated digest path from disk into a dictionary.

   If we can't load the digest successfully (either because it doesn't exist or
   for some other reason), then an empty dictionary will be returned (but the
   condition will be logged).

   @param digestPath: Path to the digest file on disk.

   @return: Dictionary representing contents of digest path.
   """
   if not os.path.isfile(digestPath):
      logger.debug("Digest %s does not exist on disk." % digestPath)
      return {}
   else:
      try: 
         return pickle.load(open(digestPath, "r"))
      except: 
         logger.error("Failed loading digest %s from disk." % digestPath)
         return {}

def _writeDigest(digest, digestPath):
   """
   Writes the digest dictionary to the indicated digest path on disk.

   If we can't write the digest successfully for any reason, we'll log the
   condition but won't throw an exception.

   @param digest: Digest dictionary to write to disk.
   @param digestPath: Path to the digest file on disk.
   """
   try: 
      pickle.dump(digest, open(digestPath, "w"))
   except: 
      logger.error("Failed to write digest %s to disk." % digestPath)

def _writeCollectIndicator(targetDir):
   """
   Writes a collect indicator file into a target collect directory.
   @param targetDir: Target directory to write indicator into.
   """
   filename = os.path.join(targetDir, COLLECT_INDICATOR)
   open(filename, "w").write("")


##########################
# executeStage() function
##########################

def executeStage(config):
   """
   Executes the stage backup action.

   @param config: Program configuration.
   @type config: Config object.
   """
   logger.info("Executed the 'stage' action successfully.")


##########################
# executeStore() function
##########################

def executeStore(config, rebuildMedia=False):
   """
   Executes the store backup action.

   If the C{rebuildMedia} argument is passed in as C{True}, then the media
   will be wiped and rebuilt from scratch, regardless of other configuration.
   This would most often be used to implement a "do a full backup now" override
   switch (i.e. "--full").

   @param config: Program configuration.
   @type config: Config object.

   @param rebuildMedia: Indicates that new media should b
   @type rebuildMedia: Boolean value.
   """
   logger.info("Executed the 'store' action successfully.")


##########################
# executePurge() function
##########################

def executePurge(config):
   """
   Executes the purge backup action.

   @param config: Program configuration.
   @type config: Config object.
   """
   logger.info("Executed the 'purge' action successfully.")


############################
# executeRebuild() function
############################

def executeRebuild(config):
   """
   Executes the rebuild backup action.

   This function exists mainly to recreate a disc that has been "trashed" due
   to media or hardware problems.  Note that the "stage complete" indicator
   isn't checked for this action.

   @param config: Program configuration.
   @type config: Config object.
   """
   logger.info("Executed the 'rebuild' action successfully.")

