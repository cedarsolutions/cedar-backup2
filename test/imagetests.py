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
# Purpose  : Tests ISO image functionality.
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# This file was created with a width of 132 characters, and NO tabs.

########################################################################
# Module documentation
########################################################################

"""
Unit tests for CedarBackup2/image.py.

Code Coverage
=============

   This module contains individual tests for the public functions and classes
   implemented in image.py.  There are also tests for many of the private
   methods (see some further notes below).

   There are some parts of this functionality that can't be tested everywhere.
   For instance, to completely test the ISO functionality, mkisofs must be
   installed and the kernel must allow loopback filesystems to be mounted.
   Some systems (like a Debian autobuilder) won't support these things, and yet
   we might still want to be able to run some tests on those systems.  Because
   of this, some of the tests will only be run if IMAGETESTS_FULL is set to "Y"
   in the environment.

   I usually prefer to test only the public interface to a class, because that
   way the regression tests don't depend on the internal implementation.  In
   this case, I've decided to test some of the private methods because their
   "privateness" is more a matter of presenting a clean external interface than
   anything else (most of the private methods are static).  Being able to test
   these methods also makes it easier to validate some of the functionality
   even if IMAGETESTS_FULL is not set to "Y" in the environment.

Naming Conventions
==================

   I prefer to avoid large unit tests which validate more than one piece of
   functionality, and I prefer to avoid using overly descriptive (read: long)
   test names, as well.  Instead, I use lots of very small tests that each
   validate one specific thing.  These small tests are then named with an index
   number, yielding something like C{testAddDir_001} or C{testValidate_010}.
   Each method has a docstring describing what it's supposed to accomplish.  I
   feel that this makes it easier to judge how important a given failure is,
   and also makes it somewhat easier to diagnose and fix individual problems.

@author Kenneth J. Pronovici <pronovic@ieee.org>
"""


########################################################################
# Import modules and do runtime validations
########################################################################

# Import standard modules
import os
import unittest
from CedarBackup2.image import IsoImage


#######################################################################
# Utility functions
#######################################################################

def runAllTests():
   """Returns true/false depending on whether the full test suite should be run."""
   if "IMAGETESTS_FULL" in os.environ:
      return os.environ["IMAGETESTS_FULL"] == "Y"
   else:
      return False


#######################################################################
# Test Case Classes
#######################################################################

#####################
# TestIsoImage class
#####################

class TestIsoImage(unittest.TestCase):

   """Tests for the IsoImage class."""

   ################
   # Setup methods
   ################

   def setUp(self):
      pass

   def tearDown(self):
      pass


   ###################
   # Test constructor
   ###################

   def testConstructor_001(self):
      """
      Test the constructor using all default arguments.
      """
      isoImage = IsoImage()
      self.failUnlessEqual(None, isoImage.device)
      self.failUnlessEqual(None, isoImage.boundaries)
      self.failUnlessEqual(None, isoImage.graftPoint)
      self.failUnlessEqual(True, isoImage.useRockRidge)
      self.failUnlessEqual(None, isoImage.applicationId)
      self.failUnlessEqual(None, isoImage.biblioFile)
      self.failUnlessEqual(None, isoImage.publisherId)
      self.failUnlessEqual(None, isoImage.preparerId)
      self.failUnlessEqual(None, isoImage.volumeId)

   def testConstructor_002(self):
      """
      Test the constructor using non-default arguments.
      """
      isoImage = IsoImage("/dev/cdrw", boundaries=(1, 2), graftPoint="/france")
      self.failUnlessEqual("/dev/cdrw", isoImage.device)
      self.failUnlessEqual((1, 2), isoImage.boundaries)
      self.failUnlessEqual("/france", isoImage.graftPoint)
      self.failUnlessEqual(True, isoImage.useRockRidge)
      self.failUnlessEqual(None, isoImage.applicationId)
      self.failUnlessEqual(None, isoImage.biblioFile)
      self.failUnlessEqual(None, isoImage.publisherId)
      self.failUnlessEqual(None, isoImage.preparerId)
      self.failUnlessEqual(None, isoImage.volumeId)


   #######################
   # Test utility methods
   #######################

   def testUtilityMethods_001(self):
      """
      Test _buildDirEntries() with an empty entries dictionary.
      """
      pass

   def testUtilityMethods_002(self):
      """
      Test _buildDirEntries() with an entries dictionary that has no graft points.
      """
      pass

   def testUtilityMethods_003(self):
      """
      Test _buildDirEntries() with an entries dictionary that has all graft points.
      """
      pass

   def testUtilityMethods_004(self):
      """
      Test _buildDirEntries() with an entries dictionary that has mixed graft points and not.
      """
      pass

   def testUtilityMethods_005(self):
      """
      Test _buildGeneralArgs() with all optional values as None.
      """
      pass

   def testUtilityMethods_006(self):
      """
      Test _buildGeneralArgs() with applicationId set.
      """
      pass

   def testUtilityMethods_007(self):
      """
      Test _buildGeneralArgs() with biblioFile set.
      """
      pass

   def testUtilityMethods_008(self):
      """
      Test _buildGeneralArgs() with publisherId set.
      """
      pass

   def testUtilityMethods_009(self):
      """
      Test _buildGeneralArgs() with preparerId set.
      """
      pass

   def testUtilityMethods_010(self):
      """
      Test _buildGeneralArgs() with volumeId set.
      """
      pass

   def testUtilityMethods_011(self):
      """
      Test _buildSizeArgs() with useRockRidge set to True.
      """
      pass

   def testUtilityMethods_012(self):
      """
      Test _buildSizeArgs() with useRockRidge set to False.
      """
      pass

   def testUtilityMethods_013(self):
      """
      Test _buildSizeArgs() with device as None and boundaries as non-None.
      """
      pass

   def testUtilityMethods_014(self):
      """
      Test _buildSizeArgs() with device as non-None and boundaries as None.
      """
      pass

   def testUtilityMethods_015(self):
      """
      Test _buildSizeArgs() with device and boundaries as non-None.
      """
      pass

   def testUtilityMethods_016(self):
      """
      Test _buildWriteArgs() with useRockRidge set to True.
      """
      pass

   def testUtilityMethods_017(self):
      """
      Test _buildWriteArgs() with useRockRidge set to False.
      """
      pass

   def testUtilityMethods_018(self):
      """
      Test _buildWriteArgs() with device as None and boundaries as non-None.
      """
      pass

   def testUtilityMethods_019(self):
      """
      Test _buildWriteArgs() with device as non-None and boundaries as None.
      """
      pass

   def testUtilityMethods_020(self):
      """
      Test _buildWriteArgs() with device and boundaries as non-None.
      """
      pass

   def testUtilityMethods_021(self):
      """
      Test _calculateSizes with an empty entries dictionary.
      """
      pass

   def testUtilityMethods_022(self):
      """
      Test _calculateSizes with an entries dictionary containing only a single file.
      """
      pass

   def testUtilityMethods_023(self):
      """
      Test _calculateSizes with an entries dictionary containing multiple files.
      """
      pass

   def testUtilityMethods_024(self):
      """
      Test _calculateSizes with an entries dictionary containing files, directories and links.
      """
      pass

   def testUtilityMethods_025(self):
      """
      Test _buildEntries with an empty entries dictionary and empty items list.
      """
      pass

   def testUtilityMethods_026(self):
      """
      Test _buildEntries with a valid entries dictionary and items list.
      """
      pass

   def testUtilityMethods_027(self):
      """
      Test _buildEntries with an items list containing a key not in the entries dictionary.
      """
      pass

   def testUtilityMethods_028(self):
      """
      Test _expandEntries with an empty entries dictionary.
      """
      pass

   def testUtilityMethods_029(self):
      """
      Test _expandEntries with an entries dictionary containing only a single file.
      """
      pass

   def testUtilityMethods_030(self):
      """
      Test _expandEntries with an entries dictionary containing only files.
      """
      pass

   def testUtilityMethods_031(self):
      """
      Test _expandEntries with an entries dictionary containing only a single empty directory.
      """
      pass

   def testUtilityMethods_032(self):
      """
      Test _expandEntries with an entries dictionary containing only a single non-empty directory.
      """
      pass

   def testUtilityMethods_033(self):
      """
      Test _expandEntries with an entries dictionary containing only directories.
      """
      pass

   def testUtilityMethods_034(self):
      """
      Test _expandEntries with an entries dictionary containing files and directories.
      """
      pass


   ##################
   # Test addEntry()
   ##################

   def testAddEntry_001(self):
      """
      Attempt to add a non-existent entry.
      """
      pass

   def testAddEntry_002(self):
      """
      Attempt to add a an entry that is a soft link to a file.
      """
      pass

   def testAddEntry_003(self):
      """
      Attempt to add a an entry that is a soft link to a directory.
      """
      pass

   def testAddEntry_004(self):
      """
      Attempt to add a file, no graft point set.
      """
      pass

   def testAddEntry_005(self):
      """
      Attempt to add a file, graft point set on the object level.
      """
      pass

   def testAddEntry_006(self):
      """
      Attempt to add a file, graft point set on the method level.
      """
      pass

   def testAddEntry_007(self):
      """
      Attempt to add a file, graft point set on the object and method levels.
      """
      pass

   def testAddEntry_008(self):
      """
      Attempt to add a directory, no graft point set.
      """
      pass

   def testAddEntry_009(self):
      """
      Attempt to add a directory, graft point set on the object level.
      """
      pass

   def testAddEntry_010(self):
      """
      Attempt to add a directory, graft point set on the method level.
      """
      pass

   def testAddEntry_011(self):
      """
      Attempt to add a directory, graft point set on the object and methods levels.
      """
      pass

   def testAddEntry_012(self):
      """
      Attempt to add a file that has already been added, override=False.
      """
      pass

   def testAddEntry_013(self):
      """
      Attempt to add a file that has already been added, override=True.
      """
      pass

   def testAddEntry_014(self):
      """
      Attempt to add a directory that has already been added, override=False, changing the graft point.
      """
      pass

   def testAddEntry_015(self):
      """
      Attempt to add a directory that has already been added, override=True, changing the graft point.
      """
      pass


   ##########################
   # Test getEstimatedSize()
   ##########################

   def testGetEstimatedSize_001(self):
      """
      Test with an empty list.
      """
      pass

   def testGetEstimatedSize_002(self):
      """
      Test with non-empty empty list.
      """
      pass


   ####################
   # Test pruneImage() 
   ####################

   def testPruneImage_001(self):
      """
      Attempt to prune an image containing no entries.
      """
      pass
   
   def testPruneImage_002(self):
      """
      Attempt to prune a non-empty image using a capacity for which all entries
      will fit.
      """
      pass
   
   def testPruneImage_003(self):
      """
      Attempt to prune a non-empty image using a capacity for which some
      entries will fit.
      """
      pass
   
   def testPruneImage_004(self):
      """
      Attempt to prune a non-empty image using a capacity for which no entries
      will fit.
      """
      pass
   
   def testPruneImage_005(self):
      """
      Attempt to prune a non-empty image using a capacity for which not even
      the overhead will fit.
      """
      pass
   

   ####################
   # Test writeImage()
   ####################

   def testWriteImage_001(self):
      """
      Attempt to write an image containing no entries.
      """
      pass

   def testWriteImage_002(self):
      """
      Attempt to write an image containing only an empty directory.
      """
      pass

   def testWriteImage_003(self):
      """
      Attempt to write an image containing only a non-empty directory.
      """
      pass

   def testWriteImage_004(self):
      """
      Attempt to write an image containing only a file.
      """
      pass

   def testWriteImage_005(self):
      """
      Attempt to write an image containing a file and an empty directory.
      """
      pass

   def testWriteImage_006(self):
      """
      Attempt to write an image containing a file and a non-empty directory.
      """
      pass

   def testWriteImage_007(self):
      """
      Attempt to write an image containing several files and a non-empty
      directory.
      """
      pass

   def testWriteImage_008(self):
      """
      Attempt to write an image containing several files and a non-empty
      directory, which has been pruned.
      """
      pass


#######################################################################
# Suite definition
#######################################################################

def suite():
   """Returns a suite containing all the test cases in this module."""
   if runAllTests():
      return unittest.TestSuite((
                                 unittest.makeSuite(TestIsoImage, 'test'),
                               ))
   else:
      return unittest.TestSuite((
                                 unittest.makeSuite(TestIsoImage, 'testConstructor'),
                                 unittest.makeSuite(TestIsoImage, 'testUtilityMethods'),
                                 unittest.makeSuite(TestIsoImage, 'testAddEntry'),
                               ))


########################################################################
# Module entry point
########################################################################

# When this module is executed from the command-line, run its tests
if __name__ == '__main__':
   unittest.main()

