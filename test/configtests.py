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
      pass

   def testConstructor_002(self):
      """
      Test constructor with all values filled in, with valid values.
      """
      pass

   def testConstructor_003(self):
      """
      Test assignment of absolutePath attribute, None value.
      """
      pass

   def testConstructor_004(self):
      """
      Test assignment of absolutePath attribute, valid value.
      """
      pass

   def testConstructor_005(self):
      """
      Test assignment of absolutePath attribute, invalid value (empty).
      """
      pass

   def testConstructor_006(self):
      """
      Test assignment of absolutePath attribute, invalid value (non-absolute).
      """
      pass

   def testConstructor_007(self):
      """
      Test assignment of retainDays attribute, None value.
      """
      pass

   def testConstructor_008(self):
      """
      Test assignment of retainDays attribute, valid value.
      """
      pass

   def testConstructor_009(self):
      """
      Test assignment of retainDays attribute, invalid value (empty).
      """
      pass

   def testConstructor_010(self):
      """
      Test assignment of retainDays attribute, invalid value (non-integer).
      """
      pass


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
      Test comparison of two differing objects, absolutePath differs (one None).
      """
      pass

   def testComparison_004(self):
      """
      Test comparison of two differing objects, absolutePath differs.
      """
      pass

   def testComparison_005(self):
      """
      Test comparison of two differing objects, retainDays differs (one None).
      """
      pass

   def testComparison_006(self):
      """
      Test comparison of two differing objects, retainDays differs.
      """
      pass


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
      pass

   def testConstructor_002(self):
      """
      Test constructor with all values filled in, with valid values.
      """
      pass

   def testConstructor_003(self):
      """
      Test assignment of name attribute, None value.
      """
      pass

   def testConstructor_004(self):
      """
      Test assignment of name attribute, valid value.
      """
      pass

   def testConstructor_005(self):
      """
      Test assignment of name attribute, invalid value (empty).
      """
      pass

   def testConstructor_006(self):
      """
      Test assignment of collectDir attribute, None value.
      """
      pass

   def testConstructor_007(self):
      """
      Test assignment of collectDir attribute, valid value.
      """
      pass

   def testConstructor_008(self):
      """
      Test assignment of collectDir attribute, invalid value (empty).
      """
      pass

   def testConstructor_009(self):
      """
      Test assignment of collectDir attribute, invalid value (non-absolute).
      """
      pass


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
      Test comparison of two differing objects, name differs (one None).
      """
      pass

   def testComparison_004(self):
      """
      Test comparison of two differing objects, name differs.
      """
      pass

   def testComparison_005(self):
      """
      Test comparison of two differing objects, collectDir differs (one None).
      """
      pass

   def testComparison_006(self):
      """
      Test comparison of two differing objects, collectDir differs.
      """
      pass



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
      pass

   def testConstructor_002(self):
      """
      Test constructor with all values filled in, with valid values.
      """
      pass

   def testConstructor_003(self):
      """
      Test assignment of name attribute, None value.
      """
      pass

   def testConstructor_004(self):
      """
      Test assignment of name attribute, valid value.
      """
      pass

   def testConstructor_005(self):
      """
      Test assignment of name attribute, invalid value (empty).
      """
      pass

   def testConstructor_006(self):
      """
      Test assignment of collectDir attribute, None value.
      """
      pass

   def testConstructor_007(self):
      """
      Test assignment of collectDir attribute, valid value.
      """
      pass

   def testConstructor_008(self):
      """
      Test assignment of collectDir attribute, invalid value (empty).
      """
      pass

   def testConstructor_009(self):
      """
      Test assignment of collectDir attribute, invalid value (non-absolute).
      """
      pass

   def testConstructor_010(self):
      """
      Test assignment of remoteUser attribute, None value.
      """
      pass

   def testConstructor_011(self):
      """
      Test assignment of remoteUser attribute, valid value.
      """
      pass

   def testConstructor_012(self):
      """
      Test assignment of remoteUser attribute, invalid value (empty).
      """
      pass

   def testConstructor_013(self):
      """
      Test assignment of rcpCommand attribute, None value.
      """
      pass

   def testConstructor_014(self):
      """
      Test assignment of rcpCommand attribute, valid value.
      """
      pass

   def testConstructor_015(self):
      """
      Test assignment of rcpCommand attribute, invalid value (empty).
      """
      pass


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
      Test comparison of two differing objects, name differs (one None).
      """
      pass

   def testComparison_004(self):
      """
      Test comparison of two differing objects, name differs.
      """
      pass

   def testComparison_005(self):
      """
      Test comparison of two differing objects, collectDir differs (one None).
      """
      pass

   def testComparison_006(self):
      """
      Test comparison of two differing objects, collectDir differs.
      """
      pass

   def testComparison_007(self):
      """
      Test comparison of two differing objects, remoteUser differs (one None).
      """
      pass

   def testComparison_008(self):
      """
      Test comparison of two differing objects, remoteUser differs.
      """
      pass

   def testComparison_009(self):
      """
      Test comparison of two differing objects, rcpCommand differs (one None).
      """
      pass

   def testComparison_010(self):
      """
      Test comparison of two differing objects, rcpCommand differs.
      """
      pass


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
      pass

   def testConstructor_002(self):
      """
      Test constructor with all values filled in, with valid values.
      """
      pass

   def testConstructor_003(self):
      """
      Test assignment of author attribute, None value.
      """
      pass

   def testConstructor_004(self):
      """
      Test assignment of author attribute, valid value.
      """
      pass

   def testConstructor_005(self):
      """
      Test assignment of author attribute, valid value (empty).
      """
      pass

   def testConstructor_006(self):
      """
      Test assignment of revision attribute, None value.
      """
      pass

   def testConstructor_007(self):
      """
      Test assignment of revision attribute, valid value.
      """
      pass

   def testConstructor_008(self):
      """
      Test assignment of revision attribute, valid value (empty).
      """
      pass

   def testConstructor_009(self):
      """
      Test assignment of description attribute, None value.
      """
      pass

   def testConstructor_010(self):
      """
      Test assignment of description attribute, valid value.
      """
      pass

   def testConstructor_011(self):
      """
      Test assignment of description attribute, valid value (empty).
      """
      pass

   def testConstructor_012(self):
      """
      Test assignment of generator attribute, None value.
      """
      pass

   def testConstructor_013(self):
      """
      Test assignment of generator attribute, valid value.
      """
      pass

   def testConstructor_014(self):
      """
      Test assignment of generator attribute, valid value (empty).
      """
      pass


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
      Test comparison of two differing objects, author differs (one None).
      """
      pass

   def testComparison_004(self):
      """
      Test comparison of two differing objects, author differs.
      """
      pass

   def testComparison_005(self):
      """
      Test comparison of two differing objects, revision differs (one None).
      """
      pass

   def testComparison_006(self):
      """
      Test comparison of two differing objects, revision differs.
      """
      pass

   def testComparison_007(self):
      """
      Test comparison of two differing objects, description differs (one None).
      """
      pass

   def testComparison_008(self):
      """
      Test comparison of two differing objects, description differs.
      """
      pass

   def testComparison_009(self):
      """
      Test comparison of two differing objects, generator differs (one None).
      """
      pass

   def testComparison_010(self):
      """
      Test comparison of two differing objects, generator differs.
      """
      pass


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
      pass

   def testConstructor_002(self):
      """
      Test constructor with all values filled in, with valid values.
      """
      pass

   def testConstructor_003(self):
      """
      Test assignment of startingDay attribute, None value.
      """
      pass

   def testConstructor_004(self):
      """
      Test assignment of startingDay attribute, valid value.
      """
      pass

   def testConstructor_005(self):
      """
      Test assignment of startingDay attribute, invalid value (empty).
      """
      pass

   def testConstructor_006(self):
      """
      Test assignment of startingDay attribute, invalid value (not in list).
      """
      pass

   def testConstructor_007(self):
      """
      Test assignment of workingDir attribute, None value.
      """
      pass

   def testConstructor_008(self):
      """
      Test assignment of workingDir attribute, valid value.
      """
      pass

   def testConstructor_009(self):
      """
      Test assignment of workingDir attribute, invalid value (empty).
      """
      pass

   def testConstructor_010(self):
      """
      Test assignment of workingDir attribute, invalid value (non-absolute).
      """
      pass

   def testConstructor_011(self):
      """
      Test assignment of backupUser attribute, None value.
      """
      pass

   def testConstructor_012(self):
      """
      Test assignment of backupUser attribute, valid value.
      """
      pass

   def testConstructor_013(self):
      """
      Test assignment of backupUser attribute, invalid value (empty).
      """
      pass

   def testConstructor_014(self):
      """
      Test assignment of backupGroup attribute, None value.
      """
      pass

   def testConstructor_015(self):
      """
      Test assignment of backupGroup attribute, valid value.
      """
      pass

   def testConstructor_016(self):
      """
      Test assignment of backupGroup attribute, invalid value (empty).
      """
      pass

   def testConstructor_017(self):
      """
      Test assignment of rcpCommand attribute, None value.
      """
      pass

   def testConstructor_018(self):
      """
      Test assignment of rcpCommand attribute, valid value.
      """
      pass

   def testConstructor_019(self):
      """
      Test assignment of rcpCommand attribute, invalid value (empty).
      """
      pass


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
      Test comparison of two differing objects, startingDay differs (one None).
      """
      pass

   def testComparison_004(self):
      """
      Test comparison of two differing objects, startingDay differs.
      """
      pass

   def testComparison_005(self):
      """
      Test comparison of two differing objects, workingDir differs (one None).
      """
      pass

   def testComparison_006(self):
      """
      Test comparison of two differing objects, workingDir differs.
      """
      pass

   def testComparison_007(self):
      """
      Test comparison of two differing objects, backupUser differs (one None).
      """
      pass

   def testComparison_008(self):
      """
      Test comparison of two differing objects, backupUser differs.
      """
      pass

   def testComparison_009(self):
      """
      Test comparison of two differing objects, backupGroup differs (one None).
      """
      pass

   def testComparison_010(self):
      """
      Test comparison of two differing objects, backupGroup differs.
      """
      pass

   def testComparison_011(self):
      """
      Test comparison of two differing objects, rcpCommand differs (one None).
      """
      pass

   def testComparison_012(self):
      """
      Test comparison of two differing objects, rcpCommand differs.
      """
      pass



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
      pass

   def testConstructor_002(self):
      """
      Test constructor with all values filled in, with valid values.
      """
      pass

   def testConstructor_003(self):
      """
      Test assignment of targetDir attribute, None value.
      """
      pass

   def testConstructor_004(self):
      """
      Test assignment of targetDir attribute, valid value.
      """
      pass

   def testConstructor_005(self):
      """
      Test assignment of targetDir attribute, invalid value (empty).
      """
      pass

   def testConstructor_006(self):
      """
      Test assignment of targetDir attribute, invalid value (non-absolute).
      """
      pass

   def testConstructor_007(self):
      """
      Test assignment of collectMode attribute, None value.
      """
      pass

   def testConstructor_008(self):
      """
      Test assignment of collectMode attribute, valid value.
      """
      pass

   def testConstructor_009(self):
      """
      Test assignment of collectMode attribute, invalid value (empty).
      """
      pass

   def testConstructor_010(self):
      """
      Test assignment of collectMode attribute, invalid value (not in list).
      """
      pass

   def testConstructor_011(self):
      """
      Test assignment of archiveMode attribute, None value.
      """
      pass

   def testConstructor_012(self):
      """
      Test assignment of archiveMode attribute, valid value.
      """
      pass

   def testConstructor_013(self):
      """
      Test assignment of archiveMode attribute, invalid value (empty).
      """
      pass

   def testConstructor_014(self):
      """
      Test assignment of archiveMode attribute, invalid value (not in list).
      """
      pass

   def testConstructor_015(self):
      """
      Test assignment of ignoreFile attribute, None value.
      """
      pass

   def testConstructor_016(self):
      """
      Test assignment of ignoreFile attribute, valid value.
      """
      pass

   def testConstructor_017(self):
      """
      Test assignment of ignoreFile attribute, invalid value (empty).
      """
      pass

   def testConstructor_018(self):
      """
      Test assignment of absoluteExcludePaths attribute, None value.
      """
      pass

   def testConstructor_019(self):
      """
      Test assignment of absoluteExcludePaths attribute, [] value.
      """
      pass

   def testConstructor_020(self):
      """
      Test assignment of absoluteExcludePaths attribute, single valid entry.
      """
      pass

   def testConstructor_021(self):
      """
      Test assignment of absoluteExcludePaths attribute, multiple valid
      entries.
      """
      pass

   def testConstructor_022(self):
      """
      Test assignment of absoluteExcludePaths attribute, single invalid entry
      (empty).
      """
      pass

   def testConstructor_023(self):
      """
      Test assignment of absoluteExcludePaths attribute, single invalid entry
      (not absolute).
      """
      pass

   def testConstructor_024(self):
      """
      Test assignment of absoluteExcludePaths attribute, mixed valid and
      invalid entries.
      """
      pass

   def testConstructor_025(self):
      """
      Test assignment of excludePatterns attribute, None value.
      """
      pass

   def testConstructor_026(self):
      """
      Test assignment of excludePatterns attribute, [] value.
      """
      pass

   def testConstructor_027(self):
      """
      Test assignment of excludePatterns attribute, single valid entry.
      """
      pass

   def testConstructor_028(self):
      """
      Test assignment of excludePatterns attribute, multiple valid entries.
      """
      pass

   def testConstructor_029(self):
      """
      Test assignment of excludePatterns attribute, single invalid entry
      (empty).
      """
      pass

   def testConstructor_030(self):
      """
      Test assignment of excludePatterns attribute, mixed valid and invalid
      entries.
      """
      pass

   def testConstructor_031(self):
      """
      Test assignment of collectDirs attribute, None value.
      """
      pass

   def testConstructor_032(self):
      """
      Test assignment of collectDirs attribute, [] value.
      """
      pass

   def testConstructor_033(self):
      """
      Test assignment of collectDirs attribute, single valid entry.
      """
      pass

   def testConstructor_034(self):
      """
      Test assignment of collectDirs attribute, multiple valid
      entries.
      """
      pass

   def testConstructor_035(self):
      """
      Test assignment of collectDirs attribute, single invalid entry
      (None).
      """
      pass

   def testConstructor_036(self):
      """
      Test assignment of collectDirs attribute, single invalid entry
      (not a CollectDir).
      """
      pass

   def testConstructor_037(self):
      """
      Test assignment of collectDirs attribute, mixed valid and
      invalid entries.
      """
      pass


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
      pass

   def testConstructor_002(self):
      """
      Test constructor with all values filled in, with valid values.
      """
      pass

   def testConstructor_003(self):
      """
      Test assignment of targetDir attribute, None value.
      """
      pass

   def testConstructor_004(self):
      """
      Test assignment of targetDir attribute, valid value.
      """
      pass

   def testConstructor_005(self):
      """
      Test assignment of targetDir attribute, invalid value (empty).
      """
      pass

   def testConstructor_006(self):
      """
      Test assignment of targetDir attribute, invalid value (non-absolute).
      """
      pass

   def testConstructor_007(self):
      """
      Test assignment of localPeers attribute, single valid entry.
      """
      pass

   def testConstructor_008(self):
      """
      Test assignment of localPeers attribute, multiple valid
      entries.
      """
      pass

   def testConstructor_009(self):
      """
      Test assignment of localPeers attribute, single invalid entry
      (None).
      """
      pass

   def testConstructor_010(self):
      """
      Test assignment of localPeers attribute, single invalid entry
      (not a LocalPeer).
      """
      pass

   def testConstructor_011(self):
      """
      Test assignment of localPeers attribute, mixed valid and
      invalid entries.
      """
      pass

   def testConstructor_012(self):
      """
      Test assignment of remotePeers attribute, single valid entry.
      """
      pass

   def testConstructor_013(self):
      """
      Test assignment of remotePeers attribute, multiple valid
      entries.
      """
      pass

   def testConstructor_014(self):
      """
      Test assignment of remotePeers attribute, single invalid entry
      (None).
      """
      pass

   def testConstructor_015(self):
      """
      Test assignment of remotePeers attribute, single invalid entry
      (not a RemotePeer).
      """
      pass

   def testConstructor_016(self):
      """
      Test assignment of remotePeers attribute, mixed valid and
      invalid entries.
      """
      pass


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
      Test comparison of two differing objects, localPeers differs (one None,
      one empty).
      """
      pass

   def testComparison_006(self):
      """
      Test comparison of two differing objects, localPeers differs (one None,
      one not empty).
      """
      pass

   def testComparison_007(self):
      """
      Test comparison of two differing objects, localPeers differs (one empty,
      one not empty).
      """
      pass

   def testComparison_008(self):
      """
      Test comparison of two differing objects, localPeers differs (both not
      empty).
      """
      pass

   def testComparison_009(self):
      """
      Test comparison of two differing objects, remotePeers differs (one None,
      one empty).
      """
      pass

   def testComparison_010(self):
      """
      Test comparison of two differing objects, remotePeers differs (one None,
      one not empty).
      """
      pass

   def testComparison_011(self):
      """
      Test comparison of two differing objects, remotePeers differs (one empty,
      one not empty).
      """
      pass

   def testComparison_012(self):
      """
      Test comparison of two differing objects, remotePeers differs (both not
      empty).
      """
      pass



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
      pass

   def testConstructor_002(self):
      """
      Test constructor with all values filled in, with valid values.
      """
      pass

   def testConstructor_003(self):
      """
      Test assignment of sourceDir attribute, None value.
      """
      pass

   def testConstructor_004(self):
      """
      Test assignment of sourceDir attribute, valid value.
      """
      pass

   def testConstructor_005(self):
      """
      Test assignment of sourceDir attribute, invalid value (empty).
      """
      pass

   def testConstructor_006(self):
      """
      Test assignment of sourceDir attribute, invalid value (non-absolute).
      """
      pass

   def testConstructor_007(self):
      """
      Test assignment of mediaType attribute, None value.
      """
      pass

   def testConstructor_008(self):
      """
      Test assignment of mediaType attribute, valid value.
      """
      pass

   def testConstructor_009(self):
      """
      Test assignment of mediaType attribute, invalid value (empty).
      """
      pass

   def testConstructor_010(self):
      """
      Test assignment of mediaType attribute, invalid value (not in list).
      """
      pass

   def testConstructor_011(self):
      """
      Test assignment of deviceType attribute, None value.
      """
      pass

   def testConstructor_012(self):
      """
      Test assignment of deviceType attribute, valid value.
      """
      pass

   def testConstructor_013(self):
      """
      Test assignment of deviceType attribute, invalid value (empty).
      """
      pass

   def testConstructor_014(self):
      """
      Test assignment of deviceType attribute, invalid value (not in list).
      """
      pass

   def testConstructor_015(self):
      """
      Test assignment of devicePath attribute, None value.
      """
      pass

   def testConstructor_016(self):
      """
      Test assignment of devicePath attribute, valid value.
      """
      pass

   def testConstructor_017(self):
      """
      Test assignment of devicePath attribute, invalid value (empty).
      """
      pass

   def testConstructor_018(self):
      """
      Test assignment of devicePath attribute, invalid value (non-absolute).
      """
      pass

   def testConstructor_019(self):
      """
      Test assignment of deviceScsiId attribute, None value.
      """
      pass

   def testConstructor_020(self):
      """
      Test assignment of deviceScsiId attribute, valid value.
      """
      pass

   def testConstructor_021(self):
      """
      Test assignment of deviceScsiId attribute, invalid value (empty).
      """
      pass

   def testConstructor_022(self):
      """
      Test assignment of deviceScsiId attribute, invalid value (invalid id).
      """
      pass

   def testConstructor_023(self):
      """
      Test assignment of driveSpeed attribute, None value.
      """
      pass

   def testConstructor_024(self):
      """
      Test assignment of driveSpeed attribute, valid value.
      """
      pass

   def testConstructor_025(self):
      """
      Test assignment of driveSpeed attribute, invalid value (not an integer).
      """
      pass

   def testConstructor_026(self):
      """
      Test assignment of checkData attribute, None value.
      """
      pass

   def testConstructor_027(self):
      """
      Test assignment of checkData attribute, valid value (real boolean).
      """
      pass

   def testConstructor_028(self):
      """
      Test assignment of checkData attribute, valid value (expression).
      """
      pass

   def testConstructor_029(self):
      """
      Test assignment of safeOverwrite attribute, None value.
      """
      pass

   def testConstructor_030(self):
      """
      Test assignment of safeOverwrite attribute, valid value (real boolean).
      """
      pass

   def testConstructor_031(self):
      """
      Test assignment of safeOverwrite attribute, valid value (expression).
      """
      pass

   def testConstructor_032(self):
      """
      Test assignment of capacityMode attribute, None value.
      """
      pass

   def testConstructor_033(self):
      """
      Test assignment of capacityMode attribute, valid value.
      """
      pass

   def testConstructor_034(self):
      """
      Test assignment of capacityMode attribute, invalid value (empty).
      """
      pass

   def testConstructor_035(self):
      """
      Test assignment of capacityMode attribute, invalid value (not in list).
      """
      pass


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
      Test comparison of two differing objects, sourceDir differs (one None).
      """
      pass

   def testComparison_004(self):
      """
      Test comparison of two differing objects, sourceDir differs.
      """
      pass

   def testComparison_005(self):
      """
      Test comparison of two differing objects, mediaType differs (one None).
      """
      pass

   def testComparison_006(self):
      """
      Test comparison of two differing objects, mediaType differs.
      """
      pass

   def testComparison_007(self):
      """
      Test comparison of two differing objects, deviceType differs (one None).
      """
      pass

   def testComparison_008(self):
      """
      Test comparison of two differing objects, deviceType differs.
      """
      pass

   def testComparison_009(self):
      """
      Test comparison of two differing objects, devicePath differs (one None).
      """
      pass

   def testComparison_010(self):
      """
      Test comparison of two differing objects, devicePath differs.
      """
      pass

   def testComparison_011(self):
      """
      Test comparison of two differing objects, deviceScsiId differs (one None).
      """
      pass

   def testComparison_012(self):
      """
      Test comparison of two differing objects, deviceScsiId differs.
      """
      pass

   def testComparison_013(self):
      """
      Test comparison of two differing objects, driveSpeed differs (one None).
      """
      pass

   def testComparison_014(self):
      """
      Test comparison of two differing objects, driveSpeed differs.
      """
      pass

   def testComparison_015(self):
      """
      Test comparison of two differing objects, checkData differs.
      """
      pass

   def testComparison_016(self):
      """
      Test comparison of two differing objects, safeOverwrite differs.
      """
      pass

   def testComparison_017(self):
      """
      Test comparison of two differing objects, capacityMode differs (one None).
      """
      pass

   def testComparison_018(self):
      """
      Test comparison of two differing objects, capacityMode differs.
      """
      pass



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
      pass

   def testConstructor_002(self):
      """
      Test constructor with all values filled in, with valid values.
      """
      pass

   def testConstructor_003(self):
      """
      Test assignment of purgeDirs attribute, None value.
      """
      pass

   def testConstructor_004(self):
      """
      Test assignment of purgeDirs attribute, [] value.
      """
      pass

   def testConstructor_005(self):
      """
      Test assignment of purgeDirs attribute, single valid entry.
      """
      pass

   def testConstructor_006(self):
      """
      Test assignment of purgeDirs attribute, multiple valid entries.
      """
      pass

   def testConstructor_007(self):
      """
      Test assignment of purgeDirs attribute, single invalid entry (empty).
      """
      pass

   def testConstructor_008(self):
      """
      Test assignment of purgeDirs attribute, single invalid entry (not
      absolute).
      """
      pass

   def testConstructor_009(self):
      """
      Test assignment of purgeDirs attribute, mixed valid and invalid entries.
      """
      pass


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
      Test comparison of two identical objects, all attributes non-None (empty
      lists).
      """
      pass

   def testComparison_003(self):
      """
      Test comparison of two identical objects, all attributes non-None
      (non-empty lists).
      """
      pass

   def testComparison_004(self):
      """
      Test comparison of two differing objects, purgeDirs differs (one None,
      one empty).
      """
      pass

   def testComparison_005(self):
      """
      Test comparison of two differing objects, purgeDirs differs (one None,
      one not empty).
      """
      pass

   def testComparison_006(self):
      """
      Test comparison of two differing objects, purgeDirs differs (one empty,
      one not empty).
      """
      pass

   def testComparison_007(self):
      """
      Test comparison of two differing objects, purgeDirs differs (both not
      empty).
      """
      pass


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

