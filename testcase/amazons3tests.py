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
# Copyright (c) 2014-2015 Kenneth J. Pronovici.
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
# Purpose  : Tests amazons3 extension functionality.
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

########################################################################
# Module documentation
########################################################################

"""
Unit tests for CedarBackup2/extend/amazons3.py.

Code Coverage
=============

   This module contains individual tests for the the public classes implemented
   in extend/amazons3.py.  There are also tests for some of the private
   functions.

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
from CedarBackup2.extend.amazons3 import LocalConfig, AmazonS3Config


#######################################################################
# Module-wide configuration and constants
#######################################################################

DATA_DIRS = [ "./data", "./testcase/data", ]
RESOURCES = [ "amazons3.conf.1", "amazons3.conf.2", "tree1.tar.gz", "tree2.tar.gz", 
              "tree8.tar.gz", "tree15.tar.gz", "tree16.tar.gz", "tree17.tar.gz",
              "tree18.tar.gz", "tree19.tar.gz", "tree20.tar.gz", ]


#######################################################################
# Test Case Classes
#######################################################################

##########################
# TestAmazonS3Config class
##########################

class TestAmazonS3Config(unittest.TestCase):

   """Tests for the AmazonS3Config class."""

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
      obj = AmazonS3Config()
      obj.__repr__()
      obj.__str__()


   ##################################
   # Test constructor and attributes
   ##################################

   def testConstructor_001(self):
      """
      Test constructor with no values filled in.
      """
      amazons3 = AmazonS3Config()
      self.failUnlessEqual(False, amazons3.warnMidnite)
      self.failUnlessEqual(None, amazons3.s3Bucket)
      self.failUnlessEqual(None, amazons3.encryptCommand)
      self.failUnlessEqual(None, amazons3.fullBackupSizeLimit)
      self.failUnlessEqual(None, amazons3.incrementalBackupSizeLimit)

   def testConstructor_002(self):
      """
      Test constructor with all values filled in, with valid values.
      """
      amazons3 = AmazonS3Config(True, "bucket", "encrypt", 1, 2)
      self.failUnlessEqual(True, amazons3.warnMidnite)
      self.failUnlessEqual("bucket", amazons3.s3Bucket)
      self.failUnlessEqual("encrypt", amazons3.encryptCommand)
      self.failUnlessEqual(1L, amazons3.fullBackupSizeLimit)
      self.failUnlessEqual(2L, amazons3.incrementalBackupSizeLimit)

   def testConstructor_003(self):
      """
      Test assignment of warnMidnite attribute, valid value (real boolean).
      """
      amazons3 = AmazonS3Config()
      self.failUnlessEqual(False, amazons3.warnMidnite)
      amazons3.warnMidnite = True
      self.failUnlessEqual(True, amazons3.warnMidnite)
      amazons3.warnMidnite = False
      self.failUnlessEqual(False, amazons3.warnMidnite)

   def testConstructor_004(self):
      """
      Test assignment of warnMidnite attribute, valid value (expression).
      """
      amazons3 = AmazonS3Config()
      self.failUnlessEqual(False, amazons3.warnMidnite)
      amazons3.warnMidnite = 0
      self.failUnlessEqual(False, amazons3.warnMidnite)
      amazons3.warnMidnite = []
      self.failUnlessEqual(False, amazons3.warnMidnite)
      amazons3.warnMidnite = None
      self.failUnlessEqual(False, amazons3.warnMidnite)
      amazons3.warnMidnite = ['a']
      self.failUnlessEqual(True, amazons3.warnMidnite)
      amazons3.warnMidnite = 3
      self.failUnlessEqual(True, amazons3.warnMidnite)

   def testConstructor_005(self):
      """
      Test assignment of s3Bucket attribute, None value.
      """
      amazons3 = AmazonS3Config(s3Bucket="bucket")
      self.failUnlessEqual("bucket", amazons3.s3Bucket)
      amazons3.s3Bucket = None
      self.failUnlessEqual(None, amazons3.s3Bucket)

   def testConstructor_006(self):
      """
      Test assignment of s3Bucket attribute, valid value.
      """
      amazons3 = AmazonS3Config()
      self.failUnlessEqual(None, amazons3.s3Bucket)
      amazons3.s3Bucket = "bucket"
      self.failUnlessEqual("bucket", amazons3.s3Bucket)

   def testConstructor_007(self):
      """
      Test assignment of s3Bucket attribute, invalid value (empty).
      """
      amazons3 = AmazonS3Config()
      self.failUnlessEqual(None, amazons3.s3Bucket)
      self.failUnlessAssignRaises(ValueError, amazons3, "s3Bucket", "")
      self.failUnlessEqual(None, amazons3.s3Bucket)

   def testConstructor_008(self):
      """
      Test assignment of encryptCommand attribute, None value.
      """
      amazons3 = AmazonS3Config(encryptCommand="encrypt")
      self.failUnlessEqual("encrypt", amazons3.encryptCommand)
      amazons3.encryptCommand = None
      self.failUnlessEqual(None, amazons3.encryptCommand)

   def testConstructor_009(self):
      """
      Test assignment of encryptCommand attribute, valid value.
      """
      amazons3 = AmazonS3Config()
      self.failUnlessEqual(None, amazons3.encryptCommand)
      amazons3.encryptCommand = "encrypt"
      self.failUnlessEqual("encrypt", amazons3.encryptCommand)

   def testConstructor_010(self):
      """
      Test assignment of encryptCommand attribute, invalid value (empty).
      """
      amazons3 = AmazonS3Config()
      self.failUnlessEqual(None, amazons3.encryptCommand)
      self.failUnlessAssignRaises(ValueError, amazons3, "encryptCommand", "")
      self.failUnlessEqual(None, amazons3.encryptCommand)

   def testConstructor_011(self):
      """
      Test assignment of fullBackupSizeLimit attribute, None value.
      """
      amazons3 = AmazonS3Config(fullBackupSizeLimit=100)
      self.failUnlessEqual(100L, amazons3.fullBackupSizeLimit)
      amazons3.fullBackupSizeLimit = None
      self.failUnlessEqual(None, amazons3.fullBackupSizeLimit)

   def testConstructor_012(self):
      """
      Test assignment of fullBackupSizeLimit attribute, valid long value.
      """
      amazons3 = AmazonS3Config()
      self.failUnlessEqual(None, amazons3.fullBackupSizeLimit)
      amazons3.fullBackupSizeLimit = 7516192768L
      self.failUnlessEqual(7516192768L, amazons3.fullBackupSizeLimit)

   def testConstructor_013(self):
      """
      Test assignment of fullBackupSizeLimit attribute, valid string value.
      """
      amazons3 = AmazonS3Config()
      self.failUnlessEqual(None, amazons3.fullBackupSizeLimit)
      amazons3.fullBackupSizeLimit = "7516192768"
      self.failUnlessEqual(7516192768L, amazons3.fullBackupSizeLimit)

   def testConstructor_014(self):
      """
      Test assignment of fullBackupSizeLimit attribute, invalid value.
      """
      amazons3 = AmazonS3Config()
      self.failUnlessEqual(None, amazons3.fullBackupSizeLimit)
      self.failUnlessAssignRaises(ValueError, amazons3, "fullBackupSizeLimit", "xxx")
      self.failUnlessEqual(None, amazons3.fullBackupSizeLimit)

   def testConstructor_015(self):
      """
      Test assignment of incrementalBackupSizeLimit attribute, None value.
      """
      amazons3 = AmazonS3Config(incrementalBackupSizeLimit=100)
      self.failUnlessEqual(100L, amazons3.incrementalBackupSizeLimit)
      amazons3.incrementalBackupSizeLimit = None
      self.failUnlessEqual(None, amazons3.incrementalBackupSizeLimit)

   def testConstructor_016(self):
      """
      Test assignment of incrementalBackupSizeLimit attribute, valid long value.
      """
      amazons3 = AmazonS3Config()
      self.failUnlessEqual(None, amazons3.incrementalBackupSizeLimit)
      amazons3.incrementalBackupSizeLimit = 7516192768L
      self.failUnlessEqual(7516192768L, amazons3.incrementalBackupSizeLimit)

   def testConstructor_017(self):
      """
      Test assignment of incrementalBackupSizeLimit attribute, valid string value.
      """
      amazons3 = AmazonS3Config()
      self.failUnlessEqual(None, amazons3.incrementalBackupSizeLimit)
      amazons3.incrementalBackupSizeLimit = "7516192768"
      self.failUnlessEqual(7516192768L, amazons3.incrementalBackupSizeLimit)

   def testConstructor_018(self):
      """
      Test assignment of incrementalBackupSizeLimit attribute, invalid value.
      """
      amazons3 = AmazonS3Config()
      self.failUnlessEqual(None, amazons3.incrementalBackupSizeLimit)
      self.failUnlessAssignRaises(ValueError, amazons3, "incrementalBackupSizeLimit", "xxx")
      self.failUnlessEqual(None, amazons3.incrementalBackupSizeLimit)


   ############################
   # Test comparison operators
   ############################

   def testComparison_001(self):
      """
      Test comparison of two identical objects, all attributes None.
      """
      amazons31 = AmazonS3Config()
      amazons32 = AmazonS3Config()
      self.failUnlessEqual(amazons31, amazons32)
      self.failUnless(amazons31 == amazons32)
      self.failUnless(not amazons31 < amazons32)
      self.failUnless(amazons31 <= amazons32)
      self.failUnless(not amazons31 > amazons32)
      self.failUnless(amazons31 >= amazons32)
      self.failUnless(not amazons31 != amazons32)

   def testComparison_002(self):
      """
      Test comparison of two identical objects, all attributes non-None.
      """
      amazons31 = AmazonS3Config(True, "bucket", "encrypt", 1, 2)
      amazons32 = AmazonS3Config(True, "bucket", "encrypt", 1, 2)
      self.failUnlessEqual(amazons31, amazons32)
      self.failUnless(amazons31 == amazons32)
      self.failUnless(not amazons31 < amazons32)
      self.failUnless(amazons31 <= amazons32)
      self.failUnless(not amazons31 > amazons32)
      self.failUnless(amazons31 >= amazons32)
      self.failUnless(not amazons31 != amazons32)

   def testComparison_003(self):
      """
      Test comparison of two differing objects, warnMidnite differs.
      """
      amazons31 = AmazonS3Config(warnMidnite=False)
      amazons32 = AmazonS3Config(warnMidnite=True)
      self.failIfEqual(amazons31, amazons32)
      self.failUnless(not amazons31 == amazons32)
      self.failUnless(amazons31 < amazons32)
      self.failUnless(amazons31 <= amazons32)
      self.failUnless(not amazons31 > amazons32)
      self.failUnless(not amazons31 >= amazons32)
      self.failUnless(amazons31 != amazons32)

   def testComparison_004(self):
      """
      Test comparison of two differing objects, s3Bucket differs (one None).
      """
      amazons31 = AmazonS3Config()
      amazons32 = AmazonS3Config(s3Bucket="bucket")
      self.failIfEqual(amazons31, amazons32)
      self.failUnless(not amazons31 == amazons32)
      self.failUnless(amazons31 < amazons32)
      self.failUnless(amazons31 <= amazons32)
      self.failUnless(not amazons31 > amazons32)
      self.failUnless(not amazons31 >= amazons32)
      self.failUnless(amazons31 != amazons32)

   def testComparison_005(self):
      """
      Test comparison of two differing objects, s3Bucket differs.
      """
      amazons31 = AmazonS3Config(s3Bucket="bucket1")
      amazons32 = AmazonS3Config(s3Bucket="bucket2")
      self.failIfEqual(amazons31, amazons32)
      self.failUnless(not amazons31 == amazons32)
      self.failUnless(amazons31 < amazons32)
      self.failUnless(amazons31 <= amazons32)
      self.failUnless(not amazons31 > amazons32)
      self.failUnless(not amazons31 >= amazons32)
      self.failUnless(amazons31 != amazons32)

   def testComparison_006(self):
      """
      Test comparison of two differing objects, encryptCommand differs (one None).
      """
      amazons31 = AmazonS3Config()
      amazons32 = AmazonS3Config(encryptCommand="encrypt")
      self.failIfEqual(amazons31, amazons32)
      self.failUnless(not amazons31 == amazons32)
      self.failUnless(amazons31 < amazons32)
      self.failUnless(amazons31 <= amazons32)
      self.failUnless(not amazons31 > amazons32)
      self.failUnless(not amazons31 >= amazons32)
      self.failUnless(amazons31 != amazons32)

   def testComparison_007(self):
      """
      Test comparison of two differing objects, encryptCommand differs.
      """
      amazons31 = AmazonS3Config(encryptCommand="encrypt1")
      amazons32 = AmazonS3Config(encryptCommand="encrypt2")
      self.failIfEqual(amazons31, amazons32)
      self.failUnless(not amazons31 == amazons32)
      self.failUnless(amazons31 < amazons32)
      self.failUnless(amazons31 <= amazons32)
      self.failUnless(not amazons31 > amazons32)
      self.failUnless(not amazons31 >= amazons32)
      self.failUnless(amazons31 != amazons32)

   def testComparison_008(self):
      """
      Test comparison of two differing objects, fullBackupSizeLimit differs (one None).
      """
      amazons31 = AmazonS3Config()
      amazons32 = AmazonS3Config(fullBackupSizeLimit=1L)
      self.failIfEqual(amazons31, amazons32)
      self.failUnless(not amazons31 == amazons32)
      self.failUnless(amazons31 < amazons32)
      self.failUnless(amazons31 <= amazons32)
      self.failUnless(not amazons31 > amazons32)
      self.failUnless(not amazons31 >= amazons32)
      self.failUnless(amazons31 != amazons32)

   def testComparison_009(self):
      """
      Test comparison of two differing objects, fullBackupSizeLimit differs.
      """
      amazons31 = AmazonS3Config(fullBackupSizeLimit=1L)
      amazons32 = AmazonS3Config(fullBackupSizeLimit=2L)
      self.failIfEqual(amazons31, amazons32)
      self.failUnless(not amazons31 == amazons32)
      self.failUnless(amazons31 < amazons32)
      self.failUnless(amazons31 <= amazons32)
      self.failUnless(not amazons31 > amazons32)
      self.failUnless(not amazons31 >= amazons32)
      self.failUnless(amazons31 != amazons32)

   def testComparison_010(self):
      """
      Test comparison of two differing objects, incrementalBackupSizeLimit differs (one None).
      """
      amazons31 = AmazonS3Config()
      amazons32 = AmazonS3Config(incrementalBackupSizeLimit=1L)
      self.failIfEqual(amazons31, amazons32)
      self.failUnless(not amazons31 == amazons32)
      self.failUnless(amazons31 < amazons32)
      self.failUnless(amazons31 <= amazons32)
      self.failUnless(not amazons31 > amazons32)
      self.failUnless(not amazons31 >= amazons32)
      self.failUnless(amazons31 != amazons32)

   def testComparison_011(self):
      """
      Test comparison of two differing objects, incrementalBackupSizeLimit differs.
      """
      amazons31 = AmazonS3Config(incrementalBackupSizeLimit=1L)
      amazons32 = AmazonS3Config(incrementalBackupSizeLimit=2L)
      self.failIfEqual(amazons31, amazons32)
      self.failUnless(not amazons31 == amazons32)
      self.failUnless(amazons31 < amazons32)
      self.failUnless(amazons31 <= amazons32)
      self.failUnless(not amazons31 > amazons32)
      self.failUnless(not amazons31 >= amazons32)
      self.failUnless(amazons31 != amazons32)


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

      We dump a document containing just the amazons3 configuration, and then
      make sure that if we push that document back into the C{LocalConfig}
      object, that the resulting object matches the original.

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
      self.failUnlessEqual(None, config.amazons3)

   def testConstructor_002(self):
      """
      Test empty constructor, validate=True.
      """
      config = LocalConfig(validate=True)
      self.failUnlessEqual(None, config.amazons3)

   def testConstructor_003(self):
      """
      Test with empty config document as both data and file, validate=False.
      """
      path = self.resources["amazons3.conf.1"]
      contents = open(path).read()
      self.failUnlessRaises(ValueError, LocalConfig, xmlData=contents, xmlPath=path, validate=False)

   def testConstructor_004(self):
      """
      Test assignment of amazons3 attribute, None value.
      """
      config = LocalConfig()
      config.amazons3 = None
      self.failUnlessEqual(None, config.amazons3)

   def testConstructor_005(self):
      """
      Test assignment of amazons3 attribute, valid value.
      """
      config = LocalConfig()
      config.amazons3 = AmazonS3Config()
      self.failUnlessEqual(AmazonS3Config(), config.amazons3)

   def testConstructor_006(self):
      """
      Test assignment of amazons3 attribute, invalid value (not AmazonS3Config).
      """
      config = LocalConfig()
      self.failUnlessAssignRaises(ValueError, config, "amazons3", "STRING!")


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
      config1.amazons3 = AmazonS3Config()

      config2 = LocalConfig()
      config2.amazons3 = AmazonS3Config()

      self.failUnlessEqual(config1, config2)
      self.failUnless(config1 == config2)
      self.failUnless(not config1 < config2)
      self.failUnless(config1 <= config2)
      self.failUnless(not config1 > config2)
      self.failUnless(config1 >= config2)
      self.failUnless(not config1 != config2)

   def testComparison_003(self):
      """
      Test comparison of two differing objects, amazons3 differs (one None).
      """
      config1 = LocalConfig()
      config2 = LocalConfig()
      config2.amazons3 = AmazonS3Config()
      self.failIfEqual(config1, config2)
      self.failUnless(not config1 == config2)
      self.failUnless(config1 < config2)
      self.failUnless(config1 <= config2)
      self.failUnless(not config1 > config2)
      self.failUnless(not config1 >= config2)
      self.failUnless(config1 != config2)

   def testComparison_004(self):
      """
      Test comparison of two differing objects, s3Bucket differs.
      """
      config1 = LocalConfig()
      config1.amazons3 = AmazonS3Config(True, "bucket1", "encrypt", 1, 2)

      config2 = LocalConfig()
      config2.amazons3 = AmazonS3Config(True, "bucket2", "encrypt", 1, 2)

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
      Test validate on a None amazons3 section.
      """
      config = LocalConfig()
      config.amazons3 = None
      self.failUnlessRaises(ValueError, config.validate)

   def testValidate_002(self):
      """
      Test validate on an empty amazons3 section.
      """
      config = LocalConfig()
      config.amazons3 = AmazonS3Config()
      self.failUnlessRaises(ValueError, config.validate)

   def testValidate_003(self):
      """
      Test validate on a non-empty amazons3 section with no values filled in.
      """
      config = LocalConfig()
      config.amazons3 = AmazonS3Config(None)
      self.failUnlessRaises(ValueError, config.validate)

   def testValidate_005(self):
      """
      Test validate on a non-empty amazons3 section with valid values filled in.
      """
      config = LocalConfig()
      config.amazons3 = AmazonS3Config(True, "bucket")
      config.validate()


   ############################
   # Test parsing of documents
   ############################

   def testParse_001(self):
      """
      Parse empty config document.
      """
      path = self.resources["amazons3.conf.1"]
      contents = open(path).read()
      self.failUnlessRaises(ValueError, LocalConfig, xmlPath=path, validate=True)
      self.failUnlessRaises(ValueError, LocalConfig, xmlData=contents, validate=True)
      config = LocalConfig(xmlPath=path, validate=False)
      self.failUnlessEqual(None, config.amazons3)
      config = LocalConfig(xmlData=contents, validate=False)
      self.failUnlessEqual(None, config.amazons3)

   def testParse_002(self):
      """
      Parse config document with filled-in values.
      """
      path = self.resources["amazons3.conf.2"]
      contents = open(path).read()
      config = LocalConfig(xmlPath=path, validate=False)
      self.failIfEqual(None, config.amazons3)
      self.failUnlessEqual(True, config.amazons3.warnMidnite)
      self.failUnlessEqual("mybucket", config.amazons3.s3Bucket)
      self.failUnlessEqual("encrypt", config.amazons3.encryptCommand)
      self.failUnlessEqual(5368709120L, config.amazons3.fullBackupSizeLimit)
      self.failUnlessEqual(2147483648, config.amazons3.incrementalBackupSizeLimit)
      config = LocalConfig(xmlData=contents, validate=False)
      self.failIfEqual(None, config.amazons3)
      self.failUnlessEqual(True, config.amazons3.warnMidnite)
      self.failUnlessEqual("mybucket", config.amazons3.s3Bucket)
      self.failUnlessEqual("encrypt", config.amazons3.encryptCommand)
      self.failUnlessEqual(5368709120L, config.amazons3.fullBackupSizeLimit)
      self.failUnlessEqual(2147483648, config.amazons3.incrementalBackupSizeLimit)


   ###################
   # Test addConfig()
   ###################

   def testAddConfig_001(self):
      """
      Test with empty config document.
      """
      amazons3 = AmazonS3Config()
      config = LocalConfig()
      config.amazons3 = amazons3
      self.validateAddConfig(config)

   def testAddConfig_002(self):
      """
      Test with values set.
      """
      amazons3 = AmazonS3Config(True, "bucket", "encrypt", 1, 2)
      config = LocalConfig()
      config.amazons3 = amazons3
      self.validateAddConfig(config)


#######################################################################
# Suite definition
#######################################################################

def suite():
   """Returns a suite containing all the test cases in this module."""
   return unittest.TestSuite((
                              unittest.makeSuite(TestAmazonS3Config, 'test'), 
                              unittest.makeSuite(TestLocalConfig, 'test'), 
                            ))


########################################################################
# Module entry point
########################################################################

# When this module is executed from the command-line, run its tests
if __name__ == '__main__':
   unittest.main()

