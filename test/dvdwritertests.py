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

import os
import unittest
import tempfile
import tarfile

from CedarBackup2.writers.dvdwriter import MediaDefinition, DvdWriter
from CedarBackup2.writers.dvdwriter import MEDIA_DVDPLUSR, MEDIA_DVDPLUSRW

from CedarBackup2.testutil import findResources, buildPath, removedir, extractTar, platformSupportsLinks


#######################################################################
# Module-wide configuration and constants
#######################################################################

GB44        = (4.4*1024.0*1024.0*1024.0)  # 4.4 GB 
GB44SECTORS = GB44/2048.0                 # 4.4 GB in 2048-byte sectors

DATA_DIRS = [ "./data", "./test/data", ]
RESOURCES = [ "tree9.tar.gz", ]


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
      try:
         self.tmpdir = tempfile.mkdtemp()
         self.resources = findResources(RESOURCES, DATA_DIRS)
      except Exception, e:
         self.fail(e)

   def tearDown(self):
      removedir(self.tmpdir)


   ##################
   # Utility methods
   ##################

   def extractTar(self, tarname):
      """Extracts a tarfile with a particular name."""
      extractTar(self.tmpdir, self.resources['%s.tar.gz' % tarname])

   def buildPath(self, components):
      """Builds a complete search path from a list of components."""
      components.insert(0, self.tmpdir)
      return buildPath(components)


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
      self.failUnlessEqual("/dev/dvd", dvdwriter.hardwareId)
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
      dvdwriter = DvdWriter("/dev/dvd", scsiId="00000000", unittest=True)
      self.failUnlessEqual("/dev/dvd", dvdwriter.device)
      self.failUnlessEqual("00000000", dvdwriter.scsiId)
      self.failUnlessEqual("/dev/dvd", dvdwriter.hardwareId)
      self.failUnlessEqual(None, dvdwriter.driveSpeed)
      self.failUnlessEqual(MEDIA_DVDPLUSRW, dvdwriter.media.mediaType)
      self.failUnlessEqual(True, dvdwriter.deviceHasTray)
      self.failUnlessEqual(True, dvdwriter.deviceCanEject)

   def testConstructor_008(self):
      """
      Test with a device and invalid drive speed.
      """
      self.failUnlessRaises(ValueError, DvdWriter, "/dev/dvd", driveSpeed="KEN", unittest=True)

   def testConstructor_009(self):
      """
      Test with a device and invalid media type.
      """
      self.failUnlessRaises(ValueError, DvdWriter, "/dev/dvd", mediaType=999, unittest=True)

   def testConstructor_010(self):
      """
      Test with all valid parameters, but no device, unittest=True.
      """
      self.failUnlessRaises(ValueError, DvdWriter, None, "ATA:1,0,0", 1, MEDIA_DVDPLUSRW, unittest=True)

   def testConstructor_011(self):
      """
      Test with all valid parameters, but no device, unittest=False.
      """
      self.failUnlessRaises(ValueError, DvdWriter, None, "ATA:1,0,0", 1, MEDIA_DVDPLUSRW, unittest=False)

   def testConstructor_012(self):
      """
      Test with all valid parameters, and an invalid device (not absolute path), unittest=True.
      """
      self.failUnlessRaises(ValueError, DvdWriter, "dev/dvd", "ATA:1,0,0", 1, MEDIA_DVDPLUSRW, unittest=True)

   def testConstructor_013(self):
      """
      Test with all valid parameters, and an invalid device (not absolute path), unittest=False.
      """
      self.failUnlessRaises(ValueError, DvdWriter, "dev/dvd", "ATA:1,0,0", 1, MEDIA_DVDPLUSRW, unittest=False)

   def testConstructor_014(self):
      """
      Test with all valid parameters, and an invalid device (path does not exist), unittest=False.
      """
      self.failUnlessRaises(ValueError, DvdWriter, "/dev/bogus", "ATA:1,0,0", 1, MEDIA_DVDPLUSRW, unittest=False)

   def testConstructor_015(self):
      """
      Test with all valid parameters.
      """
      dvdwriter = DvdWriter("/dev/dvd", "ATA:1,0,0", 1, MEDIA_DVDPLUSR, unittest=True)
      self.failUnlessEqual("/dev/dvd", dvdwriter.device)
      self.failUnlessEqual("ATA:1,0,0", dvdwriter.scsiId)
      self.failUnlessEqual("/dev/dvd", dvdwriter.hardwareId)
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
      Test with newDisc=False, tmpdir=None.
      """
      dvdwriter = DvdWriter("/dev/dvd", unittest=True)
      dvdwriter.initializeImage(False, None)
      self.failUnlessEqual(False, dvdwriter._image.newDisc)
      self.failUnlessEqual(None, dvdwriter._image.tmpdir)
      self.failUnlessEqual({}, dvdwriter._image.entries)

   def testInitializeImage_002(self):
      """
      Test with newDisc=True, tmpdir not None.
      """
      dvdwriter = DvdWriter("/dev/dvd", unittest=True)
      dvdwriter.initializeImage(True, "/path/to/somewhere")
      self.failUnlessEqual(True, dvdwriter._image.newDisc)
      self.failUnlessEqual("/path/to/somewhere", dvdwriter._image.tmpdir)
      self.failUnlessEqual({}, dvdwriter._image.entries)


   #######################
   # Test addImageEntry()
   #######################

   def testAddImageEntry_001(self):
      """
      Add a valid path with no graft point, before calling initializeImage().
      """
      self.extractTar("tree9")
      path = self.buildPath([ "tree9", "dir002", ])
      self.failUnless(os.path.exists(path))
      dvdwriter = DvdWriter("/dev/dvd", unittest=True)
      self.failUnlessRaises(ValueError, dvdwriter.addImageEntry, path, None)

   def testAddImageEntry_002(self):
      """
      Add a valid path with a graft point, before calling initializeImage().
      """
      self.extractTar("tree9")
      path = self.buildPath([ "tree9", "dir002", ])
      self.failUnless(os.path.exists(path))
      dvdwriter = DvdWriter("/dev/dvd", unittest=True)
      self.failUnlessRaises(ValueError, dvdwriter.addImageEntry, path, "ken")

   def testAddImageEntry_003(self):
      """
      Add a non-existent path with no graft point, before calling initializeImage().
      """
      self.extractTar("tree9")
      path = self.buildPath([ "tree9", "bogus", ])
      self.failIf(os.path.exists(path))
      dvdwriter = DvdWriter("/dev/dvd", unittest=True)
      self.failUnlessRaises(ValueError, dvdwriter.addImageEntry, path, None)

   def testAddImageEntry_004(self):
      """
      Add a non-existent path with a graft point, before calling initializeImage().
      """
      self.extractTar("tree9")
      path = self.buildPath([ "tree9", "bogus", ])
      self.failIf(os.path.exists(path))
      dvdwriter = DvdWriter("/dev/dvd", unittest=True)
      self.failUnlessRaises(ValueError, dvdwriter.addImageEntry, path, "ken")

   def testAddImageEntry_005(self):
      """
      Add a valid path with no graft point, after calling initializeImage().
      """
      self.extractTar("tree9")
      path = self.buildPath([ "tree9", "dir002", ])
      self.failUnless(os.path.exists(path))
      dvdwriter = DvdWriter("/dev/dvd", unittest=True)
      dvdwriter.initializeImage(False, None)
      dvdwriter.addImageEntry(path, None)
      self.failUnlessEqual({ path:None, }, dvdwriter._image.entries)

   def testAddImageEntry_006(self):
      """
      Add a valid path with a graft point, after calling initializeImage().
      """
      self.extractTar("tree9")
      path = self.buildPath([ "tree9", "dir002", ])
      self.failUnless(os.path.exists(path))
      dvdwriter = DvdWriter("/dev/dvd", unittest=True)
      dvdwriter.initializeImage(False, None)
      dvdwriter.addImageEntry(path, "ken")
      self.failUnlessEqual({ path:"ken", }, dvdwriter._image.entries)

   def testAddImageEntry_007(self):
      """
      Add a non-existent path with no graft point, after calling initializeImage().
      """
      self.extractTar("tree9")
      path = self.buildPath([ "tree9", "bogus", ])
      self.failIf(os.path.exists(path))
      dvdwriter = DvdWriter("/dev/dvd", unittest=True)
      dvdwriter.initializeImage(False, None)
      self.failUnlessRaises(ValueError, dvdwriter.addImageEntry, path, None)

   def testAddImageEntry_008(self):
      """
      Add a non-existent path with a graft point, after calling initializeImage().
      """
      self.extractTar("tree9")
      path = self.buildPath([ "tree9", "bogus", ])
      self.failIf(os.path.exists(path))
      dvdwriter = DvdWriter("/dev/dvd", unittest=True)
      dvdwriter.initializeImage(False, None)
      self.failUnlessRaises(ValueError, dvdwriter.addImageEntry, path, "ken")

   def testAddImageEntry_009(self):
      """
      Add the same path several times.
      """
      self.extractTar("tree9")
      path = self.buildPath([ "tree9", "dir002", ])
      self.failUnless(os.path.exists(path))
      dvdwriter = DvdWriter("/dev/dvd", unittest=True)
      dvdwriter.initializeImage(False, None)
      dvdwriter.addImageEntry(path, "ken")
      self.failUnlessEqual({ path:"ken", }, dvdwriter._image.entries)
      dvdwriter.addImageEntry(path, "ken")
      self.failUnlessEqual({ path:"ken", }, dvdwriter._image.entries)
      dvdwriter.addImageEntry(path, "ken")
      self.failUnlessEqual({ path:"ken", }, dvdwriter._image.entries)
      dvdwriter.addImageEntry(path, "ken")
      self.failUnlessEqual({ path:"ken", }, dvdwriter._image.entries)

   def testAddImageEntry_010(self):
      """
      Add several paths.
      """
      self.extractTar("tree9")
      path1 = self.buildPath([ "tree9", "dir001", ])
      path2 = self.buildPath([ "tree9", "dir002", ])
      path3 = self.buildPath([ "tree9", "dir001", "dir001", ])
      self.failUnless(os.path.exists(path1))
      self.failUnless(os.path.exists(path2))
      self.failUnless(os.path.exists(path3))
      dvdwriter = DvdWriter("/dev/dvd", unittest=True)
      dvdwriter.initializeImage(False, None)
      dvdwriter.addImageEntry(path1, None)
      self.failUnlessEqual({ path1:None, }, dvdwriter._image.entries)
      dvdwriter.addImageEntry(path2, "ken")
      self.failUnlessEqual({ path1:None, path2:"ken", }, dvdwriter._image.entries)
      dvdwriter.addImageEntry(path3, "another")
      self.failUnlessEqual({ path1:None, path2:"ken", path3:"another", }, dvdwriter._image.entries)


   ################################
   # Test _getEstimatedImageSize()
   ################################

   def testGetEstimatedImageSize_001(self):
      """
      Test for tree9, where size is known from filesystemtest.TestBackupFileList.testTotalSize_006()
      """
      self.extractTar("tree9")
      path = self.buildPath([ "tree9", ])
      dvdwriter = DvdWriter("/dev/dvd", unittest=True)
      dvdwriter.initializeImage(False, None)
      dvdwriter.addImageEntry(path, None)
      size = DvdWriter._getEstimatedImageSize(dvdwriter._image.entries)
      if not platformSupportsLinks():
         self.failUnlessEqual(1835, size)
      else:
         self.failUnlessEqual(1116, size)


   ############################
   # Test _searchForOverburn()
   ############################

   def testSearchForOverburn_001(self):
      """
      Test with output=None.
      """
      output = None
      DvdWriter._searchForOverburn(output)  # no exception should be thrown

   def testSearchForOverburn_002(self):
      """
      Test with output=[].
      """
      output = []
      DvdWriter._searchForOverburn(output)  # no exception should be thrown

   def testSearchForOverburn_003(self):
      """
      Test with one-line output, not containing the pattern.
      """
      output = [ "This line does not contain the pattern", ]
      DvdWriter._searchForOverburn(output)  # no exception should be thrown
      output = [ ":-( /dev/cdrom: blocks are free, to be written!", ]
      DvdWriter._searchForOverburn(output)  # no exception should be thrown
      output = [ ":-) /dev/cdrom: 89048 blocks are free, 2033746 to be written!", ]
      DvdWriter._searchForOverburn(output)  # no exception should be thrown
      output = [ ":-( /dev/cdrom: 894048blocks are free, 2033746to be written!", ]
      DvdWriter._searchForOverburn(output)  # no exception should be thrown

   def testSearchForOverburn_004(self):
      """
      Test with one-line output(s), containing the pattern.
      """
      output = [ ":-( /dev/cdrom: 894048 blocks are free, 2033746 to be written!", ]
      self.failUnlessRaises(IOError, DvdWriter._searchForOverburn, output)
      output = [ ":-( /dev/cdrom: XXXX blocks are free, XXXX to be written!", ]
      self.failUnlessRaises(IOError, DvdWriter._searchForOverburn, output)
      output = [ ":-( /dev/cdrom: 1 blocks are free, 1 to be written!", ]
      self.failUnlessRaises(IOError, DvdWriter._searchForOverburn, output)
      output = [ ":-( /dev/cdrom: 0 blocks are free, 0 to be written!", ]
      self.failUnlessRaises(IOError, DvdWriter._searchForOverburn, output)
      output = [ ":-( /dev/dvd: 0 blocks are free, 0 to be written!", ]
      self.failUnlessRaises(IOError, DvdWriter._searchForOverburn, output)
      output = [ ":-( /dev/writer: 0 blocks are free, 0 to be written!", ]
      self.failUnlessRaises(IOError, DvdWriter._searchForOverburn, output)
      output = [ ":-( bogus: 0 blocks are free, 0 to be written!", ]
      self.failUnlessRaises(IOError, DvdWriter._searchForOverburn, output)

   def testSearchForOverburn_005(self):
      """
      Test with multi-line output, not containing the pattern.
      """
      output = []
      output.append("Executing 'mkisofs -C 973744,1401056 -M /dev/fd/3 -r -graft-points music4/=music | builtin_dd of=/dev/cdrom obs=32k seek=87566'")
      output.append("Rock Ridge signatures found")
      output.append("Using THE_K000 for  music4/The_Kings_Singers (The_Kingston_Trio)")
      output.append("Using COCKT000 for music/Various_Artists/Cocktail_Classics_-_Beethovens_Fifth_and_Others (Cocktail_Classics_-_Pachelbels_Canon_and_Others)")
      output.append("Using THE_V000 for  music/Brahms/The_Violin_Sonatas (The_Viola_Sonatas) Using COMPL000 for  music/Gershwin/Complete_Gershwin_2 (Complete_Gershwin_1)")
      output.append("Using SELEC000.MP3;1 for music/Marquette_Chorus/Selected_Christmas_Carols_For_Double_Choir.mp3 (Selected_Choruses_from_The_Lark.mp3)")
      output.append("Using SELEC001.MP3;1 for music/Marquette_Chorus/Selected_Choruses_from_The_Lark.mp3 (Selected_Choruses_from_Messiah.mp3)")
      output.append("Using IN_TH000.MP3;1 for  music/Marquette_Chorus/In_the_Bleak_Midwinter.mp3 (In_the_Beginning.mp3) Using AFRIC000.MP3;1 for  music/Marquette_Chorus/African_Noel-tb.mp3 (African_Noel-satb.mp3)")
      DvdWriter._searchForOverburn(output)  # no exception should be thrown")

   def testSearchForOverburn_006(self):
      """
      Test with multi-line output, containing the pattern at the top.
      """
      output = []
      output.append(":-( /dev/cdrom: 894048 blocks are free, 2033746 to be written!")
      output.append("Executing 'mkisofs -C 973744,1401056 -M /dev/fd/3 -r -graft-points music4/=music | builtin_dd of=/dev/cdrom obs=32k seek=87566'")
      output.append("Rock Ridge signatures found")
      output.append("Using THE_K000 for  music4/The_Kings_Singers (The_Kingston_Trio)")
      output.append("Using COCKT000 for music/Various_Artists/Cocktail_Classics_-_Beethovens_Fifth_and_Others (Cocktail_Classics_-_Pachelbels_Canon_and_Others)")
      output.append("Using THE_V000 for  music/Brahms/The_Violin_Sonatas (The_Viola_Sonatas) Using COMPL000 for  music/Gershwin/Complete_Gershwin_2 (Complete_Gershwin_1)")
      output.append("Using SELEC000.MP3;1 for music/Marquette_Chorus/Selected_Christmas_Carols_For_Double_Choir.mp3 (Selected_Choruses_from_The_Lark.mp3)")
      output.append("Using SELEC001.MP3;1 for music/Marquette_Chorus/Selected_Choruses_from_The_Lark.mp3 (Selected_Choruses_from_Messiah.mp3)")
      output.append("Using IN_TH000.MP3;1 for  music/Marquette_Chorus/In_the_Bleak_Midwinter.mp3 (In_the_Beginning.mp3) Using AFRIC000.MP3;1 for  music/Marquette_Chorus/African_Noel-tb.mp3 (African_Noel-satb.mp3)")
      self.failUnlessRaises(IOError, DvdWriter._searchForOverburn, output)

   def testSearchForOverburn_007(self):
      """
      Test with multi-line output, containing the pattern at the bottom.
      """
      output = []
      output.append("Executing 'mkisofs -C 973744,1401056 -M /dev/fd/3 -r -graft-points music4/=music | builtin_dd of=/dev/cdrom obs=32k seek=87566'")
      output.append("Rock Ridge signatures found")
      output.append("Using THE_K000 for  music4/The_Kings_Singers (The_Kingston_Trio)")
      output.append("Using COCKT000 for music/Various_Artists/Cocktail_Classics_-_Beethovens_Fifth_and_Others (Cocktail_Classics_-_Pachelbels_Canon_and_Others)")
      output.append("Using THE_V000 for  music/Brahms/The_Violin_Sonatas (The_Viola_Sonatas) Using COMPL000 for  music/Gershwin/Complete_Gershwin_2 (Complete_Gershwin_1)")
      output.append("Using SELEC000.MP3;1 for music/Marquette_Chorus/Selected_Christmas_Carols_For_Double_Choir.mp3 (Selected_Choruses_from_The_Lark.mp3)")
      output.append("Using SELEC001.MP3;1 for music/Marquette_Chorus/Selected_Choruses_from_The_Lark.mp3 (Selected_Choruses_from_Messiah.mp3)")
      output.append("Using IN_TH000.MP3;1 for  music/Marquette_Chorus/In_the_Bleak_Midwinter.mp3 (In_the_Beginning.mp3) Using AFRIC000.MP3;1 for  music/Marquette_Chorus/African_Noel-tb.mp3 (African_Noel-satb.mp3)")
      output.append(":-( /dev/cdrom: 894048 blocks are free, 2033746 to be written!")
      self.failUnlessRaises(IOError, DvdWriter._searchForOverburn, output)

   def testSearchForOverburn_008(self):
      """
      Test with multi-line output, containing the pattern in the middle.
      """
      output = []
      output.append("Executing 'mkisofs -C 973744,1401056 -M /dev/fd/3 -r -graft-points music4/=music | builtin_dd of=/dev/cdrom obs=32k seek=87566'")
      output.append("Rock Ridge signatures found")
      output.append("Using THE_K000 for  music4/The_Kings_Singers (The_Kingston_Trio)")
      output.append("Using COCKT000 for music/Various_Artists/Cocktail_Classics_-_Beethovens_Fifth_and_Others (Cocktail_Classics_-_Pachelbels_Canon_and_Others)")
      output.append(":-( /dev/cdrom: 894048 blocks are free, 2033746 to be written!")
      output.append("Using THE_V000 for  music/Brahms/The_Violin_Sonatas (The_Viola_Sonatas) Using COMPL000 for  music/Gershwin/Complete_Gershwin_2 (Complete_Gershwin_1)")
      output.append("Using SELEC000.MP3;1 for music/Marquette_Chorus/Selected_Christmas_Carols_For_Double_Choir.mp3 (Selected_Choruses_from_The_Lark.mp3)")
      output.append("Using SELEC001.MP3;1 for music/Marquette_Chorus/Selected_Choruses_from_The_Lark.mp3 (Selected_Choruses_from_Messiah.mp3)")
      output.append("Using IN_TH000.MP3;1 for  music/Marquette_Chorus/In_the_Bleak_Midwinter.mp3 (In_the_Beginning.mp3) Using AFRIC000.MP3;1 for  music/Marquette_Chorus/African_Noel-tb.mp3 (African_Noel-satb.mp3)")
      self.failUnlessRaises(IOError, DvdWriter._searchForOverburn, output)

   def testSearchForOverburn_009(self):
      """
      Test with multi-line output, containing the pattern several times.
      """
      output = []
      output.append(":-( /dev/cdrom: 894048 blocks are free, 2033746 to be written!")
      output.append("Executing 'mkisofs -C 973744,1401056 -M /dev/fd/3 -r -graft-points music4/=music | builtin_dd of=/dev/cdrom obs=32k seek=87566'")
      output.append(":-( /dev/cdrom: 894048 blocks are free, 2033746 to be written!")
      output.append("Rock Ridge signatures found")
      output.append(":-( /dev/cdrom: 894048 blocks are free, 2033746 to be written!")
      output.append("Using THE_K000 for  music4/The_Kings_Singers (The_Kingston_Trio)")
      output.append(":-( /dev/cdrom: 894048 blocks are free, 2033746 to be written!")
      output.append("Using COCKT000 for music/Various_Artists/Cocktail_Classics_-_Beethovens_Fifth_and_Others (Cocktail_Classics_-_Pachelbels_Canon_and_Others)")
      output.append(":-( /dev/cdrom: 894048 blocks are free, 2033746 to be written!")
      output.append("Using THE_V000 for  music/Brahms/The_Violin_Sonatas (The_Viola_Sonatas) Using COMPL000 for  music/Gershwin/Complete_Gershwin_2 (Complete_Gershwin_1)")
      output.append(":-( /dev/cdrom: 894048 blocks are free, 2033746 to be written!")
      output.append("Using SELEC000.MP3;1 for music/Marquette_Chorus/Selected_Christmas_Carols_For_Double_Choir.mp3 (Selected_Choruses_from_The_Lark.mp3)")
      output.append(":-( /dev/cdrom: 894048 blocks are free, 2033746 to be written!")
      output.append("Using SELEC001.MP3;1 for music/Marquette_Chorus/Selected_Choruses_from_The_Lark.mp3 (Selected_Choruses_from_Messiah.mp3)")
      output.append(":-( /dev/cdrom: 894048 blocks are free, 2033746 to be written!")
      output.append("Using IN_TH000.MP3;1 for  music/Marquette_Chorus/In_the_Bleak_Midwinter.mp3 (In_the_Beginning.mp3) Using AFRIC000.MP3;1 for  music/Marquette_Chorus/African_Noel-tb.mp3 (African_Noel-satb.mp3)")
      output.append(":-( /dev/cdrom: 894048 blocks are free, 2033746 to be written!")
      output.append(":-( /dev/cdrom: 894048 blocks are free, 2033746 to be written!")
      self.failUnlessRaises(IOError, DvdWriter._searchForOverburn, output)


   #########################
   # Test _buildWriteArgs()
   #########################

   def testBuildWriteArgs_001(self):
      """
      Test with newDisc=False, hardwareId="/dev/dvd", driveSpeed=None, imagePath=None, entries=None, dryRun=False.
      """
      newDisc = False
      hardwareId = "/dev/dvd"
      driveSpeed = None
      imagePath = None
      entries = None
      dryRun = False
      self.failUnlessRaises(ValueError, DvdWriter._buildWriteArgs, newDisc, hardwareId, driveSpeed, imagePath, entries, dryRun)

   def testBuildWriteArgs_002(self):
      """
      Test with newDisc=False, hardwareId="/dev/dvd", driveSpeed=None, imagePath=None, entries=None, dryRun=True.
      """
      newDisc = False
      hardwareId = "/dev/dvd"
      driveSpeed = None
      imagePath = None
      entries = None
      dryRun = True
      self.failUnlessRaises(ValueError, DvdWriter._buildWriteArgs, newDisc, hardwareId, driveSpeed, imagePath, entries, dryRun)

   def testBuildWriteArgs_003(self):
      """
      Test with newDisc=False, hardwareId="/dev/dvd", driveSpeed=None, imagePath="/path/to/image", entries=None, dryRun=False.
      """
      newDisc = False
      hardwareId = "/dev/dvd"
      driveSpeed = None
      imagePath = "/path/to/image"
      entries = None
      dryRun = False
      expected = [ "-M", "/dev/dvd=/path/to/image", ]
      actual = DvdWriter._buildWriteArgs(newDisc, hardwareId, driveSpeed, imagePath, entries, dryRun)
      self.failUnlessEqual(actual, expected)

   def testBuildWriteArgs_004(self):
      """
      Test with newDisc=False, hardwareId="/dev/dvd", driveSpeed=None, imagePath="/path/to/image", entries=None, dryRun=True.
      """
      newDisc = False
      hardwareId = "/dev/dvd"
      driveSpeed = None
      imagePath = "/path/to/image"
      entries = None
      dryRun = True
      expected = [ "--dry-run", "-M", "/dev/dvd=/path/to/image", ]
      actual = DvdWriter._buildWriteArgs(newDisc, hardwareId, driveSpeed, imagePath, entries, dryRun)
      self.failUnlessEqual(actual, expected)

   def testBuildWriteArgs_005(self):
      """
      Test with newDisc=True, hardwareId="/dev/dvd", driveSpeed=None, imagePath="/path/to/image", entries=None, dryRun=False.
      """
      newDisc = True
      hardwareId = "/dev/dvd"
      driveSpeed = None
      imagePath = "/path/to/image"
      entries = None
      dryRun = False
      expected = [ "-Z", "/dev/dvd=/path/to/image", ]
      actual = DvdWriter._buildWriteArgs(newDisc, hardwareId, driveSpeed, imagePath, entries, dryRun)
      self.failUnlessEqual(actual, expected)

   def testBuildWriteArgs_006(self):
      """
      Test with newDisc=True, hardwareId="/dev/dvd", driveSpeed=None, imagePath="/path/to/image", entries=None, dryRun=True.
      """
      newDisc = True
      hardwareId = "/dev/dvd"
      driveSpeed = None
      imagePath = "/path/to/image"
      entries = None
      dryRun = True
      expected = [ "--dry-run", "-Z", "/dev/dvd=/path/to/image", ]
      actual = DvdWriter._buildWriteArgs(newDisc, hardwareId, driveSpeed, imagePath, entries, dryRun)
      self.failUnlessEqual(actual, expected)

   def testBuildWriteArgs_007(self):
      """
      Test with newDisc=False, hardwareId="/dev/dvd", driveSpeed=1, imagePath="/path/to/image", entries=None, dryRun=False.
      """
      newDisc = False
      hardwareId = "/dev/dvd"
      driveSpeed = 1
      imagePath = "/path/to/image"
      entries = None
      dryRun = False
      expected = [ "-speed=1", "-M", "/dev/dvd=/path/to/image", ]
      actual = DvdWriter._buildWriteArgs(newDisc, hardwareId, driveSpeed, imagePath, entries, dryRun)
      self.failUnlessEqual(actual, expected)

   def testBuildWriteArgs_008(self):
      """
      Test with newDisc=False, hardwareId="/dev/dvd", driveSpeed=2, imagePath="/path/to/image", entries=None, dryRun=True.
      """
      newDisc = False
      hardwareId = "/dev/dvd"
      driveSpeed = 2
      imagePath = "/path/to/image"
      entries = None
      dryRun = True
      expected = [ "--dry-run", "-speed=2", "-M", "/dev/dvd=/path/to/image", ]
      actual = DvdWriter._buildWriteArgs(newDisc, hardwareId, driveSpeed, imagePath, entries, dryRun)
      self.failUnlessEqual(actual, expected)

   def testBuildWriteArgs_009(self):
      """
      Test with newDisc=True, hardwareId="/dev/dvd", driveSpeed=3, imagePath="/path/to/image", entries=None, dryRun=False.
      """
      newDisc = True
      hardwareId = "/dev/dvd"
      driveSpeed = 3
      imagePath = "/path/to/image"
      entries = None
      dryRun = False
      expected = [ "-speed=3", "-Z", "/dev/dvd=/path/to/image", ]
      actual = DvdWriter._buildWriteArgs(newDisc, hardwareId, driveSpeed, imagePath, entries, dryRun)
      self.failUnlessEqual(actual, expected)

   def testBuildWriteArgs_010(self):
      """
      Test with newDisc=True, hardwareId="/dev/dvd", driveSpeed=4, imagePath="/path/to/image", entries=None, dryRun=True.
      """
      newDisc = True
      hardwareId = "/dev/dvd"
      driveSpeed = 4
      imagePath = "/path/to/image"
      entries = None
      dryRun = True
      expected = [ "--dry-run", "-speed=4", "-Z", "/dev/dvd=/path/to/image", ]
      actual = DvdWriter._buildWriteArgs(newDisc, hardwareId, driveSpeed, imagePath, entries, dryRun)
      self.failUnlessEqual(actual, expected)

   def testBuildWriteArgs_011(self):
      """
      Test with newDisc=False, hardwareId="/dev/dvd", driveSpeed=None, imagePath=None, entries=<one>, dryRun=False.
      """
      newDisc = False
      hardwareId = "/dev/dvd"
      driveSpeed = None
      imagePath = None
      entries = { "path1":None, }
      dryRun = False
      expected = [ "-M", "/dev/dvd", "-r", "-graft-points", "path1", ]
      actual = DvdWriter._buildWriteArgs(newDisc, hardwareId, driveSpeed, imagePath, entries, dryRun)
      self.failUnlessEqual(actual, expected)

   def testBuildWriteArgs_012(self):
      """
      Test with newDisc=False, hardwareId="/dev/dvd", driveSpeed=None, imagePath=None, entries=<one>, dryRun=True.
      """
      newDisc = False
      hardwareId = "/dev/dvd"
      driveSpeed = None
      imagePath = None
      entries = { "path1":None, }
      dryRun = True
      expected = [ "--dry-run", "-M", "/dev/dvd", "-r", "-graft-points", "path1", ]
      actual = DvdWriter._buildWriteArgs(newDisc, hardwareId, driveSpeed, imagePath, entries, dryRun)
      self.failUnlessEqual(actual, expected)

   def testBuildWriteArgs_013(self):
      """
      Test with newDisc=True, hardwareId="/dev/dvd", driveSpeed=None, imagePath=None, entries=<several>, dryRun=False.
      """
      newDisc = True
      hardwareId = "/dev/dvd"
      driveSpeed = None
      imagePath = None
      entries = { "path1":None, "path2":"graft2", "path3":"/path/to/graft3", }
      dryRun = False
      expected = [ "-Z", "/dev/dvd", "-r", "-graft-points", "path1", "graft2/=path2", "path/to/graft3/=path3", ]
      actual = DvdWriter._buildWriteArgs(newDisc, hardwareId, driveSpeed, imagePath, entries, dryRun)
      self.failUnlessEqual(actual, expected)

   def testBuildWriteArgs_014(self):
      """
      Test with newDisc=True, hardwareId="/dev/dvd", driveSpeed=None, imagePath=None, entries=<several>, dryRun=True.
      """
      newDisc = True
      hardwareId = "/dev/dvd"
      driveSpeed = None
      imagePath = None
      entries = { "path1":None, "path2":"graft2", "path3":"/path/to/graft3", }
      dryRun = True
      expected = [ "--dry-run", "-Z", "/dev/dvd", "-r", "-graft-points", "path1", "graft2/=path2", "path/to/graft3/=path3", ]
      actual = DvdWriter._buildWriteArgs(newDisc, hardwareId, driveSpeed, imagePath, entries, dryRun)
      self.failUnlessEqual(actual, expected)

   def testBuildWriteArgs_015(self):
      """
      Test with newDisc=False, hardwareId="/dev/dvd", driveSpeed=1, imagePath=None, entries=<several>, dryRun=False.
      """
      newDisc = False
      hardwareId = "/dev/dvd"
      driveSpeed = 1
      imagePath = None
      entries = { "path1":None, "path2":"graft2", }
      dryRun = False
      expected = [ "-speed=1", "-M", "/dev/dvd", "-r", "-graft-points", "path1", "graft2/=path2", ]
      actual = DvdWriter._buildWriteArgs(newDisc, hardwareId, driveSpeed, imagePath, entries, dryRun)
      self.failUnlessEqual(actual, expected)

   def testBuildWriteArgs_016(self):
      """
      Test with newDisc=False, hardwareId="/dev/dvd", driveSpeed=2, imagePath=None, entries=<several>, dryRun=True.
      """
      newDisc = False
      hardwareId = "/dev/dvd"
      driveSpeed = 2
      imagePath = None
      entries = { "path1":None, "path2":"graft2", }
      dryRun = True
      expected = [ "--dry-run", "-speed=2", "-M", "/dev/dvd", "-r", "-graft-points", "path1", "graft2/=path2", ]
      actual = DvdWriter._buildWriteArgs(newDisc, hardwareId, driveSpeed, imagePath, entries, dryRun)
      self.failUnlessEqual(actual, expected)

   def testBuildWriteArgs_017(self):
      """
      Test with newDisc=True, hardwareId="/dev/dvd", driveSpeed=3, imagePath=None, entries=<several>, dryRun=False.
      """
      newDisc = True
      hardwareId = "/dev/dvd"
      driveSpeed = 3
      imagePath = None
      entries = { "path1":None, "/path/to/path2":None, "/path/to/path3/":"/path/to/graft3/", }
      dryRun = False
      expected = [ "-speed=3", "-Z", "/dev/dvd", "-r", "-graft-points", 
                   "/path/to/path2", "path/to/graft3/=/path/to/path3/", "path1", ]  # sorted order
      actual = DvdWriter._buildWriteArgs(newDisc, hardwareId, driveSpeed, imagePath, entries, dryRun)
      self.failUnlessEqual(actual, expected)

   def testBuildWriteArgs_018(self):
      """
      Test with newDisc=True, hardwareId="/dev/dvd", driveSpeed=4, imagePath=None, entries=<several>, dryRun=True.
      """
      newDisc = True
      hardwareId = "/dev/dvd"
      driveSpeed = 4
      imagePath = None
      entries = { "path1":None, "/path/to/path2":None, "/path/to/path3/":"/path/to/graft3/", }
      dryRun = True
      expected = [ "--dry-run", "-speed=4", "-Z", "/dev/dvd", "-r", "-graft-points", 
                   "/path/to/path2", "path/to/graft3/=/path/to/path3/", "path1", ]  # sorted order
      actual = DvdWriter._buildWriteArgs(newDisc, hardwareId, driveSpeed, imagePath, entries, dryRun)
      self.failUnlessEqual(actual, expected)


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

