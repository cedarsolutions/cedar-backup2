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
from CedarBackup2.config import CollectDir, PurgeDir, LocalPeer, RemotePeer
from CedarBackup2.config import ReferenceConfig, OptionsConfig, CollectConfig
from CedarBackup2.config import StageConfig, StoreConfig, PurgeConfig, Config


#######################################################################
# Module-wide configuration and constants
#######################################################################

DATA_DIRS = [ "./data", "./test/data", ]
RESOURCES = [ "cback.conf.1", "cback.conf.2", "cback.conf.3", "cback.conf.4", "cback.conf.5", 
              "cback.conf.6", "cback.conf.7", "cback.conf.8", "cback.conf.9", "cback.conf.10", 
              "cback.conf.11", "cback.conf.12", "cback.conf.13", "cback.conf.14", ]


#######################################################################
# Utility functions
#######################################################################

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

def failUnlessAssignRaises(testCase, exception, object, property, value):
   """
   Equivalent of C{failUnlessRaises}, but used for property assignments instead.

   It's nice to be able to use C{failUnlessRaises} to check that a method call
   raises the exception that you expect.  Unfortunately, this method can't be
   used to check Python propery assignments, even though these property
   assignments are actually implemented underneath as methods.  

   This function (which can be easily called by unit test classes) provides an
   easy way to wrap the assignment checks.  It's not pretty, or as intuitive as
   the original check it's modeled on, but it does work.

   Let's assume you make this method call:

      testCase.failUnlessAssignRaises(ValueError, collectDir, "absolutePath", absolutePath)

   If you do this, a test case failure will be raised unless the assignment:

      collectDir.absolutePath = absolutePath

   fails with a C{ValueError} exception.  The failure message differentiates
   between the case where no exception was raised and the case where the wrong
   exception was raised.

   @note: The C{missed} and C{instead} variables are used rather than directly
   calling C{testCase.fail} upon noticing a problem because the act of
   "failure" itself generates an exception that would be caught by the general
   C{except} clause.

   @param testCase: PyUnit test case object (i.e. self).
   @param exception: Exception that is expected to be raised.
   @param object: Object whose property is to be assigned to.
   @param property: Name of the property, as a string.
   @param value: Value that is to be assigned to the property.

   @see: L{unittest.TestCase.failUnlessRaises}
   """
   missed = False
   instead = None
   try:
      exec "object.%s = value" % property
      missed = True
   except exception: pass
   except Exception, e: instead = e
   if missed:
      testCase.fail("Expected assignment to raise %s, but got no exception." % (exception.__name__))
   if instead is not None:
      testCase.fail("Expected assignment to raise %s, but got %s instead." % (ValueError, instead.__class__.__name__))


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
         self.resources = findResources()
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
         self.resources = findResources()
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
         self.resources = findResources()
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
         self.resources = findResources()
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
         self.resources = findResources()
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
         self.resources = findResources()
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
         self.resources = findResources()
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
         self.resources = findResources()
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
         self.resources = findResources()
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
         self.resources = findResources()
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
         self.resources = findResources()
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

