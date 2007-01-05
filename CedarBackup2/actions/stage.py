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
# Purpose  : Implements the standard 'stage' action.
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

########################################################################
# Module documentation
########################################################################

"""
Implements the standard 'stage' action.
@sort: executeStage
@author: Kenneth J. Pronovici <pronovic@ieee.org>
"""


########################################################################
# Imported modules
########################################################################

# System modules
import os
import time
import logging

# Cedar Backup modules
from CedarBackup2.peer import RemotePeer, LocalPeer
from CedarBackup2.util import getUidGid, changeOwnership
from CedarBackup2.actions.constants import DIR_TIME_FORMAT, STAGE_INDICATOR


########################################################################
# Module-wide constants and variables
########################################################################

logger = logging.getLogger("CedarBackup2.log.actions.stage")


########################################################################
# Public functions
########################################################################

##########################
# executeStage() function
##########################

def executeStage(configPath, options, config):
   """
   Executes the stage backup action.

   @note: The daily directory is derived once and then we stick with it, just
   in case a backup happens to span midnite.

   @note: As portions of the stage action is complete, we will write various
   indicator files so that it's obvious what actions have been completed.  Each
   peer gets a stage indicator in its collect directory, and then the master
   gets a stage indicator in its daily staging directory.  The store process
   uses the master's stage indicator to decide whether a directory is ready to
   be stored.  Currently, nothing uses the indicator at each peer, and it
   exists for reference only. 

   @param configPath: Path to configuration file on disk.
   @type configPath: String representing a path on disk.

   @param options: Program command-line options.
   @type options: Options object.

   @param config: Program configuration.
   @type config: Config object.

   @raise ValueError: Under many generic error conditions
   @raise IOError: If there are problems reading or writing files.
   """
   logger.debug("Executing stage action.")
   if config.options is None or config.stage is None:
      raise ValueError("Stage configuration is not properly filled in.")
   dailyDir = _getDailyDir(config)
   localPeers = _getLocalPeers(config)
   remotePeers = _getRemotePeers(config)
   allPeers = localPeers + remotePeers
   stagingDirs = _createStagingDirs(config, dailyDir, allPeers)
   for peer in allPeers:
      logger.info("Staging peer [%s]." % peer.name)
      if not peer.checkCollectIndicator():
         logger.error("Peer [%s] was not ready to be staged." % peer.name)
         continue
      logger.debug("Found collect indicator.")
      targetDir = stagingDirs[peer.name]
      ownership = getUidGid(config.options.backupUser,  config.options.backupGroup)
      logger.debug("Using target dir [%s], ownership [%d:%d]." % (targetDir, ownership[0], ownership[1]))
      try:
         count = peer.stagePeer(targetDir=targetDir, ownership=ownership)  # note: utilize effective user's default umask
         logger.info("Staged %d files for peer [%s]." % (count, peer.name))
         peer.writeStageIndicator()
      except (ValueError, IOError, OSError), e:
         logger.error("Error staging [%s]: %s" % (peer.name, e))
   _writeStageIndicator(config, dailyDir)
   logger.info("Executed the 'stage' action successfully.")


########################################################################
# Private utility functions
########################################################################

################################
# _createStagingDirs() function
################################

def _createStagingDirs(config, dailyDir, peers):
   """
   Creates staging directories as required.
   
   The main staging directory is the passed in daily directory, something like
   C{staging/2002/05/23}.  Then, individual peers get their own directories,
   i.e. C{staging/2002/05/23/host}.

   @param config: Config object.
   @param dailyDir: Daily staging directory.
   @param peers: List of all configured peers.

   @return: Dictionary mapping peer name to staging directory.
   """
   mapping = {}
   if os.path.isdir(dailyDir):
      logger.warn("Staging directory [%s] already existed." % dailyDir)
   else:
      try:
         logger.debug("Creating staging directory [%s]." % dailyDir)
         os.makedirs(dailyDir)
         for path in [ dailyDir, os.path.join(dailyDir, ".."), os.path.join(dailyDir, "..", ".."), ]:
            changeOwnership(path, config.options.backupUser, config.options.backupGroup)
      except Exception, e:
         raise Exception("Unable to create staging directory: %s" % e)
   for peer in peers:
      peerDir = os.path.join(dailyDir, peer.name)
      mapping[peer.name] = peerDir
      if os.path.isdir(peerDir):
         logger.warn("Peer staging directory [%s] already existed." % peerDir)
      else:
         try:
            logger.debug("Creating peer staging directory [%s]." % peerDir)
            os.makedirs(peerDir)
            changeOwnership(peerDir, config.options.backupUser, config.options.backupGroup)
         except Exception, e:
            raise Exception("Unable to create staging directory: %s" % e)
   return mapping
      

##################################
# _writeStageIndicator() function
##################################

def _writeStageIndicator(config, dailyDir):
   """
   Writes a stage indicator file into the daily staging directory.

   Note that there is a stage indicator on each peer (to indicate that a
   collect directory has been staged) and in the daily staging directory itself
   (to indicate that the staging directory has been utilized).  This just deals
   with the daily staging directory.

   @param config: Config object.
   @param dailyDir: Daily staging directory.
   """
   filename = os.path.join(dailyDir, STAGE_INDICATOR)
   logger.debug("Writing stage indicator [%s]." % filename)
   try:
      open(filename, "w").write("")
      changeOwnership(filename, config.options.backupUser, config.options.backupGroup)
   except Exception, e:
      logger.error("Error writing stage indicator: %s" % e)


########################################################################
# Private attribute "getter" functions
########################################################################

##########################
# _getDailyDir() function
##########################

def _getDailyDir(config):
   """
   Gets the daily staging directory.

   This is just a directory in the form C{staging/YYYY/MM/DD}, i.e.
   C{staging/2000/10/07}, except it will be an absolute path based on
   C{config.stage.targetDir}.

   @param config: Config object

   @return: Path of daily staging directory.
   """
   dailyDir = os.path.join(config.stage.targetDir, time.strftime(DIR_TIME_FORMAT))
   logger.debug("Daily staging directory is [%s]." % dailyDir)
   return dailyDir


############################
# _getLocalPeers() function
############################

def _getLocalPeers(config):
   """
   Return a list of L{LocalPeer} objects based on configuration.
   @param config: Config object.
   @return: List of L{LocalPeer} objects.
   """
   localPeers = []
   if config.stage.localPeers is not None:
      for peer in config.stage.localPeers:
         localPeer = LocalPeer(peer.name, peer.collectDir)
         localPeers.append(localPeer)
         logger.debug("Found local peer: [%s]" % localPeer.name)
   return localPeers


#############################
# _getRemotePeers() function
#############################

def _getRemotePeers(config):
   """
   Return a list of L{RemotePeer} objects based on configuration.
   @param config: Config object.
   @return: List of L{RemotePeer} objects.
   """
   remotePeers = []
   if config.stage.remotePeers is not None:
      for peer in config.stage.remotePeers:
         remoteUser = _getRemoteUser(config, peer)
         rcpCommand = _getRcpCommand(config, peer)
         remotePeer = RemotePeer(peer.name, peer.collectDir, config.options.workingDir,
                                 remoteUser, rcpCommand, config.options.backupUser)
         remotePeers.append(remotePeer)
         logger.debug("Found remote peer: [%s]" % remotePeer.name)
   return remotePeers


############################
# _getRemoteUser() function
############################

def _getRemoteUser(config, remotePeer):
   """
   Gets the remote user associated with a remote peer.
   Use peer's if possible, otherwise take from options section.
   @param config: Config object.
   @param remotePeer: Configuration-style remote peer object.
   @return: Name of remote user associated with remote peer.
   """
   if remotePeer.remoteUser is None:
      return config.options.backupUser
   return remotePeer.remoteUser


############################
# _getRcpCommand() function
############################

def _getRcpCommand(config, remotePeer):
   """
   Gets the RCP command associated with a remote peer.
   Use peer's if possible, otherwise take from options section.
   @param config: Config object.
   @param remotePeer: Configuration-style remote peer object.
   @return: RCP command associated with remote peer.
   """
   if remotePeer.rcpCommand is None:
      return config.options.rcpCommand
   return remotePeer.rcpCommand

