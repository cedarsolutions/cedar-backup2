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

@sort: executeCollect, executeStage, executeStore, executePurge, executeRebuild

@author: Kenneth J. Pronovici <pronovic@ieee.org>
"""


########################################################################
# Imported modules
########################################################################

# System modules
import logging


########################################################################
# Module-wide constants and variables
########################################################################

logger = logging.getLogger("CedarBackup2.log.process")


########################################################################
# Public functions
########################################################################

def executeCollect(config, full):
   """
   Executes the collect backup action.

   @param config: Program configuration.
   @type config: Config object.

   @param full: Indicates whether full backup was flagged.
   @type full: Boolean value.
   """
   logger.info("Executing collect action.")

def executeStage(config, full):
   """
   Executes the stage backup action.

   @param config: Program configuration.
   @type config: Config object.

   @param full: Indicates whether full backup was flagged.
   @type full: Boolean value.
   """
   logger.info("Executing stage action.")

def executeStore(config, full):
   """
   Executes the store backup action.

   @param config: Program configuration.
   @type config: Config object.

   @param full: Indicates whether full backup was flagged.
   @type full: Boolean value.
   """
   logger.info("Executing store action.")

def executePurge(config, full):
   """
   Executes the purge backup action.

   @param config: Program configuration.
   @type config: Config object.

   @param full: Indicates whether full backup was flagged.
   @type full: Boolean value.
   """
   logger.info("Executing purge action.")

def executeRebuild(config, full):
   """
   Executes the rebuild backup action.

   @param config: Program configuration.
   @type config: Config object.

   @param full: Indicates whether full backup was flagged.
   @type full: Boolean value.
   """
   logger.info("Executing rebuild action.")

