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
import sha
import logging
import tarfile

# Cedar Backup modules
from CedarBackup2.knapsack import firstFit, bestFit, worstFit, alternateFit


########################################################################
# Module-wide variables
########################################################################

logger = logging.getLogger("CedarBackup2.filesystem")


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
      logger.debug("Created new list with no configured exclusions.")
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
         logger.debug("Path [%s] is not a file or does not exist on disk." % path)
         raise ValueError("Path is not a file or does not exist on disk.")
      if self.excludeFiles or path in self.excludePaths:
         logger.debug("Path [%s] is excluded." % path)
         return 0
      for pattern in self.excludePatterns:
         if re.compile(pattern).match(path):
            logger.debug("Path [%s] is excluded." % path)
            return 0
      self.append(path)
      logger.debug("Added path [%s] into list." % path)
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
         logger.debug("Path [%s] is not a file or does not exist on disk." % path)
         raise ValueError("Path is not a directory or does not exist on disk.")
      if self.excludeDirs or path in self.excludePaths:
         logger.debug("Path [%s] is excluded based on exclude list." % path)
         return 0
      for pattern in self.excludePatterns:
         if re.compile(pattern).match(path):
            logger.debug("Path [%s] is excluded based on pattern [%s]." % (path, pattern))
            return 0
      self.append(path)
      logger.debug("Added path [%s] into list." % path)
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
         logger.debug("Path [%s] is not a directory or does not exist on disk." % path)
         raise ValueError("Path is not a directory or does not exist on disk.")
      if path in self.excludePaths:
         logger.debug("Path [%s] is excluded based on exclude list." % path)
         return added
      for pattern in self.excludePatterns:
         if re.compile(pattern).match(path):
            logger.debug("Path [%s] is excluded based on pattern [%s]." % (path, pattern))
            return added
      (root, dirs, files) = os.walk(path)
      if self.ignoreFile is not None and self.ignoreFile in files:
         logger.debug("Path [%s] is excluded based on ignore file." % path)
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
               logger.debug("Removed path [%s] from list." % entry)
               removed += 1
      else:
         compiled = re.compile(pattern)
         for entry in self[:]:
            if os.path.exists(entry) and os.path.isfile(entry):
               if compiled.match(entry):
                  self.remove(entry)
                  logger.debug("Removed path [%s] from list." % entry)
                  removed += 1
      logger.debug("Removed a total of %d entries." % removed);
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
               logger.debug("Removed path [%s] from list." % entry)
               removed += 1
      else:
         compiled = re.compile(pattern)
         for entry in self[:]:
            if os.path.exists(entry) and os.path.isdir(entry):
               if compiled.match(entry):
                  self.remove(entry)
                  logger.debug("Removed path [%s] from list based on pattern [%s]." % (entry, pattern))
                  removed += 1
      logger.debug("Removed a total of %d entries." % removed);
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
            logger.debug("Removed path [%s] from list based on pattern [%s]." % (entry, pattern))
            removed += 1
      logger.debug("Removed a total of %d entries." % removed);
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
            logger.debug("Removed path [%s] from list." % entry)
            removed += 1
      logger.debug("Removed a total of %d entries." % removed);
      return removed


   ##################
   # Utility methods
   ##################

   def normalize(self):
      """Normalizes the list, ensuring that each entry is unique."""
      orig = len(self)
      self.sort()
      dups = filter(lambda x, self=self: self[x] == self[x+1], range(0, len(self) - 1))
      items = map(lambda x, self=self: self[x], dups)
      map(self.remove, items)
      new = len(self)
      logger.debug("Completed normalizing list; removed %d items (%d originally, %d now)." % (new-orig, orig, new))

   def verify(self):
      """
      Verifies that all entries in the list exist on disk.
      @return: C{True} if all entries exist, C{False} otherwise.
      """
      for entry in self:
         if not os.path.exists(entry):
            logger.debug("Path [%s] is invalid; list is not valid." % entry)
            return False
      logger.debug("All entries in list are valid.")
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

   ##############
   # Constructor
   ##############

   def __init__(self):
      """Initializes a list with no configured exclusions."""
      logger.debug("Created new list with no configured exclusions.")


   ################################
   # Overridden superclass methods
   ################################

   def addDir(self, path):
      """
      Adds a directory to the list.
   
      This class does not allow directories to be added, so this overridden
      method just ignores the directory and returns zero

      @param path: Directory path to be added to the list (ignored)
      @type path: String representing a path on disk (ignored)

      @return: Always zero
      """
      logger.debug("Overriddent addDir(%s) is a no-op." % path)
      return 0


   ##################
   # Utility methods
   ##################

   def totalSize(self):
      """
      Returns the total size among all files in the list.
      @return: Total size, in bytes 
      """
      total = 0
      for entry in self:
         total += os.stat(entry)['st_size']
      return total

   def generateSizeMap(self):
      """
      Generates a mapping from file to file size in bytes.
      @return: Dictionary mapping file to file size
      """
      table = { }
      for entry in self:
         table[entry] = os.stat(entry)['st_size']
      return table

   def generateDigestMap(self):
      """
      Generates a mapping from file to file digest.

      Currently, the digest is an SHA hash, which should be pretty secure.  In
      the future, this might be a different kind of hash, but we guarantee that
      the type of the hash will not change unless the library major version
      number is bumped.

      @return: Dictionary mapping file to digest value
      """
      table = { }
      for entry in self:
         table[entry] = sha.new(open(entry).read()).hexdigest()
      return table

   def generateFitted(self, capacity, algorithm="worst_fit"):
      """
      Generates a list of items that fit in the indicated capacity.

      Sometimes, callers would like to include every item in a list, but are
      unable to because not all of the items fit in the space available.  This
      method returns a copy of the list, containing only the items that fit in
      a given capacity.  A copy is returned so that we don't lose any
      information if for some reason the fitted list is unsatisfactory.

      The fitting is done using the functions in the knapsack module.  By
      default, the first fit algorithm is used, but you can also choose
      from best fit, worst fit and alternate fit.

      @param capacity: Maximum capacity among the files in the new list
      @type capacity: Integer, in bytes

      @param algorithm: Knapsack (fit) algorithm to use
      @type algorithm: One of "first_fit", "best_fit", "worst_fit", "alternate_fit"
      
      @return: Copy of list with total size no larger than indicated capacity
      @raise ValueError: If the algorithm is invalid.
      """
      sizeMap = self.generateSizeMap()
      if algorithm == "first_fit": return firstFit(sizeMap, capacity)[0]
      elif algorithm == "best_fit": return bestFit(sizeMap, capacity)[0]
      elif algorithm == "worst_fit": return worstFit(sizeMap, capacity)[0]
      elif algorithm == "alternate_fit": return alternateFit(sizeMap, capacity)[0]
      else: raise ValueError("Algorithm [%s] is invalid." % algorithm);

   def generateTarfile(self, path, mode='tar'):
      """
      Creates a tar file containing the files in the list.

      By default, this method will create uncompressed tar files.  If you pass
      in mode C{'targz'}, then it will create gzipped tar files, and if you
      pass in mode C{'tarbz2'}, then it will create bzipped tar files.

      The tar file will be created as a GNU tar archive, which enables extended
      file name lengths, etc.  Since GNU tar is so prevalent, I've decided that
      the extra functionality out-weighs the disadvantage of not being
      "standard".

      Currently, the whole method call fails if there are problems adding any
      of the files to the archive (although the tar file may actually be
      created on disk even if there is a failure).  If an exception is thrown,
      callers are advised that they might want to call L{verify()} and then
      attempt to extract the tar file a second time, since the most common
      cause of failures is a missing file (a file that existed when the list
      was built, but is gone again by the time the tar file is built).

      @param path: Path of tar file to create on disk
      @type path: String representing a path on disk

      @param mode: Tar creation mode
      @type mode: One of either C{'tar'}, C{'targz'} or C{'tarbz2'}

      @raise ValueError: If mode is not valid
      @raise TarError: If there is a problem creating the tar file
      """
      if(mode == 'tar'): tarmode = "w:"
      elif(mode == 'targz'): tarmode = "w:gz"
      elif(mode == 'tarbz2'): tarmode = "w:bz2"
      else: raise ValueError("Mode [%s] is not valid." % mode)
      tar = tarfile.open(path, tarmode)
      for entry in self:
         tar.add(entry, recursive=False)
      tar.close()


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

   ##############
   # Constructor
   ##############

   def __init__(self):
      """Initializes a list with no configured exclusions."""
      FilesystemList.__init__(self)


   ##################
   # Utility methods
   ##################

   def purgeItems(self):
      """
      Purges all items in the list.

      Every item in the list will be purged.  Directories in the list will NOT
      be purged recursively, and hence will only be removed if they are empty.
      Errors will be ignored.
      
      To faciliate easy removal of directories that will end up being empty,
      the delete process happens in two passes: files first, then directories.
      """
      for entry in self:
         if os.path.exists(entry) and os.path.isfile(entry):
            try:
               os.path.remove(entry)
            except OSError:
               pass
      for entry in self:
         if os.path.exists(entry) and os.path.isdir(entry):
            try:
               os.path.rmdir(entry)
            except OSError:
               pass

