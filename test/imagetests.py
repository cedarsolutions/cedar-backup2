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
   implemented in image.py.  There are also tests for several of the private
   methods.

   I usually prefer to test only the public interface to a class, because that
   way the regression tests don't depend on the internal implementation.  In
   this case, I've decided to test some of the private methods, because their
   "privateness" is more a matter of presenting a clean external interface than
   anything else (most of the private methods are static).  Being able to test
   these methods also makes it easier to gain some reasonable confidence in the
   code even some tests are not run because IMAGETESTS_FULL is not set to "Y"
   in the environment (see below).

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
   suite that has no surprising system, kernel or network requirements.  If you
   want to run all of the tests, set IMAGETESTS_FULL to "Y" in the environment.

   In this module, there are three dependencies: the system must have
   C{mkisofs} installed, the kernel must allow ISO images to be mounted
   in-place via a loopback mechanism, and the current user must be allowed (via
   C{sudo}) to mount and unmount such loopback filesystems.  See documentation
   by the L{TestIsoImage.mountImage} and L{TestIsoImageunmountImage} methods
   for more information on what C{sudo} access is required.

@author Kenneth J. Pronovici <pronovic@ieee.org>
"""


########################################################################
# Import modules and do runtime validations
########################################################################

# Import standard modules
import os
import unittest
import tempfile
import tarfile
from CedarBackup2.image import IsoImage, BYTES_PER_MBYTE
from CedarBackup2.util import executeCommand


#######################################################################
# Module-wide configuration and constants
#######################################################################

DATA_DIRS = [ "./data", "./test/data", ]
RESOURCES = [ "tree9.tar.gz", ]

SUDO_CMD = [ "sudo", ]
INVALID_FILE = "bogus"         # This file name should never exist


#######################################################################
# Utility functions
#######################################################################

def runAllTests():
   """Returns true/false depending on whether the full test suite should be run."""
   if "IMAGETESTS_FULL" in os.environ:
      return os.environ["IMAGETESTS_FULL"] == "Y"
   else:
      return False

def findResources():
   """Returns a dictionary of locations for various resources."""
   resources = { }
   for resource in RESOURCES:
      for resourceDir in DATA_DIRS:
         path = os.path.join(resourceDir, resource);
         if os.path.exists(path):
            resources[resource] = path
            break
      else:
         raise Exception("Unable to find resource [%s]." % resource)
   return resources

def extractTar(tmpdir, filepath):
   """Extracts the indicated tar file to self.tmpdir."""
   tar = tarfile.open(filepath)
   for tarinfo in tar:
      tar.extract(tarinfo, tmpdir)

def buildPath(components):
   """Builds a complete path from a list of components."""
   path = components[0]
   for component in components[1:]:
      path = os.path.join(path, component)
   return path

def removedir(tree):
   """Recursively removes an entire directory."""
   for root, dirs, files in os.walk(tree, topdown=False):
      for name in files:
         path = os.path.join(root, name)
         if os.path.islink(path):
            os.remove(path)
         elif os.path.isfile(path):
            os.remove(path)
      for name in dirs:
         path = os.path.join(root, name)
         if os.path.islink(path):
            os.remove(path)
         elif os.path.isdir(path):
            os.rmdir(path)
   os.rmdir(tree)

def getBytes(mb):
   """
   Converts a megabyte (MB) value to bytes.
   """
   return float(mb) * BYTES_PER_MBYTE


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
      try:
         self.tmpdir = tempfile.mkdtemp()
         self.resources = findResources()
      except Exception, e:
         self.fail(e)

   def tearDown(self):
      removedir(self.tmpdir)


   ##################
   # Utility methods
   ##################

   def mountImage(self, imagePath):
      """
      Mounts an ISO image at C{self.tmpdir/mnt} using loopback.

      Note that this will fail unless the user has been granted permissions via
      sudo, using something like this:

         Cmnd_Alias LOOPMOUNT = /bin/mount -t iso9660 -o loop * *

      Keep in mind that this entry is a security hole, so you might not want to
      keep it in C{/etc/sudoers} all of the time.

      @return: Path the image is mounted at.
      @raise IOError: If the command cannot be executed.
      """
      mountPath = self.buildPath([ "mnt", ])
      os.mkdir(mountPath)
      args = [ "mount", "-t", "iso9660", "-o", "loop", imagePath, mountPath, ]
      (result, output) = executeCommand(SUDO_CMD, args, returnOutput=True)
      if result != 0:
         raise IOError("Error (%d) executing mkisofs command to mount image." % result)
      return mountPath
      
   def unmountImage(self):
      """
      Unmounts an ISO image from C{self.tmpdir/mnt}.

      Note that this will fail unless the user has been granted permissions via
      sudo, using something like this:

         Cmnd_Alias LOOPUNMOUNT  = /bin/umount -t iso9660 *

      Keep in mind that this entry is a security hole, so you might not want to
      keep it in C{/etc/sudoers} all of the time.

      @raise IOError: If the command cannot be executed.
      """
      mountPath = self.buildPath([ "mnt", ])
      args = [ "umount", "-t", "iso9660", mountPath, ]
      (result, output) = executeCommand(SUDO_CMD, args, returnOutput=False)
      if result != 0:
         raise IOError("Error (%d) executing mkisofs command to unmount image." % result)


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


   ################################
   # Test IsoImage utility methods
   ################################

   def testUtilityMethods_001(self):
      """
      Test _buildDirEntries() with an empty entries dictionary.
      """
      entries = {}
      result = IsoImage._buildDirEntries(entries)
      self.failUnlessEqual(0, len(result))

   def testUtilityMethods_002(self):
      """
      Test _buildDirEntries() with an entries dictionary that has no graft points.
      """
      entries = {}
      entries["/one/two/three"] = None
      entries["/four/five/six"] = None
      entries["/seven/eight/nine"] = None
      result = IsoImage._buildDirEntries(entries)
      self.failUnlessEqual(3, len(result))
      self.failUnless("/one/two/three" in result)
      self.failUnless("/four/five/six" in result)
      self.failUnless("/seven/eight/nine" in result)

   def testUtilityMethods_003(self):
      """
      Test _buildDirEntries() with an entries dictionary that has all graft points.
      """
      entries = {}
      entries["/one/two/three"] = "/backup1"
      entries["/four/five/six"] = "backup2"
      entries["/seven/eight/nine"] = "backup3"
      result = IsoImage._buildDirEntries(entries)
      self.failUnlessEqual(3, len(result))
      self.failUnless("backup1/=/one/two/three" in result)
      self.failUnless("backup2/=/four/five/six" in result)
      self.failUnless("backup3/=/seven/eight/nine" in result)

   def testUtilityMethods_004(self):
      """
      Test _buildDirEntries() with an entries dictionary that has mixed graft points and not.
      """
      entries = {}
      entries["/one/two/three"] = "backup1"
      entries["/four/five/six"] = None
      entries["/seven/eight/nine"] = "/backup3"
      result = IsoImage._buildDirEntries(entries)
      self.failUnlessEqual(3, len(result))
      self.failUnless("backup1/=/one/two/three" in result)
      self.failUnless("/four/five/six" in result)
      self.failUnless("backup3/=/seven/eight/nine" in result)

   def testUtilityMethods_005(self):
      """
      Test _buildGeneralArgs() with all optional values as None.
      """
      isoImage = IsoImage()
      result = isoImage._buildGeneralArgs()
      self.failUnlessEqual(0, len(result))

   def testUtilityMethods_006(self):
      """
      Test _buildGeneralArgs() with applicationId set.
      """
      isoImage = IsoImage()
      isoImage.applicationId = "one"
      result = isoImage._buildGeneralArgs()
      self.failUnlessEqual(["-A", "one", ], result)

   def testUtilityMethods_007(self):
      """
      Test _buildGeneralArgs() with biblioFile set.
      """
      isoImage = IsoImage()
      isoImage.biblioFile = "two"
      result = isoImage._buildGeneralArgs()
      self.failUnlessEqual(["-biblio", "two", ], result)

   def testUtilityMethods_008(self):
      """
      Test _buildGeneralArgs() with publisherId set.
      """
      isoImage = IsoImage()
      isoImage.publisherId = "three"
      result = isoImage._buildGeneralArgs()
      self.failUnlessEqual(["-publisher", "three", ], result)

   def testUtilityMethods_009(self):
      """
      Test _buildGeneralArgs() with preparerId set.
      """
      isoImage = IsoImage()
      isoImage.preparerId = "four"
      result = isoImage._buildGeneralArgs()
      self.failUnlessEqual(["-p", "four", ], result)

   def testUtilityMethods_010(self):
      """
      Test _buildGeneralArgs() with volumeId set.
      """
      isoImage = IsoImage()
      isoImage.volumeId = "five"
      result = isoImage._buildGeneralArgs()
      self.failUnlessEqual(["-V", "five", ], result)

   def testUtilityMethods_011(self):
      """
      Test _buildSizeArgs() with device and boundaries at defaults.
      """
      entries = {}
      entries["/one/two/three"] = "backup1"
      isoImage = IsoImage()
      result = isoImage._buildSizeArgs(entries)
      self.failUnlessEqual(["-print-size", "-graft-points", "-r", "backup1/=/one/two/three", ], result)

   def testUtilityMethods_012(self):
      """
      Test _buildSizeArgs() with useRockRidge set to True and device and
      boundaries at defaults.
      """
      entries = {}
      entries["/one/two/three"] = "backup1"
      isoImage = IsoImage()
      isoImage.useRockRidge = True
      result = isoImage._buildSizeArgs(entries)
      self.failUnlessEqual(["-print-size", "-graft-points", "-r", "backup1/=/one/two/three", ], result)

   def testUtilityMethods_013(self):
      """
      Test _buildSizeArgs() with useRockRidge set to False and device and
      boundaries at defaults.
      """
      entries = {}
      entries["/one/two/three"] = "backup1"
      isoImage = IsoImage()
      isoImage.useRockRidge = False
      result = isoImage._buildSizeArgs(entries)
      self.failUnlessEqual(["-print-size", "-graft-points", "backup1/=/one/two/three", ], result)

   def testUtilityMethods_014(self):
      """
      Test _buildSizeArgs() with device as None and boundaries as non-None.
      """
      entries = {}
      entries["/one/two/three"] = "backup1"
      isoImage = IsoImage(device=None, boundaries=(1, 2))
      result = isoImage._buildSizeArgs(entries)
      self.failUnlessEqual(["-print-size", "-graft-points", "-r", "backup1/=/one/two/three", ], result)

   def testUtilityMethods_015(self):
      """
      Test _buildSizeArgs() with device as non-None and boundaries as None.
      """
      entries = {}
      entries["/one/two/three"] = "backup1"
      isoImage = IsoImage(device="/dev/cdrw", boundaries=None)
      result = isoImage._buildSizeArgs(entries)
      self.failUnlessEqual(["-print-size", "-graft-points", "-r", "backup1/=/one/two/three", ], result)

   def testUtilityMethods_016(self):
      """
      Test _buildSizeArgs() with device and boundaries as non-None.
      """
      entries = {}
      entries["/one/two/three"] = "backup1"
      isoImage = IsoImage(device="/dev/cdrw", boundaries=(1, 2))
      result = isoImage._buildSizeArgs(entries)
      self.failUnlessEqual(["-print-size", "-graft-points", "-r", "-C", "1,2", "-M", "/dev/cdrw", "backup1/=/one/two/three", ], 
                           result)

   def testUtilityMethods_017(self):
      """
      Test _buildWriteArgs() with device and boundaries at defaults.
      """
      entries = {}
      entries["/one/two/three"] = "backup1"
      isoImage = IsoImage()
      result = isoImage._buildWriteArgs(entries, "/tmp/file.iso")
      self.failUnlessEqual(["-graft-points", "-r", "-o", "/tmp/file.iso", "backup1/=/one/two/three", ], result)

   def testUtilityMethods_018(self):
      """
      Test _buildWriteArgs() with useRockRidge set to True and device and
      boundaries at defaults.
      """
      entries = {}
      entries["/one/two/three"] = "backup1"
      isoImage = IsoImage()
      isoImage.useRockRidge = True
      result = isoImage._buildWriteArgs(entries, "/tmp/file.iso")
      self.failUnlessEqual(["-graft-points", "-r", "-o", "/tmp/file.iso", "backup1/=/one/two/three", ], result)

   def testUtilityMethods_019(self):
      """
      Test _buildWriteArgs() with useRockRidge set to False and device and
      boundaries at defaults.
      """
      entries = {}
      entries["/one/two/three"] = "backup1"
      isoImage = IsoImage()
      isoImage.useRockRidge = False
      result = isoImage._buildWriteArgs(entries, "/tmp/file.iso")
      self.failUnlessEqual(["-graft-points", "-o", "/tmp/file.iso", "backup1/=/one/two/three", ], result)

   def testUtilityMethods_020(self):
      """
      Test _buildWriteArgs() with device as None and boundaries as non-None.
      """
      entries = {}
      entries["/one/two/three"] = "backup1"
      isoImage = IsoImage(device=None, boundaries=(3, 4))
      isoImage.useRockRidge = False
      result = isoImage._buildWriteArgs(entries, "/tmp/file.iso")
      self.failUnlessEqual(["-graft-points", "-o", "/tmp/file.iso", "backup1/=/one/two/three", ], result)

   def testUtilityMethods_021(self):
      """
      Test _buildWriteArgs() with device as non-None and boundaries as None.
      """
      entries = {}
      entries["/one/two/three"] = "backup1"
      isoImage = IsoImage(device="/dev/cdrw", boundaries=None)
      isoImage.useRockRidge = False
      result = isoImage._buildWriteArgs(entries, "/tmp/file.iso")
      self.failUnlessEqual(["-graft-points", "-o", "/tmp/file.iso", "backup1/=/one/two/three", ], result)

   def testUtilityMethods_022(self):
      """
      Test _buildWriteArgs() with device and boundaries as non-None.
      """
      entries = {}
      entries["/one/two/three"] = "backup1"
      isoImage = IsoImage(device="/dev/cdrw", boundaries=(3, 4))
      isoImage.useRockRidge = False
      result = isoImage._buildWriteArgs(entries, "/tmp/file.iso")
      self.failUnlessEqual(["-graft-points", "-o", "/tmp/file.iso", "-C", "3,4", "-M", "/dev/cdrw", "backup1/=/one/two/three", ], 
                           result)

   def testUtilityMethods_023(self):
      """
      Test _calculateSizes with an empty entries dictionary.
      """
      entries = {}
      (table, total) = IsoImage._calculateSizes(entries)
      self.failUnlessEqual({}, table)
      self.failUnlessEqual(0, total)

   def testUtilityMethods_024(self):
      """
      Test _calculateSizes with an entries dictionary containing only a single file.
      """
      entries = {}
      self.extractTar("tree9")
      file1 = self.buildPath(["tree9", "file001", ])
      entries[file1] = None
      (table, total) = IsoImage._calculateSizes(entries)
      self.failUnlessEqual({ file1:(file1,155), }, table)
      self.failUnlessEqual(155, total)
      
   def testUtilityMethods_025(self):
      """
      Test _calculateSizes with an entries dictionary containing multiple files.
      """
      entries = {}
      self.extractTar("tree9")
      file1 = self.buildPath(["tree9", "file001", ])
      file2 = self.buildPath(["tree9", "file002", ])
      file3 = self.buildPath(["tree9", "dir001", "file001", ])
      entries[file1] = None
      entries[file2] = None
      entries[file3] = None
      (table, total) = IsoImage._calculateSizes(entries)
      self.failUnlessEqual({ file1:(file1,155), file2:(file2,242), file3:(file3,243), }, table)
      self.failUnlessEqual(640, total)

   def testUtilityMethods_026(self):
      """
      Test _calculateSizes with an entries dictionary containing files,
      directories, links and invalid items.
      """
      entries = {}
      self.extractTar("tree9")
      file1 = self.buildPath(["tree9", "file001", ])
      file2 = self.buildPath(["tree9", "file002", ])
      file3 = self.buildPath(["tree9", "dir001", "file001", ])
      file4 = self.buildPath(["tree9", INVALID_FILE, ])
      dir1 = self.buildPath(["tree9", "dir001", ])
      link1 = self.buildPath(["tree9", "link001", ])
      entries[file1] = None
      entries[file2] = None
      entries[file3] = None
      entries[file4] = None
      entries[dir1] = None
      entries[link1] = None
      (table, total) = IsoImage._calculateSizes(entries)
      self.failUnlessEqual({ file1:(file1,155), file2:(file2,242), file3:(file3,243), }, table)
      self.failUnlessEqual(640, total)

   def testUtilityMethods_027(self):
      """
      Test _buildEntries with an empty entries dictionary and empty items list.
      """
      entries = {}
      items = []
      result = IsoImage._buildEntries(entries, items)
      self.failUnlessEqual({}, result)

   def testUtilityMethods_028(self):
      """
      Test _buildEntries with a valid entries dictionary and items list.
      """
      entries = { "a":1, "b":2, "c":3, "d":4, "e":5, "f":6, }
      items = [ "a", "c", "e", ]
      result = IsoImage._buildEntries(entries, items)
      self.failUnlessEqual({ "a":1, "c":3, "e":5, }, result)

   def testUtilityMethods_029(self):
      """
      Test _buildEntries with an items list containing a key not in the entries dictionary.
      """
      entries = { "a":1, "b":2, "c":3, "d":4, "e":5, "f":6, }
      items = [ "a", "c", "e", "z", ]
      self.failUnlessRaises(KeyError, IsoImage._buildEntries, entries, items)

   def testUtilityMethods_030(self):
      """
      Test _expandEntries with an empty entries dictionary.
      """
      entries = {}
      result = IsoImage._expandEntries(entries)
      self.failUnlessEqual({}, result)

   def testUtilityMethods_031(self):
      """
      Test _expandEntries with an entries dictionary containing only a single file.
      """
      entries = {}
      self.extractTar("tree9")
      file1 = self.buildPath(["tree9", "file001", ])
      entries[file1] = None
      result = IsoImage._expandEntries(entries)
      self.failUnlessEqual({ file1:None, }, result)

   def testUtilityMethods_032(self):
      """
      Test _expandEntries with an entries dictionary containing only files.
      """
      entries = {}
      self.extractTar("tree9")
      file1 = self.buildPath(["tree9", "file001", ])
      file2 = self.buildPath(["tree9", "file002", ])
      entries[file1] = None
      entries[file2] = "whatever"
      result = IsoImage._expandEntries(entries)
      self.failUnlessEqual({ file1:None, file2:"whatever", }, result)

   def testUtilityMethods_033(self):
      """
      Test _expandEntries with an entries dictionary containing only a single empty directory.
      """
      entries = {}
      self.extractTar("tree9")
      dir1 = self.buildPath(["tree9", "dir002", "dir001", ])
      entries[dir1] = "something"
      result = IsoImage._expandEntries(entries)
      self.failUnlessEqual({}, result)

   def testUtilityMethods_034(self):
      """
      Test _expandEntries with an entries dictionary containing only a single non-empty directory.
      """
      entries = {}
      self.extractTar("tree9")
      dir1 = self.buildPath(["tree9", "dir001", ])
      file1 = self.buildPath(["tree9", "dir001", "file001", ])
      file2 = self.buildPath(["tree9", "dir001", "file002", ])
      file1graft = os.path.join("something", "dir001")
      file2graft = os.path.join("something", "dir001")
      entries[dir1] = "something/dir001"
      result = IsoImage._expandEntries(entries)
      self.failUnlessEqual({ file1:file1graft, file2:file2graft, }, result)

   def testUtilityMethods_035(self):
      """
      Test _expandEntries with an entries dictionary containing only directories.
      """
      entries = {}
      self.extractTar("tree9")
      dir1 = self.buildPath(["tree9", "dir001", ])
      dir2 = self.buildPath(["tree9", "dir002", ])
      file1 = self.buildPath(["tree9", "dir001", "file001", ])
      file2 = self.buildPath(["tree9", "dir001", "file002", ])
      file3 = self.buildPath(["tree9", "dir002", "file001", ])
      file4 = self.buildPath(["tree9", "dir002", "file002", ])
      file1graft = os.path.join("something", "dir001")
      file2graft = os.path.join("something", "dir001")
      file3graft = os.path.join("whatever", "dir002")
      file4graft = os.path.join("whatever", "dir002")
      entries[dir1] = "something/dir001"
      entries[dir2] = "whatever/dir002"
      result = IsoImage._expandEntries(entries)
      self.failUnlessEqual({ file1:file1graft, file2:file2graft, file3:file3graft, file4:file4graft, }, result)

   def testUtilityMethods_036(self):
      """
      Test _expandEntries with an entries dictionary containing files and directories.
      """
      entries = {}
      self.extractTar("tree9")
      dir1 = self.buildPath(["tree9", "dir001", ])
      dir2 = self.buildPath(["tree9", "dir002", ])
      file1 = self.buildPath(["tree9", "dir001", "file001", ])
      file2 = self.buildPath(["tree9", "dir001", "file002", ])
      file3 = self.buildPath(["tree9", "dir002", "file001", ])
      file4 = self.buildPath(["tree9", "dir002", "file002", ])
      file5 = self.buildPath(["tree9", "file001", ])
      file6 = self.buildPath(["tree9", "file002", ])
      file1graft = os.path.join("something", "dir001")
      file2graft = os.path.join("something", "dir001")
      file3graft = None
      file4graft = None
      file5graft = None
      file6graft = os.path.join("three")
      entries[dir1] = "something/dir001"
      entries[dir2] = None
      entries[file5] = None
      entries[file6] = "three"
      result = IsoImage._expandEntries(entries)
      self.failUnlessEqual({ file1:file1graft, file2:file2graft, file3:file3graft, file4:file4graft,
                             file5:file5graft, file6:file6graft, }, result)

   def testUtilityMethods_037(self):
      """
      Test _expandEntries with a deeply-nested entries dictionary.
      """
      entries = {}
      self.extractTar("tree9")
      dir1 = self.buildPath(["tree9", ])
      file1 = self.buildPath(["tree9", "dir001", "file001", ])
      file2 = self.buildPath(["tree9", "dir001", "file002", ])
      file3 = self.buildPath(["tree9", "dir002", "file001", ])
      file4 = self.buildPath(["tree9", "dir002", "file002", ])
      file5 = self.buildPath(["tree9", "file001", ])
      file6 = self.buildPath(["tree9", "file002", ])
      file1graft = os.path.join("bogus", "tree9", "dir001")
      file2graft = os.path.join("bogus", "tree9", "dir001")
      file3graft = os.path.join("bogus", "tree9", "dir002")
      file4graft = os.path.join("bogus", "tree9", "dir002")
      file5graft = os.path.join("bogus", "tree9")
      file6graft = os.path.join("bogus", "tree9")
      entries[dir1] = "bogus/tree9"
      result = IsoImage._expandEntries(entries)
      self.failUnlessEqual({ file1:file1graft, file2:file2graft, file3:file3graft, file4:file4graft,
                             file5:file5graft, file6:file6graft, }, result)

   ##################
   # Test addEntry()
   ##################

   def testAddEntry_001(self):
      """
      Attempt to add a non-existent entry.
      """
      file1 = self.buildPath([ INVALID_FILE, ])
      isoImage = IsoImage()
      self.failUnlessRaises(ValueError, isoImage.addEntry, file1)

   def testAddEntry_002(self):
      """
      Attempt to add a an entry that is a soft link to a file.
      """
      self.extractTar("tree9")
      file1 = self.buildPath([ "tree9", "dir002", "link003", ])
      isoImage = IsoImage()
      self.failUnlessRaises(ValueError, isoImage.addEntry, file1)

   def testAddEntry_003(self):
      """
      Attempt to add a an entry that is a soft link to a directory
      """
      self.extractTar("tree9")
      file1 = self.buildPath([ "tree9", "link001", ])
      isoImage = IsoImage()
      self.failUnlessRaises(ValueError, isoImage.addEntry, file1)

   def testAddEntry_004(self):
      """
      Attempt to add a file, no graft point set.
      """
      self.extractTar("tree9")
      file1 = self.buildPath([ "tree9", "file001", ])
      isoImage = IsoImage()
      self.failUnlessEqual({}, isoImage.entries)
      isoImage.addEntry(file1)
      self.failUnlessEqual({ file1:None, }, isoImage.entries)

   def testAddEntry_005(self):
      """
      Attempt to add a file, graft point set on the object level.
      """
      self.extractTar("tree9")
      file1 = self.buildPath([ "tree9", "file001", ])
      isoImage = IsoImage(graftPoint="whatever")
      self.failUnlessEqual({}, isoImage.entries)
      isoImage.addEntry(file1)
      self.failUnlessEqual({ file1:"whatever", }, isoImage.entries)

   def testAddEntry_006(self):
      """
      Attempt to add a file, graft point set on the method level.
      """
      self.extractTar("tree9")
      file1 = self.buildPath([ "tree9", "file001", ])
      isoImage = IsoImage()
      self.failUnlessEqual({}, isoImage.entries)
      isoImage.addEntry(file1, graftPoint="stuff")
      self.failUnlessEqual({ file1:"stuff", }, isoImage.entries)

   def testAddEntry_007(self):
      """
      Attempt to add a file, graft point set on the object and method levels.
      """
      self.extractTar("tree9")
      file1 = self.buildPath([ "tree9", "file001", ])
      isoImage = IsoImage(graftPoint="whatever")
      self.failUnlessEqual({}, isoImage.entries)
      isoImage.addEntry(file1, graftPoint="stuff")
      self.failUnlessEqual({ file1:"stuff", }, isoImage.entries)

   def testAddEntry_008(self):
      """
      Attempt to add a directory, no graft point set.
      """
      self.extractTar("tree9")
      dir1 = self.buildPath([ "tree9" ])
      isoImage = IsoImage()
      self.failUnlessEqual({}, isoImage.entries)
      isoImage.addEntry(dir1)
      self.failUnlessEqual({ dir1:None, }, isoImage.entries)

   def testAddEntry_009(self):
      """
      Attempt to add a directory, graft point set on the object level.
      """
      self.extractTar("tree9")
      dir1 = self.buildPath([ "tree9" ])
      isoImage = IsoImage(graftPoint="p")
      self.failUnlessEqual({}, isoImage.entries)
      isoImage.addEntry(dir1)
      self.failUnlessEqual({ dir1:"p/tree9" }, isoImage.entries)

   def testAddEntry_010(self):
      """
      Attempt to add a directory, graft point set on the method level.
      """
      self.extractTar("tree9")
      dir1 = self.buildPath([ "tree9" ])
      isoImage = IsoImage()
      self.failUnlessEqual({}, isoImage.entries)
      isoImage.addEntry(dir1, graftPoint="s")
      self.failUnlessEqual({ dir1:"s/tree9", }, isoImage.entries)

   def testAddEntry_011(self):
      """
      Attempt to add a directory, graft point set on the object and methods levels.
      """
      self.extractTar("tree9")
      dir1 = self.buildPath([ "tree9" ])
      isoImage = IsoImage(graftPoint="p")
      self.failUnlessEqual({}, isoImage.entries)
      isoImage.addEntry(dir1, graftPoint="s")
      self.failUnlessEqual({ dir1:"s/tree9", }, isoImage.entries)

   def testAddEntry_012(self):
      """
      Attempt to add a file that has already been added, override=False.
      """
      self.extractTar("tree9")
      file1 = self.buildPath([ "tree9", "file001", ])
      isoImage = IsoImage()
      self.failUnlessEqual({}, isoImage.entries)
      isoImage.addEntry(file1)
      self.failUnlessEqual({ file1:None, }, isoImage.entries)
      self.failUnlessRaises(ValueError, isoImage.addEntry, file1, override=False)
      self.failUnlessEqual({ file1:None, }, isoImage.entries)

   def testAddEntry_013(self):
      """
      Attempt to add a file that has already been added, override=True.
      """
      self.extractTar("tree9")
      file1 = self.buildPath([ "tree9", "file001", ])
      isoImage = IsoImage()
      self.failUnlessEqual({}, isoImage.entries)
      isoImage.addEntry(file1)
      self.failUnlessEqual({ file1:None, }, isoImage.entries)
      isoImage.addEntry(file1, override=True)
      self.failUnlessEqual({ file1:None, }, isoImage.entries)

   def testAddEntry_014(self):
      """
      Attempt to add a directory that has already been added, override=False, changing the graft point.
      """
      self.extractTar("tree9")
      file1 = self.buildPath([ "tree9", "file001", ])
      isoImage = IsoImage(graftPoint="whatever")
      self.failUnlessEqual({}, isoImage.entries)
      isoImage.addEntry(file1, graftPoint="one")
      self.failUnlessEqual({ file1:"one", }, isoImage.entries)
      self.failUnlessRaises(ValueError, isoImage.addEntry, file1, graftPoint="two", override=False)
      self.failUnlessEqual({ file1:"one", }, isoImage.entries)

   def testAddEntry_015(self):
      """
      Attempt to add a directory that has already been added, override=True, changing the graft point.
      """
      self.extractTar("tree9")
      file1 = self.buildPath([ "tree9", "file001", ])
      isoImage = IsoImage(graftPoint="whatever")
      self.failUnlessEqual({}, isoImage.entries)
      isoImage.addEntry(file1, graftPoint="one")
      self.failUnlessEqual({ file1:"one", }, isoImage.entries)
      isoImage.addEntry(file1, graftPoint="two", override=True)
      self.failUnlessEqual({ file1:"two", }, isoImage.entries)


   ##########################
   # Test getEstimatedSize()
   ##########################

   def testGetEstimatedSize_001(self):
      """
      Test with an empty list.
      """
      pass
      self.extractTar("tree9")
      isoImage = IsoImage()
      self.failUnlessRaises(ValueError, isoImage.getEstimatedSize)

   def testGetEstimatedSize_002(self):
      """
      Test with non-empty empty list.
      """
      self.extractTar("tree9")
      dir1 = self.buildPath([ "tree9", ])
      isoImage = IsoImage()
      isoImage.addEntry(dir1, graftPoint="base")
      result = isoImage.getEstimatedSize()
      self.failUnless(result > 0)


   ####################
   # Test pruneImage() 
   ####################

   def testPruneImage_001(self):
      """
      Attempt to prune an image containing no entries.
      """
      isoImage = IsoImage()
      self.failUnlessRaises(ValueError, isoImage.pruneImage, getBytes(650))
   
   def testPruneImage_002(self):
      """
      Attempt to prune a non-empty image using a capacity for which all entries
      will fit.
      """
      self.extractTar("tree9")
      dir1 = self.buildPath([ "tree9", ])
      file1 = self.buildPath([ "tree9", "file001", ])
      file2 = self.buildPath([ "tree9", "file002", ])
      file3 = self.buildPath([ "tree9", "dir001", "file001", ])
      file4 = self.buildPath([ "tree9", "dir001", "file002", ])
      file5 = self.buildPath([ "tree9", "dir002", "file001", ])
      file6 = self.buildPath([ "tree9", "dir002", "file002", ])
      dir1graft = "b/tree9"
      file1graft = os.path.join("b", "tree9")
      file2graft = os.path.join("b", "tree9")
      file3graft = os.path.join("b", "tree9", "dir001")
      file4graft = os.path.join("b", "tree9", "dir001")
      file5graft = os.path.join("b", "tree9", "dir002")
      file6graft = os.path.join("b", "tree9", "dir002")
      isoImage = IsoImage()
      isoImage.addEntry(dir1, graftPoint="b")
      self.failUnlessEqual({ dir1:dir1graft, }, isoImage.entries)
      result = isoImage.pruneImage(getBytes(650))  # plenty large for everything to fit
      self.failUnless(result > 0)
      self.failUnlessEqual({ file1:file1graft, file2:file2graft, file3:file3graft, file4:file4graft, 
                             file5:file5graft, file6:file6graft, }, isoImage.entries)
   
   def testPruneImage_003(self):
      """
      Attempt to prune a non-empty image using a capacity for which some
      entries will fit.

      This is one of those tests that may be fairly sensitive to specific
      mkisofs versions, but I don't know for sure.  A pretty-much empty image
      has around 381860 bytes of overhead.  If I set a capacity slightly larger
      than that (say 382000 bytes), some files should fit but not others.  All I
      can try to validate is that we don't get an exception and that the total
      number of included files is greater than zero.
      """
      self.extractTar("tree9")
      dir1 = self.buildPath([ "tree9", ])
      isoImage = IsoImage()
      isoImage.addEntry(dir1, None)
      self.failUnlessEqual({ dir1:None, }, isoImage.entries)
      result = isoImage.pruneImage(382000)  # from experimentation
      self.failUnless(result > 0)
      self.failUnless(len(isoImage.entries.keys()) > 0 and len(isoImage.entries.keys()) < 6)
   
   def testPruneImage_004(self):
      """
      Attempt to prune a non-empty image using a capacity for which no entries
      will fit.

      This is one of those tests that may be fairly sensitive to specific
      mkisofs versions, but I don't know for sure.  A pretty-much empty image
      has around 381860 bytes of overhead.  I think if I use this for my
      capacity, that no files will fit and I'll throw an IOError because of
      that.  However, there's always the chance that the IOError is because not
      even the ISO header will fit, and we won't be able to differentiate those
      two cases.

      It's also important that the entries dictionary not be changed when an
      exception is thrown!
      """
      self.extractTar("tree9")
      dir1 = self.buildPath([ "tree9", ])
      isoImage = IsoImage()
      isoImage.addEntry(dir1, None)
      self.failUnlessEqual({ dir1:None, }, isoImage.entries)
      self.failUnlessRaises(IOError, isoImage.pruneImage, 381860)  # from experimentation
   
   def testPruneImage_005(self):
      """
      Attempt to prune a non-empty image using a capacity for which not even
      the overhead will fit.

      This is one of those tests that may be fairly sensitive to specific
      mkisofs versions, but I don't know for sure.  A pretty-much empty image
      has around 381860 bytes of overhead.  I'm assuming that if I use a really
      small size (say, 10000 bytes) that I'll always get an IOError when even
      the overhead won't fit.

      It's also important that the entries dictionary not be changed when an
      exception is thrown!
      """
      self.extractTar("tree9")
      dir1 = self.buildPath([ "tree9", ])
      isoImage = IsoImage()
      isoImage.addEntry(dir1, "b")
      self.failUnlessEqual({ dir1:"b/tree9", }, isoImage.entries)
      self.failUnlessRaises(IOError, isoImage.pruneImage, 10000)  # from experimentation
      self.failUnlessEqual({ dir1:"b/tree9", }, isoImage.entries)
   

   ####################
   # Test writeImage()
   ####################

   def testWriteImage_001(self):
      """
      Attempt to write an image containing no entries.
      """
      isoImage = IsoImage()
      imagePath = self.buildPath([ "image.iso", ])
      self.failUnlessRaises(ValueError, isoImage.writeImage, imagePath)

   def testWriteImage_002(self):
      """
      Attempt to write an image containing only an empty directory, no graft point.
      """
      self.extractTar("tree9")
      isoImage = IsoImage()
      dir1 = self.buildPath([ "tree9", "dir001", "dir002", ])
      imagePath = self.buildPath([ "image.iso", ])
      isoImage.addEntry(dir1)
      isoImage.writeImage(imagePath)
      mountPath = self.mountImage(imagePath)
      self.unmountImage()

   def testWriteImage_003(self):
      """
      Attempt to write an image containing only an empty directory, with a graft point.
      """
      self.extractTar("tree9")
      isoImage = IsoImage()
      dir1 = self.buildPath([ "tree9", "dir001", "dir002", ])
      imagePath = self.buildPath([ "image.iso", ])
      isoImage.addEntry(dir1, graftPoint="base")
      isoImage.writeImage(imagePath)
      mountPath = self.mountImage(imagePath)
      self.unmountImage()

   def testWriteImage_004(self):
      """
      Attempt to write an image containing only a non-empty directory, no graft
      point.
      """
      self.extractTar("tree9")
      isoImage = IsoImage()
      dir1 = self.buildPath([ "tree9", "dir002" ])
      imagePath = self.buildPath([ "image.iso", ])
      isoImage.addEntry(dir1)
      isoImage.writeImage(imagePath)
      mountPath = self.mountImage(imagePath)
      self.unmountImage()

   def testWriteImage_005(self):
      """
      Attempt to write an image containing only a non-empty directory, with a
      graft point.
      """
      self.extractTar("tree9")
      isoImage = IsoImage()
      dir1 = self.buildPath([ "tree9", "dir002" ])
      imagePath = self.buildPath([ "image.iso", ])
      isoImage.addEntry(dir1, graftPoint=os.path.join("something", "else"))
      isoImage.writeImage(imagePath)
      mountPath = self.mountImage(imagePath)
      self.unmountImage()

   def testWriteImage_006(self):
      """
      Attempt to write an image containing only a file, no graft point.
      """
      self.extractTar("tree9")
      isoImage = IsoImage()
      file1 = self.buildPath([ "tree9", "file001" ])
      imagePath = self.buildPath([ "image.iso", ])
      isoImage.addEntry(file1)
      isoImage.writeImage(imagePath)
      mountPath = self.mountImage(imagePath)
      self.unmountImage()

   def testWriteImage_007(self):
      """
      Attempt to write an image containing only a file, with a graft point.
      """
      self.extractTar("tree9")
      isoImage = IsoImage()
      file1 = self.buildPath([ "tree9", "file001" ])
      imagePath = self.buildPath([ "image.iso", ])
      isoImage.addEntry(file1, graftPoint="point")
      isoImage.writeImage(imagePath)
      mountPath = self.mountImage(imagePath)
      self.unmountImage()

   def testWriteImage_008(self):
      """
      Attempt to write an image containing a file and an empty directory, no
      graft points.
      """
      self.extractTar("tree9")
      isoImage = IsoImage()
      file1 = self.buildPath([ "tree9", "file001" ])
      dir1 = self.buildPath([ "tree9", "dir001", "dir002", ])
      imagePath = self.buildPath([ "image.iso", ])
      isoImage.addEntry(file1)
      isoImage.addEntry(dir1)
      isoImage.writeImage(imagePath)
      mountPath = self.mountImage(imagePath)
      self.unmountImage()

   def testWriteImage_009(self):
      """
      Attempt to write an image containing a file and an empty directory, with
      graft points.
      """
      self.extractTar("tree9")
      isoImage = IsoImage(graftPoint="base")
      file1 = self.buildPath([ "tree9", "file001" ])
      dir1 = self.buildPath([ "tree9", "dir001", "dir002", ])
      imagePath = self.buildPath([ "image.iso", ])
      isoImage.addEntry(file1, graftPoint="other")
      isoImage.addEntry(dir1)
      isoImage.writeImage(imagePath)
      mountPath = self.mountImage(imagePath)
      self.unmountImage()

   def testWriteImage_010(self):
      """
      Attempt to write an image containing a file and a non-empty directory,
      mixed graft points.
      """
      self.extractTar("tree9")
      isoImage = IsoImage(graftPoint="base")
      file1 = self.buildPath([ "tree9", "file001" ])
      dir1 = self.buildPath([ "tree9", "dir001", ])
      imagePath = self.buildPath([ "image.iso", ])
      isoImage.addEntry(file1, graftPoint=None)
      isoImage.addEntry(dir1)
      isoImage.writeImage(imagePath)
      mountPath = self.mountImage(imagePath)
      self.unmountImage()

   def testWriteImage_011(self):
      """
      Attempt to write an image containing several files and a non-empty
      directory, mixed graft points.
      """
      self.extractTar("tree9")
      isoImage = IsoImage(graftPoint="base")
      file1 = self.buildPath([ "tree9", "file001" ])
      file2 = self.buildPath([ "tree9", "file002" ])
      dir1 = self.buildPath([ "tree9", "dir001", ])
      imagePath = self.buildPath([ "image.iso", ])
      isoImage.addEntry(file1, graftPoint=None)
      isoImage.addEntry(file2, graftPoint="other")
      isoImage.addEntry(dir1)
      isoImage.writeImage(imagePath)
      mountPath = self.mountImage(imagePath)
      self.unmountImage()

   def testWriteImage_012(self):
      """
      Attempt to write an image which has been pruned, containing several files
      and a non-empty directory, mixed graft points.
      """
      self.extractTar("tree9")
      isoImage = IsoImage(graftPoint="base")
      file1 = self.buildPath([ "tree9", "file001" ])
      file2 = self.buildPath([ "tree9", "file002" ])
      dir1 = self.buildPath([ "tree9", "dir001", ])
      dir2 = self.buildPath([ "tree9", "dir002", ])
      imagePath = self.buildPath([ "image.iso", ])
      isoImage.addEntry(file1, graftPoint=None)
      isoImage.addEntry(file2)
      isoImage.addEntry(dir1)
      isoImage.addEntry(dir2, graftPoint="other")
      isoImage.pruneImage(getBytes(650))
      isoImage.writeImage(imagePath)
      mountPath = self.mountImage(imagePath)
      self.unmountImage()


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

