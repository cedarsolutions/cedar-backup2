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
# Copyright (c) 2007 Kenneth J. Pronovici.
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
# Purpose  : Tests DVD writer functionality.
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

########################################################################
# Module documentation
########################################################################

"""
Unit tests for CedarBackup2/writers/dvdwriter.py.

Code Coverage
=============

   This module contains individual tests for the public classes implemented in
   cdwriter.py.

   Unfortunately, it's rather difficult to test this code in an automated
   fashion, even if you have access to a physical DVD writer drive.  It's even
   more difficult to test it if you are running on some build daemon (think of
   a Debian autobuilder) which can't be expected to have any hardware or any
   media that you could write to.  Because of this, there aren't any tests
   below that actually cause DVD media to be written to.

   As a compromise, complicated parts of the implementation are in terms of
   private static methods with well-defined behaviors.  Normally, I prefer to
   only test the public interface to class, but in this case, testing these few
   private methods will help give us some reasonable confidence in the code,
   even if we can't write a physical disc or can't run all of the tests.

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

Full vs. Reduced Tests
======================

   Some Cedar Backup regression tests require a specialized environment in
   order to run successfully.  This environment won't necessarily be available
   on every build system out there (for instance, on a Debian autobuilder).
   Because of this, the default behavior is to run a "reduced feature set" test
   suite that has no surprising system, kernel or network requirements.  There
   are no special dependencies for these tests.

@author Kenneth J. Pronovici <pronovic@ieee.org>
"""


########################################################################
# Import modules and do runtime validations
########################################################################

import unittest

from CedarBackup2.writers.dvdwriter import MediaDefinition, DvdWriter
from CedarBackup2.writers.dvdwriter import MEDIA_DVDPLUSR, MEDIA_DVDPLUSRW


#######################################################################
# Module-wide configuration and constants
#######################################################################

GB44        = (4.4*1024.0*1024.0*1024.0)  # 4.4 GB 
GB44SECTORS = GB44/2048.0                 # 4.4 GB in 2048-byte sectors


#######################################################################
# Test Case Classes
#######################################################################

############################
# TestMediaDefinition class
############################

class TestMediaDefinition(unittest.TestCase):

   """Tests for the MediaDefinition class."""

   def testConstructor_001(self):
      """
      Test the constructor with an invalid media type.
      """
      self.failUnlessRaises(ValueError, MediaDefinition, 100)

   def testConstructor_002(self):
      """
      Test the constructor with the C{MEDIA_DVDPLUSR} media type.
      """
      media = MediaDefinition(MEDIA_DVDPLUSR)
      self.failUnlessEqual(MEDIA_DVDPLUSR, media.mediaType)
      self.failUnlessEqual(False, media.rewritable)
      self.failUnlessEqual(GB44SECTORS, media.capacity)

   def testConstructor_003(self):
      """
      Test the constructor with the C{MEDIA_DVDPLUSRW} media type.
      """
      media = MediaDefinition(MEDIA_DVDPLUSRW)
      self.failUnlessEqual(MEDIA_DVDPLUSRW, media.mediaType)
      self.failUnlessEqual(True, media.rewritable)
      self.failUnlessEqual(GB44SECTORS, media.capacity)


######################
# TestDvdWriter class
######################

class TestDvdWriter(unittest.TestCase):

   """Tests for the DvdWriter class."""

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
      Test with an empty device.
      """
      self.failUnlessRaises(ValueError, DvdWriter, None);

   def testConstructor_002(self):
      """
      Test with a device only.
      """
      dvdwriter = DvdWriter("/dev/dvd", unittest=True)
      self.failUnlessEqual("/dev/dvd", dvdwriter.device)
      self.failUnlessEqual(None, dvdwriter.scsiId)
      self.failUnlessEqual("/dev/dvd", dvdwriter.hardwareId)
      self.failUnlessEqual(None, dvdwriter.driveSpeed)
      self.failUnlessEqual(MEDIA_DVDPLUSRW, dvdwriter.media.mediaType)
      self.failUnlessEqual(True, dvdwriter.deviceHasTray)
      self.failUnlessEqual(True, dvdwriter.deviceCanEject)

   def testConstructor_003(self):
      """
      Test with a device and valid SCSI id.
      """
      dvdwriter = DvdWriter("/dev/dvd", scsiId="ATA:1,0,0", unittest=True)
      self.failUnlessEqual("/dev/dvd", dvdwriter.device)
      self.failUnlessEqual("ATA:1,0,0", dvdwriter.scsiId)
      self.failUnlessEqual("ATA:1,0,0", dvdwriter.hardwareId)
      self.failUnlessEqual(None, dvdwriter.driveSpeed)
      self.failUnlessEqual(MEDIA_DVDPLUSRW, dvdwriter.media.mediaType)
      self.failUnlessEqual(True, dvdwriter.deviceHasTray)
      self.failUnlessEqual(True, dvdwriter.deviceCanEject)

   def testConstructor_004(self):
      """
      Test with a device and valid drive speed.
      """
      dvdwriter = DvdWriter("/dev/dvd", driveSpeed=3, unittest=True)
      self.failUnlessEqual("/dev/dvd", dvdwriter.device)
      self.failUnlessEqual(None, dvdwriter.scsiId)
      self.failUnlessEqual("/dev/dvd", dvdwriter.hardwareId)
      self.failUnlessEqual(3, dvdwriter.driveSpeed)
      self.failUnlessEqual(MEDIA_DVDPLUSRW, dvdwriter.media.mediaType)
      self.failUnlessEqual(True, dvdwriter.deviceHasTray)
      self.failUnlessEqual(True, dvdwriter.deviceCanEject)

   def testConstructor_005(self):
      """
      Test with a device with media type MEDIA_DVDPLUSR.
      """
      dvdwriter = DvdWriter("/dev/dvd", mediaType=MEDIA_DVDPLUSR, unittest=True)
      self.failUnlessEqual("/dev/dvd", dvdwriter.device)
      self.failUnlessEqual(None, dvdwriter.scsiId)
      self.failUnlessEqual("/dev/dvd", dvdwriter.hardwareId)
      self.failUnlessEqual(None, dvdwriter.driveSpeed)
      self.failUnlessEqual(MEDIA_DVDPLUSR, dvdwriter.media.mediaType)
      self.failUnlessEqual(True, dvdwriter.deviceHasTray)
      self.failUnlessEqual(True, dvdwriter.deviceCanEject)

   def testConstructor_006(self):
      """
      Test with a device with media type MEDIA_DVDPLUSRW.
      """
      dvdwriter = DvdWriter("/dev/dvd", mediaType=MEDIA_DVDPLUSR, unittest=True)
      self.failUnlessEqual("/dev/dvd", dvdwriter.device)
      self.failUnlessEqual(None, dvdwriter.scsiId)
      self.failUnlessEqual("/dev/dvd", dvdwriter.hardwareId)
      self.failUnlessEqual(None, dvdwriter.driveSpeed)
      self.failUnlessEqual(MEDIA_DVDPLUSR, dvdwriter.media.mediaType)
      self.failUnlessEqual(True, dvdwriter.deviceHasTray)
      self.failUnlessEqual(True, dvdwriter.deviceCanEject)

   def testConstructor_007(self):
      """
      Test with a device and invalid SCSI id.
      """
      self.failUnlessRaises(ValueError, DvdWriter, "/dev/dvd", scsiId="OOOOOO", unittest=True)

   def testConstructor_008(self):
      """
      Test with a device and invalid drive speed.
      """
      self.failUnlessRaises(ValueError, DvdWriter, "/dev/dvd", driveSpeed="KEN", unittest=True)

   def testConstructor_008(self):
      """
      Test with a device and invalid media type.
      """
      self.failUnlessRaises(ValueError, DvdWriter, "/dev/dvd", mediaType=999, unittest=True)

   def testConstructor_009(self):
      """
      Test with all valid parameters, but no device, unittest=True.
      """
      self.failUnlessRaises(ValueError, DvdWriter, None, "ATA:1,0,0", 1, MEDIA_DVDPLUSRW, unittest=True)

   def testConstructor_010(self):
      """
      Test with all valid parameters, but no device, unittest=False.
      """
      self.failUnlessRaises(ValueError, DvdWriter, None, "ATA:1,0,0", 1, MEDIA_DVDPLUSRW, unittest=False)

   def testConstructor_011(self):
      """
      Test with all valid parameters, and an invalid device (not absolute path), unittest=True.
      """
      self.failUnlessRaises(ValueError, DvdWriter, "dev/dvd", "ATA:1,0,0", 1, MEDIA_DVDPLUSRW, unittest=True)

   def testConstructor_012(self):
      """
      Test with all valid parameters, and an invalid device (not absolute path), unittest=False.
      """
      self.failUnlessRaises(ValueError, DvdWriter, "dev/dvd", "ATA:1,0,0", 1, MEDIA_DVDPLUSRW, unittest=False)

   def testConstructor_013(self):
      """
      Test with all valid parameters, and an invalid device (path does not exist), unittest=False.
      """
      self.failUnlessRaises(ValueError, DvdWriter, "/dev/bogus", "ATA:1,0,0", 1, MEDIA_DVDPLUSRW, unittest=False)

   def testConstructor_014(self):
      """
      Test with all valid parameters.
      """
      dvdwriter = DvdWriter("/dev/dvd", "ATA:1,0,0", 1, MEDIA_DVDPLUSR, unittest=True)
      self.failUnlessEqual("/dev/dvd", dvdwriter.device)
      self.failUnlessEqual("ATA:1,0,0", dvdwriter.scsiId)
      self.failUnlessEqual("ATA:1,0,0", dvdwriter.hardwareId)
      self.failUnlessEqual(1, dvdwriter.driveSpeed)
      self.failUnlessEqual(MEDIA_DVDPLUSR, dvdwriter.media.mediaType)
      self.failUnlessEqual(True, dvdwriter.deviceHasTray)
      self.failUnlessEqual(True, dvdwriter.deviceCanEject)


   ######################
   # Test isRewritable()
   ######################

   def testIsRewritable_001(self):
      """
      Test with MEDIA_DVDPLUSR.
      """
      dvdwriter = DvdWriter("/dev/dvd", mediaType=MEDIA_DVDPLUSR, unittest=True)
      self.failUnlessEqual(False, dvdwriter.isRewritable())

   def testIsRewritable_002(self):
      """
      Test with MEDIA_DVDPLUSRW.
      """
      dvdwriter = DvdWriter("/dev/dvd", mediaType=MEDIA_DVDPLUSRW, unittest=True)
      self.failUnlessEqual(True, dvdwriter.isRewritable())


   #########################
   # Test initializeImage()
   #########################

   def testInitializeImage_001(self):
      """
      """
      pass


   #######################
   # Test addImageEntry()
   #######################

   def testAddImageEntry_001(self):
      """
      """
      pass


   ################################
   # Test _getEstimatedImageSize()
   ################################

   def testGetEstimatedImageSize_001(self):
      """
      """
      pass


   ############################
   # Test _searchForOverburn()
   ############################

   def testSearchForOverburn_001(self):
      """
      """
      pass


   #########################
   # Test _buildWriteArgs()
   #########################

   def testBuildWriteArgs_001(self):
      """
      """
      pass


#######################################################################
# Suite definition
#######################################################################

def suite():
   """Returns a suite containing all the test cases in this module."""
   return unittest.TestSuite((
                              unittest.makeSuite(TestMediaDefinition, 'test'),
                              unittest.makeSuite(TestDvdWriter, 'test'),
                            ))


########################################################################
# Module entry point
########################################################################

# When this module is executed from the command-line, run its tests
if __name__ == '__main__':
   unittest.main()

