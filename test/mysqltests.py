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
# Purpose  : Tests MySQL extension functionality.
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# This file was created with a width of 132 characters, and NO tabs.

########################################################################
# Module documentation
########################################################################

"""
Unit tests for CedarBackup2/extend/mysql.py.

Code Coverage
=============

   This module contains individual tests for the many of the public functions
   and classes implemented in extend/mysql.py.  There are also tests for
   several of the private methods.

   Unfortunately, it's rather difficult to test this code in an automated
   fashion, even if you have access to MySQL, since the actual dump would need
   to have access to a real database.  Because of this, there aren't any tests
   below that actually talk to a database.

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

   It would argumably be better if we could do a completely independent check -
   but implementing that check would be equivalent to re-implementing all of
   the existing functionality that we're validating here!  After all, the most
   important thing is that data can move seamlessly from object to XML document
   and back to object.

Full vs. Reduced Tests
======================

   All of the tests in this module are considered safe to be run in an average
   build environment.  There is a no need to use a MYSQLTESTS_FULL environment
   variable to provide a "reduced feature set" test suite as for some of the
   other test modules.

@author Kenneth J. Pronovici <pronovic@ieee.org>
"""


########################################################################
# Import modules and do runtime validations
########################################################################

# System modules
import unittest
from gzip import GzipFile
import tempfile
import os
from StringIO import StringIO

# XML-related modules
from xml.dom.minidom import getDOMImplementation
from xml.dom.ext import PrettyPrint

# Cedar Backup modules
from CedarBackup2.testutil import findResources, buildPath, removedir, failUnlessAssignRaises
from CedarBackup2.extend.mysql import LocalConfig, MysqlConfig, _buildDumpArgs, _getOutputFile


#######################################################################
# Module-wide configuration and constants
#######################################################################

DATA_DIRS = [ "./data", "./test/data", ]
RESOURCES = [ "mysql.conf.1", "mysql.conf.2", "mysql.conf.3", "mysql.conf.4", ]


#######################################################################
# Test Case Classes
#######################################################################

########################
# TestMysqlConfig class
########################

class TestMysqlConfig(unittest.TestCase):

   """Tests for the MysqlConfig class."""

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
      obj = MysqlConfig()
      obj.__repr__()
      obj.__str__()


   ##################################
   # Test constructor and attributes
   ##################################

   def testConstructor_001(self):
      """
      Test constructor with no values filled in.
      """
      mysql = MysqlConfig()
      self.failUnlessEqual(None, mysql.user)
      self.failUnlessEqual(None, mysql.password)
      self.failUnlessEqual(False, mysql.all)
      self.failUnlessEqual(None, mysql.databases)

   def testConstructor_002(self):
      """
      Test constructor with all values filled in, with valid values, databases=None.
      """
      mysql = MysqlConfig("user", "password", False, None)
      self.failUnlessEqual("user", mysql.user)
      self.failUnlessEqual("password", mysql.password)
      self.failUnlessEqual(False, mysql.all)
      self.failUnlessEqual(None, mysql.databases)

   def testConstructor_003(self):
      """
      Test constructor with all values filled in, with valid values, no databases.
      """
      mysql = MysqlConfig("user", "password", True, [])
      self.failUnlessEqual("user", mysql.user)
      self.failUnlessEqual("password", mysql.password)
      self.failUnlessEqual(True, mysql.all)
      self.failUnlessEqual([], mysql.databases)

   def testConstructor_004(self):
      """
      Test constructor with all values filled in, with valid values, with one database.
      """
      mysql = MysqlConfig("user", "password", True,  [ "one", ])
      self.failUnlessEqual("user", mysql.user)
      self.failUnlessEqual("password", mysql.password)
      self.failUnlessEqual(True, mysql.all)
      self.failUnlessEqual([ "one", ], mysql.databases)

   def testConstructor_005(self):
      """
      Test constructor with all values filled in, with valid values, with multiple databases.
      """
      mysql = MysqlConfig("user", "password", True, [ "one", "two", ])
      self.failUnlessEqual("user", mysql.user)
      self.failUnlessEqual("password", mysql.password)
      self.failUnlessEqual(True, mysql.all)
      self.failUnlessEqual([ "one", "two", ], mysql.databases)

   def testConstructor_006(self):
      """
      Test assignment of user attribute, None value.
      """
      mysql = MysqlConfig(user="user")
      self.failUnlessEqual("user", mysql.user)
      mysql.user = None
      self.failUnlessEqual(None, mysql.user)

   def testConstructor_007(self):
      """
      Test assignment of user attribute, valid value.
      """
      mysql = MysqlConfig()
      self.failUnlessEqual(None, mysql.user)
      mysql.user = "user"
      self.failUnlessEqual("user", mysql.user)

   def testConstructor_008(self):
      """
      Test assignment of user attribute, invalid value (empty).
      """
      mysql = MysqlConfig()
      self.failUnlessEqual(None, mysql.user)
      self.failUnlessAssignRaises(ValueError, mysql, "user", "")
      self.failUnlessEqual(None, mysql.user)

   def testConstructor_009(self):
      """
      Test assignment of password attribute, None value.
      """
      mysql = MysqlConfig(password="password")
      self.failUnlessEqual("password", mysql.password)
      mysql.password = None
      self.failUnlessEqual(None, mysql.password)

   def testConstructor_010(self):
      """
      Test assignment of password attribute, valid value.
      """
      mysql = MysqlConfig()
      self.failUnlessEqual(None, mysql.password)
      mysql.password = "password"
      self.failUnlessEqual("password", mysql.password)

   def testConstructor_011(self):
      """
      Test assignment of password attribute, invalid value (empty).
      """
      mysql = MysqlConfig()
      self.failUnlessEqual(None, mysql.password)
      self.failUnlessAssignRaises(ValueError, mysql, "password", "")
      self.failUnlessEqual(None, mysql.password)

   def testConstructor_012(self):
      """
      Test assignment of all attribute, None value.
      """
      mysql = MysqlConfig(all=True)
      self.failUnlessEqual(True, mysql.all)
      mysql.all = None
      self.failUnlessEqual(False, mysql.all)

   def testConstructor_013(self):
      """
      Test assignment of all attribute, valid value (real boolean).
      """
      mysql = MysqlConfig()
      self.failUnlessEqual(False, mysql.all)
      mysql.all = True
      self.failUnlessEqual(True, mysql.all)
      mysql.all = False
      self.failUnlessEqual(False, mysql.all)

   def testConstructor_014(self):
      """
      Test assignment of all attribute, valid value (expression).
      """
      mysql = MysqlConfig()
      self.failUnlessEqual(False, mysql.all)
      mysql.all = 0
      self.failUnlessEqual(False, mysql.all)
      mysql.all = []
      self.failUnlessEqual(False, mysql.all)
      mysql.all = None
      self.failUnlessEqual(False, mysql.all)
      mysql.all = ['a']
      self.failUnlessEqual(True, mysql.all)
      mysql.all = 3
      self.failUnlessEqual(True, mysql.all)

   def testConstructor_015(self):
      """
      Test assignment of databases attribute, None value.
      """
      mysql = MysqlConfig(databases=[])
      self.failUnlessEqual([], mysql.databases)
      mysql.databases = None
      self.failUnlessEqual(None, mysql.databases)

   def testConstructor_016(self):
      """
      Test assignment of databases attribute, [] value.
      """
      mysql = MysqlConfig()
      self.failUnlessEqual(None, mysql.databases)
      mysql.databases = []
      self.failUnlessEqual([], mysql.databases)

   def testConstructor_017(self):
      """
      Test assignment of databases attribute, single valid entry.
      """
      mysql = MysqlConfig()
      self.failUnlessEqual(None, mysql.databases)
      mysql.databases = ["/whatever", ]
      self.failUnlessEqual(["/whatever", ], mysql.databases)
      mysql.databases.append("/stuff")
      self.failUnlessEqual(["/whatever", "/stuff", ], mysql.databases)

   def testConstructor_018(self):
      """
      Test assignment of databases attribute, multiple valid entries.
      """
      mysql = MysqlConfig()
      self.failUnlessEqual(None, mysql.databases)
      mysql.databases = ["/whatever", "/stuff", ]
      self.failUnlessEqual(["/whatever", "/stuff", ], mysql.databases)
      mysql.databases.append("/etc/X11")
      self.failUnlessEqual(["/whatever", "/stuff", "/etc/X11", ], mysql.databases)

   def testConstructor_019(self):
      """
      Test assignment of databases attribute, single invalid entry (empty).
      """
      mysql = MysqlConfig()
      self.failUnlessEqual(None, mysql.databases)
      self.failUnlessAssignRaises(ValueError, mysql, "databases", ["", ])
      self.failUnlessEqual(None, mysql.databases)

   def testConstructor_021(self):
      """
      Test assignment of databases attribute, mixed valid and invalid entries.
      """
      mysql = MysqlConfig()
      self.failUnlessEqual(None, mysql.databases)
      self.failUnlessAssignRaises(ValueError, mysql, "databases", ["good", "", "alsogood", ])
      self.failUnlessEqual(None, mysql.databases)


   ############################
   # Test comparison operators
   ############################

   def testComparison_001(self):
      """
      Test comparison of two identical objects, all attributes None.
      """
      mysql1 = MysqlConfig()
      mysql2 = MysqlConfig()
      self.failUnlessEqual(mysql1, mysql2)
      self.failUnless(mysql1 == mysql2)
      self.failUnless(not mysql1 < mysql2)
      self.failUnless(mysql1 <= mysql2)
      self.failUnless(not mysql1 > mysql2)
      self.failUnless(mysql1 >= mysql2)
      self.failUnless(not mysql1 != mysql2)

   def testComparison_002(self):
      """
      Test comparison of two identical objects, all attributes non-None, list None.
      """
      mysql1 = MysqlConfig("user", "password", True, None)
      mysql2 = MysqlConfig("user", "password", True, None)
      self.failUnlessEqual(mysql1, mysql2)
      self.failUnless(mysql1 == mysql2)
      self.failUnless(not mysql1 < mysql2)
      self.failUnless(mysql1 <= mysql2)
      self.failUnless(not mysql1 > mysql2)
      self.failUnless(mysql1 >= mysql2)
      self.failUnless(not mysql1 != mysql2)

   def testComparison_003(self):
      """
      Test comparison of two identical objects, all attributes non-None, list empty.
      """
      mysql1 = MysqlConfig("user", "password", True, [])
      mysql2 = MysqlConfig("user", "password", True, [])
      self.failUnlessEqual(mysql1, mysql2)
      self.failUnless(mysql1 == mysql2)
      self.failUnless(not mysql1 < mysql2)
      self.failUnless(mysql1 <= mysql2)
      self.failUnless(not mysql1 > mysql2)
      self.failUnless(mysql1 >= mysql2)
      self.failUnless(not mysql1 != mysql2)

   def testComparison_004(self):
      """
      Test comparison of two identical objects, all attributes non-None, list non-empty.
      """
      mysql1 = MysqlConfig("user", "password", True, [ "whatever", ])
      mysql2 = MysqlConfig("user", "password", True, [ "whatever", ])
      self.failUnlessEqual(mysql1, mysql2)
      self.failUnless(mysql1 == mysql2)
      self.failUnless(not mysql1 < mysql2)
      self.failUnless(mysql1 <= mysql2)
      self.failUnless(not mysql1 > mysql2)
      self.failUnless(mysql1 >= mysql2)
      self.failUnless(not mysql1 != mysql2)

   def testComparison_005(self):
      """
      Test comparison of two differing objects, user differs (one None).
      """
      mysql1 = MysqlConfig()
      mysql2 = MysqlConfig(user="user")
      self.failIfEqual(mysql1, mysql2)
      self.failUnless(not mysql1 == mysql2)
      self.failUnless(mysql1 < mysql2)
      self.failUnless(mysql1 <= mysql2)
      self.failUnless(not mysql1 > mysql2)
      self.failUnless(not mysql1 >= mysql2)
      self.failUnless(mysql1 != mysql2)

   def testComparison_006(self):
      """
      Test comparison of two differing objects, user differs.
      """
      mysql1 = MysqlConfig("user1", "password", True, [ "whatever", ])
      mysql2 = MysqlConfig("user2", "password", True, [ "whatever", ])
      self.failIfEqual(mysql1, mysql2)
      self.failUnless(not mysql1 == mysql2)
      self.failUnless(mysql1 < mysql2)
      self.failUnless(mysql1 <= mysql2)
      self.failUnless(not mysql1 > mysql2)
      self.failUnless(not mysql1 >= mysql2)
      self.failUnless(mysql1 != mysql2)

   def testComparison_007(self):
      """
      Test comparison of two differing objects, password differs (one None).
      """
      mysql1 = MysqlConfig()
      mysql2 = MysqlConfig(password="password")
      self.failIfEqual(mysql1, mysql2)
      self.failUnless(not mysql1 == mysql2)
      self.failUnless(mysql1 < mysql2)
      self.failUnless(mysql1 <= mysql2)
      self.failUnless(not mysql1 > mysql2)
      self.failUnless(not mysql1 >= mysql2)
      self.failUnless(mysql1 != mysql2)

   def testComparison_008(self):
      """
      Test comparison of two differing objects, password differs.
      """
      mysql1 = MysqlConfig("user", "password1", True, [ "whatever", ])
      mysql2 = MysqlConfig("user", "password2", True, [ "whatever", ])
      self.failIfEqual(mysql1, mysql2)
      self.failUnless(not mysql1 == mysql2)
      self.failUnless(mysql1 < mysql2)
      self.failUnless(mysql1 <= mysql2)
      self.failUnless(not mysql1 > mysql2)
      self.failUnless(not mysql1 >= mysql2)
      self.failUnless(mysql1 != mysql2)

   def testComparison_009(self):
      """
      Test comparison of two differing objects, all differs (one None).
      """
      mysql1 = MysqlConfig()
      mysql2 = MysqlConfig(all=True)
      self.failIfEqual(mysql1, mysql2)
      self.failUnless(not mysql1 == mysql2)
      self.failUnless(mysql1 < mysql2)
      self.failUnless(mysql1 <= mysql2)
      self.failUnless(not mysql1 > mysql2)
      self.failUnless(not mysql1 >= mysql2)
      self.failUnless(mysql1 != mysql2)

   def testComparison_010(self):
      """
      Test comparison of two differing objects, all differs.
      """
      mysql1 = MysqlConfig("user", "password", False, [ "whatever", ])
      mysql2 = MysqlConfig("user", "password", True, [ "whatever", ])
      self.failIfEqual(mysql1, mysql2)
      self.failUnless(not mysql1 == mysql2)
      self.failUnless(mysql1 < mysql2)
      self.failUnless(mysql1 <= mysql2)
      self.failUnless(not mysql1 > mysql2)
      self.failUnless(not mysql1 >= mysql2)
      self.failUnless(mysql1 != mysql2)

   def testComparison_013(self):
      """
      Test comparison of two differing objects, databases differs (one None, one empty).
      """
      mysql1 = MysqlConfig()
      mysql2 = MysqlConfig(databases=[])
      self.failIfEqual(mysql1, mysql2)
      self.failUnless(not mysql1 == mysql2)
      self.failUnless(mysql1 < mysql2)
      self.failUnless(mysql1 <= mysql2)
      self.failUnless(not mysql1 > mysql2)
      self.failUnless(not mysql1 >= mysql2)
      self.failUnless(mysql1 != mysql2)

   def testComparison_014(self):
      """
      Test comparison of two differing objects, databases differs (one None, one not empty).
      """
      mysql1 = MysqlConfig()
      mysql2 = MysqlConfig(databases=["whatever",])
      self.failIfEqual(mysql1, mysql2)
      self.failUnless(not mysql1 == mysql2)
      self.failUnless(mysql1 < mysql2)
      self.failUnless(mysql1 <= mysql2)
      self.failUnless(not mysql1 > mysql2)
      self.failUnless(not mysql1 >= mysql2)
      self.failUnless(mysql1 != mysql2)

   def testComparison_015(self):
      """
      Test comparison of two differing objects, databases differs (one empty, one not empty).
      """
      mysql1 = MysqlConfig("user", "password", True, [ ])
      mysql2 = MysqlConfig("user", "password", True, [ "whatever", ])
      self.failIfEqual(mysql1, mysql2)
      self.failUnless(not mysql1 == mysql2)
      self.failUnless(mysql1 < mysql2)
      self.failUnless(mysql1 <= mysql2)
      self.failUnless(not mysql1 > mysql2)
      self.failUnless(not mysql1 >= mysql2)
      self.failUnless(mysql1 != mysql2)

   def testComparison_016(self):
      """
      Test comparison of two differing objects, databases differs (both not empty).
      """
      mysql1 = MysqlConfig("user", "password", True, [ "whatever", ])
      mysql2 = MysqlConfig("user", "password", True, [ "whatever", "bogus", ])
      self.failIfEqual(mysql1, mysql2)
      self.failUnless(not mysql1 == mysql2)
      self.failUnless(not mysql1 < mysql2)     # note: different than standard due to unsorted list
      self.failUnless(not mysql1 <= mysql2)    # note: different than standard due to unsorted list
      self.failUnless(mysql1 > mysql2)         # note: different than standard due to unsorted list
      self.failUnless(mysql1 >= mysql2)        # note: different than standard due to unsorted list
      self.failUnless(mysql1 != mysql2)


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

      We dump a document containing just the mysql configuration, and then make
      sure that if we push that document back into the C{LocalConfig} object,
      that the resulting object matches the original.

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
      self.failUnlessEqual(None, config.mysql)

   def testConstructor_002(self):
      """
      Test empty constructor, validate=True.
      """
      config = LocalConfig(validate=True)
      self.failUnlessEqual(None, config.mysql)

   def testConstructor_003(self):
      """
      Test with empty config document as both data and file, validate=False.
      """
      path = self.resources["mysql.conf.1"]
      contents = open(path).read()
      self.failUnlessRaises(ValueError, LocalConfig, xmlData=contents, xmlPath=path, validate=False)

   def testConstructor_004(self):
      """
      Test assignment of mysql attribute, None value.
      """
      config = LocalConfig()
      config.mysql = None
      self.failUnlessEqual(None, config.mysql)

   def testConstructor_005(self):
      """
      Test assignment of mysql attribute, valid value.
      """
      config = LocalConfig()
      config.mysql = MysqlConfig()
      self.failUnlessEqual(MysqlConfig(), config.mysql)

   def testConstructor_006(self):
      """
      Test assignment of mysql attribute, invalid value (not MysqlConfig).
      """
      config = LocalConfig()
      self.failUnlessAssignRaises(ValueError, config, "mysql", "STRING!")


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
      config1.mysql = MysqlConfig()

      config2 = LocalConfig()
      config2.mysql = MysqlConfig()

      self.failUnlessEqual(config1, config2)
      self.failUnless(config1 == config2)
      self.failUnless(not config1 < config2)
      self.failUnless(config1 <= config2)
      self.failUnless(not config1 > config2)
      self.failUnless(config1 >= config2)
      self.failUnless(not config1 != config2)

   def testComparison_003(self):
      """
      Test comparison of two differing objects, mysql differs (one None).
      """
      config1 = LocalConfig()
      config2 = LocalConfig()
      config2.mysql = MysqlConfig()
      self.failIfEqual(config1, config2)
      self.failUnless(not config1 == config2)
      self.failUnless(config1 < config2)
      self.failUnless(config1 <= config2)
      self.failUnless(not config1 > config2)
      self.failUnless(not config1 >= config2)
      self.failUnless(config1 != config2)

   def testComparison_004(self):
      """
      Test comparison of two differing objects, mysql differs.
      """
      config1 = LocalConfig()
      config1.mysql = MysqlConfig(user="one")

      config2 = LocalConfig()
      config2.mysql = MysqlConfig(user="two")

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
      Test validate on a None mysql section.
      """
      config = LocalConfig()
      config.mysql = None
      self.failUnlessRaises(ValueError, config.validate)

   def testValidate_002(self):
      """
      Test validate on an empty mysql section.
      """
      config = LocalConfig()
      config.mysql = MysqlConfig()
      self.failUnlessRaises(ValueError, config.validate)

   def testValidate_003(self):
      """
      Test validate on a non-empty mysql section, all=True, databases=None.
      """
      config = LocalConfig()
      config.mysql = MysqlConfig("user", "password", True, None)
      config.validate()

   def testValidate_004(self):
      """
      Test validate on a non-empty mysql section, all=True, empty databases.
      """
      config = LocalConfig()
      config.mysql = MysqlConfig("user", "password", True, [])
      config.validate()

   def testValidate_005(self):
      """
      Test validate on a non-empty mysql section, all=True, non-empty databases.
      """
      config = LocalConfig()
      config.mysql = MysqlConfig("user", "password", True, ["whatever", ])
      self.failUnlessRaises(ValueError, config.validate)

   def testValidate_006(self):
      """
      Test validate on a non-empty mysql section, all=False, databases=None.
      """
      config = LocalConfig()
      config.mysql = MysqlConfig("user", "password", False, None)
      self.failUnlessRaises(ValueError, config.validate)

   def testValidate_007(self):
      """
      Test validate on a non-empty mysql section, all=False, empty databases.
      """
      config = LocalConfig()
      config.mysql = MysqlConfig("user", "password", False, [])
      self.failUnlessRaises(ValueError, config.validate)

   def testValidate_008(self):
      """
      Test validate on a non-empty mysql section, all=False, non-empty databases.
      """
      config = LocalConfig()
      config.mysql = MysqlConfig("user", "password", False, ["whatever", ])
      config.validate()


   ############################
   # Test parsing of documents
   ############################

   def testParse_001(self):
      """
      Parse empty config document.
      """
      path = self.resources["mysql.conf.1"]
      contents = open(path).read()
      self.failUnlessRaises(ValueError, LocalConfig, xmlPath=path, validate=True)
      self.failUnlessRaises(ValueError, LocalConfig, xmlData=contents, validate=True)
      config = LocalConfig(xmlPath=path, validate=False)
      self.failUnlessEqual(None, config.mysql)
      config = LocalConfig(xmlData=contents, validate=False)
      self.failUnlessEqual(None, config.mysql)

   def testParse_003(self):
      """
      Parse config document containing only a mysql section, no databases, all=True.
      """
      path = self.resources["mysql.conf.2"]
      contents = open(path).read()
      config = LocalConfig(xmlPath=path, validate=False)
      self.failIfEqual(None, config.mysql)
      self.failUnlessEqual("user", config.mysql.user)
      self.failUnlessEqual("password", config.mysql.password)
      self.failUnlessEqual(True, config.mysql.all)
      self.failUnlessEqual(None, config.mysql.databases)
      config = LocalConfig(xmlData=contents, validate=False)
      self.failUnlessEqual("user", config.mysql.user)
      self.failUnlessEqual("password", config.mysql.password)
      self.failIfEqual(None, config.mysql.password)
      self.failUnlessEqual(True, config.mysql.all)
      self.failUnlessEqual(None, config.mysql.databases)

   def testParse_004(self):
      """
      Parse config document containing only a mysql section, single database, all=False.
      """
      path = self.resources["mysql.conf.3"]
      contents = open(path).read()
      config = LocalConfig(xmlPath=path, validate=False)
      self.failIfEqual(None, config.mysql)
      self.failUnlessEqual("user", config.mysql.user)
      self.failUnlessEqual("password", config.mysql.password)
      self.failUnlessEqual(False, config.mysql.all)
      self.failUnlessEqual(["database", ], config.mysql.databases)
      config = LocalConfig(xmlData=contents, validate=False)
      self.failIfEqual(None, config.mysql)
      self.failUnlessEqual("user", config.mysql.user)
      self.failUnlessEqual("password", config.mysql.password)
      self.failUnlessEqual(False, config.mysql.all)
      self.failUnlessEqual(["database", ], config.mysql.databases)

   def testParse_005(self):
      """
      Parse config document containing only a mysql section, multiple databases, all=False.
      """
      path = self.resources["mysql.conf.4"]
      contents = open(path).read()
      config = LocalConfig(xmlPath=path, validate=False)
      self.failIfEqual(None, config.mysql)
      self.failUnlessEqual("user", config.mysql.user)
      self.failUnlessEqual("password", config.mysql.password)
      self.failUnlessEqual(False, config.mysql.all)
      self.failUnlessEqual(["database1", "database2", ], config.mysql.databases)
      config = LocalConfig(xmlData=contents, validate=False)
      self.failIfEqual(None, config.mysql)
      self.failUnlessEqual("user", config.mysql.user)
      self.failUnlessEqual("password", config.mysql.password)
      self.failUnlessEqual(False, config.mysql.all)
      self.failUnlessEqual(["database1", "database2", ], config.mysql.databases)


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
      config.mysql = MysqlConfig("user", "password", True, None)
      self.validateAddConfig(config)

   def testAddConfig_004(self):
      """
      Test with no databases, all other values filled in, all=False.
      """
      config = LocalConfig()
      config.mysql = MysqlConfig("user", "password", False, None)
      self.validateAddConfig(config)

   def testAddConfig_005(self):
      """
      Test with single database, all other values filled in, all=True.
      """
      config = LocalConfig()
      config.mysql = MysqlConfig("user", "password", True, [ "database", ])
      self.validateAddConfig(config)

   def testAddConfig_006(self):
      """
      Test with single database, all other values filled in, all=False.
      """
      config = LocalConfig()
      config.mysql = MysqlConfig("user", "password", False, [ "database", ])
      self.validateAddConfig(config)

   def testAddConfig_007(self):
      """
      Test with multiple databases, all other values filled in, all=True.
      """
      config = LocalConfig()
      config.mysql = MysqlConfig("user", "password", True, [ "database1", "database2", ])
      self.validateAddConfig(config)

   def testAddConfig_008(self):
      """
      Test with multiple databases, all other values filled in, all=False.
      """
      config = LocalConfig()
      config.mysql = MysqlConfig("user", "password", True, [ "database1", "database2", ])
      self.validateAddConfig(config)


######################
# TestFunctions class
######################

class TestFunctions(unittest.TestCase):

   """Tests for the public functions class."""


   ################
   # Setup methods
   ################

   def setUp(self):
      try:
         self.tmpdir = tempfile.mkdtemp()
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


   ########################
   # Test _buildDumpArgs()
   ########################

   def testBuildDumpArgs_001(self):
      """
      Test with a missing username.
      """
      self.failUnlessRaises(ValueError, _buildDumpArgs, None, "password", None)

   def testBuildDumpArgs_002(self):
      """
      Test with a missing password.
      """
      self.failUnlessRaises(ValueError, _buildDumpArgs, "user", None, None)

   def testBuildDumpArgs_003(self):
      """
      Test with a no database.
      """
      expected = [ "--all-databases", "-all", "--flush-logs", "--opt", "--user=stuff", "--password=other", ]
      args = _buildDumpArgs("stuff", "other", None)
      self.failUnlessEqual(expected, args)

   def testBuildDumpArgs_004(self):
      """
      Test with an indicated database.
      """
      expected = [ "--databases", "-all", "--flush-logs", "--opt", "--user=one", "--password=two", "db1", ]
      args = _buildDumpArgs("one", "two", "db1")
      self.failUnlessEqual(expected, args)


   ########################
   # Test _getOutputFile()
   ########################

   def testGetOutputFile_001(self):
      """
      Test with no database name, compress=True.
      """
      (outputFile, filename) = _getOutputFile(targetDir=self.tmpdir, name=None, compress=True)
      self.failUnlessEqual(self.buildPath(["mysqldump.txt.gz"]), filename)
      outputFile.write("Hello, world.\n")
      outputFile.close()
      realContents = GzipFile(filename=filename, mode="r").readlines()
      self.failUnlessEqual(1, len(realContents))
      self.failUnlessEqual("Hello, world.\n", realContents[0])

   def testGetOutputFile_002(self):
      """
      Test with no database name, compress=False.
      """
      (outputFile, filename) = _getOutputFile(targetDir=self.tmpdir, name=None, compress=False)
      self.failUnlessEqual(self.buildPath(["mysqldump.txt"]), filename)
      outputFile.write("Hello, world.\n")
      outputFile.close()
      realContents = open(filename, "r").readlines()
      self.failUnlessEqual(1, len(realContents))
      self.failUnlessEqual("Hello, world.\n", realContents[0])

   def testGetOutputFile_003(self):
      """
      Test with a simple database name, compress=True.
      """
      (outputFile, filename) = _getOutputFile(targetDir=self.tmpdir, name="database", compress=True)
      self.failUnlessEqual(self.buildPath(["mysqldump-database.txt.gz"]), filename)
      outputFile.write("Hello, world.\n")
      outputFile.close()
      realContents = GzipFile(filename=filename, mode="r").readlines()
      self.failUnlessEqual(1, len(realContents))
      self.failUnlessEqual("Hello, world.\n", realContents[0])

   def testGetOutputFile_004(self):
      """
      Test with a simple database name, compress=False.
      """
      (outputFile, filename) = _getOutputFile(targetDir=self.tmpdir, name="database", compress=False)
      self.failUnlessEqual(self.buildPath(["mysqldump-database.txt"]), filename)
      outputFile.write("Hello, world.\n")
      outputFile.close()
      realContents = open(filename, "r").readlines()
      self.failUnlessEqual(1, len(realContents))
      self.failUnlessEqual("Hello, world.\n", realContents[0])

   def testGetOutputFile_005(self):
      """
      Test with a database name containing spaces, compress=True.
      """
      (outputFile, filename) = _getOutputFile(targetDir=self.tmpdir, name="name with spaces", compress=True)
      self.failUnlessEqual(self.buildPath(["mysqldump-name with spaces.txt.gz"]), filename)
      outputFile.write("Hello, world.\n")
      outputFile.close()
      realContents = GzipFile(filename=filename, mode="r").readlines()
      self.failUnlessEqual(1, len(realContents))
      self.failUnlessEqual("Hello, world.\n", realContents[0])

   def testGetOutputFile_006(self):
      """
      Test with a database name containing spaces, compress=False.
      """
      (outputFile, filename) = _getOutputFile(targetDir=self.tmpdir, name="name with spaces", compress=False)
      self.failUnlessEqual(self.buildPath(["mysqldump-name with spaces.txt"]), filename)
      outputFile.write("Hello, world.\n")
      outputFile.close()
      realContents = open(filename, "r").readlines()
      self.failUnlessEqual(1, len(realContents))
      self.failUnlessEqual("Hello, world.\n", realContents[0])


#######################################################################
# Suite definition
#######################################################################

def suite():
   """Returns a suite containing all the test cases in this module."""
   return unittest.TestSuite((
                              unittest.makeSuite(TestMysqlConfig, 'test'), 
                              unittest.makeSuite(TestLocalConfig, 'test'), 
                              unittest.makeSuite(TestFunctions, 'test'), 
                            ))


########################################################################
# Module entry point
########################################################################

# When this module is executed from the command-line, run its tests
if __name__ == '__main__':
   unittest.main()
