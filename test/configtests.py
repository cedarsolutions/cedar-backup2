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


   ###################
   # Test constructor
   ###################

   def testConstructor_001(self):
      """
      Blah, blah.
      """
      pass


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


   ###################
   # Test constructor
   ###################

   def testConstructor_001(self):
      """
      Blah, blah.
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


   ###################
   # Test constructor
   ###################

   def testConstructor_001(self):
      """
      Blah, blah.
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


   ###################
   # Test constructor
   ###################

   def testConstructor_001(self):
      """
      Blah, blah.
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


   ###################
   # Test constructor
   ###################

   def testConstructor_001(self):
      """
      Blah, blah.
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


   ###################
   # Test constructor
   ###################

   def testConstructor_001(self):
      """
      Blah, blah.
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


   ###################
   # Test constructor
   ###################

   def testConstructor_001(self):
      """
      Blah, blah.
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


   ###################
   # Test constructor
   ###################

   def testConstructor_001(self):
      """
      Blah, blah.
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


   ###################
   # Test constructor
   ###################

   def testConstructor_001(self):
      """
      Blah, blah.
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


   ###################
   # Test constructor
   ###################

   def testConstructor_001(self):
      """
      Blah, blah.
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


   ###################
   # Test constructor
   ###################

   def testConstructor_001(self):
      """
      Blah, blah.
      """
      pass


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

