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
# Purpose  : Implements the standard 'collect' action.
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

########################################################################
# Module documentation
########################################################################

"""
Implements the standard 'collect' action.
@sort: executeCollect
@author: Kenneth J. Pronovici <pronovic@ieee.org>
"""


########################################################################
# Imported modules
########################################################################

# System modules
import os
import logging
import pickle

# Cedar Backup modules
from CedarBackup2.filesystem import BackupFileList
from CedarBackup2.util import isStartOfWeek, changeOwnership, displayBytes, buildNormalizedPath
from CedarBackup2.actions.constants import DIGEST_EXTENSION, COLLECT_INDICATOR


########################################################################
# Module-wide constants and variables
########################################################################

logger = logging.getLogger("CedarBackup2.log.actions.collect")


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
   if config.collect.collectFiles is not None:
      for collectFile in config.collect.collectFiles:
         logger.debug("Working with collect file [%s]" % collectFile.absolutePath)
         collectMode = _getCollectMode(config, collectFile)
         archiveMode = _getArchiveMode(config, collectFile)
         digestPath = _getDigestPath(config, collectFile)
         tarfilePath = _getTarfilePath(config, collectFile, archiveMode)
         if fullBackup or (collectMode in ['daily', 'incr', ]) or (collectMode == 'weekly' and todayIsStart):
            logger.debug("File meets criteria to be backed up today.")
            _collectFile(config, collectFile.absolutePath, tarfilePath, 
                         collectMode, archiveMode, resetDigest, digestPath)
         else:
            logger.debug("File will not be backed up, per collect mode.")
         logger.info("Completed collecting file [%s]" % collectFile.absolutePath)
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


########################################################################
# Private utility functions
########################################################################

##########################
# _collectFile() function
##########################

def _collectFile(config, absolutePath, tarfilePath, collectMode, archiveMode, resetDigest, digestPath):
   """
   Collects a configured collect file.
   
   The indicated collect file is collected into the indicated tarfile.
   For files that are collected incrementally, we'll use the indicated
   digest path and pay attention to the reset digest flag (basically, the reset
   digest flag ignores any existing digest, but a new digest is always
   rewritten).

   The caller must decide what the collect and archive modes are, since they
   can be on both the collect configuration and the collect file itself.

   @param config: Config object.
   @param absolutePath: Absolute path of file to collect.
   @param tarfilePath: Path to tarfile that should be created.
   @param collectMode: Collect mode to use.
   @param archiveMode: Archive mode to use.
   @param resetDigest: Reset digest flag.
   @param digestPath: Path to digest file on disk, if needed.
   """
   backupList = BackupFileList()
   backupList.addFile(absolutePath)
   _executeBackup(config, backupList, absolutePath, tarfilePath, collectMode, archiveMode, resetDigest, digestPath)


###############################
# _collectDirectory() function
###############################

def _collectDirectory(config, absolutePath, tarfilePath, collectMode, archiveMode, 
                      ignoreFile, resetDigest, digestPath, excludePaths, excludePatterns):
   """
   Collects a configured collect directory.
   
   The indicated collect directory is collected into the indicated tarfile.
   For directories that are collected incrementally, we'll use the indicated
   digest path and pay attention to the reset digest flag (basically, the reset
   digest flag ignores any existing digest, but a new digest is always
   rewritten).

   The caller must decide what the collect and archive modes are, since they
   can be on both the collect configuration and the collect directory itself.

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
   _executeBackup(config, backupList, absolutePath, tarfilePath, collectMode, archiveMode, resetDigest, digestPath)


############################
# _executeBackup() function
############################

def _executeBackup(config, backupList, absolutePath, tarfilePath, collectMode, archiveMode, resetDigest, digestPath):
   """
   Execute the backup process for the indicated backup list.

   This function exists mainly to consolidate functionality between the
   L{_collectFile} and L{_collectDirectory} functions.  Those functions build
   the backup list; this function causes the backup to execute properly and
   also manages usage of the digest file on disk as explained in their
   comments.

   For collect files, the digest file will always just contain the single file
   that is being backed up.  This might little wasteful in terms of the number
   of files that we keep around, but it's consistent and easy to understand.

   @param config: Config object.
   @param backupList: List to execute backup for
   @param absolutePath: Absolute path of directory or file to collect.
   @param tarfilePath: Path to tarfile that should be created.
   @param collectMode: Collect mode to use.
   @param archiveMode: Archive mode to use.
   @param resetDigest: Reset digest flag.
   @param digestPath: Path to digest file on disk, if needed.
   """
   if collectMode != 'incr':
      logger.debug("Collect mode is [%s]; no digest will be used." % collectMode)
      if len(backupList) == 1 and backupList[0] == absolutePath:  # special case for individual file
         logger.info("Backing up file [%s] (%s)." % (absolutePath, displayBytes(backupList.totalSize())))
      else:
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
      (removed, newDigest) = backupList.removeUnchanged(oldDigest, captureDigest=True)
      logger.debug("Removed %d unchanged files based on digest values." % removed)
      if len(backupList) == 1 and backupList[0] == absolutePath:  # special case for individual file
         logger.info("Backing up file [%s] (%s)." % (absolutePath, displayBytes(backupList.totalSize())))
      else:
         logger.info("Backing up %d files in [%s] (%s)." % (len(backupList), absolutePath, displayBytes(backupList.totalSize())))
      if len(backupList) > 0:
         backupList.generateTarfile(tarfilePath, archiveMode, True)
         changeOwnership(tarfilePath, config.options.backupUser, config.options.backupGroup)
      _writeDigest(config, newDigest, digestPath)


#########################
# _loadDigest() function
#########################

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


##########################
# _writeDigest() function
##########################

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


####################################
# _writeCollectIndicator() function
####################################

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


########################################################################
# Private attribute "getter" functions
########################################################################

############################
# getCollectMode() function
############################

def _getCollectMode(config, item):
   """
   Gets the collect mode that should be used for a collect directory or file.
   If possible, use the one on the file or directory, otherwise take from collect section.
   @param config: Config object.
   @param item: C{CollectFile} or C{CollectDir} object
   @return: Collect mode to use.
   """
   if item.collectMode is None:
      collectMode = config.collect.collectMode
   else:
      collectMode = item.collectMode
   logger.debug("Collect mode is [%s]" % collectMode)
   return collectMode


#############################
# _getArchiveMode() function
#############################

def _getArchiveMode(config, item):
   """
   Gets the archive mode that should be used for a collect directory or file.
   If possible, use the one on the file or directory, otherwise take from collect section.
   @param config: Config object.
   @param item: C{CollectFile} or C{CollectDir} object
   @return: Archive mode to use.
   """
   if item.archiveMode is None:
      archiveMode = config.collect.archiveMode
   else:
      archiveMode = item.archiveMode
   logger.debug("Archive mode is [%s]" % archiveMode)
   return archiveMode


############################
# _getIgnoreFile() function
############################

def _getIgnoreFile(config, item):
   """
   Gets the ignore file that should be used for a collect directory or file.
   If possible, use the one on the file or directory, otherwise take from collect section.
   @param config: Config object.
   @param item: C{CollectFile} or C{CollectDir} object
   @return: Ignore file to use.
   """
   if item.ignoreFile is None:
      ignoreFile = config.collect.ignoreFile
   else:
      ignoreFile = item.ignoreFile
   logger.debug("Ignore file is [%s]" % ignoreFile)
   return ignoreFile


############################
# _getDigestPath() function
############################

def _getDigestPath(config, item):
   """
   Gets the digest path associated with a collect directory or file.
   @param config: Config object.
   @param item: C{CollectFile} or C{CollectDir} object
   @return: Absolute path to the digest associated with the collect directory or file.
   """
   normalized = buildNormalizedPath(item.absolutePath)
   filename = "%s.%s" % (normalized, DIGEST_EXTENSION)
   digestPath = os.path.join(config.options.workingDir, filename)
   logger.debug("Digest path is [%s]" % digestPath)
   return digestPath


#############################
# _getTarfilePath() function
#############################

def _getTarfilePath(config, item, archiveMode):
   """
   Gets the tarfile path (including correct extension) associated with a collect directory.
   @param config: Config object.
   @param item: C{CollectFile} or C{CollectDir} object
   @param archiveMode: Archive mode to use for this tarfile.
   @return: Absolute path to the tarfile associated with the collect directory.
   """
   if archiveMode == 'tar':
      extension = "tar"
   elif archiveMode == 'targz':
      extension = "tar.gz"
   elif archiveMode == 'tarbz2':
      extension = "tar.bz2"
   normalized = buildNormalizedPath(item.absolutePath)
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
