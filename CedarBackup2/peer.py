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
# Copyright (c) 2004 Kenneth J. Pronovici.
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
@author: Kenneth J. Pronovici <pronovic@ieee.org>
"""


########################################################################
# Imported modules
########################################################################

# System modules
import os
import logging
import pwd
import grp
import shutil
import popen2
import tempfile
import sets

# Cedar Backup modules
from CedarBackup2.filesystem import FilesystemList


########################################################################
# Module-wide constants and variables
########################################################################

logger                  = logging.getLogger("CedarBackup2.peer")

DEF_RCP_COMMAND         = "/usr/bin/scp -B"
DEF_COLLECT_INDICATOR   = "cback.collect"
DEF_STAGE_INDICATOR     = "cback.stage"


########################################################################
# Public functions
########################################################################

#######################
# getUidGid() function
#######################

def getUidGcid(user, group):
   """
   Get the uid/gid associated with a user/group pair

   @param user: User name
   @type user: User name as a string

   @param group: Group name 
   @type group: Group name as a string

   @return Tuple (uid, gid) matching passed-in user and group.
   @raise ValueError: If the ownership user/group values are invalid
   """
   try:
      uid = pwd.getpwnam(user)[2]
      gid = grp.getgrnam(group)[2]
      logger.debug("Translated user/group %s/%s into uid/gid %d/%d." % (user, group, uid, gid))
      return (uid, gid)
   except Exception, e:
      logger.debug("Error looking up uid and gid for user/group %s/%s: %s" % (user, group, e))
      raise ValueError("Unable to lookup up uid and gid for passed in user/group.")


############################
# executeCommand() function
############################

def executeCommand(command, args, returnOutput=False):
   """
   Executes a shell command, hopefully in a safe way (UNIX-specific).

   This function exists to replace direct calls to os.popen() in the Cedar
   Backup code.  It's not safe to call a function such as os.popen() with
   untrusted arguments, since that can cause problems if the string contains
   non-safe variables or other constructs (imagine that the argument is
   $WHATEVER, but $WHATEVER contains something like "; rm -fR ~/; echo" in the
   current environment).

   It's safer to use popen4 (or popen2 or popen3) and pass a list rather than a
   string for the first argument.  When called this way, popen4 will use the
   list's first item as the command and the remainder of the list's items as
   arguments to that command.

   Under the normal case, the function will return a tuple of (status, None)
   where the status is the wait-encoded return status of the call per the
   Popen4 documentation.  If returnOutput is passed in as true, the function
   will return a tuple of (status, output) where output is a list of strings,
   one entry per line in the intermingled combination of stdout and stderr from
   the command.  Output is always logged to the logger.info() target, regardless
   of whether it's returned.

   @note: You cannot redirect output (i.e. 2>&1, 2>/dev/null, etc.) using this
   function.  The redirection string would be passed to the command just like
   any other argument.

   @param command: Shell command to execute
   @type command: String, just the command without any arguments

   @param args: List of arguments to the command
   @type args: List of individual arguments to the command

   @param returnOutput: Indicates whether to return the output of the command
   @type returnOutput: Boolean True or False

   @return Tuple of (result, output) as described above.
   """
   logger.debug("Executing command [%s] with args %s." % (command, args))
   output = []
   fields = [command]
   fields.extend(args)
   pipe = popen2.Popen4(fields)
   pipe.tochild.close()       # we'll never write to it, and this way we don't confuse anything.
   while True:
      line = pipe.fromchild.readline()
      if not line: break
      if returnOutput: output.append(line)
      logger.info(line[:-1]) # this way the log will (hopefully) get updated in realtime
   if returnOutput:
      return (pipe.wait(), output)
   else:
      return (pipe.wait(), None)


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
   interface shared with the RemotePeer class.

   @ivar name: Name of the peer
   @ivar collectDir: Path to the peer's collect directory (an absolute local path)
   """

   ####################
   # Interface methods
   ####################

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

      @raise ValueError: If collect directory is not an absolute path
      """
      if not os.path.isabsdir(collectDir):
         logger.debug("Collect directory [%s] not an absolute path." % collectDir)
         raise ValueError("Collect directory must be an absolute path.")
      self.name = name
      self.collectDir = collectDir

   def stagePeer(self, targetDir, ownership=None, permissions=None):
      """
      Stages data from the peer into the indicated local target directory.

      The collect and target directories must both already exist before this
      method is called.  If passed in, ownership and permissions will be
      applied to the files that are copied.

      @note: If you have user/group as strings, call the getUidGid() function
      to get the associated uid/gid as an ownership tuple.

      @param targetDir: Target directory to write data into
      @type targetDir: String representing a directory on disk

      @param ownership: Owner and group that the staged files should have
      @type ownership: Tuple of numeric ids (uid, gid)

      @param permissions: Permissions that the staged files should have
      @type permissions: UNIX permissions mode, typically specified in octal (i.e. 0640).

      @raise ValueError: If collect directory is not a directory or does not exist 
      @raise ValueError: If target directory is not a directory, does not exist or is not absolute.
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
      the collect directory doesn't exist, you'll naturally get back False.

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

      @note: If you have user/group as strings, call the getUidGid() function
      to get the associated uid/gid as an ownership tuple.

      @param stageIndicator: Name of the indicator file to write
      @type stageIndicator: String representing name of a file in the collect directory

      @param ownership: Owner and group that the indicator file should have
      @type ownership: Tuple of numeric ids (uid, gid)

      @param permissions: Permissions that the indicator file should have
      @type permissions: UNIX permissions mode, typically specified in octal (i.e. 0640).

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

   def _copyLocalDir(sourceDir, targetDir, ownership=None, permissions=None):
      """
      Copies files from the source directory to the target directory.

      This function is not recursive.  Only the files in the directory will be
      copied.   Ownership and permissions will be left at their default values
      if new values are not specified.  The source and target directories are
      allowed to be soft links to a directory, but besides that soft links are
      ignored.

      @note: This is a static method.

      @note: If you have user/group as strings, call the getUidGid() function
      to get the associated uid/gid as an ownership tuple.

      @param sourceDir Source directory
      @type sourceDir: String representing a directory on disk

      @param targetDir: Target directory
      @type targetDir: String representing a directory on disk

      @param ownership: Owner and group that the copied files should have
      @type ownership: Tuple of numeric ids (uid, gid)

      @param permissions: Permissions that the staged files should have
      @type permissions: UNIX permissions mode, typically specified in octal (i.e. 0640).

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

      If the source file is None then the target file will be created or
      overwritten as an empty file.  If the target file is None, this method is
      a no-op.  Attempting to copy a soft link or a directory will result in an
      exception.

      @note: This is a static method.

      @note: If you have user/group as strings, call the getUidGid() function
      to get the associated uid/gid as an ownership tuple.

      @param sourceFile Source file to copy
      @type sourceFile: String representing a file on disk (absolute path)

      @param targetFile: Target file to create
      @type targetFile: String representing a file on disk (absolute path)

      @param ownership: Owner and group that the copied should have
      @type ownership: Tuple of numeric ids (uid, gid)

      @param permissions: Permissions that the staged files should have
      @type permissions: UNIX permissions mode, typically specified in octal (i.e. 0640).

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
   interface shared with the LocalPeer class.

   @ivar name: Name of the peer (a valid DNS hostname)
   @ivar remoteUser: Name of the Cedar Backup user on the remote peer
   @ivar collectDir: Path to the peer's collect directory (an absolute path on the peer)
   @ivar rcpCommand: An rcp-compatible copy command to use for copying files from the peer
   """

   ####################
   # Interface methods
   ####################

   def __init__(self, name, remoteUser, collectDir, rcpCommand=None):
      """
      Initializes a remote backup peer.
      
      @param name: Name of the backup peer
      @type name: String, must be a valid DNS hostname

      @param remoteUser: Name of the Cedar Backup user on the remote peer
      @type remoteUser: String representing a username, valid via the copy command

      @param collectDir: Path to the peer's collect directory 
      @type collectDir: String representing an absolute path on the remote peer

      @param rcpCommand: An rcp-compatible copy command to use for copying files from the peer
      @type rcpCommand: String representing a system command

      @raise ValueError: If collect directory is not an absolute path
      """
      if not os.path.isabsdir(collectDir):
         raise ValueError("Collect directory must be an absolute path.")
      self.name = name
      self.remoteUser = remoteUser
      self.collectDir = collectDir
      if rcpCommand is None:
         self.rcpCommand = DEF_RCP_COMMAND
      else:
         self.rcpCommand = rcpCommand

   def stagePeer(self, targetDir, ownership=None, permissions=None):
      """
      Stages data from the peer into the indicated local target directory.

      The target directory must already exist before this method is called.  If
      passed in, ownership and permissions will be applied to the files that
      are copied.  

      @note: If you have user/group as strings, call the getUidGid() function
      to get the associated uid/gid as an ownership tuple.

      @param targetDir: Target directory to write data into
      @type targetDir: String representing a directory on disk

      @param ownership: Owner and group that the staged files should have
      @type ownership: Tuple of numeric ids (uid, gid)

      @param permissions: Permissions that the staged files should have
      @type permissions: UNIX permissions mode, typically specified in octal (i.e. 0640).

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
      RemotePeer._copyRemoteDir(self.remoteUser, self.name, self.rcpCommand, self.collectDir, targetDir, ownership, permissions)

   def checkCollectIndicator(self, collectIndicator=None):
      """
      Checks the collect indicator in the peer's staging directory.

      When a peer has completed collecting its backup files, it will write an
      empty indicator file into its collect directory.  This method checks to
      see whether that indicator has been written.  If the remote copy command
      fails, we return False as if the file weren't there.  We depend on the
      rcp command returning some sort of error if the file doesn't exist.

      If you need to, you can override the name of the collect indicator file
      by passing in a different name.

      @note: This method's behavior is UNIX-specific.  It depends on the
      ability of tempfile.NamedTemporaryFile() to create files that can be
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
         RemotePeer._copyRemoteFile(self.remoteUser, self.name, self.rcpCommand, sourceFile, targetFile.name)
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

      @note: If you have user/group as strings, call the getUidGid() function
      to get the associated uid/gid as an ownership tuple.

      @note: This method's behavior is UNIX-specific.  It depends on the
      ability of tempfile.NamedTemporaryFile() to create files that can be
      opened more than once.

      @param stageIndicator: Name of the indicator file to write
      @type stageIndicator: String representing name of a file in the collect directory

      @param ownership: Owner and group that the indicator file should have
      @type ownership: Tuple of numeric ids (uid, gid)

      @param permissions: Permissions that the indicator file should have
      @type permissions: UNIX permissions mode, typically specified in octal (i.e. 0640).

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
      RemotePeer._pushLocalFile(self.remoteUser, self.name, self.rcpCommand, sourceFile.name, targetFile)

   def _getDirContents(path):
      """
      Returns the contents of a directory in terms of a Set.
      
      The directory's contents are read as a FilesystemList() containing only
      files, and then the list is converted into a sets.Set object for later
      use.

      @note: This is a static method.

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

      @note: This is a static method.

      @note: If you have user/group as strings, call the getUidGid() function
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
      @type rcpCommand: String representing a system command

      @param sourceDir Source directory
      @type sourceDir: String representing a directory on disk

      @param targetDir: Target directory
      @type targetDir: String representing a directory on disk

      @param ownership: Owner and group that the copied files should have
      @type ownership: Tuple of numeric ids (uid, gid)

      @param permissions: Permissions that the staged files should have
      @type permissions: UNIX permissions mode, typically specified in octal (i.e. 0640).

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

      @note: This is a static method.

      @note: If you have user/group as strings, call the getUidGid() function
      to get the associated uid/gid as an ownership tuple.

      @param remoteUser: Name of the Cedar Backup user on the remote peer
      @type remoteUser: String representing a username, valid via the copy command

      @param remoteHost: Hostname of the remote peer
      @type remoteHost: String representing a hostname, accessible via the copy command

      @param rcpCommand: An rcp-compatible copy command to use for copying files
      @type rcpCommand: String representing a system command

      @param sourceFile Source file to copy
      @type sourceFile: String representing a file on disk (absolute path)

      @param targetFile: Target file to create
      @type targetFile: String representing a file on disk (absolute path)

      @param ownership: Owner and group that the copied should have
      @type ownership: Tuple of numeric ids (uid, gid)

      @param permissions: Permissions that the staged files should have
      @type permissions: UNIX permissions mode, typically specified in octal (i.e. 0640).

      @raise IOError: If there is an IO error copying the file
      @raise OSError: If there is an OS error changing permissions on the file
      """
      copySource = "%s@%s:%s" % (remoteUser, remoteHost, sourceFile)
      result = executeCommand(rcpCommand, [copySource, targetFile])[0]
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

      @note: This is a static method.

      @note: If you have user/group as strings, call the getUidGid() function
      to get the associated uid/gid as an ownership tuple.

      @param remoteUser: Name of the Cedar Backup user on the remote peer
      @type remoteUser: String representing a username, valid via the copy command

      @param remoteHost: Hostname of the remote peer
      @type remoteHost: String representing a hostname, accessible via the copy command

      @param rcpCommand: An rcp-compatible copy command to use for copying files
      @type rcpCommand: String representing a system command

      @param sourceFile Source file to copy
      @type sourceFile: String representing a file on disk (absolute path)

      @param targetFile: Target file to create
      @type targetFile: String representing a file on disk (absolute path)

      @raise IOError: If there is an IO error copying the file
      @raise OSError: If there is an OS error changing permissions on the file
      """
      copyTarget = "%s@%s:%s" % (remoteUser, remoteHost, targetFile)
      result = executeCommand(rcpCommand, [sourceFile, copyTarget])[0]
      if result != 0:
         raise IOError("Error (%d) copying file to remote host." % result)
   _pushLocalFile = staticmethod(_pushLocalFile)

