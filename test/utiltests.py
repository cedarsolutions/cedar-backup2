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
# Copyright (c) 2004-2006 Kenneth J. Pronovici.
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
# Purpose  : Tests utility functionality.
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

########################################################################
# Module documentation
########################################################################

"""
Unit tests for CedarBackup2/util.py.

Code Coverage
=============

   This module contains individual tests for the public functions and classes
   implemented in util.py.

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
   build environment.  There is a no need to use a UTILTESTS_FULL environment
   variable to provide a "reduced feature set" test suite as for some of the
   other test modules.

@author Kenneth J. Pronovici <pronovic@ieee.org>
"""


########################################################################
# Import modules and do runtime validations
########################################################################

import sys
import os
import unittest
import tempfile
from os.path import isdir

from CedarBackup2.testutil import findResources, removedir, platformHasEcho
from CedarBackup2.util import UnorderedList, PathResolverSingleton
from CedarBackup2.util import resolveCommand, executeCommand, getFunctionReference, encodePath


#######################################################################
# Module-wide configuration and constants
#######################################################################

DATA_DIRS = [ "./data", "./test/data" ]
RESOURCES = [ "lotsoflines.py", ]


#######################################################################
# Test Case Classes
#######################################################################

##########################
# TestUnorderedList class
##########################

class TestUnorderedList(unittest.TestCase):

   """Tests for the UnorderedList class."""

   ################
   # Setup methods
   ################

   def setUp(self):
      pass

   def tearDown(self):
      pass


   ##################################
   # Test unordered list comparisons
   ##################################

   def testComparison_001(self):
      """
      Test two empty lists.
      """
      list1 = UnorderedList()
      list2 = UnorderedList()
      self.failUnlessEqual(list1, list2)
      self.failUnlessEqual(list2, list1)

   def testComparison_002(self):
      """
      Test empty vs. non-empty list.
      """
      list1 = UnorderedList()
      list2 = UnorderedList()
      list1.append(1)
      list1.append(2)
      list1.append(3)
      list1.append(4)
      self.failUnlessEqual([1,2,3,4,], list1)
      self.failUnlessEqual([2,3,4,1,], list1)
      self.failUnlessEqual([3,4,1,2,], list1)
      self.failUnlessEqual([4,1,2,3,], list1)
      self.failUnlessEqual(list1, [4,3,2,1,])
      self.failUnlessEqual(list1, [3,2,1,4,])
      self.failUnlessEqual(list1, [2,1,4,3,])
      self.failUnlessEqual(list1, [1,4,3,2,])
      self.failIfEqual(list1, list2)
      self.failIfEqual(list2, list1)

   def testComparison_003(self):
      """
      Test two non-empty lists, completely different contents.
      """
      list1 = UnorderedList()
      list2 = UnorderedList()
      list1.append(1)
      list1.append(2)
      list1.append(3)
      list1.append(4)
      list2.append('a')
      list2.append('b')
      list2.append('c')
      list2.append('d')
      self.failUnlessEqual([1,2,3,4,], list1)
      self.failUnlessEqual([2,3,4,1,], list1)
      self.failUnlessEqual([3,4,1,2,], list1)
      self.failUnlessEqual([4,1,2,3,], list1)
      self.failUnlessEqual(list1, [4,3,2,1,])
      self.failUnlessEqual(list1, [3,2,1,4,])
      self.failUnlessEqual(list1, [2,1,4,3,])
      self.failUnlessEqual(list1, [1,4,3,2,])
      self.failUnlessEqual(['a','b','c','d',], list2)
      self.failUnlessEqual(['b','c','d','a',], list2)
      self.failUnlessEqual(['c','d','a','b',], list2)
      self.failUnlessEqual(['d','a','b','c',], list2)
      self.failUnlessEqual(list2, ['d','c','b','a',])
      self.failUnlessEqual(list2, ['c','b','a','d',])
      self.failUnlessEqual(list2, ['b','a','d','c',])
      self.failUnlessEqual(list2, ['a','d','c','b',])
      self.failIfEqual(list1, list2)
      self.failIfEqual(list2, list1)

   def testComparison_004(self):
      """
      Test two non-empty lists, different but overlapping contents.
      """
      list1 = UnorderedList()
      list2 = UnorderedList()
      list1.append(1)
      list1.append(2)
      list1.append(3)
      list1.append(4)
      list2.append(3)
      list2.append(4)
      list2.append('a')
      list2.append('b')
      self.failUnlessEqual([1,2,3,4,], list1)
      self.failUnlessEqual([2,3,4,1,], list1)
      self.failUnlessEqual([3,4,1,2,], list1)
      self.failUnlessEqual([4,1,2,3,], list1)
      self.failUnlessEqual(list1, [4,3,2,1,])
      self.failUnlessEqual(list1, [3,2,1,4,])
      self.failUnlessEqual(list1, [2,1,4,3,])
      self.failUnlessEqual(list1, [1,4,3,2,])
      self.failUnlessEqual([3,4,'a','b',], list2)
      self.failUnlessEqual([4,'a','b',3,], list2)
      self.failUnlessEqual(['a','b',3,4,], list2)
      self.failUnlessEqual(['b',3,4,'a',], list2)
      self.failUnlessEqual(list2, ['b','a',4,3,])
      self.failUnlessEqual(list2, ['a',4,3,'b',])
      self.failUnlessEqual(list2, [4,3,'b','a',])
      self.failUnlessEqual(list2, [3,'b','a',4,])
      self.failIfEqual(list1, list2)
      self.failIfEqual(list2, list1)

   def testComparison_005(self):
      """
      Test two non-empty lists, exactly the same contents, same order.
      """
      list1 = UnorderedList()
      list2 = UnorderedList()
      list1.append(1)
      list1.append(2)
      list1.append(3)
      list1.append(4)
      list2.append(1)
      list2.append(2)
      list2.append(3)
      list2.append(4)
      self.failUnlessEqual([1,2,3,4,], list1)
      self.failUnlessEqual([2,3,4,1,], list1)
      self.failUnlessEqual([3,4,1,2,], list1)
      self.failUnlessEqual([4,1,2,3,], list1)
      self.failUnlessEqual(list1, [4,3,2,1,])
      self.failUnlessEqual(list1, [3,2,1,4,])
      self.failUnlessEqual(list1, [2,1,4,3,])
      self.failUnlessEqual(list1, [1,4,3,2,])
      self.failUnlessEqual([1,2,3,4,], list2)
      self.failUnlessEqual([2,3,4,1,], list2)
      self.failUnlessEqual([3,4,1,2,], list2)
      self.failUnlessEqual([4,1,2,3,], list2)
      self.failUnlessEqual(list2, [4,3,2,1,])
      self.failUnlessEqual(list2, [3,2,1,4,])
      self.failUnlessEqual(list2, [2,1,4,3,])
      self.failUnlessEqual(list2, [1,4,3,2,])
      self.failUnlessEqual(list1, list2)
      self.failUnlessEqual(list2, list1)

   def testComparison_006(self):
      """
      Test two non-empty lists, exactly the same contents, different order.
      """
      list1 = UnorderedList()
      list2 = UnorderedList()
      list1.append(1)
      list1.append(2)
      list1.append(3)
      list1.append(4)
      list2.append(3)
      list2.append(1)
      list2.append(2)
      list2.append(4)
      self.failUnlessEqual([1,2,3,4,], list1)
      self.failUnlessEqual([2,3,4,1,], list1)
      self.failUnlessEqual([3,4,1,2,], list1)
      self.failUnlessEqual([4,1,2,3,], list1)
      self.failUnlessEqual(list1, [4,3,2,1,])
      self.failUnlessEqual(list1, [3,2,1,4,])
      self.failUnlessEqual(list1, [2,1,4,3,])
      self.failUnlessEqual(list1, [1,4,3,2,])
      self.failUnlessEqual([1,2,3,4,], list2)
      self.failUnlessEqual([2,3,4,1,], list2)
      self.failUnlessEqual([3,4,1,2,], list2)
      self.failUnlessEqual([4,1,2,3,], list2)
      self.failUnlessEqual(list2, [4,3,2,1,])
      self.failUnlessEqual(list2, [3,2,1,4,])
      self.failUnlessEqual(list2, [2,1,4,3,])
      self.failUnlessEqual(list2, [1,4,3,2,])
      self.failUnlessEqual(list1, list2)
      self.failUnlessEqual(list2, list1)

   def testComparison_007(self):
      """
      Test two non-empty lists, exactly the same contents, some duplicates,
      same order.
      """
      list1 = UnorderedList()
      list2 = UnorderedList()
      list1.append(1)
      list1.append(2)
      list1.append(2)
      list1.append(3)
      list1.append(4)
      list1.append(4)
      list2.append(1)
      list2.append(2)
      list2.append(2)
      list2.append(3)
      list2.append(4)
      list2.append(4)
      self.failUnlessEqual([1,2,2,3,4,4,], list1)
      self.failUnlessEqual([2,2,3,4,1,4,], list1)
      self.failUnlessEqual([2,3,4,1,4,2,], list1)
      self.failUnlessEqual([2,4,1,4,2,3,], list1)
      self.failUnlessEqual(list1, [1,2,2,3,4,4,])
      self.failUnlessEqual(list1, [2,2,3,4,1,4,])
      self.failUnlessEqual(list1, [2,3,4,1,4,2,])
      self.failUnlessEqual(list1, [2,4,1,4,2,3,])
      self.failUnlessEqual([1,2,2,3,4,4,], list2)
      self.failUnlessEqual([2,2,3,4,1,4,], list2)
      self.failUnlessEqual([2,3,4,1,4,2,], list2)
      self.failUnlessEqual([2,4,1,4,2,3,], list2)
      self.failUnlessEqual(list2, [1,2,2,3,4,4,])
      self.failUnlessEqual(list2, [2,2,3,4,1,4,])
      self.failUnlessEqual(list2, [2,3,4,1,4,2,])
      self.failUnlessEqual(list2, [2,4,1,4,2,3,])
      self.failUnlessEqual(list1, list2)
      self.failUnlessEqual(list2, list1)

   def testComparison_008(self):
      """
      Test two non-empty lists, exactly the same contents, some duplicates,
      different order.
      """
      list1 = UnorderedList()
      list2 = UnorderedList()
      list1.append(1)
      list1.append(2)
      list1.append(2)
      list1.append(3)
      list1.append(4)
      list1.append(4)
      list2.append(3)
      list2.append(1)
      list2.append(2)
      list2.append(2)
      list2.append(4)
      list2.append(4)
      self.failUnlessEqual([1,2,2,3,4,4,], list1)
      self.failUnlessEqual([2,2,3,4,1,4,], list1)
      self.failUnlessEqual([2,3,4,1,4,2,], list1)
      self.failUnlessEqual([2,4,1,4,2,3,], list1)
      self.failUnlessEqual(list1, [1,2,2,3,4,4,])
      self.failUnlessEqual(list1, [2,2,3,4,1,4,])
      self.failUnlessEqual(list1, [2,3,4,1,4,2,])
      self.failUnlessEqual(list1, [2,4,1,4,2,3,])
      self.failUnlessEqual([1,2,2,3,4,4,], list2)
      self.failUnlessEqual([2,2,3,4,1,4,], list2)
      self.failUnlessEqual([2,3,4,1,4,2,], list2)
      self.failUnlessEqual([2,4,1,4,2,3,], list2)
      self.failUnlessEqual(list2, [1,2,2,3,4,4,])
      self.failUnlessEqual(list2, [2,2,3,4,1,4,])
      self.failUnlessEqual(list2, [2,3,4,1,4,2,])
      self.failUnlessEqual(list2, [2,4,1,4,2,3,])
      self.failUnlessEqual(list1, list2)
      self.failUnlessEqual(list2, list1)


##################################
# TestPathResolverSingleton class
##################################

class TestPathResolverSingleton(unittest.TestCase):

   """Tests for the PathResolverSingleton class."""

   ################
   # Setup methods
   ################

   def setUp(self):
      pass

   def tearDown(self):
      pass


   ##########################
   # Test singleton behavior
   ##########################

   def testBehavior_001(self):
      """
      Check behavior of constructor around filling and clearing instance variable.
      """
      PathResolverSingleton._instance = None
      instance = PathResolverSingleton()
      self.failIfEqual(None, PathResolverSingleton._instance)
      self.failUnless(instance is PathResolverSingleton._instance)

      self.failUnlessRaises(RuntimeError, PathResolverSingleton)

      PathResolverSingleton._instance = None
      instance = PathResolverSingleton()
      self.failIfEqual(None, PathResolverSingleton._instance)
      self.failUnless(instance is PathResolverSingleton._instance)

   def testBehavior_002(self):
      """
      Check behavior of getInstance() around filling and clearing instance variable.
      """
      PathResolverSingleton._instance = None
      instance1 = PathResolverSingleton.getInstance()
      instance2 = PathResolverSingleton.getInstance()
      instance3 = PathResolverSingleton.getInstance()
      self.failIfEqual(None, PathResolverSingleton._instance)
      self.failUnless(instance1 is PathResolverSingleton._instance)
      self.failUnless(instance1 is instance2)
      self.failUnless(instance1 is instance3)

      PathResolverSingleton._instance = None
      PathResolverSingleton()
      instance4 = PathResolverSingleton.getInstance()
      instance5 = PathResolverSingleton.getInstance()
      instance6 = PathResolverSingleton.getInstance()
      self.failUnless(instance1 is not instance4)
      self.failUnless(instance4 is PathResolverSingleton._instance)
      self.failUnless(instance4 is instance5)
      self.failUnless(instance4 is instance6)

      PathResolverSingleton._instance = None
      instance7 = PathResolverSingleton.getInstance()
      instance8 = PathResolverSingleton.getInstance()
      instance9 = PathResolverSingleton.getInstance()
      self.failUnless(instance1 is not instance7)
      self.failUnless(instance4 is not instance7)
      self.failUnless(instance7 is PathResolverSingleton._instance)
      self.failUnless(instance7 is instance8)
      self.failUnless(instance7 is instance9)


   ############################
   # Test lookup functionality
   ############################

   def testLookup_001(self):
      """
      Test that lookup() always returns default when singleton is empty.
      """
      PathResolverSingleton._instance = None
      instance = PathResolverSingleton.getInstance()

      result = instance.lookup("whatever")
      self.failUnlessEqual(result, None)

      result = instance.lookup("whatever", None)
      self.failUnlessEqual(result, None)

      result = instance.lookup("other")
      self.failUnlessEqual(result, None)

      result = instance.lookup("other", "default")
      self.failUnlessEqual(result, "default")

   def testLookup_002(self):
      """
      Test that lookup() returns proper values when singleton is not empty.
      """
      mappings = { "one" : "/path/to/one", "two" : "/path/to/two" };
      PathResolverSingleton._instance = None
      singleton = PathResolverSingleton()
      singleton.fill(mappings)

      instance = PathResolverSingleton.getInstance()

      result = instance.lookup("whatever")
      self.failUnlessEqual(result, None)

      result = instance.lookup("whatever", None)
      self.failUnlessEqual(result, None)

      result = instance.lookup("other")
      self.failUnlessEqual(result, None)

      result = instance.lookup("other", "default")
      self.failUnlessEqual(result, "default")

      result = instance.lookup("one")
      self.failUnlessEqual(result, "/path/to/one")

      result = instance.lookup("one", None)
      self.failUnlessEqual(result, "/path/to/one")

      result = instance.lookup("two", None)
      self.failUnlessEqual(result, "/path/to/two")

      result = instance.lookup("two", "default")
      self.failUnlessEqual(result, "/path/to/two")


######################
# TestFunctions class
######################

class TestFunctions(unittest.TestCase):

   """Tests for the various public functions."""


   ################
   # Setup methods
   ################

   def setUp(self):
      try:
         self.tmpdir = tempfile.mkdtemp()
         self.resources = findResources(RESOURCES, DATA_DIRS)
      except Exception, e:
         self.fail(e)

   def tearDown(self):
      removedir(self.tmpdir)


   ##################
   # Utility methods
   ##################

   def getTempfile(self):
      """Gets a path to a temporary file on disk."""
      (fd, name) = tempfile.mkstemp(dir=self.tmpdir)
      try:
         os.close(fd)
      except: pass
      return name


   ##############################
   # Test getFunctionReference() 
   ##############################
         
   def testGetFunctionReference_001(self):
      """
      Check that the search works within "standard" Python namespace.
      """
      module = "os.path"
      function = "isdir"
      reference = getFunctionReference(module, function)
      self.failUnless(isdir is reference)

   def testGetFunctionReference_002(self):
      """
      Check that the search works for things within CedarBackup2.
      """
      module = "CedarBackup2.util"
      function = "executeCommand"
      reference = getFunctionReference(module, function)
      self.failUnless(executeCommand is reference)


   ########################
   # Test resolveCommand() 
   ########################
         
   def testResolveCommand_001(self):
      """
      Test that the command is echoed back unchanged when singleton is empty.
      """
      PathResolverSingleton._instance = None

      command = [ "BAD", ]
      expected = command[:]
      result = resolveCommand(command)
      self.failUnlessEqual(expected, result)

      command = [ "GOOD", ]
      expected = command[:]
      result = resolveCommand(command)
      self.failUnlessEqual(expected, result)

      command = [ "WHATEVER", "--verbose", "--debug", 'tvh:asa892831', "blech", "<", ]
      expected = command[:]
      result = resolveCommand(command)
      self.failUnlessEqual(expected, result)

   def testResolveCommand_002(self):
      """
      Test that the command is echoed back unchanged when mapping is not found.
      """
      PathResolverSingleton._instance = None
      mappings = { "one" : "/path/to/one", "two" : "/path/to/two" };
      singleton = PathResolverSingleton()
      singleton.fill(mappings)

      command = [ "BAD", ]
      expected = command[:]
      result = resolveCommand(command)
      self.failUnlessEqual(expected, result)

      command = [ "GOOD", ]
      expected = command[:]
      result = resolveCommand(command)
      self.failUnlessEqual(expected, result)

      command = [ "WHATEVER", "--verbose", "--debug", 'tvh:asa892831', "blech", "<", ]
      expected = command[:]
      result = resolveCommand(command)
      self.failUnlessEqual(expected, result)

   def testResolveCommand_003(self):
      """
      Test that the command is echoed back changed appropriately when mapping is found.
      """
      PathResolverSingleton._instance = None
      mappings = { "one" : "/path/to/one", "two" : "/path/to/two" };
      singleton = PathResolverSingleton()
      singleton.fill(mappings)

      command = [ "one", ]
      expected = [ "/path/to/one", ]
      result = resolveCommand(command)
      self.failUnlessEqual(expected, result)

      command = [ "two", ]
      expected = [ "/path/to/two", ]
      result = resolveCommand(command)
      self.failUnlessEqual(expected, result)

      command = [ "two", "--verbose", "--debug", 'tvh:asa892831', "blech", "<", ]
      expected = ["/path/to/two", "--verbose", "--debug", 'tvh:asa892831', "blech", "<", ]
      result = resolveCommand(command)
      self.failUnlessEqual(expected, result)


   ########################
   # Test executeCommand() 
   ########################
         
   def testExecuteCommand_001(self):
      """
      Execute a command that should succeed, no arguments, returnOutput=False
      Command-line: echo
      """
      if platformHasEcho():
         command=["echo", ]
         args=[]
         (result, output) = executeCommand(command, args, returnOutput=False)
         self.failUnlessEqual(0, result)
         self.failUnlessEqual(None, output)

   def testExecuteCommand_002(self):
      """
      Execute a command that should succeed, one argument, returnOutput=False
      Command-line: python -V
      """
      command=["python", ]
      args=["-V", ]
      (result, output) = executeCommand(command, args, returnOutput=False)
      self.failUnlessEqual(0, result)
      self.failUnlessEqual(None, output)

   def testExecuteCommand_003(self):
      """
      Execute a command that should succeed, two arguments, returnOutput=False
      Command-line: python -c "import sys; print sys.argv[1:]; sys.exit(0)"
      """
      command=["python", ]
      args=["-c", "import sys; print sys.argv[1:]; sys.exit(0)", ]
      (result, output) = executeCommand(command, args, returnOutput=False)
      self.failUnlessEqual(0, result)
      self.failUnlessEqual(None, output)

   def testExecuteCommand_004(self):
      """
      Execute a command that should succeed, three arguments, returnOutput=False
      Command-line: python -c "import sys; print sys.argv[1:]; sys.exit(0)" first
      """
      command=["python", ]
      args=["-c", "import sys; print sys.argv[1:]; sys.exit(0)", "first", ]
      (result, output) = executeCommand(command, args, returnOutput=False)
      self.failUnlessEqual(0, result)
      self.failUnlessEqual(None, output)

   def testExecuteCommand_005(self):
      """
      Execute a command that should succeed, four arguments, returnOutput=False
      Command-line: python -c "import sys; print sys.argv[1:]; sys.exit(0)" first second
      """
      command=["python", ]
      args=["-c", "import sys; print sys.argv[1:]; sys.exit(0)", "first", "second", ]
      (result, output) = executeCommand(command, args, returnOutput=False)
      self.failUnlessEqual(0, result)
      self.failUnlessEqual(None, output)

   def testExecuteCommand_006(self):
      """
      Execute a command that should fail, returnOutput=False
      Command-line: python -c "import sys; print sys.argv[1:]; sys.exit(1)"
      """
      command=["python", ]
      args=["-c", "import sys; print sys.argv[1:]; sys.exit(1)", ]
      (result, output) = executeCommand(command, args, returnOutput=False)
      self.failIfEqual(0, result)
      self.failUnlessEqual(None, output)

   def testExecuteCommand_007(self):
      """
      Execute a command that should fail, more arguments, returnOutput=False
      Command-line: python -c "import sys; print sys.argv[1:]; sys.exit(1)" first second
      """
      command=["python", ]
      args=["-c", "import sys; print sys.argv[1:]; sys.exit(1)", "first", "second", ]
      (result, output) = executeCommand(command, args, returnOutput=False)
      self.failIfEqual(0, result)
      self.failUnlessEqual(None, output)

   def testExecuteCommand_008(self):
      """
      Execute a command that should succeed, no arguments, returnOutput=True
      Command-line: echo
      """
      if platformHasEcho():
         command=["echo", ]
         args=[]
         (result, output) = executeCommand(command, args, returnOutput=True)
         self.failUnlessEqual(0, result)
         self.failUnlessEqual(1, len(output))
         self.failUnlessEqual(os.linesep, output[0])

   def testExecuteCommand_009(self):
      """
      Execute a command that should succeed, one argument, returnOutput=True
      Command-line: python -V
      """
      command=["python", ]
      args=["-V", ]
      (result, output) = executeCommand(command, args, returnOutput=True)
      self.failUnlessEqual(0, result)
      self.failUnlessEqual(1, len(output))
      self.failUnless(output[0].startswith("Python"))

   def testExecuteCommand_010(self):
      """
      Execute a command that should succeed, two arguments, returnOutput=True
      Command-line: python -c "import sys; print ''; sys.exit(0)"
      """
      command=["python", ]
      args=["-c", "import sys; print ''; sys.exit(0)", ]
      (result, output) = executeCommand(command, args, returnOutput=True)
      self.failUnlessEqual(0, result)
      self.failUnlessEqual(1, len(output))
      self.failUnlessEqual(os.linesep, output[0])

   def testExecuteCommand_011(self):
      """
      Execute a command that should succeed, three arguments, returnOutput=True
      Command-line: python -c "import sys; print '%s' % (sys.argv[1]); sys.exit(0)" first
      """
      command=["python", ]
      args=["-c", "import sys; print '%s' % (sys.argv[1]); sys.exit(0)", "first", ]
      (result, output) = executeCommand(command, args, returnOutput=True)
      self.failUnlessEqual(0, result)
      self.failUnlessEqual(1, len(output))
      self.failUnlessEqual("first%s" % os.linesep, output[0])

   def testExecuteCommand_012(self):
      """
      Execute a command that should succeed, four arguments, returnOutput=True
      Command-line: python -c "import sys; print '%s' % sys.argv[1]; print '%s' % sys.argv[2]; sys.exit(0)" first second
      """
      command=["python", ]
      args=["-c", "import sys; print '%s' % sys.argv[1]; print '%s' % sys.argv[2]; sys.exit(0)", "first", "second", ]
      (result, output) = executeCommand(command, args, returnOutput=True)
      self.failUnlessEqual(0, result)
      self.failUnlessEqual(2, len(output))
      self.failUnlessEqual("first%s" % os.linesep, output[0])
      self.failUnlessEqual("second%s" % os.linesep, output[1])

   def testExecuteCommand_013(self):
      """
      Execute a command that should fail, returnOutput=True
      Command-line: python -c "import sys; print ''; sys.exit(1)"
      """
      command=["python", ]
      args=["-c", "import sys; print ''; sys.exit(1)", ]
      (result, output) = executeCommand(command, args, returnOutput=True)
      self.failIfEqual(0, result)
      self.failUnlessEqual(1, len(output))
      self.failUnlessEqual(os.linesep, output[0])

   def testExecuteCommand_014(self):
      """
      Execute a command that should fail, more arguments, returnOutput=True
      Command-line: python -c "import sys; print '%s' % sys.argv[1]; print '%s' % sys.argv[2]; sys.exit(1)" first second
      """
      command=["python", ]
      args=["-c", "import sys; print '%s' % sys.argv[1]; print '%s' % sys.argv[2]; sys.exit(1)", "first", "second", ]
      (result, output) = executeCommand(command, args, returnOutput=True)
      self.failIfEqual(0, result)
      self.failUnlessEqual(2, len(output))
      self.failUnlessEqual("first%s" % os.linesep, output[0])
      self.failUnlessEqual("second%s" % os.linesep, output[1])

   def testExecuteCommand_015(self):
      """
      Execute a command that should succeed, no arguments, returnOutput=False
      Do this all bundled into the command list, just to check that this works as expected.
      Command-line: echo
      """
      if platformHasEcho():
         command=["echo", ]
         args=[]
         (result, output) = executeCommand(command, args, returnOutput=False)
         self.failUnlessEqual(0, result)
         self.failUnlessEqual(None, output)

   def testExecuteCommand_016(self):
      """
      Execute a command that should succeed, one argument, returnOutput=False
      Do this all bundled into the command list, just to check that this works as expected.
      Command-line: python -V
      """
      command=["python", "-V", ]
      args=[]
      (result, output) = executeCommand(command, args, returnOutput=False)
      self.failUnlessEqual(0, result)
      self.failUnlessEqual(None, output)

   def testExecuteCommand_017(self):
      """
      Execute a command that should succeed, two arguments, returnOutput=False
      Do this all bundled into the command list, just to check that this works as expected.
      Command-line: python -c "import sys; print sys.argv[1:]; sys.exit(0)"
      """
      command=["python", "-c", "import sys; print sys.argv[1:]; sys.exit(0)", ]
      args=[]
      (result, output) = executeCommand(command, args, returnOutput=False)
      self.failUnlessEqual(0, result)
      self.failUnlessEqual(None, output)

   def testExecuteCommand_018(self):
      """
      Execute a command that should succeed, three arguments, returnOutput=False
      Do this all bundled into the command list, just to check that this works as expected.
      Command-line: python -c "import sys; print sys.argv[1:]; sys.exit(0)" first
      """
      command=["python", "-c", "import sys; print sys.argv[1:]; sys.exit(0)", "first", ]
      args=[]
      (result, output) = executeCommand(command, args, returnOutput=False)
      self.failUnlessEqual(0, result)
      self.failUnlessEqual(None, output)

   def testExecuteCommand_019(self):
      """
      Execute a command that should succeed, four arguments, returnOutput=False
      Do this all bundled into the command list, just to check that this works as expected.
      Command-line: python -c "import sys; print sys.argv[1:]; sys.exit(0)" first second
      """
      command=["python", "-c", "import sys; print sys.argv[1:]; sys.exit(0)", "first", "second", ]
      args=[]
      (result, output) = executeCommand(command, args, returnOutput=False)
      self.failUnlessEqual(0, result)
      self.failUnlessEqual(None, output)

   def testExecuteCommand_020(self):
      """
      Execute a command that should fail, returnOutput=False
      Do this all bundled into the command list, just to check that this works as expected.
      Command-line: python -c "import sys; print sys.argv[1:]; sys.exit(1)"
      """
      command=["python", "-c", "import sys; print sys.argv[1:]; sys.exit(1)", ]
      args=[]
      (result, output) = executeCommand(command, args, returnOutput=False)
      self.failIfEqual(0, result)
      self.failUnlessEqual(None, output)

   def testExecuteCommand_021(self):
      """
      Execute a command that should fail, more arguments, returnOutput=False
      Do this all bundled into the command list, just to check that this works as expected.
      Command-line: python -c "import sys; print sys.argv[1:]; sys.exit(1)" first second
      """
      command=["python", "-c", "import sys; print sys.argv[1:]; sys.exit(1)", "first", "second", ]
      args=[]
      (result, output) = executeCommand(command, args, returnOutput=False)
      self.failIfEqual(0, result)
      self.failUnlessEqual(None, output)

   def testExecuteCommand_022(self):
      """
      Execute a command that should succeed, no arguments, returnOutput=True
      Do this all bundled into the command list, just to check that this works as expected.
      Command-line: echo
      """
      if platformHasEcho():
         command=["echo", ]
         args=[]
         (result, output) = executeCommand(command, args, returnOutput=True)
         self.failUnlessEqual(0, result)
         self.failUnlessEqual(1, len(output))
         self.failUnlessEqual(os.linesep, output[0])

   def testExecuteCommand_023(self):
      """
      Execute a command that should succeed, one argument, returnOutput=True
      Do this all bundled into the command list, just to check that this works as expected.
      Command-line: python -V
      """
      command=["python", "-V"]
      args=[]
      (result, output) = executeCommand(command, args, returnOutput=True)
      self.failUnlessEqual(0, result)
      self.failUnlessEqual(1, len(output))
      self.failUnless(output[0].startswith("Python"))

   def testExecuteCommand_024(self):
      """
      Execute a command that should succeed, two arguments, returnOutput=True
      Do this all bundled into the command list, just to check that this works as expected.
      Command-line: python -c "import sys; print ''; sys.exit(0)"
      """
      command=["python", "-c", "import sys; print ''; sys.exit(0)", ]
      args=[]
      (result, output) = executeCommand(command, args, returnOutput=True)
      self.failUnlessEqual(0, result)
      self.failUnlessEqual(1, len(output))
      self.failUnlessEqual(os.linesep, output[0])

   def testExecuteCommand_025(self):
      """
      Execute a command that should succeed, three arguments, returnOutput=True
      Do this all bundled into the command list, just to check that this works as expected.
      Command-line: python -c "import sys; print '%s' % (sys.argv[1]); sys.exit(0)" first
      """
      command=["python", "-c", "import sys; print '%s' % (sys.argv[1]); sys.exit(0)", "first", ]
      args=[]
      (result, output) = executeCommand(command, args, returnOutput=True)
      self.failUnlessEqual(0, result)
      self.failUnlessEqual(1, len(output))
      self.failUnlessEqual("first%s" % os.linesep, output[0])

   def testExecuteCommand_026(self):
      """
      Execute a command that should succeed, four arguments, returnOutput=True
      Do this all bundled into the command list, just to check that this works as expected.
      Command-line: python -c "import sys; print '%s' % sys.argv[1]; print '%s' % sys.argv[2]; sys.exit(0)" first second
      """
      command=["python", "-c", "import sys; print '%s' % sys.argv[1]; print '%s' % sys.argv[2]; sys.exit(0)", "first", "second", ]
      args=[]
      (result, output) = executeCommand(command, args, returnOutput=True)
      self.failUnlessEqual(0, result)
      self.failUnlessEqual(2, len(output))
      self.failUnlessEqual("first%s" % os.linesep, output[0])
      self.failUnlessEqual("second%s" % os.linesep, output[1])

   def testExecuteCommand_027(self):
      """
      Execute a command that should fail, returnOutput=True
      Do this all bundled into the command list, just to check that this works as expected.
      Command-line: python -c "import sys; print ''; sys.exit(1)"
      """
      command=["python", "-c", "import sys; print ''; sys.exit(1)", ]
      args=[]
      (result, output) = executeCommand(command, args, returnOutput=True)
      self.failIfEqual(0, result)
      self.failUnlessEqual(1, len(output))
      self.failUnlessEqual(os.linesep, output[0])

   def testExecuteCommand_028(self):
      """
      Execute a command that should fail, more arguments, returnOutput=True
      Do this all bundled into the command list, just to check that this works as expected.
      Command-line: python -c "import sys; print '%s' % sys.argv[1]; print '%s' % sys.argv[2]; sys.exit(1)" first second
      """
      command=["python", "-c", "import sys; print '%s' % sys.argv[1]; print '%s' % sys.argv[2]; sys.exit(1)", "first", "second", ]
      args=[]
      (result, output) = executeCommand(command, args, returnOutput=True)
      self.failIfEqual(0, result)
      self.failUnlessEqual(2, len(output))
      self.failUnlessEqual("first%s" % os.linesep, output[0])
      self.failUnlessEqual("second%s" % os.linesep, output[1])

   def testExecuteCommand_030(self):
      """
      Execute a command that should succeed, no arguments, returnOutput=False, ignoring stderr.
      Command-line: echo
      """
      if platformHasEcho():
         command=["echo", ]
         args=[]
         (result, output) = executeCommand(command, args, returnOutput=False, ignoreStderr=True)
         self.failUnlessEqual(0, result)
         self.failUnlessEqual(None, output)

   def testExecuteCommand_031(self):
      """
      Execute a command that should succeed, one argument, returnOutput=False, ignoring stderr.
      Command-line: python -V
      """
      command=["python", ]
      args=["-V", ]
      (result, output) = executeCommand(command, args, returnOutput=False, ignoreStderr=True)
      self.failUnlessEqual(0, result)
      self.failUnlessEqual(None, output)

   def testExecuteCommand_032(self):
      """
      Execute a command that should succeed, two arguments, returnOutput=False, ignoring stderr.
      Command-line: python -c "import sys; print sys.argv[1:]; sys.exit(0)"
      """
      command=["python", ]
      args=["-c", "import sys; print sys.argv[1:]; sys.exit(0)", ]
      (result, output) = executeCommand(command, args, returnOutput=False, ignoreStderr=True)
      self.failUnlessEqual(0, result)
      self.failUnlessEqual(None, output)

   def testExecuteCommand_033(self):
      """
      Execute a command that should succeed, three arguments, returnOutput=False, ignoring stderr.
      Command-line: python -c "import sys; print sys.argv[1:]; sys.exit(0)" first
      """
      command=["python", ]
      args=["-c", "import sys; print sys.argv[1:]; sys.exit(0)", "first", ]
      (result, output) = executeCommand(command, args, returnOutput=False, ignoreStderr=True)
      self.failUnlessEqual(0, result)
      self.failUnlessEqual(None, output)

   def testExecuteCommand_034(self):
      """
      Execute a command that should succeed, four arguments, returnOutput=False, ignoring stderr.
      Command-line: python -c "import sys; print sys.argv[1:]; sys.exit(0)" first second
      """
      command=["python", ]
      args=["-c", "import sys; print sys.argv[1:]; sys.exit(0)", "first", "second", ]
      (result, output) = executeCommand(command, args, returnOutput=False, ignoreStderr=True)
      self.failUnlessEqual(0, result)
      self.failUnlessEqual(None, output)

   def testExecuteCommand_035(self):
      """
      Execute a command that should fail, returnOutput=False, ignoring stderr.
      Command-line: python -c "import sys; print sys.argv[1:]; sys.exit(1)"
      """
      command=["python", ]
      args=["-c", "import sys; print sys.argv[1:]; sys.exit(1)", ]
      (result, output) = executeCommand(command, args, returnOutput=False, ignoreStderr=True)
      self.failIfEqual(0, result)
      self.failUnlessEqual(None, output)

   def testExecuteCommand_036(self):
      """
      Execute a command that should fail, more arguments, returnOutput=False, ignoring stderr.
      Command-line: python -c "import sys; print sys.argv[1:]; sys.exit(1)" first second
      """
      command=["python", ]
      args=["-c", "import sys; print sys.argv[1:]; sys.exit(1)", "first", "second", ]
      (result, output) = executeCommand(command, args, returnOutput=False, ignoreStderr=True)
      self.failIfEqual(0, result)
      self.failUnlessEqual(None, output)

   def testExecuteCommand_037(self):
      """
      Execute a command that should succeed, no arguments, returnOutput=True, ignoring stderr.
      Command-line: echo
      """
      if platformHasEcho():
         command=["echo", ]
         args=[]
         (result, output) = executeCommand(command, args, returnOutput=True, ignoreStderr=True)
         self.failUnlessEqual(0, result)
         self.failUnlessEqual(1, len(output))
         self.failUnlessEqual(os.linesep, output[0])

   def testExecuteCommand_038(self):
      """
      Execute a command that should succeed, one argument, returnOutput=True, ignoring stderr.
      Command-line: python -V
      """
      command=["python", ]
      args=["-V", ]
      (result, output) = executeCommand(command, args, returnOutput=True, ignoreStderr=True)
      self.failUnlessEqual(0, result)
      self.failUnlessEqual(0, len(output))

   def testExecuteCommand_039(self):
      """
      Execute a command that should succeed, two arguments, returnOutput=True, ignoring stderr.
      Command-line: python -c "import sys; print ''; sys.exit(0)"
      """
      command=["python", ]
      args=["-c", "import sys; print ''; sys.exit(0)", ]
      (result, output) = executeCommand(command, args, returnOutput=True, ignoreStderr=True)
      self.failUnlessEqual(0, result)
      self.failUnlessEqual(1, len(output))
      self.failUnlessEqual(os.linesep, output[0])

   def testExecuteCommand_040(self):
      """
      Execute a command that should succeed, three arguments, returnOutput=True, ignoring stderr.
      Command-line: python -c "import sys; print '%s' % (sys.argv[1]); sys.exit(0)" first
      """
      command=["python", ]
      args=["-c", "import sys; print '%s' % (sys.argv[1]); sys.exit(0)", "first", ]
      (result, output) = executeCommand(command, args, returnOutput=True, ignoreStderr=True)
      self.failUnlessEqual(0, result)
      self.failUnlessEqual(1, len(output))
      self.failUnlessEqual("first%s" % os.linesep, output[0])

   def testExecuteCommand_041(self):
      """
      Execute a command that should succeed, four arguments, returnOutput=True, ignoring stderr.
      Command-line: python -c "import sys; print '%s' % sys.argv[1]; print '%s' % sys.argv[2]; sys.exit(0)" first second
      """
      command=["python", ]
      args=["-c", "import sys; print '%s' % sys.argv[1]; print '%s' % sys.argv[2]; sys.exit(0)", "first", "second", ]
      (result, output) = executeCommand(command, args, returnOutput=True, ignoreStderr=True)
      self.failUnlessEqual(0, result)
      self.failUnlessEqual(2, len(output))
      self.failUnlessEqual("first%s" % os.linesep, output[0])
      self.failUnlessEqual("second%s" % os.linesep, output[1])

   def testExecuteCommand_042(self):
      """
      Execute a command that should fail, returnOutput=True, ignoring stderr.
      Command-line: python -c "import sys; print ''; sys.exit(1)"
      """
      command=["python", ]
      args=["-c", "import sys; print ''; sys.exit(1)", ]
      (result, output) = executeCommand(command, args, returnOutput=True, ignoreStderr=True)
      self.failIfEqual(0, result)
      self.failUnlessEqual(1, len(output))
      self.failUnlessEqual(os.linesep, output[0])

   def testExecuteCommand_043(self):
      """
      Execute a command that should fail, more arguments, returnOutput=True, ignoring stderr.
      Command-line: python -c "import sys; print '%s' % sys.argv[1]; print '%s' % sys.argv[2]; sys.exit(1)" first second
      """
      command=["python", ]
      args=["-c", "import sys; print '%s' % sys.argv[1]; print '%s' % sys.argv[2]; sys.exit(1)", "first", "second", ]
      (result, output) = executeCommand(command, args, returnOutput=True, ignoreStderr=True)
      self.failIfEqual(0, result)
      self.failUnlessEqual(2, len(output))
      self.failUnlessEqual("first%s" % os.linesep, output[0])
      self.failUnlessEqual("second%s" % os.linesep, output[1])

   def testExecuteCommand_044(self):
      """
      Execute a command that should succeed, no arguments, returnOutput=False, ignoring stderr.
      Do this all bundled into the command list, just to check that this works as expected.
      Command-line: echo
      """
      if platformHasEcho():
         command=["echo", ]
         args=[]
         (result, output) = executeCommand(command, args, returnOutput=False, ignoreStderr=True)
         self.failUnlessEqual(0, result)
         self.failUnlessEqual(None, output)

   def testExecuteCommand_045(self):
      """
      Execute a command that should succeed, one argument, returnOutput=False, ignoring stderr.
      Do this all bundled into the command list, just to check that this works as expected.
      Command-line: python -V
      """
      command=["python", "-V", ]
      args=[]
      (result, output) = executeCommand(command, args, returnOutput=False, ignoreStderr=True)
      self.failUnlessEqual(0, result)
      self.failUnlessEqual(None, output)

   def testExecuteCommand_046(self):
      """
      Execute a command that should succeed, two arguments, returnOutput=False, ignoring stderr.
      Do this all bundled into the command list, just to check that this works as expected.
      Command-line: python -c "import sys; print sys.argv[1:]; sys.exit(0)"
      """
      command=["python", "-c", "import sys; print sys.argv[1:]; sys.exit(0)", ]
      args=[]
      (result, output) = executeCommand(command, args, returnOutput=False, ignoreStderr=True)
      self.failUnlessEqual(0, result)
      self.failUnlessEqual(None, output)

   def testExecuteCommand_047(self):
      """
      Execute a command that should succeed, three arguments, returnOutput=False, ignoring stderr.
      Do this all bundled into the command list, just to check that this works as expected.
      Command-line: python -c "import sys; print sys.argv[1:]; sys.exit(0)" first
      """
      command=["python", "-c", "import sys; print sys.argv[1:]; sys.exit(0)", "first", ]
      args=[]
      (result, output) = executeCommand(command, args, returnOutput=False, ignoreStderr=True)
      self.failUnlessEqual(0, result)
      self.failUnlessEqual(None, output)

   def testExecuteCommand_048(self):
      """
      Execute a command that should succeed, four arguments, returnOutput=False, ignoring stderr.
      Do this all bundled into the command list, just to check that this works as expected.
      Command-line: python -c "import sys; print sys.argv[1:]; sys.exit(0)" first second
      """
      command=["python", "-c", "import sys; print sys.argv[1:]; sys.exit(0)", "first", "second", ]
      args=[]
      (result, output) = executeCommand(command, args, returnOutput=False, ignoreStderr=True)
      self.failUnlessEqual(0, result)
      self.failUnlessEqual(None, output)

   def testExecuteCommand_049(self):
      """
      Execute a command that should fail, returnOutput=False, ignoring stderr.
      Do this all bundled into the command list, just to check that this works as expected.
      Command-line: python -c "import sys; print sys.argv[1:]; sys.exit(1)"
      """
      command=["python", "-c", "import sys; print sys.argv[1:]; sys.exit(1)", ]
      args=[]
      (result, output) = executeCommand(command, args, returnOutput=False, ignoreStderr=True)
      self.failIfEqual(0, result)
      self.failUnlessEqual(None, output)

   def testExecuteCommand_050(self):
      """
      Execute a command that should fail, more arguments, returnOutput=False, ignoring stderr.
      Do this all bundled into the command list, just to check that this works as expected.
      Command-line: python -c "import sys; print sys.argv[1:]; sys.exit(1)" first second
      """
      command=["python", "-c", "import sys; print sys.argv[1:]; sys.exit(1)", "first", "second", ]
      args=[]
      (result, output) = executeCommand(command, args, returnOutput=False, ignoreStderr=True)
      self.failIfEqual(0, result)
      self.failUnlessEqual(None, output)

   def testExecuteCommand_051(self):
      """
      Execute a command that should succeed, no arguments, returnOutput=True, ignoring stderr.
      Do this all bundled into the command list, just to check that this works as expected.
      Command-line: echo
      """
      if platformHasEcho():
         command=["echo", ]
         args=[]
         (result, output) = executeCommand(command, args, returnOutput=True, ignoreStderr=True)
         self.failUnlessEqual(0, result)
         self.failUnlessEqual(1, len(output))
         self.failUnlessEqual(os.linesep, output[0])

   def testExecuteCommand_052(self):
      """
      Execute a command that should succeed, one argument, returnOutput=True, ignoring stderr.
      Do this all bundled into the command list, just to check that this works as expected.
      Command-line: python -V
      """
      command=["python", "-V"]
      args=[]
      (result, output) = executeCommand(command, args, returnOutput=True, ignoreStderr=True)
      self.failUnlessEqual(0, result)
      self.failUnlessEqual(0, len(output))

   def testExecuteCommand_053(self):
      """
      Execute a command that should succeed, two arguments, returnOutput=True, ignoring stderr.
      Do this all bundled into the command list, just to check that this works as expected.
      Command-line: python -c "import sys; print ''; sys.exit(0)"
      """
      command=["python", "-c", "import sys; print ''; sys.exit(0)", ]
      args=[]
      (result, output) = executeCommand(command, args, returnOutput=True, ignoreStderr=True)
      self.failUnlessEqual(0, result)
      self.failUnlessEqual(1, len(output))
      self.failUnlessEqual(os.linesep, output[0])

   def testExecuteCommand_054(self):
      """
      Execute a command that should succeed, three arguments, returnOutput=True, ignoring stderr.
      Do this all bundled into the command list, just to check that this works as expected.
      Command-line: python -c "import sys; print '%s' % (sys.argv[1]); sys.exit(0)" first
      """
      command=["python", "-c", "import sys; print '%s' % (sys.argv[1]); sys.exit(0)", "first", ]
      args=[]
      (result, output) = executeCommand(command, args, returnOutput=True, ignoreStderr=True)
      self.failUnlessEqual(0, result)
      self.failUnlessEqual(1, len(output))
      self.failUnlessEqual("first%s" % os.linesep, output[0])

   def testExecuteCommand_055(self):
      """
      Execute a command that should succeed, four arguments, returnOutput=True, ignoring stderr.
      Do this all bundled into the command list, just to check that this works as expected.
      Command-line: python -c "import sys; print '%s' % sys.argv[1]; print '%s' % sys.argv[2]; sys.exit(0)" first second
      """
      command=["python", "-c", "import sys; print '%s' % sys.argv[1]; print '%s' % sys.argv[2]; sys.exit(0)", "first", "second", ]
      args=[]
      (result, output) = executeCommand(command, args, returnOutput=True, ignoreStderr=True)
      self.failUnlessEqual(0, result)
      self.failUnlessEqual(2, len(output))
      self.failUnlessEqual("first%s" % os.linesep, output[0])
      self.failUnlessEqual("second%s" % os.linesep, output[1])

   def testExecuteCommand_056(self):
      """
      Execute a command that should fail, returnOutput=True, ignoring stderr.
      Do this all bundled into the command list, just to check that this works as expected.
      Command-line: python -c "import sys; print ''; sys.exit(1)"
      """
      command=["python", "-c", "import sys; print ''; sys.exit(1)", ]
      args=[]
      (result, output) = executeCommand(command, args, returnOutput=True, ignoreStderr=True)
      self.failIfEqual(0, result)
      self.failUnlessEqual(1, len(output))
      self.failUnlessEqual(os.linesep, output[0])

   def testExecuteCommand_057(self):
      """
      Execute a command that should fail, more arguments, returnOutput=True, ignoring stderr.
      Do this all bundled into the command list, just to check that this works as expected.
      Command-line: python -c "import sys; print '%s' % sys.argv[1]; print '%s' % sys.argv[2]; sys.exit(1)" first second
      """
      command=["python", "-c", "import sys; print '%s' % sys.argv[1]; print '%s' % sys.argv[2]; sys.exit(1)", "first", "second", ]
      args=[]
      (result, output) = executeCommand(command, args, returnOutput=True, ignoreStderr=True)
      self.failIfEqual(0, result)
      self.failUnlessEqual(2, len(output))
      self.failUnlessEqual("first%s" % os.linesep, output[0])
      self.failUnlessEqual("second%s" % os.linesep, output[1])

   def testExecuteCommand_058(self):
      """
      Execute a command that should succeed, no arguments, returnOutput=False, using outputFile.
      Do this all bundled into the command list, just to check that this works as expected.
      Command-line: echo
      """
      if platformHasEcho():
         command=["echo", ]
         args=[]

         filename = self.getTempfile()
         outputFile = open(filename, "w")
         try:
            result = executeCommand(command, args, returnOutput=False, outputFile=outputFile)[0]
         finally:
            outputFile.close()
         self.failUnlessEqual(0, result)
         self.failUnless(os.path.exists(filename))
         output = open(filename).readlines()

         self.failUnlessEqual(1, len(output))
         self.failUnlessEqual(os.linesep, output[0])

   def testExecuteCommand_059(self):
      """
      Execute a command that should succeed, one argument, returnOutput=False, using outputFile.
      Do this all bundled into the command list, just to check that this works as expected.
      Command-line: python -V
      """
      command=["python", "-V"]
      args=[]

      filename = self.getTempfile()
      outputFile = open(filename, "w")
      try:
         result = executeCommand(command, args, returnOutput=False, outputFile=outputFile)[0]
      finally:
         outputFile.close()
      self.failUnlessEqual(0, result)
      self.failUnless(os.path.exists(filename))
      output = open(filename).readlines()

      self.failUnlessEqual(1, len(output))
      self.failUnless(output[0].startswith("Python"))

   def testExecuteCommand_060(self):
      """
      Execute a command that should succeed, two arguments, returnOutput=False, using outputFile.
      Do this all bundled into the command list, just to check that this works as expected.
      Command-line: python -c "import sys; print ''; sys.exit(0)"
      """
      command=["python", "-c", "import sys; print ''; sys.exit(0)", ]
      args=[]

      filename = self.getTempfile()
      outputFile = open(filename, "w")
      try:
         result = executeCommand(command, args, returnOutput=False, outputFile=outputFile)[0]
      finally:
         outputFile.close()
      self.failUnlessEqual(0, result)
      self.failUnless(os.path.exists(filename))
      output = open(filename).readlines()

      self.failUnlessEqual(1, len(output))
      self.failUnlessEqual(os.linesep, output[0])

   def testExecuteCommand_061(self):
      """
      Execute a command that should succeed, three arguments, returnOutput=False, using outputFile.
      Do this all bundled into the command list, just to check that this works as expected.
      Command-line: python -c "import sys; print '%s' % (sys.argv[1]); sys.exit(0)" first
      """
      command=["python", "-c", "import sys; print '%s' % (sys.argv[1]); sys.exit(0)", "first", ]
      args=[]

      filename = self.getTempfile()
      outputFile = open(filename, "w")
      try:
         result = executeCommand(command, args, returnOutput=False, outputFile=outputFile)[0]
      finally:
         outputFile.close()
      self.failUnlessEqual(0, result)
      self.failUnless(os.path.exists(filename))
      output = open(filename).readlines()

      self.failUnlessEqual(1, len(output))
      self.failUnlessEqual("first%s" % os.linesep, output[0])

   def testExecuteCommand_062(self):
      """
      Execute a command that should succeed, four arguments, returnOutput=False, using outputFile.
      Do this all bundled into the command list, just to check that this works as expected.
      Command-line: python -c "import sys; print '%s' % sys.argv[1]; print '%s' % sys.argv[2]; sys.exit(0)" first second
      """
      command=["python", "-c", "import sys; print '%s' % sys.argv[1]; print '%s' % sys.argv[2]; sys.exit(0)", "first", "second", ]
      args=[]

      filename = self.getTempfile()
      outputFile = open(filename, "w")
      try:
         result = executeCommand(command, args, returnOutput=False, outputFile=outputFile)[0]
      finally:
         outputFile.close()
      self.failUnlessEqual(0, result)
      self.failUnless(os.path.exists(filename))
      output = open(filename).readlines()

      self.failUnlessEqual(2, len(output))
      self.failUnlessEqual("first%s" % os.linesep, output[0])
      self.failUnlessEqual("second%s" % os.linesep, output[1])

   def testExecuteCommand_063(self):
      """
      Execute a command that should fail, returnOutput=False, using outputFile.
      Do this all bundled into the command list, just to check that this works as expected.
      Command-line: python -c "import sys; print ''; sys.exit(1)"
      """
      command=["python", "-c", "import sys; print ''; sys.exit(1)", ]
      args=[]

      filename = self.getTempfile()
      outputFile = open(filename, "w")
      try:
         result = executeCommand(command, args, returnOutput=False, outputFile=outputFile)[0]
      finally:
         outputFile.close()
      self.failIfEqual(0, result)
      self.failUnless(os.path.exists(filename))
      output = open(filename).readlines()

      self.failUnlessEqual(1, len(output))
      self.failUnlessEqual(os.linesep, output[0])

   def testExecuteCommand_064(self):
      """
      Execute a command that should fail, more arguments, returnOutput=False, using outputFile.
      Do this all bundled into the command list, just to check that this works as expected.
      Command-line: python -c "import sys; print '%s' % sys.argv[1]; print '%s' % sys.argv[2]; sys.exit(1)" first second
      """
      command=["python", "-c", "import sys; print '%s' % sys.argv[1]; print '%s' % sys.argv[2]; sys.exit(1)", "first", "second", ]
      args=[]

      filename = self.getTempfile()
      outputFile = open(filename, "w")
      try:
         result = executeCommand(command, args, returnOutput=False, outputFile=outputFile)[0]
      finally:
         outputFile.close()
      self.failIfEqual(0, result)
      self.failUnless(os.path.exists(filename))
      output = open(filename).readlines()

      self.failUnlessEqual(2, len(output))
      self.failUnlessEqual("first%s" % os.linesep, output[0])
      self.failUnlessEqual("second%s" % os.linesep, output[1])

   def testExecuteCommand_065(self):
      """
      Execute a command with a huge amount of output all on stdout.  The output
      should contain only data on stdout, and ignoreStderr should be True.
      This test helps confirm that the function doesn't hang when there is
      either a lot of data or a lot of data to ignore.
      """
      lotsoflines = self.resources['lotsoflines.py']
      command=["python", lotsoflines, "stdout", ]
      args = []

      filename = self.getTempfile()
      outputFile = open(filename, "w")
      try:
         result = executeCommand(command, args, ignoreStderr=True, returnOutput=False, outputFile=outputFile)[0]
      finally:
         outputFile.close()
      self.failUnlessEqual(0, result)

      length = 0
      contents = open(filename)
      for i in contents:
         length += 1

      self.failUnlessEqual(100000, length)

   def testExecuteCommand_066(self):
      """
      Execute a command with a huge amount of output all on stdout.  The output
      should contain only data on stdout, and ignoreStderr should be False.
      This test helps confirm that the function doesn't hang when there is
      either a lot of data or a lot of data to ignore.
      """
      lotsoflines = self.resources['lotsoflines.py']
      command=["python", lotsoflines, "stdout", ]
      args = []

      filename = self.getTempfile()
      outputFile = open(filename, "w")
      try:
         result = executeCommand(command, args, ignoreStderr=False, returnOutput=False, outputFile=outputFile)[0]
      finally:
         outputFile.close()
      self.failUnlessEqual(0, result)

      length = 0
      contents = open(filename)
      for i in contents:
         length += 1

      self.failUnlessEqual(100000, length)

   def testExecuteCommand_067(self):
      """
      Execute a command with a huge amount of output all on stdout.  The output
      should contain only data on stderr, and ignoreStderr should be True.
      This test helps confirm that the function doesn't hang when there is
      either a lot of data or a lot of data to ignore.
      """
      lotsoflines = self.resources['lotsoflines.py']
      command=["python", lotsoflines, "stderr", ]
      args = []

      filename = self.getTempfile()
      outputFile = open(filename, "w")
      try:
         result = executeCommand(command, args, ignoreStderr=True, returnOutput=False, outputFile=outputFile)[0]
      finally:
         outputFile.close()
      self.failUnlessEqual(0, result)

      length = 0
      contents = open(filename)
      for i in contents:
         length += 1

      self.failUnlessEqual(0, length)

   def testExecuteCommand_068(self):
      """
      Execute a command with a huge amount of output all on stdout.  The output
      should contain only data on stdout, and ignoreStderr should be False.
      This test helps confirm that the function doesn't hang when there is
      either a lot of data or a lot of data to ignore.
      """
      lotsoflines = self.resources['lotsoflines.py']
      command=["python", lotsoflines, "stderr", ]
      args = []

      filename = self.getTempfile()
      outputFile = open(filename, "w")
      try:
         result = executeCommand(command, args, ignoreStderr=False, returnOutput=False, outputFile=outputFile)[0]
      finally:
         outputFile.close()
      self.failUnlessEqual(0, result)

      length = 0
      contents = open(filename)
      for i in contents:
         length += 1

      self.failUnlessEqual(100000, length)

   def testExecuteCommand_069(self):
      """
      Execute a command with a huge amount of output all on stdout.  The output
      should contain data on stdout and stderr, and ignoreStderr should be
      True.  This test helps confirm that the function doesn't hang when there
      is either a lot of data or a lot of data to ignore.
      """
      lotsoflines = self.resources['lotsoflines.py']
      command=["python", lotsoflines, "both", ]
      args = []

      filename = self.getTempfile()
      outputFile = open(filename, "w")
      try:
         result = executeCommand(command, args, ignoreStderr=True, returnOutput=False, outputFile=outputFile)[0]
      finally:
         outputFile.close()
      self.failUnlessEqual(0, result)

      length = 0
      contents = open(filename)
      for i in contents:
         length += 1

      self.failUnlessEqual(100000, length)

   def testExecuteCommand_070(self):
      """
      Execute a command with a huge amount of output all on stdout.  The output
      should contain data on stdout and stderr, and ignoreStderr should be
      False.  This test helps confirm that the function doesn't hang when there
      is either a lot of data or a lot of data to ignore.
      """
      lotsoflines = self.resources['lotsoflines.py']
      command=["python", lotsoflines, "both", ]
      args = []

      filename = self.getTempfile()
      outputFile = open(filename, "w")
      try:
         result = executeCommand(command, args, ignoreStderr=False, returnOutput=False, outputFile=outputFile)[0]
      finally:
         outputFile.close()
      self.failUnlessEqual(0, result)

      length = 0
      contents = open(filename)
      for i in contents:
         length += 1

      self.failUnlessEqual(100000*2, length)


   ####################
   # Test encodePath() 
   ####################
         
   def testEncodePath_002(self):
      """
      Test with a simple string, empty.
      """
      path = ""
      safePath = encodePath(path)
      self.failUnless(isinstance(safePath, str))
      self.failUnlessEqual(path, safePath)

   def testEncodePath_003(self):
      """
      Test with an simple string, an ascii word.
      """
      path = "whatever"
      safePath = encodePath(path)
      self.failUnless(isinstance(safePath, str))
      self.failUnlessEqual(path, safePath)

   def testEncodePath_004(self):
      """
      Test with simple string, a complete path.
      """
      path = "/usr/share/doc/xmltv/README.Debian"
      safePath = encodePath(path)
      self.failUnless(isinstance(safePath, str))
      self.failUnlessEqual(path, safePath)

   def testEncodePath_005(self):
      """
      Test with simple string, a non-ascii path.
      """
      path = "\xe2\x99\xaa\xe2\x99\xac"
      safePath = encodePath(path)
      self.failUnless(isinstance(safePath, str))
      self.failUnlessEqual(path, safePath)

   def testEncodePath_006(self):
      """
      Test with a simple string, empty.
      """
      path = u""
      safePath = encodePath(path)
      self.failUnless(isinstance(safePath, str))
      self.failUnlessEqual(path, safePath)

   def testEncodePath_007(self):
      """
      Test with an simple string, an ascii word.
      """
      path = u"whatever"
      safePath = encodePath(path)
      self.failUnless(isinstance(safePath, str))
      self.failUnlessEqual(path, safePath)

   def testEncodePath_008(self):
      """
      Test with simple string, a complete path.
      """
      path = u"/usr/share/doc/xmltv/README.Debian"
      safePath = encodePath(path)
      self.failUnless(isinstance(safePath, str))
      self.failUnlessEqual(path, safePath)

   def testEncodePath_009(self):
      """
      Test with simple string, a non-ascii path.

      The result is different for a UTF-8 encoding than other non-ANSI
      encodings.  However, opening the original path and then the encoded path
      seems to result in the exact same file on disk, so the test is valid.  
      """
      encoding = sys.getfilesystemencoding() or sys.getdefaultencoding()
      if encoding != 'mbcs' and encoding.find("ANSI") != 0:    # test can't work on some filesystems
         path = u"\xe2\x99\xaa\xe2\x99\xac"
         safePath = encodePath(path)
         self.failUnless(isinstance(safePath, str))
         if encoding == "utf-8":
            self.failUnlessEqual('\xc3\xa2\xc2\x99\xc2\xaa\xc3\xa2\xc2\x99\xc2\xac', safePath)
         else:
            self.failUnlessEqual("\xe2\x99\xaa\xe2\x99\xac", safePath)


#######################################################################
# Suite definition
#######################################################################

def suite():
   """Returns a suite containing all the test cases in this module."""
   return unittest.TestSuite((
                              unittest.makeSuite(TestUnorderedList, 'test'),
                              unittest.makeSuite(TestPathResolverSingleton, 'test'),
                              unittest.makeSuite(TestFunctions, 'test'),
                            ))


########################################################################
# Module entry point
########################################################################

# When this module is executed from the command-line, run its tests
if __name__ == '__main__':
   unittest.main()

