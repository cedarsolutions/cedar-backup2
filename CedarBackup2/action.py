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
# Purpose  : Provides implementation of various backup-related actions.
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# This file was created with a width of 132 characters, and NO tabs.

########################################################################
# Module documentation
########################################################################

"""
Provides implementation of various backup-related actions.

The command-line interface is mostly implemented in terms of the action-related
functionality in this module.  There is one process function for each
high-level backup action (collect, stage, store, purge, rebuild).  In turn,
each of the action functions is mostly implemented in terms of lower-level
functionality in the other Cedar Backup modules.  This is mostly "glue" code.

All of the public action functions in this file implements the Cedar Backup
Extension Architecture Interface, i.e. the same interface that extensions will
implement.  There's no particular reason it has to be this way, except that it
seems more straightforward to do it this way.

The code is organized into three rough sections: general utility code,
attribute "getter" functions, and public functions.  Attribute getter function
encode rules for getting the correct value for various attributes.  For
instance, what do we do when the device type is unset or if a collect dir
doesn't have an ignore file set, etc.  They are grouped roughly by the action
that they are associated with.  Other utility functions related to a single
public function are grouped with that function (below it, typically).  

@sort: executeCollect, executeStage, executeStore, executePurge, executeRebuild, executeValidate

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
import tempfile
import datetime

# Cedar Backup modules
from CedarBackup2.peer import RemotePeer, LocalPeer
from CedarBackup2.image import IsoImage
from CedarBackup2.writer import CdWriter
from CedarBackup2.writer import MEDIA_CDR_74, MEDIA_CDRW_74, MEDIA_CDR_80, MEDIA_CDRW_80
from CedarBackup2.filesystem import BackupFileList, PurgeItemList, compareContents
from CedarBackup2.util import getUidGid, changeOwnership, mount, unmount
from CedarBackup2.util import getFunctionReference, deviceMounted, displayBytes
from CedarBackup2.config import DEFAULT_DEVICE_TYPE, DEFAULT_MEDIA_TYPE


########################################################################
# Module-wide constants and variables
########################################################################

logger = logging.getLogger("CedarBackup2.log.process")

PREFIX_TIME_FORMAT   = "%Y/%m/%d"
DIR_TIME_FORMAT      = "%Y/%m/%d"

COLLECT_INDICATOR    = "cback.collect"
STAGE_INDICATOR      = "cback.stage"
STORE_INDICATOR      = "cback.store"
DIGEST_EXTENSION     = "sha"

SECONDS_PER_DAY      = 60*60*24

MEDIA_VOLUME_NAME    = "Cedar Backup"    # must be 32 or fewer characters long


########################################################################
# Utility functions
########################################################################

##############################
# _deriveDayOfWeek() function
##############################

def _deriveDayOfWeek(dayName):
   """
   Converts English day name to numeric day of week as from C{time.localtime}.

   For instance, the day C{monday} would be converted to the number C{0}.

   @param dayName: Day of week to convert
   @type dayName: string, i.e. C{"monday"}, C{"tuesday"}, etc.

   @returns: Integer, where Monday is 0 and Sunday is 6.
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
      return -1  # What else can we do??  Thrown an exception, I guess.


###########################
# isStartOfWeek() function
###########################

def isStartOfWeek(startingDay):
   """
   Indicates whether "today" is the backup starting day per configuration.

   If the current day's English name matches the indicated starting day, then
   today is a starting day.

   @param startingDay: Configured starting day.
   @type startingDay: string, i.e. C{"monday"}, C{"tuesday"}, etc.

   @return: Boolean indicating whether today is the starting day.
   """
   value = time.localtime().tm_wday == _deriveDayOfWeek(startingDay)
   if value:
      logger.debug("Today is the start of the week.")
   else:
      logger.debug("Today is NOT the start of the week.")
   return value


#################################
# buildNormalizedPath() function
#################################

def buildNormalizedPath(absPath):
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
# Attribute "getter" functions
########################################################################

############################
# getCollectMode() function
############################

def _getCollectMode(config, collectDir):
   """
   Gets the collect mode that should be used for a collect directory.
   Use directory's if possible, otherwise take from collect section.
   @param config: Config object.
   @param collectDir: Collect directory object.
   @return: Collect mode to use.
   """
   if collectDir.collectMode is None:
      collectMode = config.collect.collectMode
   else:
      collectMode = collectDir.collectMode
   logger.debug("Collect mode is [%s]" % collectMode)
   return collectMode


#############################
# _getArchiveMode() function
#############################

def _getArchiveMode(config, collectDir):
   """
   Gets the archive mode that should be used for a collect directory.
   Use directory's if possible, otherwise take from collect section.
   @param config: Config object.
   @param collectDir: Collect directory object.
   @return: Archive mode to use.
   """
   if collectDir.archiveMode is None:
      archiveMode = config.collect.archiveMode
   else:
      archiveMode = collectDir.archiveMode
   logger.debug("Archive mode is [%s]" % archiveMode)
   return archiveMode


############################
# _getIgnoreFile() function
############################

def _getIgnoreFile(config, collectDir):
   """
   Gets the ignore file that should be used for a collect directory.
   Use directory's if possible, otherwise take from collect section.
   @param config: Config object.
   @param collectDir: Collect directory object.
   @return: Ignore file to use.
   """
   if collectDir.ignoreFile is None:
      ignoreFile = config.collect.ignoreFile
   else:
      ignoreFile = collectDir.ignoreFile
   logger.debug("Ignore file is [%s]" % ignoreFile)
   return ignoreFile


############################
# _getDigestPath() function
############################

def _getDigestPath(config, collectDir):
   """
   Gets the digest path associated with a collect directory.
   @param config: Config object.
   @param collectDir: Collect directory object.
   @return: Absolute path to the digest associated with the collect directory.
   """
   normalized = buildNormalizedPath(collectDir.absolutePath)
   filename = "%s.%s" % (normalized, DIGEST_EXTENSION)
   digestPath = os.path.join(config.options.workingDir, filename)
   logger.debug("Digest path is [%s]" % digestPath)
   return digestPath


#############################
# _getTarfilePath() function
#############################

def _getTarfilePath(config, collectDir, archiveMode):
   """
   Gets the tarfile path (including correct extension) associated with a collect directory.
   @param config: Config object.
   @param collectDir: Collect directory object.
   @param archiveMode: Archive mode to use for this tarfile.
   @return: Absolute path to the tarfile associated with the collect directory.
   """
   if archiveMode == 'tar':
      extension = "tar"
   elif archiveMode == 'targz':
      extension = "tar.gz"
   elif archiveMode == 'tarbz2':
      extension = "tar.bz2"
   normalized = buildNormalizedPath(collectDir.absolutePath)
   filename = "%s.%s" % (normalized, extension)
   tarfilePath = os.path.join(config.collect.targetDir, filename)
   logger.debug("Tarfile path is [%s]" % tarfilePath)
   return tarfilePath


############################
# _getExclusions() function
############################

def _getExclusions(config, collectDir):
   """
   Gets exclusions (file and patterns) associated with a collect directory.

   The returned files value is a list of absolute paths to be excluded from the
   backup for a given directory.  It is derived from the collect configuration
   absolute exclude paths and the collect directory's absolute and relative
   exclude paths.  
   
   The returned patterns value is a list of patterns to be excluded from the
   backup for a given directory.  It is derived from the list of patterns from
   the collect configuration and from the collect directory itself.

   @param config: Config object.
   @param collectDir: Collect directory object.

   @return: Tuple (files, patterns) indicating what to exclude.
   """
   paths = []
   if config.collect.absoluteExcludePaths is not None:
      paths.extend(config.collect.absoluteExcludePaths)
   if collectDir.absoluteExcludePaths is not None:
      paths.extend(collectDir.absoluteExcludePaths)
   if collectDir.relativeExcludePaths is not None:
      for relativePath in collectDir.relativeExcludePaths:
         paths.append(os.path.join(collectDir.absolutePath, relativePath))
   patterns = []
   if config.collect.excludePatterns is not None:
      patterns.extend(config.collect.excludePatterns)
   if collectDir.excludePatterns is not None:
      patterns.extend(collectDir.excludePatterns)
   logger.debug("Exclude paths: %s" % paths)
   logger.debug("Exclude patterns: %s" % patterns)
   return(paths, patterns)


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

   Once we figure out what configuration value to use, we return a media
   type value that is valid in C{writer.py}, one of C{MEDIA_CDR_74},
   C{MEDIA_CDRW_74}, C{MEDIA_CDR_80} or C{MEDIA_CDRW_80}.

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
   else:
      raise ValueError("Media type [%s] is not valid." % mediaType)


########################
# _getWriter() function
########################

def _getWriter(config):
   """
   Gets a writer object based on current configuration.

   This function creates and returns a writer based on configuration.  This is
   done to abstract action methods from knowing what kind of writer is in use.
   Since all writers implement the same interface, there's no need for actions
   to care which one they're working with.
   
   Right now, only the C{cdwriter} device type is allowed, which results in a
   L{CdWriter} object.  An exception will be raised if any other device type is
   used.

   This function also checks to make sure that the device isn't mounted before
   creating a writer object for it.  Experience shows that sometimes if the
   device is mounted, we have problems with the backup.  We may as well do the
   check here first, before instantiating the writer.

   @param config: Config object.

   @return: Writer that can be used to write a directory to some media.

   @raise ValueError: If there is a problem getting the writer.
   @raise IOError: If there is a problem creating the writer object.
   """
   deviceType = _getDeviceType(config)
   mediaType = _getMediaType(config)
   if deviceMounted(config.store.devicePath):
      raise IOError("Device [%s] is currently mounted." % (config.store.devicePath))
   if deviceType == "cdwriter":
      return CdWriter(config.store.devicePath, config.store.deviceScsiId, config.store.driveSpeed, mediaType)
   else:
      raise ValueError("Device type [%s] is invalid." % config.store.deviceType)


########################################################################
# Public functions
########################################################################

############################
# executeCollect() function
############################

def executeCollect(configPath, options, config):
   """
   Executes the collect backup action.

   @note: When the collect action is complete, we will write a collect
   indicator to the collect directory, so it's obvious that the collect action
   has completed.  The stage process uses this indicator to decide whether a 
   peer is ready to be staged.

   @param configPath: Path to configuration file on disk.
   @type configPath: String representing a path on disk.

   @param options: Program command-line options.
   @type options: Options object.

   @param config: Program configuration.
   @type config: Config object.

   @raise ValueError: Under many generic error conditions
   @raise TarError: If there is a problem creating a tar file
   """
   logger.debug("Executing collect action.")
   if config.options is None or config.collect is None:
      raise ValueError("Collect configuration is not properly filled in.")
   fullBackup = options.full
   logger.debug("Full backup flag is [%s]" % fullBackup)
   todayIsStart = isStartOfWeek(config.options.startingDay)
   resetDigest = fullBackup or todayIsStart
   logger.debug("Reset digest flag is [%s]" % resetDigest)
   if config.collect.collectDirs is not None:
      for collectDir in config.collect.collectDirs:
         logger.debug("Working with collect directory [%s]" % collectDir.absolutePath)
         collectMode = _getCollectMode(config, collectDir)
         archiveMode = _getArchiveMode(config, collectDir)
         ignoreFile = _getIgnoreFile(config, collectDir)
         digestPath = _getDigestPath(config, collectDir)
         tarfilePath = _getTarfilePath(config, collectDir, archiveMode)
         (excludePaths, excludePatterns) = _getExclusions(config, collectDir)
         if fullBackup or (collectMode in ['daily', 'incr', ]) or (collectMode == 'weekly' and todayIsStart):
            logger.debug("Directory meets criteria to be backed up today.")
            _collectDirectory(config, collectDir.absolutePath, tarfilePath, 
                              collectMode, archiveMode, ignoreFile, resetDigest, 
                              digestPath, excludePaths, excludePatterns)
         else:
            logger.debug("Directory will not be backed up, per collect mode.")
         logger.info("Completed collecting directory [%s]" % collectDir.absolutePath)
   _writeCollectIndicator(config)
   logger.info("Executed the 'collect' action successfully.")

def _collectDirectory(config, absolutePath, tarfilePath, collectMode, archiveMode, 
                      ignoreFile, resetDigest, digestPath, excludePaths, excludePatterns):
   """
   Collects a directory.
   
   The indicated collect directory is collected into the indicated tarfile.
   For directories that are collected incrementally, we'll use the indicated
   digest path and pay attention to the reset digest flag (basically, the reset
   digest flag ignores any existing digest, but a new digest is always
   rewritten).

   The caller must decide what the collect and archive modes are, since they
   can be on both the collect configuration and the collect directory itself.
   The passed-in values are always used rather than looking in the collect
   directory.

   @param config: Config object.
   @param absolutePath: Absolute path of directory to collect.
   @param tarfilePath: Path to tarfile that should be created.
   @param collectMode: Collect mode to use.
   @param archiveMode: Archive mode to use.
   @param ignoreFile: Ignore file to use.
   @param resetDigest: Reset digest flag.
   @param digestPath: Path to digest file on disk, if needed.
   @param excludePaths: List of absolute paths to exclude.
   @param excludePatterns: List of patterns to exclude.
   """
   backupList = BackupFileList()
   backupList.ignoreFile = ignoreFile
   backupList.excludePaths = excludePaths
   backupList.excludePatterns = excludePatterns
   backupList.addDirContents(absolutePath)
   if collectMode != 'incr':
      logger.debug("Collect mode is [%s]; no digest will be used." % collectMode)
      logger.info("Backing up %d files in [%s] (%s)." % (len(backupList), absolutePath, displayBytes(backupList.totalSize())))
      if len(backupList) > 0:
         backupList.generateTarfile(tarfilePath, archiveMode, True)
         changeOwnership(tarfilePath, config.options.backupUser, config.options.backupGroup)
   else:
      if resetDigest:
         logger.debug("Based on resetDigest flag, digest will be cleared.")
         oldDigest = {}
      else:
         logger.debug("Based on resetDigest flag, digest will loaded from disk.")
         oldDigest = _loadDigest(digestPath)
      newDigest = backupList.generateDigestMap()   # be sure to do this before removing unchanged files!
      removed = backupList.removeUnchanged(oldDigest)
      logger.debug("Removed %d unchanged files based on digest values." % removed)
      logger.info("Backing up %d files in [%s] (%s)." % (len(backupList), absolutePath, displayBytes(backupList.totalSize())))
      if len(backupList) > 0:
         backupList.generateTarfile(tarfilePath, archiveMode, True)
         changeOwnership(tarfilePath, config.options.backupUser, config.options.backupGroup)
      _writeDigest(config, newDigest, digestPath)

def _loadDigest(digestPath):
   """
   Loads the indicated digest path from disk into a dictionary.

   If we can't load the digest successfully (either because it doesn't exist or
   for some other reason), then an empty dictionary will be returned - but the
   condition will be logged.

   @param digestPath: Path to the digest file on disk.

   @return: Dictionary representing contents of digest path.
   """
   if not os.path.isfile(digestPath):
      digest = {}
      logger.debug("Digest [%s] does not exist on disk." % digestPath)
   else:
      try: 
         digest = pickle.load(open(digestPath, "r"))
         logger.debug("Loaded digest [%s] from disk: %d entries." % (digestPath, len(digest)))
      except: 
         digest = {}
         logger.error("Failed loading digest [%s] from disk." % digestPath)
   return digest

def _writeDigest(config, digest, digestPath):
   """
   Writes the digest dictionary to the indicated digest path on disk.

   If we can't write the digest successfully for any reason, we'll log the
   condition but won't throw an exception.

   @param config: Config object.
   @param digest: Digest dictionary to write to disk.
   @param digestPath: Path to the digest file on disk.
   """
   try: 
      pickle.dump(digest, open(digestPath, "w"))
      changeOwnership(digestPath, config.options.backupUser, config.options.backupGroup)
      logger.debug("Wrote new digest [%s] to disk: %d entries." % (digestPath, len(digest)))
   except: 
      logger.error("Failed to write digest [%s] to disk." % digestPath)

def _writeCollectIndicator(config):
   """
   Writes a collect indicator file into a target collect directory.
   @param config: Config object.
   """
   filename = os.path.join(config.collect.targetDir, COLLECT_INDICATOR)
   logger.debug("Writing collect indicator [%s]." % filename)
   try:
      open(filename, "w").write("")
      changeOwnership(filename, config.options.backupUser, config.options.backupGroup)
   except Exception, e:
      logger.error("Error writing collect indicator: %s" % e)


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


##########################
# executeStore() function
##########################

def executeStore(configPath, options, config):
   """
   Executes the store backup action.

   Note that the rebuild action and the store action are very similar.  The
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
   if config.options is None or config.store is None:
      raise ValueError("Store configuration is not properly filled in.")
   rebuildMedia = options.full
   logger.debug("Rebuild media flag [%s]" % rebuildMedia)
   todayIsStart = isStartOfWeek(config.options.startingDay)
   entireDisc = rebuildMedia or todayIsStart
   logger.debug("Entire disc flag [%s]" % entireDisc)
   stagingDirs = _findCorrectDailyDir(options, config)
   _writeImage(config, entireDisc, stagingDirs)
   if config.store.checkData:
      logger.debug("Running consistency check of media.")
      _consistencyCheck(config, stagingDirs)
   _writeStoreIndicator(config, stagingDirs)
   logger.info("Executed the 'store' action successfully.")

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

def _writeImage(config, entireDisc, stagingDirs):
   """
   Builds and writes an ISO image containing the indicated stage directories.

   The generated image will contain each of the staging directories listed in
   C{stagingDirs}.  The directories will be placed into the image at the root by
   date, so staging directory C{/opt/stage/2005/02/10} will be placed into the
   disc at C{/2005/02/10}.

   @param config: Config object.
   @param entireDisc: Indicates whether entire disc should be used
   @param stagingDirs: Dictionary mapping directory path to date suffix.

   @raise ValueError: Under many generic error conditions
   @raise IOError: If there is a problem writing the image to disc.
   """
   writer = _getWriter(config)
   capacity = writer.retrieveCapacity(entireDisc=entireDisc)
   logger.debug("Media capacity: %s" % displayBytes(capacity.bytesAvailable))
   image = IsoImage(writer.device, capacity.boundaries)
   for stageDir in stagingDirs.keys():
      logger.debug("Adding stage directory [%s]." % stageDir)
      dateSuffix = stagingDirs[stageDir]
      image.addEntry(path=stageDir, graftPoint=dateSuffix, contentsOnly=True)
   imageSize = image.getEstimatedSize()
   logger.info("Image size will be %s." % displayBytes(imageSize))
   if imageSize > capacity.bytesAvailable:
      logger.error("Image (%s) does not fit in available capacity (%s)." % (displayBytes(imageSize), 
                                                                            displayBytes(capacity.bytesAvailable)))
      raise IOError("Media does not contain enough capacity to store image.")
   try:
      (handle, imagePath) = tempfile.mkstemp(dir=config.options.workingDir)
      try:
         os.close(handle)
      except: pass
      image.writeImage(imagePath)
      logger.debug("Completed creating image.")
      writer.writeImage(imagePath, entireDisc)
      logger.debug("Completed writing image to disc.")
   finally:
      if os.path.exists(imagePath): 
         try:
            os.unlink(imagePath)
         except: pass

def _consistencyCheck(config, stagingDirs):
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

   @warning: The implementation of this function is very UNIX-specific and is
   probably Linux-specific as well.

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

def _writeStoreIndicator(config, stagingDirs):
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


##########################
# executePurge() function
##########################

def executePurge(configPath, options, config):
   """
   Executes the purge backup action.

   For each configured directory, we create a purge item list, remove from the
   list anything that's younger than the configured retain days value, and then
   purge from the filesystem what's left.

   @param configPath: Path to configuration file on disk.
   @type configPath: String representing a path on disk.

   @param options: Program command-line options.
   @type options: Options object.

   @param config: Program configuration.
   @type config: Config object.

   @raise ValueError: Under many generic error conditions
   """
   logger.debug("Executing purge action.")
   if config.options is None or config.purge is None:
      raise ValueError("Purge configuration is not properly filled in.")
   if config.purge.purgeDirs is not None:
      for purgeDir in config.purge.purgeDirs:
         purgeList = PurgeItemList()
         purgeList.addDirContents(purgeDir.absolutePath)  # add everything within directory
         purgeList.removeYoungFiles(purgeDir.retainDays)  # remove young files *from the list* so they won't be purged
         purgeList.purgeItems()                           # remove remaining items from the filesystem
   logger.info("Executed the 'purge' action successfully.")


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
   logger.debug("Executing rebuild action.")
   if config.options is None or config.store is None:
      raise ValueError("Rebuild configuration is not properly filled in.")
   stagingDirs = _findRebuildDirs(config)
   _writeImage(config, True, stagingDirs)
   if config.store.checkData:
      logger.debug("Running consistency check of media.")
      _consistencyCheck(config, stagingDirs)
   _writeStoreIndicator(config, stagingDirs)
   logger.info("Executed the 'rebuild' action successfully.")

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
   start = _deriveDayOfWeek(config.options.startingDay)
   today = datetime.date.today()
   if today.weekday() >= start:
      days = today.weekday() - start + 1
   else:
      days = 7 - (start - today.weekday()) + 1
   for i in range (0, days):
      currentDay = today - datetime.timedelta(days=i)
      dateSuffix = currentDay.strftime(DIR_TIME_FORMAT)
      stageDir = os.path.join(config.stage.targetDir, dateSuffix)
      indicator = os.path.join(stageDir, STAGE_INDICATOR)
      if os.path.isdir(stageDir) and os.path.exists(indicator):
         logger.info("Rebuild process will include stage directory [%s]" % stageDir)
         stagingDirs[stageDir] = dateSuffix
   if len(stagingDirs) == 0:
      raise IOError("Unable to find any staging directories for rebuild process.")
   return stagingDirs


#############################
# executeValidate() function
#############################

def executeValidate(configPath, options, config):
   """
   Executes the validate action.

   This action validates each of the individual sections in the config file.
   This is a "runtime" validation.  The config file itself is already valid in
   a structural sense, so what we check here that is that we can actually use
   the configuration without any problems.

   There's a separate validation function for each of the configuration
   sections.  Each validation function returns a true/false indication for
   whether configuration was valid, and then logs any configuration problems it
   finds.  This way, one pass over configuration indicates most or all of the
   obvious problems, rather than finding just one problem at a time.

   Any reported problems will be logged at the ERROR level normally, or at the
   INFO level if the quiet flag is enabled.

   @param configPath: Path to configuration file on disk.
   @type configPath: String representing a path on disk.

   @param options: Program command-line options.
   @type options: Options object.

   @param config: Program configuration.
   @type config: Config object.

   @raise ValueError: If some configuration value is invalid.
   """
   logger.debug("Executing validate action.")
   if options.quiet:
      logfunc = logger.info   # info so it goes to the log
   else:
      logfunc = logger.error  # error so it goes to the screen
   valid = True
   valid &= _validateReference(config, logfunc)
   valid &= _validateOptions(config, logfunc)
   valid &= _validateCollect(config, logfunc)
   valid &= _validateStage(config, logfunc)
   valid &= _validateStore(config, logfunc)
   valid &= _validatePurge(config, logfunc)
   valid &= _validateExtensions(config, logfunc)
   if valid:
      logfunc("Configuration is valid.")
   else:
      logfunc("Configuration is not valid.")

def _validateReference(config, logfunc):
   """
   Execute runtime validations on reference configuration.

   We only validate that reference configuration exists at all.

   @param config: Program configuration.
   @param logfunc: Function to use for logging errors

   @return: True if configuration is valid, false otherwise.
   """
   valid = True
   if config.reference is None:
      logfunc("Required reference configuration does not exist.")
      valid = False
   return valid

def _validateOptions(config, logfunc):
   """
   Execute runtime validations on options configuration.

   The following validations are enforced:

      - The options section must exist
      - The working directory must exist and must be writable
      - The backup user and backup group must exist

   @param config: Program configuration.
   @param logfunc: Function to use for logging errors

   @return: True if configuration is valid, false otherwise.
   """
   valid = True
   if config.options is None:
      logfunc("Required options configuration does not exist.")
      valid = False
   else:
      valid &= _checkDir(config.options.workingDir, True, logfunc, "Working directory")
      try:
         getUidGid(config.options.backupUser, config.options.backupGroup)
      except ValueError:
         logfunc("Backup user:group [%s:%s] invalid." % (config.options.backupUser, config.options.backupGroup))
         valid = False
   return valid

def _validateCollect(config, logfunc):
   """
   Execute runtime validations on collect configuration.

   The following validations are enforced:

      - The target directory must exist and must be writable
      - Each of the individual collect directories must exist and must be readable

   @param config: Program configuration.
   @param logfunc: Function to use for logging errors

   @return: True if configuration is valid, false otherwise.
   """
   valid = True
   if config.collect is not None:
      valid &= _checkDir(config.collect.targetDir, True, logfunc, "Collect target directory")
      if config.collect.collectDirs is not None:
         for collectDir in config.collect.collectDirs:
            valid &= _checkDir(collectDir.absolutePath, False, logfunc, "Collect directory")
   return valid

def _validateStage(config, logfunc):
   """
   Execute runtime validations on stage configuration.

   The following validations are enforced:

      - The target directory must exist and must be writable
      - Each local peer's collect directory must exist and must be readable

   @note: We currently do not validate anything having to do with remote peers,
   since we don't have a straightforward way of doing it.  It would require
   adding an rsh command rather than just an rcp command to configuration, and
   that just doesn't seem worth it right now.

   @param config: Program configuration.
   @param logfunc: Function to use for logging errors

   @return: True if configuration is valid, False otherwise.
   """
   valid = True
   if config.stage is not None:
      valid &= _checkDir(config.stage.targetDir, True, logfunc, "Stage target dir ")
      if config.stage.localPeers is not None:
         for peer in config.stage.localPeers:
            valid &= _checkDir(peer.collectDir, False, logfunc, "Local peer collect dir ")
   return valid

def _validateStore(config, logfunc):
   """
   Execute runtime validations on store configuration.

   The following validations are enforced:

      - The source directory must exist and must be readable
      - The backup device (path and SCSI device) must be valid

   @param config: Program configuration.
   @param logfunc: Function to use for logging errors

   @return: True if configuration is valid, False otherwise.
   """
   valid = True
   if config.store is not None:
      valid &= _checkDir(config.store.sourceDir, False, logfunc, "Store source directory")
      try:
         _getWriter(config)
      except ValueError:
         logfunc("Backup device [%s] [%s] is not valid." % (config.store.devicePath, config.store.deviceScsiId))
         valid = False
   return valid

def _validatePurge(config, logfunc):
   """
   Execute runtime validations on purge configuration.

   The following validations are enforced:

      - Each purge directory must exist and must be writable

   @param config: Program configuration.
   @param logfunc: Function to use for logging errors

   @return: True if configuration is valid, False otherwise.
   """
   valid = True
   if config.purge is not None:
      if config.purge.purgeDirs is not None:
         for purgeDir in config.purge.purgeDirs:
            valid &= _checkDir(purgeDir.absolutePath, True, logfunc, "Purge directory")
   return valid

def _validateExtensions(config, logfunc):
   """
   Execute runtime validations on extensions configuration.

   The following validations are enforced:

      - Each indicated extension function must exist.

   @param config: Program configuration.
   @param logfunc: Function to use for logging errors

   @return: True if configuration is valid, False otherwise.
   """
   valid = True
   if config.extensions is not None:
      if config.extensions.actions is not None:
         for action in config.extensions.actions:
            try:
               getFunctionReference(action.module, action.function)
            except ImportError:
               logfunc("Unable to find function [%s.%s]." % (action.module, action.function))
               valid = False
            except ValueError:
               logfunc("Function [%s.%s] is not callable." % (action.module, action.function))
               valid = False
   return valid

def _checkDir(path, writable, logfunc, prefix):
   """
   Checks that the indicated directory is OK.

   The path must exist, must be a directory, must be readable and executable,
   and must optionally be writable.

   @param path: Path to check.
   @param writable: Check that path is writable.
   @param logfunc: Function to use for logging errors.
   @param prefix: Prefix to use on logged errors.

   @return: True if the directory is OK, False otherwise.
   """
   if not os.path.exists(path):
      logfunc("%s [%s] does not exist." % (prefix, path))
      return False
   if not os.path.isdir(path):
      logfunc("%s [%s] is not a directory." % (prefix, path))
      return False
   if not os.access(path, os.R_OK):
      logfunc("%s [%s] is not readable." % (prefix, path))
      return False
   if not os.access(path, os.X_OK):
      logfunc("%s [%s] is not executable." % (prefix, path))
      return False
   if writable and not os.access(path, os.W_OK):
      logfunc("%s [%s] is not writable." % (prefix, path))
      return False
   return True

