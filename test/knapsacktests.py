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
# Purpose  : Tests knapsack functionality.
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# This file was created with a width of 132 characters, and NO tabs.

########################################################################
# Module documentation
########################################################################

"""
Unit tests for CedarBackup2/knapsack.py.

Code Structure
==============

   Python unittest conventions usually have tests named something like
   testListInsert() or similar.  This makes sense, but with the kind of tests
   I'm doing, I don't want to end up with huge descriptive function names.
   It's klunky.

   Instead, functions will be named according to their test plan item number,
   and each test will be annotated in the method documentation.  This is more
   like the way I write JUnit tests, and I think it should will be just as easy
   to follow.

Debugging these Tests
=====================

   Debugging in here is DAMN complicated.  If you have a test::

      def test():
        try:
           # stuff
        finally:
           # remove files

   you may mysteriously have the 'stuff' fail, and you won't get any exceptions
   reported to you.  The best thing to do if you get strange situations like
   this is to move 'stuff' out of the try block - that will usually clear
   things up.

@author Kenneth J. Pronovici <pronovic@ieee.org>
"""


########################################################################
# Import modules and do runtime validations
########################################################################

# Import standard modules
import sys
import os
import unittest
from CedarBackup2.knapsack import firstFit, bestFit, worstFit, alternateFit


#######################################################################
# Module-wide configuration and constants
#######################################################################

DATA_DIRS = [ './data', './test/data' ]
RESOURCES = [ "tree1.tar.gz", "tree2.tar.gz", "tree3.tar.gz", "tree4.tar.gz", "tree5.tar.gz", "tree6.tar.gz" ]


####################
# Utility functions
####################

def findData():
   """Returns a dictionary of locations for various resources."""
   data = { }
   for resource in RESOURCES:
      for datadir in DATA_DIRS:
         path = os.path.join(datadir, resource);
         if os.path.exists(path):
            data[resource] = path
            break
      else:
         raise Exception("Unable to find resource [%s]." % resource)
   return data


#######################################################################
# Test Case Classes
#######################################################################

#####################
# TestKnapsack class
#####################

class TestKnapsack(unittest.TestCase):

   """Tests for the various knapsack functions."""

   ################
   # Setup methods
   ################

   def setUp(self):
      try:
         self.data = findData()
      except Exception, e:
         self.fail(e)

   def tearDown(self):
      pass


   #####################
   # Tests for whatever
   #####################
         
   def test_1_01(self):
      """
      Test 1.01.
      XXXXX
      """
      pass


   #####################
   # Tests for whatever
   #####################
         
   def test_2_01(self):
      """
      Test 2.01.
      XXXXX
      """
      pass


#######################################################################
# Suite definition
#######################################################################

def suite():
   """Returns a suite containing all the test cases in this module."""
   return unittest.TestSuite((unittest.makeSuite(TestKnapsack, 'test'), ))


########################################################################
# Module entry point
########################################################################

# When this module is executed from the command-line, run its tests
if __name__ == '__main__':
   unittest.main()

