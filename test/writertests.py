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
# Purpose  : Tests image writer functionality.
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
   implemented in writer.py.  There are also tests for several of the private
   methods.

   Unfortunately, it's rather difficult to test this code in an automated
   fashion, even if you have access to a physical CD writer drive.  It's even
   more difficult to test it if you are running on some build daemon (think of
   a Debian autobuilder) which can't be expected to have any hardware or any
   media that you could write to.  Because of this, there aren't any tests
   below that actually cause CD media to be written to.

   As a compromise, many of the implementation is in terms of private static
   methods.  Normally, I prefer to only test the public interface to class, but
   in this case, testing the private methods will help give us some reasonable
   confidence in the code even if we can't write a physical disc.  This isn't
   perfect, but it's better than nothing.

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
   build environment.  There is a no need to use a WRITERTESTS_FULL environment
   variable to provide a "reduced feature set" test suite as for some of the
   other test modules.

@author Kenneth J. Pronovici <pronovic@ieee.org>
"""

########################################################################
# Import modules and do runtime validations
########################################################################

import os
import unittest


#######################################################################
# Test Case Classes
#######################################################################

############################
# TestMediaDefinition class
############################

class TestMediaDefinition(unittest.TestCase):

   """Tests for the MediaDefinition class."""

   ################
   # Setup methods
   ################

   def setUp(self):
      pass

   def tearDown(self):
      pass


   ###################
   # Test constructor
   ###################

   def testConstructor_001(self):
      """
      Test the constructor using all default arguments.
      """
      pass


############################
# TestMediaCapacity class
############################

class TestMediaCapacity(unittest.TestCase):

   """Tests for the MediaCapacity class."""

   ################
   # Setup methods
   ################

   def setUp(self):
      pass

   def tearDown(self):
      pass


   ###################
   # Test constructor
   ###################

   def testConstructor_001(self):
      """
      Test the constructor using all default arguments.
      """
      pass


#####################
# TestCdWriter class
#####################

class TestCdWriter(unittest.TestCase):

   """Tests for the CdWriter class."""

   ################
   # Setup methods
   ################

   def setUp(self):
      pass

   def tearDown(self):
      pass


   ###################
   # Test constructor
   ###################

   def testConstructor_001(self):
      """
      Test the constructor using all default arguments.
      """
      pass


#######################################################################
# Suite definition
#######################################################################

def suite():
   """Returns a suite containing all the test cases in this module."""
   return unittest.TestSuite((
                              unittest.makeSuite(TestMediaDefinition, 'test'),
                              unittest.makeSuite(TestMediaCapacity, 'test'),
                              unittest.makeSuite(TestCdWriter, 'test'),
                            ))


########################################################################
# Module entry point
########################################################################

# When this module is executed from the command-line, run its tests
if __name__ == '__main__':
   unittest.main()

