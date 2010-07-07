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
# Copyright (c) 2006 Kenneth J. Pronovici.
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
# Language : Python (>= 2.5)
# Project  : Cedar Backup, release 2
# Revision : $Id$
# Purpose  : Tests PostgreSQL extension functionality.
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

########################################################################
# Module documentation
########################################################################

"""
Unit tests for CedarBackup2/extend/postgresql.py.

Code Coverage
=============

   This module contains individual tests for the many of the public functions
   and classes implemented in extend/postgresql.py.  There are also tests for
   several of the private methods.

   Unfortunately, it's rather difficult to test this code in an automated
   fashion, even if you have access to PostgreSQL, since the actual dump would
   need to have access to a real database.  Because of this, there aren't any
   tests below that actually talk to a database.

   As a compromise, I test some of the private methods in the implementation.
   Normally, I don't like to test private methods, but in this case, testing
   the private methods will help give us some reasonable confidence in the code
   even if we can't talk to a database..  This isn't perfect, but it's better
   than nothing.

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

   It would arguably be better if we could do a completely independent check -
   but implementing that check would be equivalent to re-implementing all of
   the existing functionality that we're validating here!  After all, the most
   important thing is that data can move seamlessly from object to XML document
   and back to object.

Full vs. Reduced Tests
======================

   All of the tests in this module are considered safe to be run in an average
   build environment.  There is a no need to use a POSTGRESQLTESTS_FULL
   environment variable to provide a "reduced feature set" test suite as for
   some of the other test modules.

@author Kenneth J. Pronovici <pronovic@ieee.org>
"""


########################################################################
# Import modules and do runtime validations
########################################################################

# System modules
import unittest

# Cedar Backup modules
from CedarBackup2.testutil import findResources, failUnlessAssignRaises
from CedarBackup2.xmlutil import createOutputDom, serializeDom
from CedarBackup2.extend.postgresql import LocalConfig, PostgresqlConfig


#######################################################################
# Module-wide configuration and constants
#######################################################################

DATA_DIRS = [ "./data", "./testcase/data", ]
RESOURCES = [ "postgresql.conf.1", "postgresql.conf.2", "postgresql.conf.3", "postgresql.conf.4", "postgresql.conf.5", ]


#######################################################################
# Test Case Classes
#######################################################################

#############################
# TestPostgresqlConfig class
#############################

class TestPostgresqlConfig(unittest.TestCase):

   """Tests for the PostgresqlConfig class."""

   ##################
   # Utility methods
   ##################

   def failUnlessAssignRaises(self, exception, obj, prop, value):
      """Equivalent of L{failUnlessRaises}, but used for property assignments instead."""
      failUnlessAssignRaises(self, exception, obj, prop, value)


   ############################
   # Test __repr__ and __str__
   ############################

   def testStringFuncs_001(self):
      """
      Just make sure that the string functions don't have errors (i.e. bad variable names).
      """
      obj = PostgresqlConfig()
      obj.__repr__()
      obj.__str__()


   ##################################
   # Test constructor and attributes
   ##################################

   def testConstructor_001(self):
      """
      Test constructor with no values filled in.
      """
      postgresql = PostgresqlConfig()
      self.failUnlessEqual(None, postgresql.user)
      self.failUnlessEqual(None, postgresql.compressMode)
      self.failUnlessEqual(False, postgresql.all)
      self.failUnlessEqual(None, postgresql.databases)

   def testConstructor_002(self):
      """
      Test constructor with all values filled in, with valid values, databases=None.
      """
      postgresql = PostgresqlConfig("user", "none", False, None)
      self.failUnlessEqual("user", postgresql.user)
      self.failUnlessEqual("none", postgresql.compressMode)
      self.failUnlessEqual(False, postgresql.all)
      self.failUnlessEqual(None, postgresql.databases)

   def testConstructor_003(self):
      """
      Test constructor with all values filled in, with valid values, no databases.
      """
      postgresql = PostgresqlConfig("user", "none", True, [])
      self.failUnlessEqual("user", postgresql.user)
      self.failUnlessEqual("none", postgresql.compressMode)
      self.failUnlessEqual(True, postgresql.all)
      self.failUnlessEqual([], postgresql.databases)

   def testConstructor_004(self):
      """
      Test constructor with all values filled in, with valid values, with one database.
      """
      postgresql = PostgresqlConfig("user", "gzip", True,  [ "one", ])
      self.failUnlessEqual("user", postgresql.user)
      self.failUnlessEqual("gzip", postgresql.compressMode)
      self.failUnlessEqual(True, postgresql.all)
      self.failUnlessEqual([ "one", ], postgresql.databases)

   def testConstructor_005(self):
      """
      Test constructor with all values filled in, with valid values, with multiple databases.
      """
      postgresql = PostgresqlConfig("user", "bzip2", True, [ "one", "two", ])
      self.failUnlessEqual("user", postgresql.user)
      self.failUnlessEqual("bzip2", postgresql.compressMode)
      self.failUnlessEqual(True, postgresql.all)
      self.failUnlessEqual([ "one", "two", ], postgresql.databases)

   def testConstructor_006(self):
      """
      Test assignment of user attribute, None value.
      """
      postgresql = PostgresqlConfig(user="user")
      self.failUnlessEqual("user", postgresql.user)
      postgresql.user = None
      self.failUnlessEqual(None, postgresql.user)

   def testConstructor_007(self):
      """
      Test assignment of user attribute, valid value.
      """
      postgresql = PostgresqlConfig()
      self.failUnlessEqual(None, postgresql.user)
      postgresql.user = "user"
      self.failUnlessEqual("user", postgresql.user)

   def testConstructor_008(self):
      """
      Test assignment of user attribute, invalid value (empty).
      """
      postgresql = PostgresqlConfig()
      self.failUnlessEqual(None, postgresql.user)
      self.failUnlessAssignRaises(ValueError, postgresql, "user", "")
      self.failUnlessEqual(None, postgresql.user)

   def testConstructor_009(self):
      """
      Test assignment of compressMode attribute, None value.
      """
      postgresql = PostgresqlConfig(compressMode="none")
      self.failUnlessEqual("none", postgresql.compressMode)
      postgresql.compressMode = None
      self.failUnlessEqual(None, postgresql.compressMode)

   def testConstructor_010(self):
      """
      Test assignment of compressMode attribute, valid value.
      """
      postgresql = PostgresqlConfig()
      self.failUnlessEqual(None, postgresql.compressMode)
      postgresql.compressMode = "none"
      self.failUnlessEqual("none", postgresql.compressMode)
      postgresql.compressMode = "gzip"
      self.failUnlessEqual("gzip", postgresql.compressMode)
      postgresql.compressMode = "bzip2"
      self.failUnlessEqual("bzip2", postgresql.compressMode)

   def testConstructor_011(self):
      """
      Test assignment of compressMode attribute, invalid value (empty).
      """
      postgresql = PostgresqlConfig()
      self.failUnlessEqual(None, postgresql.compressMode)
      self.failUnlessAssignRaises(ValueError, postgresql, "compressMode", "")
      self.failUnlessEqual(None, postgresql.compressMode)

   def testConstructor_012(self):
      """
      Test assignment of compressMode attribute, invalid value (not in list).
      """
      postgresql = PostgresqlConfig()
      self.failUnlessEqual(None, postgresql.compressMode)
      self.failUnlessAssignRaises(ValueError, postgresql, "compressMode", "bogus")
      self.failUnlessEqual(None, postgresql.compressMode)

   def testConstructor_013(self):
      """
      Test assignment of all attribute, None value.
      """
      postgresql = PostgresqlConfig(all=True)
      self.failUnlessEqual(True, postgresql.all)
      postgresql.all = None
      self.failUnlessEqual(False, postgresql.all)

   def testConstructor_014(self):
      """
      Test assignment of all attribute, valid value (real boolean).
      """
      postgresql = PostgresqlConfig()
      self.failUnlessEqual(False, postgresql.all)
      postgresql.all = True
      self.failUnlessEqual(True, postgresql.all)
      postgresql.all = False
      self.failUnlessEqual(False, postgresql.all)

   def testConstructor_015(self):
      """
      Test assignment of all attribute, valid value (expression).
      """
      postgresql = PostgresqlConfig()
      self.failUnlessEqual(False, postgresql.all)
      postgresql.all = 0
      self.failUnlessEqual(False, postgresql.all)
      postgresql.all = []
      self.failUnlessEqual(False, postgresql.all)
      postgresql.all = None
      self.failUnlessEqual(False, postgresql.all)
      postgresql.all = ['a']
      self.failUnlessEqual(True, postgresql.all)
      postgresql.all = 3
      self.failUnlessEqual(True, postgresql.all)

   def testConstructor_016(self):
      """
      Test assignment of databases attribute, None value.
      """
      postgresql = PostgresqlConfig(databases=[])
      self.failUnlessEqual([], postgresql.databases)
      postgresql.databases = None
      self.failUnlessEqual(None, postgresql.databases)

   def testConstructor_017(self):
      """
      Test assignment of databases attribute, [] value.
      """
      postgresql = PostgresqlConfig()
      self.failUnlessEqual(None, postgresql.databases)
      postgresql.databases = []
      self.failUnlessEqual([], postgresql.databases)

   def testConstructor_018(self):
      """
      Test assignment of databases attribute, single valid entry.
      """
      postgresql = PostgresqlConfig()
      self.failUnlessEqual(None, postgresql.databases)
      postgresql.databases = ["/whatever", ]
      self.failUnlessEqual(["/whatever", ], postgresql.databases)
      postgresql.databases.append("/stuff")
      self.failUnlessEqual(["/whatever", "/stuff", ], postgresql.databases)

   def testConstructor_019(self):
      """
      Test assignment of databases attribute, multiple valid entries.
      """
      postgresql = PostgresqlConfig()
      self.failUnlessEqual(None, postgresql.databases)
      postgresql.databases = ["/whatever", "/stuff", ]
      self.failUnlessEqual(["/whatever", "/stuff", ], postgresql.databases)
      postgresql.databases.append("/etc/X11")
      self.failUnlessEqual(["/whatever", "/stuff", "/etc/X11", ], postgresql.databases)

   def testConstructor_020(self):
      """
      Test assignment of databases attribute, single invalid entry (empty).
      """
      postgresql = PostgresqlConfig()
      self.failUnlessEqual(None, postgresql.databases)
      self.failUnlessAssignRaises(ValueError, postgresql, "databases", ["", ])
      self.failUnlessEqual(None, postgresql.databases)

   def testConstructor_021(self):
      """
      Test assignment of databases attribute, mixed valid and invalid entries.
      """
      postgresql = PostgresqlConfig()
      self.failUnlessEqual(None, postgresql.databases)
      self.failUnlessAssignRaises(ValueError, postgresql, "databases", ["good", "", "alsogood", ])
      self.failUnlessEqual(None, postgresql.databases)


   ############################
   # Test comparison operators
   ############################

   def testComparison_001(self):
      """
      Test comparison of two identical objects, all attributes None.
      """
      postgresql1 = PostgresqlConfig()
      postgresql2 = PostgresqlConfig()
      self.failUnlessEqual(postgresql1, postgresql2)
      self.failUnless(postgresql1 == postgresql2)
      self.failUnless(not postgresql1 < postgresql2)
      self.failUnless(postgresql1 <= postgresql2)
      self.failUnless(not postgresql1 > postgresql2)
      self.failUnless(postgresql1 >= postgresql2)
      self.failUnless(not postgresql1 != postgresql2)

   def testComparison_002(self):
      """
      Test comparison of two identical objects, all attributes non-None, list None.
      """
      postgresql1 = PostgresqlConfig("user", "gzip", True, None)
      postgresql2 = PostgresqlConfig("user", "gzip", True, None)
      self.failUnlessEqual(postgresql1, postgresql2)
      self.failUnless(postgresql1 == postgresql2)
      self.failUnless(not postgresql1 < postgresql2)
      self.failUnless(postgresql1 <= postgresql2)
      self.failUnless(not postgresql1 > postgresql2)
      self.failUnless(postgresql1 >= postgresql2)
      self.failUnless(not postgresql1 != postgresql2)

   def testComparison_003(self):
      """
      Test comparison of two identical objects, all attributes non-None, list empty.
      """
      postgresql1 = PostgresqlConfig("user", "bzip2", True, [])
      postgresql2 = PostgresqlConfig("user", "bzip2", True, [])
      self.failUnlessEqual(postgresql1, postgresql2)
      self.failUnless(postgresql1 == postgresql2)
      self.failUnless(not postgresql1 < postgresql2)
      self.failUnless(postgresql1 <= postgresql2)
      self.failUnless(not postgresql1 > postgresql2)
      self.failUnless(postgresql1 >= postgresql2)
      self.failUnless(not postgresql1 != postgresql2)

   def testComparison_004(self):
      """
      Test comparison of two identical objects, all attributes non-None, list non-empty.
      """
      postgresql1 = PostgresqlConfig("user", "none", True, [ "whatever", ])
      postgresql2 = PostgresqlConfig("user", "none", True, [ "whatever", ])
      self.failUnlessEqual(postgresql1, postgresql2)
      self.failUnless(postgresql1 == postgresql2)
      self.failUnless(not postgresql1 < postgresql2)
      self.failUnless(postgresql1 <= postgresql2)
      self.failUnless(not postgresql1 > postgresql2)
      self.failUnless(postgresql1 >= postgresql2)
      self.failUnless(not postgresql1 != postgresql2)

   def testComparison_005(self):
      """
      Test comparison of two differing objects, user differs (one None).
      """
      postgresql1 = PostgresqlConfig()
      postgresql2 = PostgresqlConfig(user="user")
      self.failIfEqual(postgresql1, postgresql2)
      self.failUnless(not postgresql1 == postgresql2)
      self.failUnless(postgresql1 < postgresql2)
      self.failUnless(postgresql1 <= postgresql2)
      self.failUnless(not postgresql1 > postgresql2)
      self.failUnless(not postgresql1 >= postgresql2)
      self.failUnless(postgresql1 != postgresql2)

   def testComparison_006(self):
      """
      Test comparison of two differing objects, user differs.
      """
      postgresql1 = PostgresqlConfig("user1", "gzip", True, [ "whatever", ])
      postgresql2 = PostgresqlConfig("user2", "gzip", True, [ "whatever", ])
      self.failIfEqual(postgresql1, postgresql2)
      self.failUnless(not postgresql1 == postgresql2)
      self.failUnless(postgresql1 < postgresql2)
      self.failUnless(postgresql1 <= postgresql2)
      self.failUnless(not postgresql1 > postgresql2)
      self.failUnless(not postgresql1 >= postgresql2)
      self.failUnless(postgresql1 != postgresql2)

   def testComparison_007(self):
      """
      Test comparison of two differing objects, compressMode differs (one None).
      """
      postgresql1 = PostgresqlConfig()
      postgresql2 = PostgresqlConfig(compressMode="gzip")
      self.failIfEqual(postgresql1, postgresql2)
      self.failUnless(not postgresql1 == postgresql2)
      self.failUnless(postgresql1 < postgresql2)
      self.failUnless(postgresql1 <= postgresql2)
      self.failUnless(not postgresql1 > postgresql2)
      self.failUnless(not postgresql1 >= postgresql2)
      self.failUnless(postgresql1 != postgresql2)

   def testComparison_008(self):
      """
      Test comparison of two differing objects, compressMode differs.
      """
      postgresql1 = PostgresqlConfig("user", "bzip2", True, [ "whatever", ])
      postgresql2 = PostgresqlConfig("user", "gzip", True, [ "whatever", ])
      self.failIfEqual(postgresql1, postgresql2)
      self.failUnless(not postgresql1 == postgresql2)
      self.failUnless(postgresql1 < postgresql2)
      self.failUnless(postgresql1 <= postgresql2)
      self.failUnless(not postgresql1 > postgresql2)
      self.failUnless(not postgresql1 >= postgresql2)
      self.failUnless(postgresql1 != postgresql2)

   def testComparison_009(self):
      """
      Test comparison of two differing objects, all differs (one None).
      """
      postgresql1 = PostgresqlConfig()
      postgresql2 = PostgresqlConfig(all=True)
      self.failIfEqual(postgresql1, postgresql2)
      self.failUnless(not postgresql1 == postgresql2)
      self.failUnless(postgresql1 < postgresql2)
      self.failUnless(postgresql1 <= postgresql2)
      self.failUnless(not postgresql1 > postgresql2)
      self.failUnless(not postgresql1 >= postgresql2)
      self.failUnless(postgresql1 != postgresql2)

   def testComparison_010(self):
      """
      Test comparison of two differing objects, all differs.
      """
      postgresql1 = PostgresqlConfig("user", "gzip", False, [ "whatever", ])
      postgresql2 = PostgresqlConfig("user", "gzip", True, [ "whatever", ])
      self.failIfEqual(postgresql1, postgresql2)
      self.failUnless(not postgresql1 == postgresql2)
      self.failUnless(postgresql1 < postgresql2)
      self.failUnless(postgresql1 <= postgresql2)
      self.failUnless(not postgresql1 > postgresql2)
      self.failUnless(not postgresql1 >= postgresql2)
      self.failUnless(postgresql1 != postgresql2)

   def testComparison_011(self):
      """
      Test comparison of two differing objects, databases differs (one None, one empty).
      """
      postgresql1 = PostgresqlConfig()
      postgresql2 = PostgresqlConfig(databases=[])
      self.failIfEqual(postgresql1, postgresql2)
      self.failUnless(not postgresql1 == postgresql2)
      self.failUnless(postgresql1 < postgresql2)
      self.failUnless(postgresql1 <= postgresql2)
      self.failUnless(not postgresql1 > postgresql2)
      self.failUnless(not postgresql1 >= postgresql2)
      self.failUnless(postgresql1 != postgresql2)

   def testComparison_012(self):
      """
      Test comparison of two differing objects, databases differs (one None, one not empty).
      """
      postgresql1 = PostgresqlConfig()
      postgresql2 = PostgresqlConfig(databases=["whatever", ])
      self.failIfEqual(postgresql1, postgresql2)
      self.failUnless(not postgresql1 == postgresql2)
      self.failUnless(postgresql1 < postgresql2)
      self.failUnless(postgresql1 <= postgresql2)
      self.failUnless(not postgresql1 > postgresql2)
      self.failUnless(not postgresql1 >= postgresql2)
      self.failUnless(postgresql1 != postgresql2)

   def testComparison_013(self):
      """
      Test comparison of two differing objects, databases differs (one empty, one not empty).
      """
      postgresql1 = PostgresqlConfig("user", "gzip", True, [ ])
      postgresql2 = PostgresqlConfig("user", "gzip", True, [ "whatever", ])
      self.failIfEqual(postgresql1, postgresql2)
      self.failUnless(not postgresql1 == postgresql2)
      self.failUnless(postgresql1 < postgresql2)
      self.failUnless(postgresql1 <= postgresql2)
      self.failUnless(not postgresql1 > postgresql2)
      self.failUnless(not postgresql1 >= postgresql2)
      self.failUnless(postgresql1 != postgresql2)

   def testComparison_014(self):
      """
      Test comparison of two differing objects, databases differs (both not empty).
      """
      postgresql1 = PostgresqlConfig("user", "gzip", True, [ "whatever", ])
      postgresql2 = PostgresqlConfig("user", "gzip", True, [ "whatever", "bogus", ])
      self.failIfEqual(postgresql1, postgresql2)
      self.failUnless(not postgresql1 == postgresql2)
      self.failUnless(not postgresql1 < postgresql2)     # note: different than standard due to unsorted list
      self.failUnless(not postgresql1 <= postgresql2)    # note: different than standard due to unsorted list
      self.failUnless(postgresql1 > postgresql2)         # note: different than standard due to unsorted list
      self.failUnless(postgresql1 >= postgresql2)        # note: different than standard due to unsorted list
      self.failUnless(postgresql1 != postgresql2)


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

   def failUnlessAssignRaises(self, exception, obj, prop, value):
      """Equivalent of L{failUnlessRaises}, but used for property assignments instead."""
      failUnlessAssignRaises(self, exception, obj, prop, value)

   def validateAddConfig(self, origConfig):
      """
      Validates that document dumped from C{LocalConfig.addConfig} results in
      identical object.

      We dump a document containing just the postgresql configuration, and then make
      sure that if we push that document back into the C{LocalConfig} object,
      that the resulting object matches the original.

      The C{self.failUnlessEqual} method is used for the validation, so if the
      method call returns normally, everything is OK.

      @param origConfig: Original configuration.
      """
      (xmlDom, parentNode) = createOutputDom()
      origConfig.addConfig(xmlDom, parentNode)
      xmlData = serializeDom(xmlDom)
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
      self.failUnlessEqual(None, config.postgresql)

   def testConstructor_002(self):
      """
      Test empty constructor, validate=True.
      """
      config = LocalConfig(validate=True)
      self.failUnlessEqual(None, config.postgresql)

   def testConstructor_003(self):
      """
      Test with empty config document as both data and file, validate=False.
      """
      path = self.resources["postgresql.conf.1"]
      contents = open(path).read()
      self.failUnlessRaises(ValueError, LocalConfig, xmlData=contents, xmlPath=path, validate=False)

   def testConstructor_004(self):
      """
      Test assignment of postgresql attribute, None value.
      """
      config = LocalConfig()
      config.postgresql = None
      self.failUnlessEqual(None, config.postgresql)

   def testConstructor_005(self):
      """
      Test assignment of postgresql attribute, valid value.
      """
      config = LocalConfig()
      config.postgresql = PostgresqlConfig()
      self.failUnlessEqual(PostgresqlConfig(), config.postgresql)

   def testConstructor_006(self):
      """
      Test assignment of postgresql attribute, invalid value (not PostgresqlConfig).
      """
      config = LocalConfig()
      self.failUnlessAssignRaises(ValueError, config, "postgresql", "STRING!")


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
      config1.postgresql = PostgresqlConfig()

      config2 = LocalConfig()
      config2.postgresql = PostgresqlConfig()

      self.failUnlessEqual(config1, config2)
      self.failUnless(config1 == config2)
      self.failUnless(not config1 < config2)
      self.failUnless(config1 <= config2)
      self.failUnless(not config1 > config2)
      self.failUnless(config1 >= config2)
      self.failUnless(not config1 != config2)

   def testComparison_003(self):
      """
      Test comparison of two differing objects, postgresql differs (one None).
      """
      config1 = LocalConfig()
      config2 = LocalConfig()
      config2.postgresql = PostgresqlConfig()
      self.failIfEqual(config1, config2)
      self.failUnless(not config1 == config2)
      self.failUnless(config1 < config2)
      self.failUnless(config1 <= config2)
      self.failUnless(not config1 > config2)
      self.failUnless(not config1 >= config2)
      self.failUnless(config1 != config2)

   def testComparison_004(self):
      """
      Test comparison of two differing objects, postgresql differs.
      """
      config1 = LocalConfig()
      config1.postgresql = PostgresqlConfig(user="one")

      config2 = LocalConfig()
      config2.postgresql = PostgresqlConfig(user="two")

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
      Test validate on a None postgresql section.
      """
      config = LocalConfig()
      config.postgresql = None
      self.failUnlessRaises(ValueError, config.validate)

   def testValidate_002(self):
      """
      Test validate on an empty postgresql section.
      """
      config = LocalConfig()
      config.postgresql = PostgresqlConfig()
      self.failUnlessRaises(ValueError, config.validate)

   def testValidate_003(self):
      """
      Test validate on a non-empty postgresql section, all=True, databases=None.
      """
      config = LocalConfig()
      config.postgresql = PostgresqlConfig("user", "gzip", True, None)
      config.validate()

   def testValidate_004(self):
      """
      Test validate on a non-empty postgresql section, all=True, empty databases.
      """
      config = LocalConfig()
      config.postgresql = PostgresqlConfig("user", "none", True, [])
      config.validate()

   def testValidate_005(self):
      """
      Test validate on a non-empty postgresql section, all=True, non-empty databases.
      """
      config = LocalConfig()
      config.postgresql = PostgresqlConfig("user", "bzip2", True, ["whatever", ])
      self.failUnlessRaises(ValueError, config.validate)

   def testValidate_006(self):
      """
      Test validate on a non-empty postgresql section, all=False, databases=None.
      """
      config = LocalConfig()
      config.postgresql = PostgresqlConfig("user", "gzip", False, None)
      self.failUnlessRaises(ValueError, config.validate)

   def testValidate_007(self):
      """
      Test validate on a non-empty postgresql section, all=False, empty databases.
      """
      config = LocalConfig()
      config.postgresql = PostgresqlConfig("user", "bzip2", False, [])
      self.failUnlessRaises(ValueError, config.validate)

   def testValidate_008(self):
      """
      Test validate on a non-empty postgresql section, all=False, non-empty databases.
      """
      config = LocalConfig()
      config.postgresql = PostgresqlConfig("user", "gzip", False, ["whatever", ])
      config.validate()

   def testValidate_009(self):
      """
      Test validate on a non-empty postgresql section, with user=None.
      """
      config = LocalConfig()
      config.postgresql = PostgresqlConfig(None, "gzip", True, None)
      config.validate()


   ############################
   # Test parsing of documents
   ############################

   def testParse_001(self):
      """
      Parse empty config document.
      """
      path = self.resources["postgresql.conf.1"]
      contents = open(path).read()
      self.failUnlessRaises(ValueError, LocalConfig, xmlPath=path, validate=True)
      self.failUnlessRaises(ValueError, LocalConfig, xmlData=contents, validate=True)
      config = LocalConfig(xmlPath=path, validate=False)
      self.failUnlessEqual(None, config.postgresql)
      config = LocalConfig(xmlData=contents, validate=False)
      self.failUnlessEqual(None, config.postgresql)

   def testParse_003(self):
      """
      Parse config document containing only a postgresql section, no databases, all=True.
      """
      path = self.resources["postgresql.conf.2"]
      contents = open(path).read()
      config = LocalConfig(xmlPath=path, validate=False)
      self.failIfEqual(None, config.postgresql)
      self.failUnlessEqual("user", config.postgresql.user)
      self.failUnlessEqual("none", config.postgresql.compressMode)
      self.failUnlessEqual(True, config.postgresql.all)
      self.failUnlessEqual(None, config.postgresql.databases)
      config = LocalConfig(xmlData=contents, validate=False)
      self.failUnlessEqual("user", config.postgresql.user)
      self.failUnlessEqual("none", config.postgresql.compressMode)
      self.failUnlessEqual(True, config.postgresql.all)
      self.failUnlessEqual(None, config.postgresql.databases)

   def testParse_004(self):
      """
      Parse config document containing only a postgresql section, single database, all=False.
      """
      path = self.resources["postgresql.conf.3"]
      contents = open(path).read()
      config = LocalConfig(xmlPath=path, validate=False)
      self.failIfEqual(None, config.postgresql)
      self.failUnlessEqual("user", config.postgresql.user)
      self.failUnlessEqual("gzip", config.postgresql.compressMode)
      self.failUnlessEqual(False, config.postgresql.all)
      self.failUnlessEqual(["database", ], config.postgresql.databases)
      config = LocalConfig(xmlData=contents, validate=False)
      self.failIfEqual(None, config.postgresql)
      self.failUnlessEqual("user", config.postgresql.user)
      self.failUnlessEqual("gzip", config.postgresql.compressMode)
      self.failUnlessEqual(False, config.postgresql.all)
      self.failUnlessEqual(["database", ], config.postgresql.databases)

   def testParse_005(self):
      """
      Parse config document containing only a postgresql section, multiple databases, all=False.
      """
      path = self.resources["postgresql.conf.4"]
      contents = open(path).read()
      config = LocalConfig(xmlPath=path, validate=False)
      self.failIfEqual(None, config.postgresql)
      self.failUnlessEqual("user", config.postgresql.user)
      self.failUnlessEqual("bzip2", config.postgresql.compressMode)
      self.failUnlessEqual(False, config.postgresql.all)
      self.failUnlessEqual(["database1", "database2", ], config.postgresql.databases)
      config = LocalConfig(xmlData=contents, validate=False)
      self.failIfEqual(None, config.postgresql)
      self.failUnlessEqual("user", config.postgresql.user)
      self.failUnlessEqual("bzip2", config.postgresql.compressMode)
      self.failUnlessEqual(False, config.postgresql.all)
      self.failUnlessEqual(["database1", "database2", ], config.postgresql.databases)

   def testParse_006(self):
      """
      Parse config document containing only a postgresql section, no user, multiple databases, all=False.
      """
      path = self.resources["postgresql.conf.5"]
      contents = open(path).read()
      config = LocalConfig(xmlPath=path, validate=False)
      self.failIfEqual(None, config.postgresql)
      self.failUnlessEqual(None, config.postgresql.user)
      self.failUnlessEqual("bzip2", config.postgresql.compressMode)
      self.failUnlessEqual(False, config.postgresql.all)
      self.failUnlessEqual(["database1", "database2", ], config.postgresql.databases)
      config = LocalConfig(xmlData=contents, validate=False)
      self.failIfEqual(None, config.postgresql)
      self.failUnlessEqual(None, config.postgresql.user)
      self.failUnlessEqual("bzip2", config.postgresql.compressMode)
      self.failUnlessEqual(False, config.postgresql.all)
      self.failUnlessEqual(["database1", "database2", ], config.postgresql.databases)


   ###################
   # Test addConfig()
   ###################

   def testAddConfig_001(self):
      """
      Test with empty config document
      """
      config = LocalConfig()
      self.validateAddConfig(config)

   def testAddConfig_003(self):
      """
      Test with no databases, all other values filled in, all=True.
      """
      config = LocalConfig()
      config.postgresql = PostgresqlConfig("user", "none", True, None)
      self.validateAddConfig(config)

   def testAddConfig_004(self):
      """
      Test with no databases, all other values filled in, all=False.
      """
      config = LocalConfig()
      config.postgresql = PostgresqlConfig("user", "gzip", False, None)
      self.validateAddConfig(config)

   def testAddConfig_005(self):
      """
      Test with single database, all other values filled in, all=True.
      """
      config = LocalConfig()
      config.postgresql = PostgresqlConfig("user", "bzip2", True, [ "database", ])
      self.validateAddConfig(config)

   def testAddConfig_006(self):
      """
      Test with single database, all other values filled in, all=False.
      """
      config = LocalConfig()
      config.postgresql = PostgresqlConfig("user", "none", False, [ "database", ])
      self.validateAddConfig(config)

   def testAddConfig_007(self):
      """
      Test with multiple databases, all other values filled in, all=True.
      """
      config = LocalConfig()
      config.postgresql = PostgresqlConfig("user", "bzip2", True, [ "database1", "database2", ])
      self.validateAddConfig(config)

   def testAddConfig_008(self):
      """
      Test with multiple databases, all other values filled in, all=False.
      """
      config = LocalConfig()
      config.postgresql = PostgresqlConfig("user", "gzip", True, [ "database1", "database2", ])
      self.validateAddConfig(config)

   def testAddConfig_009(self):
      """
      Test with multiple databases, user=None but all other values filled in, all=False.
      """
      config = LocalConfig()
      config.postgresql = PostgresqlConfig(None, "gzip", True, [ "database1", "database2", ])
      self.validateAddConfig(config)


#######################################################################
# Suite definition
#######################################################################

def suite():
   """Returns a suite containing all the test cases in this module."""
   return unittest.TestSuite((
                              unittest.makeSuite(TestPostgresqlConfig, 'test'), 
                              unittest.makeSuite(TestLocalConfig, 'test'), 
                            ))


########################################################################
# Module entry point
########################################################################

# When this module is executed from the command-line, run its tests
if __name__ == '__main__':
   unittest.main()

