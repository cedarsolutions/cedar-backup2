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
# Copyright (c) 2005 Kenneth J. Pronovici.
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
# Purpose  : Tests Subversion extension functionality.
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# This file was created with a width of 132 characters, and NO tabs.

########################################################################
# Module documentation
########################################################################

"""
Unit tests for CedarBackup2/extend/subversion.py.

Code Coverage
=============

   This module contains individual tests for the many of the public functions
   and classes implemented in extend/subversions.py.  There are also tests for
   several of the private methods.

   Unfortunately, it's rather difficult to test this code in an automated
   fashion, even if you have access to Subversion, since the actual backup
   would need to have access to real Subversion repositories.  Because of this,
   there aren't any tests below that actually back up repositories.

   As a compromise, I test some of the private methods in the implementation.
   Normally, I don't like to test private methods, but in this case, testing
   the private methods will help give us some reasonable confidence in the code
   even if we can't talk to Subversion successfully.  This isn't perfect, but
   it's better than nothing.

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
   is extract a node, build some XML from it, and then feed that XML back into
   another object's constructor.  If that parse process succeeds and the old
   object is equal to the new object, we assume that the extract was
   successful.  

   It would argumably be better if we could do a completely independent check -
   but implementing that check would be equivalent to re-implementing all of
   the existing functionality that we're validating here!  After all, the most
   important thing is that data can move seamlessly from object to XML document
   and back to object.

Full vs. Reduced Tests
======================

   All of the tests in this module are considered safe to be run in an average
   build environment.  There is a no need to use a SUBVERSIONTESTS_FULL
   environment variable to provide a "reduced feature set" test suite as for
   some of the other test modules.

@author Kenneth J. Pronovici <pronovic@ieee.org>
"""


########################################################################
# Import modules and do runtime validations
########################################################################

# System modules
import unittest
from gzip import GzipFile
from bz2 import BZ2File
import os
from StringIO import StringIO

# XML-related modules
from xml.dom.minidom import getDOMImplementation
from xml.dom.ext import PrettyPrint

# Cedar Backup modules
from CedarBackup2.testutil import findResources, buildPath, removedir, failUnlessAssignRaises
from CedarBackup2.extend.subversion import LocalConfig, SubversionConfig, BDBRepository


#######################################################################
# Module-wide configuration and constants
#######################################################################

DATA_DIRS = [ "./data", "./test/data", ]
RESOURCES = [ "subversion.conf.1", "subversion.conf.2", "subversion.conf.3", "subversion.conf.4", ]


#######################################################################
# Test Case Classes
#######################################################################

##########################
# TestBDBRepository class
##########################

class TestBDBRepository(unittest.TestCase):

   """Tests for the BDBRepository class."""

   ##################
   # Utility methods
   ##################

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
      obj = BDBRepository()
      obj.__repr__()
      obj.__str__()


   ##################################
   # Test constructor and attributes
   ##################################

   def testConstructor_001(self):
      """
      Test constructor with no values filled in.
      """
      repository = BDBRepository()
      self.failUnlessEqual("BDB", repository.repositoryType)
      self.failUnlessEqual(None, repository.repositoryPath)
      self.failUnlessEqual(None, repository.collectMode)
      self.failUnlessEqual(None, repository.compressMode)

   def testConstructor_002(self):
      """
      Test constructor with all values filled in.
      """
      repository = BDBRepository("/path/to/it", "daily", "gzip")
      self.failUnlessEqual("BDB", repository.repositoryType)
      self.failUnlessEqual("/path/to/it", repository.repositoryPath)
      self.failUnlessEqual("daily", repository.collectMode)
      self.failUnlessEqual("gzip", repository.compressMode)

   def testConstructor_003(self):
      """
      Test assignment of repositoryType attribute.
      """
      repository = BDBRepository()
      self.failUnlessAssignRaises(AttributeError, repository, "repositoryType", "")

   def testConstructor_004(self):
      """
      Test assignment of repositoryPath attribute, None value.
      """
      repository = BDBRepository(repositoryPath="/path/to/something")
      self.failUnlessEqual("/path/to/something", repository.repositoryPath)
      repository.repositoryPath = None
      self.failUnlessEqual(None, repository.repositoryPath)

   def testConstructor_005(self):
      """
      Test assignment of repositoryPath attribute, valid value.
      """
      repository = BDBRepository()
      self.failUnlessEqual(None, repository.repositoryPath)
      repository.repositoryPath = "/path/to/whatever"
      self.failUnlessEqual("/path/to/whatever", repository.repositoryPath)

   def testConstructor_006(self):
      """
      Test assignment of repositoryPath attribute, invalid value (empty).
      """
      repository = BDBRepository()
      self.failUnlessEqual(None, repository.repositoryPath)
      self.failUnlessAssignRaises(ValueError, repository, "repositoryPath", "")
      self.failUnlessEqual(None, repository.repositoryPath)

   def testConstructor_007(self):
      """
      Test assignment of repositoryPath attribute, invalid value (not absolute).
      """
      repository = BDBRepository()
      self.failUnlessEqual(None, repository.repositoryPath)
      self.failUnlessAssignRaises(ValueError, repository, "repositoryPath", "relative/path")
      self.failUnlessEqual(None, repository.repositoryPath)

   def testConstructor_008(self):
      """
      Test assignment of collectMode attribute, None value.
      """
      repository = BDBRepository(collectMode="daily")
      self.failUnlessEqual("daily", repository.collectMode)
      repository.collectMode = None
      self.failUnlessEqual(None, repository.collectMode)

   def testConstructor_009(self):
      """
      Test assignment of collectMode attribute, valid value.
      """
      repository = BDBRepository()
      self.failUnlessEqual(None, repository.collectMode)
      repository.collectMode = "daily"
      self.failUnlessEqual("daily", repository.collectMode)
      repository.collectMode = "weekly"
      self.failUnlessEqual("weekly", repository.collectMode)
      repository.collectMode = "incr"
      self.failUnlessEqual("incr", repository.collectMode)

   def testConstructor_010(self):
      """
      Test assignment of collectMode attribute, invalid value (empty).
      """
      repository = BDBRepository()
      self.failUnlessEqual(None, repository.collectMode)
      self.failUnlessAssignRaises(ValueError, repository, "collectMode", "")
      self.failUnlessEqual(None, repository.collectMode)

   def testConstructor_011(self):
      """
      Test assignment of collectMode attribute, invalid value (not in list).
      """
      repository = BDBRepository()
      self.failUnlessEqual(None, repository.collectMode)
      self.failUnlessAssignRaises(ValueError, repository, "collectMode", "monthly")
      self.failUnlessEqual(None, repository.collectMode)

   def testConstructor_012(self):
      """
      Test assignment of compressMode attribute, None value.
      """
      repository = BDBRepository(compressMode="gzip")
      self.failUnlessEqual("gzip", repository.compressMode)
      repository.compressMode = None
      self.failUnlessEqual(None, repository.compressMode)

   def testConstructor_013(self):
      """
      Test assignment of compressMode attribute, valid value.
      """
      repository = BDBRepository()
      self.failUnlessEqual(None, repository.compressMode)
      repository.compressMode = "bzip2"
      self.failUnlessEqual("bzip2", repository.compressMode)
      repository.compressMode = "gzip"
      self.failUnlessEqual("gzip", repository.compressMode)

   def testConstructor_014(self):
      """
      Test assignment of compressMode attribute, invalid value (empty).
      """
      repository = BDBRepository()
      self.failUnlessEqual(None, repository.compressMode)
      self.failUnlessAssignRaises(ValueError, repository, "compressMode", "")
      self.failUnlessEqual(None, repository.compressMode)

   def testConstructor_015(self):
      """
      Test assignment of compressMode attribute, invalid value (not in list).
      """
      repository = BDBRepository()
      self.failUnlessEqual(None, repository.compressMode)
      self.failUnlessAssignRaises(ValueError, repository, "compressMode", "compress")
      self.failUnlessEqual(None, repository.compressMode)


   ############################
   # Test comparison operators
   ############################

   def testComparison_001(self):
      """
      Test comparison of two identical objects, all attributes None.
      """
      repository1 = BDBRepository()
      repository2 = BDBRepository()
      self.failUnlessEqual(repository1, repository2)
      self.failUnless(repository1 == repository2)
      self.failUnless(not repository1 < repository2)
      self.failUnless(repository1 <= repository2)
      self.failUnless(not repository1 > repository2)
      self.failUnless(repository1 >= repository2)
      self.failUnless(not repository1 != repository2)

   def testComparison_002(self):
      """
      Test comparison of two identical objects, all attributes non-None.
      """
      repository1 = BDBRepository("/path", "daily", "gzip")
      repository2 = BDBRepository("/path", "daily", "gzip")
      self.failUnlessEqual(repository1, repository2)
      self.failUnless(repository1 == repository2)
      self.failUnless(not repository1 < repository2)
      self.failUnless(repository1 <= repository2)
      self.failUnless(not repository1 > repository2)
      self.failUnless(repository1 >= repository2)
      self.failUnless(not repository1 != repository2)

   def testComparison_003(self):
      """
      Test comparison of two differing objects, repositoryPath differs (one None).
      """
      repository1 = BDBRepository()
      repository2 = BDBRepository(repositoryPath="/zippy")
      self.failIfEqual(repository1, repository2)
      self.failUnless(not repository1 == repository2)
      self.failUnless(repository1 < repository2)
      self.failUnless(repository1 <= repository2)
      self.failUnless(not repository1 > repository2)
      self.failUnless(not repository1 >= repository2)
      self.failUnless(repository1 != repository2)

   def testComparison_004(self):
      """
      Test comparison of two differing objects, repositoryPath differs.
      """
      repository1 = BDBRepository("/path", "daily", "gzip")
      repository2 = BDBRepository("/zippy", "daily", "gzip")
      self.failIfEqual(repository1, repository2)
      self.failUnless(not repository1 == repository2)
      self.failUnless(repository1 < repository2)
      self.failUnless(repository1 <= repository2)
      self.failUnless(not repository1 > repository2)
      self.failUnless(not repository1 >= repository2)
      self.failUnless(repository1 != repository2)

   def testComparison_005(self):
      """
      Test comparison of two differing objects, collectMode differs (one None).
      """
      repository1 = BDBRepository()
      repository2 = BDBRepository(collectMode="incr")
      self.failIfEqual(repository1, repository2)
      self.failUnless(not repository1 == repository2)
      self.failUnless(repository1 < repository2)
      self.failUnless(repository1 <= repository2)
      self.failUnless(not repository1 > repository2)
      self.failUnless(not repository1 >= repository2)
      self.failUnless(repository1 != repository2)

   def testComparison_006(self):
      """
      Test comparison of two differing objects, collectMode differs.
      """
      repository1 = BDBRepository("/path", "daily", "gzip")
      repository2 = BDBRepository("/path", "incr", "gzip")
      self.failIfEqual(repository1, repository2)
      self.failUnless(not repository1 == repository2)
      self.failUnless(repository1 < repository2)
      self.failUnless(repository1 <= repository2)
      self.failUnless(not repository1 > repository2)
      self.failUnless(not repository1 >= repository2)
      self.failUnless(repository1 != repository2)

   def testComparison_007(self):
      """
      Test comparison of two differing objects, compressMode differs (one None).
      """
      repository1 = BDBRepository()
      repository2 = BDBRepository(compressMode="gzip")
      self.failIfEqual(repository1, repository2)
      self.failUnless(not repository1 == repository2)
      self.failUnless(repository1 < repository2)
      self.failUnless(repository1 <= repository2)
      self.failUnless(not repository1 > repository2)
      self.failUnless(not repository1 >= repository2)
      self.failUnless(repository1 != repository2)

   def testComparison_008(self):
      """
      Test comparison of two differing objects, compressMode differs.
      """
      repository1 = BDBRepository("/path", "daily", "bzip2")
      repository2 = BDBRepository("/path", "daily", "gzip")
      self.failIfEqual(repository1, repository2)
      self.failUnless(not repository1 == repository2)
      self.failUnless(repository1 < repository2)
      self.failUnless(repository1 <= repository2)
      self.failUnless(not repository1 > repository2)
      self.failUnless(not repository1 >= repository2)
      self.failUnless(repository1 != repository2)


#############################
# TestSubversionConfig class
#############################

class TestSubversionConfig(unittest.TestCase):

   """Tests for the SubversionConfig class."""

   ##################
   # Utility methods
   ##################

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
      obj = SubversionConfig()
      obj.__repr__()
      obj.__str__()


   ##################################
   # Test constructor and attributes
   ##################################

   def testConstructor_001(self):
      """
      Test constructor with no values filled in.
      """
      subversion = SubversionConfig()
      self.failUnlessEqual(None, subversion.collectMode)
      self.failUnlessEqual(None, subversion.compressMode)
      self.failUnlessEqual(None, subversion.repositories)

   def testConstructor_002(self):
      """
      Test constructor with all values filled in, with valid values, repositories=None.
      """
      subversion = SubversionConfig("daily", "gzip", None)
      self.failUnlessEqual("daily", subversion.collectMode)
      self.failUnlessEqual("gzip", subversion.compressMode)
      self.failUnlessEqual(None, subversion.repositories)

   def testConstructor_003(self):
      """
      Test constructor with all values filled in, with valid values, no repositories.
      """
      subversion = SubversionConfig("daily", "gzip", [])
      self.failUnlessEqual("daily", subversion.collectMode)
      self.failUnlessEqual("gzip", subversion.compressMode)
      self.failUnlessEqual([], subversion.repositories)

   def testConstructor_004(self):
      """
      Test constructor with all values filled in, with valid values, with one repository.
      """
      repositories = [ BDBRepository(), ]
      subversion = SubversionConfig("daily", "gzip", repositories)
      self.failUnlessEqual("daily", subversion.collectMode)
      self.failUnlessEqual("gzip", subversion.compressMode)
      self.failUnlessEqual(repositories, subversion.repositories)

   def testConstructor_005(self):
      """
      Test constructor with all values filled in, with valid values, with multiple repositories.
      """
      repositories = [ BDBRepository(collectMode="daily"), BDBRepository(collectMode="weekly"), ]
      subversion = SubversionConfig("daily", "gzip", repositories=repositories)
      self.failUnlessEqual("daily", subversion.collectMode)
      self.failUnlessEqual("gzip", subversion.compressMode)
      self.failUnlessEqual(repositories, subversion.repositories)

   def testConstructor_006(self):
      """
      Test assignment of collectMode attribute, None value.
      """
      subversion = SubversionConfig(collectMode="daily")
      self.failUnlessEqual("daily", subversion.collectMode)
      subversion.collectMode = None
      self.failUnlessEqual(None, subversion.collectMode)

   def testConstructor_007(self):
      """
      Test assignment of collectMode attribute, valid value.
      """
      subversion = SubversionConfig()
      self.failUnlessEqual(None, subversion.collectMode)
      subversion.collectMode = "weekly"
      self.failUnlessEqual("weekly", subversion.collectMode)

   def testConstructor_008(self):
      """
      Test assignment of collectMode attribute, invalid value (empty).
      """
      subversion = SubversionConfig()
      self.failUnlessEqual(None, subversion.collectMode)
      self.failUnlessAssignRaises(ValueError, subversion, "collectMode", "")
      self.failUnlessEqual(None, subversion.collectMode)

   def testConstructor_009(self):
      """
      Test assignment of compressMode attribute, None value.
      """
      subversion = SubversionConfig(compressMode="gzip")
      self.failUnlessEqual("gzip", subversion.compressMode)
      subversion.compressMode = None
      self.failUnlessEqual(None, subversion.compressMode)

   def testConstructor_010(self):
      """
      Test assignment of compressMode attribute, valid value.
      """
      subversion = SubversionConfig()
      self.failUnlessEqual(None, subversion.compressMode)
      subversion.compressMode = "bzip2"
      self.failUnlessEqual("bzip2", subversion.compressMode)

   def testConstructor_011(self):
      """
      Test assignment of compressMode attribute, invalid value (empty).
      """
      subversion = SubversionConfig()
      self.failUnlessEqual(None, subversion.compressMode)
      self.failUnlessAssignRaises(ValueError, subversion, "compressMode", "")
      self.failUnlessEqual(None, subversion.compressMode)

   def testConstructor_012(self):
      """
      Test assignment of repositories attribute, None value.
      """
      subversion = SubversionConfig(repositories=[])
      self.failUnlessEqual([], subversion.repositories)
      subversion.repositories = None
      self.failUnlessEqual(None, subversion.repositories)

   def testConstructor_013(self):
      """
      Test assignment of repositories attribute, [] value.
      """
      subversion = SubversionConfig()
      self.failUnlessEqual(None, subversion.repositories)
      subversion.repositories = []
      self.failUnlessEqual([], subversion.repositories)

   def testConstructor_014(self):
      """
      Test assignment of repositories attribute, single valid entry.
      """
      subversion = SubversionConfig()
      self.failUnlessEqual(None, subversion.repositories)
      subversion.repositories = [ BDBRepository(), ]
      self.failUnlessEqual([ BDBRepository(), ], subversion.repositories)
      subversion.repositories.append(BDBRepository(collectMode="daily"))
      self.failUnlessEqual([ BDBRepository(), BDBRepository(collectMode="daily"), ], subversion.repositories)

   def testConstructor_015(self):
      """
      Test assignment of repositories attribute, multiple valid entries.
      """
      subversion = SubversionConfig()
      self.failUnlessEqual(None, subversion.repositories)
      subversion.repositories = [ BDBRepository(collectMode="daily"), BDBRepository(collectMode="weekly"), ]
      self.failUnlessEqual([ BDBRepository(collectMode="daily"), BDBRepository(collectMode="weekly"), ], subversion.repositories)
      subversion.repositories.append(BDBRepository(collectMode="incr"))
      self.failUnlessEqual([ BDBRepository(collectMode="daily"), BDBRepository(collectMode="weekly"), BDBRepository(collectMode="incr"), ], subversion.repositories)

   def testConstructor_016(self):
      """
      Test assignment of repositories attribute, single invalid entry (None).
      """
      subversion = SubversionConfig()
      self.failUnlessEqual(None, subversion.repositories)
      self.failUnlessAssignRaises(ValueError, subversion, "repositories", [None, ])
      self.failUnlessEqual(None, subversion.repositories)

   def testConstructor_017(self):
      """
      Test assignment of repositories attribute, single invalid entry (wrong type).
      """
      subversion = SubversionConfig()
      self.failUnlessEqual(None, subversion.repositories)
      self.failUnlessAssignRaises(ValueError, subversion, "repositories", [SubversionConfig(), ])
      self.failUnlessEqual(None, subversion.repositories)

   def testConstructor_018(self):
      """
      Test assignment of repositories attribute, mixed valid and invalid entries.
      """
      subversion = SubversionConfig()
      self.failUnlessEqual(None, subversion.repositories)
      self.failUnlessAssignRaises(ValueError, subversion, "repositories", [BDBRepository(), SubversionConfig(), ])
      self.failUnlessEqual(None, subversion.repositories)


   ############################
   # Test comparison operators
   ############################

   def testComparison_001(self):
      """
      Test comparison of two identical objects, all attributes None.
      """
      subversion1 = SubversionConfig()
      subversion2 = SubversionConfig()
      self.failUnlessEqual(subversion1, subversion2)
      self.failUnless(subversion1 == subversion2)
      self.failUnless(not subversion1 < subversion2)
      self.failUnless(subversion1 <= subversion2)
      self.failUnless(not subversion1 > subversion2)
      self.failUnless(subversion1 >= subversion2)
      self.failUnless(not subversion1 != subversion2)

   def testComparison_002(self):
      """
      Test comparison of two identical objects, all attributes non-None, list None.
      """
      subversion1 = SubversionConfig("daily", "gzip", None)
      subversion2 = SubversionConfig("daily", "gzip", None)
      self.failUnlessEqual(subversion1, subversion2)
      self.failUnless(subversion1 == subversion2)
      self.failUnless(not subversion1 < subversion2)
      self.failUnless(subversion1 <= subversion2)
      self.failUnless(not subversion1 > subversion2)
      self.failUnless(subversion1 >= subversion2)
      self.failUnless(not subversion1 != subversion2)

   def testComparison_003(self):
      """
      Test comparison of two identical objects, all attributes non-None, list empty.
      """
      subversion1 = SubversionConfig("daily", "gzip", [])
      subversion2 = SubversionConfig("daily", "gzip", [])
      self.failUnlessEqual(subversion1, subversion2)
      self.failUnless(subversion1 == subversion2)
      self.failUnless(not subversion1 < subversion2)
      self.failUnless(subversion1 <= subversion2)
      self.failUnless(not subversion1 > subversion2)
      self.failUnless(subversion1 >= subversion2)
      self.failUnless(not subversion1 != subversion2)

   def testComparison_004(self):
      """
      Test comparison of two identical objects, all attributes non-None, list non-empty.
      """
      subversion1 = SubversionConfig("daily", "gzip", [ BDBRepository(), ])
      subversion2 = SubversionConfig("daily", "gzip", [ BDBRepository(), ])
      self.failUnlessEqual(subversion1, subversion2)
      self.failUnless(subversion1 == subversion2)
      self.failUnless(not subversion1 < subversion2)
      self.failUnless(subversion1 <= subversion2)
      self.failUnless(not subversion1 > subversion2)
      self.failUnless(subversion1 >= subversion2)
      self.failUnless(not subversion1 != subversion2)

   def testComparison_005(self):
      """
      Test comparison of two differing objects, collectMode differs (one None).
      """
      subversion1 = SubversionConfig()
      subversion2 = SubversionConfig(collectMode="daily")
      self.failIfEqual(subversion1, subversion2)
      self.failUnless(not subversion1 == subversion2)
      self.failUnless(subversion1 < subversion2)
      self.failUnless(subversion1 <= subversion2)
      self.failUnless(not subversion1 > subversion2)
      self.failUnless(not subversion1 >= subversion2)
      self.failUnless(subversion1 != subversion2)

   def testComparison_006(self):
      """
      Test comparison of two differing objects, collectMode differs.
      """
      subversion1 = SubversionConfig("daily", "gzip", [ BDBRepository(), ])
      subversion2 = SubversionConfig("weekly", "gzip", [ BDBRepository(), ])
      self.failIfEqual(subversion1, subversion2)
      self.failUnless(not subversion1 == subversion2)
      self.failUnless(subversion1 < subversion2)
      self.failUnless(subversion1 <= subversion2)
      self.failUnless(not subversion1 > subversion2)
      self.failUnless(not subversion1 >= subversion2)
      self.failUnless(subversion1 != subversion2)

   def testComparison_007(self):
      """
      Test comparison of two differing objects, compressMode differs (one None).
      """
      subversion1 = SubversionConfig()
      subversion2 = SubversionConfig(compressMode="bzip2")
      self.failIfEqual(subversion1, subversion2)
      self.failUnless(not subversion1 == subversion2)
      self.failUnless(subversion1 < subversion2)
      self.failUnless(subversion1 <= subversion2)
      self.failUnless(not subversion1 > subversion2)
      self.failUnless(not subversion1 >= subversion2)
      self.failUnless(subversion1 != subversion2)

   def testComparison_008(self):
      """
      Test comparison of two differing objects, compressMode differs.
      """
      subversion1 = SubversionConfig("daily", "bzip2", [ BDBRepository(), ])
      subversion2 = SubversionConfig("daily", "gzip", [ BDBRepository(), ])
      self.failIfEqual(subversion1, subversion2)
      self.failUnless(not subversion1 == subversion2)
      self.failUnless(subversion1 < subversion2)
      self.failUnless(subversion1 <= subversion2)
      self.failUnless(not subversion1 > subversion2)
      self.failUnless(not subversion1 >= subversion2)
      self.failUnless(subversion1 != subversion2)

   def testComparison_009(self):
      """
      Test comparison of two differing objects, repositories differs (one None, one empty).
      """
      subversion1 = SubversionConfig()
      subversion2 = SubversionConfig(repositories=[])
      self.failIfEqual(subversion1, subversion2)
      self.failUnless(not subversion1 == subversion2)
      self.failUnless(subversion1 < subversion2)
      self.failUnless(subversion1 <= subversion2)
      self.failUnless(not subversion1 > subversion2)
      self.failUnless(not subversion1 >= subversion2)
      self.failUnless(subversion1 != subversion2)

   def testComparison_010(self):
      """
      Test comparison of two differing objects, repositories differs (one None, one not empty).
      """
      subversion1 = SubversionConfig()
      subversion2 = SubversionConfig(repositories=[BDBRepository(), ])
      self.failIfEqual(subversion1, subversion2)
      self.failUnless(not subversion1 == subversion2)
      self.failUnless(subversion1 < subversion2)
      self.failUnless(subversion1 <= subversion2)
      self.failUnless(not subversion1 > subversion2)
      self.failUnless(not subversion1 >= subversion2)
      self.failUnless(subversion1 != subversion2)

   def testComparison_011(self):
      """
      Test comparison of two differing objects, repositories differs (one empty, one not empty).
      """
      subversion1 = SubversionConfig("daily", "gzip", [ ])
      subversion2 = SubversionConfig("daily", "gzip", [ BDBRepository(), ])
      self.failIfEqual(subversion1, subversion2)
      self.failUnless(not subversion1 == subversion2)
      self.failUnless(subversion1 < subversion2)
      self.failUnless(subversion1 <= subversion2)
      self.failUnless(not subversion1 > subversion2)
      self.failUnless(not subversion1 >= subversion2)
      self.failUnless(subversion1 != subversion2)

   def testComparison_012(self):
      """
      Test comparison of two differing objects, repositories differs (both not empty).
      """
      subversion1 = SubversionConfig("daily", "gzip", [ BDBRepository(), ])
      subversion2 = SubversionConfig("daily", "gzip", [ BDBRepository(), BDBRepository(), ])
      self.failIfEqual(subversion1, subversion2)
      self.failUnless(not subversion1 == subversion2)
      self.failUnless(subversion1 < subversion2)
      self.failUnless(subversion1 <= subversion2)
      self.failUnless(not subversion1 > subversion2)
      self.failUnless(not subversion1 >= subversion2)
      self.failUnless(subversion1 != subversion2)


########################
# TestLocalConfig class
########################

class TestLocalConfig(unittest.TestCase):

   """Tests for the LocalConfig class."""

   ################
   # Setup methods
   ################

   def setUp(self):
      try:
         self.resources = findResources(RESOURCES, DATA_DIRS)
      except Exception, e:
         self.fail(e)

   def tearDown(self):
      pass


   ##################
   # Utility methods
   ##################

   def failUnlessAssignRaises(self, exception, object, property, value):
      """Equivalent of L{failUnlessRaises}, but used for property assignments instead."""
      failUnlessAssignRaises(self, exception, object, property, value)

   def validateAddConfig(self, origConfig):
      """
      Validates that document dumped from C{LocalConfig.addConfig} results in
      identical object.

      We dump a document containing just the subversion configuration, and then
      make sure that if we push that document back into the C{LocalConfig}
      object, that the resulting object matches the original.

      The C{self.failUnlessEqual} method is used for the validation, so if the
      method call returns normally, everything is OK.

      @param origConfig: Original configuration.
      """
      impl = getDOMImplementation()
      xmlDom = impl.createDocument(None, "cb_config", None)
      parentNode = xmlDom.documentElement
      origConfig.addConfig(xmlDom, parentNode)
      xmlBuffer = StringIO()
      PrettyPrint(xmlDom, xmlBuffer)
      xmlData = xmlBuffer.getvalue()
      xmlBuffer.close()
      xmlDom.unlink()
      newConfig = LocalConfig(xmlData=xmlData, validate=False)
      self.failUnlessEqual(origConfig, newConfig)


   ############################
   # Test __repr__ and __str__
   ############################

   def testStringFuncs_001(self):
      """
      Just make sure that the string functions don't have errors (i.e. bad variable names).
      """
      obj = LocalConfig()
      obj.__repr__()
      obj.__str__()


   #####################################################
   # Test basic constructor and attribute functionality
   #####################################################

   def testConstructor_001(self):
      """
      Test empty constructor, validate=False.
      """
      config = LocalConfig(validate=False)
      self.failUnlessEqual(None, config.subversion)

   def testConstructor_002(self):
      """
      Test empty constructor, validate=True.
      """
      config = LocalConfig(validate=True)
      self.failUnlessEqual(None, config.subversion)

   def testConstructor_003(self):
      """
      Test with empty config document as both data and file, validate=False.
      """
      path = self.resources["subversion.conf.1"]
      contents = open(path).read()
      self.failUnlessRaises(ValueError, LocalConfig, xmlData=contents, xmlPath=path, validate=False)

   def testConstructor_004(self):
      """
      Test assignment of subversion attribute, None value.
      """
      config = LocalConfig()
      config.subversion = None
      self.failUnlessEqual(None, config.subversion)

   def testConstructor_005(self):
      """
      Test assignment of subversion attribute, valid value.
      """
      config = LocalConfig()
      config.subversion = SubversionConfig()
      self.failUnlessEqual(SubversionConfig(), config.subversion)

   def testConstructor_006(self):
      """
      Test assignment of subversion attribute, invalid value (not SubversionConfig).
      """
      config = LocalConfig()
      self.failUnlessAssignRaises(ValueError, config, "subversion", "STRING!")


   ############################
   # Test comparison operators
   ############################

   def testComparison_001(self):
      """
      Test comparison of two identical objects, all attributes None.
      """
      config1 = LocalConfig()
      config2 = LocalConfig()
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
      config1 = LocalConfig()
      config1.subversion = SubversionConfig()

      config2 = LocalConfig()
      config2.subversion = SubversionConfig()

      self.failUnlessEqual(config1, config2)
      self.failUnless(config1 == config2)
      self.failUnless(not config1 < config2)
      self.failUnless(config1 <= config2)
      self.failUnless(not config1 > config2)
      self.failUnless(config1 >= config2)
      self.failUnless(not config1 != config2)

   def testComparison_003(self):
      """
      Test comparison of two differing objects, subversion differs (one None).
      """
      config1 = LocalConfig()
      config2 = LocalConfig()
      config2.subversion = SubversionConfig()
      self.failIfEqual(config1, config2)
      self.failUnless(not config1 == config2)
      self.failUnless(config1 < config2)
      self.failUnless(config1 <= config2)
      self.failUnless(not config1 > config2)
      self.failUnless(not config1 >= config2)
      self.failUnless(config1 != config2)

   def testComparison_004(self):
      """
      Test comparison of two differing objects, subversion differs.
      """
      config1 = LocalConfig()
      config1.subversion = SubversionConfig(collectMode="daily")

      config2 = LocalConfig()
      config2.subversion = SubversionConfig(collectMode="weekly")

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
      Test validate on a None subversion section.
      """
      config = LocalConfig()
      config.subversion = None
      self.failUnlessRaises(ValueError, config.validate)

   def testValidate_002(self):
      """
      Test validate on an empty subversion section.
      """
      config = LocalConfig()
      config.subversion = SubversionConfig()
      self.failUnlessRaises(ValueError, config.validate)

   def testValidate_003(self):
      """
      Test validate on a non-empty subversion section, repositories=None.
      """
      config = LocalConfig()
      config.subversion = SubversionConfig("weekly", "gzip", None)
      self.failUnlessRaises(ValueError, config.validate)

   def testValidate_004(self):
      """
      Test validate on a non-empty subversion section, repositories=[].
      """
      config = LocalConfig()
      config.subversion = SubversionConfig("weekly", "gzip", [])
      self.failUnlessRaises(ValueError, config.validate)

   def testValidate_005(self):
      """
      Test validate on a non-empty subversion section, non-empty repositories,
      defaults set, no values on repositories.
      """
      repositories = [ BDBRepository(repositoryPath="/one"), BDBRepository(repositoryPath="/two") ]
      config = LocalConfig()
      config.subversion = SubversionConfig()
      config.subversion.collectMode = "daily"
      config.subversion.compressMode = "gzip"
      config.subversion.repositories = repositories
      config.validate()

   def testValidate_006(self):
      """
      Test validate on a non-empty subversion section, non-empty repositories,
      no defaults set, no values on repositiories.
      """
      repositories = [ BDBRepository(repositoryPath="/one"), BDBRepository(repositoryPath="/two") ]
      config = LocalConfig()
      config.subversion = SubversionConfig()
      config.subversion.repositories = repositories
      self.failUnlessRaises(ValueError, config.validate)

   def testValidate_007(self):
      """
      Test validate on a non-empty subversion section, non-empty repositories,
      no defaults set, both values on repositories.
      """
      repositories = [ BDBRepository(repositoryPath="/two", collectMode="weekly", compressMode="gzip") ]
      config = LocalConfig()
      config.subversion = SubversionConfig()
      config.subversion.repositories = repositories
      config.validate()

   def testValidate_008(self):
      """
      Test validate on a non-empty subversion section, non-empty repositories,
      collectMode only on repositories.
      """
      repositories = [ BDBRepository(repositoryPath="/two", collectMode="weekly") ]
      config = LocalConfig()
      config.subversion = SubversionConfig()
      config.subversion.compressMode = "gzip"
      config.subversion.repositories = repositories
      config.validate()

   def testValidate_009(self):
      """
      Test validate on a non-empty subversion section, non-empty repositories,
      compressMode only on repositories.
      """
      repositories = [ BDBRepository(repositoryPath="/two", compressMode="bzip2") ]
      config = LocalConfig()
      config.subversion = SubversionConfig()
      config.subversion.collectMode = "weekly"
      config.subversion.repositories = repositories
      config.validate()

   def testValidate_010(self):
      """
      Test validate on a non-empty subversion section, non-empty repositories,
      compressMode default and on repository.
      """
      repositories = [ BDBRepository(repositoryPath="/two", compressMode="bzip2") ]
      config = LocalConfig()
      config.subversion = SubversionConfig()
      config.subversion.collectMode = "daily"
      config.subversion.compressMode = "gzip"
      config.subversion.repositories = repositories
      config.validate()

   def testValidate_011(self):
      """
      Test validate on a non-empty subversion section, non-empty repositories,
      collectMode default and on repository.
      """
      repositories = [ BDBRepository(repositoryPath="/two", collectMode="daily") ]
      config = LocalConfig()
      config.subversion = SubversionConfig()
      config.subversion.collectMode = "daily"
      config.subversion.compressMode = "gzip"
      config.subversion.repositories = repositories
      config.validate()

   def testValidate_012(self):
      """
      Test validate on a non-empty subversion section, non-empty repositories,
      collectMode and compressMode default and on repository.
      """
      repositories = [ BDBRepository(repositoryPath="/two", collectMode="daily", compressMode="bzip2") ]
      config = LocalConfig()
      config.subversion = SubversionConfig()
      config.subversion.collectMode = "daily"
      config.subversion.compressMode = "gzip"
      config.subversion.repositories = repositories
      config.validate()


   ############################
   # Test parsing of documents
   ############################

   def testParse_001(self):
      """
      Parse empty config document.
      """
      path = self.resources["subversion.conf.1"]
      contents = open(path).read()
      self.failUnlessRaises(ValueError, LocalConfig, xmlPath=path, validate=True)
      self.failUnlessRaises(ValueError, LocalConfig, xmlData=contents, validate=True)
      config = LocalConfig(xmlPath=path, validate=False)
      self.failUnlessEqual(None, config.subversion)
      config = LocalConfig(xmlData=contents, validate=False)
      self.failUnlessEqual(None, config.subversion)

   def testParse_002(self):
      """
      Parse config document with default modes, one repository.
      """
      repositories = [ BDBRepository(repositoryPath="/opt/public/svn/software"), ]
      path = self.resources["subversion.conf.2"]
      contents = open(path).read()
      config = LocalConfig(xmlPath=path, validate=False)
      self.failIfEqual(None, config.subversion)
      self.failUnlessEqual("daily", config.subversion.collectMode)
      self.failUnlessEqual("gzip", config.subversion.compressMode)
      self.failUnlessEqual(repositories, config.subversion.repositories)
      config = LocalConfig(xmlData=contents, validate=False)
      self.failIfEqual(None, config.subversion)
      self.failUnlessEqual("daily", config.subversion.collectMode)
      self.failUnlessEqual("gzip", config.subversion.compressMode)
      self.failUnlessEqual(repositories, config.subversion.repositories)

   def testParse_003(self):
      """
      Parse config document with no default modes, one repository
      """
      repositories = [ BDBRepository(repositoryPath="/opt/public/svn/software", collectMode="daily", compressMode="gzip"), ]
      path = self.resources["subversion.conf.3"]
      contents = open(path).read()
      config = LocalConfig(xmlPath=path, validate=False)
      self.failIfEqual(None, config.subversion)
      self.failUnlessEqual(None, config.subversion.collectMode)
      self.failUnlessEqual(None, config.subversion.compressMode)
      self.failUnlessEqual(repositories, config.subversion.repositories)
      config = LocalConfig(xmlData=contents, validate=False)
      self.failIfEqual(None, config.subversion)
      self.failUnlessEqual(None, config.subversion.collectMode)
      self.failUnlessEqual(None, config.subversion.compressMode)
      self.failUnlessEqual(repositories, config.subversion.repositories)

   def testParse_004(self):
      """
      Parse config document with default modes, several repositories with
      various overrides.
      """
      repositories = []
      repositories.append(BDBRepository(repositoryPath="/opt/public/svn/one"))
      repositories.append(BDBRepository(repositoryPath="/opt/public/svn/two", collectMode="weekly"))
      repositories.append(BDBRepository(repositoryPath="/opt/public/svn/three", compressMode="bzip2"))
      repositories.append(BDBRepository(repositoryPath="/opt/public/svn/four", collectMode="incr", compressMode="bzip2"))
      path = self.resources["subversion.conf.4"]
      contents = open(path).read()
      config = LocalConfig(xmlPath=path, validate=False)
      self.failIfEqual(None, config.subversion)
      self.failUnlessEqual("daily", config.subversion.collectMode)
      self.failUnlessEqual("gzip", config.subversion.compressMode)
      self.failUnlessEqual(repositories, config.subversion.repositories)
      config = LocalConfig(xmlData=contents, validate=False)
      self.failIfEqual(None, config.subversion)
      self.failUnlessEqual("daily", config.subversion.collectMode)
      self.failUnlessEqual("gzip", config.subversion.compressMode)
      self.failUnlessEqual(repositories, config.subversion.repositories)


   ###################
   # Test addConfig()
   ###################

   def testAddConfig_001(self):
      """
      Test with empty config document.
      """
      subversion = SubversionConfig()
      config = LocalConfig()
      config.subversion = subversion
      self.validateAddConfig(config)

   def testAddConfig_002(self):
      """
      Test with defaults set, single repository with no optional values.
      """
      repositories = []
      repositories.append(BDBRepository(repositoryPath="/path"))
      subversion = SubversionConfig(collectMode="daily", compressMode="gzip", repositories=repositories)
      config = LocalConfig()
      config.subversion = subversion
      self.validateAddConfig(config)

   def testAddConfig_003(self):
      """
      Test with defaults set, single repository with collectMode set.
      """
      repositories = []
      repositories.append(BDBRepository(repositoryPath="/path", collectMode="incr"))
      subversion = SubversionConfig(collectMode="daily", compressMode="gzip", repositories=repositories)
      config = LocalConfig()
      config.subversion = subversion
      self.validateAddConfig(config)

   def testAddConfig_004(self):
      """
      Test with defaults set, single repository with compressMode set.
      """
      repositories = []
      repositories.append(BDBRepository(repositoryPath="/path", compressMode="bzip2"))
      subversion = SubversionConfig(collectMode="daily", compressMode="gzip", repositories=repositories)
      config = LocalConfig()
      config.subversion = subversion
      self.validateAddConfig(config)

   def testAddConfig_005(self):
      """
      Test with defaults set, single repository with collectMode and compressMode set.
      """
      repositories = []
      repositories.append(BDBRepository(repositoryPath="/path", collectMode="weekly", compressMode="bzip2"))
      subversion = SubversionConfig(collectMode="daily", compressMode="gzip", repositories=repositories)
      config = LocalConfig()
      config.subversion = subversion
      self.validateAddConfig(config)

   def testAddConfig_006(self):
      """
      Test with no defaults set, single repository with collectMode and compressMode set.
      """
      repositories = []
      repositories.append(BDBRepository(repositoryPath="/path", collectMode="weekly", compressMode="bzip2"))
      subversion = SubversionConfig(repositories=repositories)
      config = LocalConfig()
      config.subversion = subversion
      self.validateAddConfig(config)

   def testAddConfig_007(self):
      """
      Test with compressMode set, single repository with collectMode set.
      """
      repositories = []
      repositories.append(BDBRepository(repositoryPath="/path", collectMode="weekly"))
      subversion = SubversionConfig(compressMode="gzip", repositories=repositories)
      config = LocalConfig()
      config.subversion = subversion
      self.validateAddConfig(config)

   def testAddConfig_008(self):
      """
      Test with collectMode set, single repository with compressMode set.
      """
      repositories = []
      repositories.append(BDBRepository(repositoryPath="/path", compressMode="gzip"))
      subversion = SubversionConfig(collectMode="weekly", repositories=repositories)
      config = LocalConfig()
      config.subversion = subversion
      self.validateAddConfig(config)

   def testAddConfig_009(self):
      """
      Test with compressMode set, single repository with collectMode and compressMode set.
      """
      repositories = []
      repositories.append(BDBRepository(repositoryPath="/path", collectMode="incr", compressMode="gzip"))
      subversion = SubversionConfig(compressMode="bzip2", repositories=repositories)
      config = LocalConfig()
      config.subversion = subversion
      self.validateAddConfig(config)

   def testAddConfig_010(self):
      """
      Test with collectMode set, single repository with collectMode and compressMode set.
      """
      repositories = []
      repositories.append(BDBRepository(repositoryPath="/path", collectMode="weekly", compressMode="gzip"))
      subversion = SubversionConfig(collectMode="incr", repositories=repositories)
      config = LocalConfig()
      config.subversion = subversion
      self.validateAddConfig(config)

   def testAddConfig_011(self):
      """
      Test with defaults set, multiple repositories with collectMode and compressMode set.
      """
      repositories = []
      repositories.append(BDBRepository(repositoryPath="/path1", collectMode="daily", compressMode="gzip"))
      repositories.append(BDBRepository(repositoryPath="/path2", collectMode="weekly", compressMode="gzip"))
      repositories.append(BDBRepository(repositoryPath="/path3", collectMode="incr", compressMode="gzip"))
      repositories.append(BDBRepository(repositoryPath="/path1", collectMode="daily", compressMode="bzip2"))
      repositories.append(BDBRepository(repositoryPath="/path2", collectMode="weekly", compressMode="bzip2"))
      repositories.append(BDBRepository(repositoryPath="/path3", collectMode="incr", compressMode="bzip2"))
      subversion = SubversionConfig(collectMode="incr", compressMode="bzip2", repositories=repositories)
      config = LocalConfig()
      config.subversion = subversion
      self.validateAddConfig(config)


#######################################################################
# Suite definition
#######################################################################

def suite():
   """Returns a suite containing all the test cases in this module."""
   return unittest.TestSuite((
                              unittest.makeSuite(TestBDBRepository, 'test'), 
                              unittest.makeSuite(TestSubversionConfig, 'test'), 
                              unittest.makeSuite(TestLocalConfig, 'test'), 
                            ))


########################################################################
# Module entry point
########################################################################

# When this module is executed from the command-line, run its tests
if __name__ == '__main__':
   unittest.main()

