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


   #####################
   # Tests for whatever
   #####################
         
   def test_1_01(self):
      """
      Test 1.01.
      XXXXX
      """
      pass


   #####################
   # Tests for whatever
   #####################
         
   def test_2_01(self):
      """
      Test 2.01.
      XXXXX
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


   #####################
   # Tests for whatever
   #####################
         
   def test_1_01(self):
      """
      Test 1.01.
      XXXXX
      """
      pass


   #####################
   # Tests for whatever
   #####################
         
   def test_2_01(self):
      """
      Test 2.01.
      XXXXX
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


   #####################
   # Tests for whatever
   #####################
         
   def test_1_01(self):
      """
      Test 1.01.
      XXXXX
      """
      pass


   #####################
   # Tests for whatever
   #####################
         
   def test_2_01(self):
      """
      Test 2.01.
      XXXXX
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

