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

Python unittest conventions usually have tests named something like
testListInsert() or similar.  This makes sense, but with the kind of tests I'm
doing, I don't want to end up with huge descriptive function names.  It's
klunky.

Instead, functions will be named according to their test plan item number, and
each test will be annotated in the method documentation.  This is more like the
way I write JUnit tests, and I think it should will be just as easy to follow.

Note that the tests for each function are pretty much identical and so there's
pretty much code duplication.  In production code, I would argue that this
implies some refactoring is needed.  In here, however, I prefer having lots of
individual test cases even if there is duplication, because I think this makes
it easier to judge the extent of a problem when one exists.

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

ITEMS_01  = {  }
ITEMS_02  = { "a" : 0,       "b" : 0,      "c" : 0,      "d" : 0,      "e" : 0,      "f" : 0,      "g" : 0,      "h" : 0,       }
ITEMS_03  = { "a" : 0,       "b" : 1,      "c" : 10,     "d" : 100,    "e" : 1000,   "f" : 10000,  "g" : 100000, "h" : 1000000, }
ITEMS_04  = { "a" : 1000000, "b" : 100000, "c" : 10000,  "d" : 1000,   "e" : 100,    "f" : 10,     "g" : 1,      "h" : 0,       }
ITEMS_05  = { "a" : 1,       "b" : 1,      "c" : 1,      "d" : 1,      "e" : 1,      "f" : 1,      "g" : 1,      "h" : 1,       }
ITEMS_06  = { "a" : 10,      "b" : 10,     "c" : 10,     "d" : 10,     "e" : 10,     "f" : 10,     "g" : 10,     "h" : 10,      }
ITEMS_07  = { "a" : 100,     "b" : 100,    "c" : 100,    "d" : 100,    "e" : 100,    "f" : 100,    "g" : 100,    "h" : 100,     }
ITEMS_08  = { "a" : 1000,    "b" : 1000,   "c" : 1000,   "d" : 1000,   "e" : 1000,   "f" : 1000,   "g" : 1000,   "h" : 1000,    }
ITEMS_09  = { "a" : 10000,   "b" : 10000,  "c" : 10000,  "d" : 10000,  "e" : 10000,  "f" : 10000,  "g" : 10000,  "h" : 10000,   }
ITEMS_10  = { "a" : 100000,  "b" : 100000, "c" : 100000, "d" : 100000, "e" : 100000, "f" : 100000, "g" : 100000, "h" : 100000,  }
ITEMS_11  = { "a" : 1,       "b" : 1,      "c" : 100000, "d" : 100000, "e" : 100000, "f" : 100000, "g" : 1,      "h" : 1,       }
ITEMS_12  = { "a" : 10,      "b" : 10,     "c" : 100000, "d" : 100000, "e" : 100000, "f" : 100000, "g" : 10,     "h" : 10,      }
ITEMS_13  = { "a" : 100,     "b" : 100,    "c" : 100000, "d" : 100000, "e" : 100000, "f" : 100000, "g" : 100,    "h" : 100,     }
ITEMS_14  = { "a" : 1000,    "b" : 1000,   "c" : 100000, "d" : 100000, "e" : 100000, "f" : 100000, "g" : 1000,   "h" : 1000,    }
ITEMS_15  = { "a" : 1,       "b" : 1,      "c" : 1,      "d" : 100000, "e" : 100000, "f" : 1,      "g" : 1,      "h" : 1,       }
ITEMS_16  = { "a" : 10,      "b" : 10,     "c" : 10,     "d" : 100000, "e" : 100000, "f" : 10,     "g" : 10,     "h" : 10,      }
ITEMS_17  = { "a" : 100,     "b" : 100,    "c" : 100,    "d" : 100000, "e" : 100000, "f" : 100,    "g" : 100,    "h" : 100,     }
ITEMS_18  = { "a" : 1000,    "b" : 1000,   "c" : 1000,   "d" : 100000, "e" : 100000, "f" : 1000,   "g" : 1000,   "h" : 1000,    }


####################
# Utility functions
####################

def buildItemDict(origDict):
   """
   Creates an item dictionary suitable for passing to a knapsack function.

   The knapsack functions take a dictionary, keyed on item, of (item, size)
   tuples.  This function converts a simple item/size dictionary to a knapsack
   dictionary.  It exists for convenience.

   @param origDict: Dictionary to convert
   @type origDict: Simple dictionary mapping item to size, like C{ITEMS_02}
 
   @return: Dictionary suitable for passing to a knapsack function.
   """
   itemDict = { }
   for key in origDict.keys():
      itemDict[key] = (key, origDict[key])
   return itemDict


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
      pass

   def tearDown(self):
      pass


   ################################
   # Tests for firstFit() function
   ################################
         
   def test_1_01(self):
      """
      Test 1.01.
      Test firstFit() behavior for an empty items dictionary, zero capacity.
      """
      items = buildItemDict(ITEMS_01)
      capacity = 0
      result = firstFit(items, capacity)
      self.failUnlessEqual(([], 0), result)

   def test_1_02(self):
      """
      Test 1.02.
      Test firstFit() behavior for an empty items dictionary, non-zero capacity.
      """
      items = buildItemDict(ITEMS_01)
      capacity = 10000
      result = firstFit(items, capacity)
      self.failUnlessEqual(([], 0), result)

   def test_1_03(self):
      """
      Test 1.03.
      Test firstFit() behavior for an non-empty items dictionary, zero capacity.
      """
      items = buildItemDict(ITEMS_03)
      capacity = 0
      result = firstFit(items, capacity)
      self.failUnlessEqual(([], 0), result)

      items = buildItemDict(ITEMS_04)
      capacity = 0
      result = firstFit(items, capacity)
      self.failUnlessEqual(([], 0), result)

      items = buildItemDict(ITEMS_13)
      capacity = 0
      result = firstFit(items, capacity)
      self.failUnlessEqual(([], 0), result)

   def test_1_04(self):
      """
      Test 1.04.
      Test firstFit() behavior for non-empty items dictionary with zero-sized items, zero capacity.
      """
      items = buildItemDict(ITEMS_03)
      capacity = 0
      result = firstFit(items, capacity)
      self.failUnlessEqual(([], 0), result)

   def test_1_05(self):
      """
      Test 1.05.
      Test firstFit() behavior for items dictionary where only one item fits.
      """
      items = buildItemDict(ITEMS_05)
      capacity = 1
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(1, len(result[0]))
      self.failUnlessEqual(1, result[1])

      items = buildItemDict(ITEMS_06)
      capacity = 10
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(1, len(result[0]))
      self.failUnlessEqual(10, result[1])

      items = buildItemDict(ITEMS_07)
      capacity = 100
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(1, len(result[0]))
      self.failUnlessEqual(100, result[1])

      items = buildItemDict(ITEMS_08)
      capacity = 1000
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(1, len(result[0]))
      self.failUnlessEqual(1000, result[1])

      items = buildItemDict(ITEMS_09)
      capacity = 10000
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(1, len(result[0]))
      self.failUnlessEqual(10000, result[1])

      items = buildItemDict(ITEMS_10)
      capacity = 100000
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(1, len(result[0]))
      self.failUnlessEqual(100000, result[1])

   def test_1_06(self):
      """
      Test 1.06.
      Test firstFit() behavior for items dictionary where only 25% of items fit.
      """
      items = buildItemDict(ITEMS_05)
      capacity = 2
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(2, len(result[0]))
      self.failUnlessEqual(2, result[1])

      items = buildItemDict(ITEMS_06)
      capacity = 25
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(2, len(result[0]))
      self.failUnlessEqual(20, result[1])

      items = buildItemDict(ITEMS_07)
      capacity = 250
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(2, len(result[0]))
      self.failUnlessEqual(200, result[1])

      items = buildItemDict(ITEMS_08)
      capacity = 2500
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(2, len(result[0]))
      self.failUnlessEqual(2000, result[1])

      items = buildItemDict(ITEMS_09)
      capacity = 25000
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(2, len(result[0]))
      self.failUnlessEqual(20000, result[1])

      items = buildItemDict(ITEMS_10)
      capacity = 250000
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(2, len(result[0]))
      self.failUnlessEqual(200000, result[1])

      items = buildItemDict(ITEMS_11)
      capacity = 2
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(2, len(result[0]))
      self.failUnlessEqual(2, result[1])

      items = buildItemDict(ITEMS_12)
      capacity = 25
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(2, len(result[0]))
      self.failUnlessEqual(20, result[1])

      items = buildItemDict(ITEMS_13)
      capacity = 250
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(2, len(result[0]))
      self.failUnlessEqual(200, result[1])

      items = buildItemDict(ITEMS_14)
      capacity = 2500
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(2, len(result[0]))
      self.failUnlessEqual(2000, result[1])

   def test_1_07(self):
      """
      Test 1.07.
      Test firstFit() behavior for items dictionary where only 50% of items fit.
      """
      items = buildItemDict(ITEMS_05)
      capacity = 4
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(4, result[1])

      items = buildItemDict(ITEMS_06)
      capacity = 45
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(40, result[1])

      items = buildItemDict(ITEMS_07)
      capacity = 450
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(400, result[1])

      items = buildItemDict(ITEMS_08)
      capacity = 4500
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(4000, result[1])

      items = buildItemDict(ITEMS_09)
      capacity = 45000
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(40000, result[1])

      items = buildItemDict(ITEMS_10)
      capacity = 450000
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(400000, result[1])

      items = buildItemDict(ITEMS_11)
      capacity = 4
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(4, result[1])

      items = buildItemDict(ITEMS_12)
      capacity = 45
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(40, result[1])

      items = buildItemDict(ITEMS_13)
      capacity = 450
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(400, result[1])

      items = buildItemDict(ITEMS_14)
      capacity = 4500
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(4000, result[1])

   def test_1_08(self):
      """
      Test 1.08.
      Test firstFit() behavior for items dictionary where only 75% of items fit.
      """
      items = buildItemDict(ITEMS_05)
      capacity = 6
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(6, len(result[0]))
      self.failUnlessEqual(6, result[1])

      items = buildItemDict(ITEMS_06)
      capacity = 65
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(6, len(result[0]))
      self.failUnlessEqual(60, result[1])

      items = buildItemDict(ITEMS_07)
      capacity = 650
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(6, len(result[0]))
      self.failUnlessEqual(600, result[1])

      items = buildItemDict(ITEMS_08)
      capacity = 6500
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(6, len(result[0]))
      self.failUnlessEqual(6000, result[1])

      items = buildItemDict(ITEMS_09)
      capacity = 65000
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(6, len(result[0]))
      self.failUnlessEqual(60000, result[1])

      items = buildItemDict(ITEMS_10)
      capacity = 650000
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(6, len(result[0]))
      self.failUnlessEqual(600000, result[1])

      items = buildItemDict(ITEMS_15)
      capacity = 7
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(6, len(result[0]))
      self.failUnlessEqual(6, result[1])

      items = buildItemDict(ITEMS_16)
      capacity = 65
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(6, len(result[0]))
      self.failUnlessEqual(60, result[1])

      items = buildItemDict(ITEMS_17)
      capacity = 650
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(6, len(result[0]))
      self.failUnlessEqual(600, result[1])

      items = buildItemDict(ITEMS_18)
      capacity = 6500
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(6, len(result[0]))
      self.failUnlessEqual(6000, result[1])

   def test_1_09(self):
      """
      Test 1.09.
      Test firstFit() behavior for items dictionary where all items individually
      exceed the capacity.
      """
      items = buildItemDict(ITEMS_06)
      capacity = 9
      result = firstFit(items, capacity)
      self.failUnlessEqual(([], 0), result)

      items = buildItemDict(ITEMS_07)
      capacity = 99
      result = firstFit(items, capacity)
      self.failUnlessEqual(([], 0), result)

      items = buildItemDict(ITEMS_08)
      capacity = 999
      result = firstFit(items, capacity)
      self.failUnlessEqual(([], 0), result)

      items = buildItemDict(ITEMS_09)
      capacity = 9999
      result = firstFit(items, capacity)
      self.failUnlessEqual(([], 0), result)

      items = buildItemDict(ITEMS_10)
      capacity = 99999
      result = firstFit(items, capacity)
      self.failUnlessEqual(([], 0), result)

   def test_1_10(self):
      """
      Test 1.10.
      Test firstFit() behavior for items dictionary where first half of items
      individually exceed capacity and remainder fit.
      """
      items = buildItemDict(ITEMS_04)
      capacity = 200
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(111, result[1])

   def test_1_11(self):
      """
      Test 1.11.
      Test firstFit() behavior for items dictionary where middle half of items
      individually exceed capacity and remainder fit.
      """
      items = buildItemDict(ITEMS_11)
      capacity = 5
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(4, result[1])

      items = buildItemDict(ITEMS_12)
      capacity = 50
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(40, result[1])

      items = buildItemDict(ITEMS_13)
      capacity = 500
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(400, result[1])

      items = buildItemDict(ITEMS_14)
      capacity = 5000
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(4000, result[1])

   def test_1_12(self):
      """
      Test 1.12.
      Test firstFit() behavior for items dictionary where second half of items
      individually exceed capacity and remainder fit.
      """
      items = buildItemDict(ITEMS_03)
      capacity = 200
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(111, result[1])

   def test_1_13(self):
      """
      Test 1.10.
      Test firstFit() behavior for items dictionary where first half of items
      individually exceed capacity and only some of remainder fit.
      """
      items = buildItemDict(ITEMS_04)
      capacity = 50
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnless(len(result[0]) < 4, "%s < 4" % len(result[0]))

   def test_1_14(self):
      """
      Test 1.11.
      Test firstFit() behavior for items dictionary where middle half of items
      individually exceed capacity and only some of remainder fit.
      """
      items = buildItemDict(ITEMS_11)
      capacity = 3
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnless(len(result[0]) < 4, "%s < 4" % len(result[0]))

      items = buildItemDict(ITEMS_12)
      capacity = 35
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnless(len(result[0]) < 4, "%s < 4" % len(result[0]))

      items = buildItemDict(ITEMS_13)
      capacity = 350
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnless(len(result[0]) < 4, "%s < 4" % len(result[0]))

      items = buildItemDict(ITEMS_14)
      capacity = 3500
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnless(len(result[0]) < 4, "%s < 4" % len(result[0]))

   def test_1_15(self):
      """
      Test 1.12.
      Test firstFit() behavior for items dictionary where second half of items
      individually exceed capacity and only some of remainder fit.
      """
      items = buildItemDict(ITEMS_03)
      capacity = 50
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnless(len(result[0]) < 4, "%s < 4" % len(result[0]))

   def test_1_16(self):
      """
      Test 1.16.
      Test firstFit() behavior for items dictionary where all items fit.
      """
      items = buildItemDict(ITEMS_02)
      capacity = 1000000
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(0, result[1])

      items = buildItemDict(ITEMS_03)
      capacity = 2000000
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(1111111, result[1])

      items = buildItemDict(ITEMS_04)
      capacity = 2000000
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(1111111, result[1])

      items = buildItemDict(ITEMS_05)
      capacity = 1000000
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(8, result[1])

      items = buildItemDict(ITEMS_06)
      capacity = 1000000
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(80, result[1])

      items = buildItemDict(ITEMS_07)
      capacity = 1000000
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(800, result[1])

      items = buildItemDict(ITEMS_08)
      capacity = 1000000
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(8000, result[1])

      items = buildItemDict(ITEMS_09)
      capacity = 1000000
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(80000, result[1])

      items = buildItemDict(ITEMS_10)
      capacity = 1000000
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(800000, result[1])

      items = buildItemDict(ITEMS_11)
      capacity = 1000000
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(400004, result[1])

      items = buildItemDict(ITEMS_12)
      capacity = 1000000
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(400040, result[1])

      items = buildItemDict(ITEMS_13)
      capacity = 1000000
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(400400, result[1])

      items = buildItemDict(ITEMS_14)
      capacity = 1000000
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(404000, result[1])

      items = buildItemDict(ITEMS_15)
      capacity = 1000000
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(200006, result[1])

      items = buildItemDict(ITEMS_16)
      capacity = 1000000
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(200060, result[1])

      items = buildItemDict(ITEMS_17)
      capacity = 1000000
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(200600, result[1])

      items = buildItemDict(ITEMS_18)
      capacity = 1000000
      result = firstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(206000, result[1])


   ###############################
   # Tests for bestFit() function
   ###############################

   def test_2_01(self):
      """
      Test 1.01.
      Test bestFit() behavior for an empty items dictionary, zero capacity.
      """
      items = buildItemDict(ITEMS_01)
      capacity = 0
      result = bestFit(items, capacity)
      self.failUnlessEqual(([], 0), result)

   def test_2_02(self):
      """
      Test 1.02.
      Test bestFit() behavior for an empty items dictionary, non-zero capacity.
      """
      items = buildItemDict(ITEMS_01)
      capacity = 10000
      result = bestFit(items, capacity)
      self.failUnlessEqual(([], 0), result)

   def test_2_03(self):
      """
      Test 1.03.
      Test bestFit() behavior for an non-empty items dictionary, zero capacity.
      """
      items = buildItemDict(ITEMS_03)
      capacity = 0
      result = bestFit(items, capacity)
      self.failUnlessEqual(([], 0), result)

      items = buildItemDict(ITEMS_04)
      capacity = 0
      result = bestFit(items, capacity)
      self.failUnlessEqual(([], 0), result)

      items = buildItemDict(ITEMS_13)
      capacity = 0
      result = bestFit(items, capacity)
      self.failUnlessEqual(([], 0), result)

   def test_2_04(self):
      """
      Test 1.04.
      Test bestFit() behavior for non-empty items dictionary with zero-sized items, zero capacity.
      """
      items = buildItemDict(ITEMS_03)
      capacity = 0
      result = bestFit(items, capacity)
      self.failUnlessEqual(([], 0), result)

   def test_2_05(self):
      """
      Test 1.05.
      Test bestFit() behavior for items dictionary where only one item fits.
      """
      items = buildItemDict(ITEMS_05)
      capacity = 1
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(1, len(result[0]))
      self.failUnlessEqual(1, result[1])

      items = buildItemDict(ITEMS_06)
      capacity = 10
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(1, len(result[0]))
      self.failUnlessEqual(10, result[1])

      items = buildItemDict(ITEMS_07)
      capacity = 100
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(1, len(result[0]))
      self.failUnlessEqual(100, result[1])

      items = buildItemDict(ITEMS_08)
      capacity = 1000
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(1, len(result[0]))
      self.failUnlessEqual(1000, result[1])

      items = buildItemDict(ITEMS_09)
      capacity = 10000
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(1, len(result[0]))
      self.failUnlessEqual(10000, result[1])

      items = buildItemDict(ITEMS_10)
      capacity = 100000
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(1, len(result[0]))
      self.failUnlessEqual(100000, result[1])

   def test_2_06(self):
      """
      Test 1.06.
      Test bestFit() behavior for items dictionary where only 25% of items fit.
      """
      items = buildItemDict(ITEMS_05)
      capacity = 2
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(2, len(result[0]))
      self.failUnlessEqual(2, result[1])

      items = buildItemDict(ITEMS_06)
      capacity = 25
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(2, len(result[0]))
      self.failUnlessEqual(20, result[1])

      items = buildItemDict(ITEMS_07)
      capacity = 250
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(2, len(result[0]))
      self.failUnlessEqual(200, result[1])

      items = buildItemDict(ITEMS_08)
      capacity = 2500
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(2, len(result[0]))
      self.failUnlessEqual(2000, result[1])

      items = buildItemDict(ITEMS_09)
      capacity = 25000
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(2, len(result[0]))
      self.failUnlessEqual(20000, result[1])

      items = buildItemDict(ITEMS_10)
      capacity = 250000
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(2, len(result[0]))
      self.failUnlessEqual(200000, result[1])

      items = buildItemDict(ITEMS_11)
      capacity = 2
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(2, len(result[0]))
      self.failUnlessEqual(2, result[1])

      items = buildItemDict(ITEMS_12)
      capacity = 25
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(2, len(result[0]))
      self.failUnlessEqual(20, result[1])

      items = buildItemDict(ITEMS_13)
      capacity = 250
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(2, len(result[0]))
      self.failUnlessEqual(200, result[1])

      items = buildItemDict(ITEMS_14)
      capacity = 2500
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(2, len(result[0]))
      self.failUnlessEqual(2000, result[1])

   def test_2_07(self):
      """
      Test 1.07.
      Test bestFit() behavior for items dictionary where only 50% of items fit.
      """
      items = buildItemDict(ITEMS_05)
      capacity = 4
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(4, result[1])

      items = buildItemDict(ITEMS_06)
      capacity = 45
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(40, result[1])

      items = buildItemDict(ITEMS_07)
      capacity = 450
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(400, result[1])

      items = buildItemDict(ITEMS_08)
      capacity = 4500
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(4000, result[1])

      items = buildItemDict(ITEMS_09)
      capacity = 45000
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(40000, result[1])

      items = buildItemDict(ITEMS_10)
      capacity = 450000
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(400000, result[1])

      items = buildItemDict(ITEMS_11)
      capacity = 4
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(4, result[1])

      items = buildItemDict(ITEMS_12)
      capacity = 45
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(40, result[1])

      items = buildItemDict(ITEMS_13)
      capacity = 450
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(400, result[1])

      items = buildItemDict(ITEMS_14)
      capacity = 4500
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(4000, result[1])

   def test_2_08(self):
      """
      Test 1.08.
      Test bestFit() behavior for items dictionary where only 75% of items fit.
      """
      items = buildItemDict(ITEMS_05)
      capacity = 6
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(6, len(result[0]))
      self.failUnlessEqual(6, result[1])

      items = buildItemDict(ITEMS_06)
      capacity = 65
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(6, len(result[0]))
      self.failUnlessEqual(60, result[1])

      items = buildItemDict(ITEMS_07)
      capacity = 650
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(6, len(result[0]))
      self.failUnlessEqual(600, result[1])

      items = buildItemDict(ITEMS_08)
      capacity = 6500
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(6, len(result[0]))
      self.failUnlessEqual(6000, result[1])

      items = buildItemDict(ITEMS_09)
      capacity = 65000
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(6, len(result[0]))
      self.failUnlessEqual(60000, result[1])

      items = buildItemDict(ITEMS_10)
      capacity = 650000
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(6, len(result[0]))
      self.failUnlessEqual(600000, result[1])

      items = buildItemDict(ITEMS_15)
      capacity = 7
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(6, len(result[0]))
      self.failUnlessEqual(6, result[1])

      items = buildItemDict(ITEMS_16)
      capacity = 65
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(6, len(result[0]))
      self.failUnlessEqual(60, result[1])

      items = buildItemDict(ITEMS_17)
      capacity = 650
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(6, len(result[0]))
      self.failUnlessEqual(600, result[1])

      items = buildItemDict(ITEMS_18)
      capacity = 6500
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(6, len(result[0]))
      self.failUnlessEqual(6000, result[1])

   def test_2_09(self):
      """
      Test 1.09.
      Test bestFit() behavior for items dictionary where all items individually
      exceed the capacity.
      """
      items = buildItemDict(ITEMS_06)
      capacity = 9
      result = bestFit(items, capacity)
      self.failUnlessEqual(([], 0), result)

      items = buildItemDict(ITEMS_07)
      capacity = 99
      result = bestFit(items, capacity)
      self.failUnlessEqual(([], 0), result)

      items = buildItemDict(ITEMS_08)
      capacity = 999
      result = bestFit(items, capacity)
      self.failUnlessEqual(([], 0), result)

      items = buildItemDict(ITEMS_09)
      capacity = 9999
      result = bestFit(items, capacity)
      self.failUnlessEqual(([], 0), result)

      items = buildItemDict(ITEMS_10)
      capacity = 99999
      result = bestFit(items, capacity)
      self.failUnlessEqual(([], 0), result)

   def test_2_10(self):
      """
      Test 1.10.
      Test bestFit() behavior for items dictionary where first half of items
      individually exceed capacity and remainder fit.
      """
      items = buildItemDict(ITEMS_04)
      capacity = 200
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(111, result[1])

   def test_2_11(self):
      """
      Test 1.11.
      Test bestFit() behavior for items dictionary where middle half of items
      individually exceed capacity and remainder fit.
      """
      items = buildItemDict(ITEMS_11)
      capacity = 5
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(4, result[1])

      items = buildItemDict(ITEMS_12)
      capacity = 50
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(40, result[1])

      items = buildItemDict(ITEMS_13)
      capacity = 500
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(400, result[1])

      items = buildItemDict(ITEMS_14)
      capacity = 5000
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(4000, result[1])

   def test_2_12(self):
      """
      Test 1.12.
      Test bestFit() behavior for items dictionary where second half of items
      individually exceed capacity and remainder fit.
      """
      items = buildItemDict(ITEMS_03)
      capacity = 200
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(111, result[1])

   def test_2_13(self):
      """
      Test 1.10.
      Test bestFit() behavior for items dictionary where first half of items
      individually exceed capacity and only some of remainder fit.
      """
      items = buildItemDict(ITEMS_04)
      capacity = 50
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnless(len(result[0]) < 4, "%s < 4" % len(result[0]))

   def test_2_14(self):
      """
      Test 1.11.
      Test bestFit() behavior for items dictionary where middle half of items
      individually exceed capacity and only some of remainder fit.
      """
      items = buildItemDict(ITEMS_11)
      capacity = 3
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnless(len(result[0]) < 4, "%s < 4" % len(result[0]))

      items = buildItemDict(ITEMS_12)
      capacity = 35
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnless(len(result[0]) < 4, "%s < 4" % len(result[0]))

      items = buildItemDict(ITEMS_13)
      capacity = 350
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnless(len(result[0]) < 4, "%s < 4" % len(result[0]))

      items = buildItemDict(ITEMS_14)
      capacity = 3500
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnless(len(result[0]) < 4, "%s < 4" % len(result[0]))

   def test_2_15(self):
      """
      Test 1.12.
      Test bestFit() behavior for items dictionary where second half of items
      individually exceed capacity and only some of remainder fit.
      """
      items = buildItemDict(ITEMS_03)
      capacity = 50
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnless(len(result[0]) < 4, "%s < 4" % len(result[0]))

   def test_2_16(self):
      """
      Test 1.16.
      Test bestFit() behavior for items dictionary where all items fit.
      """
      items = buildItemDict(ITEMS_02)
      capacity = 1000000
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(0, result[1])

      items = buildItemDict(ITEMS_03)
      capacity = 2000000
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(1111111, result[1])

      items = buildItemDict(ITEMS_04)
      capacity = 2000000
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(1111111, result[1])

      items = buildItemDict(ITEMS_05)
      capacity = 1000000
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(8, result[1])

      items = buildItemDict(ITEMS_06)
      capacity = 1000000
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(80, result[1])

      items = buildItemDict(ITEMS_07)
      capacity = 1000000
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(800, result[1])

      items = buildItemDict(ITEMS_08)
      capacity = 1000000
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(8000, result[1])

      items = buildItemDict(ITEMS_09)
      capacity = 1000000
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(80000, result[1])

      items = buildItemDict(ITEMS_10)
      capacity = 1000000
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(800000, result[1])

      items = buildItemDict(ITEMS_11)
      capacity = 1000000
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(400004, result[1])

      items = buildItemDict(ITEMS_12)
      capacity = 1000000
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(400040, result[1])

      items = buildItemDict(ITEMS_13)
      capacity = 1000000
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(400400, result[1])

      items = buildItemDict(ITEMS_14)
      capacity = 1000000
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(404000, result[1])

      items = buildItemDict(ITEMS_15)
      capacity = 1000000
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(200006, result[1])

      items = buildItemDict(ITEMS_16)
      capacity = 1000000
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(200060, result[1])

      items = buildItemDict(ITEMS_17)
      capacity = 1000000
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(200600, result[1])

      items = buildItemDict(ITEMS_18)
      capacity = 1000000
      result = bestFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(206000, result[1])


   ################################
   # Tests for worstFit() function
   ################################

   def test_3_01(self):
      """
      Test 1.01.
      Test worstFit() behavior for an empty items dictionary, zero capacity.
      """
      items = buildItemDict(ITEMS_01)
      capacity = 0
      result = worstFit(items, capacity)
      self.failUnlessEqual(([], 0), result)

   def test_3_02(self):
      """
      Test 1.02.
      Test worstFit() behavior for an empty items dictionary, non-zero capacity.
      """
      items = buildItemDict(ITEMS_01)
      capacity = 10000
      result = worstFit(items, capacity)
      self.failUnlessEqual(([], 0), result)

   def test_3_03(self):
      """
      Test 1.03.
      Test worstFit() behavior for an non-empty items dictionary, zero capacity.
      """
      items = buildItemDict(ITEMS_03)
      capacity = 0
      result = worstFit(items, capacity)
      self.failUnlessEqual(([], 0), result)

      items = buildItemDict(ITEMS_04)
      capacity = 0
      result = worstFit(items, capacity)
      self.failUnlessEqual(([], 0), result)

      items = buildItemDict(ITEMS_13)
      capacity = 0
      result = worstFit(items, capacity)
      self.failUnlessEqual(([], 0), result)

   def test_3_04(self):
      """
      Test 1.04.
      Test worstFit() behavior for non-empty items dictionary with zero-sized items, zero capacity.
      """
      items = buildItemDict(ITEMS_03)
      capacity = 0
      result = worstFit(items, capacity)
      self.failUnlessEqual(([], 0), result)

   def test_3_05(self):
      """
      Test 1.05.
      Test worstFit() behavior for items dictionary where only one item fits.
      """
      items = buildItemDict(ITEMS_05)
      capacity = 1
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(1, len(result[0]))
      self.failUnlessEqual(1, result[1])

      items = buildItemDict(ITEMS_06)
      capacity = 10
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(1, len(result[0]))
      self.failUnlessEqual(10, result[1])

      items = buildItemDict(ITEMS_07)
      capacity = 100
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(1, len(result[0]))
      self.failUnlessEqual(100, result[1])

      items = buildItemDict(ITEMS_08)
      capacity = 1000
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(1, len(result[0]))
      self.failUnlessEqual(1000, result[1])

      items = buildItemDict(ITEMS_09)
      capacity = 10000
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(1, len(result[0]))
      self.failUnlessEqual(10000, result[1])

      items = buildItemDict(ITEMS_10)
      capacity = 100000
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(1, len(result[0]))
      self.failUnlessEqual(100000, result[1])

   def test_3_06(self):
      """
      Test 1.06.
      Test worstFit() behavior for items dictionary where only 25% of items fit.
      """
      items = buildItemDict(ITEMS_05)
      capacity = 2
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(2, len(result[0]))
      self.failUnlessEqual(2, result[1])

      items = buildItemDict(ITEMS_06)
      capacity = 25
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(2, len(result[0]))
      self.failUnlessEqual(20, result[1])

      items = buildItemDict(ITEMS_07)
      capacity = 250
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(2, len(result[0]))
      self.failUnlessEqual(200, result[1])

      items = buildItemDict(ITEMS_08)
      capacity = 2500
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(2, len(result[0]))
      self.failUnlessEqual(2000, result[1])

      items = buildItemDict(ITEMS_09)
      capacity = 25000
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(2, len(result[0]))
      self.failUnlessEqual(20000, result[1])

      items = buildItemDict(ITEMS_10)
      capacity = 250000
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(2, len(result[0]))
      self.failUnlessEqual(200000, result[1])

      items = buildItemDict(ITEMS_11)
      capacity = 2
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(2, len(result[0]))
      self.failUnlessEqual(2, result[1])

      items = buildItemDict(ITEMS_12)
      capacity = 25
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(2, len(result[0]))
      self.failUnlessEqual(20, result[1])

      items = buildItemDict(ITEMS_13)
      capacity = 250
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(2, len(result[0]))
      self.failUnlessEqual(200, result[1])

      items = buildItemDict(ITEMS_14)
      capacity = 2500
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(2, len(result[0]))
      self.failUnlessEqual(2000, result[1])

   def test_3_07(self):
      """
      Test 1.07.
      Test worstFit() behavior for items dictionary where only 50% of items fit.
      """
      items = buildItemDict(ITEMS_05)
      capacity = 4
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(4, result[1])

      items = buildItemDict(ITEMS_06)
      capacity = 45
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(40, result[1])

      items = buildItemDict(ITEMS_07)
      capacity = 450
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(400, result[1])

      items = buildItemDict(ITEMS_08)
      capacity = 4500
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(4000, result[1])

      items = buildItemDict(ITEMS_09)
      capacity = 45000
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(40000, result[1])

      items = buildItemDict(ITEMS_10)
      capacity = 450000
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(400000, result[1])

      items = buildItemDict(ITEMS_11)
      capacity = 4
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(4, result[1])

      items = buildItemDict(ITEMS_12)
      capacity = 45
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(40, result[1])

      items = buildItemDict(ITEMS_13)
      capacity = 450
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(400, result[1])

      items = buildItemDict(ITEMS_14)
      capacity = 4500
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(4000, result[1])

   def test_3_08(self):
      """
      Test 1.08.
      Test worstFit() behavior for items dictionary where only 75% of items fit.
      """
      items = buildItemDict(ITEMS_05)
      capacity = 6
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(6, len(result[0]))
      self.failUnlessEqual(6, result[1])

      items = buildItemDict(ITEMS_06)
      capacity = 65
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(6, len(result[0]))
      self.failUnlessEqual(60, result[1])

      items = buildItemDict(ITEMS_07)
      capacity = 650
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(6, len(result[0]))
      self.failUnlessEqual(600, result[1])

      items = buildItemDict(ITEMS_08)
      capacity = 6500
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(6, len(result[0]))
      self.failUnlessEqual(6000, result[1])

      items = buildItemDict(ITEMS_09)
      capacity = 65000
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(6, len(result[0]))
      self.failUnlessEqual(60000, result[1])

      items = buildItemDict(ITEMS_10)
      capacity = 650000
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(6, len(result[0]))
      self.failUnlessEqual(600000, result[1])

      items = buildItemDict(ITEMS_15)
      capacity = 7
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(6, len(result[0]))
      self.failUnlessEqual(6, result[1])

      items = buildItemDict(ITEMS_16)
      capacity = 65
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(6, len(result[0]))
      self.failUnlessEqual(60, result[1])

      items = buildItemDict(ITEMS_17)
      capacity = 650
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(6, len(result[0]))
      self.failUnlessEqual(600, result[1])

      items = buildItemDict(ITEMS_18)
      capacity = 6500
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(6, len(result[0]))
      self.failUnlessEqual(6000, result[1])

   def test_3_09(self):
      """
      Test 1.09.
      Test worstFit() behavior for items dictionary where all items individually
      exceed the capacity.
      """
      items = buildItemDict(ITEMS_06)
      capacity = 9
      result = worstFit(items, capacity)
      self.failUnlessEqual(([], 0), result)

      items = buildItemDict(ITEMS_07)
      capacity = 99
      result = worstFit(items, capacity)
      self.failUnlessEqual(([], 0), result)

      items = buildItemDict(ITEMS_08)
      capacity = 999
      result = worstFit(items, capacity)
      self.failUnlessEqual(([], 0), result)

      items = buildItemDict(ITEMS_09)
      capacity = 9999
      result = worstFit(items, capacity)
      self.failUnlessEqual(([], 0), result)

      items = buildItemDict(ITEMS_10)
      capacity = 99999
      result = worstFit(items, capacity)
      self.failUnlessEqual(([], 0), result)

   def test_3_10(self):
      """
      Test 1.10.
      Test worstFit() behavior for items dictionary where first half of items
      individually exceed capacity and remainder fit.
      """
      items = buildItemDict(ITEMS_04)
      capacity = 200
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(111, result[1])

   def test_3_11(self):
      """
      Test 1.11.
      Test worstFit() behavior for items dictionary where middle half of items
      individually exceed capacity and remainder fit.
      """
      items = buildItemDict(ITEMS_11)
      capacity = 5
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(4, result[1])

      items = buildItemDict(ITEMS_12)
      capacity = 50
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(40, result[1])

      items = buildItemDict(ITEMS_13)
      capacity = 500
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(400, result[1])

      items = buildItemDict(ITEMS_14)
      capacity = 5000
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(4000, result[1])

   def test_3_12(self):
      """
      Test 1.12.
      Test worstFit() behavior for items dictionary where second half of items
      individually exceed capacity and remainder fit.
      """
      items = buildItemDict(ITEMS_03)
      capacity = 200
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(111, result[1])

   def test_3_13(self):
      """
      Test 1.10.
      Test worstFit() behavior for items dictionary where first half of items
      individually exceed capacity and only some of remainder fit.
      """
      items = buildItemDict(ITEMS_04)
      capacity = 50
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnless(len(result[0]) < 4, "%s < 4" % len(result[0]))

   def test_3_14(self):
      """
      Test 1.11.
      Test worstFit() behavior for items dictionary where middle half of items
      individually exceed capacity and only some of remainder fit.
      """
      items = buildItemDict(ITEMS_11)
      capacity = 3
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnless(len(result[0]) < 4, "%s < 4" % len(result[0]))

      items = buildItemDict(ITEMS_12)
      capacity = 35
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnless(len(result[0]) < 4, "%s < 4" % len(result[0]))

      items = buildItemDict(ITEMS_13)
      capacity = 350
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnless(len(result[0]) < 4, "%s < 4" % len(result[0]))

      items = buildItemDict(ITEMS_14)
      capacity = 3500
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnless(len(result[0]) < 4, "%s < 4" % len(result[0]))

   def test_3_15(self):
      """
      Test 1.12.
      Test worstFit() behavior for items dictionary where second half of items
      individually exceed capacity and only some of remainder fit.
      """
      items = buildItemDict(ITEMS_03)
      capacity = 50
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnless(len(result[0]) < 4, "%s < 4" % len(result[0]))

   def test_3_16(self):
      """
      Test 1.16.
      Test worstFit() behavior for items dictionary where all items fit.
      """
      items = buildItemDict(ITEMS_02)
      capacity = 1000000
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(0, result[1])

      items = buildItemDict(ITEMS_03)
      capacity = 2000000
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(1111111, result[1])

      items = buildItemDict(ITEMS_04)
      capacity = 2000000
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(1111111, result[1])

      items = buildItemDict(ITEMS_05)
      capacity = 1000000
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(8, result[1])

      items = buildItemDict(ITEMS_06)
      capacity = 1000000
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(80, result[1])

      items = buildItemDict(ITEMS_07)
      capacity = 1000000
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(800, result[1])

      items = buildItemDict(ITEMS_08)
      capacity = 1000000
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(8000, result[1])

      items = buildItemDict(ITEMS_09)
      capacity = 1000000
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(80000, result[1])

      items = buildItemDict(ITEMS_10)
      capacity = 1000000
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(800000, result[1])

      items = buildItemDict(ITEMS_11)
      capacity = 1000000
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(400004, result[1])

      items = buildItemDict(ITEMS_12)
      capacity = 1000000
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(400040, result[1])

      items = buildItemDict(ITEMS_13)
      capacity = 1000000
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(400400, result[1])

      items = buildItemDict(ITEMS_14)
      capacity = 1000000
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(404000, result[1])

      items = buildItemDict(ITEMS_15)
      capacity = 1000000
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(200006, result[1])

      items = buildItemDict(ITEMS_16)
      capacity = 1000000
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(200060, result[1])

      items = buildItemDict(ITEMS_17)
      capacity = 1000000
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(200600, result[1])

      items = buildItemDict(ITEMS_18)
      capacity = 1000000
      result = worstFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(206000, result[1])


   ####################################
   # Tests for alternateFit() function
   ####################################

   def test_4_01(self):
      """
      Test 1.01.
      Test alternateFit() behavior for an empty items dictionary, zero capacity.
      """
      items = buildItemDict(ITEMS_01)
      capacity = 0
      result = alternateFit(items, capacity)
      self.failUnlessEqual(([], 0), result)

   def test_4_02(self):
      """
      Test 1.02.
      Test alternateFit() behavior for an empty items dictionary, non-zero capacity.
      """
      items = buildItemDict(ITEMS_01)
      capacity = 10000
      result = alternateFit(items, capacity)
      self.failUnlessEqual(([], 0), result)

   def test_4_03(self):
      """
      Test 1.03.
      Test alternateFit() behavior for an non-empty items dictionary, zero capacity.
      """
      items = buildItemDict(ITEMS_03)
      capacity = 0
      result = alternateFit(items, capacity)
      self.failUnlessEqual(([], 0), result)

      items = buildItemDict(ITEMS_04)
      capacity = 0
      result = alternateFit(items, capacity)
      self.failUnlessEqual(([], 0), result)

      items = buildItemDict(ITEMS_13)
      capacity = 0
      result = alternateFit(items, capacity)
      self.failUnlessEqual(([], 0), result)

   def test_4_04(self):
      """
      Test 1.04.
      Test alternateFit() behavior for non-empty items dictionary with zero-sized items, zero capacity.
      """
      items = buildItemDict(ITEMS_03)
      capacity = 0
      result = alternateFit(items, capacity)
      self.failUnlessEqual(([], 0), result)

   def test_4_05(self):
      """
      Test 1.05.
      Test alternateFit() behavior for items dictionary where only one item fits.
      """
      items = buildItemDict(ITEMS_05)
      capacity = 1
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(1, len(result[0]))
      self.failUnlessEqual(1, result[1])

      items = buildItemDict(ITEMS_06)
      capacity = 10
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(1, len(result[0]))
      self.failUnlessEqual(10, result[1])

      items = buildItemDict(ITEMS_07)
      capacity = 100
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(1, len(result[0]))
      self.failUnlessEqual(100, result[1])

      items = buildItemDict(ITEMS_08)
      capacity = 1000
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(1, len(result[0]))
      self.failUnlessEqual(1000, result[1])

      items = buildItemDict(ITEMS_09)
      capacity = 10000
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(1, len(result[0]))
      self.failUnlessEqual(10000, result[1])

      items = buildItemDict(ITEMS_10)
      capacity = 100000
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(1, len(result[0]))
      self.failUnlessEqual(100000, result[1])

   def test_4_06(self):
      """
      Test 1.06.
      Test alternateFit() behavior for items dictionary where only 25% of items fit.
      """
      items = buildItemDict(ITEMS_05)
      capacity = 2
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(2, len(result[0]))
      self.failUnlessEqual(2, result[1])

      items = buildItemDict(ITEMS_06)
      capacity = 25
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(2, len(result[0]))
      self.failUnlessEqual(20, result[1])

      items = buildItemDict(ITEMS_07)
      capacity = 250
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(2, len(result[0]))
      self.failUnlessEqual(200, result[1])

      items = buildItemDict(ITEMS_08)
      capacity = 2500
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(2, len(result[0]))
      self.failUnlessEqual(2000, result[1])

      items = buildItemDict(ITEMS_09)
      capacity = 25000
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(2, len(result[0]))
      self.failUnlessEqual(20000, result[1])

      items = buildItemDict(ITEMS_10)
      capacity = 250000
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(2, len(result[0]))
      self.failUnlessEqual(200000, result[1])

      items = buildItemDict(ITEMS_11)
      capacity = 2
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(2, len(result[0]))
      self.failUnlessEqual(2, result[1])

      items = buildItemDict(ITEMS_12)
      capacity = 25
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(2, len(result[0]))
      self.failUnlessEqual(20, result[1])

      items = buildItemDict(ITEMS_13)
      capacity = 250
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(2, len(result[0]))
      self.failUnlessEqual(200, result[1])

      items = buildItemDict(ITEMS_14)
      capacity = 2500
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(2, len(result[0]))
      self.failUnlessEqual(2000, result[1])

   def test_4_07(self):
      """
      Test 1.07.
      Test alternateFit() behavior for items dictionary where only 50% of items fit.
      """
      items = buildItemDict(ITEMS_05)
      capacity = 4
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(4, result[1])

      items = buildItemDict(ITEMS_06)
      capacity = 45
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(40, result[1])

      items = buildItemDict(ITEMS_07)
      capacity = 450
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(400, result[1])

      items = buildItemDict(ITEMS_08)
      capacity = 4500
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(4000, result[1])

      items = buildItemDict(ITEMS_09)
      capacity = 45000
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(40000, result[1])

      items = buildItemDict(ITEMS_10)
      capacity = 450000
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(400000, result[1])

      items = buildItemDict(ITEMS_11)
      capacity = 4
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(4, result[1])

      items = buildItemDict(ITEMS_12)
      capacity = 45
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(40, result[1])

      items = buildItemDict(ITEMS_13)
      capacity = 450
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(400, result[1])

      items = buildItemDict(ITEMS_14)
      capacity = 4500
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(4000, result[1])

   def test_4_08(self):
      """
      Test 1.08.
      Test alternateFit() behavior for items dictionary where only 75% of items fit.
      """
      items = buildItemDict(ITEMS_05)
      capacity = 6
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(6, len(result[0]))
      self.failUnlessEqual(6, result[1])

      items = buildItemDict(ITEMS_06)
      capacity = 65
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(6, len(result[0]))
      self.failUnlessEqual(60, result[1])

      items = buildItemDict(ITEMS_07)
      capacity = 650
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(6, len(result[0]))
      self.failUnlessEqual(600, result[1])

      items = buildItemDict(ITEMS_08)
      capacity = 6500
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(6, len(result[0]))
      self.failUnlessEqual(6000, result[1])

      items = buildItemDict(ITEMS_09)
      capacity = 65000
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(6, len(result[0]))
      self.failUnlessEqual(60000, result[1])

      items = buildItemDict(ITEMS_10)
      capacity = 650000
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(6, len(result[0]))
      self.failUnlessEqual(600000, result[1])

      items = buildItemDict(ITEMS_15)
      capacity = 7
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(6, len(result[0]))
      self.failUnlessEqual(6, result[1])

      items = buildItemDict(ITEMS_16)
      capacity = 65
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(6, len(result[0]))
      self.failUnlessEqual(60, result[1])

      items = buildItemDict(ITEMS_17)
      capacity = 650
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(6, len(result[0]))
      self.failUnlessEqual(600, result[1])

      items = buildItemDict(ITEMS_18)
      capacity = 6500
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(6, len(result[0]))
      self.failUnlessEqual(6000, result[1])

   def test_4_09(self):
      """
      Test 1.09.
      Test alternateFit() behavior for items dictionary where all items individually
      exceed the capacity.
      """
      items = buildItemDict(ITEMS_06)
      capacity = 9
      result = alternateFit(items, capacity)
      self.failUnlessEqual(([], 0), result)

      items = buildItemDict(ITEMS_07)
      capacity = 99
      result = alternateFit(items, capacity)
      self.failUnlessEqual(([], 0), result)

      items = buildItemDict(ITEMS_08)
      capacity = 999
      result = alternateFit(items, capacity)
      self.failUnlessEqual(([], 0), result)

      items = buildItemDict(ITEMS_09)
      capacity = 9999
      result = alternateFit(items, capacity)
      self.failUnlessEqual(([], 0), result)

      items = buildItemDict(ITEMS_10)
      capacity = 99999
      result = alternateFit(items, capacity)
      self.failUnlessEqual(([], 0), result)

   def test_4_10(self):
      """
      Test 1.10.
      Test alternateFit() behavior for items dictionary where first half of items
      individually exceed capacity and remainder fit.
      """
      items = buildItemDict(ITEMS_04)
      capacity = 200
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(111, result[1])

   def test_4_11(self):
      """
      Test 1.11.
      Test alternateFit() behavior for items dictionary where middle half of items
      individually exceed capacity and remainder fit.
      """
      items = buildItemDict(ITEMS_11)
      capacity = 5
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(4, result[1])

      items = buildItemDict(ITEMS_12)
      capacity = 50
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(40, result[1])

      items = buildItemDict(ITEMS_13)
      capacity = 500
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(400, result[1])

      items = buildItemDict(ITEMS_14)
      capacity = 5000
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(4000, result[1])

   def test_4_12(self):
      """
      Test 1.12.
      Test alternateFit() behavior for items dictionary where second half of items
      individually exceed capacity and remainder fit.
      """
      items = buildItemDict(ITEMS_03)
      capacity = 200
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(4, len(result[0]))
      self.failUnlessEqual(111, result[1])

   def test_4_13(self):
      """
      Test 1.10.
      Test alternateFit() behavior for items dictionary where first half of items
      individually exceed capacity and only some of remainder fit.
      """
      items = buildItemDict(ITEMS_04)
      capacity = 50
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnless(len(result[0]) < 4, "%s < 4" % len(result[0]))

   def test_4_14(self):
      """
      Test 1.11.
      Test alternateFit() behavior for items dictionary where middle half of items
      individually exceed capacity and only some of remainder fit.
      """
      items = buildItemDict(ITEMS_11)
      capacity = 3
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnless(len(result[0]) < 4, "%s < 4" % len(result[0]))

      items = buildItemDict(ITEMS_12)
      capacity = 35
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnless(len(result[0]) < 4, "%s < 4" % len(result[0]))

      items = buildItemDict(ITEMS_13)
      capacity = 350
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnless(len(result[0]) < 4, "%s < 4" % len(result[0]))

      items = buildItemDict(ITEMS_14)
      capacity = 3500
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnless(len(result[0]) < 4, "%s < 4" % len(result[0]))

   def test_4_15(self):
      """
      Test 1.12.
      Test alternateFit() behavior for items dictionary where second half of items
      individually exceed capacity and only some of remainder fit.
      """
      items = buildItemDict(ITEMS_03)
      capacity = 50
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnless(len(result[0]) < 4, "%s < 4" % len(result[0]))

   def test_4_16(self):
      """
      Test 1.16.
      Test alternateFit() behavior for items dictionary where all items fit.
      """
      items = buildItemDict(ITEMS_02)
      capacity = 1000000
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(0, result[1])

      items = buildItemDict(ITEMS_03)
      capacity = 2000000
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(1111111, result[1])

      items = buildItemDict(ITEMS_04)
      capacity = 2000000
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(1111111, result[1])

      items = buildItemDict(ITEMS_05)
      capacity = 1000000
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(8, result[1])

      items = buildItemDict(ITEMS_06)
      capacity = 1000000
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(80, result[1])

      items = buildItemDict(ITEMS_07)
      capacity = 1000000
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(800, result[1])

      items = buildItemDict(ITEMS_08)
      capacity = 1000000
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(8000, result[1])

      items = buildItemDict(ITEMS_09)
      capacity = 1000000
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(80000, result[1])

      items = buildItemDict(ITEMS_10)
      capacity = 1000000
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(800000, result[1])

      items = buildItemDict(ITEMS_11)
      capacity = 1000000
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(400004, result[1])

      items = buildItemDict(ITEMS_12)
      capacity = 1000000
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(400040, result[1])

      items = buildItemDict(ITEMS_13)
      capacity = 1000000
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(400400, result[1])

      items = buildItemDict(ITEMS_14)
      capacity = 1000000
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(404000, result[1])

      items = buildItemDict(ITEMS_15)
      capacity = 1000000
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(200006, result[1])

      items = buildItemDict(ITEMS_16)
      capacity = 1000000
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(200060, result[1])

      items = buildItemDict(ITEMS_17)
      capacity = 1000000
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(200600, result[1])

      items = buildItemDict(ITEMS_18)
      capacity = 1000000
      result = alternateFit(items, capacity)
      self.failUnless(result[1] <= capacity, "%s <= %s" % (result[1], capacity))
      self.failUnlessEqual(8, len(result[0]))
      self.failUnlessEqual(206000, result[1])


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

