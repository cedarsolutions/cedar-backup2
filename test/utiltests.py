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
# Purpose  : Tests utility functionality.
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# This file was created with a width of 132 characters, and NO tabs.

########################################################################
# Module documentation
########################################################################

"""
Unit tests for CedarBackup2/util.py.

Code Coverage
=============

   This module contains individual tests for the public functions
   and classes implemented in util.py.

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

@author Kenneth J. Pronovici <pronovic@ieee.org>
"""


########################################################################
# Import modules and do runtime validations
########################################################################

# Import standard modules
import unittest
from CedarBackup2.util import executeCommand


#######################################################################
# Test Case Classes
#######################################################################

######################
# TestFunctions class
######################

class TestFunctions(unittest.TestCase):

   """Tests for the various public functions."""

   ################
   # Setup methods
   ################

   def setUp(self):
      pass

   def tearDown(self):
      pass


   ######################################
   # Tests for executeCommand() function
   ######################################
         
   def testExecuteCommand_001(self):
      """
      Execute a command that should succeed, no arguments, returnOutput=False
      Command-line: echo
      """
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
      command=["echo", ]
      args=[]
      (result, output) = executeCommand(command, args, returnOutput=True)
      self.failUnlessEqual(0, result)
      self.failUnlessEqual(1, len(output))
      self.failUnlessEqual("\n", output[0])

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
      self.failUnlessEqual("\n", output[0])

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
      self.failUnlessEqual("first\n", output[0])

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
      self.failUnlessEqual("first\n", output[0])
      self.failUnlessEqual("second\n", output[1])

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
      self.failUnlessEqual("\n", output[0])

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
      self.failUnlessEqual("first\n", output[0])
      self.failUnlessEqual("second\n", output[1])

   def testExecuteCommand_015(self):
      """
      Execute a command that should succeed, no arguments, returnOutput=False
      Do this all bundled into the command list, just to check that this works as expected.
      Command-line: echo
      """
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
      command=["echo", ]
      args=[]
      (result, output) = executeCommand(command, args, returnOutput=True)
      self.failUnlessEqual(0, result)
      self.failUnlessEqual(1, len(output))
      self.failUnlessEqual("\n", output[0])

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
      self.failUnlessEqual("\n", output[0])

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
      self.failUnlessEqual("first\n", output[0])

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
      self.failUnlessEqual("first\n", output[0])
      self.failUnlessEqual("second\n", output[1])

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
      self.failUnlessEqual("\n", output[0])

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
      self.failUnlessEqual("first\n", output[0])
      self.failUnlessEqual("second\n", output[1])


#######################################################################
# Suite definition
#######################################################################

def suite():
   """Returns a suite containing all the test cases in this module."""
   return unittest.TestSuite((
                              unittest.makeSuite(TestFunctions, 'test'),
                            ))


########################################################################
# Module entry point
########################################################################

# When this module is executed from the command-line, run its tests
if __name__ == '__main__':
   unittest.main()

