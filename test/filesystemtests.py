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

Code Structure
==============

   Python unittest conventions usually have tests named something like
   testListInsert() or similar.  This makes sense, but with the kind of tests
   I'm doing, I don't want to end up with huge descriptive function names.
   It's klunky.

   Instead, functions will be named according to their test plan item number,
   and each test will be annotated in the method documentation.  This is more
   like the way I write JUnit tests, and I think it should will be just as easy
   to follow.

Code Coverage
=============

   There are individual tests for each of the objects implemented in
   filesystem.py: FilesystemList, BackupFileList and PurgeItemList.
   BackupFileList and PurgeItemList inherit from FilesystemList, and
   FilesystemList itself inherits from the standard Python list object.  For
   the most part, I won't spend time testing inherited functionality,
   especially if it's already been tested.  However, there are some tests of
   the base list functionality just to ensure that the inheritence has been
   constructed properly.

Debugging these Tests
=====================

   Debugging in here is DAMN complicated.  If you have a test::

      def test():
        try:
           # stuff
        finally:
           # remove files

   you may mysteriously have the 'stuff' fail, and you won't get any exceptions
   reported to you.  The best thing to do if you get strange situations like
   this is to move 'stuff' out of the try block - that will usually clear
   things up.

@author Kenneth J. Pronovici <pronovic@ieee.org>
"""


########################################################################
# Import modules and do runtime validations
########################################################################

import sys
import os
import unittest
from CedarBackup2.filesystem import FilesystemList, BackupFileList, PurgeItemList


#######################################################################
# Module-wide configuration and constants
#######################################################################

DATA_DIRS = [ './data', './test/data' ]
RESOURCES = [ "tree1.tar.gz", "tree2.tar.gz", "tree3.tar.gz", "tree4.tar.gz", "tree5.tar.gz", "tree6.tar.gz" ]


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
         self.data = findData()
      except Exception, e:
         self.fail(e)

   def tearDown(self):
      pass


   ################################
   # Test basic list functionality
   ################################
         
   def test_1_01(self):
      """
      Test 1.01
      Test the append() method.
      """
      fileList = FilesystemList()
      self.failUnlessEqual([], fileList)
      fileList.append('a')
      self.failUnlessEqual(['a'], fileList)
      fileList.append('b')
      self.failUnlessEqual(['a', 'b'], fileList)

   def test_1_02(self):
      """
      Test 1.02
      Test the insert() method.
      """
      fileList = FilesystemList()
      self.failUnlessEqual([], fileList)
      fileList.insert(0, 'a')
      self.failUnlessEqual(['a'], fileList)
      fileList.insert(0, 'b')
      self.failUnlessEqual(['b', 'a'], fileList)

   def test_1_03(self):
      """
      Test 1.03
      Test the remove() method.
      """
      fileList = FilesystemList()
      self.failUnlessEqual([], fileList)
      fileList.insert(0, 'a')
      fileList.insert(0, 'b')
      self.failUnlessEqual(['b', 'a'], fileList)
      fileList.remove('a')
      self.failUnlessEqual(['b'], fileList)
      fileList.remove('b')
      self.failUnlessEqual([], fileList)

   def test_1_04(self):
      """
      Test 1.04
      Test the pop() method.
      """
      fileList = FilesystemList()
      self.failUnlessEqual([], fileList)
      fileList.append('a')
      fileList.append('b')
      fileList.append('c')
      fileList.append('d')
      fileList.append('e')
      self.failUnlessEqual(['a', 'b', 'c', 'd', 'e'], fileList)
      self.failUnlessEqual('e', fileList.pop())
      self.failUnlessEqual(['a', 'b', 'c', 'd'], fileList)
      self.failUnlessEqual('d', fileList.pop())
      self.failUnlessEqual(['a', 'b', 'c'], fileList)
      self.failUnlessEqual('c', fileList.pop())
      self.failUnlessEqual(['a', 'b'], fileList)
      self.failUnlessEqual('b', fileList.pop())
      self.failUnlessEqual(['a'], fileList)
      self.failUnlessEqual('a', fileList.pop())
      self.failUnlessEqual([], fileList)

   def test_1_05(self):
      """
      Test 1.05
      Test the count() method.
      """
      fileList = FilesystemList()
      self.failUnlessEqual([], fileList)
      fileList.append('a')
      fileList.append('b')
      fileList.append('c')
      fileList.append('d')
      fileList.append('e')
      self.failUnlessEqual(['a', 'b', 'c', 'd', 'e'], fileList)
      self.failUnlessEqual(1, fileList.count('a'))

   def test_1_06(self):
      """
      Test 1.06
      Test the index() method.
      """
      fileList = FilesystemList()
      self.failUnlessEqual([], fileList)
      fileList.append('a')
      fileList.append('b')
      fileList.append('c')
      fileList.append('d')
      fileList.append('e')
      self.failUnlessEqual(['a', 'b', 'c', 'd', 'e'], fileList)
      self.failUnlessEqual(2, fileList.index('c'))

   def test_1_07(self):
      """
      Test 1.07
      Test the reverse() method.
      """
      fileList = FilesystemList()
      self.failUnlessEqual([], fileList)
      fileList.append('a')
      fileList.append('b')
      fileList.append('c')
      fileList.append('d')
      fileList.append('e')
      self.failUnlessEqual(['a', 'b', 'c', 'd', 'e'], fileList)
      fileList.reverse()
      self.failUnlessEqual(['e', 'd', 'c', 'b', 'a'], fileList)
      fileList.reverse()
      self.failUnlessEqual(['a', 'b', 'c', 'd', 'e'], fileList)

   def test_1_08(self):
      """
      Test 1.08
      Test the sort() method.
      """
      fileList = FilesystemList()
      self.failUnlessEqual([], fileList)
      fileList.append('e')
      fileList.append('d')
      fileList.append('c')
      fileList.append('b')
      fileList.append('a')
      self.failUnlessEqual(['e', 'd', 'c', 'b', 'a'], fileList)
      fileList.sort()
      self.failUnlessEqual(['a', 'b', 'c', 'd', 'e'], fileList)
      fileList.sort()
      self.failUnlessEqual(['a', 'b', 'c', 'd', 'e'], fileList)

   def test_1_09(self):
      """
      Test 1.09
      Test slicing.
      """
      fileList = FilesystemList()
      self.failUnlessEqual([], fileList)
      fileList.append('e')
      fileList.append('d')
      fileList.append('c')
      fileList.append('b')
      fileList.append('a')
      self.failUnlessEqual(['e', 'd', 'c', 'b', 'a'], fileList)
      self.failUnlessEqual(['e', 'd', 'c', 'b', 'a'], fileList[:])
      self.failUnlessEqual(['e', 'd', 'c', 'b', 'a'], fileList[0:])
      self.failUnlessEqual('e', fileList[0])
      self.failUnlessEqual('a', fileList[4])
      self.failUnlessEqual(['d', 'c', 'b'], fileList[1:4])


   #################
   # Test addFile()
   #################
         
   def test_2_01(self):
      """
      Test 2.01.
      Attempt to add a file that doesn't exist; no exclusions.
      """
      pass

   def test_2_02(self):
      """
      Test 2.02.
      Attempt to add a directory; no exclusions.
      """
      pass

   def test_2_03(self):
      """
      Test 2.03.
      Attempt to add a soft link; no exclusions.
      """
      pass

   def test_2_04(self):
      """
      Test 2.04.
      Attempt to add an existing file; no exclusions.
      """
      pass

   def test_2_05(self):
      """
      Test 2.05.
      Attempt to add a file that doesn't exist; excludeFiles set.
      """
      pass

   def test_2_06(self):
      """
      Test 2.06.
      Attempt to add a directory; excludeFiles set.
      """
      pass

   def test_2_07(self):
      """
      Test 2.07.
      Attempt to add a soft link; excludeFiles set.
      """
      pass

   def test_2_08(self):
      """
      Test 2.08.
      Attempt to add an existing file; excludeFiles set.
      """
      pass

   def test_2_09(self):
      """
      Test 2.09.
      Attempt to add a file that doesn't exist; excludeDirs set.
      """
      pass

   def test_2_10(self):
      """
      Test 2.10.
      Attempt to add a directory; excludeDirs set.
      """
      pass

   def test_2_11(self):
      """
      Test 2.11.
      Attempt to add a soft link; excludeDirs set.
      """
      pass

   def test_2_12(self):
      """
      Test 2.12.
      Attempt to add an existing file; excludeDirs set.
      """
      pass

   def test_2_13(self):
      """
      Test 2.13.
      Attempt to add a file that doesn't exist; with excludePaths including the
      path.
      """
      pass

   def test_2_14(self):
      """
      Test 2.14.
      Attempt to add a directory; with excludePaths including the path.
      """
      pass

   def test_2_15(self):
      """
      Test 2.15.
      Attempt to add a soft link; with excludePaths including the path.
      """
      pass

   def test_2_16(self):
      """
      Test 2.16.
      Attempt to add an existing file; with excludePaths including the path.
      """
      pass

   def test_2_17(self):
      """
      Test 2.17.
      Attempt to add a file that doesn't exist; with excludePaths not including
      the path.
      """
      pass

   def test_2_18(self):
      """
      Test 2.18.
      Attempt to add a directory; with excludePaths not including the path.
      """
      pass

   def test_2_19(self):
      """
      Test 2.19.
      Attempt to add a soft link; with excludePaths not including the path.
      """
      pass

   def test_2_20(self):
      """
      Test 2.20.
      Attempt to add an existing file; with excludePaths not including the path.
      """
      pass

   def test_2_21(self):
      """
      Test 2.21.
      Attempt to add a file that doesn't exist; with excludePatterns matching
      the path.
      """
      pass

   def test_2_22(self):
      """
      Test 2.22.
      Attempt to add a directory; with excludePatterns matching the path.
      """
      pass

   def test_2_23(self):
      """
      Test 2.23.
      Attempt to add a soft link; with excludePatterns matching the path.
      """
      pass

   def test_2_24(self):
      """
      Test 2.24.
      Attempt to add an existing file; with excludePatterns matching the path.
      """
      pass

   def test_2_25(self):
      """
      Test 2.25.
      Attempt to add a file that doesn't exist; with excludePatterns not
      matching the path.
      """
      pass

   def test_2_26(self):
      """
      Test 2.26.
      Attempt to add a directory; with excludePatterns not matching the path.
      """
      pass

   def test_2_27(self):
      """
      Test 2.27.
      Attempt to add a soft link; with excludePatterns not matching the path.
      """
      pass

   def test_2_28(self):
      """
      Test 2.28.
      Attempt to add an existing file; with excludePatterns not matching the
      path.
      """
      pass


   ################
   # Test addDir()
   ################
         
   def test_3_01(self):
      """
      Test 3.01.
      Attempt to add a directory that doesn't exist; no exclusions.
      """
      pass

   def test_3_02(self):
      """
      Test 3.02.
      Attempt to add a file; no exclusions.
      """
      pass

   def test_3_03(self):
      """
      Test 3.03.
      Attempt to add a soft link; no exclusions.
      """
      pass

   def test_3_04(self):
      """
      Test 3.04.
      Attempt to add an existing directory; no exclusions.
      """
      pass

   def test_3_05(self):
      """
      Test 3.05.
      Attempt to add a directory that doesn't exist; excludeFiles set.
      """
      pass

   def test_3_06(self):
      """
      Test 3.06.
      Attempt to add a file; excludeFiles set.
      """
      pass

   def test_3_07(self):
      """
      Test 3.07.
      Attempt to add a soft link; excludeFiles set.
      """
      pass

   def test_3_08(self):
      """
      Test 3.08.
      Attempt to add an existing directory; excludeFiles set.
      """
      pass

   def test_3_09(self):
      """
      Test 3.09.
      Attempt to add a directory that doesn't exist; excludeDirs set.
      """
      pass

   def test_3_10(self):
      """
      Test 3.10.
      Attempt to add a file; excludeDirs set.
      """
      pass

   def test_3_11(self):
      """
      Test 3.11.
      Attempt to add a soft link; excludeDirs set.
      """
      pass

   def test_3_12(self):
      """
      Test 3.12.
      Attempt to add an existing directory; excludeDirs set.
      """
      pass

   def test_3_13(self):
      """
      Test 3.13.
      Attempt to add a directory that doesn't exist; with excludePaths
      including the path.
      """
      pass

   def test_3_14(self):
      """
      Test 3.14.
      Attempt to add a file; with excludePaths including the path.
      """
      pass

   def test_3_15(self):
      """
      Test 3.15.
      Attempt to add a soft link; with excludePaths including the path.
      """
      pass

   def test_3_16(self):
      """
      Test 3.16.
      Attempt to add an existing directory; with excludePaths including the
      path.
      """
      pass

   def test_3_17(self):
      """
      Test 3.17.
      Attempt to add a directory that doesn't exist; with excludePaths not
      including the path.
      """
      pass

   def test_3_18(self):
      """
      Test 3.18.
      Attempt to add a file; with excludePaths not including the path.
      """
      pass

   def test_3_19(self):
      """
      Test 3.19.
      Attempt to add a soft link; with excludePaths not including the path.
      """
      pass

   def test_3_20(self):
      """
      Test 3.20.
      Attempt to add an existing directory; with excludePaths not including the
      path.
      """
      pass

   def test_3_21(self):
      """
      Test 3.21.
      Attempt to add a directory that doesn't exist; with excludePatterns
      matching the path.
      """
      pass

   def test_3_22(self):
      """
      Test 3.22.
      Attempt to add a file; with excludePatterns matching the path.
      """
      pass

   def test_3_23(self):
      """
      Test 3.23.
      Attempt to add a soft link; with excludePatterns matching the path.
      """
      pass

   def test_3_24(self):
      """
      Test 3.24.
      Attempt to add an existing directory; with excludePatterns matching the
      path.
      """
      pass

   def test_3_25(self):
      """
      Test 3.25.
      Attempt to add a directory that doesn't exist; with excludePatterns not
      matching the path.
      """
      pass

   def test_3_26(self):
      """
      Test 3.26.
      Attempt to add a file; with excludePatterns not matching the path.
      """
      pass

   def test_3_27(self):
      """
      Test 3.27.
      Attempt to add a soft link; with excludePatterns not matching the path.
      """
      pass

   def test_3_28(self):
      """
      Test 3.28.
      Attempt to add an existing directory; with excludePatterns not matching
      the path.
      """
      pass


   ########################
   # Test addDirContents()
   ########################
         
   def test_4_01(self):
      """
      Test 4.01.
      Attempt to add a directory that doesn't exist; no exclusions.
      """
      pass

   def test_4_02(self):
      """
      Test 4.02.
      Attempt to add a file; no exclusions.
      """
      pass

   def test_4_03(self):
      """
      Test 4.03.
      Attempt to add a soft link; no exclusions.
      """
      pass

   def test_4_04(self):
      """
      Test 4.04.
      Attempt to add an empty directory containing ignore file; no exclusions.
      """
      pass

   def test_4_05(self):
      """
      Test 4.05.
      Attempt to add an empty directory; no exclusions.
      """
      pass

   def test_4_06(self):
      """
      Test 4.06.
      Attempt to add an non-empty directory containing ignore file; no
      exclusions.
      """
      pass

   def test_4_07(self):
      """
      Test 4.07.
      Attempt to add an non-empty directory; no exclusions.
      """
      pass

   def test_4_08(self):
      """
      Test 4.08.
      Attempt to add a directory that doesn't exist; excludeFiles set.
      """
      pass

   def test_4_09(self):
      """
      Test 4.09.
      Attempt to add a file; excludeFiles set.
      """
      pass

   def test_4_10(self):
      """
      Test 4.10.
      Attempt to add a soft link; excludeFiles set.
      """
      pass

   def test_4_11(self):
      """
      Test 4.11.
      Attempt to add an empty directory containing ignore file; excludeFiles set.
      """
      pass

   def test_4_12(self):
      """
      Test 4.12.
      Attempt to add an empty directory; excludeFiles set.
      """
      pass

   def test_4_13(self):
      """
      Test 4.13.
      Attempt to add an non-empty directory containing ignore file; excludeFiles set.
      """
      pass

   def test_4_14(self):
      """
      Test 4.14.
      Attempt to add an non-empty directory; excludeFiles set.
      """
      pass

   def test_4_15(self):
      """
      Test 4.15.
      Attempt to add a directory that doesn't exist; excludeDirs set.
      """
      pass

   def test_4_16(self):
      """
      Test 4.16.
      Attempt to add a file; excludeDirs set.
      """
      pass

   def test_4_17(self):
      """
      Test 4.17.
      Attempt to add a soft link; excludeDirs set.
      """
      pass

   def test_4_18(self):
      """
      Test 4.18.
      Attempt to add an empty directory containing ignore file; excludeDirs set.
      """
      pass

   def test_4_19(self):
      """
      Test 4.19.
      Attempt to add an empty directory; excludeDirs set.
      """
      pass

   def test_4_20(self):
      """
      Test 4.20.
      Attempt to add an non-empty directory containing ignore file; excludeDirs set.
      """
      pass

   def test_4_21(self):
      """
      Test 4.21.
      Attempt to add an non-empty directory; excludeDirs set.
      """
      pass

   def test_4_22(self):
      """
      Test 4.22.
      Attempt to add a directory that doesn't exist; with excludePaths
      including the path.
      """
      pass

   def test_4_23(self):
      """
      Test 4.23.
      Attempt to add a file; with excludePaths including the path.
      """
      pass

   def test_4_24(self):
      """
      Test 4.24.
      Attempt to add a soft link; with excludePaths including the path.
      """
      pass

   def test_4_25(self):
      """
      Test 4.25.
      Attempt to add an empty directory containing ignore file; with
      excludePaths including the path.
      """
      pass

   def test_4_26(self):
      """
      Test 4.26.
      Attempt to add an empty directory; with excludePaths including the path.
      """
      pass

   def test_4_27(self):
      """
      Test 4.27.
      Attempt to add an non-empty directory containing ignore file; with
      excludePaths including the path.
      """
      pass

   def test_4_28(self):
      """
      Test 4.28.
      Attempt to add an non-empty directory; with excludePaths including the
      path.
      """
      pass

   def test_4_29(self):
      """
      Test 4.29.
      Attempt to add a directory that doesn't exist; with excludePaths not
      including the path.
      """
      pass

   def test_4_30(self):
      """
      Test 4.30.
      Attempt to add a file; with excludePaths not including the path.
      """
      pass

   def test_4_31(self):
      """
      Test 4.31.
      Attempt to add a soft link; with excludePaths not including the path.
      """
      pass

   def test_4_32(self):
      """
      Test 4.32.
      Attempt to add an empty directory containing ignore file; with
      excludePaths not including the path.
      """
      pass

   def test_4_33(self):
      """
      Test 4.33.
      Attempt to add an empty directory; with excludePaths not including the
      path.
      """
      pass

   def test_4_34(self):
      """
      Test 4.34.
      Attempt to add an non-empty directory containing ignore file; with
      excludePaths not including the path.
      """
      pass

   def test_4_35(self):
      """
      Test 4.35.
      Attempt to add an non-empty directory; with excludePaths not including
      the path.
      """
      pass

   def test_4_36(self):
      """
      Test 4.36.
      Attempt to add a directory that doesn't exist; with excludePatterns
      matching the path.
      """
      pass

   def test_4_38(self):
      """
      Test 4.38.
      Attempt to add a file; with excludePatterns matching the path.
      """
      pass

   def test_4_39(self):
      """
      Test 4.39.
      Attempt to add a soft link; with excludePatterns matching the path.
      """
      pass

   def test_4_40(self):
      """
      Test 4.40.
      Attempt to add an empty directory containing ignore file; with
      excludePatterns matching the path.
      """
      pass

   def test_4_41(self):
      """
      Test 4.41.
      Attempt to add an empty directory; with excludePatterns matching the
      path.
      """
      pass

   def test_4_42(self):
      """
      Test 4.42.
      Attempt to add an non-empty directory containing ignore file; with
      excludePatterns matching the path.
      """
      pass

   def test_4_43(self):
      """
      Test 4.43.
      Attempt to add an non-empty directory; with excludePatterns matching the
      path.
      """
      pass

   def test_4_44(self):
      """
      Test 4.44.
      Attempt to add a directory that doesn't exist; with excludePatterns not
      matching the path.
      """
      pass

   def test_4_45(self):
      """
      Test 4.45.
      Attempt to add a file; with excludePatterns not matching the path.
      """
      pass

   def test_4_46(self):
      """
      Test 4.46.
      Attempt to add a soft link; with excludePatterns not matching the path.
      """
      pass

   def test_4_47(self):
      """
      Test 4.47.
      Attempt to add an empty directory containing ignore file; with
      excludePatterns not matching the path.
      """
      pass

   def test_4_48(self):
      """
      Test 4.48.
      Attempt to add an empty directory; with excludePatterns not matching the
      path.
      """
      pass

   def test_4_49(self):
      """
      Test 4.49.
      Attempt to add an non-empty directory containing ignore file; with
      excludePatterns not matching the path.
      """
      pass

   def test_4_50(self):
      """
      Test 4.50.
      Attempt to add an non-empty directory; with excludePatterns not matching
      the path.
      """
      pass


   #####################
   # Test removeFiles()
   #####################
         
   def test_5_01(self):
      """
      Test 5.01.
      Test with an empty list and a pattern of None.
      """
      pass

   def test_5_02(self):
      """
      Test 5.02.
      Test with an empty list and a non-empty pattern.
      """
      pass

   def test_5_03(self):
      """
      Test 5.03.
      Test with a non-empty list (files only) and a pattern of None.
      """
      pass

   def test_5_04(self):
      """
      Test 5.04.
      Test with a non-empty list (directories only) and a pattern of None.
      """
      pass

   def test_5_05(self):
      """
      Test 5.05.
      Test with a non-empty list (files and directories) and a pattern of None.
      """
      pass

   def test_5_06(self):
      """
      Test 5.06.
      Test with a non-empty list (files and directories, some nonexistent) and
      a pattern of None.
      """
      pass

   def test_5_07(self):
      """
      Test 5.07.
      Test with a non-empty list (files only) and a non-empty pattern that
      matches none of them.
      """
      pass

   def test_5_08(self):
      """
      Test 5.08.
      Test with a non-empty list (directories only) and a non-empty pattern
      that matches none of them.
      """
      pass

   def test_5_09(self):
      """
      Test 5.09.
      Test with a non-empty list (files and directories) and a non-empty
      pattern that matches none of them.
      """
      pass

   def test_5_10(self):
      """
      Test 5.10.
      Test with a non-empty list (files and directories, some nonexistent) and
      a non-empty pattern that matches none of them.
      """
      pass

   def test_5_11(self):
      """
      Test 5.11.
      Test with a non-empty list (files only) and a non-empty pattern that
      matches some of them.
      """
      pass

   def test_5_12(self):
      """
      Test 5.12.
      Test with a non-empty list (directories only) and a non-empty pattern
      that matches some of them.
      """
      pass

   def test_5_13(self):
      """
      Test 5.13.
      Test with a non-empty list (files and directories) and a non-empty
      pattern that matches some of them.
      """
      pass

   def test_5_14(self):
      """
      Test 5.14.
      Test with a non-empty list (files and directories, some nonexistent) and
      a non-empty pattern that matches some of them.
      """
      pass

   def test_5_15(self):
      """
      Test 5.15.
      Test with a non-empty list (files only) and a non-empty pattern that
      matches all of them.
      """
      pass

   def test_5_16(self):
      """
      Test 5.16.
      Test with a non-empty list (directories only) and a non-empty pattern
      that matches all of them.
      """
      pass

   def test_5_17(self):
      """
      Test 5.17.
      Test with a non-empty list (files and directories) and a non-empty
      pattern that matches all of them.
      """
      pass

   def test_5_18(self):
      """
      Test 5.18.
      Test with a non-empty list (files and directories, some nonexistent) and
      a non-empty pattern that matches all of them.
      """
      pass


   ####################
   # Test removeDirs()
   ####################
         
   def test_6_01(self):
      """
      Test 6.01.
      Test with an empty list and a pattern of None.
      """
      pass

   def test_6_02(self):
      """
      Test 6.02.
      Test with an empty list and a non-empty pattern.
      """
      pass

   def test_6_03(self):
      """
      Test 6.03.
      Test with a non-empty list (files only) and a pattern of None.
      """
      pass

   def test_6_04(self):
      """
      Test 6.04.
      Test with a non-empty list (directories only) and a pattern of None.
      """
      pass

   def test_6_05(self):
      """
      Test 6.05.
      Test with a non-empty list (files and directories) and a pattern of None.
      """
      pass

   def test_6_06(self):
      """
      Test 6.06.
      Test with a non-empty list (files and directories, some nonexistent) and
      a pattern of None.
      """
      pass

   def test_6_07(self):
      """
      Test 6.07.
      Test with a non-empty list (files only) and a non-empty pattern that
      matches none of them.
      """
      pass

   def test_6_08(self):
      """
      Test 6.08.
      Test with a non-empty list (directories only) and a non-empty pattern
      that matches none of them.
      """
      pass

   def test_6_09(self):
      """
      Test 6.09.
      Test with a non-empty list (files and directories) and a non-empty
      pattern that matches none of them.
      """
      pass

   def test_6_10(self):
      """
      Test 6.10.
      Test with a non-empty list (files and directories, some nonexistent) and
      a non-empty pattern that matches none of them.
      """
      pass

   def test_6_11(self):
      """
      Test 6.11.
      Test with a non-empty list (files only) and a non-empty pattern that
      matches some of them.
      """
      pass

   def test_6_12(self):
      """
      Test 6.12.
      Test with a non-empty list (directories only) and a non-empty pattern
      that matches some of them.
      """
      pass

   def test_6_13(self):
      """
      Test 6.13.
      Test with a non-empty list (files and directories) and a non-empty
      pattern that matches some of them.
      """
      pass

   def test_6_14(self):
      """
      Test 6.14.
      Test with a non-empty list (files and directories, some nonexistent) and
      a non-empty pattern that matches some of them.
      """
      pass

   def test_6_15(self):
      """
      Test 6.15.
      Test with a non-empty list (files only) and a non-empty pattern that
      matches all of them.
      """
      pass

   def test_6_16(self):
      """
      Test 6.16.
      Test with a non-empty list (directories only) and a non-empty pattern
      that matches all of them.
      """
      pass

   def test_6_17(self):
      """
      Test 6.17.
      Test with a non-empty list (files and directories) and a non-empty
      pattern that matches all of them.
      """
      pass

   def test_6_18(self):
      """
      Test 6.18.
      Test with a non-empty list (files and directories, some nonexistent) and
      a non-empty pattern that matches all of them.
      """
      pass


   #####################
   # Test removeMatch()
   #####################
         
   def test_7_01(self):
      """
      Test 7.01.
      Test with an empty list and a pattern of None.
      """
      pass

   def test_7_02(self):
      """
      Test 7.02.
      Test with an empty list and a non-empty pattern.
      """
      pass

   def test_7_03(self):
      """
      Test 7.07.
      Test with a non-empty list (files only) and a non-empty pattern that
      matches none of them.
      """
      pass

   def test_7_04(self):
      """
      Test 7.08.
      Test with a non-empty list (directories only) and a non-empty pattern
      that matches none of them.
      """
      pass

   def test_7_05(self):
      """
      Test 7.09.
      Test with a non-empty list (files and directories) and a non-empty
      pattern that matches none of them.
      """
      pass

   def test_7_06(self):
      """
      Test 7.06.
      Test with a non-empty list (files and directories, some nonexistent) and
      a non-empty pattern that matches none of them.
      """
      pass

   def test_7_07(self):
      """
      Test 7.07.
      Test with a non-empty list (files only) and a non-empty pattern that
      matches some of them.
      """
      pass

   def test_7_08(self):
      """
      Test 7.08.
      Test with a non-empty list (directories only) and a non-empty pattern
      that matches some of them.
      """
      pass

   def test_7_09(self):
      """
      Test 7.09.
      Test with a non-empty list (files and directories) and a non-empty
      pattern that matches some of them.
      """
      pass

   def test_7_10(self):
      """
      Test 7.10.
      Test with a non-empty list (files and directories, some nonexistent) and
      a non-empty pattern that matches some of them.
      """
      pass

   def test_7_11(self):
      """
      Test 7.11.
      Test with a non-empty list (files only) and a non-empty pattern that
      matches all of them.
      """
      pass

   def test_7_12(self):
      """
      Test 7.12.
      Test with a non-empty list (directories only) and a non-empty pattern
      that matches all of them.
      """
      pass

   def test_7_13(self):
      """
      Test 7.13.
      Test with a non-empty list (files and directories) and a non-empty
      pattern that matches all of them.
      """
      pass

   def test_7_14(self):
      """
      Test 7.14.
      Test with a non-empty list (files and directories, some nonexistent) and
      a non-empty pattern that matches all of them.
      """
      pass


   #######################
   # Test removeInvalid()
   #######################
         
   def test_8_01(self):
      """
      Test 8.01.
      Test with an empty list.
      """
      pass

   def test_8_02(self):
      """
      Test 8.02.
      Test with a non-empty list containing only invalid entries (files only).
      """
      pass

   def test_8_03(self):
      """
      Test 8.03.
      Test with a non-empty list containing only valid entries (files only).
      """
      pass

   def test_8_04(self):
      """
      Test 8.04.
      Test with a non-empty list containing only valid entries (directories
      only).
      """
      pass

   def test_8_05(self):
      """
      Test 8.05.
      Test with a non-empty list containing only valid entries (files and
      directories).
      """
      pass

   def test_8_06(self):
      """
      Test 8.06.
      Test with a non-empty list containing valid and invalid entries (files
      only).
      """
      pass

   def test_8_07(self):
      """
      Test 8.07.
      Test with a non-empty list containing valid and invalid entries
      (directories only).
      """
      pass

   def test_8_08(self):
      """
      Test 8.08.
      Test with a non-empty list containing valid and invalid entries (files
      and directories).
      """
      pass


   ###################
   # Test normalize()
   ###################
         
   def test_9_01(self):
      """
      Test 9.01.
      Test with an empty list.
      """
      pass

   def test_9_02(self):
      """
      Test 9.02.
      Test with a list containing one entry.
      """
      pass

   def test_9_03(self):
      """
      Test 9.03.
      Test with a list containing two entries, no duplicates.
      """
      pass

   def test_9_04(self):
      """
      Test 9.04.
      Test with a list containing two entries, with duplicates.
      """
      pass

   def test_9_05(self):
      """
      Test 9.05.
      Test with a list containing many entries, no duplicates.
      """
      pass

   def test_9_06(self):
      """
      Test 9.06.
      Test with a list containing many entries, with duplicates.
      """
      pass


   ################
   # Test verify()
   ################
         
   def test_10_01(self):
      """
      Test 10.01.
      Test with an empty list.
      """
      pass

   def test_10_02(self):
      """
      Test 10.02.
      Test with a non-empty list containing only invalid entries (files only).
      """
      pass

   def test_10_03(self):
      """
      Test 10.03.
      Test with a non-empty list containing only valid entries (files only).
      """
      pass

   def test_10_04(self):
      """
      Test 10.04.
      Test with a non-empty list containing only valid entries (directories
      only).
      """
      pass

   def test_10_05(self):
      """
      Test 10.05.
      Test with a non-empty list containing only valid entries (files and
      directories).
      """
      pass

   def test_10_06(self):
      """
      Test 10.06.
      Test with a non-empty list containing valid and invalid entries (files
      only).
      """
      pass

   def test_10_07(self):
      """
      Test 10.07.
      Test with a non-empty list containing valid and invalid entries
      (directories only).
      """
      pass

   def test_10_08(self):
      """
      Test 10.08.
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
         
   def test_1_01(self):
      """
      Test 1.01.
      Test that function is overridden with empty list, no exclusions.
      """
      pass

   def test_1_02(self):
      """
      Test 1.02.
      Test that function is overridden with non-empty list, no exclusions.
      """
      pass

   def test_1_03(self):
      """
      Test 1.03.
      Test that function is overridden with empty list, excludeFiles sets.
      """
      pass

   def test_1_04(self):
      """
      Test 1.04.
      Test that function is overridden with non-empty list, excludeFiles sets.
      """
      pass

   def test_1_05(self):
      """
      Test 1.05.
      Test that function is overridden with empty list, excludeDirs sets.
      """
      pass

   def test_1_06(self):
      """
      Test 1.06.
      Test that function is overridden with non-empty list, excludeDirs sets.
      """
      pass

   def test_1_07(self):
      """
      Test 1.07.
      Test that function is overridden with empty list, excludePaths sets.
      """
      pass

   def test_1_08(self):
      """
      Test 1.08.
      Test that function is overridden with non-empty list, excludePaths sets.
      """
      pass

   def test_1_09(self):
      """
      Test 1.09.
      Test that function is overridden with empty list, excludePatterns sets.
      """
      pass

   def test_1_10(self):
      """
      Test 1.10.
      Test that function is overridden with non-empty list, excludePatterns sets.
      """
      pass


   ###################
   # Test totalSize()
   ###################
         
   def test_2_01(self):
      """
      Test 2.01.
      Test on an empty list.
      """
      pass

   def test_2_02(self):
      """
      Test 2.02.
      Test on a non-empty list containing a directory.
      """
      pass

   def test_2_03(self):
      """
      Test 2.03.
      Test on a non-empty list containing a non-existent file.
      """
      pass

   def test_2_04(self):
      """
      Test 2.04.
      Test on a non-empty list containing only valid entries.
      """
      pass


   #########################
   # Test generateSizeMap()
   #########################
         
   def test_3_01(self):
      """
      Test 3.01.
      Test on an empty list.
      """
      pass

   def test_3_02(self):
      """
      Test 3.02.
      Test on a non-empty list containing a directory.
      """
      pass

   def test_3_03(self):
      """
      Test 3.03.
      Test on a non-empty list containing a non-existent file.
      """
      pass

   def test_3_04(self):
      """
      Test 3.04.
      Test on a non-empty list containing only valid entries.
      """
      pass


   ###########################
   # Test generateDigestMap()
   ###########################
         
   def test_4_01(self):
      """
      Test 4.01.
      Test on an empty list.
      """
      pass

   def test_4_02(self):
      """
      Test 4.02.
      Test on a non-empty list containing a directory.
      """
      pass

   def test_4_03(self):
      """
      Test 4.03.
      Test on a non-empty list containing a non-existent file.
      """
      pass

   def test_4_04(self):
      """
      Test 4.04.
      Test on a non-empty list containing only valid entries.
      """
      pass


   ########################
   # Test generateFitted()
   ########################
         
   def test_5_01(self):
      """
      Test 5.01.
      Test on an empty list.
      """
      pass

   def test_5_02(self):
      """
      Test 5.02.
      Test on a non-empty list containing a directory.
      """
      pass

   def test_5_03(self):
      """
      Test 5.03.
      Test on a non-empty list containing a non-existent file.
      """
      pass

   def test_5_04(self):
      """
      Test 5.04.
      Test on a non-empty list containing only valid entries, all of which fit.
      """
      pass

   def test_5_05(self):
      """
      Test 5.05.
      Test on a non-empty list containing only valid entries, some of which fit.
      """
      pass

   def test_5_06(self):
      """
      Test 5.06.
      Test on a non-empty list containing only valid entries, none of which fit.
      """
      pass


   #########################
   # Test generateTarfile()
   #########################
         
   def test_6_01(self):
      """
      Test 6.01.
      Test on an empty list.
      """
      pass

   def test_6_02(self):
      """
      Test 6.02.
      Test on a non-empty list containing a directory.
      """
      pass

   def test_6_03(self):
      """
      Test 6.03.
      Test on a non-empty list containing a non-existent file, ignore=False.
      """
      pass

   def test_6_04(self):
      """
      Test 6.04.
      Test on a non-empty list containing a non-existent file, ignore=True.
      """
      pass

   def test_6_05(self):
      """
      Test 6.05.
      Test on a non-empty list containing only valid entries, with an invalid mode.
      """
      pass

   def test_6_06(self):
      """
      Test 6.06.
      Test on a non-empty list containing only valid entries, default mode.
      """
      pass

   def test_6_07(self):
      """
      Test 6.07.
      Test on a non-empty list containing only valid entries, 'tar' mode.
      """
      pass

   def test_6_08(self):
      """
      Test 6.08.
      Test on a non-empty list containing only valid entries, 'targz' mode.
      """
      pass

   def test_6_09(self):
      """
      Test 6.09.
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
         
   def test_1_01(self):
      """
      Test 1.01.
      Test with an empty list.
      """
      pass

   def test_1_02(self):
      """
      Test 1.02.
      Test with a list containing non-existent entries.
      """
      pass

   def test_1_03(self):
      """
      Test 1.03.
      Test with a list containing only non-empty directories.
      """
      pass

   def test_1_04(self):
      """
      Test 1.04.
      Test with a list containing only empty directories.
      """
      pass

   def test_1_05(self):
      """
      Test 1.05.
      Test with a list containing only files.
      """
      pass

   def test_1_06(self):
      """
      Test 1.06.
      Test with a list containing a directory and some of the files in that directory.
      """
      pass

   def test_1_07(self):
      """
      Test 1.07.
      Test with a list containing a directory and all of the files in that directory.
      """
      pass

   def test_1_08(self):
      """
      Test 1.08.
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

