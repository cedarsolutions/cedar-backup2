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
# Purpose  : Provides filesystem-related objects.
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# This file was created with a width of 132 characters, and NO tabs.

########################################################################
# Module documentation
########################################################################

"""
Provides filesystem-related objects.
@author Kenneth J. Pronovici <pronovic@ieee.org>
"""


########################################################################
# Imported modules
########################################################################

# System modules
import os
import re


########################################################################
# FilesystemList class definition
########################################################################

class FilesystemList(list):

   ######################
   # Class documentation
   ######################

   """
   Represents a list of filesystem items.

   This is a generic class that represents a list of filesystem items.  Callers
   can add individual files or directories to the list, or can recursively add
   the contents of a directory.  The class also allows for up-front exclusions
   in several forms (all files, all directories, all items matching a pattern,
   or all directories containing a specific "ignore file").  Symbolic links are
   not supported.

   The custom methods such as L{addFile} will only add items if they exist on
   the filesystem and do not match any exclusions that are already in place.
   However, since a FilesystemList is a subclass of Python's standard list
   class, callers can also add items to the list in the usual way, using
   methods like C{append()} or C{insert()}.  No validations apply to items
   added to the list in this way.

   Once a list has been created, callers can remove individual items from the
   list using standard methods like C{pop()} or C{remove()} or they can use
   custom methods to remove specific types of entries or entries which match a
   particular pattern.

   @ivar excludeFiles: Boolean indicating whether files should be excluded
   @ivar excludeDirs: Boolean indicating whether directories should be excluded
   @ivar excludePaths: List of absolute paths to be excluded
   @ivar excludePatterns: List of regular expression patterns to be excluded
   @ivar ignoreFile: Name of file which will cause directory contents to be ignored
   """


   ##############
   # Constructor
   ##############

   def __init__(self):
      """Initializes a list with no configured exclusions."""
      list.__init__(self)
      self.excludeFiles = False
      self.excludeDirs = False
      self.excludePaths = []
      self.excludePatterns = []
      self.ignoreFile = None


   ##############
   # Add methods
   ##############

   def addFile(self, path):
      """
      Adds a file to the list.
   
      The path must exist and must be a file.  It will be added to the list
      subject to any exclusions that are in place.

      @param path: File path to be added to the list
      @type path: String representing a path on disk

      @return: Number of items added to the list.
      @raise ValueError: If path is not a file or does not exist.
      """
      if not os.path.exists(path) or not os.path.isfile(path):
         raise ValueError("Path is not a file or does not exist on disk.");
      if self.excludeFiles or path in self.excludePaths:
         return 0
      for pattern in self.excludePatterns:
         if re.compile(pattern).match(path):
            return 0
      self.append(path)
      return 1

   def addDir(self, path):
      """
      Adds a directory to the list.
   
      The path must exist and must be a directory.  It will be added to the 
      list subject to any exclusions that are in place.  The L{ignoreFile}
      does not apply to this method, only to L{addDirContents}.

      @param path: Directory path to be added to the list
      @type path: String representing a path on disk

      @return: Number of items added to the list.
      @raise ValueError: If path is not a directory or does not exist.
      """
      if not os.path.exists(path) or not os.path.isdir(path):
         raise ValueError("Path is not a directory or does not exist on disk.");
      if self.excludeDirs or path in self.excludePaths:
         return 0
      for pattern in self.excludePatterns:
         if re.compile(pattern).match(path):
            return 0
      self.append(path)
      return 1

   def addDirContents(self, path, recurse=True):
      """
      Adds the contents of a directory to the list.

      The path must exist and must be a directory.  The contents of the
      directory (as well as the directory path itself) will be added to the
      list, subject to any exclusions that are in place.  

      If C{recurse} is C{True}, then the contents of the directory will be
      added to the list recursively (i.e. the directory's children will be
      added, as well as all of their children, etc., etc.), subject to the same
      exclusions as usual.

      @note If a directory's absolute path matches an exclude pattern or path,
      or if the directory contains the configured ignore file, then the
      directory and all of its contents will be recursively excluded from the
      list.
   
      @note The L{excludeDirs} flag only controls whether the directory path
      itself is added to the list once it has been discovered.  It does I{not}
      affect whether the directory will actually be recursed into in search of
      other children.

      @param path: Directory path whose contents should be added to the list
      @type path: String representing a path on disk

      @return: Number of items recursively added to the list
      @raise ValueError: If path is not a directory or does not exist.
      """
      added = 0
      if not os.path.exists(path) or not os.path.isdir(path):
         raise ValueError("Path is not a directory or does not exist on disk.");
      if path in self.excludePaths:
         return added
      for pattern in self.excludePatterns:
         if re.compile(pattern).match(path):
            return added
      (root, dirs, files) = os.walk(path)
      if self.ignoreFile is not None and self.ignoreFile in files:
         return added
      added += self.addDir(path)
      for f in files:
         added += self.addFile(os.path.join(root, f))
      for d in dirs:
         if recurse:
            added += self.addDirContents(os.path.join(root, d), True)
         else:
            added += self.addDir(os.path.join(root, d))
      return added


   #################
   # Remove methods
   #################

   def removeFiles(self, pattern=None):
      """
      Removes file entries from the list.

      If C{pattern} is not passed in or is C{None}, then all file entries will
      be removed from the list.  Otherwise, only those file entries matching
      the pattern will be removed.  Any entry which does not exist on disk
      will be ignored (use L{removeInvalid} to purge those entries).

      This method might be fairly slow for large lists, since it must check the
      type of each item in the list.  If you know ahead of time that you want
      to exclude all files, then you will be better off setting L{excludeFiles}
      to C{True} before adding items to the list.

      @param pattern: Regular expression pattern representing entries to remove

      @return: Number of entries removed
      """
      removed = 0
      if pattern is None:
         for entry in self[:]:
            if os.path.exists(entry) and os.path.isfile(entry):
               self.remove(entry)
               removed += 1
      else:
         compiled = re.compile(pattern)
         for entry in self[:]:
            if os.path.exists(entry) and os.path.isfile(entry):
               if compiled.match(entry):
                  self.remove(entry)
                  removed += 1
      return removed

   def removeDirs(self, pattern=None):
      """
      Removes directory entries from the list.

      If C{pattern} is not passed in or is C{None}, then all directory entries
      will be removed from the list.  Otherwise, only those directory entries
      matching the pattern will be removed.  Any entry which does not exist on
      disk will be ignored (use L{removeInvalid} to purge those entries).

      This method might be fairly slow for large lists, since it must check the
      type of each item in the list.  If you know ahead of time that you want
      to exclude all directories, then you will be better off setting
      L{excludeDirs} to C{True} before adding items to the list (note that this
      will not prevent you from recursively adding the I{contents} of
      directories).

      @param pattern: Regular expression pattern representing entries to remove

      @return: Number of entries removed
      """
      removed = 0
      if pattern is None:
         for entry in self[:]:
            if os.path.exists(entry) and os.path.isdir(entry):
               self.remove(entry)
               removed += 1
      else:
         compiled = re.compile(pattern)
         for entry in self[:]:
            if os.path.exists(entry) and os.path.isdir(entry):
               if compiled.match(entry):
                  self.remove(entry)
                  removed += 1
      return removed

   def removeMatch(self, pattern):
      """
      Removes from the list all entries matching a pattern.

      This method removes from the list all entries which match the passed in
      C{pattern}.  Since there is no need to check the type of each entry, it
      is faster to call this method than to call the L{removeFiles},
      L{removeDirs} method individually.  If you know which patterns you will
      want to remove ahead of time, you may be better off setting
      L{excludePatterns} before adding items to the list.

      @param pattern: Regular expression pattern representing entries to remove

      @return: Number of entries removed.
      """
      removed = 0
      compiled = re.compile(pattern)
      for entry in self[:]:
         if compiled.match(entry):
            self.remove(entry)
            removed += 1
      return removed

   def removeInvalid(self):
      """
      Removes from the list all entries that do not exist on disk.

      This method removes from the list all entries which do not currently
      exist on disk in some form.  No attention is paid to whether the entries
      are files or directories.

      @return: Number of entries removed.
      """
      removed = 0
      for entry in self[:]:
         if not os.path.exists(entry):
            self.remove(entry)
            removed += 1
      return removed


   ##################
   # Utility methods
   ##################

   def normalize(self):
      """Normalizes the list, ensuring that each entry is unique."""
      self.sort()
      dups = filter(lambda x, self=self: self[x] == self[x+1], range(0, len(self) - 1))
      items = map(lambda x, self=self: self[x], dups)
      map(self.remove, items)

   def verify(self):
      """
      Verifies that all entries in the list exist on disk.
      @return: C{True} if all entries exist, C{False} otherwise.
      """
      for entry in self:
         if not os.path.exists(entry):
            return False
      return True


########################################################################
# BackupFileList class definition
########################################################################

class BackupFileList(FilesystemList):

   ######################
   # Class documentation
   ######################

   """
   List of files to be backed up.

   A BackupFileList is a L{FilesystemList} containing a list of files to be
   backed up.  It only contains files, not directories.  On top of the generic
   functionality provided by L{FilesystemList}, this class adds functionality
   to keep a hash (checksum) for each file in the list, and it also provides a
   method to calculate the total size of the files in the list and a way to
   export the list into tar form.
   """

   pass


########################################################################
# PurgeItemList class definition
########################################################################

class PurgeItemList(FilesystemList):

   ######################
   # Class documentation
   ######################

   """
   List of files and directories to be purged.

   A PurgeItemList is a L{FilesystemList} containing a list of files and
   directories to be purged.  On top of the generic functionality provided by
   L{FilesystemList}, this class adds functionality to purge the items in the
   list.
   """

   pass

