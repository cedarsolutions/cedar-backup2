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
# Purpose  : Tests configuration functionality.
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# This file was created with a width of 132 characters, and NO tabs.

########################################################################
# Module documentation
########################################################################

"""
Unit tests for CedarBackup2/config.py.

Code Coverage
=============

   This module contains individual tests for the public functions and classes
   implemented in config.py.  

   I usually prefer to test only the public interface to a class, because that
   way the regression tests don't depend on the internal implementation.  In
   this case, I've decided to test some of the private methods, because their
   "privateness" is more a matter of presenting a clean external interface than
   anything else.  In particular, this is the case with the private validation
   functions (I use the private functions so I can test just the validations
   for one specific case, even if the public interface only exposes one broad
   validation).

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

Testing XML Extraction
======================

   It's difficult to validated that generated XML is exactly "right",
   especially when dealing with pretty-printed XML.  We can't just provide a
   constant string and say "the result must match this".  Instead, what we do
   is extract the XML and then feed it back into another object's constructor.
   If that parse process succeeds and the old object is equal to the new
   object, we assume that the extract was successful.  

   It would argumably be better if we could do a completely independent check -
   but implementing that check would be equivalent to re-implementing all of
   the existing functionality that we're validating here!  After all, the most
   important thing is that data can move seamlessly from object to XML document
   and back to object.

Full vs. Reduced Tests
======================

   All of the tests in this module are considered safe to be run in an average
   build environment.  There is a no need to use a CONFIGTESTS_FULL environment
   variable to provide a "reduced feature set" test suite as for some of the
   other test modules.

@author Kenneth J. Pronovici <pronovic@ieee.org>
"""


########################################################################
# Import modules and do runtime validations
########################################################################

import os
import unittest
import tempfile
from CedarBackup2.testutil import findResources, buildPath, removedir, failUnlessAssignRaises
from CedarBackup2.config import CollectDir, PurgeDir, LocalPeer, RemotePeer
from CedarBackup2.config import ReferenceConfig, OptionsConfig, CollectConfig
from CedarBackup2.config import StageConfig, StoreConfig, PurgeConfig, Config


#######################################################################
# Module-wide configuration and constants
#######################################################################

DATA_DIRS = [ "./data", "./test/data", ]
RESOURCES = [ "cback.conf.1", "cback.conf.2", "cback.conf.3", "cback.conf.4", "cback.conf.5", 
              "cback.conf.6", "cback.conf.7", "cback.conf.8", "cback.conf.9", "cback.conf.10", 
              "cback.conf.11", "cback.conf.12", "cback.conf.13", "cback.conf.14", "cback.conf.15", ]


#######################################################################
# Test Case Classes
#######################################################################

#######################
# TestCollectDir class
#######################

class TestCollectDir(unittest.TestCase):

   """Tests for the CollectDir class."""

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

   def buildPath(self, components):
      """Builds a complete search path from a list of components."""
      components.insert(0, self.tmpdir)
      return buildPath(components)

   def failUnlessAssignRaises(self, exception, object, property, value):
      """Equivalent of L{failUnlessRaises}, but used for property assignments instead."""
      failUnlessAssignRaises(self, exception, object, property, value)


   ############################
   # Test __repr__ and __str__
   ############################

   def testStringFuncs_001(self):
      """
      Just make sure that the string functions don't have errors (i.e. bad variable names).
      """
      obj = CollectDir()
      obj.__repr__()
      obj.__str__()


   ##################################
   # Test constructor and attributes
   ##################################

   def testConstructor_001(self):
      """
      Test constructor with no values filled in.
      """
      collectDir = CollectDir()
      self.failUnlessEqual(None, collectDir.absolutePath)
      self.failUnlessEqual(None, collectDir.collectMode)
      self.failUnlessEqual(None, collectDir.archiveMode)
      self.failUnlessEqual(None, collectDir.ignoreFile)
      self.failUnlessEqual(None, collectDir.absoluteExcludePaths)
      self.failUnlessEqual(None, collectDir.relativeExcludePaths)
      self.failUnlessEqual(None, collectDir.excludePatterns)

   def testConstructor_002(self):
      """
      Test constructor with all values filled in, with valid values.
      """
      collectDir = CollectDir("/etc/whatever", "incr", "tar", ".ignore", [], [], [])
      self.failUnlessEqual("/etc/whatever", collectDir.absolutePath)
      self.failUnlessEqual("incr", collectDir.collectMode)
      self.failUnlessEqual("tar", collectDir.archiveMode)
      self.failUnlessEqual(".ignore", collectDir.ignoreFile)
      self.failUnlessEqual([], collectDir.absoluteExcludePaths)
      self.failUnlessEqual([], collectDir.relativeExcludePaths)
      self.failUnlessEqual([], collectDir.excludePatterns)

   def testConstructor_003(self):
      """
      Test assignment of absolutePath attribute, None value.
      """
      collectDir = CollectDir(absolutePath="/whatever")
      self.failUnlessEqual("/whatever", collectDir.absolutePath)
      collectDir.absolutePath = None
      self.failUnlessEqual(None, collectDir.absolutePath)

   def testConstructor_004(self):
      """
      Test assignment of absolutePath attribute, valid value.
      """
      collectDir = CollectDir()
      self.failUnlessEqual(None, collectDir.absolutePath)
      collectDir.absolutePath = "/etc/whatever"
      self.failUnlessEqual("/etc/whatever", collectDir.absolutePath)

   def testConstructor_005(self):
      """
      Test assignment of absolutePath attribute, invalid value (empty).
      """
      collectDir = CollectDir()
      self.failUnlessEqual(None, collectDir.absolutePath)
      self.failUnlessAssignRaises(ValueError, collectDir, "absolutePath", "")
      self.failUnlessEqual(None, collectDir.absolutePath)

   def testConstructor_006(self):
      """
      Test assignment of absolutePath attribute, invalid value (non-absolute).
      """
      collectDir = CollectDir()
      self.failUnlessEqual(None, collectDir.absolutePath)
      self.failUnlessAssignRaises(ValueError, collectDir, "absolutePath", "whatever")
      self.failUnlessEqual(None, collectDir.absolutePath)

   def testConstructor_007(self):
      """
      Test assignment of collectMode attribute, None value.
      """
      collectDir = CollectDir(collectMode="incr")
      self.failUnlessEqual("incr", collectDir.collectMode)
      collectDir.collectMode = None
      self.failUnlessEqual(None, collectDir.collectMode)

   def testConstructor_008(self):
      """
      Test assignment of collectMode attribute, valid value.
      """
      collectDir = CollectDir()
      self.failUnlessEqual(None, collectDir.collectMode)
      collectDir.collectMode = "daily"
      self.failUnlessEqual("daily", collectDir.collectMode)
      collectDir.collectMode = "weekly"
      self.failUnlessEqual("weekly", collectDir.collectMode)
      collectDir.collectMode = "incr"
      self.failUnlessEqual("incr", collectDir.collectMode)

   def testConstructor_009(self):
      """
      Test assignment of collectMode attribute, invalid value (empty).
      """
      collectDir = CollectDir()
      self.failUnlessEqual(None, collectDir.collectMode)
      self.failUnlessAssignRaises(ValueError, collectDir, "collectMode", "")
      self.failUnlessEqual(None, collectDir.collectMode)

   def testConstructor_010(self):
      """
      Test assignment of collectMode attribute, invalid value (not in list).
      """
      collectDir = CollectDir()
      self.failUnlessEqual(None, collectDir.collectMode)
      self.failUnlessAssignRaises(ValueError, collectDir, "collectMode", "bogus")
      self.failUnlessEqual(None, collectDir.collectMode)

   def testConstructor_011(self):
      """
      Test assignment of archiveMode attribute, None value.
      """
      collectDir = CollectDir(archiveMode="tar")
      self.failUnlessEqual("tar", collectDir.archiveMode)
      collectDir.archiveMode = None
      self.failUnlessEqual(None, collectDir.archiveMode)

   def testConstructor_012(self):
      """
      Test assignment of archiveMode attribute, valid value.
      """
      collectDir = CollectDir()
      self.failUnlessEqual(None, collectDir.archiveMode)
      collectDir.archiveMode = "tar"
      self.failUnlessEqual("tar", collectDir.archiveMode)
      collectDir.archiveMode = "targz"
      self.failUnlessEqual("targz", collectDir.archiveMode)
      collectDir.archiveMode = "tarbz2"
      self.failUnlessEqual("tarbz2", collectDir.archiveMode)

   def testConstructor_013(self):
      """
      Test assignment of archiveMode attribute, invalid value (empty).
      """
      collectDir = CollectDir()
      self.failUnlessEqual(None, collectDir.archiveMode)
      self.failUnlessAssignRaises(ValueError, collectDir, "archiveMode", "")
      self.failUnlessEqual(None, collectDir.archiveMode)

   def testConstructor_014(self):
      """
      Test assignment of archiveMode attribute, invalid value (not in list).
      """
      collectDir = CollectDir()
      self.failUnlessEqual(None, collectDir.archiveMode)
      self.failUnlessAssignRaises(ValueError, collectDir, "archiveMode", "bogus")
      self.failUnlessEqual(None, collectDir.archiveMode)

   def testConstructor_015(self):
      """
      Test assignment of ignoreFile attribute, None value.
      """
      collectDir = CollectDir(ignoreFile="ignore")
      self.failUnlessEqual("ignore", collectDir.ignoreFile)
      collectDir.ignoreFile = None
      self.failUnlessEqual(None, collectDir.ignoreFile)

   def testConstructor_016(self):
      """
      Test assignment of ignoreFile attribute, valid value.
      """
      collectDir = CollectDir()
      self.failUnlessEqual(None, collectDir.ignoreFile)
      collectDir.ignoreFile = "ignorefile"
      self.failUnlessEqual("ignorefile", collectDir.ignoreFile)

   def testConstructor_017(self):
      """
      Test assignment of ignoreFile attribute, invalid value (empty).
      """
      collectDir = CollectDir()
      self.failUnlessEqual(None, collectDir.ignoreFile)
      self.failUnlessAssignRaises(ValueError, collectDir, "ignoreFile", "")
      self.failUnlessEqual(None, collectDir.ignoreFile)

   def testConstructor_018(self):
      """
      Test assignment of absoluteExcludePaths attribute, None value.
      """
      collectDir = CollectDir(absoluteExcludePaths=[])
      self.failUnlessEqual([], collectDir.absoluteExcludePaths)
      collectDir.absoluteExcludePaths = None
      self.failUnlessEqual(None, collectDir.absoluteExcludePaths)

   def testConstructor_019(self):
      """
      Test assignment of absoluteExcludePaths attribute, [] value.
      """
      collectDir = CollectDir()
      self.failUnlessEqual(None, collectDir.absoluteExcludePaths)
      collectDir.absoluteExcludePaths = []
      self.failUnlessEqual([], collectDir.absoluteExcludePaths)

   def testConstructor_020(self):
      """
      Test assignment of absoluteExcludePaths attribute, single valid entry.
      """
      collectDir = CollectDir()
      self.failUnlessEqual(None, collectDir.absoluteExcludePaths)
      collectDir.absoluteExcludePaths = ["/whatever", ]
      self.failUnlessEqual(["/whatever", ], collectDir.absoluteExcludePaths)
      collectDir.absoluteExcludePaths.append("/stuff")
      self.failUnlessEqual(["/whatever", "/stuff", ], collectDir.absoluteExcludePaths)

   def testConstructor_021(self):
      """
      Test assignment of absoluteExcludePaths attribute, multiple valid
      entries.
      """
      collectDir = CollectDir()
      self.failUnlessEqual(None, collectDir.absoluteExcludePaths)
      collectDir.absoluteExcludePaths = ["/whatever", "/stuff", ]
      self.failUnlessEqual(["/whatever", "/stuff", ], collectDir.absoluteExcludePaths)
      collectDir.absoluteExcludePaths.append("/etc/X11")
      self.failUnlessEqual(["/whatever", "/stuff", "/etc/X11", ], collectDir.absoluteExcludePaths)

   def testConstructor_022(self):
      """
      Test assignment of absoluteExcludePaths attribute, single invalid entry
      (empty).
      """
      collectDir = CollectDir()
      self.failUnlessEqual(None, collectDir.absoluteExcludePaths)
      self.failUnlessAssignRaises(ValueError, collectDir, "absoluteExcludePaths", ["", ])
      self.failUnlessEqual(None, collectDir.absoluteExcludePaths)

   def testConstructor_023(self):
      """
      Test assignment of absoluteExcludePaths attribute, single invalid entry
      (not absolute).
      """
      collectDir = CollectDir()
      self.failUnlessEqual(None, collectDir.absoluteExcludePaths)
      self.failUnlessAssignRaises(ValueError, collectDir, "absoluteExcludePaths", ["notabsolute", ])
      self.failUnlessEqual(None, collectDir.absoluteExcludePaths)

   def testConstructor_024(self):
      """
      Test assignment of absoluteExcludePaths attribute, mixed valid and
      invalid entries.
      """
      collectDir = CollectDir()
      self.failUnlessEqual(None, collectDir.absoluteExcludePaths)
      self.failUnlessAssignRaises(ValueError, collectDir, "absoluteExcludePaths", ["/good", "bad", "/alsogood", ])
      self.failUnlessEqual(None, collectDir.absoluteExcludePaths)

   def testConstructor_025(self):
      """
      Test assignment of relativeExcludePaths attribute, None value.
      """
      collectDir = CollectDir(relativeExcludePaths=[])
      self.failUnlessEqual([], collectDir.relativeExcludePaths)
      collectDir.relativeExcludePaths = None
      self.failUnlessEqual(None, collectDir.relativeExcludePaths)

   def testConstructor_026(self):
      """
      Test assignment of relativeExcludePaths attribute, [] value.
      """
      collectDir = CollectDir()
      self.failUnlessEqual(None, collectDir.relativeExcludePaths)
      collectDir.relativeExcludePaths = []
      self.failUnlessEqual([], collectDir.relativeExcludePaths)

   def testConstructor_027(self):
      """
      Test assignment of relativeExcludePaths attribute, single valid entry.
      """
      collectDir = CollectDir()
      self.failUnlessEqual(None, collectDir.relativeExcludePaths)
      collectDir.relativeExcludePaths = ["stuff", ]
      self.failUnlessEqual(["stuff", ], collectDir.relativeExcludePaths)
      collectDir.relativeExcludePaths.insert(0, "bogus")
      self.failUnlessEqual(["bogus", "stuff", ], collectDir.relativeExcludePaths)

   def testConstructor_028(self):
      """
      Test assignment of relativeExcludePaths attribute, multiple valid
      entries.
      """
      collectDir = CollectDir()
      self.failUnlessEqual(None, collectDir.relativeExcludePaths)
      collectDir.relativeExcludePaths = ["bogus", "stuff", ]
      self.failUnlessEqual(["bogus", "stuff", ], collectDir.relativeExcludePaths)
      collectDir.relativeExcludePaths.append("more")
      self.failUnlessEqual(["bogus", "stuff", "more", ], collectDir.relativeExcludePaths)

   def testConstructor_029(self):
      """
      Test assignment of excludePatterns attribute, None value.
      """
      collectDir = CollectDir(excludePatterns=[])
      self.failUnlessEqual([], collectDir.excludePatterns)
      collectDir.excludePatterns = None
      self.failUnlessEqual(None, collectDir.excludePatterns)

   def testConstructor_030(self):
      """
      Test assignment of excludePatterns attribute, [] value.
      """
      collectDir = CollectDir()
      self.failUnlessEqual(None, collectDir.excludePatterns)
      collectDir.excludePatterns = []
      self.failUnlessEqual([], collectDir.excludePatterns)

   def testConstructor_031(self):
      """
      Test assignment of excludePatterns attribute, single valid entry.
      """
      collectDir = CollectDir()
      self.failUnlessEqual(None, collectDir.excludePatterns)
      collectDir.excludePatterns = ["valid", ]
      self.failUnlessEqual(["valid", ], collectDir.excludePatterns)
      collectDir.excludePatterns.append("more")
      self.failUnlessEqual(["valid", "more", ], collectDir.excludePatterns)

   def testConstructor_032(self):
      """
      Test assignment of excludePatterns attribute, multiple valid entries.
      """
      collectDir = CollectDir()
      self.failUnlessEqual(None, collectDir.excludePatterns)
      collectDir.excludePatterns = ["valid", "more", ]
      self.failUnlessEqual(["valid", "more", ], collectDir.excludePatterns)
      collectDir.excludePatterns.insert(1, "bogus")
      self.failUnlessEqual(["valid", "bogus", "more", ], collectDir.excludePatterns)


   ############################
   # Test comparison operators
   ############################

   def testComparison_001(self):
      """
      Test comparison of two identical objects, all attributes None.
      """
      collectDir1 = CollectDir()
      collectDir2 = CollectDir()
      self.failUnlessEqual(collectDir1, collectDir2)
      self.failUnless(collectDir1 == collectDir2)
      self.failUnless(not collectDir1 < collectDir2)
      self.failUnless(collectDir1 <= collectDir2)
      self.failUnless(not collectDir1 > collectDir2)
      self.failUnless(collectDir1 >= collectDir2)
      self.failUnless(not collectDir1 != collectDir2)

   def testComparison_002(self):
      """
      Test comparison of two identical objects, all attributes non-None (empty
      lists).
      """
      collectDir1 = CollectDir("/etc/whatever", "incr", "tar", ".ignore", [], [], [])
      collectDir2 = CollectDir("/etc/whatever", "incr", "tar", ".ignore", [], [], [])
      self.failUnless(collectDir1 == collectDir2)
      self.failUnless(not collectDir1 < collectDir2)
      self.failUnless(collectDir1 <= collectDir2)
      self.failUnless(not collectDir1 > collectDir2)
      self.failUnless(collectDir1 >= collectDir2)
      self.failUnless(not collectDir1 != collectDir2)

   def testComparison_003(self):
      """
      Test comparison of two identical objects, all attributes non-None
      (non-empty lists).
      """
      collectDir1 = CollectDir("/etc/whatever", "incr", "tar", ".ignore", ["/one",], ["two",], ["three",])
      collectDir2 = CollectDir("/etc/whatever", "incr", "tar", ".ignore", ["/one",], ["two",], ["three",])
      self.failUnless(collectDir1 == collectDir2)
      self.failUnless(not collectDir1 < collectDir2)
      self.failUnless(collectDir1 <= collectDir2)
      self.failUnless(not collectDir1 > collectDir2)
      self.failUnless(collectDir1 >= collectDir2)
      self.failUnless(not collectDir1 != collectDir2)

   def testComparison_004(self):
      """
      Test comparison of two differing objects, absolutePath differs (one None).
      """
      collectDir1 = CollectDir()
      collectDir2 = CollectDir(absolutePath="/whatever")
      self.failIfEqual(collectDir1, collectDir2)
      self.failUnless(not collectDir1 == collectDir2)
      self.failUnless(collectDir1 < collectDir2)
      self.failUnless(collectDir1 <= collectDir2)
      self.failUnless(not collectDir1 > collectDir2)
      self.failUnless(not collectDir1 >= collectDir2)
      self.failUnless(collectDir1 != collectDir2)

   def testComparison_005(self):
      """
      Test comparison of two differing objects, absolutePath differs.
      """
      collectDir1 = CollectDir("/etc/whatever", "incr", "tar", ".ignore", [], [], [])
      collectDir2 = CollectDir("/stuff", "incr", "tar", ".ignore", [], [], [])
      self.failIfEqual(collectDir1, collectDir2)
      self.failUnless(not collectDir1 == collectDir2)
      self.failUnless(collectDir1 < collectDir2)
      self.failUnless(collectDir1 <= collectDir2)
      self.failUnless(not collectDir1 > collectDir2)
      self.failUnless(not collectDir1 >= collectDir2)
      self.failUnless(collectDir1 != collectDir2)

   def testComparison_006(self):
      """
      Test comparison of two differing objects, collectMode differs (one None).
      """
      collectDir1 = CollectDir()
      collectDir2 = CollectDir(collectMode="incr")
      self.failIfEqual(collectDir1, collectDir2)
      self.failUnless(not collectDir1 == collectDir2)
      self.failUnless(collectDir1 < collectDir2)
      self.failUnless(collectDir1 <= collectDir2)
      self.failUnless(not collectDir1 > collectDir2)
      self.failUnless(not collectDir1 >= collectDir2)
      self.failUnless(collectDir1 != collectDir2)

   def testComparison_007(self):
      """
      Test comparison of two differing objects, collectMode differs.
      """
      collectDir1 = CollectDir("/etc/whatever", "incr", "tar", ".ignore", [], [], [])
      collectDir2 = CollectDir("/etc/whatever", "daily", "tar", ".ignore", [], [], [])
      self.failIfEqual(collectDir1, collectDir2)
      self.failUnless(not collectDir1 == collectDir2)
      self.failUnless(not collectDir1 < collectDir2)
      self.failUnless(not collectDir1 <= collectDir2)
      self.failUnless(collectDir1 > collectDir2)
      self.failUnless(collectDir1 >= collectDir2)
      self.failUnless(collectDir1 != collectDir2)

   def testComparison_008(self):
      """
      Test comparison of two differing objects, archiveMode differs (one None).
      """
      collectDir1 = CollectDir()
      collectDir2 = CollectDir(archiveMode="tar")
      self.failIfEqual(collectDir1, collectDir2)
      self.failUnless(not collectDir1 == collectDir2)
      self.failUnless(collectDir1 < collectDir2)
      self.failUnless(collectDir1 <= collectDir2)
      self.failUnless(not collectDir1 > collectDir2)
      self.failUnless(not collectDir1 >= collectDir2)
      self.failUnless(collectDir1 != collectDir2)

   def testComparison_009(self):
      """
      Test comparison of two differing objects, archiveMode differs.
      """
      collectDir1 = CollectDir("/etc/whatever", "incr", "targz", ".ignore", [], [], [])
      collectDir2 = CollectDir("/etc/whatever", "incr", "tar", ".ignore", [], [], [])
      self.failIfEqual(collectDir1, collectDir2)
      self.failUnless(not collectDir1 == collectDir2)
      self.failUnless(not collectDir1 < collectDir2)
      self.failUnless(not collectDir1 <= collectDir2)
      self.failUnless(collectDir1 > collectDir2)
      self.failUnless(collectDir1 >= collectDir2)
      self.failUnless(collectDir1 != collectDir2)

   def testComparison_010(self):
      """
      Test comparison of two differing objects, ignoreFile differs (one None).
      """
      collectDir1 = CollectDir()
      collectDir2 = CollectDir(ignoreFile="ignore")
      self.failIfEqual(collectDir1, collectDir2)
      self.failUnless(not collectDir1 == collectDir2)
      self.failUnless(collectDir1 < collectDir2)
      self.failUnless(collectDir1 <= collectDir2)
      self.failUnless(not collectDir1 > collectDir2)
      self.failUnless(not collectDir1 >= collectDir2)
      self.failUnless(collectDir1 != collectDir2)

   def testComparison_011(self):
      """
      Test comparison of two differing objects, ignoreFile differs.
      """
      collectDir1 = CollectDir("/etc/whatever", "incr", "tar", "ignore", [], [], [])
      collectDir2 = CollectDir("/etc/whatever", "incr", "tar", ".ignore", [], [], [])
      self.failIfEqual(collectDir1, collectDir2)
      self.failUnless(not collectDir1 == collectDir2)
      self.failUnless(not collectDir1 < collectDir2)
      self.failUnless(not collectDir1 <= collectDir2)
      self.failUnless(collectDir1 > collectDir2)
      self.failUnless(collectDir1 >= collectDir2)
      self.failUnless(collectDir1 != collectDir2)

   def testComparison_012(self):
      """
      Test comparison of two differing objects, absoluteExcludePaths differs
      (one None, one empty).
      """
      collectDir1 = CollectDir()
      collectDir2 = CollectDir(absoluteExcludePaths=[])
      self.failIfEqual(collectDir1, collectDir2)
      self.failUnless(not collectDir1 == collectDir2)
      self.failUnless(collectDir1 < collectDir2)
      self.failUnless(collectDir1 <= collectDir2)
      self.failUnless(not collectDir1 > collectDir2)
      self.failUnless(not collectDir1 >= collectDir2)
      self.failUnless(collectDir1 != collectDir2)

   def testComparison_013(self):
      """
      Test comparison of two differing objects, absoluteExcludePaths differs
      (one None, one not empty).
      """
      collectDir1 = CollectDir()
      collectDir2 = CollectDir(absoluteExcludePaths=["/whatever",])
      self.failIfEqual(collectDir1, collectDir2)
      self.failUnless(not collectDir1 == collectDir2)
      self.failUnless(collectDir1 < collectDir2)
      self.failUnless(collectDir1 <= collectDir2)
      self.failUnless(not collectDir1 > collectDir2)
      self.failUnless(not collectDir1 >= collectDir2)
      self.failUnless(collectDir1 != collectDir2)

   def testComparison_014(self):
      """
      Test comparison of two differing objects, absoluteExcludePaths differs
      (one empty, one not empty).
      """
      collectDir1 = CollectDir("/etc/whatever", "incr", "tar", ".ignore", [], [], [])
      collectDir2 = CollectDir("/etc/whatever", "incr", "tar", ".ignore", ["/whatever", ], [], [])
      self.failIfEqual(collectDir1, collectDir2)
      self.failUnless(not collectDir1 == collectDir2)
      self.failUnless(collectDir1 < collectDir2)
      self.failUnless(collectDir1 <= collectDir2)
      self.failUnless(not collectDir1 > collectDir2)
      self.failUnless(not collectDir1 >= collectDir2)
      self.failUnless(collectDir1 != collectDir2)

   def testComparison_015(self):
      """
      Test comparison of two differing objects, absoluteExcludePaths differs
      (both not empty).
      """
      collectDir1 = CollectDir("/etc/whatever", "incr", "tar", ".ignore", ["/stuff", ], [], [])
      collectDir2 = CollectDir("/etc/whatever", "incr", "tar", ".ignore", ["/stuff", "/something", ], [], [])
      self.failIfEqual(collectDir1, collectDir2)
      self.failUnless(not collectDir1 == collectDir2)
      self.failUnless(not collectDir1 < collectDir2)     # note: different than standard due to unsorted list
      self.failUnless(not collectDir1 <= collectDir2)    # note: different than standard due to unsorted list
      self.failUnless(collectDir1 > collectDir2)         # note: different than standard due to unsorted list
      self.failUnless(collectDir1 >= collectDir2)        # note: different than standard due to unsorted list
      self.failUnless(collectDir1 != collectDir2)

   def testComparison_016(self):
      """
      Test comparison of two differing objects, relativeExcludePaths differs
      (one None, one empty).
      """
      collectDir1 = CollectDir()
      collectDir2 = CollectDir(relativeExcludePaths=[])
      self.failIfEqual(collectDir1, collectDir2)
      self.failUnless(not collectDir1 == collectDir2)
      self.failUnless(collectDir1 < collectDir2)
      self.failUnless(collectDir1 <= collectDir2)
      self.failUnless(not collectDir1 > collectDir2)
      self.failUnless(not collectDir1 >= collectDir2)
      self.failUnless(collectDir1 != collectDir2)

   def testComparison_017(self):
      """
      Test comparison of two differing objects, relativeExcludePaths differs
      (one None, one not empty).
      """
      collectDir1 = CollectDir()
      collectDir2 = CollectDir(relativeExcludePaths=["stuff", "other", ])
      self.failIfEqual(collectDir1, collectDir2)
      self.failUnless(not collectDir1 == collectDir2)
      self.failUnless(collectDir1 < collectDir2)
      self.failUnless(collectDir1 <= collectDir2)
      self.failUnless(not collectDir1 > collectDir2)
      self.failUnless(not collectDir1 >= collectDir2)
      self.failUnless(collectDir1 != collectDir2)

   def testComparison_018(self):
      """
      Test comparison of two differing objects, relativeExcludePaths differs
      (one empty, one not empty).
      """
      collectDir1 = CollectDir("/etc/whatever", "incr", "tar", ".ignore", [], ["one", ], [])
      collectDir2 = CollectDir("/etc/whatever", "incr", "tar", ".ignore", [], [], [])
      self.failIfEqual(collectDir1, collectDir2)
      self.failUnless(not collectDir1 == collectDir2)
      self.failUnless(not collectDir1 < collectDir2)
      self.failUnless(not collectDir1 <= collectDir2)
      self.failUnless(collectDir1 > collectDir2)
      self.failUnless(collectDir1 >= collectDir2)
      self.failUnless(collectDir1 != collectDir2)

   def testComparison_019(self):
      """
      Test comparison of two differing objects, relativeExcludePaths differs
      (both not empty).
      """
      collectDir1 = CollectDir("/etc/whatever", "incr", "tar", ".ignore", [], ["one", ], [])
      collectDir2 = CollectDir("/etc/whatever", "incr", "tar", ".ignore", [], ["two", ], [])
      self.failIfEqual(collectDir1, collectDir2)
      self.failUnless(not collectDir1 == collectDir2)
      self.failUnless(collectDir1 < collectDir2)
      self.failUnless(collectDir1 <= collectDir2)
      self.failUnless(not collectDir1 > collectDir2)
      self.failUnless(not collectDir1 >= collectDir2)
      self.failUnless(collectDir1 != collectDir2)

   def testComparison_020(self):
      """
      Test comparison of two differing objects, excludePatterns differs (one
      None, one empty).
      """
      collectDir1 = CollectDir()
      collectDir2 = CollectDir(excludePatterns=[])
      self.failIfEqual(collectDir1, collectDir2)
      self.failUnless(not collectDir1 == collectDir2)
      self.failUnless(collectDir1 < collectDir2)
      self.failUnless(collectDir1 <= collectDir2)
      self.failUnless(not collectDir1 > collectDir2)
      self.failUnless(not collectDir1 >= collectDir2)
      self.failUnless(collectDir1 != collectDir2)

   def testComparison_021(self):
      """
      Test comparison of two differing objects, excludePatterns differs (one
      None, one not empty).
      """
      collectDir1 = CollectDir()
      collectDir2 = CollectDir(excludePatterns=["one", "two", "three", ])
      self.failIfEqual(collectDir1, collectDir2)
      self.failUnless(not collectDir1 == collectDir2)
      self.failUnless(collectDir1 < collectDir2)
      self.failUnless(collectDir1 <= collectDir2)
      self.failUnless(not collectDir1 > collectDir2)
      self.failUnless(not collectDir1 >= collectDir2)
      self.failUnless(collectDir1 != collectDir2)

   def testComparison_022(self):
      """
      Test comparison of two differing objects, excludePatterns differs (one
      empty, one not empty).
      """
      collectDir1 = CollectDir("/etc/whatever", "incr", "tar", ".ignore", [], [], [])
      collectDir2 = CollectDir("/etc/whatever", "incr", "tar", ".ignore", [], [], ["pattern", ])
      self.failIfEqual(collectDir1, collectDir2)
      self.failUnless(not collectDir1 == collectDir2)
      self.failUnless(collectDir1 < collectDir2)
      self.failUnless(collectDir1 <= collectDir2)
      self.failUnless(not collectDir1 > collectDir2)
      self.failUnless(not collectDir1 >= collectDir2)
      self.failUnless(collectDir1 != collectDir2)

   def testComparison_023(self):
      """
      Test comparison of two differing objects, excludePatterns differs (both
      not empty).
      """
      collectDir1 = CollectDir("/etc/whatever", "incr", "tar", ".ignore", [], [], ["p1", ])
      collectDir2 = CollectDir("/etc/whatever", "incr", "tar", ".ignore", [], [], ["p2", ])
      self.failIfEqual(collectDir1, collectDir2)
      self.failUnless(not collectDir1 == collectDir2)
      self.failUnless(collectDir1 < collectDir2)
      self.failUnless(collectDir1 <= collectDir2)
      self.failUnless(not collectDir1 > collectDir2)
      self.failUnless(not collectDir1 >= collectDir2)
      self.failUnless(collectDir1 != collectDir2)


#####################
# TestPurgeDir class
#####################

class TestPurgeDir(unittest.TestCase):

   """Tests for the PurgeDir class."""

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

   def buildPath(self, components):
      """Builds a complete search path from a list of components."""
      components.insert(0, self.tmpdir)
      return buildPath(components)

   def failUnlessAssignRaises(self, exception, object, property, value):
      """Equivalent of L{failUnlessRaises}, but used for property assignments instead."""
      failUnlessAssignRaises(self, exception, object, property, value)


   ############################
   # Test __repr__ and __str__
   ############################

   def testStringFuncs_001(self):
      """
      Just make sure that the string functions don't have errors (i.e. bad variable names).
      """
      obj = PurgeDir()
      obj.__repr__()
      obj.__str__()


   ##################################
   # Test constructor and attributes
   ##################################

   def testConstructor_001(self):
      """
      Test constructor with no values filled in.
      """
      purgeDir = PurgeDir()
      self.failUnlessEqual(None, purgeDir.absolutePath)
      self.failUnlessEqual(None, purgeDir.retainDays)

   def testConstructor_002(self):
      """
      Test constructor with all values filled in, with valid values.
      """
      purgeDir = PurgeDir("/whatever", 0)
      self.failUnlessEqual("/whatever", purgeDir.absolutePath)
      self.failUnlessEqual(0, purgeDir.retainDays)

   def testConstructor_003(self):
      """
      Test assignment of absolutePath attribute, None value.
      """
      purgeDir = PurgeDir(absolutePath="/whatever")
      self.failUnlessEqual("/whatever", purgeDir.absolutePath)
      purgeDir.absolutePath = None
      self.failUnlessEqual(None, purgeDir.absolutePath)

   def testConstructor_004(self):
      """
      Test assignment of absolutePath attribute, valid value.
      """
      purgeDir = PurgeDir()
      self.failUnlessEqual(None, purgeDir.absolutePath)
      purgeDir.absolutePath = "/etc/whatever"
      self.failUnlessEqual("/etc/whatever", purgeDir.absolutePath)

   def testConstructor_005(self):
      """
      Test assignment of absolutePath attribute, invalid value (empty).
      """
      purgeDir = PurgeDir()
      self.failUnlessEqual(None, purgeDir.absolutePath)
      self.failUnlessAssignRaises(ValueError, purgeDir, "absolutePath", "")
      self.failUnlessEqual(None, purgeDir.absolutePath)

   def testConstructor_006(self):
      """
      Test assignment of absolutePath attribute, invalid value (non-absolute).
      """
      purgeDir = PurgeDir()
      self.failUnlessEqual(None, purgeDir.absolutePath)
      self.failUnlessAssignRaises(ValueError, purgeDir, "absolutePath", "bogus")
      self.failUnlessEqual(None, purgeDir.absolutePath)

   def testConstructor_007(self):
      """
      Test assignment of retainDays attribute, None value.
      """
      purgeDir = PurgeDir(retainDays=12)
      self.failUnlessEqual(12, purgeDir.retainDays)
      purgeDir.retainDays = None
      self.failUnlessEqual(None, purgeDir.retainDays)

   def testConstructor_008(self):
      """
      Test assignment of retainDays attribute, valid value (integer).
      """
      purgeDir = PurgeDir()
      self.failUnlessEqual(None, purgeDir.retainDays)
      purgeDir.retainDays = 12
      self.failUnlessEqual(12, purgeDir.retainDays)

   def testConstructor_009(self):
      """
      Test assignment of retainDays attribute, valid value (string representing integer).
      """
      purgeDir = PurgeDir()
      self.failUnlessEqual(None, purgeDir.retainDays)
      purgeDir.retainDays = "12"
      self.failUnlessEqual(12, purgeDir.retainDays)

   def testConstructor_010(self):
      """
      Test assignment of retainDays attribute, invalid value (empty string).
      """
      purgeDir = PurgeDir()
      self.failUnlessEqual(None, purgeDir.retainDays)
      self.failUnlessAssignRaises(ValueError, purgeDir, "retainDays", "")
      self.failUnlessEqual(None, purgeDir.retainDays)

   def testConstructor_011(self):
      """
      Test assignment of retainDays attribute, invalid value (non-integer, like a list).
      """
      purgeDir = PurgeDir()
      self.failUnlessEqual(None, purgeDir.retainDays)
      self.failUnlessAssignRaises(ValueError, purgeDir, "retainDays", [])
      self.failUnlessEqual(None, purgeDir.retainDays)

   def testConstructor_012(self):
      """
      Test assignment of retainDays attribute, invalid value (string representing non-integer).
      """
      purgeDir = PurgeDir()
      self.failUnlessEqual(None, purgeDir.retainDays)
      self.failUnlessAssignRaises(ValueError, purgeDir, "retainDays", "blech")
      self.failUnlessEqual(None, purgeDir.retainDays)


   ############################
   # Test comparison operators
   ############################

   def testComparison_001(self):
      """
      Test comparison of two identical objects, all attributes None.
      """
      purgeDir1 = PurgeDir()
      purgeDir2 = PurgeDir()
      self.failUnlessEqual(purgeDir1, purgeDir2)
      self.failUnless(purgeDir1 == purgeDir2)
      self.failUnless(not purgeDir1 < purgeDir2)
      self.failUnless(purgeDir1 <= purgeDir2)
      self.failUnless(not purgeDir1 > purgeDir2)
      self.failUnless(purgeDir1 >= purgeDir2)
      self.failUnless(not purgeDir1 != purgeDir2)

   def testComparison_002(self):
      """
      Test comparison of two identical objects, all attributes non-None.
      """
      purgeDir1 = PurgeDir("/etc/whatever", 12)
      purgeDir2 = PurgeDir("/etc/whatever", 12)
      self.failUnless(purgeDir1 == purgeDir2)
      self.failUnless(not purgeDir1 < purgeDir2)
      self.failUnless(purgeDir1 <= purgeDir2)
      self.failUnless(not purgeDir1 > purgeDir2)
      self.failUnless(purgeDir1 >= purgeDir2)
      self.failUnless(not purgeDir1 != purgeDir2)

   def testComparison_003(self):
      """
      Test comparison of two differing objects, absolutePath differs (one None).
      """
      purgeDir1 = PurgeDir()
      purgeDir2 = PurgeDir(absolutePath="/whatever")
      self.failIfEqual(purgeDir1, purgeDir2)
      self.failUnless(not purgeDir1 == purgeDir2)
      self.failUnless(purgeDir1 < purgeDir2)
      self.failUnless(purgeDir1 <= purgeDir2)
      self.failUnless(not purgeDir1 > purgeDir2)
      self.failUnless(not purgeDir1 >= purgeDir2)
      self.failUnless(purgeDir1 != purgeDir2)

   def testComparison_004(self):
      """
      Test comparison of two differing objects, absolutePath differs.
      """
      purgeDir1 = PurgeDir("/etc/blech", 12)
      purgeDir2 = PurgeDir("/etc/whatever", 12)
      self.failIfEqual(purgeDir1, purgeDir2)
      self.failUnless(not purgeDir1 == purgeDir2)
      self.failUnless(purgeDir1 < purgeDir2)
      self.failUnless(purgeDir1 <= purgeDir2)
      self.failUnless(not purgeDir1 > purgeDir2)
      self.failUnless(not purgeDir1 >= purgeDir2)
      self.failUnless(purgeDir1 != purgeDir2)

   def testComparison_005(self):
      """
      Test comparison of two differing objects, retainDays differs (one None).
      """
      purgeDir1 = PurgeDir()
      purgeDir2 = PurgeDir(retainDays=365)
      self.failIfEqual(purgeDir1, purgeDir2)
      self.failUnless(not purgeDir1 == purgeDir2)
      self.failUnless(purgeDir1 < purgeDir2)
      self.failUnless(purgeDir1 <= purgeDir2)
      self.failUnless(not purgeDir1 > purgeDir2)
      self.failUnless(not purgeDir1 >= purgeDir2)
      self.failUnless(purgeDir1 != purgeDir2)

   def testComparison_006(self):
      """
      Test comparison of two differing objects, retainDays differs.
      """
      purgeDir1 = PurgeDir("/etc/whatever", 365)
      purgeDir2 = PurgeDir("/etc/whatever", 12)
      self.failIfEqual(purgeDir1, purgeDir2)
      self.failUnless(not purgeDir1 == purgeDir2)
      self.failUnless(not purgeDir1 < purgeDir2)
      self.failUnless(not purgeDir1 <= purgeDir2)
      self.failUnless(purgeDir1 > purgeDir2)
      self.failUnless(purgeDir1 >= purgeDir2)
      self.failUnless(purgeDir1 != purgeDir2)


######################
# TestLocalPeer class
######################

class TestLocalPeer(unittest.TestCase):

   """Tests for the LocalPeer class."""

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

   def buildPath(self, components):
      """Builds a complete search path from a list of components."""
      components.insert(0, self.tmpdir)
      return buildPath(components)

   def failUnlessAssignRaises(self, exception, object, property, value):
      """Equivalent of L{failUnlessRaises}, but used for property assignments instead."""
      failUnlessAssignRaises(self, exception, object, property, value)


   ############################
   # Test __repr__ and __str__
   ############################

   def testStringFuncs_001(self):
      """
      Just make sure that the string functions don't have errors (i.e. bad variable names).
      """
      obj = LocalPeer()
      obj.__repr__()
      obj.__str__()


   ##################################
   # Test constructor and attributes
   ##################################

   def testConstructor_001(self):
      """
      Test constructor with no values filled in.
      """
      localPeer = LocalPeer()
      self.failUnlessEqual(None, localPeer.name)
      self.failUnlessEqual(None, localPeer.collectDir)

   def testConstructor_002(self):
      """
      Test constructor with all values filled in, with valid values.
      """
      localPeer = LocalPeer("myname", "/whatever")
      self.failUnlessEqual("myname", localPeer.name)
      self.failUnlessEqual("/whatever", localPeer.collectDir)

   def testConstructor_003(self):
      """
      Test assignment of name attribute, None value.
      """
      localPeer = LocalPeer(name="myname")
      self.failUnlessEqual("myname", localPeer.name)
      localPeer.name = None
      self.failUnlessEqual(None, localPeer.name)

   def testConstructor_004(self):
      """
      Test assignment of name attribute, valid value.
      """
      localPeer = LocalPeer()
      self.failUnlessEqual(None, localPeer.name)
      localPeer.name = "myname"
      self.failUnlessEqual("myname", localPeer.name)

   def testConstructor_005(self):
      """
      Test assignment of name attribute, invalid value (empty).
      """
      localPeer = LocalPeer()
      self.failUnlessEqual(None, localPeer.name)
      self.failUnlessAssignRaises(ValueError, localPeer, "name", "")
      self.failUnlessEqual(None, localPeer.name)

   def testConstructor_006(self):
      """
      Test assignment of collectDir attribute, None value.
      """
      localPeer = LocalPeer(collectDir="/whatever")
      self.failUnlessEqual("/whatever", localPeer.collectDir)
      localPeer.collectDir = None
      self.failUnlessEqual(None, localPeer.collectDir)

   def testConstructor_007(self):
      """
      Test assignment of collectDir attribute, valid value.
      """
      localPeer = LocalPeer()
      self.failUnlessEqual(None, localPeer.collectDir)
      localPeer.collectDir = "/etc/stuff"
      self.failUnlessEqual("/etc/stuff", localPeer.collectDir)

   def testConstructor_008(self):
      """
      Test assignment of collectDir attribute, invalid value (empty).
      """
      localPeer = LocalPeer()
      self.failUnlessEqual(None, localPeer.collectDir)
      self.failUnlessAssignRaises(ValueError, localPeer, "collectDir", "")
      self.failUnlessEqual(None, localPeer.collectDir)

   def testConstructor_009(self):
      """
      Test assignment of collectDir attribute, invalid value (non-absolute).
      """
      localPeer = LocalPeer()
      self.failUnlessEqual(None, localPeer.collectDir)
      self.failUnlessAssignRaises(ValueError, localPeer, "collectDir", "bogus")
      self.failUnlessEqual(None, localPeer.collectDir)


   ############################
   # Test comparison operators
   ############################

   def testComparison_001(self):
      """
      Test comparison of two identical objects, all attributes None.
      """
      localPeer1 = LocalPeer()
      localPeer2 = LocalPeer()
      self.failUnlessEqual(localPeer1, localPeer2)
      self.failUnless(localPeer1 == localPeer2)
      self.failUnless(not localPeer1 < localPeer2)
      self.failUnless(localPeer1 <= localPeer2)
      self.failUnless(not localPeer1 > localPeer2)
      self.failUnless(localPeer1 >= localPeer2)
      self.failUnless(not localPeer1 != localPeer2)

   def testComparison_002(self):
      """
      Test comparison of two identical objects, all attributes non-None.
      """
      localPeer1 = LocalPeer("myname", "/etc/stuff")
      localPeer2 = LocalPeer("myname", "/etc/stuff")
      self.failUnless(localPeer1 == localPeer2)
      self.failUnless(not localPeer1 < localPeer2)
      self.failUnless(localPeer1 <= localPeer2)
      self.failUnless(not localPeer1 > localPeer2)
      self.failUnless(localPeer1 >= localPeer2)
      self.failUnless(not localPeer1 != localPeer2)

   def testComparison_003(self):
      """
      Test comparison of two differing objects, name differs (one None).
      """
      localPeer1 = LocalPeer()
      localPeer2 = LocalPeer(name="blech")
      self.failIfEqual(localPeer1, localPeer2)
      self.failUnless(not localPeer1 == localPeer2)
      self.failUnless(localPeer1 < localPeer2)
      self.failUnless(localPeer1 <= localPeer2)
      self.failUnless(not localPeer1 > localPeer2)
      self.failUnless(not localPeer1 >= localPeer2)
      self.failUnless(localPeer1 != localPeer2)

   def testComparison_004(self):
      """
      Test comparison of two differing objects, name differs.
      """
      localPeer1 = LocalPeer("name", "/etc/stuff")
      localPeer2 = LocalPeer("name", "/etc/whatever")
      self.failIfEqual(localPeer1, localPeer2)
      self.failUnless(not localPeer1 == localPeer2)
      self.failUnless(localPeer1 < localPeer2)
      self.failUnless(localPeer1 <= localPeer2)
      self.failUnless(not localPeer1 > localPeer2)
      self.failUnless(not localPeer1 >= localPeer2)
      self.failUnless(localPeer1 != localPeer2)

   def testComparison_005(self):
      """
      Test comparison of two differing objects, collectDir differs (one None).
      """
      localPeer1 = LocalPeer()
      localPeer2 = LocalPeer(collectDir="/etc/whatever")
      self.failIfEqual(localPeer1, localPeer2)
      self.failUnless(not localPeer1 == localPeer2)
      self.failUnless(localPeer1 < localPeer2)
      self.failUnless(localPeer1 <= localPeer2)
      self.failUnless(not localPeer1 > localPeer2)
      self.failUnless(not localPeer1 >= localPeer2)
      self.failUnless(localPeer1 != localPeer2)

   def testComparison_006(self):
      """
      Test comparison of two differing objects, collectDir differs.
      """
      localPeer1 = LocalPeer("name2", "/etc/stuff")
      localPeer2 = LocalPeer("name1", "/etc/stuff")
      self.failIfEqual(localPeer1, localPeer2)
      self.failUnless(not localPeer1 == localPeer2)
      self.failUnless(not localPeer1 < localPeer2)
      self.failUnless(not localPeer1 <= localPeer2)
      self.failUnless(localPeer1 > localPeer2)
      self.failUnless(localPeer1 >= localPeer2)
      self.failUnless(localPeer1 != localPeer2)


#######################
# TestRemotePeer class
#######################

class TestRemotePeer(unittest.TestCase):

   """Tests for the RemotePeer class."""

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

   def buildPath(self, components):
      """Builds a complete search path from a list of components."""
      components.insert(0, self.tmpdir)
      return buildPath(components)

   def failUnlessAssignRaises(self, exception, object, property, value):
      """Equivalent of L{failUnlessRaises}, but used for property assignments instead."""
      failUnlessAssignRaises(self, exception, object, property, value)


   ############################
   # Test __repr__ and __str__
   ############################

   def testStringFuncs_001(self):
      """
      Just make sure that the string functions don't have errors (i.e. bad variable names).
      """
      obj = RemotePeer()
      obj.__repr__()
      obj.__str__()


   ##################################
   # Test constructor and attributes
   ##################################

   def testConstructor_001(self):
      """
      Test constructor with no values filled in.
      """
      remotePeer = RemotePeer()
      self.failUnlessEqual(None, remotePeer.name)
      self.failUnlessEqual(None, remotePeer.collectDir)
      self.failUnlessEqual(None, remotePeer.remoteUser)
      self.failUnlessEqual(None, remotePeer.rcpCommand)

   def testConstructor_002(self):
      """
      Test constructor with all values filled in, with valid values.
      """
      remotePeer = RemotePeer("myname", "/stuff", "backup", "scp -1 -B")
      self.failUnlessEqual("myname", remotePeer.name)
      self.failUnlessEqual("/stuff", remotePeer.collectDir)
      self.failUnlessEqual("backup", remotePeer.remoteUser)
      self.failUnlessEqual("scp -1 -B", remotePeer.rcpCommand)

   def testConstructor_003(self):
      """
      Test assignment of name attribute, None value.
      """
      remotePeer = RemotePeer(name="myname")
      self.failUnlessEqual("myname", remotePeer.name)
      remotePeer.name = None
      self.failUnlessEqual(None, remotePeer.name)

   def testConstructor_004(self):
      """
      Test assignment of name attribute, valid value.
      """
      remotePeer = RemotePeer()
      self.failUnlessEqual(None, remotePeer.name)
      remotePeer.name = "namename"
      self.failUnlessEqual("namename", remotePeer.name)

   def testConstructor_005(self):
      """
      Test assignment of name attribute, invalid value (empty).
      """
      remotePeer = RemotePeer()
      self.failUnlessEqual(None, remotePeer.name)
      self.failUnlessAssignRaises(ValueError, remotePeer, "name", "")
      self.failUnlessEqual(None, remotePeer.name)

   def testConstructor_006(self):
      """
      Test assignment of collectDir attribute, None value.
      """
      remotePeer = RemotePeer(collectDir="/etc/stuff")
      self.failUnlessEqual("/etc/stuff", remotePeer.collectDir)
      remotePeer.collectDir = None
      self.failUnlessEqual(None, remotePeer.collectDir)

   def testConstructor_007(self):
      """
      Test assignment of collectDir attribute, valid value.
      """
      remotePeer = RemotePeer()
      self.failUnlessEqual(None, remotePeer.collectDir)
      remotePeer.collectDir = "/tmp"
      self.failUnlessEqual("/tmp", remotePeer.collectDir)

   def testConstructor_008(self):
      """
      Test assignment of collectDir attribute, invalid value (empty).
      """
      remotePeer = RemotePeer()
      self.failUnlessEqual(None, remotePeer.collectDir)
      self.failUnlessAssignRaises(ValueError, remotePeer, "collectDir", "")
      self.failUnlessEqual(None, remotePeer.collectDir)

   def testConstructor_009(self):
      """
      Test assignment of collectDir attribute, invalid value (non-absolute).
      """
      remotePeer = RemotePeer()
      self.failUnlessEqual(None, remotePeer.collectDir)
      self.failUnlessAssignRaises(ValueError, remotePeer, "collectDir", "bogus/stuff/there")
      self.failUnlessEqual(None, remotePeer.collectDir)

   def testConstructor_010(self):
      """
      Test assignment of remoteUser attribute, None value.
      """
      remotePeer = RemotePeer(remoteUser="spot")
      self.failUnlessEqual("spot", remotePeer.remoteUser)
      remotePeer.remoteUser = None
      self.failUnlessEqual(None, remotePeer.remoteUser)

   def testConstructor_011(self):
      """
      Test assignment of remoteUser attribute, valid value.
      """
      remotePeer = RemotePeer()
      self.failUnlessEqual(None, remotePeer.remoteUser)
      remotePeer.remoteUser = "spot"
      self.failUnlessEqual("spot", remotePeer.remoteUser)

   def testConstructor_012(self):
      """
      Test assignment of remoteUser attribute, invalid value (empty).
      """
      remotePeer = RemotePeer()
      self.failUnlessEqual(None, remotePeer.remoteUser)
      self.failUnlessAssignRaises(ValueError, remotePeer, "remoteUser", "")
      self.failUnlessEqual(None, remotePeer.remoteUser)

   def testConstructor_013(self):
      """
      Test assignment of rcpCommand attribute, None value.
      """
      remotePeer = RemotePeer()
      self.failUnlessEqual(None, remotePeer.rcpCommand)
      remotePeer.rcpCommand = "scp"
      self.failUnlessEqual("scp", remotePeer.rcpCommand)

   def testConstructor_014(self):
      """
      Test assignment of rcpCommand attribute, valid value.
      """
      remotePeer = RemotePeer()
      self.failUnlessEqual(None, remotePeer.rcpCommand)
      remotePeer.rcpCommand = "scp"
      self.failUnlessEqual("scp", remotePeer.rcpCommand)

   def testConstructor_015(self):
      """
      Test assignment of rcpCommand attribute, invalid value (empty).
      """
      remotePeer = RemotePeer()
      self.failUnlessEqual(None, remotePeer.rcpCommand)
      self.failUnlessAssignRaises(ValueError, remotePeer, "rcpCommand", "")
      self.failUnlessEqual(None, remotePeer.rcpCommand)


   ############################
   # Test comparison operators
   ############################

   def testComparison_001(self):
      """
      Test comparison of two identical objects, all attributes None.
      """
      remotePeer1 = RemotePeer()
      remotePeer2 = RemotePeer()
      self.failUnlessEqual(remotePeer1, remotePeer2)
      self.failUnless(remotePeer1 == remotePeer2)
      self.failUnless(not remotePeer1 < remotePeer2)
      self.failUnless(remotePeer1 <= remotePeer2)
      self.failUnless(not remotePeer1 > remotePeer2)
      self.failUnless(remotePeer1 >= remotePeer2)
      self.failUnless(not remotePeer1 != remotePeer2)

   def testComparison_002(self):
      """
      Test comparison of two identical objects, all attributes non-None.
      """
      remotePeer1 = RemotePeer("name", "/etc/stuff/tmp/X11", "backup", "scp -1 -B")
      remotePeer2 = RemotePeer("name", "/etc/stuff/tmp/X11", "backup", "scp -1 -B")
      self.failUnless(remotePeer1 == remotePeer2)
      self.failUnless(not remotePeer1 < remotePeer2)
      self.failUnless(remotePeer1 <= remotePeer2)
      self.failUnless(not remotePeer1 > remotePeer2)
      self.failUnless(remotePeer1 >= remotePeer2)
      self.failUnless(not remotePeer1 != remotePeer2)

   def testComparison_003(self):
      """
      Test comparison of two differing objects, name differs (one None).
      """
      remotePeer1 = RemotePeer()
      remotePeer2 = RemotePeer(name="name")
      self.failIfEqual(remotePeer1, remotePeer2)
      self.failUnless(not remotePeer1 == remotePeer2)
      self.failUnless(remotePeer1 < remotePeer2)
      self.failUnless(remotePeer1 <= remotePeer2)
      self.failUnless(not remotePeer1 > remotePeer2)
      self.failUnless(not remotePeer1 >= remotePeer2)
      self.failUnless(remotePeer1 != remotePeer2)

   def testComparison_004(self):
      """
      Test comparison of two differing objects, name differs.
      """
      remotePeer1 = RemotePeer("name1", "/etc/stuff/tmp/X11", "backup", "scp -1 -B")
      remotePeer2 = RemotePeer("name2", "/etc/stuff/tmp/X11", "backup", "scp -1 -B")
      self.failIfEqual(remotePeer1, remotePeer2)
      self.failUnless(not remotePeer1 == remotePeer2)
      self.failUnless(remotePeer1 < remotePeer2)
      self.failUnless(remotePeer1 <= remotePeer2)
      self.failUnless(not remotePeer1 > remotePeer2)
      self.failUnless(not remotePeer1 >= remotePeer2)
      self.failUnless(remotePeer1 != remotePeer2)

   def testComparison_005(self):
      """
      Test comparison of two differing objects, collectDir differs (one None).
      """
      remotePeer1 = RemotePeer()
      remotePeer2 = RemotePeer(collectDir="/tmp")
      self.failIfEqual(remotePeer1, remotePeer2)
      self.failUnless(not remotePeer1 == remotePeer2)
      self.failUnless(remotePeer1 < remotePeer2)
      self.failUnless(remotePeer1 <= remotePeer2)
      self.failUnless(not remotePeer1 > remotePeer2)
      self.failUnless(not remotePeer1 >= remotePeer2)
      self.failUnless(remotePeer1 != remotePeer2)

   def testComparison_006(self):
      """
      Test comparison of two differing objects, collectDir differs.
      """
      remotePeer1 = RemotePeer("name", "/etc", "backup", "scp -1 -B")
      remotePeer2 = RemotePeer("name", "/etc/stuff/tmp/X11", "backup", "scp -1 -B")
      self.failIfEqual(remotePeer1, remotePeer2)
      self.failUnless(not remotePeer1 == remotePeer2)
      self.failUnless(remotePeer1 < remotePeer2)
      self.failUnless(remotePeer1 <= remotePeer2)
      self.failUnless(not remotePeer1 > remotePeer2)
      self.failUnless(not remotePeer1 >= remotePeer2)
      self.failUnless(remotePeer1 != remotePeer2)

   def testComparison_007(self):
      """
      Test comparison of two differing objects, remoteUser differs (one None).
      """
      remotePeer1 = RemotePeer()
      remotePeer2 = RemotePeer(remoteUser="spot")
      self.failIfEqual(remotePeer1, remotePeer2)
      self.failUnless(not remotePeer1 == remotePeer2)
      self.failUnless(remotePeer1 < remotePeer2)
      self.failUnless(remotePeer1 <= remotePeer2)
      self.failUnless(not remotePeer1 > remotePeer2)
      self.failUnless(not remotePeer1 >= remotePeer2)
      self.failUnless(remotePeer1 != remotePeer2)

   def testComparison_008(self):
      """
      Test comparison of two differing objects, remoteUser differs.
      """
      remotePeer1 = RemotePeer("name", "/etc/stuff/tmp/X11", "spot", "scp -1 -B")
      remotePeer2 = RemotePeer("name", "/etc/stuff/tmp/X11", "backup", "scp -1 -B")
      self.failIfEqual(remotePeer1, remotePeer2)
      self.failUnless(not remotePeer1 == remotePeer2)
      self.failUnless(not remotePeer1 < remotePeer2)
      self.failUnless(not remotePeer1 <= remotePeer2)
      self.failUnless(remotePeer1 > remotePeer2)
      self.failUnless(remotePeer1 >= remotePeer2)
      self.failUnless(remotePeer1 != remotePeer2)

   def testComparison_009(self):
      """
      Test comparison of two differing objects, rcpCommand differs (one None).
      """
      remotePeer1 = RemotePeer()
      remotePeer2 = RemotePeer(rcpCommand="scp")
      self.failIfEqual(remotePeer1, remotePeer2)
      self.failUnless(not remotePeer1 == remotePeer2)
      self.failUnless(remotePeer1 < remotePeer2)
      self.failUnless(remotePeer1 <= remotePeer2)
      self.failUnless(not remotePeer1 > remotePeer2)
      self.failUnless(not remotePeer1 >= remotePeer2)
      self.failUnless(remotePeer1 != remotePeer2)

   def testComparison_010(self):
      """
      Test comparison of two differing objects, rcpCommand differs.
      """
      remotePeer1 = RemotePeer("name", "/etc/stuff/tmp/X11", "backup", "scp -2 -B")
      remotePeer2 = RemotePeer("name", "/etc/stuff/tmp/X11", "backup", "scp -1 -B")
      self.failIfEqual(remotePeer1, remotePeer2)
      self.failUnless(not remotePeer1 == remotePeer2)
      self.failUnless(not remotePeer1 < remotePeer2)
      self.failUnless(not remotePeer1 <= remotePeer2)
      self.failUnless(remotePeer1 > remotePeer2)
      self.failUnless(remotePeer1 >= remotePeer2)
      self.failUnless(remotePeer1 != remotePeer2)


############################
# TestReferenceConfig class
############################

class TestReferenceConfig(unittest.TestCase):

   """Tests for the ReferenceConfig class."""

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

   def buildPath(self, components):
      """Builds a complete search path from a list of components."""
      components.insert(0, self.tmpdir)
      return buildPath(components)

   def failUnlessAssignRaises(self, exception, object, property, value):
      """Equivalent of L{failUnlessRaises}, but used for property assignments instead."""
      failUnlessAssignRaises(self, exception, object, property, value)


   ############################
   # Test __repr__ and __str__
   ############################

   def testStringFuncs_001(self):
      """
      Just make sure that the string functions don't have errors (i.e. bad variable names).
      """
      obj = ReferenceConfig()
      obj.__repr__()
      obj.__str__()


   ##################################
   # Test constructor and attributes
   ##################################

   def testConstructor_001(self):
      """
      Test constructor with no values filled in.
      """
      reference = ReferenceConfig()
      self.failUnlessEqual(None, reference.author)
      self.failUnlessEqual(None, reference.revision)
      self.failUnlessEqual(None, reference.description)
      self.failUnlessEqual(None, reference.generator)

   def testConstructor_002(self):
      """
      Test constructor with all values filled in, with valid values.
      """
      reference = ReferenceConfig("one", "two", "three", "four")
      self.failUnlessEqual("one", reference.author)
      self.failUnlessEqual("two", reference.revision)
      self.failUnlessEqual("three", reference.description)
      self.failUnlessEqual("four", reference.generator)

   def testConstructor_003(self):
      """
      Test assignment of author attribute, None value.
      """
      reference = ReferenceConfig(author="one")
      self.failUnlessEqual("one", reference.author)
      reference.author = None
      self.failUnlessEqual(None, reference.author)

   def testConstructor_004(self):
      """
      Test assignment of author attribute, valid value.
      """
      reference = ReferenceConfig()
      self.failUnlessEqual(None, reference.author)
      reference.author = "one"
      self.failUnlessEqual("one", reference.author)

   def testConstructor_005(self):
      """
      Test assignment of author attribute, valid value (empty).
      """
      reference = ReferenceConfig()
      self.failUnlessEqual(None, reference.author)
      reference.author = ""
      self.failUnlessEqual("", reference.author)

   def testConstructor_006(self):
      """
      Test assignment of revision attribute, None value.
      """
      reference = ReferenceConfig(revision="one")
      self.failUnlessEqual("one", reference.revision)
      reference.revision = None
      self.failUnlessEqual(None, reference.revision)

   def testConstructor_007(self):
      """
      Test assignment of revision attribute, valid value.
      """
      reference = ReferenceConfig()
      self.failUnlessEqual(None, reference.revision)
      reference.revision = "one"
      self.failUnlessEqual("one", reference.revision)

   def testConstructor_008(self):
      """
      Test assignment of revision attribute, valid value (empty).
      """
      reference = ReferenceConfig()
      self.failUnlessEqual(None, reference.revision)
      reference.revision = ""
      self.failUnlessEqual("", reference.revision)

   def testConstructor_009(self):
      """
      Test assignment of description attribute, None value.
      """
      reference = ReferenceConfig(description="one")
      self.failUnlessEqual("one", reference.description)
      reference.description = None
      self.failUnlessEqual(None, reference.description)

   def testConstructor_010(self):
      """
      Test assignment of description attribute, valid value.
      """
      reference = ReferenceConfig()
      self.failUnlessEqual(None, reference.description)
      reference.description = "one"
      self.failUnlessEqual("one", reference.description)

   def testConstructor_011(self):
      """
      Test assignment of description attribute, valid value (empty).
      """
      reference = ReferenceConfig()
      self.failUnlessEqual(None, reference.description)
      reference.description = ""
      self.failUnlessEqual("", reference.description)

   def testConstructor_012(self):
      """
      Test assignment of generator attribute, None value.
      """
      reference = ReferenceConfig(generator="one")
      self.failUnlessEqual("one", reference.generator)
      reference.generator = None
      self.failUnlessEqual(None, reference.generator)

   def testConstructor_013(self):
      """
      Test assignment of generator attribute, valid value.
      """
      reference = ReferenceConfig()
      self.failUnlessEqual(None, reference.generator)
      reference.generator = "one"
      self.failUnlessEqual("one", reference.generator)

   def testConstructor_014(self):
      """
      Test assignment of generator attribute, valid value (empty).
      """
      reference = ReferenceConfig()
      self.failUnlessEqual(None, reference.generator)
      reference.generator = ""
      self.failUnlessEqual("", reference.generator)


   ############################
   # Test comparison operators
   ############################

   def testComparison_001(self):
      """
      Test comparison of two identical objects, all attributes None.
      """
      reference1 = ReferenceConfig()
      reference2 = ReferenceConfig()
      self.failUnlessEqual(reference1, reference2)
      self.failUnless(reference1 == reference2)
      self.failUnless(not reference1 < reference2)
      self.failUnless(reference1 <= reference2)
      self.failUnless(not reference1 > reference2)
      self.failUnless(reference1 >= reference2)
      self.failUnless(not reference1 != reference2)

   def testComparison_002(self):
      """
      Test comparison of two identical objects, all attributes non-None.
      """
      reference1 = ReferenceConfig("one", "two", "three", "four")
      reference2 = ReferenceConfig("one", "two", "three", "four")
      self.failUnless(reference1 == reference2)
      self.failUnless(not reference1 < reference2)
      self.failUnless(reference1 <= reference2)
      self.failUnless(not reference1 > reference2)
      self.failUnless(reference1 >= reference2)
      self.failUnless(not reference1 != reference2)

   def testComparison_003(self):
      """
      Test comparison of two differing objects, author differs (one None).
      """
      reference1 = ReferenceConfig()
      reference2 = ReferenceConfig(author="one")
      self.failIfEqual(reference1, reference2)
      self.failUnless(not reference1 == reference2)
      self.failUnless(reference1 < reference2)
      self.failUnless(reference1 <= reference2)
      self.failUnless(not reference1 > reference2)
      self.failUnless(not reference1 >= reference2)
      self.failUnless(reference1 != reference2)

   def testComparison_004(self):
      """
      Test comparison of two differing objects, author differs (one empty).
      """
      reference1 = ReferenceConfig("", "two", "three", "four")
      reference2 = ReferenceConfig("one", "two", "three", "four")
      self.failIfEqual(reference1, reference2)
      self.failUnless(not reference1 == reference2)
      self.failUnless(reference1 < reference2)
      self.failUnless(reference1 <= reference2)
      self.failUnless(not reference1 > reference2)
      self.failUnless(not reference1 >= reference2)
      self.failUnless(reference1 != reference2)

   def testComparison_005(self):
      """
      Test comparison of two differing objects, author differs.
      """
      reference1 = ReferenceConfig("one", "two", "three", "four")
      reference2 = ReferenceConfig("author", "two", "three", "four")
      self.failIfEqual(reference1, reference2)
      self.failUnless(not reference1 == reference2)
      self.failUnless(not reference1 < reference2)
      self.failUnless(not reference1 <= reference2)
      self.failUnless(reference1 > reference2)
      self.failUnless(reference1 >= reference2)
      self.failUnless(reference1 != reference2)

   def testComparison_006(self):
      """
      Test comparison of two differing objects, revision differs (one None).
      """
      reference1 = ReferenceConfig()
      reference2 = ReferenceConfig(revision="one")
      self.failIfEqual(reference1, reference2)
      self.failUnless(not reference1 == reference2)
      self.failUnless(reference1 < reference2)
      self.failUnless(reference1 <= reference2)
      self.failUnless(not reference1 > reference2)
      self.failUnless(not reference1 >= reference2)
      self.failUnless(reference1 != reference2)

   def testComparison_007(self):
      """
      Test comparison of two differing objects, revision differs (one empty).
      """
      reference1 = ReferenceConfig("one", "two", "three", "four")
      reference2 = ReferenceConfig("one", "", "three", "four")
      self.failIfEqual(reference1, reference2)
      self.failUnless(not reference1 == reference2)
      self.failUnless(not reference1 < reference2)
      self.failUnless(not reference1 <= reference2)
      self.failUnless(reference1 > reference2)
      self.failUnless(reference1 >= reference2)
      self.failUnless(reference1 != reference2)

   def testComparison_008(self):
      """
      Test comparison of two differing objects, revision differs.
      """
      reference1 = ReferenceConfig("one", "two", "three", "four")
      reference2 = ReferenceConfig("one", "revision", "three", "four")
      self.failIfEqual(reference1, reference2)
      self.failUnless(not reference1 == reference2)
      self.failUnless(not reference1 < reference2)
      self.failUnless(not reference1 <= reference2)
      self.failUnless(reference1 > reference2)
      self.failUnless(reference1 >= reference2)
      self.failUnless(reference1 != reference2)

   def testComparison_009(self):
      """
      Test comparison of two differing objects, description differs (one None).
      """
      reference1 = ReferenceConfig()
      reference2 = ReferenceConfig(description="one")
      self.failIfEqual(reference1, reference2)
      self.failUnless(not reference1 == reference2)
      self.failUnless(reference1 < reference2)
      self.failUnless(reference1 <= reference2)
      self.failUnless(not reference1 > reference2)
      self.failUnless(not reference1 >= reference2)
      self.failUnless(reference1 != reference2)

   def testComparison_010(self):
      """
      Test comparison of two differing objects, description differs (one empty).
      """
      reference1 = ReferenceConfig("one", "two", "three", "four")
      reference2 = ReferenceConfig("one", "two", "", "four")
      self.failIfEqual(reference1, reference2)
      self.failUnless(not reference1 == reference2)
      self.failUnless(not reference1 < reference2)
      self.failUnless(not reference1 <= reference2)
      self.failUnless(reference1 > reference2)
      self.failUnless(reference1 >= reference2)
      self.failUnless(reference1 != reference2)

   def testComparison_011(self):
      """
      Test comparison of two differing objects, description differs.
      """
      reference1 = ReferenceConfig("one", "two", "description", "four")
      reference2 = ReferenceConfig("one", "two", "three", "four")
      self.failIfEqual(reference1, reference2)
      self.failUnless(not reference1 == reference2)
      self.failUnless(reference1 < reference2)
      self.failUnless(reference1 <= reference2)
      self.failUnless(not reference1 > reference2)
      self.failUnless(not reference1 >= reference2)
      self.failUnless(reference1 != reference2)

   def testComparison_012(self):
      """
      Test comparison of two differing objects, generator differs (one None).
      """
      reference1 = ReferenceConfig()
      reference2 = ReferenceConfig(generator="one")
      self.failIfEqual(reference1, reference2)
      self.failUnless(not reference1 == reference2)
      self.failUnless(reference1 < reference2)
      self.failUnless(reference1 <= reference2)
      self.failUnless(not reference1 > reference2)
      self.failUnless(not reference1 >= reference2)
      self.failUnless(reference1 != reference2)

   def testComparison_013(self):
      """
      Test comparison of two differing objects, generator differs (one empty).
      """
      reference1 = ReferenceConfig("one", "two", "three", "")
      reference2 = ReferenceConfig("one", "two", "three", "four")
      self.failIfEqual(reference1, reference2)
      self.failUnless(not reference1 == reference2)
      self.failUnless(reference1 < reference2)
      self.failUnless(reference1 <= reference2)
      self.failUnless(not reference1 > reference2)
      self.failUnless(not reference1 >= reference2)
      self.failUnless(reference1 != reference2)

   def testComparison_014(self):
      """
      Test comparison of two differing objects, generator differs.
      """
      reference1 = ReferenceConfig("one", "two", "three", "four")
      reference2 = ReferenceConfig("one", "two", "three", "generator")
      self.failIfEqual(reference1, reference2)
      self.failUnless(not reference1 == reference2)
      self.failUnless(reference1 < reference2)
      self.failUnless(reference1 <= reference2)
      self.failUnless(not reference1 > reference2)
      self.failUnless(not reference1 >= reference2)
      self.failUnless(reference1 != reference2)


##########################
# TestOptionsConfig class
##########################

class TestOptionsConfig(unittest.TestCase):

   """Tests for the OptionsConfig class."""

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

   def buildPath(self, components):
      """Builds a complete search path from a list of components."""
      components.insert(0, self.tmpdir)
      return buildPath(components)

   def failUnlessAssignRaises(self, exception, object, property, value):
      """Equivalent of L{failUnlessRaises}, but used for property assignments instead."""
      failUnlessAssignRaises(self, exception, object, property, value)


   ############################
   # Test __repr__ and __str__
   ############################

   def testStringFuncs_001(self):
      """
      Just make sure that the string functions don't have errors (i.e. bad variable names).
      """
      obj = OptionsConfig()
      obj.__repr__()
      obj.__str__()


   ##################################
   # Test constructor and attributes
   ##################################

   def testConstructor_001(self):
      """
      Test constructor with no values filled in.
      """
      options = OptionsConfig()
      self.failUnlessEqual(None, options.startingDay)
      self.failUnlessEqual(None, options.workingDir)
      self.failUnlessEqual(None, options.backupUser)
      self.failUnlessEqual(None, options.backupGroup)
      self.failUnlessEqual(None, options.rcpCommand)

   def testConstructor_002(self):
      """
      Test constructor with all values filled in, with valid values.
      """
      options = OptionsConfig("monday", "/tmp", "user", "group", "scp -1 -B")
      self.failUnlessEqual("monday", options.startingDay)
      self.failUnlessEqual("/tmp", options.workingDir)
      self.failUnlessEqual("user", options.backupUser)
      self.failUnlessEqual("group", options.backupGroup)
      self.failUnlessEqual("scp -1 -B", options.rcpCommand)

   def testConstructor_003(self):
      """
      Test assignment of startingDay attribute, None value.
      """
      options = OptionsConfig(startingDay="monday")
      self.failUnlessEqual("monday", options.startingDay)
      options.startingDay = None
      self.failUnlessEqual(None, options.startingDay)

   def testConstructor_004(self):
      """
      Test assignment of startingDay attribute, valid value.
      """
      options = OptionsConfig()
      self.failUnlessEqual(None, options.startingDay)
      options.startingDay = "monday"
      self.failUnlessEqual("monday", options.startingDay)
      options.startingDay = "tuesday"
      self.failUnlessEqual("tuesday", options.startingDay)
      options.startingDay = "wednesday"
      self.failUnlessEqual("wednesday", options.startingDay)
      options.startingDay = "thursday"
      self.failUnlessEqual("thursday", options.startingDay)
      options.startingDay = "friday"
      self.failUnlessEqual("friday", options.startingDay)
      options.startingDay = "saturday"
      self.failUnlessEqual("saturday", options.startingDay)
      options.startingDay = "sunday"
      self.failUnlessEqual("sunday", options.startingDay)

   def testConstructor_005(self):
      """
      Test assignment of startingDay attribute, invalid value (empty).
      """
      options = OptionsConfig()
      self.failUnlessEqual(None, options.startingDay)
      self.failUnlessAssignRaises(ValueError, options, "startingDay", "")
      self.failUnlessEqual(None, options.startingDay)

   def testConstructor_006(self):
      """
      Test assignment of startingDay attribute, invalid value (not in list).
      """
      options = OptionsConfig()
      self.failUnlessEqual(None, options.startingDay)
      self.failUnlessAssignRaises(ValueError, options, "startingDay", "dienstag")   # ha, ha, pretend I'm German
      self.failUnlessEqual(None, options.startingDay)

   def testConstructor_007(self):
      """
      Test assignment of workingDir attribute, None value.
      """
      options = OptionsConfig(workingDir="/tmp")
      self.failUnlessEqual("/tmp", options.workingDir)
      options.workingDir = None
      self.failUnlessEqual(None, options.workingDir)

   def testConstructor_008(self):
      """
      Test assignment of workingDir attribute, valid value.
      """
      options = OptionsConfig()
      self.failUnlessEqual(None, options.workingDir)
      options.workingDir = "/tmp"
      self.failUnlessEqual("/tmp", options.workingDir)

   def testConstructor_009(self):
      """
      Test assignment of workingDir attribute, invalid value (empty).
      """
      options = OptionsConfig()
      self.failUnlessEqual(None, options.workingDir)
      self.failUnlessAssignRaises(ValueError, options, "workingDir", "")
      self.failUnlessEqual(None, options.workingDir)

   def testConstructor_010(self):
      """
      Test assignment of workingDir attribute, invalid value (non-absolute).
      """
      options = OptionsConfig()
      self.failUnlessEqual(None, options.workingDir)
      self.failUnlessAssignRaises(ValueError, options, "workingDir", "stuff")
      self.failUnlessEqual(None, options.workingDir)

   def testConstructor_011(self):
      """
      Test assignment of backupUser attribute, None value.
      """
      options = OptionsConfig(backupUser="user")
      self.failUnlessEqual("user", options.backupUser)
      options.backupUser = None
      self.failUnlessEqual(None, options.backupUser)

   def testConstructor_012(self):
      """
      Test assignment of backupUser attribute, valid value.
      """
      options = OptionsConfig()
      self.failUnlessEqual(None, options.backupUser)
      options.backupUser = "user"
      self.failUnlessEqual("user", options.backupUser)

   def testConstructor_013(self):
      """
      Test assignment of backupUser attribute, invalid value (empty).
      """
      options = OptionsConfig()
      self.failUnlessEqual(None, options.backupUser)
      self.failUnlessAssignRaises(ValueError, options, "backupUser", "")
      self.failUnlessEqual(None, options.backupUser)

   def testConstructor_014(self):
      """
      Test assignment of backupGroup attribute, None value.
      """
      options = OptionsConfig(backupGroup="group")
      self.failUnlessEqual("group", options.backupGroup)
      options.backupGroup = None
      self.failUnlessEqual(None, options.backupGroup)

   def testConstructor_015(self):
      """
      Test assignment of backupGroup attribute, valid value.
      """
      options = OptionsConfig()
      self.failUnlessEqual(None, options.backupGroup)
      options.backupGroup = "group"
      self.failUnlessEqual("group", options.backupGroup)

   def testConstructor_016(self):
      """
      Test assignment of backupGroup attribute, invalid value (empty).
      """
      options = OptionsConfig()
      self.failUnlessEqual(None, options.backupGroup)
      self.failUnlessAssignRaises(ValueError, options, "backupGroup", "")
      self.failUnlessEqual(None, options.backupGroup)

   def testConstructor_017(self):
      """
      Test assignment of rcpCommand attribute, None value.
      """
      options = OptionsConfig(rcpCommand="command")
      self.failUnlessEqual("command", options.rcpCommand)
      options.rcpCommand = None
      self.failUnlessEqual(None, options.rcpCommand)

   def testConstructor_018(self):
      """
      Test assignment of rcpCommand attribute, valid value.
      """
      options = OptionsConfig()
      self.failUnlessEqual(None, options.rcpCommand)
      options.rcpCommand = "command"
      self.failUnlessEqual("command", options.rcpCommand)

   def testConstructor_019(self):
      """
      Test assignment of rcpCommand attribute, invalid value (empty).
      """
      options = OptionsConfig()
      self.failUnlessEqual(None, options.rcpCommand)
      self.failUnlessAssignRaises(ValueError, options, "rcpCommand", "")
      self.failUnlessEqual(None, options.rcpCommand)


   ############################
   # Test comparison operators
   ############################

   def testComparison_001(self):
      """
      Test comparison of two identical objects, all attributes None.
      """
      options1 = OptionsConfig()
      options2 = OptionsConfig()
      self.failUnlessEqual(options1, options2)
      self.failUnless(options1 == options2)
      self.failUnless(not options1 < options2)
      self.failUnless(options1 <= options2)
      self.failUnless(not options1 > options2)
      self.failUnless(options1 >= options2)
      self.failUnless(not options1 != options2)

   def testComparison_002(self):
      """
      Test comparison of two identical objects, all attributes non-None.
      """
      options1 = OptionsConfig("monday", "/tmp", "user", "group", "scp -1 -B")
      options2 = OptionsConfig("monday", "/tmp", "user", "group", "scp -1 -B")
      self.failUnlessEqual(options1, options2)
      self.failUnless(options1 == options2)
      self.failUnless(not options1 < options2)
      self.failUnless(options1 <= options2)
      self.failUnless(not options1 > options2)
      self.failUnless(options1 >= options2)
      self.failUnless(not options1 != options2)

   def testComparison_003(self):
      """
      Test comparison of two differing objects, startingDay differs (one None).
      """
      options1 = OptionsConfig()
      options2 = OptionsConfig(startingDay="monday")
      self.failIfEqual(options1, options2)
      self.failUnless(not options1 == options2)
      self.failUnless(options1 < options2)
      self.failUnless(options1 <= options2)
      self.failUnless(not options1 > options2)
      self.failUnless(not options1 >= options2)
      self.failUnless(options1 != options2)

   def testComparison_004(self):
      """
      Test comparison of two differing objects, startingDay differs.
      """
      options1 = OptionsConfig("monday", "/tmp", "user", "group", "scp -1 -B")
      options2 = OptionsConfig("tuesday", "/tmp", "user", "group", "scp -1 -B")
      self.failIfEqual(options1, options2)
      self.failUnless(not options1 == options2)
      self.failUnless(options1 < options2)
      self.failUnless(options1 <= options2)
      self.failUnless(not options1 > options2)
      self.failUnless(not options1 >= options2)
      self.failUnless(options1 != options2)

   def testComparison_005(self):
      """
      Test comparison of two differing objects, workingDir differs (one None).
      """
      options1 = OptionsConfig()
      options2 = OptionsConfig(workingDir="/tmp")
      self.failIfEqual(options1, options2)
      self.failUnless(not options1 == options2)
      self.failUnless(options1 < options2)
      self.failUnless(options1 <= options2)
      self.failUnless(not options1 > options2)
      self.failUnless(not options1 >= options2)
      self.failUnless(options1 != options2)

   def testComparison_006(self):
      """
      Test comparison of two differing objects, workingDir differs.
      """
      options1 = OptionsConfig("monday", "/tmp/whatever", "user", "group", "scp -1 -B")
      options2 = OptionsConfig("monday", "/tmp", "user", "group", "scp -1 -B")
      self.failIfEqual(options1, options2)
      self.failUnless(not options1 == options2)
      self.failUnless(not options1 < options2)
      self.failUnless(not options1 <= options2)
      self.failUnless(options1 > options2)
      self.failUnless(options1 >= options2)
      self.failUnless(options1 != options2)

   def testComparison_007(self):
      """
      Test comparison of two differing objects, backupUser differs (one None).
      """
      options1 = OptionsConfig()
      options2 = OptionsConfig(backupUser="user")
      self.failIfEqual(options1, options2)
      self.failUnless(not options1 == options2)
      self.failUnless(options1 < options2)
      self.failUnless(options1 <= options2)
      self.failUnless(not options1 > options2)
      self.failUnless(not options1 >= options2)
      self.failUnless(options1 != options2)

   def testComparison_008(self):
      """
      Test comparison of two differing objects, backupUser differs.
      """
      options1 = OptionsConfig("monday", "/tmp", "user2", "group", "scp -1 -B")
      options2 = OptionsConfig("monday", "/tmp", "user1", "group", "scp -1 -B")
      self.failIfEqual(options1, options2)
      self.failUnless(not options1 == options2)
      self.failUnless(not options1 < options2)
      self.failUnless(not options1 <= options2)
      self.failUnless(options1 > options2)
      self.failUnless(options1 >= options2)
      self.failUnless(options1 != options2)

   def testComparison_009(self):
      """
      Test comparison of two differing objects, backupGroup differs (one None).
      """
      options1 = OptionsConfig()
      options2 = OptionsConfig(backupGroup="group")
      self.failIfEqual(options1, options2)
      self.failUnless(not options1 == options2)
      self.failUnless(options1 < options2)
      self.failUnless(options1 <= options2)
      self.failUnless(not options1 > options2)
      self.failUnless(not options1 >= options2)
      self.failUnless(options1 != options2)

   def testComparison_010(self):
      """
      Test comparison of two differing objects, backupGroup differs.
      """
      options1 = OptionsConfig("monday", "/tmp", "user", "group1", "scp -1 -B")
      options2 = OptionsConfig("monday", "/tmp", "user", "group2", "scp -1 -B")
      self.failIfEqual(options1, options2)
      self.failUnless(not options1 == options2)
      self.failUnless(options1 < options2)
      self.failUnless(options1 <= options2)
      self.failUnless(not options1 > options2)
      self.failUnless(not options1 >= options2)
      self.failUnless(options1 != options2)

   def testComparison_011(self):
      """
      Test comparison of two differing objects, rcpCommand differs (one None).
      """
      options1 = OptionsConfig()
      options2 = OptionsConfig(rcpCommand="command")
      self.failIfEqual(options1, options2)
      self.failUnless(not options1 == options2)
      self.failUnless(options1 < options2)
      self.failUnless(options1 <= options2)
      self.failUnless(not options1 > options2)
      self.failUnless(not options1 >= options2)
      self.failUnless(options1 != options2)

   def testComparison_012(self):
      """
      Test comparison of two differing objects, rcpCommand differs.
      """
      options1 = OptionsConfig("monday", "/tmp", "user", "group", "scp -2 -B")
      options2 = OptionsConfig("monday", "/tmp", "user", "group", "scp -1 -B")
      self.failIfEqual(options1, options2)
      self.failUnless(not options1 == options2)
      self.failUnless(not options1 < options2)
      self.failUnless(not options1 <= options2)
      self.failUnless(options1 > options2)
      self.failUnless(options1 >= options2)
      self.failUnless(options1 != options2)


##########################
# TestCollectConfig class
##########################

class TestCollectConfig(unittest.TestCase):

   """Tests for the CollectConfig class."""

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

   def buildPath(self, components):
      """Builds a complete search path from a list of components."""
      components.insert(0, self.tmpdir)
      return buildPath(components)

   def failUnlessAssignRaises(self, exception, object, property, value):
      """Equivalent of L{failUnlessRaises}, but used for property assignments instead."""
      failUnlessAssignRaises(self, exception, object, property, value)


   ############################
   # Test __repr__ and __str__
   ############################

   def testStringFuncs_001(self):
      """
      Just make sure that the string functions don't have errors (i.e. bad variable names).
      """
      obj = CollectConfig()
      obj.__repr__()
      obj.__str__()


   ##################################
   # Test constructor and attributes
   ##################################

   def testConstructor_001(self):
      """
      Test constructor with no values filled in.
      """
      collect = CollectConfig()
      self.failUnlessEqual(None, collect.targetDir)
      self.failUnlessEqual(None, collect.collectMode)
      self.failUnlessEqual(None, collect.archiveMode)
      self.failUnlessEqual(None, collect.ignoreFile)
      self.failUnlessEqual(None, collect.absoluteExcludePaths)
      self.failUnlessEqual(None, collect.excludePatterns)
      self.failUnlessEqual(None, collect.collectDirs)

   def testConstructor_002(self):
      """
      Test constructor with all values filled in, with valid values (lists empty).
      """
      collect = CollectConfig("/target", "incr", "tar", "ignore", [], [], [])
      self.failUnlessEqual("/target", collect.targetDir)
      self.failUnlessEqual("incr", collect.collectMode)
      self.failUnlessEqual("tar", collect.archiveMode)
      self.failUnlessEqual("ignore", collect.ignoreFile)
      self.failUnlessEqual([], collect.absoluteExcludePaths)
      self.failUnlessEqual([], collect.excludePatterns)
      self.failUnlessEqual([], collect.collectDirs)

   def testConstructor_003(self):
      """
      Test constructor with all values filled in, with valid values (lists not empty).
      """
      collect = CollectConfig("/target", "incr", "tar", "ignore", ["/path",], ["pattern",], [CollectDir(),])
      self.failUnlessEqual("/target", collect.targetDir)
      self.failUnlessEqual("incr", collect.collectMode)
      self.failUnlessEqual("tar", collect.archiveMode)
      self.failUnlessEqual("ignore", collect.ignoreFile)
      self.failUnlessEqual(["/path",], collect.absoluteExcludePaths)
      self.failUnlessEqual(["pattern",], collect.excludePatterns)
      self.failUnlessEqual([CollectDir(),], collect.collectDirs)

   def testConstructor_004(self):
      """
      Test assignment of targetDir attribute, None value.
      """
      collect = CollectConfig(targetDir="/whatever")
      self.failUnlessEqual("/whatever", collect.targetDir)
      collect.targetDir = None
      self.failUnlessEqual(None, collect.targetDir)

   def testConstructor_005(self):
      """
      Test assignment of targetDir attribute, valid value.
      """
      collect = CollectConfig()
      self.failUnlessEqual(None, collect.targetDir)
      collect.targetDir = "/whatever"
      self.failUnlessEqual("/whatever", collect.targetDir)

   def testConstructor_006(self):
      """
      Test assignment of targetDir attribute, invalid value (empty).
      """
      collect = CollectConfig()
      self.failUnlessEqual(None, collect.targetDir)
      self.failUnlessAssignRaises(ValueError, collect, "targetDir", "")
      self.failUnlessEqual(None, collect.targetDir)

   def testConstructor_007(self):
      """
      Test assignment of targetDir attribute, invalid value (non-absolute).
      """
      collect = CollectConfig()
      self.failUnlessEqual(None, collect.targetDir)
      self.failUnlessAssignRaises(ValueError, collect, "targetDir", "bogus")
      self.failUnlessEqual(None, collect.targetDir)

   def testConstructor_008(self):
      """
      Test assignment of collectMode attribute, None value.
      """
      collect = CollectConfig(collectMode="incr")
      self.failUnlessEqual("incr", collect.collectMode)
      collect.collectMode = None
      self.failUnlessEqual(None, collect.collectMode)

   def testConstructor_009(self):
      """
      Test assignment of collectMode attribute, valid value.
      """
      collect = CollectConfig()
      self.failUnlessEqual(None, collect.collectMode)
      collect.collectMode = "daily"
      self.failUnlessEqual("daily", collect.collectMode)
      collect.collectMode = "weekly"
      self.failUnlessEqual("weekly", collect.collectMode)
      collect.collectMode = "incr"
      self.failUnlessEqual("incr", collect.collectMode)

   def testConstructor_010(self):
      """
      Test assignment of collectMode attribute, invalid value (empty).
      """
      collect = CollectConfig()
      self.failUnlessEqual(None, collect.collectMode)
      self.failUnlessAssignRaises(ValueError, collect, "collectMode", "")
      self.failUnlessEqual(None, collect.collectMode)

   def testConstructor_011(self):
      """
      Test assignment of collectMode attribute, invalid value (not in list).
      """
      collect = CollectConfig()
      self.failUnlessEqual(None, collect.collectMode)
      self.failUnlessAssignRaises(ValueError, collect, "collectMode", "periodic")
      self.failUnlessEqual(None, collect.collectMode)

   def testConstructor_012(self):
      """
      Test assignment of archiveMode attribute, None value.
      """
      collect = CollectConfig(archiveMode="tar")
      self.failUnlessEqual("tar", collect.archiveMode)
      collect.archiveMode = None
      self.failUnlessEqual(None, collect.archiveMode)

   def testConstructor_013(self):
      """
      Test assignment of archiveMode attribute, valid value.
      """
      collect = CollectConfig()
      self.failUnlessEqual(None, collect.archiveMode)
      collect.archiveMode = "tar"
      self.failUnlessEqual("tar", collect.archiveMode)
      collect.archiveMode = "targz"
      self.failUnlessEqual("targz", collect.archiveMode)
      collect.archiveMode = "tarbz2"
      self.failUnlessEqual("tarbz2", collect.archiveMode)

   def testConstructor_014(self):
      """
      Test assignment of archiveMode attribute, invalid value (empty).
      """
      collect = CollectConfig()
      self.failUnlessEqual(None, collect.archiveMode)
      self.failUnlessAssignRaises(ValueError, collect, "archiveMode", "")
      self.failUnlessEqual(None, collect.archiveMode)

   def testConstructor_015(self):
      """
      Test assignment of archiveMode attribute, invalid value (not in list).
      """
      collect = CollectConfig()
      self.failUnlessEqual(None, collect.archiveMode)
      self.failUnlessAssignRaises(ValueError, collect, "archiveMode", "tarz")
      self.failUnlessEqual(None, collect.archiveMode)

   def testConstructor_016(self):
      """
      Test assignment of ignoreFile attribute, None value.
      """
      collect = CollectConfig(ignoreFile="ignore")
      self.failUnlessEqual("ignore", collect.ignoreFile)
      collect.ignoreFile = None
      self.failUnlessEqual(None, collect.ignoreFile)

   def testConstructor_017(self):
      """
      Test assignment of ignoreFile attribute, valid value.
      """
      collect = CollectConfig()
      self.failUnlessEqual(None, collect.ignoreFile)
      collect.ignoreFile = "ignore"
      self.failUnlessEqual("ignore", collect.ignoreFile)

   def testConstructor_018(self):
      """
      Test assignment of ignoreFile attribute, invalid value (empty).
      """
      collect = CollectConfig()
      self.failUnlessEqual(None, collect.ignoreFile)
      self.failUnlessAssignRaises(ValueError, collect, "ignoreFile", "")
      self.failUnlessEqual(None, collect.ignoreFile)

   def testConstructor_019(self):
      """
      Test assignment of absoluteExcludePaths attribute, None value.
      """
      collect = CollectConfig(absoluteExcludePaths=[])
      self.failUnlessEqual([], collect.absoluteExcludePaths)
      collect.absoluteExcludePaths = None
      self.failUnlessEqual(None, collect.absoluteExcludePaths)

   def testConstructor_020(self):
      """
      Test assignment of absoluteExcludePaths attribute, [] value.
      """
      collect = CollectConfig()
      self.failUnlessEqual(None, collect.absoluteExcludePaths)
      collect.absoluteExcludePaths = []
      self.failUnlessEqual([], collect.absoluteExcludePaths)

   def testConstructor_021(self):
      """
      Test assignment of absoluteExcludePaths attribute, single valid entry.
      """
      collect = CollectConfig()
      self.failUnlessEqual(None, collect.absoluteExcludePaths)
      collect.absoluteExcludePaths = ["/whatever",]
      self.failUnlessEqual(["/whatever", ], collect.absoluteExcludePaths)

   def testConstructor_022(self):
      """
      Test assignment of absoluteExcludePaths attribute, multiple valid
      entries.
      """
      collect = CollectConfig()
      self.failUnlessEqual(None, collect.absoluteExcludePaths)
      collect.absoluteExcludePaths = ["/one", "/two", "/three", ]
      self.failUnlessEqual(["/one", "/two", "/three", ], collect.absoluteExcludePaths)

   def testConstructor_023(self):
      """
      Test assignment of absoluteExcludePaths attribute, single invalid entry
      (empty).
      """
      collect = CollectConfig()
      self.failUnlessEqual(None, collect.absoluteExcludePaths)
      self.failUnlessAssignRaises(ValueError, collect, "absoluteExcludePaths", [ "", ])
      self.failUnlessEqual(None, collect.absoluteExcludePaths)

   def testConstructor_024(self):
      """
      Test assignment of absoluteExcludePaths attribute, single invalid entry
      (not absolute).
      """
      collect = CollectConfig()
      self.failUnlessEqual(None, collect.absoluteExcludePaths)
      self.failUnlessAssignRaises(ValueError, collect, "absoluteExcludePaths", [ "one", ])
      self.failUnlessEqual(None, collect.absoluteExcludePaths)

   def testConstructor_025(self):
      """
      Test assignment of absoluteExcludePaths attribute, mixed valid and
      invalid entries.
      """
      collect = CollectConfig()
      self.failUnlessEqual(None, collect.absoluteExcludePaths)
      self.failUnlessAssignRaises(ValueError, collect, "absoluteExcludePaths", [ "one", "/two", ])
      self.failUnlessEqual(None, collect.absoluteExcludePaths)

   def testConstructor_026(self):
      """
      Test assignment of excludePatterns attribute, None value.
      """
      collect = CollectConfig(excludePatterns=[])
      self.failUnlessEqual([], collect.excludePatterns)
      collect.excludePatterns = None
      self.failUnlessEqual(None, collect.excludePatterns)

   def testConstructor_027(self):
      """
      Test assignment of excludePatterns attribute, [] value.
      """
      collect = CollectConfig()
      self.failUnlessEqual(None, collect.excludePatterns)
      collect.excludePatterns = []
      self.failUnlessEqual([], collect.excludePatterns)

   def testConstructor_028(self):
      """
      Test assignment of excludePatterns attribute, single valid entry.
      """
      collect = CollectConfig()
      self.failUnlessEqual(None, collect.excludePatterns)
      collect.excludePatterns = ["pattern", ]
      self.failUnlessEqual(["pattern", ], collect.excludePatterns)

   def testConstructor_029(self):
      """
      Test assignment of excludePatterns attribute, multiple valid entries.
      """
      collect = CollectConfig()
      self.failUnlessEqual(None, collect.excludePatterns)
      collect.excludePatterns = ["pattern1", "pattern2", ]
      self.failUnlessEqual(["pattern1", "pattern2", ], collect.excludePatterns)

   def testConstructor_030(self):
      """
      Test assignment of collectDirs attribute, None value.
      """
      collect = CollectConfig(collectDirs=[])
      self.failUnlessEqual([], collect.collectDirs)
      collect.collectDirs = None
      self.failUnlessEqual(None, collect.collectDirs)

   def testConstructor_031(self):
      """
      Test assignment of collectDirs attribute, [] value.
      """
      collect = CollectConfig()
      self.failUnlessEqual(None, collect.excludePatterns)
      collect.excludePatterns = []
      self.failUnlessEqual([], collect.excludePatterns)

   def testConstructor_032(self):
      """
      Test assignment of collectDirs attribute, single valid entry.
      """
      collect = CollectConfig()
      self.failUnlessEqual(None, collect.excludePatterns)
      collect.excludePatterns = [CollectDir(absolutePath="/one"), ]
      self.failUnlessEqual([CollectDir(absolutePath="/one"), ], collect.excludePatterns)

   def testConstructor_033(self):
      """
      Test assignment of collectDirs attribute, multiple valid
      entries.
      """
      collect = CollectConfig()
      self.failUnlessEqual(None, collect.excludePatterns)
      collect.excludePatterns = [CollectDir(absolutePath="/one"), CollectDir(absolutePath="/two"), ]
      self.failUnlessEqual([CollectDir(absolutePath="/one"), CollectDir(absolutePath="/two"), ], collect.excludePatterns)

   def testConstructor_034(self):
      """
      Test assignment of collectDirs attribute, single invalid entry
      (None).
      """
      collect = CollectConfig()
      self.failUnlessEqual(None, collect.collectDirs)
      self.failUnlessAssignRaises(ValueError, collect, "collectDirs", [ None, ])
      self.failUnlessEqual(None, collect.collectDirs)

   def testConstructor_035(self):
      """
      Test assignment of collectDirs attribute, single invalid entry
      (not a CollectDir).
      """
      collect = CollectConfig()
      self.failUnlessEqual(None, collect.collectDirs)
      self.failUnlessAssignRaises(ValueError, collect, "collectDirs", [ "hello", ])
      self.failUnlessEqual(None, collect.collectDirs)

   def testConstructor_036(self):
      """
      Test assignment of collectDirs attribute, mixed valid and
      invalid entries.
      """
      collect = CollectConfig()
      self.failUnlessEqual(None, collect.collectDirs)
      self.failUnlessAssignRaises(ValueError, collect, "collectDirs", [ "hello", CollectDir(), ])
      self.failUnlessEqual(None, collect.collectDirs)


   ############################
   # Test comparison operators
   ############################

   def testComparison_001(self):
      """
      Test comparison of two identical objects, all attributes None.
      """
      pass

   def testComparison_002(self):
      """
      Test comparison of two identical objects, all attributes non-None.
      """
      pass

   def testComparison_003(self):
      """
      Test comparison of two differing objects, targetDir differs (one None).
      """
      pass

   def testComparison_004(self):
      """
      Test comparison of two differing objects, targetDir differs.
      """
      pass

   def testComparison_005(self):
      """
      Test comparison of two differing objects, collectMode differs (one None).
      """
      pass

   def testComparison_006(self):
      """
      Test comparison of two differing objects, collectMode differs.
      """
      pass

   def testComparison_007(self):
      """
      Test comparison of two differing objects, archiveMode differs (one None).
      """
      pass

   def testComparison_008(self):
      """
      Test comparison of two differing objects, archiveMode differs.
      """
      pass

   def testComparison_009(self):
      """
      Test comparison of two differing objects, ignoreFile differs (one None).
      """
      pass

   def testComparison_010(self):
      """
      Test comparison of two differing objects, ignoreFile differs.
      """
      pass

   def testComparison_011(self):
      """
      Test comparison of two differing objects, absoluteExcludePaths differs
      (one None, one empty).
      """
      pass

   def testComparison_012(self):
      """
      Test comparison of two differing objects, absoluteExcludePaths differs
      (one None, one not empty).
      """
      pass

   def testComparison_013(self):
      """
      Test comparison of two differing objects, absoluteExcludePaths differs
      (one empty, one not empty).
      """
      pass

   def testComparison_014(self):
      """
      Test comparison of two differing objects, absoluteExcludePaths differs
      (both not empty).
      """
      pass

   def testComparison_015(self):
      """
      Test comparison of two differing objects, excludePatterns differs (one
      None, one empty).
      """
      pass

   def testComparison_016(self):
      """
      Test comparison of two differing objects, excludePatterns differs (one
      None, one not empty).
      """
      pass

   def testComparison_017(self):
      """
      Test comparison of two differing objects, excludePatterns differs (one
      empty, one not empty).
      """
      pass

   def testComparison_018(self):
      """
      Test comparison of two differing objects, excludePatterns differs (both
      not empty).
      """
      pass

   def testComparison_019(self):
      """
      Test comparison of two differing objects, collectDirs differs (one
      None, one empty).
      """
      pass

   def testComparison_020(self):
      """
      Test comparison of two differing objects, collectDirs differs (one
      None, one not empty).
      """
      pass

   def testComparison_021(self):
      """
      Test comparison of two differing objects, collectDirs differs (one
      empty, one not empty).
      """
      pass

   def testComparison_022(self):
      """
      Test comparison of two differing objects, collectDirs differs (both
      not empty).
      """
      pass


########################
# TestStageConfig class
########################

class TestStageConfig(unittest.TestCase):

   """Tests for the StageConfig class."""

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

   def buildPath(self, components):
      """Builds a complete search path from a list of components."""
      components.insert(0, self.tmpdir)
      return buildPath(components)

   def failUnlessAssignRaises(self, exception, object, property, value):
      """Equivalent of L{failUnlessRaises}, but used for property assignments instead."""
      failUnlessAssignRaises(self, exception, object, property, value)


   ############################
   # Test __repr__ and __str__
   ############################

   def testStringFuncs_001(self):
      """
      Just make sure that the string functions don't have errors (i.e. bad variable names).
      """
      obj = StageConfig()
      obj.__repr__()
      obj.__str__()


   ##################################
   # Test constructor and attributes
   ##################################

   def testConstructor_001(self):
      """
      Test constructor with no values filled in.
      """
      stage = StageConfig()
      self.failUnlessEqual(None, stage.targetDir)
      self.failUnlessEqual(None, stage.localPeers)
      self.failUnlessEqual(None, stage.remotePeers)

   def testConstructor_002(self):
      """
      Test constructor with all values filled in, with valid values (empty lists).
      """
      stage = StageConfig("/whatever", [], [])
      self.failUnlessEqual("/whatever", stage.targetDir)
      self.failUnlessEqual([], stage.localPeers)
      self.failUnlessEqual([], stage.remotePeers)

   def testConstructor_003(self):
      """
      Test constructor with all values filled in, with valid values (non-empty lists).
      """
      stage = StageConfig("/whatever", [LocalPeer(), ], [RemotePeer(), ])
      self.failUnlessEqual("/whatever", stage.targetDir)
      self.failUnlessEqual([LocalPeer(), ], stage.localPeers)
      self.failUnlessEqual([RemotePeer(), ], stage.remotePeers)

   def testConstructor_004(self):
      """
      Test assignment of targetDir attribute, None value.
      """
      stage = StageConfig(targetDir="/whatever")
      self.failUnlessEqual("/whatever", stage.targetDir)
      stage.targetDir = None
      self.failUnlessEqual(None, stage.targetDir)

   def testConstructor_005(self):
      """
      Test assignment of targetDir attribute, valid value.
      """
      stage = StageConfig()
      self.failUnlessEqual(None, stage.targetDir)
      stage.targetDir = "/whatever"
      self.failUnlessEqual("/whatever", stage.targetDir)

   def testConstructor_006(self):
      """
      Test assignment of targetDir attribute, invalid value (empty).
      """
      stage = StageConfig()
      self.failUnlessEqual(None, stage.targetDir)
      self.failUnlessAssignRaises(ValueError, stage, "targetDir", "")
      self.failUnlessEqual(None, stage.targetDir)

   def testConstructor_007(self):
      """
      Test assignment of targetDir attribute, invalid value (non-absolute).
      """
      stage = StageConfig()
      self.failUnlessEqual(None, stage.targetDir)
      self.failUnlessAssignRaises(ValueError, stage, "targetDir", "stuff")
      self.failUnlessEqual(None, stage.targetDir)

   def testConstructor_008(self):
      """
      Test assignment of localPeers attribute, None value.
      """
      stage = StageConfig(localPeers=[])
      self.failUnlessEqual([], stage.localPeers)
      stage.localPeers = None
      self.failUnlessEqual(None, stage.localPeers)

   def testConstructor_009(self):
      """
      Test assignment of localPeers attribute, empty list.
      """
      stage = StageConfig()
      self.failUnlessEqual(None, stage.localPeers)
      stage.localPeers = []
      self.failUnlessEqual([], stage.localPeers)

   def testConstructor_010(self):
      """
      Test assignment of localPeers attribute, single valid entry.
      """
      stage = StageConfig()
      self.failUnlessEqual(None, stage.localPeers)
      stage.localPeers = [LocalPeer(), ]
      self.failUnlessEqual([LocalPeer(), ], stage.localPeers)

   def testConstructor_011(self):
      """
      Test assignment of localPeers attribute, multiple valid
      entries.
      """
      stage = StageConfig()
      self.failUnlessEqual(None, stage.localPeers)
      stage.localPeers = [LocalPeer(name="one"), LocalPeer(name="two"), ]
      self.failUnlessEqual([LocalPeer(name="one"), LocalPeer(name="two"), ], stage.localPeers)

   def testConstructor_012(self):
      """
      Test assignment of localPeers attribute, single invalid entry
      (None).
      """
      stage = StageConfig()
      self.failUnlessEqual(None, stage.localPeers)
      self.failUnlessAssignRaises(ValueError, stage, "localPeers", [None, ])
      self.failUnlessEqual(None, stage.localPeers)

   def testConstructor_013(self):
      """
      Test assignment of localPeers attribute, single invalid entry
      (not a LocalPeer).
      """
      stage = StageConfig()
      self.failUnlessEqual(None, stage.localPeers)
      self.failUnlessAssignRaises(ValueError, stage, "localPeers", [RemotePeer(), ])
      self.failUnlessEqual(None, stage.localPeers)

   def testConstructor_014(self):
      """
      Test assignment of localPeers attribute, mixed valid and
      invalid entries.
      """
      stage = StageConfig()
      self.failUnlessEqual(None, stage.localPeers)
      self.failUnlessAssignRaises(ValueError, stage, "localPeers", [LocalPeer(), RemotePeer(), ])
      self.failUnlessEqual(None, stage.localPeers)

   def testConstructor_015(self):
      """
      Test assignment of remotePeers attribute, None value.
      """
      stage = StageConfig(remotePeers=[])
      self.failUnlessEqual([], stage.remotePeers)
      stage.remotePeers = None
      self.failUnlessEqual(None, stage.remotePeers)

   def testConstructor_016(self):
      """
      Test assignment of remotePeers attribute, empty list.
      """
      stage = StageConfig()
      self.failUnlessEqual(None, stage.remotePeers)
      stage.remotePeers = []
      self.failUnlessEqual([], stage.remotePeers)

   def testConstructor_017(self):
      """
      Test assignment of remotePeers attribute, single valid entry.
      """
      stage = StageConfig()
      self.failUnlessEqual(None, stage.remotePeers)
      stage.remotePeers = [RemotePeer(name="one"), ]
      self.failUnlessEqual([RemotePeer(name="one"), ], stage.remotePeers)

   def testConstructor_018(self):
      """
      Test assignment of remotePeers attribute, multiple valid
      entries.
      """
      stage = StageConfig()
      self.failUnlessEqual(None, stage.remotePeers)
      stage.remotePeers = [RemotePeer(name="one"), RemotePeer(name="two"), ]
      self.failUnlessEqual([RemotePeer(name="one"), RemotePeer(name="two"), ], stage.remotePeers)

   def testConstructor_019(self):
      """
      Test assignment of remotePeers attribute, single invalid entry
      (None).
      """
      stage = StageConfig()
      self.failUnlessEqual(None, stage.remotePeers)
      self.failUnlessAssignRaises(ValueError, stage, "remotePeers", [None, ])
      self.failUnlessEqual(None, stage.remotePeers)

   def testConstructor_020(self):
      """
      Test assignment of remotePeers attribute, single invalid entry
      (not a RemotePeer).
      """
      stage = StageConfig()
      self.failUnlessEqual(None, stage.remotePeers)
      self.failUnlessAssignRaises(ValueError, stage, "remotePeers", [LocalPeer(), ])
      self.failUnlessEqual(None, stage.remotePeers)

   def testConstructor_021(self):
      """
      Test assignment of remotePeers attribute, mixed valid and
      invalid entries.
      """
      stage = StageConfig()
      self.failUnlessEqual(None, stage.remotePeers)
      self.failUnlessAssignRaises(ValueError, stage, "remotePeers", [LocalPeer(), RemotePeer(), ])
      self.failUnlessEqual(None, stage.remotePeers)


   ############################
   # Test comparison operators
   ############################

   def testComparison_001(self):
      """
      Test comparison of two identical objects, all attributes None.
      """
      stage1 = StageConfig()
      stage2 = StageConfig()
      self.failUnlessEqual(stage1, stage2)
      self.failUnless(stage1 == stage2)
      self.failUnless(not stage1 < stage2)
      self.failUnless(stage1 <= stage2)
      self.failUnless(not stage1 > stage2)
      self.failUnless(stage1 >= stage2)
      self.failUnless(not stage1 != stage2)

   def testComparison_002(self):
      """
      Test comparison of two identical objects, all attributes non-None (empty lists).
      """
      stage1 = StageConfig("/target", [], [])
      stage2 = StageConfig("/target", [], [])
      self.failUnlessEqual(stage1, stage2)
      self.failUnless(stage1 == stage2)
      self.failUnless(not stage1 < stage2)
      self.failUnless(stage1 <= stage2)
      self.failUnless(not stage1 > stage2)
      self.failUnless(stage1 >= stage2)
      self.failUnless(not stage1 != stage2)

   def testComparison_003(self):
      """
      Test comparison of two identical objects, all attributes non-None (non-empty lists).
      """
      stage1 = StageConfig("/target", [LocalPeer(), ], [RemotePeer(), ])
      stage2 = StageConfig("/target", [LocalPeer(), ], [RemotePeer(), ])
      self.failUnlessEqual(stage1, stage2)
      self.failUnless(stage1 == stage2)
      self.failUnless(not stage1 < stage2)
      self.failUnless(stage1 <= stage2)
      self.failUnless(not stage1 > stage2)
      self.failUnless(stage1 >= stage2)
      self.failUnless(not stage1 != stage2)

   def testComparison_004(self):
      """
      Test comparison of two differing objects, targetDir differs (one None).
      """
      stage1 = StageConfig()
      stage2 = StageConfig(targetDir="/whatever")
      self.failIfEqual(stage1, stage2)
      self.failUnless(not stage1 == stage2)
      self.failUnless(stage1 < stage2)
      self.failUnless(stage1 <= stage2)
      self.failUnless(not stage1 > stage2)
      self.failUnless(not stage1 >= stage2)
      self.failUnless(stage1 != stage2)

   def testComparison_005(self):
      """
      Test comparison of two differing objects, targetDir differs.
      """
      stage1 = StageConfig("/target1", [LocalPeer(), ], [RemotePeer(), ])
      stage2 = StageConfig("/target2", [LocalPeer(), ], [RemotePeer(), ])
      self.failIfEqual(stage1, stage2)
      self.failUnless(not stage1 == stage2)
      self.failUnless(stage1 < stage2)
      self.failUnless(stage1 <= stage2)
      self.failUnless(not stage1 > stage2)
      self.failUnless(not stage1 >= stage2)
      self.failUnless(stage1 != stage2)

   def testComparison_006(self):
      """
      Test comparison of two differing objects, localPeers differs (one None,
      one empty).
      """
      stage1 = StageConfig("/target", None, [RemotePeer(), ])
      stage2 = StageConfig("/target", [], [RemotePeer(), ])
      self.failIfEqual(stage1, stage2)
      self.failUnless(not stage1 == stage2)
      self.failUnless(stage1 < stage2)
      self.failUnless(stage1 <= stage2)
      self.failUnless(not stage1 > stage2)
      self.failUnless(not stage1 >= stage2)
      self.failUnless(stage1 != stage2)

   def testComparison_007(self):
      """
      Test comparison of two differing objects, localPeers differs (one None,
      one not empty).
      """
      stage1 = StageConfig("/target", None, [RemotePeer(), ])
      stage2 = StageConfig("/target", [LocalPeer(), ], [RemotePeer(), ])
      self.failIfEqual(stage1, stage2)
      self.failUnless(not stage1 == stage2)
      self.failUnless(stage1 < stage2)
      self.failUnless(stage1 <= stage2)
      self.failUnless(not stage1 > stage2)
      self.failUnless(not stage1 >= stage2)
      self.failUnless(stage1 != stage2)

   def testComparison_008(self):
      """
      Test comparison of two differing objects, localPeers differs (one empty,
      one not empty).
      """
      stage1 = StageConfig("/target", [], [RemotePeer(), ])
      stage2 = StageConfig("/target", [LocalPeer(), ], [RemotePeer(), ])
      self.failIfEqual(stage1, stage2)
      self.failUnless(not stage1 == stage2)
      self.failUnless(stage1 < stage2)
      self.failUnless(stage1 <= stage2)
      self.failUnless(not stage1 > stage2)
      self.failUnless(not stage1 >= stage2)
      self.failUnless(stage1 != stage2)

   def testComparison_009(self):
      """
      Test comparison of two differing objects, localPeers differs (both not
      empty).
      """
      stage1 = StageConfig("/target", [LocalPeer(name="one"), ], [RemotePeer(), ])
      stage2 = StageConfig("/target", [LocalPeer(name="two"), ], [RemotePeer(), ])
      self.failIfEqual(stage1, stage2)
      self.failUnless(not stage1 == stage2)
      self.failUnless(stage1 < stage2)
      self.failUnless(stage1 <= stage2)
      self.failUnless(not stage1 > stage2)
      self.failUnless(not stage1 >= stage2)
      self.failUnless(stage1 != stage2)

   def testComparison_010(self):
      """
      Test comparison of two differing objects, remotePeers differs (one None,
      one empty).
      """
      stage1 = StageConfig("/target", [LocalPeer(), ], None)
      stage2 = StageConfig("/target", [LocalPeer(), ], [])
      self.failIfEqual(stage1, stage2)
      self.failUnless(not stage1 == stage2)
      self.failUnless(stage1 < stage2)
      self.failUnless(stage1 <= stage2)
      self.failUnless(not stage1 > stage2)
      self.failUnless(not stage1 >= stage2)
      self.failUnless(stage1 != stage2)

   def testComparison_011(self):
      """
      Test comparison of two differing objects, remotePeers differs (one None,
      one not empty).
      """
      stage1 = StageConfig("/target", [LocalPeer(), ], None)
      stage2 = StageConfig("/target", [LocalPeer(), ], [RemotePeer(), ])
      self.failIfEqual(stage1, stage2)
      self.failUnless(not stage1 == stage2)
      self.failUnless(stage1 < stage2)
      self.failUnless(stage1 <= stage2)
      self.failUnless(not stage1 > stage2)
      self.failUnless(not stage1 >= stage2)
      self.failUnless(stage1 != stage2)

   def testComparison_012(self):
      """
      Test comparison of two differing objects, remotePeers differs (one empty,
      one not empty).
      """
      stage1 = StageConfig("/target", [LocalPeer(), ], [])
      stage2 = StageConfig("/target", [LocalPeer(), ], [RemotePeer(), ])
      self.failIfEqual(stage1, stage2)
      self.failUnless(not stage1 == stage2)
      self.failUnless(stage1 < stage2)
      self.failUnless(stage1 <= stage2)
      self.failUnless(not stage1 > stage2)
      self.failUnless(not stage1 >= stage2)
      self.failUnless(stage1 != stage2)

   def testComparison_013(self):
      """
      Test comparison of two differing objects, remotePeers differs (both not
      empty).
      """
      stage1 = StageConfig("/target", [LocalPeer(), ], [RemotePeer(name="two"), ])
      stage2 = StageConfig("/target", [LocalPeer(), ], [RemotePeer(name="one"), ])
      self.failIfEqual(stage1, stage2)
      self.failUnless(not stage1 == stage2)
      self.failUnless(not stage1 < stage2)
      self.failUnless(not stage1 <= stage2)
      self.failUnless(stage1 > stage2)
      self.failUnless(stage1 >= stage2)
      self.failUnless(stage1 != stage2)


########################
# TestStoreConfig class
########################

class TestStoreConfig(unittest.TestCase):

   """Tests for the StoreConfig class."""

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

   def buildPath(self, components):
      """Builds a complete search path from a list of components."""
      components.insert(0, self.tmpdir)
      return buildPath(components)

   def failUnlessAssignRaises(self, exception, object, property, value):
      """Equivalent of L{failUnlessRaises}, but used for property assignments instead."""
      failUnlessAssignRaises(self, exception, object, property, value)


   ############################
   # Test __repr__ and __str__
   ############################

   def testStringFuncs_001(self):
      """
      Just make sure that the string functions don't have errors (i.e. bad variable names).
      """
      obj = StoreConfig()
      obj.__repr__()
      obj.__str__()


   ##################################
   # Test constructor and attributes
   ##################################

   def testConstructor_001(self):
      """
      Test constructor with no values filled in.
      """
      store = StoreConfig()
      self.failUnlessEqual(None, store.sourceDir)
      self.failUnlessEqual(None, store.mediaType)
      self.failUnlessEqual(None, store.deviceType)
      self.failUnlessEqual(None, store.devicePath)
      self.failUnlessEqual(None, store.deviceScsiId)
      self.failUnlessEqual(None, store.driveSpeed)
      self.failUnlessEqual(False, store.checkData)
      self.failUnlessEqual(False, store.safeOverwrite)
      self.failUnlessEqual(None, store.capacityMode)

   def testConstructor_002(self):
      """
      Test constructor with all values filled in, with valid values.
      """
      store = StoreConfig("/source", "cdr-74", "cdwriter", "/dev/cdrw", "0,0,0", 4, True, True, "fail")
      self.failUnlessEqual("/source", store.sourceDir)
      self.failUnlessEqual("cdr-74", store.mediaType)
      self.failUnlessEqual("cdwriter", store.deviceType)
      self.failUnlessEqual("/dev/cdrw", store.devicePath)
      self.failUnlessEqual("0,0,0", store.deviceScsiId)
      self.failUnlessEqual(4, store.driveSpeed)
      self.failUnlessEqual(True, store.checkData)
      self.failUnlessEqual(True, store.safeOverwrite)
      self.failUnlessEqual("fail", store.capacityMode)

   def testConstructor_003(self):
      """
      Test assignment of sourceDir attribute, None value.
      """
      store = StoreConfig(sourceDir="/whatever")
      self.failUnlessEqual("/whatever", store.sourceDir)
      store.sourceDir = None
      self.failUnlessEqual(None, store.sourceDir)

   def testConstructor_004(self):
      """
      Test assignment of sourceDir attribute, valid value.
      """
      store = StoreConfig()
      self.failUnlessEqual(None, store.sourceDir)
      store.sourceDir = "/whatever"
      self.failUnlessEqual("/whatever", store.sourceDir)

   def testConstructor_005(self):
      """
      Test assignment of sourceDir attribute, invalid value (empty).
      """
      store = StoreConfig()
      self.failUnlessEqual(None, store.sourceDir)
      self.failUnlessAssignRaises(ValueError, store, "sourceDir", "")
      self.failUnlessEqual(None, store.sourceDir)

   def testConstructor_006(self):
      """
      Test assignment of sourceDir attribute, invalid value (non-absolute).
      """
      store = StoreConfig()
      self.failUnlessEqual(None, store.sourceDir)
      self.failUnlessAssignRaises(ValueError, store, "sourceDir", "bogus")
      self.failUnlessEqual(None, store.sourceDir)

   def testConstructor_007(self):
      """
      Test assignment of mediaType attribute, None value.
      """
      store = StoreConfig(mediaType="cdr-74")
      self.failUnlessEqual("cdr-74", store.mediaType)
      store.mediaType = None
      self.failUnlessEqual(None, store.mediaType)

   def testConstructor_008(self):
      """
      Test assignment of mediaType attribute, valid value.
      """
      store = StoreConfig()
      self.failUnlessEqual(None, store.mediaType)
      store.mediaType = "cdr-74"
      self.failUnlessEqual("cdr-74", store.mediaType)
      store.mediaType = "cdrw-74"
      self.failUnlessEqual("cdrw-74", store.mediaType)
      store.mediaType = "cdr-80"
      self.failUnlessEqual("cdr-80", store.mediaType)
      store.mediaType = "cdrw-80"
      self.failUnlessEqual("cdrw-80", store.mediaType)

   def testConstructor_009(self):
      """
      Test assignment of mediaType attribute, invalid value (empty).
      """
      store = StoreConfig()
      self.failUnlessEqual(None, store.mediaType)
      self.failUnlessAssignRaises(ValueError, store, "mediaType", "")
      self.failUnlessEqual(None, store.mediaType)

   def testConstructor_010(self):
      """
      Test assignment of mediaType attribute, invalid value (not in list).
      """
      store = StoreConfig()
      self.failUnlessEqual(None, store.mediaType)
      self.failUnlessAssignRaises(ValueError, store, "mediaType", "floppy")
      self.failUnlessEqual(None, store.mediaType)

   def testConstructor_011(self):
      """
      Test assignment of deviceType attribute, None value.
      """
      store = StoreConfig(deviceType="cdwriter")
      self.failUnlessEqual("cdwriter", store.deviceType)
      store.deviceType = None
      self.failUnlessEqual(None, store.deviceType)

   def testConstructor_012(self):
      """
      Test assignment of deviceType attribute, valid value.
      """
      store = StoreConfig()
      self.failUnlessEqual(None, store.deviceType)
      store.deviceType = "cdwriter"
      self.failUnlessEqual("cdwriter", store.deviceType)

   def testConstructor_013(self):
      """
      Test assignment of deviceType attribute, invalid value (empty).
      """
      store = StoreConfig()
      self.failUnlessEqual(None, store.deviceType)
      self.failUnlessAssignRaises(ValueError, store, "deviceType", "")
      self.failUnlessEqual(None, store.deviceType)

   def testConstructor_014(self):
      """
      Test assignment of deviceType attribute, invalid value (not in list).
      """
      store = StoreConfig()
      self.failUnlessEqual(None, store.deviceType)
      self.failUnlessAssignRaises(ValueError, store, "deviceType", "ftape")
      self.failUnlessEqual(None, store.deviceType)

   def testConstructor_015(self):
      """
      Test assignment of devicePath attribute, None value.
      """
      store = StoreConfig(devicePath="/dev/cdrw")
      self.failUnlessEqual("/dev/cdrw", store.devicePath)
      store.devicePath = None
      self.failUnlessEqual(None, store.devicePath)

   def testConstructor_016(self):
      """
      Test assignment of devicePath attribute, valid value.
      """
      store = StoreConfig()
      self.failUnlessEqual(None, store.devicePath)
      store.devicePath = "/dev/cdrw"
      self.failUnlessEqual("/dev/cdrw", store.devicePath)

   def testConstructor_017(self):
      """
      Test assignment of devicePath attribute, invalid value (empty).
      """
      store = StoreConfig()
      self.failUnlessEqual(None, store.devicePath)
      self.failUnlessAssignRaises(ValueError, store, "devicePath", "")
      self.failUnlessEqual(None, store.devicePath)

   def testConstructor_018(self):
      """
      Test assignment of devicePath attribute, invalid value (non-absolute).
      """
      store = StoreConfig()
      self.failUnlessEqual(None, store.devicePath)
      self.failUnlessAssignRaises(ValueError, store, "devicePath", "dev/cdrw")
      self.failUnlessEqual(None, store.devicePath)

   def testConstructor_019(self):
      """
      Test assignment of deviceScsiId attribute, None value.
      """
      store = StoreConfig(deviceScsiId="0,0,0")
      self.failUnlessEqual("0,0,0", store.deviceScsiId)
      store.deviceScsiId = None
      self.failUnlessEqual(None, store.deviceScsiId)

   def testConstructor_020(self):
      """
      Test assignment of deviceScsiId attribute, valid value.
      """
      store = StoreConfig()
      self.failUnlessEqual(None, store.deviceScsiId)
      store.deviceScsiId = "0,0,0"
      self.failUnlessEqual("0,0,0", store.deviceScsiId)
      store.deviceScsiId = "ATA:0,0,0"
      self.failUnlessEqual("ATA:0,0,0", store.deviceScsiId)

   def testConstructor_021(self):
      """
      Test assignment of deviceScsiId attribute, invalid value (empty).
      """
      store = StoreConfig()
      self.failUnlessEqual(None, store.deviceScsiId)
      self.failUnlessAssignRaises(ValueError, store, "deviceScsiId", "")
      self.failUnlessEqual(None, store.deviceScsiId)

   def testConstructor_022(self):
      """
      Test assignment of deviceScsiId attribute, invalid value (invalid id).
      """
      store = StoreConfig()
      self.failUnlessEqual(None, store.deviceScsiId)
      self.failUnlessAssignRaises(ValueError, store, "deviceScsiId", "ATB:0,0,0")
      self.failUnlessEqual(None, store.deviceScsiId)
      self.failUnlessAssignRaises(ValueError, store, "deviceScsiId", "1:2:3")
      self.failUnlessEqual(None, store.deviceScsiId)

   def testConstructor_023(self):
      """
      Test assignment of driveSpeed attribute, None value.
      """
      store = StoreConfig(driveSpeed=4)
      self.failUnlessEqual(4, store.driveSpeed)
      store.driveSpeed = None
      self.failUnlessEqual(None, store.driveSpeed)

   def testConstructor_024(self):
      """
      Test assignment of driveSpeed attribute, valid value.
      """
      store = StoreConfig()
      self.failUnlessEqual(None, store.driveSpeed)
      store.driveSpeed = 4
      self.failUnlessEqual(4, store.driveSpeed)
      store.driveSpeed = "12"
      self.failUnlessEqual(12, store.driveSpeed)

   def testConstructor_025(self):
      """
      Test assignment of driveSpeed attribute, invalid value (not an integer).
      """
      store = StoreConfig()
      self.failUnlessEqual(None, store.driveSpeed)
      self.failUnlessAssignRaises(ValueError, store, "driveSpeed", "blech")
      self.failUnlessEqual(None, store.driveSpeed)
      self.failUnlessAssignRaises(ValueError, store, "driveSpeed", CollectDir())
      self.failUnlessEqual(None, store.driveSpeed)

   def testConstructor_026(self):
      """
      Test assignment of checkData attribute, None value.
      """
      store = StoreConfig(checkData=True)
      self.failUnlessEqual(True, store.checkData)
      store.checkData = None
      self.failUnlessEqual(False, store.checkData)

   def testConstructor_027(self):
      """
      Test assignment of checkData attribute, valid value (real boolean).
      """
      store = StoreConfig()
      self.failUnlessEqual(False, store.checkData)
      store.checkData = True
      self.failUnlessEqual(True, store.checkData)
      store.checkData = False
      self.failUnlessEqual(False, store.checkData)

   def testConstructor_028(self):
      """
      Test assignment of checkData attribute, valid value (expression).
      """
      store = StoreConfig()
      self.failUnlessEqual(False, store.checkData)
      store.checkData = 0
      self.failUnlessEqual(False, store.checkData)
      store.checkData = []
      self.failUnlessEqual(False, store.checkData)
      store.checkData = None
      self.failUnlessEqual(False, store.checkData)
      store.checkData = ['a']
      self.failUnlessEqual(True, store.checkData)
      store.checkData = 3
      self.failUnlessEqual(True, store.checkData)

   def testConstructor_029(self):
      """
      Test assignment of safeOverwrite attribute, None value.
      """
      store = StoreConfig(safeOverwrite=True)
      self.failUnlessEqual(True, store.safeOverwrite)
      store.safeOverwrite = None
      self.failUnlessEqual(False, store.safeOverwrite)

   def testConstructor_030(self):
      """
      Test assignment of safeOverwrite attribute, valid value (real boolean).
      """
      store = StoreConfig()
      self.failUnlessEqual(False, store.safeOverwrite)
      store.safeOverwrite = True
      self.failUnlessEqual(True, store.safeOverwrite)
      store.safeOverwrite = False
      self.failUnlessEqual(False, store.safeOverwrite)

   def testConstructor_031(self):
      """
      Test assignment of safeOverwrite attribute, valid value (expression).
      """
      store = StoreConfig()
      self.failUnlessEqual(False, store.safeOverwrite)
      store.safeOverwrite = 0
      self.failUnlessEqual(False, store.safeOverwrite)
      store.safeOverwrite = []
      self.failUnlessEqual(False, store.safeOverwrite)
      store.safeOverwrite = None
      self.failUnlessEqual(False, store.safeOverwrite)
      store.safeOverwrite = ['a']
      self.failUnlessEqual(True, store.safeOverwrite)
      store.safeOverwrite = 3
      self.failUnlessEqual(True, store.safeOverwrite)

   def testConstructor_032(self):
      """
      Test assignment of capacityMode attribute, None value.
      """
      store = StoreConfig(capacityMode="fail")
      self.failUnlessEqual("fail", store.capacityMode)
      store.capacityMode = None
      self.failUnlessEqual(None, store.capacityMode)

   def testConstructor_033(self):
      """
      Test assignment of capacityMode attribute, valid value.
      """
      store = StoreConfig()
      self.failUnlessEqual(None, store.capacityMode)
      store.capacityMode = "fail"
      self.failUnlessEqual("fail", store.capacityMode)
      store.capacityMode = "discard"
      self.failUnlessEqual("discard", store.capacityMode)
      store.capacityMode = "overwrite"
      self.failUnlessEqual("overwrite", store.capacityMode)
      store.capacityMode = "rebuild"
      self.failUnlessEqual("rebuild", store.capacityMode)
      store.capacityMode = "rewrite"
      self.failUnlessEqual("rewrite", store.capacityMode)

   def testConstructor_034(self):
      """
      Test assignment of capacityMode attribute, invalid value (empty).
      """
      store = StoreConfig()
      self.failUnlessEqual(None, store.capacityMode)
      self.failUnlessAssignRaises(ValueError, store, "capacityMode", "")
      self.failUnlessEqual(None, store.capacityMode)

   def testConstructor_035(self):
      """
      Test assignment of capacityMode attribute, invalid value (not in list).
      """
      store = StoreConfig()
      self.failUnlessEqual(None, store.capacityMode)
      self.failUnlessAssignRaises(ValueError, store, "capacityMode", "giveup")
      self.failUnlessEqual(None, store.capacityMode)


   ############################
   # Test comparison operators
   ############################

   def testComparison_001(self):
      """
      Test comparison of two identical objects, all attributes None.
      """
      store1 = StoreConfig()
      store2 = StoreConfig()
      self.failUnlessEqual(store1, store2)
      self.failUnless(store1 == store2)
      self.failUnless(not store1 < store2)
      self.failUnless(store1 <= store2)
      self.failUnless(not store1 > store2)
      self.failUnless(store1 >= store2)
      self.failUnless(not store1 != store2)

   def testComparison_002(self):
      """
      Test comparison of two identical objects, all attributes non-None.
      """
      store1 = StoreConfig("/source", "cdr-74", "cdwriter", "/dev/cdrw", "0,0,0", 4, True, True, "fail")
      store2 = StoreConfig("/source", "cdr-74", "cdwriter", "/dev/cdrw", "0,0,0", 4, True, True, "fail")
      self.failUnlessEqual(store1, store2)
      self.failUnless(store1 == store2)
      self.failUnless(not store1 < store2)
      self.failUnless(store1 <= store2)
      self.failUnless(not store1 > store2)
      self.failUnless(store1 >= store2)
      self.failUnless(not store1 != store2)

   def testComparison_003(self):
      """
      Test comparison of two differing objects, sourceDir differs (one None).
      """
      store1 = StoreConfig()
      store2 = StoreConfig(sourceDir="/whatever")
      self.failIfEqual(store1, store2)
      self.failUnless(not store1 == store2)
      self.failUnless(store1 < store2)
      self.failUnless(store1 <= store2)
      self.failUnless(not store1 > store2)
      self.failUnless(not store1 >= store2)
      self.failUnless(store1 != store2)

   def testComparison_004(self):
      """
      Test comparison of two differing objects, sourceDir differs.
      """
      store1 = StoreConfig("/source1", "cdr-74", "cdwriter", "/dev/cdrw", "0,0,0", 4, True, True, "fail")
      store2 = StoreConfig("/source2", "cdr-74", "cdwriter", "/dev/cdrw", "0,0,0", 4, True, True, "fail")
      self.failIfEqual(store1, store2)
      self.failUnless(not store1 == store2)
      self.failUnless(store1 < store2)
      self.failUnless(store1 <= store2)
      self.failUnless(not store1 > store2)
      self.failUnless(not store1 >= store2)
      self.failUnless(store1 != store2)

   def testComparison_005(self):
      """
      Test comparison of two differing objects, mediaType differs (one None).
      """
      store1 = StoreConfig()
      store2 = StoreConfig(mediaType="cdr-74")
      self.failIfEqual(store1, store2)
      self.failUnless(not store1 == store2)
      self.failUnless(store1 < store2)
      self.failUnless(store1 <= store2)
      self.failUnless(not store1 > store2)
      self.failUnless(not store1 >= store2)
      self.failUnless(store1 != store2)

   def testComparison_006(self):
      """
      Test comparison of two differing objects, mediaType differs.
      """
      store1 = StoreConfig("/source", "cdrw-74", "cdwriter", "/dev/cdrw", "0,0,0", 4, True, True, "fail")
      store2 = StoreConfig("/source", "cdr-74", "cdwriter", "/dev/cdrw", "0,0,0", 4, True, True, "fail")
      self.failIfEqual(store1, store2)
      self.failUnless(not store1 == store2)
      self.failUnless(not store1 < store2)
      self.failUnless(not store1 <= store2)
      self.failUnless(store1 > store2)
      self.failUnless(store1 >= store2)
      self.failUnless(store1 != store2)

   def testComparison_007(self):
      """
      Test comparison of two differing objects, deviceType differs (one None).
      """
      store1 = StoreConfig()
      store2 = StoreConfig(deviceType="cdwriter")
      self.failIfEqual(store1, store2)
      self.failUnless(not store1 == store2)
      self.failUnless(store1 < store2)
      self.failUnless(store1 <= store2)
      self.failUnless(not store1 > store2)
      self.failUnless(not store1 >= store2)
      self.failUnless(store1 != store2)

   def testComparison_008(self):
      """
      Test comparison of two differing objects, devicePath differs (one None).
      """
      store1 = StoreConfig()
      store2 = StoreConfig(devicePath="/dev/cdrw")
      self.failIfEqual(store1, store2)
      self.failUnless(not store1 == store2)
      self.failUnless(store1 < store2)
      self.failUnless(store1 <= store2)
      self.failUnless(not store1 > store2)
      self.failUnless(not store1 >= store2)
      self.failUnless(store1 != store2)

   def testComparison_009(self):
      """
      Test comparison of two differing objects, devicePath differs.
      """
      store1 = StoreConfig("/source", "cdr-74", "cdwriter", "/dev/cdrw", "0,0,0", 4, True, True, "fail")
      store2 = StoreConfig("/source", "cdr-74", "cdwriter", "/dev/hdd", "0,0,0", 4, True, True, "fail")
      self.failIfEqual(store1, store2)
      self.failUnless(not store1 == store2)
      self.failUnless(store1 < store2)
      self.failUnless(store1 <= store2)
      self.failUnless(not store1 > store2)
      self.failUnless(not store1 >= store2)
      self.failUnless(store1 != store2)

   def testComparison_010(self):
      """
      Test comparison of two differing objects, deviceScsiId differs (one None).
      """
      store1 = StoreConfig()
      store2 = StoreConfig(deviceScsiId="0,0,0")
      self.failIfEqual(store1, store2)
      self.failUnless(not store1 == store2)
      self.failUnless(store1 < store2)
      self.failUnless(store1 <= store2)
      self.failUnless(not store1 > store2)
      self.failUnless(not store1 >= store2)
      self.failUnless(store1 != store2)

   def testComparison_011(self):
      """
      Test comparison of two differing objects, deviceScsiId differs.
      """
      store1 = StoreConfig("/source", "cdr-74", "cdwriter", "/dev/cdrw", "0,0,0", 4, True, True, "fail")
      store2 = StoreConfig("/source", "cdr-74", "cdwriter", "/dev/cdrw", "ATA:0,0,0", 4, True, True, "fail")
      self.failIfEqual(store1, store2)
      self.failUnless(not store1 == store2)
      self.failUnless(store1 < store2)
      self.failUnless(store1 <= store2)
      self.failUnless(not store1 > store2)
      self.failUnless(not store1 >= store2)
      self.failUnless(store1 != store2)

   def testComparison_012(self):
      """
      Test comparison of two differing objects, driveSpeed differs (one None).
      """
      store1 = StoreConfig()
      store2 = StoreConfig(driveSpeed=3)
      self.failIfEqual(store1, store2)
      self.failUnless(not store1 == store2)
      self.failUnless(store1 < store2)
      self.failUnless(store1 <= store2)
      self.failUnless(not store1 > store2)
      self.failUnless(not store1 >= store2)
      self.failUnless(store1 != store2)

   def testComparison_013(self):
      """
      Test comparison of two differing objects, driveSpeed differs.
      """
      store1 = StoreConfig("/source", "cdr-74", "cdwriter", "/dev/cdrw", "0,0,0", 1, True, True, "fail")
      store2 = StoreConfig("/source", "cdr-74", "cdwriter", "/dev/cdrw", "0,0,0", 4, True, True, "fail")
      self.failIfEqual(store1, store2)
      self.failUnless(not store1 == store2)
      self.failUnless(store1 < store2)
      self.failUnless(store1 <= store2)
      self.failUnless(not store1 > store2)
      self.failUnless(not store1 >= store2)
      self.failUnless(store1 != store2)

   def testComparison_014(self):
      """
      Test comparison of two differing objects, checkData differs.
      """
      store1 = StoreConfig("/source", "cdr-74", "cdwriter", "/dev/cdrw", "0,0,0", 4, False, True, "fail")
      store2 = StoreConfig("/source", "cdr-74", "cdwriter", "/dev/cdrw", "0,0,0", 4, True, True, "fail")
      self.failIfEqual(store1, store2)
      self.failUnless(not store1 == store2)
      self.failUnless(store1 < store2)
      self.failUnless(store1 <= store2)
      self.failUnless(not store1 > store2)
      self.failUnless(not store1 >= store2)
      self.failUnless(store1 != store2)

   def testComparison_015(self):
      """
      Test comparison of two differing objects, safeOverwrite differs.
      """
      store1 = StoreConfig("/source", "cdr-74", "cdwriter", "/dev/cdrw", "0,0,0", 4, True, True, "fail")
      store2 = StoreConfig("/source", "cdr-74", "cdwriter", "/dev/cdrw", "0,0,0", 4, True, False, "fail")
      self.failIfEqual(store1, store2)
      self.failUnless(not store1 == store2)
      self.failUnless(not store1 < store2)
      self.failUnless(not store1 <= store2)
      self.failUnless(store1 > store2)
      self.failUnless(store1 >= store2)
      self.failUnless(store1 != store2)

   def testComparison_016(self):
      """
      Test comparison of two differing objects, capacityMode differs (one None).
      """
      store1 = StoreConfig()
      store2 = StoreConfig(capacityMode="fail")
      self.failIfEqual(store1, store2)
      self.failUnless(not store1 == store2)
      self.failUnless(store1 < store2)
      self.failUnless(store1 <= store2)
      self.failUnless(not store1 > store2)
      self.failUnless(not store1 >= store2)
      self.failUnless(store1 != store2)

   def testComparison_017(self):
      """
      Test comparison of two differing objects, capacityMode differs.
      """
      store1 = StoreConfig("/source", "cdr-74", "cdwriter", "/dev/cdrw", "0,0,0", 4, True, True, "overwrite")
      store2 = StoreConfig("/source", "cdr-74", "cdwriter", "/dev/cdrw", "0,0,0", 4, True, True, "fail")
      self.failIfEqual(store1, store2)
      self.failUnless(not store1 == store2)
      self.failUnless(not store1 < store2)
      self.failUnless(not store1 <= store2)
      self.failUnless(store1 > store2)
      self.failUnless(store1 >= store2)
      self.failUnless(store1 != store2)


########################
# TestPurgeConfig class
########################

class TestPurgeConfig(unittest.TestCase):

   """Tests for the PurgeConfig class."""

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

   def buildPath(self, components):
      """Builds a complete search path from a list of components."""
      components.insert(0, self.tmpdir)
      return buildPath(components)

   def failUnlessAssignRaises(self, exception, object, property, value):
      """Equivalent of L{failUnlessRaises}, but used for property assignments instead."""
      failUnlessAssignRaises(self, exception, object, property, value)


   ############################
   # Test __repr__ and __str__
   ############################

   def testStringFuncs_001(self):
      """
      Just make sure that the string functions don't have errors (i.e. bad variable names).
      """
      obj = PurgeConfig()
      obj.__repr__()
      obj.__str__()


   ##################################
   # Test constructor and attributes
   ##################################

   def testConstructor_001(self):
      """
      Test constructor with no values filled in.
      """
      purge = PurgeConfig()
      self.failUnlessEqual(None, purge.purgeDirs)

   def testConstructor_002(self):
      """
      Test constructor with all values filled in, with valid values (empty list).
      """
      purge = PurgeConfig([])
      self.failUnlessEqual([], purge.purgeDirs)

   def testConstructor_003(self):
      """
      Test constructor with all values filled in, with valid values (non-empty list).
      """
      purge = PurgeConfig([PurgeDir(), ])
      self.failUnlessEqual([PurgeDir(), ], purge.purgeDirs)

   def testConstructor_004(self):
      """
      Test assignment of purgeDirs attribute, None value.
      """
      purge = PurgeConfig([])
      self.failUnlessEqual([], purge.purgeDirs)
      purge.purgeDirs = None
      self.failUnlessEqual(None, purge.purgeDirs)

   def testConstructor_005(self):
      """
      Test assignment of purgeDirs attribute, [] value.
      """
      purge = PurgeConfig()
      self.failUnlessEqual(None, purge.purgeDirs)
      purge.purgeDirs = []
      self.failUnlessEqual([], purge.purgeDirs)

   def testConstructor_006(self):
      """
      Test assignment of purgeDirs attribute, single valid entry.
      """
      purge = PurgeConfig()
      self.failUnlessEqual(None, purge.purgeDirs)
      purge.purgeDirs = [PurgeDir(), ]
      self.failUnlessEqual([PurgeDir(), ], purge.purgeDirs)

   def testConstructor_007(self):
      """
      Test assignment of purgeDirs attribute, multiple valid entries.
      """
      purge = PurgeConfig()
      self.failUnlessEqual(None, purge.purgeDirs)
      purge.purgeDirs = [PurgeDir("/one"), PurgeDir("/two"), ]
      self.failUnlessEqual([PurgeDir("/one"), PurgeDir("/two"), ], purge.purgeDirs)

   def testConstructor_009(self):
      """
      Test assignment of purgeDirs attribute, single invalid entry (not a
      PurgeDir).
      """
      purge = PurgeConfig()
      self.failUnlessEqual(None, purge.purgeDirs)
      self.failUnlessAssignRaises(ValueError, purge, "purgeDirs", [ RemotePeer(), ])
      self.failUnlessEqual(None, purge.purgeDirs)

   def testConstructor_010(self):
      """
      Test assignment of purgeDirs attribute, mixed valid and invalid entries.
      """
      purge = PurgeConfig()
      self.failUnlessEqual(None, purge.purgeDirs)
      self.failUnlessAssignRaises(ValueError, purge, "purgeDirs", [ PurgeDir(), RemotePeer(), ])
      self.failUnlessEqual(None, purge.purgeDirs)


   ############################
   # Test comparison operators
   ############################

   def testComparison_001(self):
      """
      Test comparison of two identical objects, all attributes None.
      """
      purge1 = PurgeConfig()
      purge2 = PurgeConfig()
      self.failUnlessEqual(purge1, purge2)
      self.failUnless(purge1 == purge2)
      self.failUnless(not purge1 < purge2)
      self.failUnless(purge1 <= purge2)
      self.failUnless(not purge1 > purge2)
      self.failUnless(purge1 >= purge2)
      self.failUnless(not purge1 != purge2)

   def testComparison_002(self):
      """
      Test comparison of two identical objects, all attributes non-None (empty
      lists).
      """
      purge1 = PurgeConfig([])
      purge2 = PurgeConfig([])
      self.failUnlessEqual(purge1, purge2)
      self.failUnless(purge1 == purge2)
      self.failUnless(not purge1 < purge2)
      self.failUnless(purge1 <= purge2)
      self.failUnless(not purge1 > purge2)
      self.failUnless(purge1 >= purge2)
      self.failUnless(not purge1 != purge2)

   def testComparison_003(self):
      """
      Test comparison of two identical objects, all attributes non-None
      (non-empty lists).
      """
      purge1 = PurgeConfig([PurgeDir(), ])
      purge2 = PurgeConfig([PurgeDir(), ])
      self.failUnlessEqual(purge1, purge2)
      self.failUnless(purge1 == purge2)
      self.failUnless(not purge1 < purge2)
      self.failUnless(purge1 <= purge2)
      self.failUnless(not purge1 > purge2)
      self.failUnless(purge1 >= purge2)
      self.failUnless(not purge1 != purge2)

   def testComparison_004(self):
      """
      Test comparison of two differing objects, purgeDirs differs (one None,
      one empty).
      """
      purge1 = PurgeConfig(None)
      purge2 = PurgeConfig([])
      self.failIfEqual(purge1, purge2)
      self.failUnless(not purge1 == purge2)
      self.failUnless(purge1 < purge2)
      self.failUnless(purge1 <= purge2)
      self.failUnless(not purge1 > purge2)
      self.failUnless(not purge1 >= purge2)
      self.failUnless(purge1 != purge2)

   def testComparison_005(self):
      """
      Test comparison of two differing objects, purgeDirs differs (one None,
      one not empty).
      """
      purge1 = PurgeConfig(None)
      purge2 = PurgeConfig([PurgeDir(), ])
      self.failIfEqual(purge1, purge2)
      self.failUnless(not purge1 == purge2)
      self.failUnless(purge1 < purge2)
      self.failUnless(purge1 <= purge2)
      self.failUnless(not purge1 > purge2)
      self.failUnless(not purge1 >= purge2)
      self.failUnless(purge1 != purge2)

   def testComparison_006(self):
      """
      Test comparison of two differing objects, purgeDirs differs (one empty,
      one not empty).
      """
      purge1 = PurgeConfig([])
      purge2 = PurgeConfig([PurgeDir(), ])
      self.failIfEqual(purge1, purge2)
      self.failUnless(not purge1 == purge2)
      self.failUnless(purge1 < purge2)
      self.failUnless(purge1 <= purge2)
      self.failUnless(not purge1 > purge2)
      self.failUnless(not purge1 >= purge2)
      self.failUnless(purge1 != purge2)

   def testComparison_007(self):
      """
      Test comparison of two differing objects, purgeDirs differs (both not
      empty).
      """
      purge1 = PurgeConfig([PurgeDir("/two"), ])
      purge2 = PurgeConfig([PurgeDir("/one"), ])
      self.failIfEqual(purge1, purge2)
      self.failUnless(not purge1 == purge2)
      self.failUnless(not purge1 < purge2)
      self.failUnless(not purge1 <= purge2)
      self.failUnless(purge1 > purge2)
      self.failUnless(purge1 >= purge2)
      self.failUnless(purge1 != purge2)


###################
# TestConfig class
###################

class TestConfig(unittest.TestCase):

   """Tests for the Config class."""

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

   def buildPath(self, components):
      """Builds a complete search path from a list of components."""
      components.insert(0, self.tmpdir)
      return buildPath(components)

   def failUnlessAssignRaises(self, exception, object, property, value):
      """Equivalent of L{failUnlessRaises}, but used for property assignments instead."""
      failUnlessAssignRaises(self, exception, object, property, value)


   ############################
   # Test __repr__ and __str__
   ############################

   def testStringFuncs_001(self):
      """
      Just make sure that the string functions don't have errors (i.e. bad variable names).
      """
      obj = Config()
      obj.__repr__()
      obj.__str__()


   #####################################################
   # Test basic constructor and attribute functionality
   #####################################################

   def testConstructor_001(self):
      """
      Test empty constructor, validate=False.
      """
      config = Config(validate=False)
      self.failUnlessEqual(None, config.reference)
      self.failUnlessEqual(None, config.options)
      self.failUnlessEqual(None, config.collect)
      self.failUnlessEqual(None, config.stage)
      self.failUnlessEqual(None, config.store)
      self.failUnlessEqual(None, config.purge)

   def testConstructor_002(self):
      """
      Test empty constructor, validate=True.
      """
      config = Config(validate=True)
      self.failUnlessEqual(None, config.reference)
      self.failUnlessEqual(None, config.options)
      self.failUnlessEqual(None, config.collect)
      self.failUnlessEqual(None, config.stage)
      self.failUnlessEqual(None, config.store)
      self.failUnlessEqual(None, config.purge)

   def testConstructor_003(self):
      """
      Test with empty config document as both data and file, validate=False.
      """
      path = self.resources["cback.conf.2"]
      contents = open(path).read()
      self.failUnlessRaises(ValueError, Config, xmlData=contents, xmlPath=path, validate=False)

   def testConstructor_004(self):
      """
      Test with empty config document as data, validate=False.
      """
      path = self.resources["cback.conf.2"]
      contents = open(path).read()
      config = Config(xmlData=contents, validate=False)
      self.failUnlessEqual(None, config.reference)
      self.failUnlessEqual(None, config.options)
      self.failUnlessEqual(None, config.collect)
      self.failUnlessEqual(None, config.stage)
      self.failUnlessEqual(None, config.store)
      self.failUnlessEqual(None, config.purge)

   def testConstructor_005(self):
      """
      Test with empty config document in a file, validate=False.
      """
      path = self.resources["cback.conf.2"]
      config = Config(xmlPath=path, validate=False)
      self.failUnlessEqual(None, config.reference)
      self.failUnlessEqual(None, config.options)
      self.failUnlessEqual(None, config.collect)
      self.failUnlessEqual(None, config.stage)
      self.failUnlessEqual(None, config.store)
      self.failUnlessEqual(None, config.purge)

   def testConstructor_006(self):
      """
      Test assignment of reference attribute, None value.
      """
      config = Config()
      config.reference = None
      self.failUnlessEqual(None, config.reference)

   def testConstructor_007(self):
      """
      Test assignment of reference attribute, valid value.
      """
      config = Config()
      config.reference = ReferenceConfig()
      self.failUnlessEqual(ReferenceConfig(), config.reference)

   def testConstructor_008(self):
      """
      Test assignment of reference attribute, invalid value (not ReferenceConfig).
      """
      config = Config()
      self.failUnlessAssignRaises(ValueError, config, "reference", CollectDir())

   def testConstructor_009(self):
      """
      Test assignment of options attribute, None value.
      """
      config = Config()
      config.options = None
      self.failUnlessEqual(None, config.options)

   def testConstructor_010(self):
      """
      Test assignment of options attribute, valid value.
      """
      config = Config()
      config.options = OptionsConfig()
      self.failUnlessEqual(OptionsConfig(), config.options)

   def testConstructor_011(self):
      """
      Test assignment of options attribute, invalid value (not OptionsConfig).
      """
      config = Config()
      self.failUnlessAssignRaises(ValueError, config, "options", CollectDir())

   def testConstructor_012(self):
      """
      Test assignment of collect attribute, None value.
      """
      config = Config()
      config.collect = None
      self.failUnlessEqual(None, config.collect)

   def testConstructor_013(self):
      """
      Test assignment of collect attribute, valid value.
      """
      config = Config()
      config.collect = CollectConfig()
      self.failUnlessEqual(CollectConfig(), config.collect)

   def testConstructor_014(self):
      """
      Test assignment of collect attribute, invalid value (not CollectConfig).
      """
      config = Config()
      self.failUnlessAssignRaises(ValueError, config, "collect", CollectDir())

   def testConstructor_015(self):
      """
      Test assignment of stage attribute, None value.
      """
      config = Config()
      config.stage = None
      self.failUnlessEqual(None, config.stage)

   def testConstructor_016(self):
      """
      Test assignment of stage attribute, valid value.
      """
      config = Config()
      config.stage = StageConfig()
      self.failUnlessEqual(StageConfig(), config.stage)

   def testConstructor_017(self):
      """
      Test assignment of stage attribute, invalid value (not StageConfig).
      """
      config = Config()
      self.failUnlessAssignRaises(ValueError, config, "stage", CollectDir())

   def testConstructor_018(self):
      """
      Test assignment of store attribute, None value.
      """
      config = Config()
      config.store = None
      self.failUnlessEqual(None, config.store)

   def testConstructor_019(self):
      """
      Test assignment of store attribute, valid value.
      """
      config = Config()
      config.store = StoreConfig()
      self.failUnlessEqual(StoreConfig(), config.store)

   def testConstructor_020(self):
      """
      Test assignment of store attribute, invalid value (not StoreConfig).
      """
      config = Config()
      self.failUnlessAssignRaises(ValueError, config, "store", CollectDir())

   def testConstructor_021(self):
      """
      Test assignment of purge attribute, None value.
      """
      config = Config()
      config.purge = None
      self.failUnlessEqual(None, config.purge)

   def testConstructor_022(self):
      """
      Test assignment of purge attribute, valid value.
      """
      config = Config()
      config.purge = PurgeConfig()
      self.failUnlessEqual(PurgeConfig(), config.purge)

   def testConstructor_023(self):
      """
      Test assignment of purge attribute, invalid value (not PurgeConfig).
      """
      config = Config()
      self.failUnlessAssignRaises(ValueError, config, "purge", CollectDir())


   ############################
   # Test comparison operators
   ############################

   def testComparison_001(self):
      """
      Test comparison of two identical objects, all attributes None.
      """
      config1 = Config()
      config2 = Config()
      self.failUnlessEqual(config1, config2)
      self.failUnless(config1 == config2)
      self.failUnless(not config1 < config2)
      self.failUnless(config1 <= config2)
      self.failUnless(not config1 > config2)
      self.failUnless(config1 >= config2)
      self.failUnless(not config1 != config2)

   def testComparison_002(self):
      """
      Test comparison of two identical objects, all attributes non-None.
      """
      config1 = Config()
      config1.reference = ReferenceConfig()
      config1.options = OptionsConfig()
      config1.collect = CollectConfig()
      config1.stage = StageConfig()
      config1.store = StoreConfig()
      config1.purge = PurgeConfig()

      config2 = Config()
      config2.reference = ReferenceConfig()
      config2.options = OptionsConfig()
      config2.collect = CollectConfig()
      config2.stage = StageConfig()
      config2.store = StoreConfig()
      config2.purge = PurgeConfig()

      self.failUnlessEqual(config1, config2)
      self.failUnless(config1 == config2)
      self.failUnless(not config1 < config2)
      self.failUnless(config1 <= config2)
      self.failUnless(not config1 > config2)
      self.failUnless(config1 >= config2)
      self.failUnless(not config1 != config2)

   def testComparison_003(self):
      """
      Test comparison of two differing objects, reference differs (one None).
      """
      config1 = Config()
      config2 = Config()
      config2.reference = ReferenceConfig()
      self.failIfEqual(config1, config2)
      self.failUnless(not config1 == config2)
      self.failUnless(config1 < config2)
      self.failUnless(config1 <= config2)
      self.failUnless(not config1 > config2)
      self.failUnless(not config1 >= config2)
      self.failUnless(config1 != config2)

   def testComparison_004(self):
      """
      Test comparison of two differing objects, reference differs.
      """
      config1 = Config()
      config1.reference = ReferenceConfig(author="one")
      config1.options = OptionsConfig()
      config1.collect = CollectConfig()
      config1.stage = StageConfig()
      config1.store = StoreConfig()
      config1.purge = PurgeConfig()

      config2 = Config()
      config2.reference = ReferenceConfig(author="two")
      config2.options = OptionsConfig()
      config2.collect = CollectConfig()
      config2.stage = StageConfig()
      config2.store = StoreConfig()
      config2.purge = PurgeConfig()

      self.failIfEqual(config1, config2)
      self.failUnless(not config1 == config2)
      self.failUnless(config1 < config2)
      self.failUnless(config1 <= config2)
      self.failUnless(not config1 > config2)
      self.failUnless(not config1 >= config2)
      self.failUnless(config1 != config2)

   def testComparison_005(self):
      """
      Test comparison of two differing objects, options differs (one None).
      """
      config1 = Config()
      config2 = Config()
      config2.options = OptionsConfig()
      self.failIfEqual(config1, config2)
      self.failUnless(not config1 == config2)
      self.failUnless(config1 < config2)
      self.failUnless(config1 <= config2)
      self.failUnless(not config1 > config2)
      self.failUnless(not config1 >= config2)
      self.failUnless(config1 != config2)

   def testComparison_006(self):
      """
      Test comparison of two differing objects, options differs.
      """
      config1 = Config()
      config1.reference = ReferenceConfig()
      config1.options = OptionsConfig(startingDay="tuesday")
      config1.collect = CollectConfig()
      config1.stage = StageConfig()
      config1.store = StoreConfig()
      config1.purge = PurgeConfig()

      config2 = Config()
      config2.reference = ReferenceConfig()
      config2.options = OptionsConfig(startingDay="monday")
      config2.collect = CollectConfig()
      config2.stage = StageConfig()
      config2.store = StoreConfig()
      config2.purge = PurgeConfig()

      self.failIfEqual(config1, config2)
      self.failUnless(not config1 == config2)
      self.failUnless(not config1 < config2)
      self.failUnless(not config1 <= config2)
      self.failUnless(config1 > config2)
      self.failUnless(config1 >= config2)
      self.failUnless(config1 != config2)

   def testComparison_007(self):
      """
      Test comparison of two differing objects, collect differs (one None).
      """
      config1 = Config()
      config2 = Config()
      config2.collect = CollectConfig()
      self.failIfEqual(config1, config2)
      self.failUnless(not config1 == config2)
      self.failUnless(config1 < config2)
      self.failUnless(config1 <= config2)
      self.failUnless(not config1 > config2)
      self.failUnless(not config1 >= config2)
      self.failUnless(config1 != config2)

   def testComparison_008(self):
      """
      Test comparison of two differing objects, collect differs.
      """
      config1 = Config()
      config1.reference = ReferenceConfig()
      config1.options = OptionsConfig()
      config1.collect = CollectConfig(collectMode="daily")
      config1.stage = StageConfig()
      config1.store = StoreConfig()
      config1.purge = PurgeConfig()

      config2 = Config()
      config2.reference = ReferenceConfig()
      config2.options = OptionsConfig()
      config2.collect = CollectConfig(collectMode="incr")
      config2.stage = StageConfig()
      config2.store = StoreConfig()
      config2.purge = PurgeConfig()

      self.failIfEqual(config1, config2)
      self.failUnless(not config1 == config2)
      self.failUnless(config1 < config2)
      self.failUnless(config1 <= config2)
      self.failUnless(not config1 > config2)
      self.failUnless(not config1 >= config2)
      self.failUnless(config1 != config2)

   def testComparison_009(self):
      """
      Test comparison of two differing objects, stage differs (one None).
      """
      config1 = Config()
      config2 = Config()
      config2.stage = StageConfig()
      self.failIfEqual(config1, config2)
      self.failUnless(not config1 == config2)
      self.failUnless(config1 < config2)
      self.failUnless(config1 <= config2)
      self.failUnless(not config1 > config2)
      self.failUnless(not config1 >= config2)
      self.failUnless(config1 != config2)

   def testComparison_010(self):
      """
      Test comparison of two differing objects, stage differs.
      """
      config1 = Config()
      config1.reference = ReferenceConfig()
      config1.options = OptionsConfig()
      config1.collect = CollectConfig()
      config1.stage = StageConfig(targetDir="/something")
      config1.store = StoreConfig()
      config1.purge = PurgeConfig()

      config2 = Config()
      config2.reference = ReferenceConfig()
      config2.options = OptionsConfig()
      config2.collect = CollectConfig()
      config2.stage = StageConfig(targetDir="/whatever")
      config2.store = StoreConfig()
      config2.purge = PurgeConfig()

      self.failIfEqual(config1, config2)
      self.failUnless(not config1 == config2)
      self.failUnless(config1 < config2)
      self.failUnless(config1 <= config2)
      self.failUnless(not config1 > config2)
      self.failUnless(not config1 >= config2)
      self.failUnless(config1 != config2)

   def testComparison_011(self):
      """
      Test comparison of two differing objects, store differs (one None).
      """
      config1 = Config()
      config2 = Config()
      config2.store = StoreConfig()
      self.failIfEqual(config1, config2)
      self.failUnless(not config1 == config2)
      self.failUnless(config1 < config2)
      self.failUnless(config1 <= config2)
      self.failUnless(not config1 > config2)
      self.failUnless(not config1 >= config2)
      self.failUnless(config1 != config2)

   def testComparison_012(self):
      """
      Test comparison of two differing objects, store differs.
      """
      config1 = Config()
      config1.reference = ReferenceConfig()
      config1.options = OptionsConfig()
      config1.collect = CollectConfig()
      config1.stage = StageConfig()
      config1.store = StoreConfig(deviceScsiId="ATA:0,0,0")
      config1.purge = PurgeConfig()

      config2 = Config()
      config2.reference = ReferenceConfig()
      config2.options = OptionsConfig()
      config2.collect = CollectConfig()
      config2.stage = StageConfig()
      config2.store = StoreConfig(deviceScsiId="0,0,0")
      config2.purge = PurgeConfig()

      self.failIfEqual(config1, config2)
      self.failUnless(not config1 == config2)
      self.failUnless(not config1 < config2)
      self.failUnless(not config1 <= config2)
      self.failUnless(config1 > config2)
      self.failUnless(config1 >= config2)
      self.failUnless(config1 != config2)

   def testComparison_013(self):
      """
      Test comparison of two differing objects, purge differs (one None).
      """
      config1 = Config()
      config2 = Config()
      config2.purge = PurgeConfig()
      self.failIfEqual(config1, config2)
      self.failUnless(not config1 == config2)
      self.failUnless(config1 < config2)
      self.failUnless(config1 <= config2)
      self.failUnless(not config1 > config2)
      self.failUnless(not config1 >= config2)
      self.failUnless(config1 != config2)

   def testComparison_014(self):
      """
      Test comparison of two differing objects, purge differs.
      """
      config1 = Config()
      config1.reference = ReferenceConfig()
      config1.options = OptionsConfig()
      config1.collect = CollectConfig()
      config1.stage = StageConfig()
      config1.store = StoreConfig()
      config1.purge = PurgeConfig(purgeDirs=None)

      config2 = Config()
      config2.reference = ReferenceConfig()
      config2.options = OptionsConfig()
      config2.collect = CollectConfig()
      config2.stage = StageConfig()
      config2.store = StoreConfig()
      config2.purge = PurgeConfig(purgeDirs=[])

      self.failIfEqual(config1, config2)
      self.failUnless(not config1 == config2)
      self.failUnless(config1 < config2)
      self.failUnless(config1 <= config2)
      self.failUnless(not config1 > config2)
      self.failUnless(not config1 >= config2)
      self.failUnless(config1 != config2)


   ######################
   # Test validate logic 
   ######################

   def testValidate_001(self):
      """
      Test validate on an empty reference section.
      """
      config = Config()
      config.reference = ReferenceConfig()
      config._validateReference()

   def testValidate_002(self):
      """
      Test validate on a non-empty reference section, with everything filled in.
      """
      config = Config()
      config.reference = ReferenceConfig("author", "revision", "description", "generator")
      config._validateReference()

   def testValidate_003(self):
      """
      Test validate on an empty options section.
      """
      config = Config()
      config.options = OptionsConfig()
      self.failUnlessRaises(ValueError, config._validateOptions)

   def testValidate_004(self):
      """
      Test validate on a non-empty options section, with everything filled in.
      """
      config = Config()
      config.options = OptionsConfig("monday", "/whatever", "user", "group", "command")
      config._validateOptions()

   def testValidate_005(self):
      """
      Test validate on a non-empty options section, with individual items missing.
      """
      config = Config()
      config.options = OptionsConfig("monday", "/whatever", "user", "group", "command")
      config._validateOptions()
      config.options = OptionsConfig("monday", "/whatever", "user", "group", "command")
      config.options.startingDay = None
      self.failUnlessRaises(ValueError, config._validateOptions)
      config.options = OptionsConfig("monday", "/whatever", "user", "group", "command")
      config.options.workingDir = None
      self.failUnlessRaises(ValueError, config._validateOptions)
      config.options = OptionsConfig("monday", "/whatever", "user", "group", "command")
      config.options.backupUser = None
      self.failUnlessRaises(ValueError, config._validateOptions)
      config.options = OptionsConfig("monday", "/whatever", "user", "group", "command")
      config.options.backupGroup = None
      self.failUnlessRaises(ValueError, config._validateOptions)
      config.options = OptionsConfig("monday", "/whatever", "user", "group", "command")
      config.options.rcpCommand = None
      self.failUnlessRaises(ValueError, config._validateOptions)

   def testValidate_006(self):
      """
      Test validate on an empty collect section.
      """
      config = Config()
      config.collect = CollectConfig()
      self.failUnlessRaises(ValueError, config._validateCollect)

   def testValidate_007(self):
      """
      Test validate on collect section containing only targetDir.
      """
      config = Config()
      config.collect = CollectConfig()
      config.collect.targetDir = "/whatever"
      self.failUnlessRaises(ValueError, config._validateCollect)

   def testValidate_008(self):
      """
      Test validate on collect section containing only targetDir and one
      collectDirs entry that is empty.
      """
      config = Config()
      config.collect = CollectConfig()
      config.collect.targetDir = "/whatever"
      config.collect.collectDirs = [ CollectDir(), ]
      self.failUnlessRaises(ValueError, config._validateCollect)

   def testValidate_009(self):
      """
      Test validate on collect section containing only targetDir and one
      collectDirs entry with only a path.
      """
      config = Config()
      config.collect = CollectConfig()
      config.collect.targetDir = "/whatever"
      config.collect.collectDirs = [ CollectDir(absolutePath="/stuff"), ]
      self.failUnlessRaises(ValueError, config._validateCollect)

   def testValidate_010(self):
      """
      Test validate on collect section containing only targetDir and one
      collectDirs entry with path, collect mode, archive mode and ignore file.
      """
      config = Config()
      config.collect = CollectConfig()
      config.collect.targetDir = "/whatever"
      config.collect.collectDirs = [ CollectDir(absolutePath="/stuff", collectMode="incr", archiveMode="tar", ignoreFile="i"), ]
      config._validateCollect()

   def testValidate_011(self):
      """
      Test validate on collect section containing targetDir, collect mode,
      archive mode and ignore file, and one collectDirs entry with only a path.
      """
      config = Config()
      config.collect = CollectConfig()
      config.collect.targetDir = "/whatever"
      config.collect.collectMode = "incr"
      config.collect.archiveMode = "tar"
      config.collect.ignoreFile = "ignore"
      config.collect.collectDirs = [ CollectDir(absolutePath="/stuff"), ]
      config._validateCollect()

   def testValidate_012(self):
      """
      Test validate on collect section containing targetDir, but with collect mode,
      archive mode and ignore file mixed between main section and directories.
      """
      config = Config()
      config.collect = CollectConfig()
      config.collect.targetDir = "/whatever"
      config.collect.archiveMode = "tar"
      config.collect.ignoreFile = "ignore"
      config.collect.collectDirs = [ CollectDir(absolutePath="/stuff", collectMode="incr", ignoreFile="i"), ]
      config._validateCollect()
      config.collect.collectDirs.append(CollectDir(absolutePath="/stuff2"))
      self.failUnlessRaises(ValueError, config._validateCollect)
      config.collect.collectDirs[-1].collectMode="daily"
      config._validateCollect()

   def testValidate_013(self):
      """
      Test validate on an empty stage section.
      """
      config = Config()
      config.stage = StageConfig()
      self.failUnlessRaises(ValueError, config._validateStage)

   def testValidate_014(self):
      """
      Test validate on stage section containing only targetDir and None for the
      lists.
      """
      config = Config()
      config.stage = StageConfig()
      config.stage.targetDir = "/whatever"
      config.stage.localPeers = None
      config.stage.remotePeers = None
      self.failUnlessRaises(ValueError, config._validateStage)

   def testValidate_015(self):
      """
      Test validate on stage section containing only targetDir and [] for the
      lists.
      """
      config = Config()
      config.stage = StageConfig()
      config.stage.targetDir = "/whatever"
      config.stage.localPeers = []
      config.stage.remotePeers = []
      self.failUnlessRaises(ValueError, config._validateStage)

   def testValidate_016(self):
      """
      Test validate on stage section containing targetDir and one local peer
      that is empty.
      """
      config = Config()
      config.stage = StageConfig()
      config.stage.targetDir = "/whatever"
      config.stage.localPeers = [LocalPeer(), ]
      self.failUnlessRaises(ValueError, config._validateStage)

   def testValidate_017(self):
      """
      Test validate on stage section containing targetDir and one local peer
      with only a name.
      """
      config = Config()
      config.stage = StageConfig()
      config.stage.targetDir = "/whatever"
      config.stage.localPeers = [LocalPeer(name="name"), ]
      self.failUnlessRaises(ValueError, config._validateStage)

   def testValidate_018(self):
      """
      Test validate on stage section containing targetDir and one local peer
      with a name and path, None for remote list.
      """
      config = Config()
      config.stage = StageConfig()
      config.stage.targetDir = "/whatever"
      config.stage.localPeers = [LocalPeer(name="name", collectDir="/somewhere"), ]
      config.stage.remotePeers = None
      config._validateStage()

   def testValidate_019(self):
      """
      Test validate on stage section containing targetDir and one local peer
      with a name and path, [] for remote list.
      """
      config = Config()
      config.stage = StageConfig()
      config.stage.targetDir = "/whatever"
      config.stage.localPeers = [LocalPeer(name="name", collectDir="/somewhere"), ]
      config.stage.remotePeers = []
      config._validateStage()

   def testValidate_020(self):
      """
      Test validate on stage section containing targetDir and one remote peer
      that is empty.
      """
      config = Config()
      config.stage = StageConfig()
      config.stage.targetDir = "/whatever"
      config.stage.remotePeers = [RemotePeer(), ]
      self.failUnlessRaises(ValueError, config._validateStage)

   def testValidate_021(self):
      """
      Test validate on stage section containing targetDir and one remote peer
      with only a name.
      """
      config = Config()
      config.stage = StageConfig()
      config.stage.targetDir = "/whatever"
      config.stage.remotePeers = [RemotePeer(name="blech"), ]
      self.failUnlessRaises(ValueError, config._validateStage)

   def testValidate_022(self):
      """
      Test validate on stage section containing targetDir and one remote peer
      with a name and path, None for local list.
      """
      config = Config()
      config.stage = StageConfig()
      config.stage.targetDir = "/whatever"
      config.stage.localPeers = None
      config.stage.remotePeers = [RemotePeer(name="blech", collectDir="/some/path/to/data"), ]
      self.failUnlessRaises(ValueError, config._validateStage)
      config.options = OptionsConfig(backupUser="ken", rcpCommand="command")
      config._validateStage()
      config.options = None
      self.failUnlessRaises(ValueError, config._validateStage)
      config.stage.remotePeers[-1].remoteUser = "remote"
      config.stage.remotePeers[-1].rcpCommand = "command"
      config._validateStage()

   def testValidate_023(self):
      """
      Test validate on stage section containing targetDir and one remote peer
      with a name and path, [] for local list.
      """
      config = Config()
      config.stage = StageConfig()
      config.stage.targetDir = "/whatever"
      config.stage.localPeers = []
      config.stage.remotePeers = [RemotePeer(name="blech", collectDir="/some/path/to/data"), ]
      self.failUnlessRaises(ValueError, config._validateStage)
      config.options = OptionsConfig(backupUser="ken", rcpCommand="command")
      config._validateStage()
      config.options = None
      self.failUnlessRaises(ValueError, config._validateStage)
      config.stage.remotePeers[-1].remoteUser = "remote"
      config.stage.remotePeers[-1].rcpCommand = "command"
      config._validateStage()

   def testValidate_024(self):
      """
      Test validate on stage section containing targetDir and one remote and
      one local peer.
      """
      config = Config()
      config.stage = StageConfig()
      config.stage.targetDir = "/whatever"
      config.stage.localPeers = [LocalPeer(name="metoo", collectDir="/nowhere"),  ]
      config.stage.remotePeers = [RemotePeer(name="blech", collectDir="/some/path/to/data"), ]
      self.failUnlessRaises(ValueError, config._validateStage)
      config.options = OptionsConfig(backupUser="ken", rcpCommand="command")
      config._validateStage()
      config.options = None
      self.failUnlessRaises(ValueError, config._validateStage)
      config.stage.remotePeers[-1].remoteUser = "remote"
      config.stage.remotePeers[-1].rcpCommand = "command"
      config._validateStage()

   def testValidate_025(self):
      """
      Test validate on stage section containing targetDir multiple remote and
      local peers.
      """
      config = Config()
      config.stage = StageConfig()
      config.stage.targetDir = "/whatever"
      config.stage.localPeers = [LocalPeer(name="metoo", collectDir="/nowhere"), LocalPeer("one", "/two"), LocalPeer("a", "/b"), ]
      config.stage.remotePeers = [RemotePeer(name="blech", collectDir="/some/path/to/data"), RemotePeer("a", "/b"), ]
      self.failUnlessRaises(ValueError, config._validateStage)
      config.options = OptionsConfig(backupUser="ken", rcpCommand="command")
      config._validateStage()
      config.options = None
      self.failUnlessRaises(ValueError, config._validateStage)
      config.stage.remotePeers[-1].remoteUser = "remote"
      config.stage.remotePeers[-1].rcpCommand = "command"
      self.failUnlessRaises(ValueError, config._validateStage)
      config.stage.remotePeers[0].remoteUser = "remote"
      config.stage.remotePeers[0].rcpCommand = "command"
      config._validateStage()

   def testValidate_026(self):
      """
      Test validate on an empty store section.
      """
      config = Config()
      config.store = StoreConfig()
      self.failUnlessRaises(ValueError, config._validateStore)

   def testValidate_027(self):
      """
      Test validate on store section with everything filled in.
      """
      config = Config()
      config.store = StoreConfig()
      config.store.sourceDir = "/source"
      config.store.mediaType = "cdr-74"
      config.store.deviceType = "cdwriter"
      config.store.devicePath = "/dev/cdrw"
      config.store.deviceScsiId = "0,0,0"
      config.store.driveSpeed = 4
      config.store.checkData = True
      config.store.safeOverwrite = False
      config.store.capacityMode = "overwrite"
      config._validateStore()

   def testValidate_028(self):
      """
      Test validate on store section missing one each of required fields.
      """
      config = Config()
      config.store = StoreConfig()
      config.store.mediaType = "cdr-74"
      config.store.deviceType = "cdwriter"
      config.store.devicePath = "/dev/cdrw"
      config.store.deviceScsiId = "0,0,0"
      config.store.driveSpeed = 4
      config.store.checkData = True
      config.store.safeOverwrite = False
      config.store.capacityMode = "overwrite"
      self.failUnlessRaises(ValueError, config._validateStore)

      config.store = StoreConfig()
      config.store.sourceDir = "/source"
      config.store.deviceType = "cdwriter"
      config.store.devicePath = "/dev/cdrw"
      config.store.deviceScsiId = "0,0,0"
      config.store.driveSpeed = 4
      config.store.checkData = True
      config.store.safeOverwrite = False
      config.store.capacityMode = "overwrite"
      self.failUnlessRaises(ValueError, config._validateStore)

      config.store = StoreConfig()
      config.store.sourceDir = "/source"
      config.store.mediaType = "cdr-74"
      config.store.deviceType = "cdwriter"
      config.store.deviceScsiId = "0,0,0"
      config.store.driveSpeed = 4
      config.store.checkData = True
      config.store.safeOverwrite = False
      config.store.capacityMode = "overwrite"
      self.failUnlessRaises(ValueError, config._validateStore)

      config.store = StoreConfig()
      config.store.sourceDir = "/source"
      config.store.mediaType = "cdr-74"
      config.store.deviceType = "cdwriter"
      config.store.devicePath = "/dev/cdrw"
      config.store.driveSpeed = 4
      config.store.checkData = True
      config.store.safeOverwrite = False
      config.store.capacityMode = "overwrite"
      self.failUnlessRaises(ValueError, config._validateStore)

   def testValidate_029(self):
      """
      Test validate on store section missing one each of device type, drive
      speed and capacity mode and the booleans.
      """
      config = Config()
      config.store = StoreConfig()
      config.store.sourceDir = "/source"
      config.store.mediaType = "cdr-74"
      config.store.devicePath = "/dev/cdrw"
      config.store.deviceScsiId = "0,0,0"
      config.store.driveSpeed = 4
      config.store.checkData = True
      config.store.safeOverwrite = False
      config.store.capacityMode = "overwrite"
      config._validateStore()

      config.store = StoreConfig()
      config.store.sourceDir = "/source"
      config.store.mediaType = "cdr-74"
      config.store.deviceType = "cdwriter"
      config.store.devicePath = "/dev/cdrw"
      config.store.deviceScsiId = "0,0,0"
      config.store.checkData = True
      config.store.safeOverwrite = False
      config.store.capacityMode = "overwrite"
      config._validateStore()

      config.store = StoreConfig()
      config.store.sourceDir = "/source"
      config.store.mediaType = "cdr-74"
      config.store.deviceType = "cdwriter"
      config.store.devicePath = "/dev/cdrw"
      config.store.deviceScsiId = "0,0,0"
      config.store.driveSpeed = 4
      config.store.checkData = True
      config.store.safeOverwrite = False
      config._validateStore()

      config.store = StoreConfig()
      config.store.sourceDir = "/source"
      config.store.mediaType = "cdr-74"
      config.store.deviceType = "cdwriter"
      config.store.devicePath = "/dev/cdrw"
      config.store.deviceScsiId = "0,0,0"
      config.store.driveSpeed = 4
      config.store.checkData = True
      config.store.safeOverwrite = False
      config.store.capacityMode = "overwrite"

      config.store = StoreConfig()
      config.store.sourceDir = "/source"
      config.store.mediaType = "cdr-74"
      config.store.deviceType = "cdwriter"
      config.store.devicePath = "/dev/cdrw"
      config.store.deviceScsiId = "0,0,0"
      config.store.driveSpeed = 4
      config.store.safeOverwrite = False
      config.store.capacityMode = "overwrite"
      config._validateStore()

      config.store = StoreConfig()
      config.store.sourceDir = "/source"
      config.store.mediaType = "cdr-74"
      config.store.deviceType = "cdwriter"
      config.store.devicePath = "/dev/cdrw"
      config.store.deviceScsiId = "0,0,0"
      config.store.driveSpeed = 4
      config.store.checkData = True
      config.store.capacityMode = "overwrite"
      config._validateStore()

   def testValidate_030(self):
      """
      Test validate on an empty purge section, with a None list.
      """
      config = Config()
      config.purge = PurgeConfig()
      config.purge.purgeDirs = None
      config._validatePurge()

   def testValidate_031(self):
      """
      Test validate on an empty purge section, with [] for the list.
      """
      config = Config()
      config.purge = PurgeConfig()
      config.purge.purgeDirs = []
      config._validatePurge()

   def testValidate_032(self):
      """
      Test validate on an a purge section, with one empty purge dir.
      """
      config = Config()
      config.purge = PurgeConfig()
      config.purge.purgeDirs = [PurgeDir(), ]
      self.failUnlessRaises(ValueError, config._validatePurge)

   def testValidate_033(self):
      """
      Test validate on an a purge section, with one purge dir that has only a
      path.
      """
      config = Config()
      config.purge = PurgeConfig()
      config.purge.purgeDirs = [PurgeDir(absolutePath="/whatever"), ]
      self.failUnlessRaises(ValueError, config._validatePurge)

   def testValidate_034(self):
      """
      Test validate on an a purge section, with one purge dir that has only
      retain days.
      """
      config = Config()
      config.purge = PurgeConfig()
      config.purge.purgeDirs = [PurgeDir(retainDays=3), ]
      self.failUnlessRaises(ValueError, config._validatePurge)

   def testValidate_035(self):
      """
      Test validate on an a purge section, with one purge dir that makes sense.
      """
      config = Config()
      config.purge = PurgeConfig()
      config.purge.purgeDirs = [ PurgeDir(absolutePath="/whatever", retainDays=4), ]
      config._validatePurge()

   def testValidate_036(self):
      """
      Test validate on an a purge section, with several purge dirs that make
      sense.
      """
      config = Config()
      config.purge = PurgeConfig()
      config.purge.purgeDirs = [ PurgeDir("/whatever", 4), PurgeDir("/etc/different", 12), ]
      config._validatePurge()


   ############################
   # Test parsing of documents
   ############################

   def testParse_001(self):
      """
      Parse empty config document, validate=False.
      """
      path = self.resources["cback.conf.2"]
      config = Config(xmlPath=path, validate=False)
      expected = Config()
      self.failUnlessEqual(expected, config)

   def testParse_002(self):
      """
      Parse empty config document, validate=True.
      """
      path = self.resources["cback.conf.2"]
      self.failUnlessRaises(ValueError, Config, xmlPath=path, validate=True)

   def testParse_003(self):
      """
      Parse config document containing only a reference section, containing
      only required fields, validate=False.
      """
      path = self.resources["cback.conf.3"]
      config = Config(xmlPath=path, validate=False)
      expected = Config()
      expected.reference = ReferenceConfig()
      self.failUnlessEqual(expected, config)

   def testParse_004(self):
      """
      Parse config document containing only a reference section, containing
      only required fields, validate=True.
      """
      path = self.resources["cback.conf.3"]
      self.failUnlessRaises(ValueError, Config, xmlPath=path, validate=True)

   def testParse_005(self):
      """
      Parse config document containing only a reference section, containing all
      required and optional fields, validate=False.
      """
      path = self.resources["cback.conf.4"]
      config = Config(xmlPath=path, validate=False)
      expected = Config()
      expected.reference = ReferenceConfig("$Author: pronovic $", "1.3", "Sample configuration", "Generated by hand.")
      self.failUnlessEqual(expected, config)

   def testParse_006(self):
      """
      Parse config document containing only a reference section, containing all
      required and optional fields, validate=True.
      """
      path = self.resources["cback.conf.4"]
      self.failUnlessRaises(ValueError, Config, xmlPath=path, validate=True)

   def testParse_007(self):
      """
      Parse config document containing only an options section, containing only
      required fields, validate=False.
      """
      path = self.resources["cback.conf.5"]
      config = Config(xmlPath=path, validate=False)
      expected = Config()
      expected.options = OptionsConfig("tuesday", "/opt/backup/tmp", "backup", "group", "/usr/bin/scp -1 -B")
      self.failUnlessEqual(expected, config)

   def testParse_008(self):
      """
      Parse config document containing only an options section, containing only
      required fields, validate=True.
      """
      path = self.resources["cback.conf.5"]
      self.failUnlessRaises(ValueError, Config, xmlPath=path, validate=True)

   def testParse_009(self):
      """
      Parse config document containing only an options section, containing
      required and optional fields, validate=False.
      """
      path = self.resources["cback.conf.6"]
      config = Config(xmlPath=path, validate=False)
      expected = Config()
      expected.options = OptionsConfig("tuesday", "/opt/backup/tmp", "backup", "group", "/usr/bin/scp -1 -B")
      self.failUnlessEqual(expected, config)

   def testParse_010(self):
      """
      Parse config document containing only an options section, containing
      required and optional fields, validate=True.
      """
      path = self.resources["cback.conf.6"]
      self.failUnlessRaises(ValueError, Config, xmlPath=path, validate=True)

   def testParse_011(self):
      """
      Parse config document containing only a collect section, containing only
      required fields, validate=False.
      """
      path = self.resources["cback.conf.7"]
      config = Config(xmlPath=path, validate=False)
      expected = Config()
      expected.collect = CollectConfig("/opt/backup/collect", "daily", "tar", ".ignore")
      expected.collect.collectDirs = [CollectDir(absolutePath="/etc"), ]
      self.failUnlessEqual(expected, config)

   def testParse_012(self):
      """
      Parse config document containing only a collect section, containing only
      required fields, validate=True.
      """
      path = self.resources["cback.conf.7"]
      self.failUnlessRaises(ValueError, Config, xmlPath=path, validate=True)

   def testParse_013(self):
      """
      Parse config document containing only a collect section, containing
      required and optional fields, validate=False.
      """
      path = self.resources["cback.conf.8"]
      config = Config(xmlPath=path, validate=False)
      expected = Config()
      expected.collect = CollectConfig("/opt/backup/collect", "daily", "targz", ".cbignore")
      expected.collect.absoluteExcludePaths = ["/etc/cback.conf", "/etc/X11", ]
      expected.collect.excludePatterns = [".*tmp.*", ".*\.netscape\/.*", ]
      expected.collect.collectDirs = []
      expected.collect.collectDirs.append(CollectDir(absolutePath="/root"))
      expected.collect.collectDirs.append(CollectDir(absolutePath="/var/log", collectMode="incr"))
      expected.collect.collectDirs.append(CollectDir(absolutePath="/etc",collectMode="incr",archiveMode="tar",ignoreFile=".ignore"))
      collectDir = CollectDir(absolutePath="/opt")
      collectDir.absoluteExcludePaths = [ "/opt/share", "/opt/tmp", ]
      collectDir.relativeExcludePaths = [ "large", "backup", ]
      collectDir.excludePatterns = [ ".*\.doc\.*", ".*\.xls\.*", ]
      expected.collect.collectDirs.append(collectDir)
      self.failUnlessEqual(expected, config)

   def testParse_014(self):
      """
      Parse config document containing only a collect section, containing
      required and optional fields, validate=True.
      """
      path = self.resources["cback.conf.8"]
      self.failUnlessRaises(ValueError, Config, xmlPath=path, validate=True)

   def testParse_015(self):
      """
      Parse config document containing only a stage section, containing only
      required fields, validate=False.
      """
      path = self.resources["cback.conf.9"]
      config = Config(xmlPath=path, validate=False)
      expected = Config()
      expected.stage = StageConfig()
      expected.stage.targetDir = "/opt/backup/staging"
      expected.stage.localPeers = None
      expected.stage.remotePeers = [ RemotePeer("machine2", "/opt/backup/collect"), ]
      self.failUnlessEqual(expected, config)

   def testParse_016(self):
      """
      Parse config document containing only a stage section, containing only
      required fields, validate=True.
      """
      path = self.resources["cback.conf.9"]
      self.failUnlessRaises(ValueError, Config, xmlPath=path, validate=True)

   def testParse_017(self):
      """
      Parse config document containing only a stage section, containing all
      required and optional fields, validate=False.
      """
      path = self.resources["cback.conf.10"]
      config = Config(xmlPath=path, validate=False)
      expected = Config()
      expected.stage = StageConfig()
      expected.stage.targetDir = "/opt/backup/staging"
      expected.stage.localPeers = []
      expected.stage.remotePeers = []
      expected.stage.localPeers.append(LocalPeer("machine1-1", "/opt/backup/collect"))
      expected.stage.localPeers.append(LocalPeer("machine1-2", "/var/backup"))
      expected.stage.remotePeers.append(RemotePeer("machine2", "/backup/collect"))
      expected.stage.remotePeers.append(RemotePeer("machine3", "/home/whatever/tmp", remoteUser="someone", rcpCommand="scp -B"))
      self.failUnlessEqual(expected, config)

   def testParse_018(self):
      """
      Parse config document containing only a stage section, containing all
      required and optional fields, validate=True.
      """
      path = self.resources["cback.conf.10"]
      self.failUnlessRaises(ValueError, Config, xmlPath=path, validate=True)

   def testParse_019(self):
      """
      Parse config document containing only a store section, containing only
      required fields, validate=False.
      """
      path = self.resources["cback.conf.11"]
      config = Config(xmlPath=path, validate=False)
      expected = Config()
      expected.store = StoreConfig("/opt/backup/staging", mediaType="cdrw-74", devicePath="/dev/cdrw", deviceScsiId="0,0,0")
      self.failUnlessEqual(expected, config)

   def testParse_020(self):
      """
      Parse config document containing only a store section, containing only
      required fields, validate=True.
      """
      path = self.resources["cback.conf.11"]
      self.failUnlessRaises(ValueError, Config, xmlPath=path, validate=True)

   def testParse_021(self):
      """
      Parse config document containing only a store section, containing all
      required and optional fields, validate=False.
      """
      path = self.resources["cback.conf.12"]
      config = Config(xmlPath=path, validate=False)
      expected = Config()
      expected.store = StoreConfig()
      expected.store.sourceDir = "/opt/backup/staging"
      expected.store.mediaType = "cdrw-74"
      expected.store.deviceType = "cdwriter"
      expected.store.devicePath = "/dev/cdrw"
      expected.store.deviceScsiId = "0,0,0"
      expected.store.driveSpeed = 4
      expected.store.checkData = True
      expected.store.safeOverwrite = True
      expected.store.capacityMode = "fail"
      self.failUnlessEqual(expected, config)

   def testParse_022(self):
      """
      Parse config document containing only a store section, containing all
      required and optional fields, validate=True.
      """
      path = self.resources["cback.conf.12"]
      self.failUnlessRaises(ValueError, Config, xmlPath=path, validate=True)

   def testParse_023(self):
      """
      Parse config document containing only a purge section, containing only
      required fields, validate=False.
      """
      path = self.resources["cback.conf.13"]
      config = Config(xmlPath=path, validate=False)
      expected = Config()
      expected.purge = PurgeConfig()
      expected.purge.purgeDirs = [PurgeDir("/opt/backup/stage", 5), ]
      self.failUnlessEqual(expected, config)

   def testParse_024(self):
      """
      Parse config document containing only a purge section, containing only
      required fields, validate=True.
      """
      path = self.resources["cback.conf.13"]
      self.failUnlessRaises(ValueError, Config, xmlPath=path, validate=True)

   def testParse_025(self):
      """
      Parse config document containing only a purge section, containing all
      required and optional fields, validate=False.
      """
      path = self.resources["cback.conf.14"]
      config = Config(xmlPath=path, validate=False)
      expected = Config()
      expected.purge = PurgeConfig()
      expected.purge.purgeDirs = []
      expected.purge.purgeDirs.append(PurgeDir("/opt/backup/stage", 5))
      expected.purge.purgeDirs.append(PurgeDir("/opt/backup/collect", 0))
      expected.purge.purgeDirs.append(PurgeDir("/home/backup/tmp", 12))
      self.failUnlessEqual(expected, config)

   def testParse_026(self):
      """
      Parse config document containing only a purge section, containing all
      required and optional fields, validate=True.
      """
      path = self.resources["cback.conf.14"]
      self.failUnlessRaises(ValueError, Config, xmlPath=path, validate=True)

   def testParse_027(self):
      """
      Parse complete document containing all required and optional fields,
      validate=False.
      """
      path = self.resources["cback.conf.15"]
      config = Config(xmlPath=path, validate=False)
      expected = Config()
      expected.reference = ReferenceConfig("$Author: pronovic $", "1.3", "Sample configuration", "Generated by hand.")
      expected.options = OptionsConfig("tuesday", "/opt/backup/tmp", "backup", "group", "/usr/bin/scp -1 -B")
      expected.collect = CollectConfig("/opt/backup/collect", "daily", "targz", ".cbignore")
      expected.collect.absoluteExcludePaths = ["/etc/cback.conf", "/etc/X11", ]
      expected.collect.excludePatterns = [".*tmp.*", ".*\.netscape\/.*", ]
      expected.collect.collectDirs = []
      expected.collect.collectDirs.append(CollectDir(absolutePath="/root"))
      expected.collect.collectDirs.append(CollectDir(absolutePath="/var/log", collectMode="incr"))
      expected.collect.collectDirs.append(CollectDir(absolutePath="/etc",collectMode="incr",archiveMode="tar",ignoreFile=".ignore"))
      collectDir = CollectDir(absolutePath="/opt")
      collectDir.absoluteExcludePaths = [ "/opt/share", "/opt/tmp", ]
      collectDir.relativeExcludePaths = [ "large", "backup", ]
      collectDir.excludePatterns = [ ".*\.doc\.*", ".*\.xls\.*", ]
      expected.collect.collectDirs.append(collectDir)
      expected.stage = StageConfig()
      expected.stage.targetDir = "/opt/backup/staging"
      expected.stage.localPeers = []
      expected.stage.remotePeers = []
      expected.stage.localPeers.append(LocalPeer("machine1-1", "/opt/backup/collect"))
      expected.stage.localPeers.append(LocalPeer("machine1-2", "/var/backup"))
      expected.stage.remotePeers.append(RemotePeer("machine2", "/backup/collect"))
      expected.stage.remotePeers.append(RemotePeer("machine3", "/home/whatever/tmp", remoteUser="someone", rcpCommand="scp -B"))
      expected.store = StoreConfig()
      expected.store.sourceDir = "/opt/backup/staging"
      expected.store.mediaType = "cdrw-74"
      expected.store.deviceType = "cdwriter"
      expected.store.devicePath = "/dev/cdrw"
      expected.store.deviceScsiId = "0,0,0"
      expected.store.driveSpeed = 4
      expected.store.checkData = True
      expected.store.safeOverwrite = True
      expected.store.capacityMode = "fail"
      expected.purge = PurgeConfig()
      expected.purge.purgeDirs = []
      expected.purge.purgeDirs.append(PurgeDir("/opt/backup/stage", 5))
      expected.purge.purgeDirs.append(PurgeDir("/opt/backup/collect", 0))
      expected.purge.purgeDirs.append(PurgeDir("/home/backup/tmp", 12))
      self.failUnlessEqual(expected, config)

   def testParse_028(self):
      """
      Parse complete document containing all required and optional fields,
      validate=True.
      """
      path = self.resources["cback.conf.15"]
      config = Config(xmlPath=path, validate=True)
      expected = Config()
      expected.reference = ReferenceConfig("$Author: pronovic $", "1.3", "Sample configuration", "Generated by hand.")
      expected.options = OptionsConfig("tuesday", "/opt/backup/tmp", "backup", "group", "/usr/bin/scp -1 -B")
      expected.collect = CollectConfig("/opt/backup/collect", "daily", "targz", ".cbignore")
      expected.collect.absoluteExcludePaths = ["/etc/cback.conf", "/etc/X11", ]
      expected.collect.excludePatterns = [".*tmp.*", ".*\.netscape\/.*", ]
      expected.collect.collectDirs = []
      expected.collect.collectDirs.append(CollectDir(absolutePath="/root"))
      expected.collect.collectDirs.append(CollectDir(absolutePath="/var/log", collectMode="incr"))
      expected.collect.collectDirs.append(CollectDir(absolutePath="/etc",collectMode="incr",archiveMode="tar",ignoreFile=".ignore"))
      collectDir = CollectDir(absolutePath="/opt")
      collectDir.absoluteExcludePaths = [ "/opt/share", "/opt/tmp", ]
      collectDir.relativeExcludePaths = [ "large", "backup", ]
      collectDir.excludePatterns = [ ".*\.doc\.*", ".*\.xls\.*", ]
      expected.collect.collectDirs.append(collectDir)
      expected.stage = StageConfig()
      expected.stage.targetDir = "/opt/backup/staging"
      expected.stage.localPeers = []
      expected.stage.remotePeers = []
      expected.stage.localPeers.append(LocalPeer("machine1-1", "/opt/backup/collect"))
      expected.stage.localPeers.append(LocalPeer("machine1-2", "/var/backup"))
      expected.stage.remotePeers.append(RemotePeer("machine2", "/backup/collect"))
      expected.stage.remotePeers.append(RemotePeer("machine3", "/home/whatever/tmp", remoteUser="someone", rcpCommand="scp -B"))
      expected.store = StoreConfig()
      expected.store.sourceDir = "/opt/backup/staging"
      expected.store.mediaType = "cdrw-74"
      expected.store.deviceType = "cdwriter"
      expected.store.devicePath = "/dev/cdrw"
      expected.store.deviceScsiId = "0,0,0"
      expected.store.driveSpeed = 4
      expected.store.checkData = True
      expected.store.safeOverwrite = True
      expected.store.capacityMode = "fail"
      expected.purge = PurgeConfig()
      expected.purge.purgeDirs = []
      expected.purge.purgeDirs.append(PurgeDir("/opt/backup/stage", 5))
      expected.purge.purgeDirs.append(PurgeDir("/opt/backup/collect", 0))
      expected.purge.purgeDirs.append(PurgeDir("/home/backup/tmp", 12))
      self.failUnlessEqual(expected, config)

   def testParse_029(self):
      """
      Parse a sample from Cedar Backup v1.x, which must still be valid,
      validate=False.
      """
      path = self.resources["cback.conf.1"]
      config = Config(xmlPath=path, validate=False)
      expected = Config()
      expected.reference = ReferenceConfig("$Author: pronovic $", "1.3", "Sample configuration")
      expected.options = OptionsConfig("tuesday", "/opt/backup/tmp", "backup", "backup", "/usr/bin/scp -1 -B")
      expected.collect = CollectConfig()
      expected.collect.targetDir = "/opt/backup/collect"
      expected.collect.archiveMode = "targz"
      expected.collect.ignoreFile = ".cbignore"
      expected.collect.collectDirs = []
      expected.collect.collectDirs.append(CollectDir("/etc", collectMode="daily"))
      expected.collect.collectDirs.append(CollectDir("/var/log", collectMode="incr"))
      collectDir = CollectDir("/opt", collectMode="weekly")
      collectDir.absoluteExcludePaths = ["/opt/large", "/opt/backup", "/opt/tmp", ]
      expected.collect.collectDirs.append(collectDir)
      expected.stage = StageConfig()
      expected.stage.targetDir = "/opt/backup/staging"
      expected.stage.localPeers = [LocalPeer("machine1", "/opt/backup/collect"), ]
      expected.stage.remotePeers = [RemotePeer("machine2", "/opt/backup/collect", remoteUser="backup"), ]
      expected.store = StoreConfig()
      expected.store.sourceDir = "/opt/backup/staging"
      expected.store.devicePath = "/dev/cdrw"
      expected.store.deviceScsiId = "0,0,0"
      expected.store.driveSpeed = 4
      expected.store.mediaType = "cdrw-74"
      expected.store.checkData = True
      expected.purge = PurgeConfig()
      expected.purge.purgeDirs = []
      expected.purge.purgeDirs.append(PurgeDir("/opt/backup/stage", 5))
      expected.purge.purgeDirs.append(PurgeDir("/opt/backup/collect", 0))
      self.failUnlessEqual(expected, config)

   def testParse_030(self):
      """
      Parse a sample from Cedar Backup v1.x, which must still be valid,
      validate=True.
      """
      path = self.resources["cback.conf.1"]
      config = Config(xmlPath=path, validate=True)
      expected = Config()
      expected.reference = ReferenceConfig("$Author: pronovic $", "1.3", "Sample configuration")
      expected.options = OptionsConfig("tuesday", "/opt/backup/tmp", "backup", "backup", "/usr/bin/scp -1 -B")
      expected.collect = CollectConfig()
      expected.collect.targetDir = "/opt/backup/collect"
      expected.collect.archiveMode = "targz"
      expected.collect.ignoreFile = ".cbignore"
      expected.collect.collectDirs = []
      expected.collect.collectDirs.append(CollectDir("/etc", collectMode="daily"))
      expected.collect.collectDirs.append(CollectDir("/var/log", collectMode="incr"))
      collectDir = CollectDir("/opt", collectMode="weekly")
      collectDir.absoluteExcludePaths = ["/opt/large", "/opt/backup", "/opt/tmp", ]
      expected.collect.collectDirs.append(collectDir)
      expected.stage = StageConfig()
      expected.stage.targetDir = "/opt/backup/staging"
      expected.stage.localPeers = [LocalPeer("machine1", "/opt/backup/collect"), ]
      expected.stage.remotePeers = [RemotePeer("machine2", "/opt/backup/collect", remoteUser="backup"), ]
      expected.store = StoreConfig()
      expected.store.sourceDir = "/opt/backup/staging"
      expected.store.devicePath = "/dev/cdrw"
      expected.store.deviceScsiId = "0,0,0"
      expected.store.driveSpeed = 4
      expected.store.mediaType = "cdrw-74"
      expected.store.checkData = True
      expected.purge = PurgeConfig()
      expected.purge.purgeDirs = []
      expected.purge.purgeDirs.append(PurgeDir("/opt/backup/stage", 5))
      expected.purge.purgeDirs.append(PurgeDir("/opt/backup/collect", 0))
      self.failUnlessEqual(expected, config)


   #########################
   # Test the extract logic
   #########################

   def testExtractXml_001(self):
      """
      Extract empty config document, validate=True.
      """
      before = Config()
      self.failUnlessRaises(ValueError, before.extractXml, validate=True)

   def testExtractXml_002(self):
      """
      Extract empty config document, validate=False.
      """
      before = Config()
      beforeXml = before.extractXml(validate=False)
      after = Config(xmlData=beforeXml, validate=False)
      self.failUnlessEqual(before, after)

   def testExtractXml_003(self):
      """
      Extract document containing only a valid reference section,
      validate=True.
      """
      before = Config()
      before.reference = ReferenceConfig("$Author: pronovic $", "1.3", "Sample configuration")
      self.failUnlessRaises(ValueError, before.extractXml, validate=True)

   def testExtractXml_004(self):
      """
      Extract document containing only a valid reference section,
      validate=False.
      """
      before = Config()
      before.reference = ReferenceConfig("$Author: pronovic $", "1.3", "Sample configuration")
      beforeXml = before.extractXml(validate=False)
      after = Config(xmlData=beforeXml, validate=False)
      self.failUnlessEqual(before, after)

   def testExtractXml_005(self):
      """
      Extract document containing only a valid options section, validate=True.
      """
      before = Config()
      before.options = OptionsConfig("tuesday", "/opt/backup/tmp", "backup", "backup", "/usr/bin/scp -1 -B")
      self.failUnlessRaises(ValueError, before.extractXml, validate=True)

   def testExtractXml_006(self):
      """
      Extract document containing only a valid options section, validate=False.
      """
      before = Config()
      before.options = OptionsConfig("tuesday", "/opt/backup/tmp", "backup", "backup", "/usr/bin/scp -1 -B")
      beforeXml = before.extractXml(validate=False)
      after = Config(xmlData=beforeXml, validate=False)
      self.failUnlessEqual(before, after)

   def testExtractXml_007(self):
      """
      Extract document containing only an invalid options section,
      validate=True.
      """
      before = Config()
      before.options = OptionsConfig()
      self.failUnlessRaises(ValueError, before.extractXml, validate=True)

   def testExtractXml_008(self):
      """
      Extract document containing only an invalid options section,
      validate=False.
      """
      before = Config()
      before.options = OptionsConfig()
      beforeXml = before.extractXml(validate=False)
      after = Config(xmlData=beforeXml, validate=False)
      self.failUnlessEqual(before, after)

   def testExtractXml_009(self):
      """
      Extract document containing only a valid collect section, empty lists,
      validate=True.
      """
      before = Config()
      before.collect = CollectConfig()
      before.collect.targetDir = "/opt/backup/collect"
      before.collect.archiveMode = "targz"
      before.collect.ignoreFile = ".cbignore"
      before.collect.collectDirs = [CollectDir("/etc", collectMode="daily"), ]
      self.failUnlessRaises(ValueError, before.extractXml, validate=True)

   def testExtractXml_010(self):
      """
      Extract document containing only a valid collect section, empty lists,
      validate=False.
      """
      before = Config()
      before.collect = CollectConfig()
      before.collect.targetDir = "/opt/backup/collect"
      before.collect.archiveMode = "targz"
      before.collect.ignoreFile = ".cbignore"
      before.collect.collectDirs = [CollectDir("/etc", collectMode="daily"), ]
      beforeXml = before.extractXml(validate=False)
      after = Config(xmlData=beforeXml, validate=False)
      self.failUnlessEqual(before, after)

   def testExtractXml_011(self):
      """
      Extract document containing only a valid collect section, non-empty
      lists, validate=True.
      """
      before = Config()
      before.collect = CollectConfig()
      before.collect.targetDir = "/opt/backup/collect"
      before.collect.archiveMode = "targz"
      before.collect.ignoreFile = ".cbignore"
      before.collect.absoluteExcludePaths = [ "/one", "/two", "/three", ]
      before.collect.excludePatterns = [ "pattern", ]
      before.collect.collectDirs = [CollectDir("/etc", collectMode="daily"), ]
      self.failUnlessRaises(ValueError, before.extractXml, validate=True)

   def testExtractXml_012(self):
      """
      Extract document containing only a valid collect section, non-empty
      lists, validate=False.
      """
      before = Config()
      before.collect = CollectConfig()
      before.collect.targetDir = "/opt/backup/collect"
      before.collect.archiveMode = "targz"
      before.collect.ignoreFile = ".cbignore"
      before.collect.absoluteExcludePaths = [ "/one", "/two", "/three", ]
      before.collect.excludePatterns = [ "pattern", ]
      before.collect.collectDirs = [CollectDir("/etc", collectMode="daily"), ]
      beforeXml = before.extractXml(validate=False)
      after = Config(xmlData=beforeXml, validate=False)
      self.failUnlessEqual(before, after)

   def testExtractXml_013(self):
      """
      Extract document containing only an invalid collect section,
      validate=True.
      """
      before = Config()
      before.collect = CollectConfig()
      self.failUnlessRaises(ValueError, before.extractXml, validate=True)

   def testExtractXml_014(self):
      """
      Extract document containing only an invalid collect section,
      validate=False.
      """
      before = Config()
      before.collect = CollectConfig()
      beforeXml = before.extractXml(validate=False)
      after = Config(xmlData=beforeXml, validate=False)
      self.failUnlessEqual(before, after)

   def testExtractXml_015(self):
      """
      Extract document containing only a valid stage section, one empty list,
      validate=True.
      """
      before = Config()
      before.stage = StageConfig()
      before.stage.targetDir = "/opt/backup/staging"
      before.stage.localPeers = [LocalPeer("machine1", "/opt/backup/collect"), ]
      before.stage.remotePeers = None
      self.failUnlessRaises(ValueError, before.extractXml, validate=True)

   def testExtractXml_016(self):
      """
      Extract document containing only a valid stage section, empty lists,
      validate=False.
      """
      before = Config()
      before.stage = StageConfig()
      before.stage.targetDir = "/opt/backup/staging"
      before.stage.localPeers = [LocalPeer("machine1", "/opt/backup/collect"), ]
      before.stage.remotePeers = None
      beforeXml = before.extractXml(validate=False)
      after = Config(xmlData=beforeXml, validate=False)
      self.failUnlessEqual(before, after)

   def testExtractXml_017(self):
      """
      Extract document containing only a valid stage section, non-empty lists,
      validate=True.
      """
      before = Config()
      before.stage = StageConfig()
      before.stage.targetDir = "/opt/backup/staging"
      before.stage.localPeers = [LocalPeer("machine1", "/opt/backup/collect"), ]
      before.stage.remotePeers = [RemotePeer("machine2", "/opt/backup/collect", remoteUser="backup"), ]
      self.failUnlessRaises(ValueError, before.extractXml, validate=True)

   def testExtractXml_018(self):
      """
      Extract document containing only a valid stage section, non-empty lists,
      validate=False.
      """
      before = Config()
      before.stage = StageConfig()
      before.stage.targetDir = "/opt/backup/staging"
      before.stage.localPeers = [LocalPeer("machine1", "/opt/backup/collect"), ]
      before.stage.remotePeers = [RemotePeer("machine2", "/opt/backup/collect", remoteUser="backup"), ]
      beforeXml = before.extractXml(validate=False)
      after = Config(xmlData=beforeXml, validate=False)
      self.failUnlessEqual(before, after)

   def testExtractXml_019(self):
      """
      Extract document containing only an invalid stage section, validate=True.
      """
      before = Config()
      before.stage = StageConfig()
      self.failUnlessRaises(ValueError, before.extractXml, validate=True)

   def testExtractXml_020(self):
      """
      Extract document containing only an invalid stage section,
      validate=False.
      """
      before = Config()
      before.stage = StageConfig()
      beforeXml = before.extractXml(validate=False)
      after = Config(xmlData=beforeXml, validate=False)
      self.failUnlessEqual(before, after)

   def testExtractXml_021(self):
      """
      Extract document containing only a valid store section, validate=True.
      """
      before = Config()
      before.store = StoreConfig()
      before.store.sourceDir = "/opt/backup/staging"
      before.store.devicePath = "/dev/cdrw"
      before.store.deviceScsiId = "0,0,0"
      before.store.driveSpeed = 4
      before.store.mediaType = "cdrw-74"
      before.store.checkData = True
      self.failUnlessRaises(ValueError, before.extractXml, validate=True)

   def testExtractXml_022(self):
      """
      Extract document containing only a valid store section, validate=False.
      """
      before = Config()
      before.store = StoreConfig()
      before.store.sourceDir = "/opt/backup/staging"
      before.store.devicePath = "/dev/cdrw"
      before.store.deviceScsiId = "0,0,0"
      before.store.driveSpeed = 4
      before.store.mediaType = "cdrw-74"
      before.store.checkData = True
      beforeXml = before.extractXml(validate=False)
      after = Config(xmlData=beforeXml, validate=False)
      self.failUnlessEqual(before, after)

   def testExtractXml_023(self):
      """
      Extract document containing only an invalid store section, validate=True.
      """
      before = Config()
      before.store = StoreConfig()
      self.failUnlessRaises(ValueError, before.extractXml, validate=True)

   def testExtractXml_024(self):
      """
      Extract document containing only an invalid store section,
      validate=False.
      """
      before = Config()
      before.store = StoreConfig()
      beforeXml = before.extractXml(validate=False)
      after = Config(xmlData=beforeXml, validate=False)
      self.failUnlessEqual(before, after)

   def testExtractXml_025(self):
      """
      Extract document containing only a valid purge section, empty list,
      validate=True.
      """
      before = Config()
      before.purge = PurgeConfig()
      self.failUnlessRaises(ValueError, before.extractXml, validate=True)

   def testExtractXml_026(self):
      """
      Extract document containing only a valid purge section, empty list,
      validate=False.
      """
      before = Config()
      before.purge = PurgeConfig()
      beforeXml = before.extractXml(validate=False)
      after = Config(xmlData=beforeXml, validate=False)
      self.failUnlessEqual(before, after)

   def testExtractXml_027(self):
      """
      Extract document containing only a valid purge section, non-empty list,
      validate=True.
      """
      before = Config()
      before.purge = PurgeConfig()
      before.purge.purgeDirs = []
      before.purge.purgeDirs.append(PurgeDir(absolutePath="/whatever", retainDays=3))
      self.failUnlessRaises(ValueError, before.extractXml, validate=True)

   def testExtractXml_028(self):
      """
      Extract document containing only a valid purge section, non-empty list,
      validate=False.
      """
      before = Config()
      before.purge = PurgeConfig()
      before.purge.purgeDirs = []
      before.purge.purgeDirs.append(PurgeDir(absolutePath="/whatever", retainDays=3))
      beforeXml = before.extractXml(validate=False)
      after = Config(xmlData=beforeXml, validate=False)
      self.failUnlessEqual(before, after)

   def testExtractXml_029(self):
      """
      Extract document containing only an invalid purge section, validate=True.
      """
      before = Config()
      before.purge = PurgeConfig()
      before.purge.purgeDirs = []
      before.purge.purgeDirs.append(PurgeDir(absolutePath="/whatever"))
      self.failUnlessRaises(ValueError, before.extractXml, validate=True)

   def testExtractXml_030(self):
      """
      Extract document containing only an invalid purge section,
      validate=False.
      """
      before = Config()
      before.purge = PurgeConfig()
      before.purge.purgeDirs = []
      before.purge.purgeDirs.append(PurgeDir(absolutePath="/whatever"))
      beforeXml = before.extractXml(validate=False)
      after = Config(xmlData=beforeXml, validate=False)
      self.failUnlessEqual(before, after)

   def testExtract_031(self):
      """
      Extract complete document containing all required and optional fields,
      validate=False.
      """
      path = self.resources["cback.conf.15"]
      before = Config(xmlPath=path, validate=False)
      beforeXml = before.extractXml(validate=False)
      after = Config(xmlData=beforeXml, validate=False)
      self.failUnlessEqual(before, after)

   def testExtract_032(self):
      """
      Extract complete document containing all required and optional fields,
      validate=True.
      """
      path = self.resources["cback.conf.15"]
      before = Config(xmlPath=path, validate=True)
      beforeXml = before.extractXml(validate=True)
      after = Config(xmlData=beforeXml, validate=True)
      self.failUnlessEqual(before, after)

   def testExtract_033(self):
      """
      Extract a sample from Cedar Backup v1.x, which must still be valid,
      validate=False.
      """
      path = self.resources["cback.conf.1"]
      before = Config(xmlPath=path, validate=False)
      beforeXml = before.extractXml(validate=False)
      after = Config(xmlData=beforeXml, validate=False)
      self.failUnlessEqual(before, after)

   def testExtract_034(self):
      """
      Extract a sample from Cedar Backup v1.x, which must still be valid,
      validate=True.
      """
      path = self.resources["cback.conf.1"]
      before = Config(xmlPath=path, validate=True)
      beforeXml = before.extractXml(validate=True)
      after = Config(xmlData=beforeXml, validate=True)
      self.failUnlessEqual(before, after)


#######################################################################
# Suite definition
#######################################################################

def suite():
   """Returns a suite containing all the test cases in this module."""
   return unittest.TestSuite((
                              unittest.makeSuite(TestCollectDir, 'test'), 
                              unittest.makeSuite(TestPurgeDir, 'test'), 
                              unittest.makeSuite(TestLocalPeer, 'test'), 
                              unittest.makeSuite(TestRemotePeer, 'test'), 
                              unittest.makeSuite(TestReferenceConfig, 'test'), 
                              unittest.makeSuite(TestOptionsConfig, 'test'), 
                              unittest.makeSuite(TestCollectConfig, 'test'), 
                              unittest.makeSuite(TestStageConfig, 'test'), 
                              unittest.makeSuite(TestStoreConfig, 'test'), 
                              unittest.makeSuite(TestPurgeConfig, 'test'), 
                              unittest.makeSuite(TestConfig, 'test'), 
                            ))


########################################################################
# Module entry point
########################################################################

# When this module is executed from the command-line, run its tests
if __name__ == '__main__':
   unittest.main()

