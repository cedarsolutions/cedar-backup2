#!/usr/bin/env python
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
# Purpose  : Tests filesystem-related objects.
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# This file was created with a width of 132 characters, and NO tabs.

########################################################################
# Module documentation
########################################################################

"""
Unit tests for CedarBackup2/filesystem.py.

Test Notes
==========

   This module contains individual tests for each of the objects implemented in
   filesystem.py: FilesystemList, BackupFileList and PurgeItemList.

   The BackupFileList and PurgeItemList classes inherit from FilesystemList,
   and the FilesystemList class itself inherits from the standard Python list
   class.  For the most part, I won't spend time testing inherited
   functionality, especially if it's already been tested.  However, I do test
   some of the base list functionality just to ensure that the inheritence has
   been constructed properly and everything seems to work as expected.

Naming Conventions
==================

   I prefer to avoid large unit tests which validate more than one piece of
   functionality.  Instead, I create lots of very small tests that each
   validate one specific thing.  These small tests are then named with an index
   number, yielding something like C{testAddDir_001} or C{testValidate_010}.
   Each method then has a docstring describing what it's supposed to
   accomplish.  I feel that this makes it easier to judge the extent of a
   problem when one exists.

Debugging these Tests
=====================

   Debugging in here can get be somewhat complicated.  If you have a test::

      def test():
        try:
           # stuff
        finally:
           # remove files

   you may mysteriously have the 'stuff' fail, and you won't get any exceptions
   reported to you.  The best thing to do if you get strange situations like
   this is to move 'stuff' out of the try block and re-run the test - that will
   usually clear things up.

@author Kenneth J. Pronovici <pronovic@ieee.org>
"""


########################################################################
# Import modules and do runtime validations
########################################################################

import sys
import os
import unittest
import tempfile
import tarfile
from CedarBackup2.filesystem import FilesystemList, BackupFileList, PurgeItemList


#######################################################################
# Module-wide configuration and constants
#######################################################################

DATA_DIRS = [ './data', './test/data' ]
RESOURCES = [ "tree1.tar.gz", "tree2.tar.gz", "tree3.tar.gz", "tree4.tar.gz", "tree5.tar.gz", "tree6.tar.gz" ]

INVALID_FILE = "bogus.file"         # This file name should never exist


####################
# Utility functions
####################

def findData():
   """Returns a dictionary of locations for various resources."""
   data = { }
   for resource in RESOURCES:
      for datadir in DATA_DIRS:
         path = os.path.join(datadir, resource);
         if os.path.exists(path):
            data[resource] = path
            break
      else:
         raise Exception("Unable to find resource [%s]." % resource)
   return data

def extractTar(tmpdir, filepath):
   """Extracts the indicated tar file to self.tmpdir."""
   tar = tarfile.open(filepath)
   for tarinfo in tar:
      tar.extract(tarinfo, tmpdir)


#######################################################################
# Test Case Classes
#######################################################################

###########################
# TestFilesystemList class
###########################

class TestFilesystemList(unittest.TestCase):

   """Tests for the FilesystemList object."""

   ################
   # Setup methods
   ################

   def setUp(self):
      try:
         self.tmpdir = tempfile.mkdtemp()
         self.data = findData()
      except Exception, e:
         self.fail(e)

   def tearDown(self):
      try:
         os.removedirs(self.tmpdir)
      except: pass


   ################################
   # Test basic list functionality
   ################################
         
   def testBasic_001(self):
      """
      Test the append() method.
      """
      fsList = FilesystemList()
      self.failUnlessEqual([], fsList)
      fsList.append('a')
      self.failUnlessEqual(['a'], fsList)
      fsList.append('b')
      self.failUnlessEqual(['a', 'b'], fsList)

   def testBasic_002(self):
      """
      Test the insert() method.
      """
      fsList = FilesystemList()
      self.failUnlessEqual([], fsList)
      fsList.insert(0, 'a')
      self.failUnlessEqual(['a'], fsList)
      fsList.insert(0, 'b')
      self.failUnlessEqual(['b', 'a'], fsList)

   def testBasic_003(self):
      """
      Test the remove() method.
      """
      fsList = FilesystemList()
      self.failUnlessEqual([], fsList)
      fsList.insert(0, 'a')
      fsList.insert(0, 'b')
      self.failUnlessEqual(['b', 'a'], fsList)
      fsList.remove('a')
      self.failUnlessEqual(['b'], fsList)
      fsList.remove('b')
      self.failUnlessEqual([], fsList)

   def testBasic_004(self):
      """
      Test the pop() method.
      """
      fsList = FilesystemList()
      self.failUnlessEqual([], fsList)
      fsList.append('a')
      fsList.append('b')
      fsList.append('c')
      fsList.append('d')
      fsList.append('e')
      self.failUnlessEqual(['a', 'b', 'c', 'd', 'e'], fsList)
      self.failUnlessEqual('e', fsList.pop())
      self.failUnlessEqual(['a', 'b', 'c', 'd'], fsList)
      self.failUnlessEqual('d', fsList.pop())
      self.failUnlessEqual(['a', 'b', 'c'], fsList)
      self.failUnlessEqual('c', fsList.pop())
      self.failUnlessEqual(['a', 'b'], fsList)
      self.failUnlessEqual('b', fsList.pop())
      self.failUnlessEqual(['a'], fsList)
      self.failUnlessEqual('a', fsList.pop())
      self.failUnlessEqual([], fsList)

   def testBasic_005(self):
      """
      Test the count() method.
      """
      fsList = FilesystemList()
      self.failUnlessEqual([], fsList)
      fsList.append('a')
      fsList.append('b')
      fsList.append('c')
      fsList.append('d')
      fsList.append('e')
      self.failUnlessEqual(['a', 'b', 'c', 'd', 'e'], fsList)
      self.failUnlessEqual(1, fsList.count('a'))

   def testBasic_006(self):
      """
      Test the index() method.
      """
      fsList = FilesystemList()
      self.failUnlessEqual([], fsList)
      fsList.append('a')
      fsList.append('b')
      fsList.append('c')
      fsList.append('d')
      fsList.append('e')
      self.failUnlessEqual(['a', 'b', 'c', 'd', 'e'], fsList)
      self.failUnlessEqual(2, fsList.index('c'))

   def testBasic_007(self):
      """
      Test the reverse() method.
      """
      fsList = FilesystemList()
      self.failUnlessEqual([], fsList)
      fsList.append('a')
      fsList.append('b')
      fsList.append('c')
      fsList.append('d')
      fsList.append('e')
      self.failUnlessEqual(['a', 'b', 'c', 'd', 'e'], fsList)
      fsList.reverse()
      self.failUnlessEqual(['e', 'd', 'c', 'b', 'a'], fsList)
      fsList.reverse()
      self.failUnlessEqual(['a', 'b', 'c', 'd', 'e'], fsList)

   def testBasic_008(self):
      """
      Test the sort() method.
      """
      fsList = FilesystemList()
      self.failUnlessEqual([], fsList)
      fsList.append('e')
      fsList.append('d')
      fsList.append('c')
      fsList.append('b')
      fsList.append('a')
      self.failUnlessEqual(['e', 'd', 'c', 'b', 'a'], fsList)
      fsList.sort()
      self.failUnlessEqual(['a', 'b', 'c', 'd', 'e'], fsList)
      fsList.sort()
      self.failUnlessEqual(['a', 'b', 'c', 'd', 'e'], fsList)

   def testBasic_009(self):
      """
      Test slicing.
      """
      fsList = FilesystemList()
      self.failUnlessEqual([], fsList)
      fsList.append('e')
      fsList.append('d')
      fsList.append('c')
      fsList.append('b')
      fsList.append('a')
      self.failUnlessEqual(['e', 'd', 'c', 'b', 'a'], fsList)
      self.failUnlessEqual(['e', 'd', 'c', 'b', 'a'], fsList[:])
      self.failUnlessEqual(['e', 'd', 'c', 'b', 'a'], fsList[0:])
      self.failUnlessEqual('e', fsList[0])
      self.failUnlessEqual('a', fsList[4])
      self.failUnlessEqual(['d', 'c', 'b'], fsList[1:4])


   #################
   # Test addFile()
   #################
         
   def testAddFile_001(self):
      """
      Attempt to add a file that doesn't exist; no exclusions.
      """
      pass

   def testAddFile_002(self):
      """
      Attempt to add a directory; no exclusions.
      """
      pass

   def testAddFile_003(self):
      """
      Attempt to add a soft link; no exclusions.
      """
      pass

   def testAddFile_004(self):
      """
      Attempt to add an existing file; no exclusions.
      """
      pass

   def testAddFile_005(self):
      """
      Attempt to add a file that doesn't exist; excludeFiles set.
      """
      pass

   def testAddFile_006(self):
      """
      Attempt to add a directory; excludeFiles set.
      """
      pass

   def testAddFile_007(self):
      """
      Attempt to add a soft link; excludeFiles set.
      """
      pass

   def testAddFile_008(self):
      """
      Attempt to add an existing file; excludeFiles set.
      """
      pass

   def testAddFile_009(self):
      """
      Attempt to add a file that doesn't exist; excludeDirs set.
      """
      pass

   def testAddFile_010(self):
      """
      Attempt to add a directory; excludeDirs set.
      """
      pass

   def testAddFile_011(self):
      """
      Attempt to add a soft link; excludeDirs set.
      """
      pass

   def testAddFile_012(self):
      """
      Attempt to add an existing file; excludeDirs set.
      """
      pass

   def testAddFile_013(self):
      """
      Attempt to add a file that doesn't exist; with excludePaths including the
      path.
      """
      pass

   def testAddFile_014(self):
      """
      Attempt to add a directory; with excludePaths including the path.
      """
      pass

   def testAddFile_015(self):
      """
      Attempt to add a soft link; with excludePaths including the path.
      """
      pass

   def testAddFile_016(self):
      """
      Attempt to add an existing file; with excludePaths including the path.
      """
      pass

   def testAddFile_017(self):
      """
      Attempt to add a file that doesn't exist; with excludePaths not including
      the path.
      """
      pass

   def testAddFile_018(self):
      """
      Attempt to add a directory; with excludePaths not including the path.
      """
      pass

   def testAddFile_019(self):
      """
      Attempt to add a soft link; with excludePaths not including the path.
      """
      pass

   def testAddFile_020(self):
      """
      Attempt to add an existing file; with excludePaths not including the path.
      """
      pass

   def testAddFile_021(self):
      """
      Attempt to add a file that doesn't exist; with excludePatterns matching
      the path.
      """
      pass

   def testAddFile_022(self):
      """
      Attempt to add a directory; with excludePatterns matching the path.
      """
      pass

   def testAddFile_023(self):
      """
      Attempt to add a soft link; with excludePatterns matching the path.
      """
      pass

   def testAddFile_024(self):
      """
      Attempt to add an existing file; with excludePatterns matching the path.
      """
      pass

   def testAddFile_025(self):
      """
      Attempt to add a file that doesn't exist; with excludePatterns not
      matching the path.
      """
      pass

   def testAddFile_026(self):
      """
      Attempt to add a directory; with excludePatterns not matching the path.
      """
      pass

   def testAddFile_027(self):
      """
      Attempt to add a soft link; with excludePatterns not matching the path.
      """
      pass

   def testAddFile_028(self):
      """
      Attempt to add an existing file; with excludePatterns not matching the
      path.
      """
      pass


   ################
   # Test addDir()
   ################
         
   def testAddDir_001(self):
      """
      Attempt to add a directory that doesn't exist; no exclusions.
      """
      pass

   def testAddDir_002(self):
      """
      Attempt to add a file; no exclusions.
      """
      pass

   def testAddDir_003(self):
      """
      Attempt to add a soft link; no exclusions.
      """
      pass

   def testAddDir_004(self):
      """
      Attempt to add an existing directory; no exclusions.
      """
      pass

   def testAddDir_005(self):
      """
      Attempt to add a directory that doesn't exist; excludeFiles set.
      """
      pass

   def testAddDir_006(self):
      """
      Attempt to add a file; excludeFiles set.
      """
      pass

   def testAddDir_007(self):
      """
      Attempt to add a soft link; excludeFiles set.
      """
      pass

   def testAddDir_008(self):
      """
      Attempt to add an existing directory; excludeFiles set.
      """
      pass

   def testAddDir_009(self):
      """
      Attempt to add a directory that doesn't exist; excludeDirs set.
      """
      pass

   def testAddDir_010(self):
      """
      Attempt to add a file; excludeDirs set.
      """
      pass

   def testAddDir_011(self):
      """
      Attempt to add a soft link; excludeDirs set.
      """
      pass

   def testAddDir_012(self):
      """
      Attempt to add an existing directory; excludeDirs set.
      """
      pass

   def testAddDir_013(self):
      """
      Attempt to add a directory that doesn't exist; with excludePaths
      including the path.
      """
      pass

   def testAddDir_014(self):
      """
      Attempt to add a file; with excludePaths including the path.
      """
      pass

   def testAddDir_015(self):
      """
      Attempt to add a soft link; with excludePaths including the path.
      """
      pass

   def testAddDir_016(self):
      """
      Attempt to add an existing directory; with excludePaths including the
      path.
      """
      pass

   def testAddDir_017(self):
      """
      Attempt to add a directory that doesn't exist; with excludePaths not
      including the path.
      """
      pass

   def testAddDir_018(self):
      """
      Attempt to add a file; with excludePaths not including the path.
      """
      pass

   def testAddDir_019(self):
      """
      Attempt to add a soft link; with excludePaths not including the path.
      """
      pass

   def testAddDir_020(self):
      """
      Attempt to add an existing directory; with excludePaths not including the
      path.
      """
      pass

   def testAddDir_021(self):
      """
      Attempt to add a directory that doesn't exist; with excludePatterns
      matching the path.
      """
      pass

   def testAddDir_022(self):
      """
      Attempt to add a file; with excludePatterns matching the path.
      """
      pass

   def testAddDir_023(self):
      """
      Attempt to add a soft link; with excludePatterns matching the path.
      """
      pass

   def testAddDir_024(self):
      """
      Attempt to add an existing directory; with excludePatterns matching the
      path.
      """
      pass

   def testAddDir_025(self):
      """
      Attempt to add a directory that doesn't exist; with excludePatterns not
      matching the path.
      """
      pass

   def testAddDir_026(self):
      """
      Attempt to add a file; with excludePatterns not matching the path.
      """
      pass

   def testAddDir_027(self):
      """
      Attempt to add a soft link; with excludePatterns not matching the path.
      """
      pass

   def testAddDir_028(self):
      """
      Attempt to add an existing directory; with excludePatterns not matching
      the path.
      """
      pass


   ########################
   # Test addDirContents()
   ########################
         
   def testAddDirContents_001(self):
      """
      Attempt to add a directory that doesn't exist; no exclusions.
      """
      pass

   def testAddDirContents_002(self):
      """
      Attempt to add a file; no exclusions.
      """
      pass

   def testAddDirContents_003(self):
      """
      Attempt to add a soft link; no exclusions.
      """
      pass

   def testAddDirContents_004(self):
      """
      Attempt to add an empty directory containing ignore file; no exclusions.
      """
      pass

   def testAddDirContents_005(self):
      """
      Attempt to add an empty directory; no exclusions.
      """
      pass

   def testAddDirContents_006(self):
      """
      Attempt to add an non-empty directory containing ignore file; no
      exclusions.
      """
      pass

   def testAddDirContents_007(self):
      """
      Attempt to add an non-empty directory; no exclusions.
      """
      pass

   def testAddDirContents_008(self):
      """
      Attempt to add a directory that doesn't exist; excludeFiles set.
      """
      pass

   def testAddDirContents_009(self):
      """
      Attempt to add a file; excludeFiles set.
      """
      pass

   def testAddDirContents_010(self):
      """
      Attempt to add a soft link; excludeFiles set.
      """
      pass

   def testAddDirContents_011(self):
      """
      Attempt to add an empty directory containing ignore file; excludeFiles set.
      """
      pass

   def testAddDirContents_012(self):
      """
      Attempt to add an empty directory; excludeFiles set.
      """
      pass

   def testAddDirContents_013(self):
      """
      Attempt to add an non-empty directory containing ignore file; excludeFiles set.
      """
      pass

   def testAddDirContents_014(self):
      """
      Attempt to add an non-empty directory; excludeFiles set.
      """
      pass

   def testAddDirContents_015(self):
      """
      Attempt to add a directory that doesn't exist; excludeDirs set.
      """
      pass

   def testAddDirContents_016(self):
      """
      Attempt to add a file; excludeDirs set.
      """
      pass

   def testAddDirContents_017(self):
      """
      Attempt to add a soft link; excludeDirs set.
      """
      pass

   def testAddDirContents_018(self):
      """
      Attempt to add an empty directory containing ignore file; excludeDirs set.
      """
      pass

   def testAddDirContents_019(self):
      """
      Attempt to add an empty directory; excludeDirs set.
      """
      pass

   def testAddDirContents_020(self):
      """
      Attempt to add an non-empty directory containing ignore file; excludeDirs set.
      """
      pass

   def testAddDirContents_021(self):
      """
      Attempt to add an non-empty directory; excludeDirs set.
      """
      pass

   def testAddDirContents_022(self):
      """
      Attempt to add a directory that doesn't exist; with excludePaths
      including the path.
      """
      pass

   def testAddDirContents_023(self):
      """
      Attempt to add a file; with excludePaths including the path.
      """
      pass

   def testAddDirContents_024(self):
      """
      Attempt to add a soft link; with excludePaths including the path.
      """
      pass

   def testAddDirContents_025(self):
      """
      Attempt to add an empty directory containing ignore file; with
      excludePaths including the path.
      """
      pass

   def testAddDirContents_026(self):
      """
      Attempt to add an empty directory; with excludePaths including the path.
      """
      pass

   def testAddDirContents_027(self):
      """
      Attempt to add an non-empty directory containing ignore file; with
      excludePaths including the path.
      """
      pass

   def testAddDirContents_028(self):
      """
      Attempt to add an non-empty directory; with excludePaths including the
      path.
      """
      pass

   def testAddDirContents_029(self):
      """
      Attempt to add a directory that doesn't exist; with excludePaths not
      including the path.
      """
      pass

   def testAddDirContents_030(self):
      """
      Attempt to add a file; with excludePaths not including the path.
      """
      pass

   def testAddDirContents_031(self):
      """
      Attempt to add a soft link; with excludePaths not including the path.
      """
      pass

   def testAddDirContents_032(self):
      """
      Attempt to add an empty directory containing ignore file; with
      excludePaths not including the path.
      """
      pass

   def testAddDirContents_033(self):
      """
      Attempt to add an empty directory; with excludePaths not including the
      path.
      """
      pass

   def testAddDirContents_034(self):
      """
      Attempt to add an non-empty directory containing ignore file; with
      excludePaths not including the path.
      """
      pass

   def testAddDirContents_035(self):
      """
      Attempt to add an non-empty directory; with excludePaths not including
      the path.
      """
      pass

   def testAddDirContents_036(self):
      """
      Attempt to add a directory that doesn't exist; with excludePatterns
      matching the path.
      """
      pass

   def testAddDirContents_038(self):
      """
      Attempt to add a file; with excludePatterns matching the path.
      """
      pass

   def testAddDirContents_039(self):
      """
      Attempt to add a soft link; with excludePatterns matching the path.
      """
      pass

   def testAddDirContents_040(self):
      """
      Attempt to add an empty directory containing ignore file; with
      excludePatterns matching the path.
      """
      pass

   def testAddDirContents_041(self):
      """
      Attempt to add an empty directory; with excludePatterns matching the
      path.
      """
      pass

   def testAddDirContents_042(self):
      """
      Attempt to add an non-empty directory containing ignore file; with
      excludePatterns matching the path.
      """
      pass

   def testAddDirContents_043(self):
      """
      Attempt to add an non-empty directory; with excludePatterns matching the
      path.
      """
      pass

   def testAddDirContents_044(self):
      """
      Attempt to add a directory that doesn't exist; with excludePatterns not
      matching the path.
      """
      pass

   def testAddDirContents_045(self):
      """
      Attempt to add a file; with excludePatterns not matching the path.
      """
      pass

   def testAddDirContents_046(self):
      """
      Attempt to add a soft link; with excludePatterns not matching the path.
      """
      pass

   def testAddDirContents_047(self):
      """
      Attempt to add an empty directory containing ignore file; with
      excludePatterns not matching the path.
      """
      pass

   def testAddDirContents_048(self):
      """
      Attempt to add an empty directory; with excludePatterns not matching the
      path.
      """
      pass

   def testAddDirContents_049(self):
      """
      Attempt to add an non-empty directory containing ignore file; with
      excludePatterns not matching the path.
      """
      pass

   def testAddDirContents_050(self):
      """
      Attempt to add an non-empty directory; with excludePatterns not matching
      the path.
      """
      pass


   #####################
   # Test removeFiles()
   #####################
         
   def testRemoveFiles_001(self):
      """
      Test with an empty list and a pattern of None.
      """
      pass

   def testRemoveFiles_002(self):
      """
      Test with an empty list and a non-empty pattern.
      """
      pass

   def testRemoveFiles_003(self):
      """
      Test with a non-empty list (files only) and a pattern of None.
      """
      pass

   def testRemoveFiles_004(self):
      """
      Test with a non-empty list (directories only) and a pattern of None.
      """
      pass

   def testRemoveFiles_005(self):
      """
      Test with a non-empty list (files and directories) and a pattern of None.
      """
      pass

   def testRemoveFiles_006(self):
      """
      Test with a non-empty list (files and directories, some nonexistent) and
      a pattern of None.
      """
      pass

   def testRemoveFiles_007(self):
      """
      Test with a non-empty list (files only) and a non-empty pattern that
      matches none of them.
      """
      pass

   def testRemoveFiles_008(self):
      """
      Test with a non-empty list (directories only) and a non-empty pattern
      that matches none of them.
      """
      pass

   def testRemoveFiles_009(self):
      """
      Test with a non-empty list (files and directories) and a non-empty
      pattern that matches none of them.
      """
      pass

   def testRemoveFiles_010(self):
      """
      Test with a non-empty list (files and directories, some nonexistent) and
      a non-empty pattern that matches none of them.
      """
      pass

   def testRemoveFiles_011(self):
      """
      Test with a non-empty list (files only) and a non-empty pattern that
      matches some of them.
      """
      pass

   def testRemoveFiles_012(self):
      """
      Test with a non-empty list (directories only) and a non-empty pattern
      that matches some of them.
      """
      pass

   def testRemoveFiles_013(self):
      """
      Test with a non-empty list (files and directories) and a non-empty
      pattern that matches some of them.
      """
      pass

   def testRemoveFiles_014(self):
      """
      Test with a non-empty list (files and directories, some nonexistent) and
      a non-empty pattern that matches some of them.
      """
      pass

   def testRemoveFiles_015(self):
      """
      Test with a non-empty list (files only) and a non-empty pattern that
      matches all of them.
      """
      pass

   def testRemoveFiles_016(self):
      """
      Test with a non-empty list (directories only) and a non-empty pattern
      that matches all of them.
      """
      pass

   def testRemoveFiles_017(self):
      """
      Test with a non-empty list (files and directories) and a non-empty
      pattern that matches all of them.
      """
      pass

   def testRemoveFiles_018(self):
      """
      Test with a non-empty list (files and directories, some nonexistent) and
      a non-empty pattern that matches all of them.
      """
      pass


   ####################
   # Test removeDirs()
   ####################
         
   def testRemoveDirs_001(self):
      """
      Test with an empty list and a pattern of None.
      """
      pass

   def testRemoveDirs_002(self):
      """
      Test with an empty list and a non-empty pattern.
      """
      pass

   def testRemoveDirs_003(self):
      """
      Test with a non-empty list (files only) and a pattern of None.
      """
      pass

   def testRemoveDirs_004(self):
      """
      Test with a non-empty list (directories only) and a pattern of None.
      """
      pass

   def testRemoveDirs_005(self):
      """
      Test with a non-empty list (files and directories) and a pattern of None.
      """
      pass

   def testRemoveDirs_006(self):
      """
      Test with a non-empty list (files and directories, some nonexistent) and
      a pattern of None.
      """
      pass

   def testRemoveDirs_007(self):
      """
      Test with a non-empty list (files only) and a non-empty pattern that
      matches none of them.
      """
      pass

   def testRemoveDirs_008(self):
      """
      Test with a non-empty list (directories only) and a non-empty pattern
      that matches none of them.
      """
      pass

   def testRemoveDirs_009(self):
      """
      Test with a non-empty list (files and directories) and a non-empty
      pattern that matches none of them.
      """
      pass

   def testRemoveDirs_010(self):
      """
      Test with a non-empty list (files and directories, some nonexistent) and
      a non-empty pattern that matches none of them.
      """
      pass

   def testRemoveDirs_011(self):
      """
      Test with a non-empty list (files only) and a non-empty pattern that
      matches some of them.
      """
      pass

   def testRemoveDirs_012(self):
      """
      Test with a non-empty list (directories only) and a non-empty pattern
      that matches some of them.
      """
      pass

   def testRemoveDirs_013(self):
      """
      Test with a non-empty list (files and directories) and a non-empty
      pattern that matches some of them.
      """
      pass

   def testRemoveDirs_014(self):
      """
      Test with a non-empty list (files and directories, some nonexistent) and
      a non-empty pattern that matches some of them.
      """
      pass

   def testRemoveDirs_015(self):
      """
      Test with a non-empty list (files only) and a non-empty pattern that
      matches all of them.
      """
      pass

   def testRemoveDirs_016(self):
      """
      Test with a non-empty list (directories only) and a non-empty pattern
      that matches all of them.
      """
      pass

   def testRemoveDirs_017(self):
      """
      Test with a non-empty list (files and directories) and a non-empty
      pattern that matches all of them.
      """
      pass

   def testRemoveDirs_018(self):
      """
      Test with a non-empty list (files and directories, some nonexistent) and
      a non-empty pattern that matches all of them.
      """
      pass


   #####################
   # Test removeMatch()
   #####################
         
   def testRemoveMatch_001(self):
      """
      Test with an empty list and a pattern of None.
      """
      pass

   def testRemoveMatch_002(self):
      """
      Test with an empty list and a non-empty pattern.
      """
      pass

   def testRemoveMatch_003(self):
      """
      Test with a non-empty list (files only) and a non-empty pattern that
      matches none of them.
      """
      pass

   def testRemoveMatch_004(self):
      """
      Test with a non-empty list (directories only) and a non-empty pattern
      that matches none of them.
      """
      pass

   def testRemoveMatch_005(self):
      """
      Test with a non-empty list (files and directories) and a non-empty
      pattern that matches none of them.
      """
      pass

   def testRemoveMatch_006(self):
      """
      Test with a non-empty list (files and directories, some nonexistent) and
      a non-empty pattern that matches none of them.
      """
      pass

   def testRemoveMatch_007(self):
      """
      Test with a non-empty list (files only) and a non-empty pattern that
      matches some of them.
      """
      pass

   def testRemoveMatch_008(self):
      """
      Test with a non-empty list (directories only) and a non-empty pattern
      that matches some of them.
      """
      pass

   def testRemoveMatch_009(self):
      """
      Test with a non-empty list (files and directories) and a non-empty
      pattern that matches some of them.
      """
      pass

   def testRemoveMatch_010(self):
      """
      Test with a non-empty list (files and directories, some nonexistent) and
      a non-empty pattern that matches some of them.
      """
      pass

   def testRemoveMatch_011(self):
      """
      Test with a non-empty list (files only) and a non-empty pattern that
      matches all of them.
      """
      pass

   def testRemoveMatch_012(self):
      """
      Test with a non-empty list (directories only) and a non-empty pattern
      that matches all of them.
      """
      pass

   def testRemoveMatch_013(self):
      """
      Test with a non-empty list (files and directories) and a non-empty
      pattern that matches all of them.
      """
      pass

   def testRemoveMatch_014(self):
      """
      Test with a non-empty list (files and directories, some nonexistent) and
      a non-empty pattern that matches all of them.
      """
      pass


   #######################
   # Test removeInvalid()
   #######################
         
   def testRemoveInvalid_001(self):
      """
      Test with an empty list.
      """
      pass

   def testRemoveInvalid_002(self):
      """
      Test with a non-empty list containing only invalid entries (files only).
      """
      pass

   def testRemoveInvalid_003(self):
      """
      Test with a non-empty list containing only valid entries (files only).
      """
      pass

   def testRemoveInvalid_004(self):
      """
      Test with a non-empty list containing only valid entries (directories
      only).
      """
      pass

   def testRemoveInvalid_005(self):
      """
      Test with a non-empty list containing only valid entries (files and
      directories).
      """
      pass

   def testRemoveInvalid_006(self):
      """
      Test with a non-empty list containing valid and invalid entries (files
      only).
      """
      pass

   def testRemoveInvalid_007(self):
      """
      Test with a non-empty list containing valid and invalid entries
      (directories only).
      """
      pass

   def testRemoveInvalid_008(self):
      """
      Test with a non-empty list containing valid and invalid entries (files
      and directories).
      """
      pass


   ###################
   # Test normalize()
   ###################
         
   def testNormalize_001(self):
      """
      Test with an empty list.
      """
      pass

   def testNormalize_002(self):
      """
      Test with a list containing one entry.
      """
      pass

   def testNormalize_003(self):
      """
      Test with a list containing two entries, no duplicates.
      """
      pass

   def testNormalize_004(self):
      """
      Test with a list containing two entries, with duplicates.
      """
      pass

   def testNormalize_005(self):
      """
      Test with a list containing many entries, no duplicates.
      """
      pass

   def testNormalize_006(self):
      """
      Test with a list containing many entries, with duplicates.
      """
      pass


   ################
   # Test verify()
   ################
         
   def testVerify_001(self):
      """
      Test with an empty list.
      """
      pass

   def testVerify_002(self):
      """
      Test with a non-empty list containing only invalid entries (files only).
      """
      pass

   def testVerify_003(self):
      """
      Test with a non-empty list containing only valid entries (files only).
      """
      pass

   def testVerify_004(self):
      """
      Test with a non-empty list containing only valid entries (directories
      only).
      """
      pass

   def testVerify_005(self):
      """
      Test with a non-empty list containing only valid entries (files and
      directories).
      """
      pass

   def testVerify_006(self):
      """
      Test with a non-empty list containing valid and invalid entries (files
      only).
      """
      pass

   def testVerify_007(self):
      """
      Test with a non-empty list containing valid and invalid entries
      (directories only).
      """
      pass

   def testVerify_008(self):
      """
      Test with a non-empty list containing valid and invalid entries (files
      and directories).
      """
      pass


###########################
# TestBackupFileList class
###########################

class TestBackupFileList(unittest.TestCase):

   """Tests for the BackupFileList object."""

   ################
   # Setup methods
   ################

   def setUp(self):
      try:
         self.data = findData()
      except Exception, e:
         self.fail(e)

   def tearDown(self):
      pass


   ################
   # Test addDir()
   ################
         
   def testAddDir_001(self):
      """
      Test that function is overridden with empty list, no exclusions.
      """
      pass

   def testAddDir_002(self):
      """
      Test that function is overridden with non-empty list, no exclusions.
      """
      pass

   def testAddDir_003(self):
      """
      Test that function is overridden with empty list, excludeFiles sets.
      """
      pass

   def testAddDir_004(self):
      """
      Test that function is overridden with non-empty list, excludeFiles sets.
      """
      pass

   def testAddDir_005(self):
      """
      Test that function is overridden with empty list, excludeDirs sets.
      """
      pass

   def testAddDir_006(self):
      """
      Test that function is overridden with non-empty list, excludeDirs sets.
      """
      pass

   def testAddDir_007(self):
      """
      Test that function is overridden with empty list, excludePaths sets.
      """
      pass

   def testAddDir_008(self):
      """
      Test that function is overridden with non-empty list, excludePaths sets.
      """
      pass

   def testAddDir_009(self):
      """
      Test that function is overridden with empty list, excludePatterns sets.
      """
      pass

   def testAddDir_010(self):
      """
      Test that function is overridden with non-empty list, excludePatterns sets.
      """
      pass


   ###################
   # Test totalSize()
   ###################
         
   def testTotalSize_001(self):
      """
      Test on an empty list.
      """
      pass

   def testTotalSize_002(self):
      """
      Test on a non-empty list containing a directory.
      """
      pass

   def testTotalSize_003(self):
      """
      Test on a non-empty list containing a non-existent file.
      """
      pass

   def testTotalSize_004(self):
      """
      Test on a non-empty list containing only valid entries.
      """
      pass


   #########################
   # Test generateSizeMap()
   #########################
         
   def testGenerateSizeMap_001(self):
      """
      Test on an empty list.
      """
      pass

   def testGenerateSizeMap_002(self):
      """
      Test on a non-empty list containing a directory.
      """
      pass

   def testGenerateSizeMap_003(self):
      """
      Test on a non-empty list containing a non-existent file.
      """
      pass

   def testGenerateSizeMap_004(self):
      """
      Test on a non-empty list containing only valid entries.
      """
      pass


   ###########################
   # Test generateDigestMap()
   ###########################
         
   def testGenerateDigestMap01(self):
      """
      Test on an empty list.
      """
      pass

   def testGenerateDigestMap02(self):
      """
      Test on a non-empty list containing a directory.
      """
      pass

   def testGenerateDigestMap03(self):
      """
      Test on a non-empty list containing a non-existent file.
      """
      pass

   def testGenerateDigestMap04(self):
      """
      Test on a non-empty list containing only valid entries.
      """
      pass


   ########################
   # Test generateFitted()
   ########################
         
   def testGenerateFitted_001(self):
      """
      Test on an empty list.
      """
      pass

   def testGenerateFitted_002(self):
      """
      Test on a non-empty list containing a directory.
      """
      pass

   def testGenerateFitted_003(self):
      """
      Test on a non-empty list containing a non-existent file.
      """
      pass

   def testGenerateFitted_004(self):
      """
      Test on a non-empty list containing only valid entries, all of which fit.
      """
      pass

   def testGenerateFitted_005(self):
      """
      Test on a non-empty list containing only valid entries, some of which fit.
      """
      pass

   def testGenerateFitted_006(self):
      """
      Test on a non-empty list containing only valid entries, none of which fit.
      """
      pass


   #########################
   # Test generateTarfile()
   #########################
         
   def testGenerateTarfile_001(self):
      """
      Test on an empty list.
      """
      pass

   def testGenerateTarfile_002(self):
      """
      Test on a non-empty list containing a directory.
      """
      pass

   def testGenerateTarfile_003(self):
      """
      Test on a non-empty list containing a non-existent file, ignore=False.
      """
      pass

   def testGenerateTarfile_004(self):
      """
      Test on a non-empty list containing a non-existent file, ignore=True.
      """
      pass

   def testGenerateTarfile_005(self):
      """
      Test on a non-empty list containing only valid entries, with an invalid mode.
      """
      pass

   def testGenerateTarfile_006(self):
      """
      Test on a non-empty list containing only valid entries, default mode.
      """
      pass

   def testGenerateTarfile_007(self):
      """
      Test on a non-empty list containing only valid entries, 'tar' mode.
      """
      pass

   def testGenerateTarfile_008(self):
      """
      Test on a non-empty list containing only valid entries, 'targz' mode.
      """
      pass

   def testGenerateTarfile_009(self):
      """
      Test on a non-empty list containing only valid entries, 'tarbz2' mode.
      """
      pass


##########################
# TestPurgeItemList class
##########################

class TestPurgeItemList(unittest.TestCase):

   """Tests for the PurgeItemList object."""

   ################
   # Setup methods
   ################

   def setUp(self):
      try:
         self.data = findData()
      except Exception, e:
         self.fail(e)

   def tearDown(self):
      pass


   ####################
   # Test purgeItems()
   ####################
         
   def testPurgeItems01(self):
      """
      Test with an empty list.
      """
      pass

   def testPurgeItems02(self):
      """
      Test with a list containing non-existent entries.
      """
      pass

   def testPurgeItems03(self):
      """
      Test with a list containing only non-empty directories.
      """
      pass

   def testPurgeItems04(self):
      """
      Test with a list containing only empty directories.
      """
      pass

   def testPurgeItems05(self):
      """
      Test with a list containing only files.
      """
      pass

   def testPurgeItems06(self):
      """
      Test with a list containing a directory and some of the files in that directory.
      """
      pass

   def testPurgeItems07(self):
      """
      Test with a list containing a directory and all of the files in that directory.
      """
      pass

   def testPurgeItems08(self):
      """
      Test with a list containing various kinds of entries.
      """
      pass


#######################################################################
# Suite definition
#######################################################################

def suite():
   """Returns a suite containing all the test cases in this module."""
   return unittest.TestSuite((unittest.makeSuite(TestFilesystemList, 'test'),
                              unittest.makeSuite(TestBackupFileList, 'test'),
                              unittest.makeSuite(TestPurgeItemList, 'test'), ))



########################################################################
# Module entry point
########################################################################

# When this module is executed from the command-line, run its tests
if __name__ == '__main__':
   unittest.main()

