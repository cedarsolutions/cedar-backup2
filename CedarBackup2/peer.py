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
# Purpose  : Provides backup peer-related objects.
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# This file was created with a width of 132 characters, and NO tabs.

########################################################################
# Module documentation
########################################################################

"""
Provides backup peer-related objects and utility functions.

@sort: LocalPeer, Remote Peer

@var DEF_COLLECT_INDICATOR: Name of the default collect indicator file.
@var DEF_STAGE_INDICATOR: Name of the default stage indicator file.

@author: Kenneth J. Pronovici <pronovic@ieee.org>
"""


########################################################################
# Imported modules
########################################################################

# System modules
import os
import logging
import shutil
import tempfile
import sets
import re

# Cedar Backup modules
from CedarBackup2.filesystem import FilesystemList
from CedarBackup2.util import splitCommandLine, executeCommand


########################################################################
# Module-wide constants and variables
########################################################################

logger                  = logging.getLogger("CedarBackup2.log.peer")

DEF_RCP_COMMAND         = [ "/usr/bin/scp", "-B", "-q", "-C" ]
DEF_COLLECT_INDICATOR   = "cback.collect"
DEF_STAGE_INDICATOR     = "cback.stage"


########################################################################
# LocalPeer class definition
########################################################################

class LocalPeer(object):

   ######################
   # Class documentation
   ######################

   """
   Backup peer representing a local peer in a backup pool.

   This is a class representing a local (non-network) peer in a backup pool.
   Local peers are backed up by simple filesystem copy operations.  A local
   peer has associated with it a name (typically, but not necessarily, a
   hostname) and a collect directory.

   The public methods other than the constructor are part of a "backup peer"
   interface shared with the C{RemotePeer} class.

   @sort: __init__, stagePeer, checkCollectIndicator, writeStageIndicator, 
          _copyLocalDir, _copyLocalFile, name, collectDir
   """

   ##############
   # Constructor
   ##############

   def __init__(self, name, collectDir):
      """
      Initializes a local backup peer.

      Note that the collect directory must be an absolute path, but does not
      have to exist when the object is instantiated.  We do a lazy validation
      on this value since we could (potentially) be creating peer objects
      before an ongoing backup completed.
      
      @param name: Name of the backup peer
      @type name: String, typically a hostname

      @param collectDir: Path to the peer's collect directory 
      @type collectDir: String representing an absolute local path on disk

      @raise ValueError: If the name is empty.
      @raise ValueError: If collect directory is not an absolute path.
      """
      self._name = None
      self._collectDir = None
      self.name = name
      self.collectDir = collectDir


   #############
   # Properties
   #############

   def _setName(self, value):
      """
      Property target used to set the peer name.
      The value must be a non-empty string and cannot be C{None}.
      @raise ValueError: If the value is an empty string or C{None}.
      """
      if value is None or len(value) < 1:
         raise ValueError("Peer name must be a non-empty string.")
      self._name = value

   def _getName(self):
      """
      Property target used to get the peer name.
      """
      return self._name

   def _setCollectDir(self, value):
      """
      Property target used to set the collect directory.
      The value must be an absolute path and cannot be C{None}.
      It does not have to exist on disk at the time of assignment.
      @raise ValueError: If the value is C{None} or is not an absolute path.
      """
      if value is None or not os.path.isabs(value):
         raise ValueError("Collect directory must be an absolute path.")
      self._collectDir = value

   def _getCollectDir(self):
      """
      Property target used to get the collect directory.
      """
      return self._collectDir

   name = property(_getName, _setName, None, "Name of the peer.")
   collectDir = property(_getCollectDir, _setCollectDir, None, "Path to the peer's collect directory (an absolute local path).")


   #################
   # Public methods
   #################

   def stagePeer(self, targetDir, ownership=None, permissions=None):
      """
      Stages data from the peer into the indicated local target directory.

      The collect and target directories must both already exist before this
      method is called.  If passed in, ownership and permissions will be
      applied to the files that are copied.
   
      @note: The caller is responsible for checking that the indicator exists,
      if they care.  This function only stages the files within the directory.

      @note: If you have user/group as strings, call the L{util.getUidGid} function
      to get the associated uid/gid as an ownership tuple.

      @param targetDir: Target directory to write data into
      @type targetDir: String representing a directory on disk

      @param ownership: Owner and group that the staged files should have
      @type ownership: Tuple of numeric ids C{(uid, gid)}

      @param permissions: Permissions that the staged files should have
      @type permissions: UNIX permissions mode, specified in octal (i.e. C{0640}).

      @raise ValueError: If collect directory is not a directory or does not exist 
      @raise ValueError: If target directory is not a directory, does not exist or is not absolute.
      @raise IOError: If there were no files to stage (i.e. the directory was empty)
      @raise IOError: If there is an IO error copying a file.
      @raise OSError: If there is an OS error copying or changing permissions on a file
      """
      if not os.path.isabs(targetDir):
         logger.debug("Target directory [%s] not an absolute path." % targetDir)
         raise ValueError("Target directory must be an absolute path.")
      if not os.path.exists(self.collectDir) or not os.path.isdir(self.collectDir):
         logger.debug("Collect directory [%s] is not a directory or does not exist on disk." % self.collectDir)
         raise ValueError("Collect directory is not a directory or does not exist on disk.")
      if not os.path.exists(targetDir) or not os.path.isdir(targetDir):
         logger.debug("Target directory [%s] is not a directory or does not exist on disk." % targetDir)
         raise ValueError("Target directory is not a directory or does not exist on disk.")
      LocalPeer._copyLocalDir(self.collectDir, targetDir, ownership, permissions)

   def checkCollectIndicator(self, collectIndicator=None):
      """
      Checks the collect indicator in the peer's staging directory.

      When a peer has completed collecting its backup files, it will write an
      empty indicator file into its collect directory.  This method checks to
      see whether that indicator has been written.  We're "stupid" here - if
      the collect directory doesn't exist, you'll naturally get back C{False}.

      If you need to, you can override the name of the collect indicator file
      by passing in a different name.

      @param collectIndicator: Name of the collect indicator file to check
      @type collectIndicator: String representing name of a file in the collect directory

      @return: Boolean true/false depending on whether the indicator exists.
      """
      if collectIndicator is None:
         return os.path.exists(os.path.join(self.collectDir, DEF_COLLECT_INDICATOR))
      else:
         return os.path.exists(os.path.join(self.collectDir, collectIndicator))

   def writeStageIndicator(self, stageIndicator=None, ownership=None, permissions=None):
      """
      Writes the stage indicator in the peer's staging directory.

      When the master has completed collecting its backup files, it will write
      an empty indicator file into the peer's collect directory.  The presence
      of this file implies that the staging process is complete.

      If you need to, you can override the name of the stage indicator file by
      passing in a different name.

      @note: If you have user/group as strings, call the L{util.getUidGid}
      function to get the associated uid/gid as an ownership tuple.

      @param stageIndicator: Name of the indicator file to write
      @type stageIndicator: String representing name of a file in the collect directory

      @param ownership: Owner and group that the indicator file should have
      @type ownership: Tuple of numeric ids C{(uid, gid)}

      @param permissions: Permissions that the indicator file should have
      @type permissions: UNIX permissions mode, specified in octal (i.e. C{0640}).

      @raise ValueError: If collect directory is not a directory or does not exist 
      @raise IOError: If there is an IO error creating the file.
      @raise OSError: If there is an OS error creating or changing permissions on the file
      """
      if not os.path.exists(self.collectDir) or not os.path.isdir(self.collectDir):
         logger.debug("Collect directory [%s] is not a directory or does not exist on disk." % self.collectDir)
         raise ValueError("Collect directory is not a directory or does not exist on disk.")
      if stageIndicator is None:
         fileName = os.path.join(self.collectDir, DEF_STAGE_INDICATOR)
      else:
         fileName = os.path.join(self.collectDir, stageIndicator)
      LocalPeer._copyLocalFile(None, fileName, ownership, permissions)    # None for sourceFile results in an empty target


   ##################
   # Private methods
   ##################

   def _copyLocalDir(sourceDir, targetDir, ownership=None, permissions=None):
      """
      Copies files from the source directory to the target directory.

      This function is not recursive.  Only the files in the directory will be
      copied.   Ownership and permissions will be left at their default values
      if new values are not specified.  The source and target directories are
      allowed to be soft links to a directory, but besides that soft links are
      ignored.

      @note: If you have user/group as strings, call the L{util.getUidGid}
      function to get the associated uid/gid as an ownership tuple.

      @param sourceDir: Source directory
      @type sourceDir: String representing a directory on disk

      @param targetDir: Target directory
      @type targetDir: String representing a directory on disk

      @param ownership: Owner and group that the copied files should have
      @type ownership: Tuple of numeric ids C{(uid, gid)}

      @param permissions: Permissions that the staged files should have
      @type permissions: UNIX permissions mode, specified in octal (i.e. C{0640}).

      @return: Number of files copied from the source directory to the target directory.
      @raise ValueError: If source or target is not a directory or does not exist.
      @raise IOError: If there is an IO error copying the files.
      @raise OSError: If there is an OS error copying or changing permissions on a files
      """
      for fileName in os.listdir(sourceDir):
         sourceFile = os.path.join(sourceDir, fileName)
         targetFile = os.path.join(targetDir, fileName)
         LocalPeer._copyLocalFile(sourceFile, targetFile, ownership, permissions)
   _copyLocalDir = staticmethod(_copyLocalDir)

   def _copyLocalFile(sourceFile=None, targetFile=None, ownership=None, permissions=None):
      """
      Copies a source file to a target file.

      If the source file is C{None} then the target file will be created or
      overwritten as an empty file.  If the target file is C{None}, this method
      is a no-op.  Attempting to copy a soft link or a directory will result in
      an exception.

      @note: If you have user/group as strings, call the L{util.getUidGid}
      function to get the associated uid/gid as an ownership tuple.

      @param sourceFile: Source file to copy
      @type sourceFile: String representing a file on disk, as an absolute path

      @param targetFile: Target file to create
      @type targetFile: String representing a file on disk, as an absolute path

      @param ownership: Owner and group that the copied should have
      @type ownership: Tuple of numeric ids C{(uid, gid)}

      @param permissions: Permissions that the staged files should have
      @type permissions: UNIX permissions mode, specified in octal (i.e. C{0640}).

      @raise ValueError: If the passed-in source file is not a regular file.
      @raise IOError: If there is an IO error copying the file
      @raise OSError: If there is an OS error copying or changing permissions on a file
      """
      if targetFile is None:
         return
      if sourceFile is None:
         open(targetFile, "w").write("")
      else:
         if os.path.isfile(sourceFile) and not os.path.islink(sourceFile):
            shutil.copy(sourceFile, targetFile)
         else:
            logger.debug("Source [%s] is not a regular file." % sourceFile)
            raise ValueError("Source is not a regular file.")
      if ownership is not None:
         os.chown(targetFile, ownership[0], ownership[1])
      if permissions is not None:
         os.chmod(targetFile, permissions)
   _copyLocalFile = staticmethod(_copyLocalFile)


########################################################################
# RemotePeer class definition
########################################################################

class RemotePeer(object):

   ######################
   # Class documentation
   ######################

   """
   Backup peer representing a remote peer in a backup pool.

   This is a class representing a remote (networked) peer in a backup pool.
   Remote peers are backed up using an rcp-compatible copy command.  A remote
   peer has associated with it a name (which must be a valid hostname), a
   collect directory and a copy method (an rcp-compatible command).

   The copy method is associated with the peer and not with the actual request
   to copy, because we can envision that each remote host might have a
   different connect method.

   The public methods other than the constructor are part of a "backup peer"
   interface shared with the C{LocalPeer} class.

   @sort: __init__, stagePeer, checkCollectIndicator, writeStageIndicator, 
          _getDirContents _copyRemoteDir, _copyRemoteFile, _pushLocalFile, 
          name, collectDir, remoteUser, rcpCommand
   """

   ##############
   # Constructor
   ##############

   def __init__(self, name, collectDir, remoteUser, rcpCommand=None):
      """
      Initializes a remote backup peer.

      @note: If provided, the rcp command will eventually be parsed into a list
      of strings suitable for passing to L{popen2.Popen4} in order to avoid
      security holes related to shell interpolation.   This parsing will be
      done by the L{util.splitCommandLine} function.  See the documentation for
      that function for some important notes about its limitations.

      @param name: Name of the backup peer
      @type name: String, must be a valid DNS hostname

      @param collectDir: Path to the peer's collect directory 
      @type collectDir: String representing an absolute path on the remote peer

      @param remoteUser: Name of the Cedar Backup user on the remote peer
      @type remoteUser: String representing a username, valid via the copy command

      @param rcpCommand: An rcp-compatible copy command to use for copying files from the peer
      @type rcpCommand: String representing a system command including required arguments

      @raise ValueError: If collect directory is not an absolute path
      """
      self._name = None
      self._collectDir = None
      self._remoteUser = None
      self._rcpCommand = None
      self._rcpCommandList = None
      self.name = name
      self.collectDir = collectDir
      self.remoteUser = remoteUser
      self.rcpCommand = rcpCommand


   #############
   # Properties
   #############

   def _setName(self, value):
      """
      Property target used to set the peer name.
      The value must be a non-empty string and cannot be C{None}.
      @raise ValueError: If the value is an empty string or C{None}.
      """
      if value is None or len(value) < 1:
         raise ValueError("Peer name must be a non-empty string.")
      self._name = value

   def _getName(self):
      """
      Property target used to get the peer name.
      """
      return self._name

   def _setCollectDir(self, value):
      """
      Property target used to set the collect directory.
      The value must be an absolute path and cannot be C{None}.
      It does not have to exist on disk at the time of assignment.
      @raise ValueError: If the value is C{None} or is not an absolute path.
      """
      if value is None or not os.path.isabs(value):
         raise ValueError("Collect directory must be an absolute path.")
      self._collectDir = value

   def _getCollectDir(self):
      """
      Property target used to get the collect directory.
      """
      return self._collectDir

   def _setRemoteUser(self, value):
      """
      Property target used to set the remote user.
      The value must be a non-empty string and cannot be C{None}.
      @raise ValueError: If the value is an empty string or C{None}.
      """
      if value is None or len(value) < 1:
         raise ValueError("Peer remote user must be a non-empty string.")
      self._remoteUser = value

   def _getRemoteUser(self):
      """
      Property target used to get the remote user.
      """
      return self._remoteUser

   def _setRcpCommand(self, value):
      """
      Property target to set the rcp command.

      The value must be a non-empty string or C{None}.  Its value is stored in
      the two forms: "raw" as provided by the client, and "parsed" into a list
      suitable for being passed to L{util.executeCommand} via
      L{util.splitCommandLine}.  

      However, all the caller will ever see via the property is the actual
      value they set (which includes seeing C{None}, even if we translate that
      internally to C{DEF_RCP_COMMAND}).  Internally, we should always use
      C{self._rcpCommandList} if we want the actual command list.

      @raise ValueError: If the value is an empty string.
      """
      if value is None:
         self._rcpCommand = None
         self._rcpCommandList = DEF_RCP_COMMAND
      else:
         if len(value) >= 1:
            self._rcpCommand = value
            self._rcpCommandList = splitCommandLine(self._rcpCommand)
         else:
            raise ValueError("The rcp command must be a non-empty string.")

   def _getRcpCommand(self):
      """
      Property target used to get the rcp command.
      """
      return self._rcpCommand

   name = property(_getName, _setName, None, "Name of the peer (a valid DNS hostname).")
   collectDir = property(_getCollectDir, _setCollectDir, None, "Path to the peer's collect directory (an absolute local path).")
   remoteUser = property(_getRemoteUser, _setRemoteUser, None, "Name of the Cedar Backup user on the remote peer.")
   rcpCommand = property(_getRcpCommand, _setRcpCommand, None, "An rcp-compatible copy command to use for copying files.")


   #################
   # Public methods
   #################

   def stagePeer(self, targetDir, ownership=None, permissions=None):
      """
      Stages data from the peer into the indicated local target directory.

      The target directory must already exist before this method is called.  If
      passed in, ownership and permissions will be applied to the files that
      are copied.  

      @note: If you have user/group as strings, call the L{util.getUidGid} function
      to get the associated uid/gid as an ownership tuple.

      @note: Unlike the local peer version of this method, an I/O error might
      be raised if the directory is empty.  Since we're using a remote copy
      method, we just don't have the fine-grained control over our exceptions
      that's available when we can look directly at the filesystem, and we
      can't control whether the remote copy method thinks an empty directory is
      an error.  

      @param targetDir: Target directory to write data into
      @type targetDir: String representing a directory on disk

      @param ownership: Owner and group that the staged files should have
      @type ownership: Tuple of numeric ids C{(uid, gid)}

      @param permissions: Permissions that the staged files should have
      @type permissions: UNIX permissions mode, specified in octal (i.e. C{0640}).

      @raise ValueError: If target directory is not a directory, does not exist or is not absolute.
      @raise IOError: If there is an IO error copying a file.
      @raise OSError: If there is an OS error copying or changing permissions on a file
      """
      if not os.path.isabs(targetDir):
         logger.debug("Target directory [%s] not an absolute path." % targetDir)
         raise ValueError("Target directory must be an absolute path.")
      if not os.path.exists(targetDir) or not os.path.isdir(targetDir):
         logger.debug("Target directory [%s] is not a directory or does not exist on disk." % targetDir)
         raise ValueError("Target directory is not a directory or does not exist on disk.")
      RemotePeer._copyRemoteDir(self.remoteUser, self.name, self._rcpCommandList, 
                                self.collectDir, targetDir, ownership, permissions)

   def checkCollectIndicator(self, collectIndicator=None):
      """
      Checks the collect indicator in the peer's staging directory.

      When a peer has completed collecting its backup files, it will write an
      empty indicator file into its collect directory.  This method checks to
      see whether that indicator has been written.  If the remote copy command
      fails, we return C{False} as if the file weren't there.  We depend on the
      rcp command returning some sort of error if the file doesn't exist.

      If you need to, you can override the name of the collect indicator file
      by passing in a different name.

      @note: This method's behavior is UNIX-specific.  It depends on the
      ability of L{tempfile.NamedTemporaryFile} to create files that can be
      opened more than once.

      @param collectIndicator: Name of the collect indicator file to check
      @type collectIndicator: String representing name of a file in the collect directory

      @return: Boolean true/false depending on whether the indicator exists.
      """
      targetFile = tempfile.NamedTemporaryFile()
      if collectIndicator is None:
         sourceFile = os.path.join(self.collectDir, DEF_COLLECT_INDICATOR)
      else:
         sourceFile = os.path.join(self.collectDir, collectIndicator)
      try:
         RemotePeer._copyRemoteFile(self.remoteUser, self.name, self._rcpCommandList, sourceFile, targetFile.name)
         return True
      except:
         return False

   def writeStageIndicator(self, stageIndicator=None):
      """
      Writes the stage indicator in the peer's staging directory.

      When the master has completed collecting its backup files, it will write
      an empty indicator file into the peer's collect directory.  The presence
      of this file implies that the staging process is complete.

      If you need to, you can override the name of the stage indicator file by
      passing in a different name.

      @note: If you have user/group as strings, call the L{util.getUidGid} function
      to get the associated uid/gid as an ownership tuple.

      @note: This method's behavior is UNIX-specific.  It depends on the
      ability of L{tempfile.NamedTemporaryFile} to create files that can be
      opened more than once.

      @param stageIndicator: Name of the indicator file to write
      @type stageIndicator: String representing name of a file in the collect directory

      @raise ValueError: If collect directory is not a directory or does not exist 
      @raise IOError: If there is an IO error creating the file.
      @raise OSError: If there is an OS error creating or changing permissions on the file
      """
      if not os.path.exists(self.collectDir) or not os.path.isdir(self.collectDir):
         logger.debug("Collect directory [%s] is not a directory or does not exist on disk." % self.collectDir)
         raise ValueError("Collect directory is not a directory or does not exist on disk.")
      sourceFile = tempfile.NamedTemporaryFile()
      if stageIndicator is None:
         targetFile = os.path.join(self.collectDir, DEF_STAGE_INDICATOR)
      else:
         targetFile = os.path.join(self.collectDir, stageIndicator)
      RemotePeer._pushLocalFile(self.remoteUser, self.name, self._rcpCommandList, sourceFile.name, targetFile)


   ##################
   # Private methods
   ##################

   def _getDirContents(path):
      """
      Returns the contents of a directory in terms of a Set.
      
      The directory's contents are read as a L{FilesystemList} containing only
      files, and then the list is converted into a L{sets.Set} object for later
      use.

      @param path: Directory path to get contents for
      @type path: String representing a path on disk

      @return: Set of files in the directory
      @raise ValueError: If path is not a directory or does not exist.
      """
      contents = FilesystemList()
      contents.excludeDirs = True
      contents.excludeLinks = True
      contents.addDirContents(path)
      return sets.Set(contents)
   _getDirContents = staticmethod(_getDirContents)

   def _copyRemoteDir(remoteUser, remoteHost, rcpCommand, sourceDir, targetDir, ownership=None, permissions=None):
      """
      Copies files from the source directory to the target directory.

      This function is not recursive.  Only the files in the directory will be
      copied.   Ownership and permissions will be left at their default values
      if new values are not specified.  Behavior when copying soft links from
      the collect directory is dependent on the behavior of the specified rcp
      command.

      @note: If you have user/group as strings, call the L{util.getUidGid} function
      to get the associated uid/gid as an ownership tuple.

      @note: We don't have a good way of knowing exactly what files we copied
      down from the remote peer, unless we want to parse the output of the rcp
      command (ugh).  We could change permissions on everything in the target
      directory, but that's kind of ugly too.  Instead, we use Python's set
      functionality to figure out what files were added while we executed the
      rcp command.  This isn't perfect - for instance, it's not correct if
      someone else is messing with the directory at the same time we're doing
      the remote copy - but it's about as good as we're going to get.

      @param remoteUser: Name of the Cedar Backup user on the remote peer
      @type remoteUser: String representing a username, valid via the copy command

      @param remoteHost: Hostname of the remote peer
      @type remoteHost: String representing a hostname, accessible via the copy command

      @param rcpCommand: An rcp-compatible copy command to use for copying files
      @type rcpCommand: Command as a list to be passed to L{util.executeCommand}

      @param sourceDir: Source directory
      @type sourceDir: String representing a directory on disk

      @param targetDir: Target directory
      @type targetDir: String representing a directory on disk

      @param ownership: Owner and group that the copied files should have
      @type ownership: Tuple of numeric ids C{(uid, gid)}

      @param permissions: Permissions that the staged files should have
      @type permissions: UNIX permissions mode, specified in octal (i.e. C{0640}).

      @return: Number of files copied from the source directory to the target directory.
      @raise ValueError: If source or target is not a directory or does not exist.
      @raise IOError: If there is an IO error copying the files.
      """
      beforeSet = RemotePeer._getDirContents(targetDir)
      copySource = "%s@%s:%s/*" % (remoteUser, remoteHost, sourceDir)
      result = executeCommand(rcpCommand, [copySource, targetDir])[0]
      if result != 0:
         raise IOError("Error (%d) copying files from remote host." % result)
      afterSet = RemotePeer._getDirContents(targetDir)
      for targetFile in afterSet.difference(beforeSet):  # files we added as part of copy
         if ownership is not None:
            os.chown(targetFile, ownership[0], ownership[1])
         if permissions is not None:
            os.chmod(targetFile, permissions)
   _copyRemoteDir = staticmethod(_copyRemoteDir)

   def _copyRemoteFile(remoteUser, remoteHost, rcpCommand, sourceFile, targetFile, ownership=None, permissions=None):
      """
      Copies a remote source file to a target file.

      @note: Internally, we have to go through and escape any spaces in the
      source and target paths with double-backslash, otherwise things get
      screwed up.  I hope this is portable to various different rcp methods,
      but I guess it might not be (all I have to test with is OpenSSH).

      @note: If you have user/group as strings, call the L{util.getUidGid} function
      to get the associated uid/gid as an ownership tuple.

      @param remoteUser: Name of the Cedar Backup user on the remote peer
      @type remoteUser: String representing a username, valid via the copy command

      @param remoteHost: Hostname of the remote peer
      @type remoteHost: String representing a hostname, accessible via the copy command

      @param rcpCommand: An rcp-compatible copy command to use for copying files
      @type rcpCommand: Command as a list to be passed to L{util.executeCommand}

      @param sourceFile: Source file to copy
      @type sourceFile: String representing a file on disk, as an absolute path

      @param targetFile: Target file to create
      @type targetFile: String representing a file on disk, as an absolute path

      @param ownership: Owner and group that the copied should have
      @type ownership: Tuple of numeric ids C{(uid, gid)}

      @param permissions: Permissions that the staged files should have
      @type permissions: UNIX permissions mode, specified in octal (i.e. C{0640}).

      @raise IOError: If there is an IO error copying the file
      @raise OSError: If there is an OS error changing permissions on the file
      """
      copySource = "%s@%s:%s" % (remoteUser, remoteHost, sourceFile.replace(" ", "\\ "))
      result = executeCommand(rcpCommand, [copySource, targetFile.replace(" ", "\\ ")])[0]
      if result != 0:
         raise IOError("Error (%d) copying file from remote host." % result)
      if ownership is not None:
         os.chown(targetFile, ownership[0], ownership[1])
      if permissions is not None:
         os.chmod(targetFile, permissions)
   _copyRemoteFile = staticmethod(_copyRemoteFile)

   def _pushLocalFile(remoteUser, remoteHost, rcpCommand, sourceFile, targetFile):
      """
      Copies a local source file to a remote host.

      @note: Internally, we have to go through and escape any spaces in the
      source and target paths with double-backslash, otherwise things get
      screwed up.  I hope this is portable to various different rcp methods,
      but I guess it might not be (all I have to test with is OpenSSH).

      @note: If you have user/group as strings, call the L{util.getUidGid} function
      to get the associated uid/gid as an ownership tuple.

      @param remoteUser: Name of the Cedar Backup user on the remote peer
      @type remoteUser: String representing a username, valid via the copy command

      @param remoteHost: Hostname of the remote peer
      @type remoteHost: String representing a hostname, accessible via the copy command

      @param rcpCommand: An rcp-compatible copy command to use for copying files
      @type rcpCommand: Command as a list to be passed to L{util.executeCommand}

      @param sourceFile: Source file to copy
      @type sourceFile: String representing a file on disk, as an absolute path

      @param targetFile: Target file to create
      @type targetFile: String representing a file on disk, as an absolute path

      @raise IOError: If there is an IO error copying the file
      @raise OSError: If there is an OS error changing permissions on the file
      """
      copyTarget = "%s@%s:%s" % (remoteUser, remoteHost, targetFile.replace(" ", "\\ "))
      result = executeCommand(rcpCommand, [sourceFile.replace(" ", "\\ "), copyTarget])[0]
      if result != 0:
         raise IOError("Error (%d) copying file to remote host." % result)
   _pushLocalFile = staticmethod(_pushLocalFile)

