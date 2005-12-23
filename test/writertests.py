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
# Purpose  : Tests image writer functionality.
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

########################################################################
# Module documentation
########################################################################

"""
Unit tests for CedarBackup2/image.py.

Code Coverage
=============

   This module contains individual tests for the public functions and classes
   implemented in writer.py.  There are also tests for several of the private
   methods.

   Unfortunately, it's rather difficult to test this code in an automated
   fashion, even if you have access to a physical CD writer drive.  It's even
   more difficult to test it if you are running on some build daemon (think of
   a Debian autobuilder) which can't be expected to have any hardware or any
   media that you could write to.  Because of this, there aren't any tests
   below that actually cause CD media to be written to.

   As a compromise, many of the implementation is in terms of private static
   methods.  Normally, I prefer to only test the public interface to class, but
   in this case, testing the private methods will help give us some reasonable
   confidence in the code even if we can't write a physical disc.  This isn't
   perfect, but it's better than nothing.

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

   All of the tests in this module are considered safe to be run in an average
   build environment.  There is a no need to use a WRITERTESTS_FULL environment
   variable to provide a "reduced feature set" test suite as for some of the
   other test modules.

   I used to try and run tests against an actual device, to make sure that this
   worked.  However, those tests ended up being kind of bogus, because my main
   development environment doesn't have a writer, and even if it had one, any
   device with the same name on another user's system wouldn't necessarily
   return sensible results.  That's just pointless.  We'll just have to rely on
   the other tests to make sure that things seem sensible.

@author Kenneth J. Pronovici <pronovic@ieee.org>
"""

########################################################################
# Import modules and do runtime validations
########################################################################

import os
import re
import unittest
from CedarBackup2.writer import validateScsiId
from CedarBackup2.writer import MediaDefinition, MediaCapacity, CdWriter
from CedarBackup2.writer import MEDIA_CDR_74, MEDIA_CDRW_74, MEDIA_CDR_80, MEDIA_CDRW_80


########################################################################
# Constants
########################################################################

MB650 = (650.0*1024.0*1024.0)    # 650 MB
MB700 = (700.0*1024.0*1024.0)    # 700 MB
ILEAD = (11400.0*2048.0)         # Initial lead-in
SLEAD = (6900.0*2048.0)          # Session lead-in


#######################################################################
# Test Case Classes
#######################################################################

######################
# TestFunctions class
######################

class TestFunctions(unittest.TestCase):

   """Tests various functions in writer.py."""

   def testValidateScsiId_001(self):
      """
      Test with simple scsibus,target,lun address.
      """
      scsiId = "0,0,0"
      result = validateScsiId(scsiId)
      self.failUnlessEqual(scsiId, result)

   def testValidateScsiId_002(self):
      """
      Test with simple scsibus,target,lun address containing spaces.
      """
      scsiId = " 0,   0, 0 "
      result = validateScsiId(scsiId)
      self.failUnlessEqual(scsiId, result)

   def testValidateScsiId_003(self):
      """
      Test with simple ATA address.
      """
      scsiId = "ATA:3,2,1"
      result = validateScsiId(scsiId)
      self.failUnlessEqual(scsiId, result)

   def testValidateScsiId_004(self):
      """
      Test with simple ATA address containing spaces.
      """
      scsiId = "ATA: 3, 2,1  "
      result = validateScsiId(scsiId)
      self.failUnlessEqual(scsiId, result)

   def testValidateScsiId_005(self):
      """
      Test with simple ATAPI address.
      """
      scsiId = "ATAPI:1,2,3"
      result = validateScsiId(scsiId)
      self.failUnlessEqual(scsiId, result)

   def testValidateScsiId_006(self):
      """
      Test with simple ATAPI address containing spaces.
      """
      scsiId = "  ATAPI:1,   2, 3"
      result = validateScsiId(scsiId)
      self.failUnlessEqual(scsiId, result)

   def testValidateScsiId_007(self):
      """
      Test with default-device Mac address.
      """
      scsiId = "IOCompactDiscServices"
      result = validateScsiId(scsiId)
      self.failUnlessEqual(scsiId, result)

   def testValidateScsiId_008(self):
      """
      Test with an alternate-device Mac address.
      """
      scsiId = "IOCompactDiscServices/2"
      result = validateScsiId(scsiId)
      self.failUnlessEqual(scsiId, result)

   def testValidateScsiId_009(self):
      """
      Test with an alternate-device Mac address.
      """
      scsiId = "IOCompactDiscServices/12"
      result = validateScsiId(scsiId)
      self.failUnlessEqual(scsiId, result)

   def testValidateScsiId_010(self):
      """
      Test with an invalid address with a missing field.
      """
      scsiId = "1,2"
      self.failUnlessRaises(ValueError, validateScsiId, scsiId)

   def testValidateScsiId_011(self):
      """
      Test with an invalid address with an invalid prefix.
      """
      scsiId = "ATABI:1,2,3"
      self.failUnlessRaises(ValueError, validateScsiId, scsiId)

   def testValidateScsiId_012(self):
      """
      Test with an invalid Mac-style address with a backslash.
      """
      scsiId = "IOCompactDiscServices\\3"
      self.failUnlessRaises(ValueError, validateScsiId, scsiId)


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
      Test the constructor with the C{MEDIA_CDR_74} media type.
      """
      media = MediaDefinition(MEDIA_CDR_74)
      self.failUnlessEqual(MEDIA_CDR_74, media.mediaType)
      self.failUnlessEqual(False, media.rewritable)
      self.failIfEqual(0, media.initialLeadIn)    # just care that it's set, not what its value is
      self.failIfEqual(0, media.leadIn)           # just care that it's set, not what its value is
      self.failUnlessEqual(332800, media.capacity)

   def testConstructor_003(self):
      """
      Test the constructor with the C{MEDIA_CDRW_74} media type.
      """
      media = MediaDefinition(MEDIA_CDRW_74)
      self.failUnlessEqual(MEDIA_CDRW_74, media.mediaType)
      self.failUnlessEqual(True, media.rewritable)
      self.failIfEqual(0, media.initialLeadIn)    # just care that it's set, not what its value is
      self.failIfEqual(0, media.leadIn)           # just care that it's set, not what its value is
      self.failUnlessEqual(332800, media.capacity)

   def testConstructor_004(self):
      """
      Test the constructor with the C{MEDIA_CDR_80} media type.
      """
      media = MediaDefinition(MEDIA_CDR_80)
      self.failUnlessEqual(MEDIA_CDR_80, media.mediaType)
      self.failUnlessEqual(False, media.rewritable)
      self.failIfEqual(0, media.initialLeadIn)    # just care that it's set, not what its value is
      self.failIfEqual(0, media.leadIn)           # just care that it's set, not what its value is
      self.failUnlessEqual(358400, media.capacity)

   def testConstructor_005(self):
      """
      Test the constructor with the C{MEDIA_CDRW_80} media type.
      """
      media = MediaDefinition(MEDIA_CDRW_80)
      self.failUnlessEqual(MEDIA_CDRW_80, media.mediaType)
      self.failUnlessEqual(True, media.rewritable)
      self.failIfEqual(0, media.initialLeadIn)    # just care that it's set, not what its value is
      self.failIfEqual(0, media.leadIn)           # just care that it's set, not what its value is
      self.failUnlessEqual(358400, media.capacity)


############################
# TestMediaCapacity class
############################

class TestMediaCapacity(unittest.TestCase):

   """Tests for the MediaCapacity class."""

   def testConstructor_001(self):
      """
      Test the constructor.
      """
      capacity = MediaCapacity(100, 200, (300, 400))
      self.failUnlessEqual(100, capacity.bytesUsed)
      self.failUnlessEqual(200, capacity.bytesAvailable)
      self.failUnlessEqual((300, 400), capacity.boundaries)


#####################
# TestCdWriter class
#####################

class TestCdWriter(unittest.TestCase):

   """Tests for the CdWriter class."""

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

   # Note: testConstructor_001() has been removed 

   def testConstructor_002(self):
      """
      Test the constructor with device C{/dev/null}, which is writable and exists.
      Use a valid non-ATA SCSI id and defaults for the remaining arguments.  Make sure
      that C{unittest=True}
      """
      writer = CdWriter(device="/dev/null", scsiId="0,0,0", unittest=True)
      self.failUnlessEqual("/dev/null", writer.device)
      self.failUnlessEqual("0,0,0", writer.scsiId)
      self.failUnlessEqual(None, writer.driveSpeed)
      self.failUnlessEqual(MEDIA_CDRW_74, writer.media.mediaType)
      self.failUnlessEqual(True, writer.isRewritable())

   def testConstructor_003(self):
      """
      Test the constructor with device C{/dev/null}, which is writable and exists.
      Use a valid ATA SCSI id and defaults for the remaining arguments.  Make sure
      that C{unittest=True}.
      """
      writer = CdWriter(device="/dev/null", scsiId="ATA:0,0,0", unittest=True)
      self.failUnlessEqual("/dev/null", writer.device)
      self.failUnlessEqual("ATA:0,0,0", writer.scsiId)
      self.failUnlessEqual(None, writer.driveSpeed)
      self.failUnlessEqual(MEDIA_CDRW_74, writer.media.mediaType)
      self.failUnlessEqual(True, writer.isRewritable())

   def testConstructor_004(self):
      """
      Test the constructor with device C{/dev/null}, which is writable and exists.
      Use a valid ATAPI SCSI id and defaults for the remaining arguments.  Make sure
      that C{unittest=True}.
      """
      writer = CdWriter(device="/dev/null", scsiId="ATAPI:0,0,0", unittest=True)
      self.failUnlessEqual("/dev/null", writer.device)
      self.failUnlessEqual("ATAPI:0,0,0", writer.scsiId)
      self.failUnlessEqual(None, writer.driveSpeed)
      self.failUnlessEqual(MEDIA_CDRW_74, writer.media.mediaType)
      self.failUnlessEqual(True, writer.isRewritable())

   def testConstructor_005(self):
      """
      Test the constructor with device C{/dev/null} (which is writable and exists).
      Use an invalid SCSI id and defaults for the remaining arguments.  Make sure that
      C{unittest=False}.
      """
      self.failUnlessRaises(ValueError, CdWriter, device="/dev/null", scsiId="blech", unittest=False)

   def testConstructor_006(self):
      """
      Test the constructor with device C{/dev/null} (which is writable and exists).
      Use an invalid SCSI id and defaults for the remaining arguments.  Make sure that
      C{unittest=True}.
      """
      self.failUnlessRaises(ValueError, CdWriter, device="/dev/null", scsiId="blech", unittest=True)

   def testConstructor_007(self):
      """
      Test the constructor with a non-absolute device path.  Use a valid SCSI
      id and defaults for the remaining arguments.  Make sure that C{unittest=False}.
      """
      self.failUnlessRaises(ValueError, CdWriter, device="dev/null", scsiId="0,0,0", unittest=False)

   def testConstructor_008(self):
      """
      Test the constructor with a non-absolute device path.  Use a valid SCSI
      id and defaults for the remaining arguments.  Make sure that C{unittest=True}.
      """
      self.failUnlessRaises(ValueError, CdWriter, device="dev/null", scsiId="0,0,0", unittest=True)

   def testConstructor_009(self):
      """
      Test the constructor with an absolute device path that does not exist.
      Use a valid SCSI id and defaults for the remaining arguments.  Make sure
      that C{unittest=False}.
      """
      self.failUnlessRaises(ValueError, CdWriter, device="/bogus", scsiId="0,0,0", unittest=False)

   def testConstructor_010(self):
      """
      Test the constructor with an absolute device path that does not exist.
      Use a valid SCSI id and defaults for the remaining arguments.  Make sure
      that C{unittest=True}.
      """
      writer = CdWriter(device="/bogus", scsiId="0,0,0", unittest=True)
      self.failUnlessEqual("/bogus", writer.device)
      self.failUnlessEqual("0,0,0", writer.scsiId)
      self.failUnlessEqual(None, writer.driveSpeed)
      self.failUnlessEqual(MEDIA_CDRW_74, writer.media.mediaType)
      self.failUnlessEqual(True, writer.isRewritable())

   def testConstructor_011(self):
      """
      Test the constructor with device C{/dev/null}, which is writable and
      exists.  Use a valid SCSI id and a value of 0 for the drive speed.  Make
      sure that C{unittest=False}.
      """
      self.failUnlessRaises(ValueError, CdWriter, device="/dev/null", scsiId="0,0,0", driveSpeed=0, unittest=False)

   def testConstructor_012(self):
      """
      Test the constructor with device C{/dev/null}, which is writable and
      exists.  Use a valid SCSI id and a value of 0 for the drive speed.  Make
      sure that C{unittest=True}.
      """
      self.failUnlessRaises(ValueError, CdWriter, device="/dev/null", scsiId="0,0,0", driveSpeed=0, unittest=True)

   # Note: testConstructor_013() has been removed

   def testConstructor_014(self):
      """
      Test the constructor with device C{/dev/null}, which is writable and
      exists.  Use a valid SCSI id and a value of 1 for the drive speed.  Make
      sure that C{unittest=True}.
      """
      writer = CdWriter(device="/dev/null", scsiId="0,0,0", driveSpeed=1, unittest=True)
      self.failUnlessEqual("/dev/null", writer.device)
      self.failUnlessEqual("0,0,0", writer.scsiId)
      self.failUnlessEqual(1, writer.driveSpeed)
      self.failUnlessEqual(MEDIA_CDRW_74, writer.media.mediaType)
      self.failUnlessEqual(True, writer.isRewritable())

   # Note: testConstructor_015() has been removed 

   def testConstructor_016(self):
      """
      Test the constructor with device C{/dev/null}, which is writable and
      exists.  Use a valid SCSI id and a value of 5 for the drive speed.  Make
      sure that C{unittest=True}.
      """
      writer = CdWriter(device="/dev/null", scsiId="0,0,0", driveSpeed=5, unittest=True)
      self.failUnlessEqual("/dev/null", writer.device)
      self.failUnlessEqual("0,0,0", writer.scsiId)
      self.failUnlessEqual(5, writer.driveSpeed)
      self.failUnlessEqual(MEDIA_CDRW_74, writer.media.mediaType)
      self.failUnlessEqual(True, writer.isRewritable())

   def testConstructor_017(self):
      """
      Test the constructor with device C{/dev/null}, which is writable and
      exists.  Use a valid SCSI id and an invalid media type.  Make sure that
      C{unittest=False}.
      """
      self.failUnlessRaises(ValueError, CdWriter, device="/dev/null", scsiId="0,0,0", mediaType=42, unittest=False)

   def testConstructor_018(self):
      """
      Test the constructor with device C{/dev/null}, which is writable and
      exists.  Use a valid SCSI id and an invalid media type.  Make sure that
      C{unittest=True}.
      """
      self.failUnlessRaises(ValueError, CdWriter, device="/dev/null", scsiId="0,0,0", mediaType=42, unittest=True)

   # Note: testConstructor_019() has been removed

   def testConstructor_020(self):
      """
      Test the constructor with device C{/dev/null}, which is writable and
      exists.  Use a valid SCSI id and a media type of MEDIA_CDR_74.  Make sure
      that C{unittest=True}.
      """
      writer = CdWriter(device="/dev/null", scsiId="0,0,0", mediaType=MEDIA_CDR_74, unittest=True)
      self.failUnlessEqual("/dev/null", writer.device)
      self.failUnlessEqual("0,0,0", writer.scsiId)
      self.failUnlessEqual(None, writer.driveSpeed)
      self.failUnlessEqual(MEDIA_CDR_74, writer.media.mediaType)
      self.failUnlessEqual(False, writer.isRewritable())

   # Note: testConstructor_021() has been removed

   def testConstructor_022(self):
      """
      Test the constructor with device C{/dev/null}, which is writable and
      exists.  Use a valid SCSI id and a media type of MEDIA_CDRW_74.  Make sure
      that C{unittest=True}.
      """
      writer = CdWriter(device="/dev/null", scsiId="0,0,0", mediaType=MEDIA_CDRW_74, unittest=True)
      self.failUnlessEqual("/dev/null", writer.device)
      self.failUnlessEqual("0,0,0", writer.scsiId)
      self.failUnlessEqual(None, writer.driveSpeed)
      self.failUnlessEqual(MEDIA_CDRW_74, writer.media.mediaType)
      self.failUnlessEqual(True, writer.isRewritable())

   # Note: testConstructor_023() has been removed

   def testConstructor_024(self):
      """
      Test the constructor with device C{/dev/null}, which is writable and
      exists.  Use a valid SCSI id and a media type of MEDIA_CDR_80.  Make sure
      that C{unittest=True}.
      """
      writer = CdWriter(device="/dev/null", scsiId="0,0,0", mediaType=MEDIA_CDR_80, unittest=True)
      self.failUnlessEqual("/dev/null", writer.device)
      self.failUnlessEqual("0,0,0", writer.scsiId)
      self.failUnlessEqual(None, writer.driveSpeed)
      self.failUnlessEqual(MEDIA_CDR_80, writer.media.mediaType)
      self.failUnlessEqual(False, writer.isRewritable())

   # Note: testConstructor_025() has been removed

   def testConstructor_026(self):
      """
      Test the constructor with device C{/dev/null}, which is writable and
      exists.  Use a valid SCSI id and a media type of MEDIA_CDRW_80.  Make sure
      that C{unittest=True}.
      """
      writer = CdWriter(device="/dev/null", scsiId="0,0,0", mediaType=MEDIA_CDRW_80, unittest=True)
      self.failUnlessEqual("/dev/null", writer.device)
      self.failUnlessEqual("0,0,0", writer.scsiId)
      self.failUnlessEqual(None, writer.driveSpeed)
      self.failUnlessEqual(MEDIA_CDRW_80, writer.media.mediaType)
      self.failUnlessEqual(True, writer.isRewritable())


   ####################################
   # Test the capacity-related methods
   ####################################

   def testCapacity_001(self):
      """
      Test _calculateCapacity for boundaries of None and MEDIA_CDR_74.
      """
      expectedAvailable = MB650-ILEAD # 650 MB, minus initial lead-in
      media = MediaDefinition(MEDIA_CDR_74)
      boundaries = None
      capacity = CdWriter._calculateCapacity(media, boundaries)
      self.failUnlessEqual(0, capacity.bytesUsed)
      self.failUnlessEqual(expectedAvailable, capacity.bytesAvailable)
      self.failUnlessEqual(None, capacity.boundaries)

   def testCapacity_002(self):
      """
      Test _calculateCapacity for boundaries of None and MEDIA_CDRW_74.
      """
      expectedAvailable = MB650-ILEAD  # 650 MB, minus initial lead-in
      media = MediaDefinition(MEDIA_CDRW_74)
      boundaries = None
      capacity = CdWriter._calculateCapacity(media, boundaries)
      self.failUnlessEqual(0, capacity.bytesUsed)
      self.failUnlessEqual(expectedAvailable, capacity.bytesAvailable)
      self.failUnlessEqual(None, capacity.boundaries)

   def testCapacity_003(self):
      """
      Test _calculateCapacity for boundaries of None and MEDIA_CDR_80.
      """
      expectedAvailable = MB700-ILEAD  # 700 MB, minus initial lead-in
      media = MediaDefinition(MEDIA_CDR_80)
      boundaries = None
      capacity = CdWriter._calculateCapacity(media, boundaries)
      self.failUnlessEqual(0, capacity.bytesUsed)
      self.failUnlessEqual(expectedAvailable, capacity.bytesAvailable)
      self.failUnlessEqual(None, capacity.boundaries)

   def testCapacity_004(self):
      """
      Test _calculateCapacity for boundaries of None and MEDIA_CDRW_80.
      """
      expectedAvailable = MB700-ILEAD # 700 MB, minus initial lead-in
      media = MediaDefinition(MEDIA_CDRW_80)
      boundaries = None
      capacity = CdWriter._calculateCapacity(media, boundaries)
      self.failUnlessEqual(0, capacity.bytesUsed)
      self.failUnlessEqual(expectedAvailable, capacity.bytesAvailable)
      self.failUnlessEqual(None, capacity.boundaries)

   def testCapacity_005(self):
      """
      Test _calculateCapacity for boundaries of (0, 1) and MEDIA_CDR_74.
      """
      expectedUsed = (1*2048.0)  # 1 sector
      expectedAvailable = MB650-SLEAD-expectedUsed # 650 MB, minus session lead-in, minus 1 sector
      media = MediaDefinition(MEDIA_CDR_74)
      boundaries = (0, 1)
      capacity = CdWriter._calculateCapacity(media, boundaries)
      self.failUnlessEqual(expectedUsed, capacity.bytesUsed)
      self.failUnlessEqual(expectedAvailable, capacity.bytesAvailable)
      self.failUnlessEqual((0, 1), capacity.boundaries)

   def testCapacity_006(self):
      """
      Test _calculateCapacity for boundaries of (0, 1) and MEDIA_CDRW_74.
      """
      expectedUsed = (1*2048.0)                    # 1 sector
      expectedAvailable = MB650-SLEAD-expectedUsed # 650 MB, minus session lead-in, minus 1 sector
      media = MediaDefinition(MEDIA_CDRW_74)
      boundaries = (0, 1)
      capacity = CdWriter._calculateCapacity(media, boundaries)
      self.failUnlessEqual(expectedUsed, capacity.bytesUsed)
      self.failUnlessEqual(expectedAvailable, capacity.bytesAvailable)
      self.failUnlessEqual((0, 1), capacity.boundaries)

   def testCapacity_007(self):
      """
      Test _calculateCapacity for boundaries of (0, 1) and MEDIA_CDR_80.
      """
      expectedUsed = (1*2048.0)                    # 1 sector
      expectedAvailable = MB700-SLEAD-expectedUsed # 700 MB, minus session lead-in, minus 1 sector
      media = MediaDefinition(MEDIA_CDR_80)
      boundaries = (0, 1)
      capacity = CdWriter._calculateCapacity(media, boundaries)
      self.failUnlessEqual(expectedUsed, capacity.bytesUsed)
      self.failUnlessEqual(expectedAvailable, capacity.bytesAvailable) # 700 MB - lead-in - 1 sector
      self.failUnlessEqual((0, 1), capacity.boundaries)

   def testCapacity_008(self):
      """
      Test _calculateCapacity for boundaries of (0, 1) and MEDIA_CDRW_80.
      """
      expectedUsed = (1*2048.0)                    # 1 sector
      expectedAvailable = MB700-SLEAD-expectedUsed # 700 MB, minus session lead-in, minus 1 sector
      media = MediaDefinition(MEDIA_CDRW_80)
      boundaries = (0, 1)
      capacity = CdWriter._calculateCapacity(media, boundaries)
      self.failUnlessEqual(expectedUsed, capacity.bytesUsed)
      self.failUnlessEqual(expectedAvailable, capacity.bytesAvailable)
      self.failUnlessEqual((0, 1), capacity.boundaries)

   def testCapacity_009(self):
      """
      Test _calculateCapacity for boundaries of (0, 999) and MEDIA_CDR_74.
      """
      expectedUsed = (999*2048.0)                  # 999 sectors
      expectedAvailable = MB650-SLEAD-expectedUsed # 650 MB, minus session lead-in, minus 999 sectors
      media = MediaDefinition(MEDIA_CDR_74)
      boundaries = (0, 999)
      capacity = CdWriter._calculateCapacity(media, boundaries)
      self.failUnlessEqual(expectedUsed, capacity.bytesUsed)
      self.failUnlessEqual(expectedAvailable, capacity.bytesAvailable)
      self.failUnlessEqual((0,999), capacity.boundaries)

   def testCapacity_010(self):
      """
      Test _calculateCapacity for boundaries of (0, 999) and MEDIA_CDRW_74.
      """
      expectedUsed = (999*2048.0)                  # 999 sectors
      expectedAvailable = MB650-SLEAD-expectedUsed # 650 MB, minus session lead-in, minus 999 sectors
      media = MediaDefinition(MEDIA_CDRW_74)
      boundaries = (0, 999)
      capacity = CdWriter._calculateCapacity(media, boundaries)
      self.failUnlessEqual(expectedUsed, capacity.bytesUsed)
      self.failUnlessEqual(expectedAvailable, capacity.bytesAvailable)
      self.failUnlessEqual((0, 999), capacity.boundaries)

   def testCapacity_011(self):
      """
      Test _calculateCapacity for boundaries of (0, 999) and MEDIA_CDR_80.
      """
      expectedUsed = (999*2048.0)                  # 999 sectors
      expectedAvailable = MB700-SLEAD-expectedUsed # 700 MB, minus session lead-in, minus 999 sectors
      media = MediaDefinition(MEDIA_CDR_80)
      boundaries = (0, 999)
      capacity = CdWriter._calculateCapacity(media, boundaries)
      self.failUnlessEqual(expectedUsed, capacity.bytesUsed)
      self.failUnlessEqual(expectedAvailable, capacity.bytesAvailable)
      self.failUnlessEqual((0, 999), capacity.boundaries)

   def testCapacity_012(self):
      """
      Test _calculateCapacity for boundaries of (0, 999) and MEDIA_CDRW_80.
      """
      expectedUsed = (999*2048.0)                  # 999 sectors
      expectedAvailable = MB700-SLEAD-expectedUsed # 700 MB, minus session lead-in, minus 999 sectors
      media = MediaDefinition(MEDIA_CDRW_80)
      boundaries = (0, 999)
      capacity = CdWriter._calculateCapacity(media, boundaries)
      self.failUnlessEqual(expectedUsed, capacity.bytesUsed)
      self.failUnlessEqual(expectedAvailable, capacity.bytesAvailable)
      self.failUnlessEqual((0, 999), capacity.boundaries)

   def testCapacity_013(self):
      """
      Test _calculateCapacity for boundaries of (500, 1000) and MEDIA_CDR_74.
      """
      expectedUsed = (1000*2048.0)                 # 1000 sectors
      expectedAvailable = MB650-SLEAD-expectedUsed # 650 MB, minus session lead-in, minus 1000 sectors
      media = MediaDefinition(MEDIA_CDR_74)
      boundaries = (500, 1000)
      capacity = CdWriter._calculateCapacity(media, boundaries)
      self.failUnlessEqual(expectedUsed, capacity.bytesUsed)
      self.failUnlessEqual(expectedAvailable, capacity.bytesAvailable)
      self.failUnlessEqual((500, 1000), capacity.boundaries)

   def testCapacity_014(self):
      """
      Test _calculateCapacity for boundaries of (500, 1000) and MEDIA_CDRW_74.
      """
      expectedUsed = (1000*2048.0)                 # 1000 sectors
      expectedAvailable = MB650-SLEAD-expectedUsed # 650 MB, minus session lead-in, minus 1000 sectors
      media = MediaDefinition(MEDIA_CDRW_74)
      boundaries = (500, 1000)
      capacity = CdWriter._calculateCapacity(media, boundaries)
      self.failUnlessEqual(expectedUsed, capacity.bytesUsed)
      self.failUnlessEqual(expectedAvailable, capacity.bytesAvailable)
      self.failUnlessEqual((500, 1000), capacity.boundaries)

   def testCapacity_015(self):
      """
      Test _calculateCapacity for boundaries of (500, 1000) and MEDIA_CDR_80.
      """
      expectedUsed = (1000*2048.0)                 # 1000 sectors
      expectedAvailable = MB700-SLEAD-expectedUsed # 700 MB, minus session lead-in, minus 1000 sectors
      media = MediaDefinition(MEDIA_CDR_80)
      boundaries = (500, 1000)
      capacity = CdWriter._calculateCapacity(media, boundaries)
      self.failUnlessEqual(expectedUsed, capacity.bytesUsed)
      self.failUnlessEqual(expectedAvailable, capacity.bytesAvailable)
      self.failUnlessEqual((500, 1000), capacity.boundaries)

   def testCapacity_016(self):
      """
      Test _calculateCapacity for boundaries of (500, 1000) and MEDIA_CDRW_80.
      """
      expectedUsed = (1000*2048.0)                 # 1000 sectors
      expectedAvailable = MB700-SLEAD-expectedUsed # 700 MB, minus session lead-in, minus 1000 sectors
      media = MediaDefinition(MEDIA_CDRW_80)
      boundaries = (500, 1000)
      capacity = CdWriter._calculateCapacity(media, boundaries)
      self.failUnlessEqual(expectedUsed, capacity.bytesUsed)
      self.failUnlessEqual(expectedAvailable, capacity.bytesAvailable)    # 650 MB minus lead-in
      self.failUnlessEqual((500, 1000), capacity.boundaries)

   def testCapacity_017(self):
      """
      Test _getBoundaries when self.deviceSupportsMulti is False; entireDisc=False, useMulti=True.
      """
      writer = CdWriter(device="/dev/cdrw", scsiId="0,0,0", unittest=True)
      writer._deviceSupportsMulti = False;
      boundaries = writer._getBoundaries(entireDisc=False, useMulti=True)
      self.failUnlessEqual(None, boundaries)

   def testCapacity_018(self):
      """
      Test _getBoundaries when self.deviceSupportsMulti is False; entireDisc=True, useMulti=True.
      """
      writer = CdWriter(device="/dev/cdrw", scsiId="0,0,0", unittest=True)
      writer._deviceSupportsMulti = False;
      boundaries = writer._getBoundaries(entireDisc=True, useMulti=True)
      self.failUnlessEqual(None, boundaries)

   def testCapacity_019(self):
      """
      Test _getBoundaries when self.deviceSupportsMulti is False; entireDisc=True, useMulti=False.
      """
      writer = CdWriter(device="/dev/cdrw", scsiId="0,0,0", unittest=True)
      writer._deviceSupportsMulti = False;
      boundaries = writer._getBoundaries(entireDisc=False, useMulti=False)
      self.failUnlessEqual(None, boundaries)

   def testCapacity_020(self):
      """
      Test _getBoundaries when self.deviceSupportsMulti is False; entireDisc=False, useMulti=False.
      """
      writer = CdWriter(device="/dev/cdrw", scsiId="0,0,0", unittest=True)
      writer._deviceSupportsMulti = False;
      boundaries = writer._getBoundaries(entireDisc=False, useMulti=False)
      self.failUnlessEqual(None, boundaries)

   # Note: testCapacity_021() has been removed

   def testCapacity_022(self):
      """
      Test _getBoundaries when self.deviceSupportsMulti is True; entireDisc=True, useMulti=True.
      """
      writer = CdWriter(device="/dev/cdrw", scsiId="0,0,0", unittest=True)
      writer._deviceSupportsMulti = True;
      boundaries = writer._getBoundaries(entireDisc=True, useMulti=True)
      self.failUnlessEqual(None, boundaries)

   def testCapacity_023(self):
      """
      Test _getBoundaries when self.deviceSupportsMulti is True; entireDisc=True, useMulti=False.
      """
      writer = CdWriter(device="/dev/cdrw", scsiId="0,0,0", unittest=True)
      writer._deviceSupportsMulti = True;
      boundaries = writer._getBoundaries(entireDisc=True, useMulti=False)
      self.failUnlessEqual(None, boundaries)

   # Note: testCapacity_024() has been removed

   def testCapacity_025(self):
      """
      Test _calculateCapacity for boundaries of (321342, 330042) and MEDIA_CDRW_74.
      This was a bug fixed for v2.1.2.
      """
      expectedUsed = (330042*2048.0)   # 330042 sectors
      expectedAvailable = 0            # nothing should be available
      media = MediaDefinition(MEDIA_CDRW_74)
      boundaries = (321342, 330042)
      capacity = CdWriter._calculateCapacity(media, boundaries)
      self.failUnlessEqual(expectedUsed, capacity.bytesUsed)
      self.failUnlessEqual(expectedAvailable, capacity.bytesAvailable)
      self.failUnlessEqual((321342, 330042), capacity.boundaries)

   def testCapacity_026(self):
      """
      Test _calculateCapacity for boundaries of (0,330042) and MEDIA_CDRW_74.
      This was a bug fixed for v2.1.3.
      """
      expectedUsed = (330042*2048.0)   # 330042 sectors
      expectedAvailable = 0            # nothing should be available
      media = MediaDefinition(MEDIA_CDRW_74)
      boundaries = (0, 330042)
      capacity = CdWriter._calculateCapacity(media, boundaries)
      self.failUnlessEqual(expectedUsed, capacity.bytesUsed)
      self.failUnlessEqual(expectedAvailable, capacity.bytesAvailable)
      self.failUnlessEqual((0, 330042), capacity.boundaries)


   #########################################
   # Test methods that build argument lists
   #########################################

   def testBuildArgs_001(self):
      """
      Test _buildOpenTrayArgs().
      """
      args = CdWriter._buildOpenTrayArgs(device="/dev/stuff")
      self.failUnlessEqual(["/dev/stuff", ], args)

   def testBuildArgs_002(self):
      """
      Test _buildCloseTrayArgs().
      """
      args = CdWriter._buildCloseTrayArgs(device="/dev/stuff")
      self.failUnlessEqual(["-t", "/dev/stuff", ], args)

   def testBuildArgs_003(self):
      """
      Test _buildPropertiesArgs().
      """
      args = CdWriter._buildPropertiesArgs(scsiId="0,0,0")
      self.failUnlessEqual(["-prcap", "dev=0,0,0", ], args)

   def testBuildArgs_004(self):
      """
      Test _buildBoundariesArgs().
      """
      args = CdWriter._buildBoundariesArgs(scsiId="ATA:0,0,0")
      self.failUnlessEqual(["-msinfo", "dev=ATA:0,0,0", ], args)

   def testBuildArgs_005(self):
      """
      Test _buildBoundariesArgs().
      """
      args = CdWriter._buildBoundariesArgs(scsiId="ATAPI:0,0,0")
      self.failUnlessEqual(["-msinfo", "dev=ATAPI:0,0,0", ], args)

   def testBuildArgs_006(self):
      """
      Test _buildBlankArgs(), default drive speed.
      """
      args = CdWriter._buildBlankArgs(scsiId="ATA:0,0,0")
      self.failUnlessEqual(["-v", "blank=fast", "dev=ATA:0,0,0", ], args)

   def testBuildArgs_007(self):
      """
      Test _buildBlankArgs(), default drive speed.
      """
      args = CdWriter._buildBlankArgs(scsiId="ATAPI:0,0,0")
      self.failUnlessEqual(["-v", "blank=fast", "dev=ATAPI:0,0,0", ], args)

   def testBuildArgs_008(self):
      """
      Test _buildBlankArgs(), with None for drive speed.
      """
      args = CdWriter._buildBlankArgs(scsiId="0,0,0", driveSpeed=None)
      self.failUnlessEqual(["-v", "blank=fast", "dev=0,0,0", ], args)

   def testBuildArgs_009(self):
      """
      Test _buildBlankArgs(), with 1 for drive speed.
      """
      args = CdWriter._buildBlankArgs(scsiId="0,0,0", driveSpeed=1)
      self.failUnlessEqual(["-v", "blank=fast", "speed=1", "dev=0,0,0", ], args)

   def testBuildArgs_010(self):
      """
      Test _buildBlankArgs(), with 5 for drive speed.
      """
      args = CdWriter._buildBlankArgs(scsiId="ATA:1,2,3", driveSpeed=5)
      self.failUnlessEqual(["-v", "blank=fast", "speed=5", "dev=ATA:1,2,3", ], args)

   def testBuildArgs_011(self):
      """
      Test _buildBlankArgs(), with 5 for drive speed.
      """
      args = CdWriter._buildBlankArgs(scsiId="ATAPI:1,2,3", driveSpeed=5)
      self.failUnlessEqual(["-v", "blank=fast", "speed=5", "dev=ATAPI:1,2,3", ], args)

   def testBuildArgs_012(self):
      """
      Test _buildWriteArgs(), default drive speed and writeMulti.
      """
      args = CdWriter._buildWriteArgs(scsiId="0,0,0", imagePath="/whatever")
      self.failUnlessEqual(["-v", "dev=0,0,0", "-multi", "-data", "/whatever" ], args)

   def testBuildArgs_013(self):
      """
      Test _buildWriteArgs(), None for drive speed, True for writeMulti.
      """
      args = CdWriter._buildWriteArgs(scsiId="0,0,0", imagePath="/whatever", driveSpeed=None, writeMulti=True)
      self.failUnlessEqual(["-v", "dev=0,0,0", "-multi", "-data", "/whatever" ], args)

   def testBuildArgs_014(self):
      """
      Test _buildWriteArgs(), None for drive speed, False for writeMulti.
      """
      args = CdWriter._buildWriteArgs(scsiId="0,0,0", imagePath="/whatever", driveSpeed=None, writeMulti=False)
      self.failUnlessEqual(["-v", "dev=0,0,0", "-data", "/whatever" ], args)

   def testBuildArgs_015(self):
      """
      Test _buildWriteArgs(), 1 for drive speed, True for writeMulti.
      """
      args = CdWriter._buildWriteArgs(scsiId="0,0,0", imagePath="/whatever", driveSpeed=1, writeMulti=True)
      self.failUnlessEqual(["-v", "speed=1", "dev=0,0,0", "-multi", "-data", "/whatever" ], args)

   def testBuildArgs_016(self):
      """
      Test _buildWriteArgs(), 5 for drive speed, True for writeMulti.
      """
      args = CdWriter._buildWriteArgs(scsiId="0,1,2", imagePath="/whatever", driveSpeed=5, writeMulti=True)
      self.failUnlessEqual(["-v", "speed=5", "dev=0,1,2", "-multi", "-data", "/whatever" ], args)

   def testBuildArgs_017(self):
      """
      Test _buildWriteArgs(), 1 for drive speed, False for writeMulti.
      """
      args = CdWriter._buildWriteArgs(scsiId="0,0,0", imagePath="/dvl/stuff/whatever/more", driveSpeed=1, writeMulti=False)
      self.failUnlessEqual(["-v", "speed=1", "dev=0,0,0", "-data", "/dvl/stuff/whatever/more" ], args)

   def testBuildArgs_018(self):
      """
      Test _buildWriteArgs(), 5 for drive speed, False for writeMulti.
      """
      args = CdWriter._buildWriteArgs(scsiId="ATA:1,2,3", imagePath="/whatever", driveSpeed=5, writeMulti=False)
      self.failUnlessEqual(["-v", "speed=5", "dev=ATA:1,2,3", "-data", "/whatever" ], args)

   def testBuildArgs_019(self):
      """
      Test _buildWriteArgs(), 5 for drive speed, False for writeMulti.
      """
      args = CdWriter._buildWriteArgs(scsiId="ATAPI:1,2,3", imagePath="/whatever", driveSpeed=5, writeMulti=False)
      self.failUnlessEqual(["-v", "speed=5", "dev=ATAPI:1,2,3", "-data", "/whatever" ], args)


   ##########################################
   # Test methods that parse cdrecord output
   ##########################################

   def testParseOutput_001(self):
      """
      Test _parseBoundariesOutput() for valid data, taken from a real example.
      """
      output = [ "268582,302230\n", ]
      boundaries = CdWriter._parseBoundariesOutput(output)
      self.failUnlessEqual((268582, 302230), boundaries)

   def testParseOutput_002(self):
      """
      Test _parseBoundariesOutput() for valid data, taken from a real example,
      lots of extra whitespace around the values.
      """
      output = [ "   268582 ,  302230    \n", ]
      boundaries = CdWriter._parseBoundariesOutput(output)
      self.failUnlessEqual((268582, 302230), boundaries)

   def testParseOutput_003(self):
      """
      Test _parseBoundariesOutput() for valid data, taken from a real example,
      lots of extra garbage after the first line.
      """
      output = [ "268582,302230\n", "more\n", "bogus\n", "crap\n", "here\n", "to\n", "confuse\n", "things\n", ]
      boundaries = CdWriter._parseBoundariesOutput(output)
      self.failUnlessEqual((268582, 302230), boundaries)

   def testParseOutput_004(self):
      """
      Test _parseBoundariesOutput() for valid data, taken from a real example,
      lots of extra garbage before the first line.
      """
      output = [ "more\n", "bogus\n", "crap\n", "here\n", "to\n", "confuse\n", "things\n", "268582,302230\n", ]
      self.failUnlessRaises(IOError, CdWriter._parseBoundariesOutput, output)

   def testParseOutput_005(self):
      """
      Test _parseBoundariesOutput() for valid data, taken from a real example,
      with first value converted to negative.
      """
      output = [ "-268582,302230\n", ]
      self.failUnlessRaises(IOError, CdWriter._parseBoundariesOutput, output)

   def testParseOutput_006(self):
      """
      Test _parseBoundariesOutput() for valid data, taken from a real example,
      with second value converted to negative.
      """
      output = [ "268582,-302230\n", ]
      self.failUnlessRaises(IOError, CdWriter._parseBoundariesOutput, output)

   def testParseOutput_007(self):
      """
      Test _parseBoundariesOutput() for valid data, taken from a real example,
      with first value converted to zero.
      """
      output = [ "0,302230\n", ]
      boundaries = CdWriter._parseBoundariesOutput(output)
      self.failUnlessEqual((0, 302230), boundaries)

   def testParseOutput_008(self):
      """
      Test _parseBoundariesOutput() for valid data, taken from a real example,
      with second value converted to zero.
      """
      output = [ "268582,0\n", ]
      boundaries = CdWriter._parseBoundariesOutput(output)
      self.failUnlessEqual((268582, 0), boundaries)

   def testParseOutput_009(self):
      """
      Test _parseBoundariesOutput() for valid data, taken from a real example,
      with first value converted to negative and second value converted to zero.
      """
      output = [ "-268582,0\n", ]
      self.failUnlessRaises(IOError, CdWriter._parseBoundariesOutput, output)

   def testParseOutput_010(self):
      """
      Test _parseBoundariesOutput() for valid data, taken from a real example,
      with first value converted to zero and second value converted to negative.
      """
      output = [ "0,-302230\n", ]
      self.failUnlessRaises(IOError, CdWriter._parseBoundariesOutput, output)

   def testParseOutput_011(self):
      """
      Test _parsePropertiesOutput() for valid data, taken from a real example,
      including stderr and stdout mixed together.
      """
      output = ["scsidev: '0,0,0'\n", 
                'scsibus: 0 target: 0 lun: 0\n', 
                'Linux sg driver version: 3.1.22\n', 
                'Cdrecord 1.10 (i686-pc-linux-gnu) Copyright (C) 1995-2001 J\xf6rg Schilling\n', 
                "Using libscg version 'schily-0.5'\n", 
                'Device type    : Removable CD-ROM\n', 
                'Version        : 0\n', 
                'Response Format: 1\n', 
                "Vendor_info    : 'SONY    '\n", 
                "Identifikation : 'CD-RW  CRX140E  '\n", 
                "Revision       : '1.0n'\n", 
                'Device seems to be: Generic mmc CD-RW.\n', 
                '\n', 
                'Drive capabilities, per page 2A:\n', 
                '\n', 
                '  Does read CD-R media\n', 
                '  Does write CD-R media\n', 
                '  Does read CD-RW media\n', 
                '  Does write CD-RW media\n', 
                '  Does not read DVD-ROM media\n', 
                '  Does not read DVD-R media\n', 
                '  Does not write DVD-R media\n', 
                '  Does not read DVD-RAM media\n', 
                '  Does not write DVD-RAM media\n', 
                '  Does support test writing\n', '\n', 
                '  Does read Mode 2 Form 1 blocks\n', 
                '  Does read Mode 2 Form 2 blocks\n', 
                '  Does read digital audio blocks\n', 
                '  Does restart non-streamed digital audio reads accurately\n', 
                '  Does not support BURN-Proof (Sanyo)\n', 
                '  Does read multi-session CDs\n', 
                '  Does read fixed-packet CD media using Method 2\n', 
                '  Does not read CD bar code\n', 
                '  Does not read R-W subcode information\n', 
                '  Does read raw P-W subcode data from lead in\n', 
                '  Does return CD media catalog number\n', 
                '  Does return CD ISRC information\n', 
                '  Does not support C2 error pointers\n', 
                '  Does not deliver composite A/V data\n', 
                '\n', 
                '  Does play audio CDs\n', 
                '  Number of volume control levels: 256\n', 
                '  Does support individual volume control setting for each channel\n', 
                '  Does support independent mute setting for each channel\n', 
                '  Does not support digital output on port 1\n', 
                '  Does not support digital output on port 2\n', 
                '\n', 
                '  Loading mechanism type: tray\n', 
                '  Does support ejection of CD via START/STOP command\n', 
                '  Does not lock media on power up via prevent jumper\n', 
                '  Does allow media to be locked in the drive via PREVENT/ALLOW command\n', 
                '  Is not currently in a media-locked state\n', 
                '  Does not support changing side of disk\n', 
                '  Does not have load-empty-slot-in-changer feature\n', 
                '  Does not support Individual Disk Present feature\n', 
                '\n', 
                '  Maximum read  speed in kB/s: 5645\n', 
                '  Current read  speed in kB/s: 3528\n', 
                '  Maximum write speed in kB/s: 1411\n', 
                '  Current write speed in kB/s: 706\n', 
                '  Buffer size in KB: 4096\n', ]
      (deviceType, deviceVendor, deviceId, deviceBufferSize, 
       deviceSupportsMulti, deviceHasTray, deviceCanEject) = CdWriter._parsePropertiesOutput(output)
      self.failUnlessEqual("Removable CD-ROM", deviceType)
      self.failUnlessEqual("SONY", deviceVendor)
      self.failUnlessEqual("CD-RW  CRX140E", deviceId)
      self.failUnlessEqual(4096.0*1024.0, deviceBufferSize)
      self.failUnlessEqual(True, deviceSupportsMulti)
      self.failUnlessEqual(True, deviceHasTray)
      self.failUnlessEqual(True, deviceCanEject)

   def testParseOutput_012(self):
      """
      Test _parsePropertiesOutput() for valid data, taken from a real example,
      including only stdout.
      """
      output = ['Cdrecord 1.10 (i686-pc-linux-gnu) Copyright (C) 1995-2001 J\xf6rg Schilling\n', 
                "Using libscg version 'schily-0.5'\n", 
                'Device type    : Removable CD-ROM\n', 
                'Version        : 0\n', 
                'Response Format: 1\n', 
                "Vendor_info    : 'SONY    '\n", 
                "Identifikation : 'CD-RW  CRX140E  '\n", 
                "Revision       : '1.0n'\n", 
                'Device seems to be: Generic mmc CD-RW.\n', 
                '\n', 
                'Drive capabilities, per page 2A:\n', 
                '\n', 
                '  Does read CD-R media\n', 
                '  Does write CD-R media\n', 
                '  Does read CD-RW media\n', 
                '  Does write CD-RW media\n', 
                '  Does not read DVD-ROM media\n', 
                '  Does not read DVD-R media\n', 
                '  Does not write DVD-R media\n', 
                '  Does not read DVD-RAM media\n', 
                '  Does not write DVD-RAM media\n', 
                '  Does support test writing\n', '\n', 
                '  Does read Mode 2 Form 1 blocks\n', 
                '  Does read Mode 2 Form 2 blocks\n', 
                '  Does read digital audio blocks\n', 
                '  Does restart non-streamed digital audio reads accurately\n', 
                '  Does not support BURN-Proof (Sanyo)\n', 
                '  Does read multi-session CDs\n', 
                '  Does read fixed-packet CD media using Method 2\n', 
                '  Does not read CD bar code\n', 
                '  Does not read R-W subcode information\n', 
                '  Does read raw P-W subcode data from lead in\n', 
                '  Does return CD media catalog number\n', 
                '  Does return CD ISRC information\n', 
                '  Does not support C2 error pointers\n', 
                '  Does not deliver composite A/V data\n', 
                '\n', 
                '  Does play audio CDs\n', 
                '  Number of volume control levels: 256\n', 
                '  Does support individual volume control setting for each channel\n', 
                '  Does support independent mute setting for each channel\n', 
                '  Does not support digital output on port 1\n', 
                '  Does not support digital output on port 2\n', 
                '\n', 
                '  Loading mechanism type: tray\n', 
                '  Does support ejection of CD via START/STOP command\n', 
                '  Does not lock media on power up via prevent jumper\n', 
                '  Does allow media to be locked in the drive via PREVENT/ALLOW command\n', 
                '  Is not currently in a media-locked state\n', 
                '  Does not support changing side of disk\n', 
                '  Does not have load-empty-slot-in-changer feature\n', 
                '  Does not support Individual Disk Present feature\n', 
                '\n', 
                '  Maximum read  speed in kB/s: 5645\n', 
                '  Current read  speed in kB/s: 3528\n', 
                '  Maximum write speed in kB/s: 1411\n', 
                '  Current write speed in kB/s: 706\n', 
                '  Buffer size in KB: 4096\n', ]
      (deviceType, deviceVendor, deviceId, deviceBufferSize, 
       deviceSupportsMulti, deviceHasTray, deviceCanEject) = CdWriter._parsePropertiesOutput(output)
      self.failUnlessEqual("Removable CD-ROM", deviceType)
      self.failUnlessEqual("SONY", deviceVendor)
      self.failUnlessEqual("CD-RW  CRX140E", deviceId)
      self.failUnlessEqual(4096.0*1024.0, deviceBufferSize)
      self.failUnlessEqual(True, deviceSupportsMulti)
      self.failUnlessEqual(True, deviceHasTray)
      self.failUnlessEqual(True, deviceCanEject)

   def testParseOutput_013(self):
      """
      Test _parsePropertiesOutput() for valid data, taken from a real example,
      including stderr and stdout mixed together, device type removed.
      """
      output = ["scsidev: '0,0,0'\n", 
                'scsibus: 0 target: 0 lun: 0\n', 
                'Linux sg driver version: 3.1.22\n', 
                'Cdrecord 1.10 (i686-pc-linux-gnu) Copyright (C) 1995-2001 J\xf6rg Schilling\n', 
                "Using libscg version 'schily-0.5'\n", 
                'Version        : 0\n', 
                'Response Format: 1\n', 
                "Vendor_info    : 'SONY    '\n", 
                "Identifikation : 'CD-RW  CRX140E  '\n", 
                "Revision       : '1.0n'\n", 
                'Device seems to be: Generic mmc CD-RW.\n', 
                '\n', 
                'Drive capabilities, per page 2A:\n', 
                '\n', 
                '  Does read CD-R media\n', 
                '  Does write CD-R media\n', 
                '  Does read CD-RW media\n', 
                '  Does write CD-RW media\n', 
                '  Does not read DVD-ROM media\n', 
                '  Does not read DVD-R media\n', 
                '  Does not write DVD-R media\n', 
                '  Does not read DVD-RAM media\n', 
                '  Does not write DVD-RAM media\n', 
                '  Does support test writing\n', '\n', 
                '  Does read Mode 2 Form 1 blocks\n', 
                '  Does read Mode 2 Form 2 blocks\n', 
                '  Does read digital audio blocks\n', 
                '  Does restart non-streamed digital audio reads accurately\n', 
                '  Does not support BURN-Proof (Sanyo)\n', 
                '  Does read multi-session CDs\n', 
                '  Does read fixed-packet CD media using Method 2\n', 
                '  Does not read CD bar code\n', 
                '  Does not read R-W subcode information\n', 
                '  Does read raw P-W subcode data from lead in\n', 
                '  Does return CD media catalog number\n', 
                '  Does return CD ISRC information\n', 
                '  Does not support C2 error pointers\n', 
                '  Does not deliver composite A/V data\n', 
                '\n', 
                '  Does play audio CDs\n', 
                '  Number of volume control levels: 256\n', 
                '  Does support individual volume control setting for each channel\n', 
                '  Does support independent mute setting for each channel\n', 
                '  Does not support digital output on port 1\n', 
                '  Does not support digital output on port 2\n', 
                '\n', 
                '  Loading mechanism type: tray\n', 
                '  Does support ejection of CD via START/STOP command\n', 
                '  Does not lock media on power up via prevent jumper\n', 
                '  Does allow media to be locked in the drive via PREVENT/ALLOW command\n', 
                '  Is not currently in a media-locked state\n', 
                '  Does not support changing side of disk\n', 
                '  Does not have load-empty-slot-in-changer feature\n', 
                '  Does not support Individual Disk Present feature\n', 
                '\n', 
                '  Maximum read  speed in kB/s: 5645\n', 
                '  Current read  speed in kB/s: 3528\n', 
                '  Maximum write speed in kB/s: 1411\n', 
                '  Current write speed in kB/s: 706\n', 
                '  Buffer size in KB: 4096\n', ]
      (deviceType, deviceVendor, deviceId, deviceBufferSize, 
       deviceSupportsMulti, deviceHasTray, deviceCanEject) = CdWriter._parsePropertiesOutput(output)
      self.failUnlessEqual(None, deviceType)
      self.failUnlessEqual("SONY", deviceVendor)
      self.failUnlessEqual("CD-RW  CRX140E", deviceId)
      self.failUnlessEqual(4096.0*1024.0, deviceBufferSize)
      self.failUnlessEqual(True, deviceSupportsMulti)
      self.failUnlessEqual(True, deviceHasTray)
      self.failUnlessEqual(True, deviceCanEject)

   def testParseOutput_014(self):
      """
      Test _parsePropertiesOutput() for valid data, taken from a real example,
      including stderr and stdout mixed together, device vendor removed.
      """
      output = ["scsidev: '0,0,0'\n", 
                'scsibus: 0 target: 0 lun: 0\n', 
                'Linux sg driver version: 3.1.22\n', 
                'Cdrecord 1.10 (i686-pc-linux-gnu) Copyright (C) 1995-2001 J\xf6rg Schilling\n', 
                "Using libscg version 'schily-0.5'\n", 
                'Device type    : Removable CD-ROM\n', 
                'Version        : 0\n', 
                'Response Format: 1\n', 
                "Identifikation : 'CD-RW  CRX140E  '\n", 
                "Revision       : '1.0n'\n", 
                'Device seems to be: Generic mmc CD-RW.\n', 
                '\n', 
                'Drive capabilities, per page 2A:\n', 
                '\n', 
                '  Does read CD-R media\n', 
                '  Does write CD-R media\n', 
                '  Does read CD-RW media\n', 
                '  Does write CD-RW media\n', 
                '  Does not read DVD-ROM media\n', 
                '  Does not read DVD-R media\n', 
                '  Does not write DVD-R media\n', 
                '  Does not read DVD-RAM media\n', 
                '  Does not write DVD-RAM media\n', 
                '  Does support test writing\n', '\n', 
                '  Does read Mode 2 Form 1 blocks\n', 
                '  Does read Mode 2 Form 2 blocks\n', 
                '  Does read digital audio blocks\n', 
                '  Does restart non-streamed digital audio reads accurately\n', 
                '  Does not support BURN-Proof (Sanyo)\n', 
                '  Does read multi-session CDs\n', 
                '  Does read fixed-packet CD media using Method 2\n', 
                '  Does not read CD bar code\n', 
                '  Does not read R-W subcode information\n', 
                '  Does read raw P-W subcode data from lead in\n', 
                '  Does return CD media catalog number\n', 
                '  Does return CD ISRC information\n', 
                '  Does not support C2 error pointers\n', 
                '  Does not deliver composite A/V data\n', 
                '\n', 
                '  Does play audio CDs\n', 
                '  Number of volume control levels: 256\n', 
                '  Does support individual volume control setting for each channel\n', 
                '  Does support independent mute setting for each channel\n', 
                '  Does not support digital output on port 1\n', 
                '  Does not support digital output on port 2\n', 
                '\n', 
                '  Loading mechanism type: tray\n', 
                '  Does support ejection of CD via START/STOP command\n', 
                '  Does not lock media on power up via prevent jumper\n', 
                '  Does allow media to be locked in the drive via PREVENT/ALLOW command\n', 
                '  Is not currently in a media-locked state\n', 
                '  Does not support changing side of disk\n', 
                '  Does not have load-empty-slot-in-changer feature\n', 
                '  Does not support Individual Disk Present feature\n', 
                '\n', 
                '  Maximum read  speed in kB/s: 5645\n', 
                '  Current read  speed in kB/s: 3528\n', 
                '  Maximum write speed in kB/s: 1411\n', 
                '  Current write speed in kB/s: 706\n', 
                '  Buffer size in KB: 4096\n', ]
      (deviceType, deviceVendor, deviceId, deviceBufferSize, 
       deviceSupportsMulti, deviceHasTray, deviceCanEject) = CdWriter._parsePropertiesOutput(output)
      self.failUnlessEqual("Removable CD-ROM", deviceType)
      self.failUnlessEqual(None, deviceVendor)
      self.failUnlessEqual("CD-RW  CRX140E", deviceId)
      self.failUnlessEqual(4096.0*1024.0, deviceBufferSize)
      self.failUnlessEqual(True, deviceSupportsMulti)
      self.failUnlessEqual(True, deviceHasTray)
      self.failUnlessEqual(True, deviceCanEject)

   def testParseOutput_015(self):
      """
      Test _parsePropertiesOutput() for valid data, taken from a real example,
      including stderr and stdout mixed together, device id removed.
      """
      output = ["scsidev: '0,0,0'\n", 
                'scsibus: 0 target: 0 lun: 0\n', 
                'Linux sg driver version: 3.1.22\n', 
                'Cdrecord 1.10 (i686-pc-linux-gnu) Copyright (C) 1995-2001 J\xf6rg Schilling\n', 
                "Using libscg version 'schily-0.5'\n", 
                'Device type    : Removable CD-ROM\n', 
                'Version        : 0\n', 
                'Response Format: 1\n', 
                "Vendor_info    : 'SONY    '\n", 
                "Revision       : '1.0n'\n", 
                'Device seems to be: Generic mmc CD-RW.\n', 
                '\n', 
                'Drive capabilities, per page 2A:\n', 
                '\n', 
                '  Does read CD-R media\n', 
                '  Does write CD-R media\n', 
                '  Does read CD-RW media\n', 
                '  Does write CD-RW media\n', 
                '  Does not read DVD-ROM media\n', 
                '  Does not read DVD-R media\n', 
                '  Does not write DVD-R media\n', 
                '  Does not read DVD-RAM media\n', 
                '  Does not write DVD-RAM media\n', 
                '  Does support test writing\n', '\n', 
                '  Does read Mode 2 Form 1 blocks\n', 
                '  Does read Mode 2 Form 2 blocks\n', 
                '  Does read digital audio blocks\n', 
                '  Does restart non-streamed digital audio reads accurately\n', 
                '  Does not support BURN-Proof (Sanyo)\n', 
                '  Does read multi-session CDs\n', 
                '  Does read fixed-packet CD media using Method 2\n', 
                '  Does not read CD bar code\n', 
                '  Does not read R-W subcode information\n', 
                '  Does read raw P-W subcode data from lead in\n', 
                '  Does return CD media catalog number\n', 
                '  Does return CD ISRC information\n', 
                '  Does not support C2 error pointers\n', 
                '  Does not deliver composite A/V data\n', 
                '\n', 
                '  Does play audio CDs\n', 
                '  Number of volume control levels: 256\n', 
                '  Does support individual volume control setting for each channel\n', 
                '  Does support independent mute setting for each channel\n', 
                '  Does not support digital output on port 1\n', 
                '  Does not support digital output on port 2\n', 
                '\n', 
                '  Loading mechanism type: tray\n', 
                '  Does support ejection of CD via START/STOP command\n', 
                '  Does not lock media on power up via prevent jumper\n', 
                '  Does allow media to be locked in the drive via PREVENT/ALLOW command\n', 
                '  Is not currently in a media-locked state\n', 
                '  Does not support changing side of disk\n', 
                '  Does not have load-empty-slot-in-changer feature\n', 
                '  Does not support Individual Disk Present feature\n', 
                '\n', 
                '  Maximum read  speed in kB/s: 5645\n', 
                '  Current read  speed in kB/s: 3528\n', 
                '  Maximum write speed in kB/s: 1411\n', 
                '  Current write speed in kB/s: 706\n', 
                '  Buffer size in KB: 4096\n', ]
      (deviceType, deviceVendor, deviceId, deviceBufferSize, 
       deviceSupportsMulti, deviceHasTray, deviceCanEject) = CdWriter._parsePropertiesOutput(output)
      self.failUnlessEqual("Removable CD-ROM", deviceType)
      self.failUnlessEqual("SONY", deviceVendor)
      self.failUnlessEqual(None, deviceId)
      self.failUnlessEqual(4096.0*1024.0, deviceBufferSize)
      self.failUnlessEqual(True, deviceSupportsMulti)
      self.failUnlessEqual(True, deviceHasTray)
      self.failUnlessEqual(True, deviceCanEject)

   def testParseOutput_016(self):
      """
      Test _parsePropertiesOutput() for valid data, taken from a real example,
      including stderr and stdout mixed together, buffer size removed.
      """
      output = ["scsidev: '0,0,0'\n", 
                'scsibus: 0 target: 0 lun: 0\n', 
                'Linux sg driver version: 3.1.22\n', 
                'Cdrecord 1.10 (i686-pc-linux-gnu) Copyright (C) 1995-2001 J\xf6rg Schilling\n', 
                "Using libscg version 'schily-0.5'\n", 
                'Device type    : Removable CD-ROM\n', 
                'Version        : 0\n', 
                'Response Format: 1\n', 
                "Vendor_info    : 'SONY    '\n", 
                "Identifikation : 'CD-RW  CRX140E  '\n", 
                "Revision       : '1.0n'\n", 
                'Device seems to be: Generic mmc CD-RW.\n', 
                '\n', 
                'Drive capabilities, per page 2A:\n', 
                '\n', 
                '  Does read CD-R media\n', 
                '  Does write CD-R media\n', 
                '  Does read CD-RW media\n', 
                '  Does write CD-RW media\n', 
                '  Does not read DVD-ROM media\n', 
                '  Does not read DVD-R media\n', 
                '  Does not write DVD-R media\n', 
                '  Does not read DVD-RAM media\n', 
                '  Does not write DVD-RAM media\n', 
                '  Does support test writing\n', '\n', 
                '  Does read Mode 2 Form 1 blocks\n', 
                '  Does read Mode 2 Form 2 blocks\n', 
                '  Does read digital audio blocks\n', 
                '  Does restart non-streamed digital audio reads accurately\n', 
                '  Does not support BURN-Proof (Sanyo)\n', 
                '  Does read multi-session CDs\n', 
                '  Does read fixed-packet CD media using Method 2\n', 
                '  Does not read CD bar code\n', 
                '  Does not read R-W subcode information\n', 
                '  Does read raw P-W subcode data from lead in\n', 
                '  Does return CD media catalog number\n', 
                '  Does return CD ISRC information\n', 
                '  Does not support C2 error pointers\n', 
                '  Does not deliver composite A/V data\n', 
                '\n', 
                '  Does play audio CDs\n', 
                '  Number of volume control levels: 256\n', 
                '  Does support individual volume control setting for each channel\n', 
                '  Does support independent mute setting for each channel\n', 
                '  Does not support digital output on port 1\n', 
                '  Does not support digital output on port 2\n', 
                '\n', 
                '  Loading mechanism type: tray\n', 
                '  Does support ejection of CD via START/STOP command\n', 
                '  Does not lock media on power up via prevent jumper\n', 
                '  Does allow media to be locked in the drive via PREVENT/ALLOW command\n', 
                '  Is not currently in a media-locked state\n', 
                '  Does not support changing side of disk\n', 
                '  Does not have load-empty-slot-in-changer feature\n', 
                '  Does not support Individual Disk Present feature\n', 
                '\n', 
                '  Maximum read  speed in kB/s: 5645\n', 
                '  Current read  speed in kB/s: 3528\n', 
                '  Maximum write speed in kB/s: 1411\n', 
                '  Current write speed in kB/s: 706\n', ]
      (deviceType, deviceVendor, deviceId, deviceBufferSize, 
       deviceSupportsMulti, deviceHasTray, deviceCanEject) = CdWriter._parsePropertiesOutput(output)
      self.failUnlessEqual("Removable CD-ROM", deviceType)
      self.failUnlessEqual("SONY", deviceVendor)
      self.failUnlessEqual("CD-RW  CRX140E", deviceId)
      self.failUnlessEqual(None, deviceBufferSize)
      self.failUnlessEqual(True, deviceSupportsMulti)
      self.failUnlessEqual(True, deviceHasTray)
      self.failUnlessEqual(True, deviceCanEject)

   def testParseOutput_017(self):
      """
      Test _parsePropertiesOutput() for valid data, taken from a real example,
      including stderr and stdout mixed together, "supports multi" removed.
      """
      output = ["scsidev: '0,0,0'\n", 
                'scsibus: 0 target: 0 lun: 0\n', 
                'Linux sg driver version: 3.1.22\n', 
                'Cdrecord 1.10 (i686-pc-linux-gnu) Copyright (C) 1995-2001 J\xf6rg Schilling\n', 
                "Using libscg version 'schily-0.5'\n", 
                'Device type    : Removable CD-ROM\n', 
                'Version        : 0\n', 
                'Response Format: 1\n', 
                "Vendor_info    : 'SONY    '\n", 
                "Identifikation : 'CD-RW  CRX140E  '\n", 
                "Revision       : '1.0n'\n", 
                'Device seems to be: Generic mmc CD-RW.\n', 
                '\n', 
                'Drive capabilities, per page 2A:\n', 
                '\n', 
                '  Does read CD-R media\n', 
                '  Does write CD-R media\n', 
                '  Does read CD-RW media\n', 
                '  Does write CD-RW media\n', 
                '  Does not read DVD-ROM media\n', 
                '  Does not read DVD-R media\n', 
                '  Does not write DVD-R media\n', 
                '  Does not read DVD-RAM media\n', 
                '  Does not write DVD-RAM media\n', 
                '  Does support test writing\n', '\n', 
                '  Does read Mode 2 Form 1 blocks\n', 
                '  Does read Mode 2 Form 2 blocks\n', 
                '  Does read digital audio blocks\n', 
                '  Does restart non-streamed digital audio reads accurately\n', 
                '  Does not support BURN-Proof (Sanyo)\n', 
                '  Does read fixed-packet CD media using Method 2\n', 
                '  Does not read CD bar code\n', 
                '  Does not read R-W subcode information\n', 
                '  Does read raw P-W subcode data from lead in\n', 
                '  Does return CD media catalog number\n', 
                '  Does return CD ISRC information\n', 
                '  Does not support C2 error pointers\n', 
                '  Does not deliver composite A/V data\n', 
                '\n', 
                '  Does play audio CDs\n', 
                '  Number of volume control levels: 256\n', 
                '  Does support individual volume control setting for each channel\n', 
                '  Does support independent mute setting for each channel\n', 
                '  Does not support digital output on port 1\n', 
                '  Does not support digital output on port 2\n', 
                '\n', 
                '  Loading mechanism type: tray\n', 
                '  Does support ejection of CD via START/STOP command\n', 
                '  Does not lock media on power up via prevent jumper\n', 
                '  Does allow media to be locked in the drive via PREVENT/ALLOW command\n', 
                '  Is not currently in a media-locked state\n', 
                '  Does not support changing side of disk\n', 
                '  Does not have load-empty-slot-in-changer feature\n', 
                '  Does not support Individual Disk Present feature\n', 
                '\n', 
                '  Maximum read  speed in kB/s: 5645\n', 
                '  Current read  speed in kB/s: 3528\n', 
                '  Maximum write speed in kB/s: 1411\n', 
                '  Current write speed in kB/s: 706\n', 
                '  Buffer size in KB: 4096\n', ]
      (deviceType, deviceVendor, deviceId, deviceBufferSize, 
       deviceSupportsMulti, deviceHasTray, deviceCanEject) = CdWriter._parsePropertiesOutput(output)
      self.failUnlessEqual("Removable CD-ROM", deviceType)
      self.failUnlessEqual("SONY", deviceVendor)
      self.failUnlessEqual("CD-RW  CRX140E", deviceId)
      self.failUnlessEqual(4096.0*1024.0, deviceBufferSize)
      self.failUnlessEqual(False, deviceSupportsMulti)
      self.failUnlessEqual(True, deviceHasTray)
      self.failUnlessEqual(True, deviceCanEject)

   def testParseOutput_018(self):
      """
      Test _parsePropertiesOutput() for valid data, taken from a real example,
      including stderr and stdout mixed together, "has tray" removed.
      """
      output = ["scsidev: '0,0,0'\n", 
                'scsibus: 0 target: 0 lun: 0\n', 
                'Linux sg driver version: 3.1.22\n', 
                'Cdrecord 1.10 (i686-pc-linux-gnu) Copyright (C) 1995-2001 J\xf6rg Schilling\n', 
                "Using libscg version 'schily-0.5'\n", 
                'Device type    : Removable CD-ROM\n', 
                'Version        : 0\n', 
                'Response Format: 1\n', 
                "Vendor_info    : 'SONY    '\n", 
                "Identifikation : 'CD-RW  CRX140E  '\n", 
                "Revision       : '1.0n'\n", 
                'Device seems to be: Generic mmc CD-RW.\n', 
                '\n', 
                'Drive capabilities, per page 2A:\n', 
                '\n', 
                '  Does read CD-R media\n', 
                '  Does write CD-R media\n', 
                '  Does read CD-RW media\n', 
                '  Does write CD-RW media\n', 
                '  Does not read DVD-ROM media\n', 
                '  Does not read DVD-R media\n', 
                '  Does not write DVD-R media\n', 
                '  Does not read DVD-RAM media\n', 
                '  Does not write DVD-RAM media\n', 
                '  Does support test writing\n', '\n', 
                '  Does read Mode 2 Form 1 blocks\n', 
                '  Does read Mode 2 Form 2 blocks\n', 
                '  Does read digital audio blocks\n', 
                '  Does restart non-streamed digital audio reads accurately\n', 
                '  Does not support BURN-Proof (Sanyo)\n', 
                '  Does read multi-session CDs\n', 
                '  Does read fixed-packet CD media using Method 2\n', 
                '  Does not read CD bar code\n', 
                '  Does not read R-W subcode information\n', 
                '  Does read raw P-W subcode data from lead in\n', 
                '  Does return CD media catalog number\n', 
                '  Does return CD ISRC information\n', 
                '  Does not support C2 error pointers\n', 
                '  Does not deliver composite A/V data\n', 
                '\n', 
                '  Does play audio CDs\n', 
                '  Number of volume control levels: 256\n', 
                '  Does support individual volume control setting for each channel\n', 
                '  Does support independent mute setting for each channel\n', 
                '  Does not support digital output on port 1\n', 
                '  Does not support digital output on port 2\n', 
                '\n', 
                '  Does support ejection of CD via START/STOP command\n', 
                '  Does not lock media on power up via prevent jumper\n', 
                '  Does allow media to be locked in the drive via PREVENT/ALLOW command\n', 
                '  Is not currently in a media-locked state\n', 
                '  Does not support changing side of disk\n', 
                '  Does not have load-empty-slot-in-changer feature\n', 
                '  Does not support Individual Disk Present feature\n', 
                '\n', 
                '  Maximum read  speed in kB/s: 5645\n', 
                '  Current read  speed in kB/s: 3528\n', 
                '  Maximum write speed in kB/s: 1411\n', 
                '  Current write speed in kB/s: 706\n', 
                '  Buffer size in KB: 4096\n', ]
      (deviceType, deviceVendor, deviceId, deviceBufferSize, 
       deviceSupportsMulti, deviceHasTray, deviceCanEject) = CdWriter._parsePropertiesOutput(output)
      self.failUnlessEqual("Removable CD-ROM", deviceType)
      self.failUnlessEqual("SONY", deviceVendor)
      self.failUnlessEqual("CD-RW  CRX140E", deviceId)
      self.failUnlessEqual(4096.0*1024.0, deviceBufferSize)
      self.failUnlessEqual(True, deviceSupportsMulti)
      self.failUnlessEqual(False, deviceHasTray)
      self.failUnlessEqual(True, deviceCanEject)

   def testParseOutput_019(self):
      """
      Test _parsePropertiesOutput() for valid data, taken from a real example,
      including stderr and stdout mixed together, "can eject" removed.
      """
      output = ["scsidev: '0,0,0'\n", 
                'scsibus: 0 target: 0 lun: 0\n', 
                'Linux sg driver version: 3.1.22\n', 
                'Cdrecord 1.10 (i686-pc-linux-gnu) Copyright (C) 1995-2001 J\xf6rg Schilling\n', 
                "Using libscg version 'schily-0.5'\n", 
                'Device type    : Removable CD-ROM\n', 
                'Version        : 0\n', 
                'Response Format: 1\n', 
                "Vendor_info    : 'SONY    '\n", 
                "Identifikation : 'CD-RW  CRX140E  '\n", 
                "Revision       : '1.0n'\n", 
                'Device seems to be: Generic mmc CD-RW.\n', 
                '\n', 
                'Drive capabilities, per page 2A:\n', 
                '\n', 
                '  Does read CD-R media\n', 
                '  Does write CD-R media\n', 
                '  Does read CD-RW media\n', 
                '  Does write CD-RW media\n', 
                '  Does not read DVD-ROM media\n', 
                '  Does not read DVD-R media\n', 
                '  Does not write DVD-R media\n', 
                '  Does not read DVD-RAM media\n', 
                '  Does not write DVD-RAM media\n', 
                '  Does support test writing\n', '\n', 
                '  Does read Mode 2 Form 1 blocks\n', 
                '  Does read Mode 2 Form 2 blocks\n', 
                '  Does read digital audio blocks\n', 
                '  Does restart non-streamed digital audio reads accurately\n', 
                '  Does not support BURN-Proof (Sanyo)\n', 
                '  Does read multi-session CDs\n', 
                '  Does read fixed-packet CD media using Method 2\n', 
                '  Does not read CD bar code\n', 
                '  Does not read R-W subcode information\n', 
                '  Does read raw P-W subcode data from lead in\n', 
                '  Does return CD media catalog number\n', 
                '  Does return CD ISRC information\n', 
                '  Does not support C2 error pointers\n', 
                '  Does not deliver composite A/V data\n', 
                '\n', 
                '  Does play audio CDs\n', 
                '  Number of volume control levels: 256\n', 
                '  Does support individual volume control setting for each channel\n', 
                '  Does support independent mute setting for each channel\n', 
                '  Does not support digital output on port 1\n', 
                '  Does not support digital output on port 2\n', 
                '\n', 
                '  Loading mechanism type: tray\n', 
                '  Does not lock media on power up via prevent jumper\n', 
                '  Does allow media to be locked in the drive via PREVENT/ALLOW command\n', 
                '  Is not currently in a media-locked state\n', 
                '  Does not support changing side of disk\n', 
                '  Does not have load-empty-slot-in-changer feature\n', 
                '  Does not support Individual Disk Present feature\n', 
                '\n', 
                '  Maximum read  speed in kB/s: 5645\n', 
                '  Current read  speed in kB/s: 3528\n', 
                '  Maximum write speed in kB/s: 1411\n', 
                '  Current write speed in kB/s: 706\n', 
                '  Buffer size in KB: 4096\n', ]
      (deviceType, deviceVendor, deviceId, deviceBufferSize, 
       deviceSupportsMulti, deviceHasTray, deviceCanEject) = CdWriter._parsePropertiesOutput(output)
      self.failUnlessEqual("Removable CD-ROM", deviceType)
      self.failUnlessEqual("SONY", deviceVendor)
      self.failUnlessEqual("CD-RW  CRX140E", deviceId)
      self.failUnlessEqual(4096.0*1024.0, deviceBufferSize)
      self.failUnlessEqual(True, deviceSupportsMulti)
      self.failUnlessEqual(True, deviceHasTray)
      self.failUnlessEqual(False, deviceCanEject)

   def testParseOutput_020(self):
      """
      Test _parsePropertiesOutput() for nonsensical data, just a bunch of empty
      lines.
      """
      output = [ '\n', '\n', '\n', '\n', '\n',  '\n', '\n', '\n', '\n', '\n',  '\n', '\n', '\n', '\n', '\n', ]
      (deviceType, deviceVendor, deviceId, deviceBufferSize, 
       deviceSupportsMulti, deviceHasTray, deviceCanEject) = CdWriter._parsePropertiesOutput(output)
      self.failUnlessEqual(None, deviceType)
      self.failUnlessEqual(None, deviceVendor)
      self.failUnlessEqual(None, deviceId)
      self.failUnlessEqual(None, deviceBufferSize)
      self.failUnlessEqual(False, deviceSupportsMulti)
      self.failUnlessEqual(False, deviceHasTray)
      self.failUnlessEqual(False, deviceCanEject)

   def testParseOutput_021(self):
      """
      Test _parsePropertiesOutput() for nonsensical data, just an empty list.
      """
      output = [ ]
      (deviceType, deviceVendor, deviceId, deviceBufferSize, 
       deviceSupportsMulti, deviceHasTray, deviceCanEject) = CdWriter._parsePropertiesOutput(output)
      self.failUnlessEqual(None, deviceType)
      self.failUnlessEqual(None, deviceVendor)
      self.failUnlessEqual(None, deviceId)
      self.failUnlessEqual(None, deviceBufferSize)
      self.failUnlessEqual(False, deviceSupportsMulti)
      self.failUnlessEqual(False, deviceHasTray)
      self.failUnlessEqual(False, deviceCanEject)


#######################################################################
# Suite definition
#######################################################################

def suite():
   """Returns a suite containing all the test cases in this module."""
   return unittest.TestSuite((
                              unittest.makeSuite(TestFunctions, 'test'),
                              unittest.makeSuite(TestMediaDefinition, 'test'),
                              unittest.makeSuite(TestMediaCapacity, 'test'),
                              unittest.makeSuite(TestCdWriter, 'test'),
                            ))


########################################################################
# Module entry point
########################################################################

# When this module is executed from the command-line, run its tests
if __name__ == '__main__':
   unittest.main()

