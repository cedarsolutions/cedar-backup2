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
import tempfile

# Cedar Backup modules
from CedarBackup2.peer import RemotePeer, LocalPeer
from CedarBackup2.image import IsoImage
from CedarBackup2.writer import CdWriter
from CedarBackup2.filesystem import BackupFileList
from CedarBackup2.util import getUidGid


########################################################################
# Module-wide constants and variables
########################################################################

logger = logging.getLogger("CedarBackup2.log.process")

PREFIX_TIME_FORMAT   = "%Y/%m/%d"
DIR_TIME_FORMAT      = "%Y/%m/%d"

COLLECT_INDICATOR    = "cback.collect"
STAGE_INDICATOR      = "cback.stage"
STORE_INDICATOR      = "cback.store"
DIGEST_EXTENSION     = ".sha"

SECONDS_PER_DAY      = 60*60*24

MEDIA_VOLUME_NAME    = "Cedar Backup"    # must be 32 or fewer characters long


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

def _changeOwnership(user, group, path):
   """
   Changes ownership of path to match the user and group.
   @param user: User which owns file.
   @param group: Group which owns file.
   @param path: Path whose ownership to change.
   """
   try:
      (uid, gid) = getUidGid(user, group)
      os.chown(path, uid, gid)
   except Exception, e:
      logger.error("Error changing ownership of %s: %s" % (path, e))


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

   @note: When the collect action is complete, we will write a collect
   indicator to the collect directory, so it's obvious that the collect action
   has completed.  The stage process uses this indicator to decide whether a 
   peer is ready to be staged.

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
         collectMode = _getCollectMode(config, collectDir)
         archiveMode = _getArchiveMode(config, collectDir)
         digestPath = _getDigestPath(config, collectDir)
         tarfilePath = _getTarfilePath(config, collectDir, archiveMode)
         if fullBackup or collectMode in ['daily', 'incr', ] or (collectMode == 'weekly' and todayIsStart):
            _collectDirectory(config, collectDir.absolutePath, tarfilePath, collectMode, archiveMode, resetDigest, digestPath)
         logger.info("Completed collecting directory: %s" % collectDir.absolutePath)
   _writeCollectIndicator(config)
   logger.info("Executed the 'collect' action successfully.")

def _getCollectMode(config, collectDir):
   """
   Gets the collect mode that should be used for a collect directory.
   Use directory's if possible, otherwise take from collect section.
   @param config: Config object.
   @param collectDir: Collect directory object.
   @return: Collect mode to use.
   """
   if collectDir.collectMode is None:
      return config.collect.collectMode
   return collectDir.collectMode

def _getArchiveMode(config, collectDir):
   """
   Gets the archive mode that should be used for a collect directory.
   Use directory's if possible, otherwise take from collect section.
   @param config: Config object.
   @param collectDir: Collect directory object.
   @return: Archive mode to use.
   """
   if collectDir.archiveMode is None:
      return config.collect.archiveMode
   return collectDir.archiveMode

def _getDigestPath(config, collectDir):
   """
   Gets the digest path associated with a collect directory.
   @param config: Config object.
   @param collectDir: Collect directory object.
   @return: Absolute path to the digest associated with the collect directory.
   """
   normalized = _getNormalizedPath(collectDir.absolutePath)
   filename = "%s.%s" % (normalized, DIGEST_EXTENSION)
   return os.path.join(config.options.workingDir, filename)

def _getTarfilePath(config, collectDir, archiveMode):
   """
   Gets the tarfile path (including correct extension) associated with a collect directory.
   @param config: Config object.
   @param collectDir: Collect directory object.
   @param archiveMode: Archive mode to use for this tarfile.
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
   return os.path.join(config.collect.targetDir, filename)

def _collectDirectory(config, absolutePath, tarfilePath, collectMode, archiveMode, resetDigest, digestPath):
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

   @param config: Config object.
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
      _changeOwnership(tarfilePath, config.options.backupUser, config.options.backupGroup)
   else:
      digest = {}
      if not resetDigest:
         digest = _loadDigest(digestPath)
         backupList.removeUnchanged(digest)
      backupList.generateTarfile(tarfilePath, archiveMode, True)
      _changeOwnership(tarfilePath, config.options.backupUser, config.options.backupGroup)
      digest = backupList.generateDigestMap()
      _writeDigest(config, digest, digestPath)

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
      _changeOwnership(digestPath, config.options.backupUser, config.options.backupGroup)
   except: 
      logger.error("Failed to write digest %s to disk." % digestPath)

def _writeCollectIndicator(config):
   """
   Writes a collect indicator file into a target collect directory.
   @param config: Config object.
   """
   filename = os.path.join(config.collect.targetDir, COLLECT_INDICATOR)
   try:
      open(filename, "w").write("")
      _changeOwnership(filename, config.options.backupUser, config.options.backupGroup)
   except Exception, e:
      logger.error("Error writing collect indicator: %s", e)


##########################
# executeStage() function
##########################

def executeStage(config):
   """
   Executes the stage backup action.

   @note: The daily directory is derived once and then we stick with it, just
   in case a backup happens to span midnite.

   @note: When the stage action is complete, we will write various indicator
   files so that it's obvious what actions have been completed.  Each peer gets
   a stage indicator in its collect directory, and then the master gets a stage
   indicator in its daily staging directory.  The store process uses the
   master's stage indicator to decide whehter a directory is ready to be
   stored.  Currently, nothing uses the indicator at each peer, and it exists
   for reference only. 

   @param config: Program configuration.
   @type config: Config object.
   """
   if config.options is None or config.stage is None:
      raise ValueError("Configuration is not properly filled in.")
   dailyDir = _getDailyDir(config)
   localPeers = _getLocalPeers(config)
   remotePeers = _getRemotePeers(config)
   allPeers = localPeers + remotePeers
   stagingDirs = _createStagingDirs(config, dailyDir, allPeers)
   for peer in allPeers:
      if not peer.checkCollectIndicator():
         logger.error("Peer '%s' was not ready to be staged." % peer.name)
         continue
      targetDir = stagingDirs[peer.name]
      ownership = (config.options.backupUser, config.options.backupGroup)
      peer.stagePeer(targetDir=targetDir, ownership=ownership)  # note: utilize backup user's default umask
      peer.writeStageIndicator()
   _writeStageIndicator(config, dailyDir)
   logger.info("Executed the 'stage' action successfully.")

def _getDailyDir(config):
   """
   Gets the daily staging directory.
   
   This is just a directory in the form C{staging/YYYY/MM/DD}, i.e.
   C{staging/2000/10/07}, except it will be an absolute path based on
   C{config.stage.targetDir}.

   @param config: Config object

   @return: Daily staging directory;
   """
   return os.path.join(config.stage.targetDir, time.strftime(DIR_TIME_FORMAT))

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
   return localPeers

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
         remotePeer = RemotePeer(peer.name, peer.collectDir, remoteUser, rcpCommand)
         remotePeers.append(remotePeer)
   return remotePeers

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
   if not os.path.isdir(dailyDir):
      try:
         os.makedirs(dailyDir)
         for path in [ dailyDir, os.path.join(dailyDir, ".."), os.path.join(dailyDir, "..", ".."), ]:
            _changeOwnership(path, config.options.backupUser, config.options.backupGroup)
      except Exception, e:
         raise Exception("Unable to create staging directory: %s" % e)
   for peer in peers:
      peerDir = os.path.join(dailyDir, peer.name)
      try:
         os.makedirs(peerDir)
         _changeOwnership(peerDir, config.options.backupUser, config.options.backupGroup)
         mapping[peer.name] = peerDir
      except Exception, e:
         raise Exception("Unable to create staging directory: %s" % e)
   return mapping
      
def _writeStageIndicator(config, dailyDir):
   """
   Writes a stage indicator file into the daily staging directory.

   Note that there is a stage indicator on each peer (to indicate that a
   collect directory has been staged) and in the daily staging directory itself
   (to indicate that the staging directory has been utilized).

   @param config: Config object.
   @param dailyDir: Daily staging directory.
   """
   filename = os.path.join(dailyDir, STAGE_INDICATOR)
   try:
      open(filename, "w").write("")
      _changeOwnership(filename, config.options.backupUser, config.options.backupGroup)
   except Exception, e:
      logger.error("Error writing stage indicator: %s", e)


##########################
# executeStore() function
##########################

def executeStore(config, rebuildMedia=False):
   """
   Executes the store backup action.

   If the C{rebuildMedia} argument is passed in as C{True}, then the media will
   be wiped and rebuilt from scratch, regardless of other configuration.  This
   would most often be used to implement a "do a full backup now" override
   switch (i.e. "--full").

   @note: When the store action is complete, we will write a store indicator to
   the daily staging directory we used, so it's obvious that the store action
   has completed.  This store indicator is used as discussed in the notes for
   L{_getCorrectStoreDir}.

   @param config: Program configuration.
   @type config: Config object.

   @param rebuildMedia: Indicates that new media should b
   @type rebuildMedia: Boolean value.
   """
   if config.options is None or config.store is None:
      raise ValueError("Configuration is not properly filled in.")
   todayIsStart = _todayIsStart(config.options.startingDay)
   entireDisc = rebuildMedia or todayIsStart
   (storeDir, dateSuffix) = _getCorrectStoreDir(config)
   writer = _getWriter(config)
   (image, imagePath) = _createImage(config, entireDisc, storeDir, dateSuffix, writer)
   try:
      writer.writeImage(imagePath, newDisc=entireDisc)
   finally:
      os.unlink(imagePath)
   logger.warn(" *** Warning: consistency check is not yet implemented! *** ")
   _writeStoreIndicator(config, storeDir)
   logger.info("Executed the 'store' action successfully.")

def _getCorrectStoreDir(config):
   """
   Get directory that should be stored.

   Normally, we will just attempt to store the staging directory for the
   current day.  However, if we can't find that directory or that directory
   does not have a staging indicator written to it, we'll look one day on
   either side of the current day (first before, then after) for a different
   directory that has been staged but not yet stored.  If we find such a
   directory, we'll use it instead.  This way, we can seamlessly handle the
   case where a backup spans midnite (i.e. the stage happens on a different day
   than the store).

   @param config: Config object.

   @return: Daily staging directory to be stored.
   @raise Exception: If a store directory cannot be found.
   """
   t = time.time()
   today = time.localtime(t)
   yesterday = time.localtime(t-SECONDS_PER_DAY)
   tomorrow = time.localtime(t+SECONDS_PER_DAY)
   for stamp in [ today, yesterday, tomorrow, ]:
      dateSuffix = time.strftime(DIR_TIME_FORMAT, stamp)
      dailyDir = os.path.join(config.store.sourceDir, dateSuffix)
      stageIndicator = os.path.join(dailyDir, STAGE_INDICATOR)
      if os.path.isdir(dailyDir) and os.path.isfile(stageIndicator):
         logger.debug("Found dir %s ready to be stored." % dailyDir)
         return (dailyDir, dateSuffix)
   raise Exception("Unable to find a staged directory ready to be stored.")

def _getWriter(config):
   """
   Gets a writer object based on current configuration.

   This method abstracts (a bit) the main store method from knowing what kind
   of writer it's using.  It creates and returns a writer based on
   configuration.  Right now, it will always return a L{CdWriter} and will
   thrown an exception if any other kind of writer is specified.

   @param config: Config object.

   @return: Writer that can be used to write a directory to some media.
   """
   if config.store.deviceType != "cdwriter":
      raise ValueError("Device type '%s' is invalid." % config.store.deviceType)
   return CdWriter(config.store.devicePath, config.store.deviceScsiId, config.store.driveSpeed, config.store.mediaType)

def _writeStoreIndicator(config, dailyDir):
   """
   Writes a store indicator file into a target store directory.

   Note that there is a store indicator on each peer (to indicate that a
   collect directory has been stored) and in the daily staging directory itself
   (to indicate that the staging directory has been utilized).

   @param config: Config object.
   @param dailyDir: Daily staging directory that was stored.
   """
   dailyDir = _getDailyDir(config)
   filename = os.path.join(dailyDir, STORE_INDICATOR)
   try:
      open(filename, "w").write("")
      _changeOwnership(filename, config.options.backupUser, config.options.backupGroup)
   except Exception, e:
      logger.error("Error writing store indicator: %s", e)

def _createImage(config, entireDisc, storeDir, dateSuffix, writer):
   """
   Creates and returns an ISO image ready to write to disc.

   The image will be created and then written to disc in the working directory
   with a temporary name.  The caller must remove the image when it is done
   being written.

   @todo: Implement handlers for the 'overwrite', 'rebuild' and 'rewrite'
   capacity modes.

   @param config: Config object.
   @param entireDisc: Indicates whether entire disc should be used (i.e. rewrite disc).
   @param storeDir: Directory to be written into the image.
   @param dateSuffix: Date string (i.e. C{2000/10/07} to be used as the graft point for the data.
   @param writer: Writer associated with the media.

   @return: Tuple of (image, imagePath).

   @raise IOError: If the media is full and the image cannot be made to fit.
   """
   capacity = writer.retrieveCapacity(entireDisc=entireDisc)
   image = IsoImage(writer.device, capacity.boundaries)
   image.addEntry(path=storeDir, graftPoint=dateSuffix, contentsOnly=True)
   imageSize = image.getEstimatedSize()
   logger.info("Image size will be %.2f bytes." % imageSize)
   if imageSize > capacity.bytesAvailable:
      logger.info("Image (%.2f bytes) does not fit in available capacity (%.2f bytes)." % (imageSize, capacity.bytesAvailable))
      if config.store.capacityMode == 'fail':
         raise IOError("Media does not contain enough capacity to store image.")
      elif config.store.capacityMode == 'overwrite':
         logger.error("Capacity mode 'overwrite' is currently not implemented; defaulting to 'fail'.")
         raise IOError("Media does not contain enough capacity to store image.")
      elif config.store.capacityMode == 'rebuild':
         logger.error("Capacity mode 'rebuild' is currently not implemented; defaulting to 'fail'.")
         raise IOError("Media does not contain enough capacity to store image.")
      elif config.store.capacityMode == 'rewrite':
         logger.error("Capacity mode 'rewrite' is currently not implemented; defaulting to 'fail'.")
         raise IOError("Media does not contain enough capacity to store image.")
      elif config.store.capacityMode == 'discard':
         logger.debug("Capacity mode is 'discard', so we will prune to fit if possible.")
         try:
            imageSize = image.pruneImage(capacity.bytesAvailable)
            logger.info("Image was successfully pruned to %.2f bytes, and will now fit." % imageSize)
         except IOError:
            logger.error("Capacity mode is 'discard', but we could not prune to fit the capacity.")
            raise IOError("Media does not contain enough capacity to store image.")
   (handle, imagePath) = tempfile.mkstemp(dir=config.options.workingDir)
   handle.close()
   image.writeImage(imagePath)
   return (image, imagePath)


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

