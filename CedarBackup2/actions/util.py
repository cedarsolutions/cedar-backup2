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
import logging

# Cedar Backup modules
from CedarBackup2.filesystem import FilesystemList
from CedarBackup2.util import changeOwnership
from CedarBackup2.actions.constants import INDICATOR_PATTERN


########################################################################
# Module-wide constants and variables
########################################################################

logger = logging.getLogger("CedarBackup2.log.actions.util")


########################################################################
# Public functions
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
   """
   filename = os.path.join(targetDir, indicatorFile)
   logger.debug("Writing indicator file [%s]." % filename)
   try:
      open(filename, "w").write("")
      changeOwnership(filename, backupUser, backupGroup)
   except Exception, e:
      logger.error("Error writing indicator file: %s" % e)


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

