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
# Purpose  : Implements the standard 'rebuild' action.
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

########################################################################
# Module documentation
########################################################################

"""
Implements the standard 'rebuild' action.
@sort: executeRebuild
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

# Cedar Backup modules
from CedarBackup2.util import deriveDayOfWeek
from CedarBackup2.actions.util import checkMediaState
from CedarBackup2.actions.constants import DIR_TIME_FORMAT, STAGE_INDICATOR
from CedarBackup2.actions.store import writeImage, writeStoreIndicator, consistencyCheck


########################################################################
# Module-wide constants and variables
########################################################################

logger = logging.getLogger("CedarBackup2.log.actions.rebuild")


########################################################################
# Public functions
########################################################################

############################
# executeRebuild() function
############################

def executeRebuild(configPath, options, config):
   """
   Executes the rebuild backup action.

   This function exists mainly to recreate a disc that has been "trashed" due
   to media or hardware problems.  Note that the "stage complete" indicator
   isn't checked for this action.

   Note that the rebuild action and the store action are very similar.  The
   main difference is that while store only stores a single day's staging
   directory, the rebuild action operates on multiple staging directories.

   @param configPath: Path to configuration file on disk.
   @type configPath: String representing a path on disk.

   @param options: Program command-line options.
   @type options: Options object.

   @param config: Program configuration.
   @type config: Config object.

   @raise ValueError: Under many generic error conditions
   @raise IOError: If there are problems reading or writing files.
   """
   logger.debug("Executing the 'rebuild' action.")
   if sys.platform == "darwin":
      logger.warn("Warning: the rebuild action is not fully supported on Mac OS X.")
      logger.warn("See the Cedar Backup software manual for further information.")
   if config.options is None or config.store is None:
      raise ValueError("Rebuild configuration is not properly filled in.")
   if config.store.checkMedia:
      checkMediaState(config.store.devicePath)
   stagingDirs = _findRebuildDirs(config)
   writeImage(config, True, stagingDirs)
   if config.store.checkData:
      if sys.platform == "darwin":
         logger.warn("Warning: consistency check cannot be run successfully on Mac OS X.")
         logger.warn("See the Cedar Backup software manual for further information.")
      else:
         logger.debug("Running consistency check of media.")
         consistencyCheck(config, stagingDirs)
   writeStoreIndicator(config, stagingDirs)
   logger.info("Executed the 'rebuild' action successfully.")


########################################################################
# Private utility functions
########################################################################

##############################
# _findRebuildDirs() function
##############################

def _findRebuildDirs(config):
   """
   Finds the set of directories to be included in a disc rebuild.

   A the rebuild action is supposed to recreate the "last week's" disc.  This
   won't always be possible if some of the staging directories are missing.
   However, the general procedure is to look back into the past no further than
   the previous "starting day of week", and then work forward from there trying
   to find all of the staging directories between then and now that still exist
   and have a stage indicator.

   @param config: Config object.

   @return: Correct staging dir, as a dict mapping directory to date suffix.
   @raise IOError: If we do not find at least one staging directory.
   """
   stagingDirs = {}
   start = deriveDayOfWeek(config.options.startingDay)
   today = datetime.date.today()
   if today.weekday() >= start:
      days = today.weekday() - start + 1
   else:
      days = 7 - (start - today.weekday()) + 1
   for i in range (0, days):
      currentDay = today - datetime.timedelta(days=i)
      dateSuffix = currentDay.strftime(DIR_TIME_FORMAT)
      stageDir = os.path.join(config.store.sourceDir, dateSuffix)
      indicator = os.path.join(stageDir, STAGE_INDICATOR)
      if os.path.isdir(stageDir) and os.path.exists(indicator):
         logger.info("Rebuild process will include stage directory [%s]" % stageDir)
         stagingDirs[stageDir] = dateSuffix
   if len(stagingDirs) == 0:
      raise IOError("Unable to find any staging directories for rebuild process.")
   return stagingDirs

