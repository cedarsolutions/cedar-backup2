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
# Copyright (c) 2004-2005 Kenneth J. Pronovici.
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
# Purpose  : Tests command-line interface functionality.
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# This file was created with a width of 132 characters, and NO tabs.

########################################################################
# Module documentation
########################################################################

"""
Unit tests for CedarBackup2/cli.py.

Code Coverage
=============

   This module contains individual tests for the many of the public functions
   and classes implemented in cli.py.  Where possible, we test functions that
   print output by passing a custom file descriptor.  Sometimes, we only ensure
   that a function or method runs without failure, and we don't validate what
   its result is or what it prints out.

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
   build environment.  There is a no need to use a CLITESTS_FULL environment
   variable to provide a "reduced feature set" test suite as for some of the
   other test modules.

@author Kenneth J. Pronovici <pronovic@ieee.org>
"""


########################################################################
# Import modules and do runtime validations
########################################################################

import unittest
from StringIO import StringIO
from getopt import GetoptError
from CedarBackup2.testutil import failUnlessAssignRaises
from CedarBackup2.config import ExtendedAction
from CedarBackup2.cli import _usage, _version
from CedarBackup2.cli import Options
from CedarBackup2.cli import _ActionSet
from CedarBackup2.action import executeCollect, executeStage, executeStore, executePurge, executeRebuild, executeValidate


#######################################################################
# Test Case Classes
#######################################################################

######################
# TestFunctions class
######################

class TestFunctions(unittest.TestCase):

   """Tests for the public functions."""

   ################
   # Setup methods
   ################

   def setUp(self):
      pass

   def tearDown(self):
      pass


   ##################
   # Utility methods
   ##################

   def captureOutput(self, callable):
      """
      Captures the output (stdout, stderr) of a function or a method.

      Some of our functions don't do anything other than just print output.  We
      need a way to test these functions (at least nominally) but we don't want
      any of the output spoiling the test suite output.

      This function just creates a dummy file descriptor that can be used as a
      target by the callable function, rather than C{stdout} or C{stderr}.

      @note: This method assumes that C{callable} doesn't take any arguments
      besides keyword argument C{fd} to specify the file descriptor.

      @param callable: Callable function or method.

      @return: Output of function, as one big string.
      """
      fd = StringIO()
      callable(fd=fd)
      result = fd.getvalue()
      fd.close()
      return result


   ########################
   # Test simple functions
   ########################

   def testSimpleFuncs_001(self):
      """
      Test that the _usage() function runs without errors.
      We don't care what the output is, and we don't check.
      """
      self.captureOutput(_usage)

   def testSimpleFuncs_002(self):
      """
      Test that the _version() function runs without errors.
      We don't care what the output is, and we don't check.
      """
      self.captureOutput(_version)


####################
# TestOptions class
####################

class TestOptions(unittest.TestCase):

   """Tests for the Options class."""

   ################
   # Setup methods
   ################

   def setUp(self):
      pass

   def tearDown(self):
      pass


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
      obj = Options()
      obj.__repr__()
      obj.__str__()


   ##################################
   # Test constructor and attributes
   ##################################

   def testConstructor_001(self):
      """
      Test constructor with no arguments.
      """
      options = Options()
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_002(self):
      """
      Test constructor with validate=False, no other arguments.
      """
      options = Options(validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_003(self):
      """
      Test constructor with argumentList=[], validate=False.
      """
      options = Options(argumentList=[], validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_004(self):
      """
      Test constructor with argumentString="", validate=False.
      """
      options = Options(argumentString="", validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_005(self):
      """
      Test constructor with argumentList=["--help", ], validate=False.
      """
      options = Options(argumentList=["--help", ], validate=False)
      self.failUnlessEqual(True, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_006(self):
      """
      Test constructor with argumentString="--help", validate=False.
      """
      options = Options(argumentString="--help", validate=False)
      self.failUnlessEqual(True, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_007(self):
      """
      Test constructor with argumentList=["-h", ], validate=False.
      """
      options = Options(argumentList=["-h", ], validate=False)
      self.failUnlessEqual(True, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_008(self):
      """
      Test constructor with argumentString="-h", validate=False.
      """
      options = Options(argumentString="-h", validate=False)
      self.failUnlessEqual(True, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_009(self):
      """
      Test constructor with argumentList=["--version", ], validate=False.
      """
      options = Options(argumentList=["--version", ], validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(True, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_010(self):
      """
      Test constructor with argumentString="--version", validate=False.
      """
      options = Options(argumentString="--version", validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(True, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_011(self):
      """
      Test constructor with argumentList=["-V", ], validate=False.
      """
      options = Options(argumentList=["-V", ], validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(True, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_012(self):
      """
      Test constructor with argumentString="-V", validate=False.
      """
      options = Options(argumentString="-V", validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(True, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_013(self):
      """
      Test constructor with argumentList=["--verbose", ], validate=False.
      """
      options = Options(argumentList=["--verbose", ], validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(True, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_014(self):
      """
      Test constructor with argumentString="--verbose", validate=False.
      """
      options = Options(argumentString="--verbose", validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(True, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_015(self):
      """
      Test constructor with argumentList=["-b", ], validate=False.
      """
      options = Options(argumentList=["-b", ], validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(True, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_016(self):
      """
      Test constructor with argumentString="-b", validate=False.
      """
      options = Options(argumentString="-b", validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(True, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_017(self):
      """
      Test constructor with argumentList=["--quiet", ], validate=False.
      """
      options = Options(argumentList=["--quiet", ], validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(True, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_018(self):
      """
      Test constructor with argumentString="--quiet", validate=False.
      """
      options = Options(argumentString="--quiet", validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(True, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_019(self):
      """
      Test constructor with argumentList=["-q", ], validate=False.
      """
      options = Options(argumentList=["-q", ], validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(True, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_020(self):
      """
      Test constructor with argumentString="-q", validate=False.
      """
      options = Options(argumentString="-q", validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(True, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_021(self):
      """
      Test constructor with argumentList=["--config", ], validate=False.
      """
      self.failUnlessRaises(GetoptError, Options, argumentList=["--config", ], validate=False)

   def testConstructor_022(self):
      """
      Test constructor with argumentString="--config", validate=False.
      """
      self.failUnlessRaises(GetoptError, Options, argumentString="--config", validate=False)

   def testConstructor_023(self):
      """
      Test constructor with argumentList=["-c", ], validate=False.
      """
      self.failUnlessRaises(GetoptError, Options, argumentList=["-c", ], validate=False)

   def testConstructor_024(self):
      """
      Test constructor with argumentString="-c", validate=False.
      """
      self.failUnlessRaises(GetoptError, Options, argumentString="-c", validate=False)

   def testConstructor_025(self):
      """
      Test constructor with argumentList=["--config", "something", ], validate=False.
      """
      options = Options(argumentList=["--config", "something", ], validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual("something", options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_026(self):
      """
      Test constructor with argumentString="--config something", validate=False.
      """
      options = Options(argumentString="--config something", validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual("something", options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_027(self):
      """
      Test constructor with argumentList=["-c", "something", ], validate=False.
      """
      options = Options(argumentList=["-c", "something", ], validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual("something", options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_028(self):
      """
      Test constructor with argumentString="-c something", validate=False.
      """
      options = Options(argumentString="-c something", validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual("something", options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_029(self):
      """
      Test constructor with argumentList=["--full", ], validate=False.
      """
      options = Options(argumentList=["--full", ], validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(True, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_030(self):
      """
      Test constructor with argumentString="--full", validate=False.
      """
      options = Options(argumentString="--full", validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(True, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_031(self):
      """
      Test constructor with argumentList=["-f", ], validate=False.
      """
      options = Options(argumentList=["-f", ], validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(True, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_032(self):
      """
      Test constructor with argumentString="-f", validate=False.
      """
      options = Options(argumentString="-f", validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(True, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_033(self):
      """
      Test constructor with argumentList=["--logfile", ], validate=False.
      """
      self.failUnlessRaises(GetoptError, Options, argumentList=["--logfile", ], validate=False)

   def testConstructor_034(self):
      """
      Test constructor with argumentString="--logfile", validate=False.
      """
      self.failUnlessRaises(GetoptError, Options, argumentString="--logfile", validate=False)

   def testConstructor_035(self):
      """
      Test constructor with argumentList=["-l", ], validate=False.
      """
      self.failUnlessRaises(GetoptError, Options, argumentList=["-l", ], validate=False)

   def testConstructor_036(self):
      """
      Test constructor with argumentString="-l", validate=False.
      """
      self.failUnlessRaises(GetoptError, Options, argumentString="-l", validate=False)

   def testConstructor_037(self):
      """
      Test constructor with argumentList=["--logfile", "something", ], validate=False.
      """
      options = Options(argumentList=["--logfile", "something", ], validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual("something", options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_038(self):
      """
      Test constructor with argumentString="--logfile something", validate=False.
      """
      options = Options(argumentString="--logfile something", validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual("something", options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_039(self):
      """
      Test constructor with argumentList=["-l", "something", ], validate=False.
      """
      options = Options(argumentList=["-l", "something", ], validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual("something", options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_040(self):
      """
      Test constructor with argumentString="-l something", validate=False.
      """
      options = Options(argumentString="-l something", validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual("something", options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_041(self):
      """
      Test constructor with argumentList=["--owner", ], validate=False.
      """
      self.failUnlessRaises(GetoptError, Options, argumentList=["--owner", ], validate=False)

   def testConstructor_042(self):
      """
      Test constructor with argumentString="--owner", validate=False.
      """
      self.failUnlessRaises(GetoptError, Options, argumentString="--owner", validate=False)

   def testConstructor_043(self):
      """
      Test constructor with argumentList=["-o", ], validate=False.
      """
      self.failUnlessRaises(GetoptError, Options, argumentList=["-o", ], validate=False)

   def testConstructor_044(self):
      """
      Test constructor with argumentString="-o", validate=False.
      """
      self.failUnlessRaises(GetoptError, Options, argumentString="-o", validate=False)

   def testConstructor_045(self):
      """
      Test constructor with argumentList=["--owner", "something", ], validate=False.
      """
      self.failUnlessRaises(ValueError, Options, argumentList=["--owner", "something", ], validate=False)

   def testConstructor_046(self):
      """
      Test constructor with argumentString="--owner something", validate=False.
      """
      self.failUnlessRaises(ValueError, Options, argumentString="--owner something", validate=False)

   def testConstructor_047(self):
      """
      Test constructor with argumentList=["-o", "something", ], validate=False.
      """
      self.failUnlessRaises(ValueError, Options, argumentList=["-o", "something", ], validate=False)

   def testConstructor_048(self):
      """
      Test constructor with argumentString="-o something", validate=False.
      """
      self.failUnlessRaises(ValueError, Options, argumentString="-o something", validate=False)

   def testConstructor_049(self):
      """
      Test constructor with argumentList=["--owner", "a:b", ], validate=False.
      """
      options = Options(argumentList=["--owner", "a:b", ], validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(("a", "b"), options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_050(self):
      """
      Test constructor with argumentString="--owner a:b", validate=False.
      """
      options = Options(argumentString="--owner a:b", validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(("a", "b"), options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_051(self):
      """
      Test constructor with argumentList=["-o", "a:b", ], validate=False.
      """
      options = Options(argumentList=["-o", "a:b", ], validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(("a", "b"), options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_052(self):
      """
      Test constructor with argumentString="-o a:b", validate=False.
      """
      options = Options(argumentString="-o a:b", validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(("a", "b"), options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_053(self):
      """
      Test constructor with argumentList=["--mode", ], validate=False.
      """
      self.failUnlessRaises(GetoptError, Options, argumentList=["--mode", ], validate=False)

   def testConstructor_054(self):
      """
      Test constructor with argumentString="--mode", validate=False.
      """
      self.failUnlessRaises(GetoptError, Options, argumentString="--mode", validate=False)

   def testConstructor_055(self):
      """
      Test constructor with argumentList=["-m", ], validate=False.
      """
      self.failUnlessRaises(GetoptError, Options, argumentList=["-m", ], validate=False)

   def testConstructor_056(self):
      """
      Test constructor with argumentString="-m", validate=False.
      """
      self.failUnlessRaises(GetoptError, Options, argumentString="-m", validate=False)

   def testConstructor_057(self):
      """
      Test constructor with argumentList=["--mode", "something", ], validate=False.
      """
      self.failUnlessRaises(ValueError, Options, argumentList=["--mode", "something", ], validate=False)

   def testConstructor_058(self):
      """
      Test constructor with argumentString="--mode something", validate=False.
      """
      self.failUnlessRaises(ValueError, Options, argumentString="--mode something", validate=False)

   def testConstructor_059(self):
      """
      Test constructor with argumentList=["-m", "something", ], validate=False.
      """
      self.failUnlessRaises(ValueError, Options, argumentList=["-m", "something", ], validate=False)

   def testConstructor_060(self):
      """
      Test constructor with argumentString="-m something", validate=False.
      """
      self.failUnlessRaises(ValueError, Options, argumentString="-m something", validate=False)

   def testConstructor_061(self):
      """
      Test constructor with argumentList=["--mode", "631", ], validate=False.
      """
      options = Options(argumentList=["--mode", "631", ], validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(0631, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_062(self):
      """
      Test constructor with argumentString="--mode 631", validate=False.
      """
      options = Options(argumentString="--mode 631", validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(0631, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_063(self):
      """
      Test constructor with argumentList=["-m", "631", ], validate=False.
      """
      options = Options(argumentList=["-m", "631", ], validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(0631, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_064(self):
      """
      Test constructor with argumentString="-m 631", validate=False.
      """
      options = Options(argumentString="-m 631", validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(0631, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_065(self):
      """
      Test constructor with argumentList=["--output", ], validate=False.
      """
      options = Options(argumentList=["--output", ], validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(True, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_066(self):
      """
      Test constructor with argumentString="--output", validate=False.
      """
      options = Options(argumentString="--output", validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(True, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_067(self):
      """
      Test constructor with argumentList=["-O", ], validate=False.
      """
      options = Options(argumentList=["-O", ], validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(True, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_068(self):
      """
      Test constructor with argumentString="-O", validate=False.
      """
      options = Options(argumentString="-O", validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(True, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_069(self):
      """
      Test constructor with argumentList=["--debug", ], validate=False.
      """
      options = Options(argumentList=["--debug", ], validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(True, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_070(self):
      """
      Test constructor with argumentString="--debug", validate=False.
      """
      options = Options(argumentString="--debug", validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(True, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_071(self):
      """
      Test constructor with argumentList=["-d", ], validate=False.
      """
      options = Options(argumentList=["-d", ], validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(True, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_072(self):
      """
      Test constructor with argumentString="-d", validate=False.
      """
      options = Options(argumentString="-d", validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(True, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_073(self):
      """
      Test constructor with argumentList=["--stack", ], validate=False.
      """
      options = Options(argumentList=["--stack", ], validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(True, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_074(self):
      """
      Test constructor with argumentString="--stack", validate=False.
      """
      options = Options(argumentString="--stack", validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(True, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_075(self):
      """
      Test constructor with argumentList=["-s", ], validate=False.
      """
      options = Options(argumentList=["-s", ], validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(True, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_076(self):
      """
      Test constructor with argumentString="-s", validate=False.
      """
      options = Options(argumentString="-s", validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(True, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_077(self):
      """
      Test constructor with argumentList=["all", ], validate=False.
      """
      options = Options(argumentList=["all", ], validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual(["all", ], options.actions)

   def testConstructor_078(self):
      """
      Test constructor with argumentString="all", validate=False.
      """
      options = Options(argumentString="all", validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual(["all", ], options.actions)

   def testConstructor_079(self):
      """
      Test constructor with argumentList=["collect", ], validate=False.
      """
      options = Options(argumentList=["collect", ], validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual(["collect", ], options.actions)

   def testConstructor_080(self):
      """
      Test constructor with argumentString="collect", validate=False.
      """
      options = Options(argumentString="collect", validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual(["collect", ], options.actions)

   def testConstructor_081(self):
      """
      Test constructor with argumentList=["stage", ], validate=False.
      """
      options = Options(argumentList=["stage", ], validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual(["stage", ], options.actions)

   def testConstructor_082(self):
      """
      Test constructor with argumentString="stage", validate=False.
      """
      options = Options(argumentString="stage", validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual(["stage", ], options.actions)

   def testConstructor_083(self):
      """
      Test constructor with argumentList=["store", ], validate=False.
      """
      options = Options(argumentList=["store", ], validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual(["store", ], options.actions)

   def testConstructor_084(self):
      """
      Test constructor with argumentString="store", validate=False.
      """
      options = Options(argumentString="store", validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual(["store", ], options.actions)

   def testConstructor_085(self):
      """
      Test constructor with argumentList=["purge", ], validate=False.
      """
      options = Options(argumentList=["purge", ], validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual(["purge", ], options.actions)

   def testConstructor_086(self):
      """
      Test constructor with argumentString="purge", validate=False.
      """
      options = Options(argumentString="purge", validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual(["purge", ], options.actions)

   def testConstructor_087(self):
      """
      Test constructor with argumentList=["rebuild", ], validate=False.
      """
      options = Options(argumentList=["rebuild", ], validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual(["rebuild", ], options.actions)

   def testConstructor_088(self):
      """
      Test constructor with argumentString="rebuild", validate=False.
      """
      options = Options(argumentString="rebuild", validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual(["rebuild", ], options.actions)

   def testConstructor_089(self):
      """
      Test constructor with argumentList=["validate", ], validate=False.
      """
      options = Options(argumentList=["validate", ], validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual(["validate", ], options.actions)

   def testConstructor_090(self):
      """
      Test constructor with argumentString="validate", validate=False.
      """
      options = Options(argumentString="validate", validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual(["validate", ], options.actions)

   def testConstructor_091(self):
      """
      Test constructor with argumentList=["collect", "all", ], validate=False.
      """
      options = Options(argumentList=["collect", "all", ], validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual(["collect", "all", ], options.actions)

   def testConstructor_092(self):
      """
      Test constructor with argumentString="collect all", validate=False.
      """
      options = Options(argumentString="collect all", validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual(["collect", "all", ], options.actions)

   def testConstructor_093(self):
      """
      Test constructor with argumentList=["collect", "rebuild", ], validate=False.
      """
      options = Options(argumentList=["collect", "rebuild", ], validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual(["collect", "rebuild", ], options.actions)

   def testConstructor_094(self):
      """
      Test constructor with argumentString="collect rebuild", validate=False.
      """
      options = Options(argumentString="collect rebuild", validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual(["collect", "rebuild", ], options.actions)

   def testConstructor_095(self):
      """
      Test constructor with argumentList=["collect", "validate", ], validate=False.
      """
      options = Options(argumentList=["collect", "validate", ], validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual(["collect", "validate", ], options.actions)

   def testConstructor_096(self):
      """
      Test constructor with argumentString="collect validate", validate=False.
      """
      options = Options(argumentString="collect validate", validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual(["collect", "validate", ], options.actions)

   def testConstructor_097(self):
      """
      Test constructor with argumentList=["-d", "--verbose", "-O", "--mode", "600", "collect", "stage", ], validate=False.
      """
      options = Options(argumentList=["-d", "--verbose", "-O", "--mode", "600", "collect", "stage", ], validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(True, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(0600, options.mode)
      self.failUnlessEqual(True, options.output)
      self.failUnlessEqual(True, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual(["collect", "stage", ], options.actions)

   def testConstructor_098(self):
      """
      Test constructor with argumentString="-d --verbose -O --mode 600 collect stage", validate=False.
      """
      options = Options(argumentString="-d --verbose -O --mode 600 collect stage", validate=False)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(True, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(0600, options.mode)
      self.failUnlessEqual(True, options.output)
      self.failUnlessEqual(True, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual(["collect", "stage", ], options.actions)

   def testConstructor_099(self):
      """
      Test constructor with argumentList=[], validate=True.
      """
      self.failUnlessRaises(ValueError, Options, argumentList=[], validate=True)

   def testConstructor_100(self):
      """
      Test constructor with argumentString="", validate=True.
      """
      self.failUnlessRaises(ValueError, Options, argumentString="", validate=True)

   def testConstructor_101(self):
      """
      Test constructor with argumentList=["--help", ], validate=True.
      """
      options = Options(argumentList=["--help", ], validate=True)
      self.failUnlessEqual(True, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_102(self):
      """
      Test constructor with argumentString="--help", validate=True.
      """
      options = Options(argumentString="--help", validate=True)
      self.failUnlessEqual(True, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_103(self):
      """
      Test constructor with argumentList=["-h", ], validate=True.
      """
      options = Options(argumentList=["-h", ], validate=True)
      self.failUnlessEqual(True, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_104(self):
      """
      Test constructor with argumentString="-h", validate=True.
      """
      options = Options(argumentString="-h", validate=True)
      self.failUnlessEqual(True, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_105(self):
      """
      Test constructor with argumentList=["--version", ], validate=True.
      """
      options = Options(argumentList=["--version", ], validate=True)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(True, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_106(self):
      """
      Test constructor with argumentString="--version", validate=True.
      """
      options = Options(argumentString="--version", validate=True)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(True, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_107(self):
      """
      Test constructor with argumentList=["-V", ], validate=True.
      """
      options = Options(argumentList=["-V", ], validate=True)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(True, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_108(self):
      """
      Test constructor with argumentString="-V", validate=True.
      """
      options = Options(argumentString="-V", validate=True)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(True, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual([], options.actions)

   def testConstructor_109(self):
      """
      Test constructor with argumentList=["--verbose", ], validate=True.
      """
      self.failUnlessRaises(ValueError, Options, argumentList=["--verbose", ], validate=True)

   def testConstructor_110(self):
      """
      Test constructor with argumentString="--verbose", validate=True.
      """
      self.failUnlessRaises(ValueError, Options, argumentString="--verbose", validate=True)

   def testConstructor_111(self):
      """
      Test constructor with argumentList=["-b", ], validate=True.
      """
      self.failUnlessRaises(ValueError, Options, argumentList=["-b", ], validate=True)

   def testConstructor_112(self):
      """
      Test constructor with argumentString="-b", validate=True.
      """
      self.failUnlessRaises(ValueError, Options, argumentString="-b", validate=True)

   def testConstructor_113(self):
      """
      Test constructor with argumentList=["--quiet", ], validate=True.
      """
      self.failUnlessRaises(ValueError, Options, argumentList=["--quiet", ], validate=True)

   def testConstructor_114(self):
      """
      Test constructor with argumentString="--quiet", validate=True.
      """
      self.failUnlessRaises(ValueError, Options, argumentString="--quiet", validate=True)

   def testConstructor_115(self):
      """
      Test constructor with argumentList=["-q", ], validate=True.
      """
      self.failUnlessRaises(ValueError, Options, argumentList=["-q", ], validate=True)

   def testConstructor_116(self):
      """
      Test constructor with argumentString="-q", validate=True.
      """
      self.failUnlessRaises(ValueError, Options, argumentString="-q", validate=True)

   def testConstructor_117(self):
      """
      Test constructor with argumentList=["--config", ], validate=True.
      """
      self.failUnlessRaises(GetoptError, Options, argumentList=["--config", ], validate=True)

   def testConstructor_118(self):
      """
      Test constructor with argumentString="--config", validate=True.
      """
      self.failUnlessRaises(GetoptError, Options, argumentString="--config", validate=True)

   def testConstructor_119(self):
      """
      Test constructor with argumentList=["-c", ], validate=True.
      """
      self.failUnlessRaises(GetoptError, Options, argumentList=["-c", ], validate=True)

   def testConstructor_120(self):
      """
      Test constructor with argumentString="-c", validate=True.
      """
      self.failUnlessRaises(GetoptError, Options, argumentString="-c", validate=True)

   def testConstructor_121(self):
      """
      Test constructor with argumentList=["--config", "something", ], validate=True.
      """
      self.failUnlessRaises(ValueError, Options, argumentList=["--config", "something", ], validate=True)

   def testConstructor_122(self):
      """
      Test constructor with argumentString="--config something", validate=True.
      """
      self.failUnlessRaises(ValueError, Options, argumentString="--config something", validate=True)

   def testConstructor_123(self):
      """
      Test constructor with argumentList=["-c", "something", ], validate=True.
      """
      self.failUnlessRaises(ValueError, Options, argumentList=["-c", "something", ], validate=True)

   def testConstructor_124(self):
      """
      Test constructor with argumentString="-c something", validate=True.
      """
      self.failUnlessRaises(ValueError, Options, argumentString="-c something", validate=True)

   def testConstructor_125(self):
      """
      Test constructor with argumentList=["--full", ], validate=True.
      """
      self.failUnlessRaises(ValueError, Options, argumentList=["--full", ], validate=True)

   def testConstructor_126(self):
      """
      Test constructor with argumentString="--full", validate=True.
      """
      self.failUnlessRaises(ValueError, Options, argumentString="--full", validate=True)

   def testConstructor_127(self):
      """
      Test constructor with argumentList=["-f", ], validate=True.
      """
      self.failUnlessRaises(ValueError, Options, argumentList=["-f", ], validate=True)

   def testConstructor_128(self):
      """
      Test constructor with argumentString="-f", validate=True.
      """
      self.failUnlessRaises(ValueError, Options, argumentString="-f", validate=True)

   def testConstructor_129(self):
      """
      Test constructor with argumentList=["--logfile", ], validate=True.
      """
      self.failUnlessRaises(GetoptError, Options, argumentList=["--logfile", ], validate=True)

   def testConstructor_130(self):
      """
      Test constructor with argumentString="--logfile", validate=True.
      """
      self.failUnlessRaises(GetoptError, Options, argumentString="--logfile", validate=True)

   def testConstructor_131(self):
      """
      Test constructor with argumentList=["-l", ], validate=True.
      """
      self.failUnlessRaises(GetoptError, Options, argumentList=["-l", ], validate=True)

   def testConstructor_132(self):
      """
      Test constructor with argumentString="-l", validate=True.
      """
      self.failUnlessRaises(GetoptError, Options, argumentString="-l", validate=True)

   def testConstructor_133(self):
      """
      Test constructor with argumentList=["--logfile", "something", ], validate=True.
      """
      self.failUnlessRaises(ValueError, Options, argumentList=["--logfile", "something", ], validate=True)

   def testConstructor_134(self):
      """
      Test constructor with argumentString="--logfile something", validate=True.
      """
      self.failUnlessRaises(ValueError, Options, argumentString="--logfile something", validate=True)

   def testConstructor_135(self):
      """
      Test constructor with argumentList=["-l", "something", ], validate=True.
      """
      self.failUnlessRaises(ValueError, Options, argumentList=["-l", "something", ], validate=True)

   def testConstructor_136(self):
      """
      Test constructor with argumentString="-l something", validate=True.
      """
      self.failUnlessRaises(ValueError, Options, argumentString="-l something", validate=True)

   def testConstructor_137(self):
      """
      Test constructor with argumentList=["--owner", ], validate=True.
      """
      self.failUnlessRaises(GetoptError, Options, argumentList=["--owner", ], validate=True)

   def testConstructor_138(self):
      """
      Test constructor with argumentString="--owner", validate=True.
      """
      self.failUnlessRaises(GetoptError, Options, argumentString="--owner", validate=True)

   def testConstructor_139(self):
      """
      Test constructor with argumentList=["-o", ], validate=True.
      """
      self.failUnlessRaises(GetoptError, Options, argumentList=["-o", ], validate=True)

   def testConstructor_140(self):
      """
      Test constructor with argumentString="-o", validate=True.
      """
      self.failUnlessRaises(GetoptError, Options, argumentString="-o", validate=True)

   def testConstructor_141(self):
      """
      Test constructor with argumentList=["--owner", "something", ], validate=True.
      """
      self.failUnlessRaises(ValueError, Options, argumentList=["--owner", "something", ], validate=True)

   def testConstructor_142(self):
      """
      Test constructor with argumentString="--owner something", validate=True.
      """
      self.failUnlessRaises(ValueError, Options, argumentString="--owner something", validate=True)

   def testConstructor_143(self):
      """
      Test constructor with argumentList=["-o", "something", ], validate=True.
      """
      self.failUnlessRaises(ValueError, Options, argumentList=["-o", "something", ], validate=True)

   def testConstructor_144(self):
      """
      Test constructor with argumentString="-o something", validate=True.
      """
      self.failUnlessRaises(ValueError, Options, argumentString="-o something", validate=True)

   def testConstructor_145(self):
      """
      Test constructor with argumentList=["--owner", "a:b", ], validate=True.
      """
      self.failUnlessRaises(ValueError, Options, argumentList=["--owner", "a:b", ], validate=True)

   def testConstructor_146(self):
      """
      Test constructor with argumentString="--owner a:b", validate=True.
      """
      self.failUnlessRaises(ValueError, Options, argumentString="--owner a:b", validate=True)

   def testConstructor_147(self):
      """
      Test constructor with argumentList=["-o", "a:b", ], validate=True.
      """
      self.failUnlessRaises(ValueError, Options, argumentList=["-o", "a:b", ], validate=True)

   def testConstructor_148(self):
      """
      Test constructor with argumentString="-o a:b", validate=True.
      """
      self.failUnlessRaises(ValueError, Options, argumentString="-o a:b", validate=True)

   def testConstructor_149(self):
      """
      Test constructor with argumentList=["--mode", ], validate=True.
      """
      self.failUnlessRaises(GetoptError, Options, argumentList=["--mode", ], validate=True)

   def testConstructor_150(self):
      """
      Test constructor with argumentString="--mode", validate=True.
      """
      self.failUnlessRaises(GetoptError, Options, argumentString="--mode", validate=True)

   def testConstructor_151(self):
      """
      Test constructor with argumentList=["-m", ], validate=True.
      """
      self.failUnlessRaises(GetoptError, Options, argumentList=["-m", ], validate=True)

   def testConstructor_152(self):
      """
      Test constructor with argumentString="-m", validate=True.
      """
      self.failUnlessRaises(GetoptError, Options, argumentString="-m", validate=True)

   def testConstructor_153(self):
      """
      Test constructor with argumentList=["--mode", "something", ], validate=True.
      """
      self.failUnlessRaises(ValueError, Options, argumentList=["--mode", "something", ], validate=True)

   def testConstructor_154(self):
      """
      Test constructor with argumentString="--mode something", validate=True.
      """
      self.failUnlessRaises(ValueError, Options, argumentString="--mode something", validate=True)

   def testConstructor_155(self):
      """
      Test constructor with argumentList=["-m", "something", ], validate=True.
      """
      self.failUnlessRaises(ValueError, Options, argumentList=["-m", "something", ], validate=True)

   def testConstructor_156(self):
      """
      Test constructor with argumentString="-m something", validate=True.
      """
      self.failUnlessRaises(ValueError, Options, argumentString="-m something", validate=True)

   def testConstructor_157(self):
      """
      Test constructor with argumentList=["--mode", "631", ], validate=True.
      """
      self.failUnlessRaises(ValueError, Options, argumentList=["--mode", "631", ], validate=True)

   def testConstructor_158(self):
      """
      Test constructor with argumentString="--mode 631", validate=True.
      """
      self.failUnlessRaises(ValueError, Options, argumentString="--mode 631", validate=True)

   def testConstructor_159(self):
      """
      Test constructor with argumentList=["-m", "631", ], validate=True.
      """
      self.failUnlessRaises(ValueError, Options, argumentList=["-m", "631", ], validate=True)

   def testConstructor_160(self):
      """
      Test constructor with argumentString="-m 631", validate=True.
      """
      self.failUnlessRaises(ValueError, Options, argumentString="-m 631", validate=True)

   def testConstructor_161(self):
      """
      Test constructor with argumentList=["--output", ], validate=True.
      """
      self.failUnlessRaises(ValueError, Options, argumentList=["--output", ], validate=True)

   def testConstructor_162(self):
      """
      Test constructor with argumentString="--output", validate=True.
      """
      self.failUnlessRaises(ValueError, Options, argumentString="--output", validate=True)

   def testConstructor_163(self):
      """
      Test constructor with argumentList=["-O", ], validate=True.
      """
      self.failUnlessRaises(ValueError, Options, argumentList=["-O", ], validate=True)

   def testConstructor_164(self):
      """
      Test constructor with argumentString="-O", validate=True.
      """
      self.failUnlessRaises(ValueError, Options, argumentString="-O", validate=True)

   def testConstructor_165(self):
      """
      Test constructor with argumentList=["--debug", ], validate=True.
      """
      self.failUnlessRaises(ValueError, Options, argumentList=["--debug", ], validate=True)

   def testConstructor_166(self):
      """
      Test constructor with argumentString="--debug", validate=True.
      """
      self.failUnlessRaises(ValueError, Options, argumentString="--debug", validate=True)

   def testConstructor_167(self):
      """
      Test constructor with argumentList=["-d", ], validate=True.
      """
      self.failUnlessRaises(ValueError, Options, argumentList=["-d", ], validate=True)

   def testConstructor_168(self):
      """
      Test constructor with argumentString="-d", validate=True.
      """
      self.failUnlessRaises(ValueError, Options, argumentString="-d", validate=True)

   def testConstructor_169(self):
      """
      Test constructor with argumentList=["--stack", ], validate=True.
      """
      self.failUnlessRaises(ValueError, Options, argumentList=["--stack", ], validate=True)

   def testConstructor_170(self):
      """
      Test constructor with argumentString="--stack", validate=True.
      """
      self.failUnlessRaises(ValueError, Options, argumentString="--stack", validate=True)

   def testConstructor_171(self):
      """
      Test constructor with argumentList=["-s", ], validate=True.
      """
      self.failUnlessRaises(ValueError, Options, argumentList=["-s", ], validate=True)

   def testConstructor_172(self):
      """
      Test constructor with argumentString="-s", validate=True.
      """
      self.failUnlessRaises(ValueError, Options, argumentString="-s", validate=True)

   def testConstructor_173(self):
      """
      Test constructor with argumentList=["all", ], validate=True.
      """
      options = Options(argumentList=["all", ], validate=True)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual(["all", ], options.actions)

   def testConstructor_174(self):
      """
      Test constructor with argumentString="all", validate=True.
      """
      options = Options(argumentString="all", validate=True)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual(["all", ], options.actions)

   def testConstructor_175(self):
      """
      Test constructor with argumentList=["collect", ], validate=True.
      """
      options = Options(argumentList=["collect", ], validate=True)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual(["collect", ], options.actions)

   def testConstructor_176(self):
      """
      Test constructor with argumentString="collect", validate=True.
      """
      options = Options(argumentString="collect", validate=True)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual(["collect", ], options.actions)

   def testConstructor_177(self):
      """
      Test constructor with argumentList=["stage", ], validate=True.
      """
      options = Options(argumentList=["stage", ], validate=True)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual(["stage", ], options.actions)

   def testConstructor_178(self):
      """
      Test constructor with argumentString="stage", validate=True.
      """
      options = Options(argumentString="stage", validate=True)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual(["stage", ], options.actions)

   def testConstructor_179(self):
      """
      Test constructor with argumentList=["store", ], validate=True.
      """
      options = Options(argumentList=["store", ], validate=True)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual(["store", ], options.actions)

   def testConstructor_180(self):
      """
      Test constructor with argumentString="store", validate=True.
      """
      options = Options(argumentString="store", validate=True)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual(["store", ], options.actions)

   def testConstructor_181(self):
      """
      Test constructor with argumentList=["purge", ], validate=True.
      """
      options = Options(argumentList=["purge", ], validate=True)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual(["purge", ], options.actions)

   def testConstructor_182(self):
      """
      Test constructor with argumentString="purge", validate=True.
      """
      options = Options(argumentString="purge", validate=True)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual(["purge", ], options.actions)

   def testConstructor_183(self):
      """
      Test constructor with argumentList=["rebuild", ], validate=True.
      """
      options = Options(argumentList=["rebuild", ], validate=True)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual(["rebuild", ], options.actions)

   def testConstructor_184(self):
      """
      Test constructor with argumentString="rebuild", validate=True.
      """
      options = Options(argumentString="rebuild", validate=True)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual(["rebuild", ], options.actions)

   def testConstructor_185(self):
      """
      Test constructor with argumentList=["validate", ], validate=True.
      """
      options = Options(argumentList=["validate", ], validate=True)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual(["validate", ], options.actions)

   def testConstructor_186(self):
      """
      Test constructor with argumentString="validate", validate=True.
      """
      options = Options(argumentString="validate", validate=True)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(False, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(None, options.mode)
      self.failUnlessEqual(False, options.output)
      self.failUnlessEqual(False, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual(["validate", ], options.actions)

   def testConstructor_187(self):
      """
      Test constructor with argumentList=["-d", "--verbose", "-O", "--mode", "600", "collect", "stage", ], validate=True.
      """
      options = Options(argumentList=["-d", "--verbose", "-O", "--mode", "600", "collect", "stage", ], validate=True)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(True, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(0600, options.mode)
      self.failUnlessEqual(True, options.output)
      self.failUnlessEqual(True, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual(["collect", "stage", ], options.actions)

   def testConstructor_188(self):
      """
      Test constructor with argumentString="-d --verbose -O --mode 600 collect stage", validate=True.
      """
      options = Options(argumentString="-d --verbose -O --mode 600 collect stage", validate=True)
      self.failUnlessEqual(False, options.help)
      self.failUnlessEqual(False, options.version)
      self.failUnlessEqual(True, options.verbose)
      self.failUnlessEqual(False, options.quiet)
      self.failUnlessEqual(None, options.config)
      self.failUnlessEqual(False, options.full)
      self.failUnlessEqual(None, options.logfile)
      self.failUnlessEqual(None, options.owner)
      self.failUnlessEqual(0600, options.mode)
      self.failUnlessEqual(True, options.output)
      self.failUnlessEqual(True, options.debug)
      self.failUnlessEqual(False, options.stacktrace)
      self.failUnlessEqual(["collect", "stage", ], options.actions)


   ############################
   # Test comparison operators
   ############################

   def testComparison_001(self):
      """
      Test comparison of two identical objects, all attributes at defaults.
      """
      options1 = Options()
      options2 = Options()
      self.failUnlessEqual(options1, options2)
      self.failUnless(options1 == options2)
      self.failUnless(not options1 < options2)
      self.failUnless(options1 <= options2)
      self.failUnless(not options1 > options2)
      self.failUnless(options1 >= options2)
      self.failUnless(not options1 != options2)

   def testComparison_002(self):
      """
      Test comparison of two identical objects, all attributes filled in and same.
      """
      options1 = Options()
      options2 = Options()

      options1.help = True
      options1.version = True
      options1.verbose = True
      options1.quiet = True
      options1.config = "config"
      options1.full = True
      options1.logfile = "logfile"
      options1.owner = ("a", "b")
      options1.mode = "631"
      options1.output = True
      options1.debug = True
      options1.stacktrace = False
      options1.actions = ["collect", ]

      options2.help = True
      options2.version = True
      options2.verbose = True
      options2.quiet = True
      options2.config = "config"
      options2.full = True
      options2.logfile = "logfile"
      options2.owner = ("a", "b")
      options2.mode = 0631
      options2.output = True
      options2.debug = True
      options2.stacktrace = False
      options2.actions = ["collect", ]

      self.failUnlessEqual(options1, options2)
      self.failUnless(options1 == options2)
      self.failUnless(not options1 < options2)
      self.failUnless(options1 <= options2)
      self.failUnless(not options1 > options2)
      self.failUnless(options1 >= options2)
      self.failUnless(not options1 != options2)

   def testComparison_003(self):
      """
      Test comparison of two identical objects, all attributes filled in, help different.
      """
      options1 = Options()
      options2 = Options()

      options1.help = True
      options1.version = True
      options1.verbose = True
      options1.quiet = True
      options1.config = "config"
      options1.full = True
      options1.logfile = "logfile"
      options1.owner = ("a", "b")
      options1.mode = "631"
      options1.output = True
      options1.debug = True
      options1.stacktrace = False
      options1.actions = ["collect", ]

      options2.help = False
      options2.version = True
      options2.verbose = True
      options2.quiet = True
      options2.config = "config"
      options2.full = True
      options2.logfile = "logfile"
      options2.owner = ("a", "b")
      options2.mode = 0631
      options2.output = True
      options2.debug = True
      options2.stacktrace = False
      options2.actions = ["collect", ]

      self.failIfEqual(options1, options2)
      self.failUnless(not options1 == options2)
      self.failUnless(not options1 < options2)
      self.failUnless(not options1 <= options2)
      self.failUnless(options1 > options2)
      self.failUnless(options1 >= options2)
      self.failUnless(options1 != options2)

   def testComparison_004(self):
      """
      Test comparison of two identical objects, all attributes filled in, version different.
      """
      options1 = Options()
      options2 = Options()

      options1.help = True
      options1.version = False
      options1.verbose = True
      options1.quiet = True
      options1.config = "config"
      options1.full = True
      options1.logfile = "logfile"
      options1.owner = ("a", "b")
      options1.mode = "631"
      options1.output = True
      options1.debug = True
      options1.stacktrace = False
      options1.actions = ["collect", ]

      options2.help = True
      options2.version = True
      options2.verbose = True
      options2.quiet = True
      options2.config = "config"
      options2.full = True
      options2.logfile = "logfile"
      options2.owner = ("a", "b")
      options2.mode = 0631
      options2.output = True
      options2.debug = True
      options2.stacktrace = False
      options2.actions = ["collect", ]

      self.failIfEqual(options1, options2)
      self.failUnless(not options1 == options2)
      self.failUnless(options1 < options2)
      self.failUnless(options1 <= options2)
      self.failUnless(not options1 > options2)
      self.failUnless(not options1 >= options2)
      self.failUnless(options1 != options2)

   def testComparison_005(self):
      """
      Test comparison of two identical objects, all attributes filled in, verbose different.
      """
      options1 = Options()
      options2 = Options()

      options1.help = True
      options1.version = True
      options1.verbose = False
      options1.quiet = True
      options1.config = "config"
      options1.full = True
      options1.logfile = "logfile"
      options1.owner = ("a", "b")
      options1.mode = "631"
      options1.output = True
      options1.debug = True
      options1.stacktrace = False
      options1.actions = ["collect", ]

      options2.help = True
      options2.version = True
      options2.verbose = True
      options2.quiet = True
      options2.config = "config"
      options2.full = True
      options2.logfile = "logfile"
      options2.owner = ("a", "b")
      options2.mode = 0631
      options2.output = True
      options2.debug = True
      options2.stacktrace = False
      options2.actions = ["collect", ]

      self.failIfEqual(options1, options2)
      self.failUnless(not options1 == options2)
      self.failUnless(options1 < options2)
      self.failUnless(options1 <= options2)
      self.failUnless(not options1 > options2)
      self.failUnless(not options1 >= options2)
      self.failUnless(options1 != options2)

   def testComparison_006(self):
      """
      Test comparison of two identical objects, all attributes filled in, quiet different.
      """
      options1 = Options()
      options2 = Options()

      options1.help = True
      options1.version = True
      options1.verbose = True
      options1.quiet = True
      options1.config = "config"
      options1.full = True
      options1.logfile = "logfile"
      options1.owner = ("a", "b")
      options1.mode = "631"
      options1.output = True
      options1.debug = True
      options1.stacktrace = False
      options1.actions = ["collect", ]

      options2.help = True
      options2.version = True
      options2.verbose = True
      options2.quiet = False
      options2.config = "config"
      options2.full = True
      options2.logfile = "logfile"
      options2.owner = ("a", "b")
      options2.mode = 0631
      options2.output = True
      options2.debug = True
      options2.stacktrace = False
      options2.actions = ["collect", ]

      self.failIfEqual(options1, options2)
      self.failUnless(not options1 == options2)
      self.failUnless(not options1 < options2)
      self.failUnless(not options1 <= options2)
      self.failUnless(options1 > options2)
      self.failUnless(options1 >= options2)
      self.failUnless(options1 != options2)

   def testComparison_007(self):
      """
      Test comparison of two identical objects, all attributes filled in, config different.
      """
      options1 = Options()
      options2 = Options()

      options1.help = True
      options1.version = True
      options1.verbose = True
      options1.quiet = True
      options1.config = "whatever"
      options1.full = True
      options1.logfile = "logfile"
      options1.owner = ("a", "b")
      options1.mode = "631"
      options1.output = True
      options1.debug = True
      options1.stacktrace = False
      options1.actions = ["collect", ]

      options2.help = True
      options2.version = True
      options2.verbose = True
      options2.quiet = True
      options2.config = "config"
      options2.full = True
      options2.logfile = "logfile"
      options2.owner = ("a", "b")
      options2.mode = 0631
      options2.output = True
      options2.debug = True
      options2.stacktrace = False
      options2.actions = ["collect", ]

      self.failIfEqual(options1, options2)
      self.failUnless(not options1 == options2)
      self.failUnless(not options1 < options2)
      self.failUnless(not options1 <= options2)
      self.failUnless(options1 > options2)
      self.failUnless(options1 >= options2)
      self.failUnless(options1 != options2)

   def testComparison_008(self):
      """
      Test comparison of two identical objects, all attributes filled in, full different.
      """
      options1 = Options()
      options2 = Options()

      options1.help = True
      options1.version = True
      options1.verbose = True
      options1.quiet = True
      options1.config = "config"
      options1.full = False
      options1.logfile = "logfile"
      options1.owner = ("a", "b")
      options1.mode = "631"
      options1.output = True
      options1.debug = True
      options1.stacktrace = False
      options1.actions = ["collect", ]

      options2.help = True
      options2.version = True
      options2.verbose = True
      options2.quiet = True
      options2.config = "config"
      options2.full = True
      options2.logfile = "logfile"
      options2.owner = ("a", "b")
      options2.mode = 0631
      options2.output = True
      options2.debug = True
      options2.stacktrace = False
      options2.actions = ["collect", ]

      self.failIfEqual(options1, options2)
      self.failUnless(not options1 == options2)
      self.failUnless(options1 < options2)
      self.failUnless(options1 <= options2)
      self.failUnless(not options1 > options2)
      self.failUnless(not options1 >= options2)
      self.failUnless(options1 != options2)

   def testComparison_009(self):
      """
      Test comparison of two identical objects, all attributes filled in, logfile different.
      """
      options1 = Options()
      options2 = Options()

      options1.help = True
      options1.version = True
      options1.verbose = True
      options1.quiet = True
      options1.config = "config"
      options1.full = True
      options1.logfile = "logfile"
      options1.owner = ("a", "b")
      options1.mode = "631"
      options1.output = True
      options1.debug = True
      options1.stacktrace = False
      options1.actions = ["collect", ]

      options2.help = True
      options2.version = True
      options2.verbose = True
      options2.quiet = True
      options2.config = "config"
      options2.full = True
      options2.logfile = "stuff"
      options2.owner = ("a", "b")
      options2.mode = 0631
      options2.output = True
      options2.debug = True
      options2.stacktrace = False
      options2.actions = ["collect", ]

      self.failIfEqual(options1, options2)
      self.failUnless(not options1 == options2)
      self.failUnless(options1 < options2)
      self.failUnless(options1 <= options2)
      self.failUnless(not options1 > options2)
      self.failUnless(not options1 >= options2)
      self.failUnless(options1 != options2)

   def testComparison_010(self):
      """
      Test comparison of two identical objects, all attributes filled in, owner different.
      """
      options1 = Options()
      options2 = Options()

      options1.help = True
      options1.version = True
      options1.verbose = True
      options1.quiet = True
      options1.config = "config"
      options1.full = True
      options1.logfile = "logfile"
      options1.owner = ("a", "b")
      options1.mode = "631"
      options1.output = True
      options1.debug = True
      options1.stacktrace = False
      options1.actions = ["collect", ]

      options2.help = True
      options2.version = True
      options2.verbose = True
      options2.quiet = True
      options2.config = "config"
      options2.full = True
      options2.logfile = "logfile"
      options2.owner = ("c", "d")
      options2.mode = 0631
      options2.output = True
      options2.debug = True
      options2.stacktrace = False
      options2.actions = ["collect", ]

      self.failIfEqual(options1, options2)
      self.failUnless(not options1 == options2)
      self.failUnless(options1 < options2)
      self.failUnless(options1 <= options2)
      self.failUnless(not options1 > options2)
      self.failUnless(not options1 >= options2)
      self.failUnless(options1 != options2)

   def testComparison_011(self):
      """
      Test comparison of two identical objects, all attributes filled in, mode different.
      """
      options1 = Options()
      options2 = Options()

      options1.help = True
      options1.version = True
      options1.verbose = True
      options1.quiet = True
      options1.config = "config"
      options1.full = True
      options1.logfile = "logfile"
      options1.owner = ("a", "b")
      options1.mode = 0600
      options1.output = True
      options1.debug = True
      options1.stacktrace = False
      options1.actions = ["collect", ]

      options2.help = True
      options2.version = True
      options2.verbose = True
      options2.quiet = True
      options2.config = "config"
      options2.full = True
      options2.logfile = "logfile"
      options2.owner = ("a", "b")
      options2.mode = 0631
      options2.output = True
      options2.debug = True
      options2.stacktrace = False
      options2.actions = ["collect", ]

      self.failIfEqual(options1, options2)
      self.failUnless(not options1 == options2)
      self.failUnless(options1 < options2)
      self.failUnless(options1 <= options2)
      self.failUnless(not options1 > options2)
      self.failUnless(not options1 >= options2)
      self.failUnless(options1 != options2)

   def testComparison_012(self):
      """
      Test comparison of two identical objects, all attributes filled in, output different.
      """
      options1 = Options()
      options2 = Options()

      options1.help = True
      options1.version = True
      options1.verbose = True
      options1.quiet = True
      options1.config = "config"
      options1.full = True
      options1.logfile = "logfile"
      options1.owner = ("a", "b")
      options1.mode = "631"
      options1.output = False
      options1.debug = True
      options1.stacktrace = False
      options1.actions = ["collect", ]

      options2.help = True
      options2.version = True
      options2.verbose = True
      options2.quiet = True
      options2.config = "config"
      options2.full = True
      options2.logfile = "logfile"
      options2.owner = ("a", "b")
      options2.mode = 0631
      options2.output = True
      options2.debug = True
      options2.stacktrace = False
      options2.actions = ["collect", ]

      self.failIfEqual(options1, options2)
      self.failUnless(not options1 == options2)
      self.failUnless(options1 < options2)
      self.failUnless(options1 <= options2)
      self.failUnless(not options1 > options2)
      self.failUnless(not options1 >= options2)
      self.failUnless(options1 != options2)

   def testComparison_013(self):
      """
      Test comparison of two identical objects, all attributes filled in, debug different.
      """
      options1 = Options()
      options2 = Options()

      options1.help = True
      options1.version = True
      options1.verbose = True
      options1.quiet = True
      options1.config = "config"
      options1.full = True
      options1.logfile = "logfile"
      options1.owner = ("a", "b")
      options1.mode = "631"
      options1.output = True
      options1.debug = True
      options1.stacktrace = False
      options1.actions = ["collect", ]

      options2.help = True
      options2.version = True
      options2.verbose = True
      options2.quiet = True
      options2.config = "config"
      options2.full = True
      options2.logfile = "logfile"
      options2.owner = ("a", "b")
      options2.mode = 0631
      options2.output = True
      options2.debug = False
      options1.stacktrace = False
      options2.actions = ["collect", ]

      self.failIfEqual(options1, options2)
      self.failUnless(not options1 == options2)
      self.failUnless(not options1 < options2)
      self.failUnless(not options1 <= options2)
      self.failUnless(options1 > options2)
      self.failUnless(options1 >= options2)
      self.failUnless(options1 != options2)

   def testComparison_014(self):
      """
      Test comparison of two identical objects, all attributes filled in, stacktrace different.
      """
      options1 = Options()
      options2 = Options()

      options1.help = True
      options1.version = True
      options1.verbose = True
      options1.quiet = True
      options1.config = "config"
      options1.full = True
      options1.logfile = "logfile"
      options1.owner = ("a", "b")
      options1.mode = "631"
      options1.output = True
      options1.debug = True
      options1.stacktrace = False
      options1.actions = ["collect", ]

      options2.help = True
      options2.version = True
      options2.verbose = True
      options2.quiet = True
      options2.config = "config"
      options2.full = True
      options2.logfile = "logfile"
      options2.owner = ("a", "b")
      options2.mode = 0631
      options2.output = True
      options2.debug = True
      options2.stacktrace = True
      options2.actions = ["collect", ]

      self.failIfEqual(options1, options2)
      self.failUnless(not options1 == options2)
      self.failUnless(options1 < options2)
      self.failUnless(options1 <= options2)
      self.failUnless(not options1 > options2)
      self.failUnless(not options1 >= options2)
      self.failUnless(options1 != options2)


   ###########################
   # Test buildArgumentList()
   ###########################

   def testBuildArgumentList_001(self):
      """Test with no values set, validate=False."""
      options = Options()
      argumentList = options.buildArgumentList(validate=False)
      self.failUnlessEqual([], argumentList)

   def testBuildArgumentList_002(self):
      """Test with help set, validate=False."""
      options = Options()
      options.help = True
      argumentList = options.buildArgumentList(validate=False)
      self.failUnlessEqual(["--help", ], argumentList)

   def testBuildArgumentList_003(self):
      """Test with version set, validate=False."""
      options = Options()
      options.version = True
      argumentList = options.buildArgumentList(validate=False)
      self.failUnlessEqual(["--version", ], argumentList)

   def testBuildArgumentList_004(self):
      """Test with verbose set, validate=False."""
      options = Options()
      options.verbose = True
      argumentList = options.buildArgumentList(validate=False)
      self.failUnlessEqual(["--verbose", ], argumentList)

   def testBuildArgumentList_005(self):
      """Test with quiet set, validate=False."""
      options = Options()
      options.quiet = True
      argumentList = options.buildArgumentList(validate=False)
      self.failUnlessEqual(["--quiet", ], argumentList)

   def testBuildArgumentList_006(self):
      """Test with config set, validate=False."""
      options = Options()
      options.config = "stuff"
      argumentList = options.buildArgumentList(validate=False)
      self.failUnlessEqual(["--config", "stuff", ], argumentList)

   def testBuildArgumentList_007(self):
      """Test with full set, validate=False."""
      options = Options()
      options.full = True
      argumentList = options.buildArgumentList(validate=False)
      self.failUnlessEqual(["--full", ], argumentList)

   def testBuildArgumentList_008(self):
      """Test with logfile set, validate=False."""
      options = Options()
      options.logfile = "bogus"
      argumentList = options.buildArgumentList(validate=False)
      self.failUnlessEqual(["--logfile", "bogus", ], argumentList)

   def testBuildArgumentList_009(self):
      """Test with owner set, validate=False."""
      options = Options()
      options.owner = ("ken", "group")
      argumentList = options.buildArgumentList(validate=False)
      self.failUnlessEqual(["--owner", "ken:group", ], argumentList)

   def testBuildArgumentList_010(self):
      """Test with mode set, validate=False."""
      options = Options()
      options.mode = 0644
      argumentList = options.buildArgumentList(validate=False)
      self.failUnlessEqual(["--mode", "644", ], argumentList)

   def testBuildArgumentList_011(self):
      """Test with output set, validate=False."""
      options = Options()
      options.output = True
      argumentList = options.buildArgumentList(validate=False)
      self.failUnlessEqual(["--output", ], argumentList)

   def testBuildArgumentList_012(self):
      """Test with debug set, validate=False."""
      options = Options()
      options.debug = True
      argumentList = options.buildArgumentList(validate=False)
      self.failUnlessEqual(["--debug", ], argumentList)

   def testBuildArgumentList_013(self):
      """Test with stacktrace set, validate=False."""
      options = Options()
      options.stacktrace = True
      argumentList = options.buildArgumentList(validate=False)
      self.failUnlessEqual(["--stack", ], argumentList)

   def testBuildArgumentList_014(self):
      """Test with actions containing one item, validate=False."""
      options = Options()
      options.actions = [ "collect", ]
      argumentList = options.buildArgumentList(validate=False)
      self.failUnlessEqual(["collect", ], argumentList)

   def testBuildArgumentList_015(self):
      """Test with actions containing multiple items, validate=False."""
      options = Options()
      options.actions = [ "collect", "stage", "store", "purge", ]
      argumentList = options.buildArgumentList(validate=False)
      self.failUnlessEqual(["collect", "stage", "store", "purge", ], argumentList)

   def testBuildArgumentList_016(self):
      """Test with all values set, actions containing one item, validate=False."""
      options = Options()
      options.help = True
      options.version = True
      options.verbose = True
      options.quiet = True
      options.config = "config"
      options.full = True
      options.logfile = "logfile"
      options.owner = ("a", "b")
      options.mode = "631"
      options.output = True
      options.debug = True
      options.stacktrace = True
      options.actions = ["collect", ]
      argumentList = options.buildArgumentList(validate=False)
      self.failUnlessEqual(["--help", "--version", "--verbose", "--quiet", "--config", "config", 
                             "--full", "--logfile", "logfile", "--owner", "a:b", "--mode", "631", 
                             "--output", "--debug", "--stack", "collect", ], argumentList)

   def testBuildArgumentList_017(self):
      """Test with all values set, actions containing multiple items, validate=False."""
      options = Options()
      options.help = True
      options.version = True
      options.verbose = True
      options.quiet = True
      options.config = "config"
      options.full = True
      options.logfile = "logfile"
      options.owner = ("a", "b")
      options.mode = "631"
      options.output = True
      options.debug = True
      options.stacktrace = True
      options.actions = ["collect", "stage", ]
      argumentList = options.buildArgumentList(validate=False)
      self.failUnlessEqual(["--help", "--version", "--verbose", "--quiet", "--config", "config", 
                             "--full", "--logfile", "logfile", "--owner", "a:b", "--mode", "631", 
                             "--output", "--debug", "--stack", "collect", "stage", ], argumentList)

   def testBuildArgumentList_018(self):
      """Test with no values set, validate=True."""
      options = Options()
      self.failUnlessRaises(ValueError, options.buildArgumentList, validate=True)

   def testBuildArgumentList_019(self):
      """Test with help set, validate=True."""
      options = Options()
      options.help = True
      argumentList = options.buildArgumentList(validate=True)
      self.failUnlessEqual(["--help", ], argumentList)

   def testBuildArgumentList_020(self):
      """Test with version set, validate=True."""
      options = Options()
      options.version = True
      argumentList = options.buildArgumentList(validate=True)
      self.failUnlessEqual(["--version", ], argumentList)

   def testBuildArgumentList_021(self):
      """Test with verbose set, validate=True."""
      options = Options()
      options.verbose = True
      self.failUnlessRaises(ValueError, options.buildArgumentList, validate=True)

   def testBuildArgumentList_022(self):
      """Test with quiet set, validate=True."""
      options = Options()
      options.quiet = True
      self.failUnlessRaises(ValueError, options.buildArgumentList, validate=True)

   def testBuildArgumentList_023(self):
      """Test with config set, validate=True."""
      options = Options()
      options.config = "stuff"
      self.failUnlessRaises(ValueError, options.buildArgumentList, validate=True)

   def testBuildArgumentList_024(self):
      """Test with full set, validate=True."""
      options = Options()
      options.full = True
      self.failUnlessRaises(ValueError, options.buildArgumentList, validate=True)

   def testBuildArgumentList_025(self):
      """Test with logfile set, validate=True."""
      options = Options()
      options.logfile = "bogus"
      self.failUnlessRaises(ValueError, options.buildArgumentList, validate=True)

   def testBuildArgumentList_026(self):
      """Test with owner set, validate=True."""
      options = Options()
      options.owner = ("ken", "group")
      self.failUnlessRaises(ValueError, options.buildArgumentList, validate=True)

   def testBuildArgumentList_027(self):
      """Test with mode set, validate=True."""
      options = Options()
      options.mode = 0644
      self.failUnlessRaises(ValueError, options.buildArgumentList, validate=True)

   def testBuildArgumentList_028(self):
      """Test with output set, validate=True."""
      options = Options()
      options.output = True
      self.failUnlessRaises(ValueError, options.buildArgumentList, validate=True)

   def testBuildArgumentList_029(self):
      """Test with debug set, validate=True."""
      options = Options()
      options.debug = True
      self.failUnlessRaises(ValueError, options.buildArgumentList, validate=True)

   def testBuildArgumentList_030(self):
      """Test with stacktrace set, validate=True."""
      options = Options()
      options.stacktrace = True
      self.failUnlessRaises(ValueError, options.buildArgumentList, validate=True)

   def testBuildArgumentList_031(self):
      """Test with actions containing one item, validate=True."""
      options = Options()
      options.actions = [ "collect", ]
      argumentList = options.buildArgumentList(validate=True)
      self.failUnlessEqual(["collect", ], argumentList)

   def testBuildArgumentList_032(self):
      """Test with actions containing multiple items, validate=True."""
      options = Options()
      options.actions = [ "collect", "stage", "store", "purge", ]
      argumentList = options.buildArgumentList(validate=True)
      self.failUnlessEqual(["collect", "stage", "store", "purge", ], argumentList)

   def testBuildArgumentList_033(self):
      """Test with all values set, actions containing one item, validate=True."""
      options = Options()
      options.help = True
      options.version = True
      options.verbose = True
      options.quiet = True
      options.config = "config"
      options.full = True
      options.logfile = "logfile"
      options.owner = ("a", "b")
      options.mode = "631"
      options.output = True
      options.debug = True
      options.stacktrace = True
      options.actions = ["collect", ]
      argumentList = options.buildArgumentList(validate=True)
      self.failUnlessEqual(["--help", "--version", "--verbose", "--quiet", "--config", "config", 
                             "--full", "--logfile", "logfile", "--owner", "a:b", "--mode", "631", 
                             "--output", "--debug", "--stack", "collect", ], argumentList)

   def testBuildArgumentList_034(self):
      """Test with all values set, actions containing multiple items, validate=True."""
      options = Options()
      options.help = True
      options.version = True
      options.verbose = True
      options.quiet = True
      options.config = "config"
      options.full = True
      options.logfile = "logfile"
      options.owner = ("a", "b")
      options.mode = "631"
      options.output = True
      options.debug = True
      options.stacktrace = True
      options.actions = ["collect", "stage", ]
      argumentList = options.buildArgumentList(validate=True)
      self.failUnlessEqual(["--help", "--version", "--verbose", "--quiet", "--config", "config", 
                             "--full", "--logfile", "logfile", "--owner", "a:b", "--mode", "631", 
                             "--output", "--debug", "--stack", "collect", "stage", ], argumentList)


   #############################
   # Test buildArgumentString()
   #############################

   def testBuildArgumentString_001(self):
      """Test with no values set, validate=False."""
      options = Options()
      argumentString = options.buildArgumentString(validate=False)
      self.failUnlessEqual("", argumentString)

   def testBuildArgumentString_002(self):
      """Test with help set, validate=False."""
      options = Options()
      options.help = True
      argumentString = options.buildArgumentString(validate=False)
      self.failUnlessEqual("--help ", argumentString)

   def testBuildArgumentString_003(self):
      """Test with version set, validate=False."""
      options = Options()
      options.version = True
      argumentString = options.buildArgumentString(validate=False)
      self.failUnlessEqual("--version ", argumentString)

   def testBuildArgumentString_004(self):
      """Test with verbose set, validate=False."""
      options = Options()
      options.verbose = True
      argumentString = options.buildArgumentString(validate=False)
      self.failUnlessEqual("--verbose ", argumentString)

   def testBuildArgumentString_005(self):
      """Test with quiet set, validate=False."""
      options = Options()
      options.quiet = True
      argumentString = options.buildArgumentString(validate=False)
      self.failUnlessEqual("--quiet ", argumentString)

   def testBuildArgumentString_006(self):
      """Test with config set, validate=False."""
      options = Options()
      options.config = "stuff"
      argumentString = options.buildArgumentString(validate=False)
      self.failUnlessEqual('--config "stuff" ', argumentString)

   def testBuildArgumentString_007(self):
      """Test with full set, validate=False."""
      options = Options()
      options.full = True
      argumentString = options.buildArgumentString(validate=False)
      self.failUnlessEqual("--full ", argumentString)

   def testBuildArgumentString_008(self):
      """Test with logfile set, validate=False."""
      options = Options()
      options.logfile = "bogus"
      argumentString = options.buildArgumentString(validate=False)
      self.failUnlessEqual('--logfile "bogus" ', argumentString)

   def testBuildArgumentString_009(self):
      """Test with owner set, validate=False."""
      options = Options()
      options.owner = ("ken", "group")
      argumentString = options.buildArgumentString(validate=False)
      self.failUnlessEqual('--owner "ken:group" ', argumentString)

   def testBuildArgumentString_010(self):
      """Test with mode set, validate=False."""
      options = Options()
      options.mode = 0644
      argumentString = options.buildArgumentString(validate=False)
      self.failUnlessEqual('--mode 644 ', argumentString)

   def testBuildArgumentString_011(self):
      """Test with output set, validate=False."""
      options = Options()
      options.output = True
      argumentString = options.buildArgumentString(validate=False)
      self.failUnlessEqual("--output ", argumentString)

   def testBuildArgumentString_012(self):
      """Test with debug set, validate=False."""
      options = Options()
      options.debug = True
      argumentString = options.buildArgumentString(validate=False)
      self.failUnlessEqual("--debug ", argumentString)

   def testBuildArgumentString_013(self):
      """Test with stacktrace set, validate=False."""
      options = Options()
      options.stacktrace = True
      argumentString = options.buildArgumentString(validate=False)
      self.failUnlessEqual("--stack ", argumentString)

   def testBuildArgumentString_014(self):
      """Test with actions containing one item, validate=False."""
      options = Options()
      options.actions = [ "collect", ]
      argumentString = options.buildArgumentString(validate=False)
      self.failUnlessEqual('"collect" ', argumentString)

   def testBuildArgumentString_015(self):
      """Test with actions containing multiple items, validate=False."""
      options = Options()
      options.actions = [ "collect", "stage", "store", "purge", ]
      argumentString = options.buildArgumentString(validate=False)
      self.failUnlessEqual('"collect" "stage" "store" "purge" ', argumentString)

   def testBuildArgumentString_016(self):
      """Test with all values set, actions containing one item, validate=False."""
      options = Options()
      options.help = True
      options.version = True
      options.verbose = True
      options.quiet = True
      options.config = "config"
      options.full = True
      options.logfile = "logfile"
      options.owner = ("a", "b")
      options.mode = "631"
      options.output = True
      options.debug = True
      options.stacktrace = True
      options.actions = ["collect", ]
      argumentString = options.buildArgumentString(validate=False)
      self.failUnlessEqual('--help --version --verbose --quiet --config "config" --full --logfile "logfile" --owner "a:b" --mode 631 --output --debug --stack "collect" ', argumentString)

   def testBuildArgumentString_017(self):
      """Test with all values set, actions containing multiple items, validate=False."""
      options = Options()
      options.help = True
      options.version = True
      options.verbose = True
      options.quiet = True
      options.config = "config"
      options.full = True
      options.logfile = "logfile"
      options.owner = ("a", "b")
      options.mode = "631"
      options.output = True
      options.debug = True
      options.stacktrace = True
      options.actions = ["collect", "stage", ]
      argumentString = options.buildArgumentString(validate=False)
      self.failUnlessEqual('--help --version --verbose --quiet --config "config" --full --logfile "logfile" --owner "a:b" --mode 631 --output --debug --stack "collect" "stage" ', argumentString)

   def testBuildArgumentString_018(self):
      """Test with no values set, validate=True."""
      options = Options()
      self.failUnlessRaises(ValueError, options.buildArgumentString, validate=True)

   def testBuildArgumentString_019(self):
      """Test with help set, validate=True."""
      options = Options()
      options.help = True
      argumentString = options.buildArgumentString(validate=True)
      self.failUnlessEqual("--help ", argumentString)

   def testBuildArgumentString_020(self):
      """Test with version set, validate=True."""
      options = Options()
      options.version = True
      argumentString = options.buildArgumentString(validate=True)
      self.failUnlessEqual("--version ", argumentString)

   def testBuildArgumentString_021(self):
      """Test with verbose set, validate=True."""
      options = Options()
      options.verbose = True
      self.failUnlessRaises(ValueError, options.buildArgumentString, validate=True)

   def testBuildArgumentString_022(self):
      """Test with quiet set, validate=True."""
      options = Options()
      options.quiet = True
      self.failUnlessRaises(ValueError, options.buildArgumentString, validate=True)

   def testBuildArgumentString_023(self):
      """Test with config set, validate=True."""
      options = Options()
      options.config = "stuff"
      self.failUnlessRaises(ValueError, options.buildArgumentString, validate=True)

   def testBuildArgumentString_024(self):
      """Test with full set, validate=True."""
      options = Options()
      options.full = True
      self.failUnlessRaises(ValueError, options.buildArgumentString, validate=True)

   def testBuildArgumentString_025(self):
      """Test with logfile set, validate=True."""
      options = Options()
      options.logfile = "bogus"
      self.failUnlessRaises(ValueError, options.buildArgumentString, validate=True)

   def testBuildArgumentString_026(self):
      """Test with owner set, validate=True."""
      options = Options()
      options.owner = ("ken", "group")
      self.failUnlessRaises(ValueError, options.buildArgumentString, validate=True)

   def testBuildArgumentString_027(self):
      """Test with mode set, validate=True."""
      options = Options()
      options.mode = 0644
      self.failUnlessRaises(ValueError, options.buildArgumentString, validate=True)

   def testBuildArgumentString_028(self):
      """Test with output set, validate=True."""
      options = Options()
      options.output = True
      self.failUnlessRaises(ValueError, options.buildArgumentString, validate=True)

   def testBuildArgumentString_029(self):
      """Test with debug set, validate=True."""
      options = Options()
      options.debug = True
      self.failUnlessRaises(ValueError, options.buildArgumentString, validate=True)

   def testBuildArgumentString_030(self):
      """Test with stacktrace set, validate=True."""
      options = Options()
      options.stacktrace = True
      self.failUnlessRaises(ValueError, options.buildArgumentString, validate=True)

   def testBuildArgumentString_031(self):
      """Test with actions containing one item, validate=True."""
      options = Options()
      options.actions = [ "collect", ]
      argumentString = options.buildArgumentString(validate=True)
      self.failUnlessEqual('"collect" ', argumentString)

   def testBuildArgumentString_032(self):
      """Test with actions containing multiple items, validate=True."""
      options = Options()
      options.actions = [ "collect", "stage", "store", "purge", ]
      argumentString = options.buildArgumentString(validate=True)
      self.failUnlessEqual('"collect" "stage" "store" "purge" ', argumentString)

   def testBuildArgumentString_033(self):
      """Test with all values set, actions containing one item, validate=True."""
      options = Options()
      options.help = True
      options.version = True
      options.verbose = True
      options.quiet = True
      options.config = "config"
      options.full = True
      options.logfile = "logfile"
      options.owner = ("a", "b")
      options.mode = "631"
      options.output = True
      options.debug = True
      options.stacktrace = True
      options.actions = ["collect", ]
      argumentString = options.buildArgumentString(validate=True)
      self.failUnlessEqual('--help --version --verbose --quiet --config "config" --full --logfile "logfile" --owner "a:b" --mode 631 --output --debug --stack "collect" ', argumentString)

   def testBuildArgumentString_034(self):
      """Test with all values set, actions containing multiple items, validate=True."""
      options = Options()
      options.help = True
      options.version = True
      options.verbose = True
      options.quiet = True
      options.config = "config"
      options.full = True
      options.logfile = "logfile"
      options.owner = ("a", "b")
      options.mode = "631"
      options.output = True
      options.debug = True
      options.stacktrace = True
      options.actions = ["collect", "stage", ]
      argumentString = options.buildArgumentString(validate=True)
      self.failUnlessEqual('--help --version --verbose --quiet --config "config" --full --logfile "logfile" --owner "a:b" --mode 631 --output --debug --stack "collect" "stage" ', argumentString)


######################
# TestActionSet class
######################

class TestActionSet(unittest.TestCase):

   """Tests for the _ActionSet class."""

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

   def testActionSet_001(self):
      """
      Test with actions=None, extensions=None.
      """
      actions = None
      extensions = None
      self.failUnlessRaises(ValueError, _ActionSet, actions, extensions)

   def testActionSet_002(self):
      """
      Test with actions=[], extensions=None.
      """
      actions = []
      extensions = None
      self.failUnlessRaises(ValueError, _ActionSet, actions, extensions)

   def testActionSet_003(self):
      """
      Test with actions=[], extensions=[].
      """
      actions = []
      extensions = []
      self.failUnlessRaises(ValueError, _ActionSet, actions, extensions)

   def testActionSet_004(self):
      """
      Test with actions=[ collect ], extensions=[].
      """
      actions = [ "collect", ]
      extensions = []
      actionSet = _ActionSet(actions, extensions)
      self.failIf(actionSet.actionSet is None)
      self.failUnless(len(actionSet.actionSet) == 1)
      self.failUnlessEqual(100, actionSet.actionSet[0].index)
      self.failUnlessEqual(executeCollect, actionSet.actionSet[0].function)
      self.failUnlessEqual(None, actionSet.actionSet[0].extension)

   def testActionSet_005(self):
      """
      Test with actions=[ stage ], extensions=[].
      """
      actions = [ "stage", ]
      extensions = []
      actionSet = _ActionSet(actions, extensions)
      self.failIf(actionSet.actionSet is None)
      self.failUnless(len(actionSet.actionSet) == 1)
      self.failUnlessEqual(200, actionSet.actionSet[0].index)
      self.failUnlessEqual(executeStage, actionSet.actionSet[0].function)
      self.failUnlessEqual(None, actionSet.actionSet[0].extension)

   def testActionSet_006(self):
      """
      Test with actions=[ store ], extensions=[].
      """
      actions = [ "store", ]
      extensions = []
      actionSet = _ActionSet(actions, extensions)
      self.failIf(actionSet.actionSet is None)
      self.failUnless(len(actionSet.actionSet) == 1)
      self.failUnlessEqual(300, actionSet.actionSet[0].index)
      self.failUnlessEqual(executeStore, actionSet.actionSet[0].function)
      self.failUnlessEqual(None, actionSet.actionSet[0].extension)

   def testActionSet_007(self):
      """
      Test with actions=[ purge ], extensions=[].
      """
      actions = [ "purge", ]
      extensions = []
      actionSet = _ActionSet(actions, extensions)
      self.failIf(actionSet.actionSet is None)
      self.failUnless(len(actionSet.actionSet) == 1)
      self.failUnlessEqual(400, actionSet.actionSet[0].index)
      self.failUnlessEqual(executePurge, actionSet.actionSet[0].function)
      self.failUnlessEqual(None, actionSet.actionSet[0].extension)

   def testActionSet_008(self):
      """
      Test with actions=[ all ], extensions=[].
      """
      actions = [ "all", ]
      extensions = []
      actionSet = _ActionSet(actions, extensions)
      self.failIf(actionSet.actionSet is None)
      self.failUnless(len(actionSet.actionSet) == 4)
      self.failUnlessEqual(100, actionSet.actionSet[0].index)
      self.failUnlessEqual(executeCollect, actionSet.actionSet[0].function)
      self.failUnlessEqual(None, actionSet.actionSet[0].extension)
      self.failUnlessEqual(200, actionSet.actionSet[1].index)
      self.failUnlessEqual(executeStage, actionSet.actionSet[1].function)
      self.failUnlessEqual(None, actionSet.actionSet[1].extension)
      self.failUnlessEqual(300, actionSet.actionSet[2].index)
      self.failUnlessEqual(executeStore, actionSet.actionSet[2].function)
      self.failUnlessEqual(None, actionSet.actionSet[2].extension)
      self.failUnlessEqual(400, actionSet.actionSet[3].index)
      self.failUnlessEqual(executePurge, actionSet.actionSet[3].function)
      self.failUnlessEqual(None, actionSet.actionSet[3].extension)

   def testActionSet_009(self):
      """
      Test with actions=[ rebuild ], extensions=[].
      """
      actions = [ "rebuild", ]
      extensions = []
      actionSet = _ActionSet(actions, extensions)
      self.failUnless(len(actionSet.actionSet) == 1)
      self.failUnlessEqual(None, actionSet.actionSet[0].index)
      self.failUnlessEqual(executeRebuild, actionSet.actionSet[0].function)
      self.failUnlessEqual(None, actionSet.actionSet[0].extension)

   def testActionSet_010(self):
      """
      Test with actions=[ validate ], extensions=[].
      """
      actions = [ "validate", ]
      extensions = []
      actionSet = _ActionSet(actions, extensions)
      self.failUnless(len(actionSet.actionSet) == 1)
      self.failUnlessEqual(None, actionSet.actionSet[0].index)
      self.failUnlessEqual(executeValidate, actionSet.actionSet[0].function)
      self.failUnlessEqual(None, actionSet.actionSet[0].extension)

   def testActionSet_011(self):
      """
      Test with actions=[ collect, collect ], extensions=[].
      """
      actions = [ "collect", "collect", ]
      extensions = []
      actionSet = _ActionSet(actions, extensions)
      self.failUnless(len(actionSet.actionSet) == 2)
      self.failUnlessEqual(100, actionSet.actionSet[0].index)
      self.failUnlessEqual(executeCollect, actionSet.actionSet[0].function)
      self.failUnlessEqual(None, actionSet.actionSet[0].extension)
      self.failUnlessEqual(100, actionSet.actionSet[1].index)
      self.failUnlessEqual(executeCollect, actionSet.actionSet[1].function)
      self.failUnlessEqual(None, actionSet.actionSet[1].extension)

   def testActionSet_012(self):
      """
      Test with actions=[ collect, stage ], extensions=[].
      """
      actions = [ "collect", "stage", ]
      extensions = []
      actionSet = _ActionSet(actions, extensions)
      self.failUnless(len(actionSet.actionSet) == 2)
      self.failUnlessEqual(100, actionSet.actionSet[0].index)
      self.failUnlessEqual(executeCollect, actionSet.actionSet[0].function)
      self.failUnlessEqual(None, actionSet.actionSet[0].extension)
      self.failUnlessEqual(200, actionSet.actionSet[1].index)
      self.failUnlessEqual(executeStage, actionSet.actionSet[1].function)
      self.failUnlessEqual(None, actionSet.actionSet[1].extension)

   def testActionSet_013(self):
      """
      Test with actions=[ collect, store ], extensions=[].
      """
      actions = [ "collect", "store", ]
      extensions = []
      actionSet = _ActionSet(actions, extensions)
      self.failUnless(len(actionSet.actionSet) == 2)
      self.failUnlessEqual(100, actionSet.actionSet[0].index)
      self.failUnlessEqual(executeCollect, actionSet.actionSet[0].function)
      self.failUnlessEqual(None, actionSet.actionSet[0].extension)
      self.failUnlessEqual(300, actionSet.actionSet[1].index)
      self.failUnlessEqual(executeStore, actionSet.actionSet[1].function)
      self.failUnlessEqual(None, actionSet.actionSet[1].extension)

   def testActionSet_014(self):
      """
      Test with actions=[ collect, purge ], extensions=[].
      """
      actions = [ "collect", "purge", ]
      extensions = []
      actionSet = _ActionSet(actions, extensions)
      self.failUnless(len(actionSet.actionSet) == 2)
      self.failUnlessEqual(100, actionSet.actionSet[0].index)
      self.failUnlessEqual(executeCollect, actionSet.actionSet[0].function)
      self.failUnlessEqual(None, actionSet.actionSet[0].extension)
      self.failUnlessEqual(400, actionSet.actionSet[1].index)
      self.failUnlessEqual(executePurge, actionSet.actionSet[1].function)
      self.failUnlessEqual(None, actionSet.actionSet[1].extension)

   def testActionSet_015(self):
      """
      Test with actions=[ collect, all ], extensions=[].
      """
      actions = [ "collect", "all", ]
      extensions = []
      self.failUnlessRaises(ValueError, _ActionSet, actions, extensions)

   def testActionSet_016(self):
      """
      Test with actions=[ collect, rebuild ], extensions=[].
      """
      actions = [ "collect", "rebuild", ]
      extensions = []
      self.failUnlessRaises(ValueError, _ActionSet, actions, extensions)

   def testActionSet_017(self):
      """
      Test with actions=[ collect, validate ], extensions=[].
      """
      actions = [ "collect", "validate", ]
      extensions = []
      self.failUnlessRaises(ValueError, _ActionSet, actions, extensions)

   def testActionSet_018(self):
      """
      Test with actions=[ stage, collect ], extensions=[].
      """
      actions = [ "stage", "collect", ]
      extensions = []
      actionSet = _ActionSet(actions, extensions)
      self.failUnless(len(actionSet.actionSet) == 2)
      self.failUnlessEqual(100, actionSet.actionSet[0].index)
      self.failUnlessEqual(executeCollect, actionSet.actionSet[0].function)
      self.failUnlessEqual(None, actionSet.actionSet[0].extension)
      self.failUnlessEqual(200, actionSet.actionSet[1].index)
      self.failUnlessEqual(executeStage, actionSet.actionSet[1].function)
      self.failUnlessEqual(None, actionSet.actionSet[1].extension)

   def testActionSet_019(self):
      """
      Test with actions=[ stage, stage ], extensions=[].
      """
      actions = [ "stage", "stage", ]
      extensions = []
      actionSet = _ActionSet(actions, extensions)
      self.failUnless(len(actionSet.actionSet) == 2)
      self.failUnlessEqual(200, actionSet.actionSet[0].index)
      self.failUnlessEqual(executeStage, actionSet.actionSet[0].function)
      self.failUnlessEqual(None, actionSet.actionSet[0].extension)
      self.failUnlessEqual(200, actionSet.actionSet[1].index)
      self.failUnlessEqual(executeStage, actionSet.actionSet[1].function)
      self.failUnlessEqual(None, actionSet.actionSet[1].extension)

   def testActionSet_020(self):
      """
      Test with actions=[ stage, store ], extensions=[].
      """
      actions = [ "stage", "store", ]
      extensions = []
      actionSet = _ActionSet(actions, extensions)
      self.failUnless(len(actionSet.actionSet) == 2)
      self.failUnlessEqual(200, actionSet.actionSet[0].index)
      self.failUnlessEqual(executeStage, actionSet.actionSet[0].function)
      self.failUnlessEqual(None, actionSet.actionSet[0].extension)
      self.failUnlessEqual(300, actionSet.actionSet[1].index)
      self.failUnlessEqual(executeStore, actionSet.actionSet[1].function)
      self.failUnlessEqual(None, actionSet.actionSet[1].extension)

   def testActionSet_021(self):
      """
      Test with actions=[ stage, purge ], extensions=[].
      """
      actions = [ "stage", "purge", ]
      extensions = []
      actionSet = _ActionSet(actions, extensions)
      self.failUnless(len(actionSet.actionSet) == 2)
      self.failUnlessEqual(200, actionSet.actionSet[0].index)
      self.failUnlessEqual(executeStage, actionSet.actionSet[0].function)
      self.failUnlessEqual(None, actionSet.actionSet[0].extension)
      self.failUnlessEqual(400, actionSet.actionSet[1].index)
      self.failUnlessEqual(executePurge, actionSet.actionSet[1].function)
      self.failUnlessEqual(None, actionSet.actionSet[1].extension)

   def testActionSet_022(self):
      """
      Test with actions=[ stage, all ], extensions=[].
      """
      actions = [ "stage", "all", ]
      extensions = []
      self.failUnlessRaises(ValueError, _ActionSet, actions, extensions)

   def testActionSet_023(self):
      """
      Test with actions=[ stage, rebuild ], extensions=[].
      """
      actions = [ "stage", "rebuild", ]
      extensions = []
      self.failUnlessRaises(ValueError, _ActionSet, actions, extensions)

   def testActionSet_024(self):
      """
      Test with actions=[ stage, validate ], extensions=[].
      """
      actions = [ "stage", "validate", ]
      extensions = []
      self.failUnlessRaises(ValueError, _ActionSet, actions, extensions)

   def testActionSet_025(self):
      """
      Test with actions=[ store, collect ], extensions=[].
      """
      actions = [ "store", "collect", ]
      extensions = []
      actionSet = _ActionSet(actions, extensions)
      self.failUnless(len(actionSet.actionSet) == 2)
      self.failUnlessEqual(100, actionSet.actionSet[0].index)
      self.failUnlessEqual(executeCollect, actionSet.actionSet[0].function)
      self.failUnlessEqual(None, actionSet.actionSet[0].extension)
      self.failUnlessEqual(300, actionSet.actionSet[1].index)
      self.failUnlessEqual(executeStore, actionSet.actionSet[1].function)
      self.failUnlessEqual(None, actionSet.actionSet[1].extension)

   def testActionSet_026(self):
      """
      Test with actions=[ store, stage ], extensions=[].
      """
      actions = [ "store", "stage", ]
      extensions = []
      actionSet = _ActionSet(actions, extensions)
      self.failUnless(len(actionSet.actionSet) == 2)
      self.failUnlessEqual(200, actionSet.actionSet[0].index)
      self.failUnlessEqual(executeStage, actionSet.actionSet[0].function)
      self.failUnlessEqual(None, actionSet.actionSet[0].extension)
      self.failUnlessEqual(300, actionSet.actionSet[1].index)
      self.failUnlessEqual(executeStore, actionSet.actionSet[1].function)
      self.failUnlessEqual(None, actionSet.actionSet[1].extension)

   def testActionSet_027(self):
      """
      Test with actions=[ store, store ], extensions=[].
      """
      actions = [ "store", "store", ]
      extensions = []
      actionSet = _ActionSet(actions, extensions)
      self.failUnless(len(actionSet.actionSet) == 2)
      self.failUnlessEqual(300, actionSet.actionSet[0].index)
      self.failUnlessEqual(executeStore, actionSet.actionSet[0].function)
      self.failUnlessEqual(None, actionSet.actionSet[0].extension)
      self.failUnlessEqual(300, actionSet.actionSet[1].index)
      self.failUnlessEqual(executeStore, actionSet.actionSet[1].function)
      self.failUnlessEqual(None, actionSet.actionSet[1].extension)

   def testActionSet_028(self):
      """
      Test with actions=[ store, purge ], extensions=[].
      """
      actions = [ "store", "purge", ]
      extensions = []
      actionSet = _ActionSet(actions, extensions)
      self.failUnless(len(actionSet.actionSet) == 2)
      self.failUnlessEqual(300, actionSet.actionSet[0].index)
      self.failUnlessEqual(executeStore, actionSet.actionSet[0].function)
      self.failUnlessEqual(None, actionSet.actionSet[0].extension)
      self.failUnlessEqual(400, actionSet.actionSet[1].index)
      self.failUnlessEqual(executePurge, actionSet.actionSet[1].function)
      self.failUnlessEqual(None, actionSet.actionSet[1].extension)

   def testActionSet_029(self):
      """
      Test with actions=[ store, all ], extensions=[].
      """
      actions = [ "store", "all", ]
      extensions = []
      self.failUnlessRaises(ValueError, _ActionSet, actions, extensions)

   def testActionSet_030(self):
      """
      Test with actions=[ store, rebuild ], extensions=[].
      """
      actions = [ "store", "rebuild", ]
      extensions = []
      self.failUnlessRaises(ValueError, _ActionSet, actions, extensions)

   def testActionSet_031(self):
      """
      Test with actions=[ store, validate ], extensions=[].
      """
      actions = [ "store", "validate", ]
      extensions = []
      self.failUnlessRaises(ValueError, _ActionSet, actions, extensions)

   def testActionSet_032(self):
      """
      Test with actions=[ purge, collect ], extensions=[].
      """
      actions = [ "purge", "collect", ]
      extensions = []
      actionSet = _ActionSet(actions, extensions)
      self.failUnless(len(actionSet.actionSet) == 2)
      self.failUnlessEqual(100, actionSet.actionSet[0].index)
      self.failUnlessEqual(executeCollect, actionSet.actionSet[0].function)
      self.failUnlessEqual(None, actionSet.actionSet[0].extension)
      self.failUnlessEqual(400, actionSet.actionSet[1].index)
      self.failUnlessEqual(executePurge, actionSet.actionSet[1].function)
      self.failUnlessEqual(None, actionSet.actionSet[1].extension)

   def testActionSet_033(self):
      """
      Test with actions=[ purge, stage ], extensions=[].
      """
      actions = [ "purge", "stage", ]
      extensions = []
      actionSet = _ActionSet(actions, extensions)
      self.failUnless(len(actionSet.actionSet) == 2)
      self.failUnlessEqual(200, actionSet.actionSet[0].index)
      self.failUnlessEqual(executeStage, actionSet.actionSet[0].function)
      self.failUnlessEqual(None, actionSet.actionSet[0].extension)
      self.failUnlessEqual(400, actionSet.actionSet[1].index)
      self.failUnlessEqual(executePurge, actionSet.actionSet[1].function)
      self.failUnlessEqual(None, actionSet.actionSet[1].extension)

   def testActionSet_034(self):
      """
      Test with actions=[ purge, store ], extensions=[].
      """
      actions = [ "purge", "store", ]
      extensions = []
      actionSet = _ActionSet(actions, extensions)
      self.failUnless(len(actionSet.actionSet) == 2)
      self.failUnlessEqual(300, actionSet.actionSet[0].index)
      self.failUnlessEqual(executeStore, actionSet.actionSet[0].function)
      self.failUnlessEqual(None, actionSet.actionSet[0].extension)
      self.failUnlessEqual(400, actionSet.actionSet[1].index)
      self.failUnlessEqual(executePurge, actionSet.actionSet[1].function)
      self.failUnlessEqual(None, actionSet.actionSet[1].extension)

   def testActionSet_035(self):
      """
      Test with actions=[ purge, purge ], extensions=[].
      """
      actions = [ "purge", "purge", ]
      extensions = []
      actionSet = _ActionSet(actions, extensions)
      self.failUnless(len(actionSet.actionSet) == 2)
      self.failUnlessEqual(400, actionSet.actionSet[0].index)
      self.failUnlessEqual(executePurge, actionSet.actionSet[0].function)
      self.failUnlessEqual(None, actionSet.actionSet[0].extension)
      self.failUnlessEqual(400, actionSet.actionSet[1].index)
      self.failUnlessEqual(executePurge, actionSet.actionSet[1].function)
      self.failUnlessEqual(None, actionSet.actionSet[1].extension)

   def testActionSet_036(self):
      """
      Test with actions=[ purge, all ], extensions=[].
      """
      actions = [ "purge", "all", ]
      extensions = []
      self.failUnlessRaises(ValueError, _ActionSet, actions, extensions)

   def testActionSet_037(self):
      """
      Test with actions=[ purge, rebuild ], extensions=[].
      """
      actions = [ "purge", "rebuild", ]
      extensions = []
      self.failUnlessRaises(ValueError, _ActionSet, actions, extensions)

   def testActionSet_038(self):
      """
      Test with actions=[ purge, validate ], extensions=[].
      """
      actions = [ "purge", "validate", ]
      extensions = []
      self.failUnlessRaises(ValueError, _ActionSet, actions, extensions)

   def testActionSet_039(self):
      """
      Test with actions=[ all, collect ], extensions=[].
      """
      actions = [ "all", "collect", ]
      extensions = []
      self.failUnlessRaises(ValueError, _ActionSet, actions, extensions)

   def testActionSet_040(self):
      """
      Test with actions=[ all, stage ], extensions=[].
      """
      actions = [ "all", "stage", ]
      extensions = []
      self.failUnlessRaises(ValueError, _ActionSet, actions, extensions)

   def testActionSet_041(self):
      """
      Test with actions=[ all, store ], extensions=[].
      """
      actions = [ "all", "store", ]
      extensions = []
      self.failUnlessRaises(ValueError, _ActionSet, actions, extensions)

   def testActionSet_042(self):
      """
      Test with actions=[ all, purge ], extensions=[].
      """
      actions = [ "all", "purge", ]
      extensions = []
      self.failUnlessRaises(ValueError, _ActionSet, actions, extensions)

   def testActionSet_043(self):
      """
      Test with actions=[ all, all ], extensions=[].
      """
      actions = [ "all", "all", ]
      extensions = []
      self.failUnlessRaises(ValueError, _ActionSet, actions, extensions)

   def testActionSet_044(self):
      """
      Test with actions=[ all, rebuild ], extensions=[].
      """
      actions = [ "all", "rebuild", ]
      extensions = []
      self.failUnlessRaises(ValueError, _ActionSet, actions, extensions)

   def testActionSet_045(self):
      """
      Test with actions=[ all, validate ], extensions=[].
      """
      actions = [ "all", "validate", ]
      extensions = []
      self.failUnlessRaises(ValueError, _ActionSet, actions, extensions)

   def testActionSet_046(self):
      """
      Test with actions=[ rebuild, collect ], extensions=[].
      """
      actions = [ "rebuild", "collect", ]
      extensions = []
      self.failUnlessRaises(ValueError, _ActionSet, actions, extensions)

   def testActionSet_047(self):
      """
      Test with actions=[ rebuild, stage ], extensions=[].
      """
      actions = [ "rebuild", "stage", ]
      extensions = []
      self.failUnlessRaises(ValueError, _ActionSet, actions, extensions)

   def testActionSet_048(self):
      """
      Test with actions=[ rebuild, store ], extensions=[].
      """
      actions = [ "rebuild", "store", ]
      extensions = []
      self.failUnlessRaises(ValueError, _ActionSet, actions, extensions)

   def testActionSet_049(self):
      """
      Test with actions=[ rebuild, purge ], extensions=[].
      """
      actions = [ "rebuild", "purge", ]
      extensions = []
      self.failUnlessRaises(ValueError, _ActionSet, actions, extensions)

   def testActionSet_050(self):
      """
      Test with actions=[ rebuild, all ], extensions=[].
      """
      actions = [ "rebuild", "all", ]
      extensions = []
      self.failUnlessRaises(ValueError, _ActionSet, actions, extensions)

   def testActionSet_051(self):
      """
      Test with actions=[ rebuild, rebuild ], extensions=[].
      """
      actions = [ "rebuild", "rebuild", ]
      extensions = []
      self.failUnlessRaises(ValueError, _ActionSet, actions, extensions)

   def testActionSet_052(self):
      """
      Test with actions=[ rebuild, validate ], extensions=[].
      """
      actions = [ "rebuild", "validate", ]
      extensions = []
      self.failUnlessRaises(ValueError, _ActionSet, actions, extensions)

   def testActionSet_053(self):
      """
      Test with actions=[ validate, collect ], extensions=[].
      """
      actions = [ "validate", "collect", ]
      extensions = []
      self.failUnlessRaises(ValueError, _ActionSet, actions, extensions)

   def testActionSet_054(self):
      """
      Test with actions=[ validate, stage ], extensions=[].
      """
      actions = [ "validate", "stage", ]
      extensions = []
      self.failUnlessRaises(ValueError, _ActionSet, actions, extensions)

   def testActionSet_055(self):
      """
      Test with actions=[ validate, store ], extensions=[].
      """
      actions = [ "validate", "store", ]
      extensions = []
      self.failUnlessRaises(ValueError, _ActionSet, actions, extensions)

   def testActionSet_056(self):
      """
      Test with actions=[ validate, purge ], extensions=[].
      """
      actions = [ "validate", "purge", ]
      extensions = []
      self.failUnlessRaises(ValueError, _ActionSet, actions, extensions)

   def testActionSet_057(self):
      """
      Test with actions=[ validate, all ], extensions=[].
      """
      actions = [ "validate", "all", ]
      extensions = []
      self.failUnlessRaises(ValueError, _ActionSet, actions, extensions)

   def testActionSet_058(self):
      """
      Test with actions=[ validate, rebuild ], extensions=[].
      """
      actions = [ "validate", "rebuild", ]
      extensions = []
      self.failUnlessRaises(ValueError, _ActionSet, actions, extensions)

   def testActionSet_059(self):
      """
      Test with actions=[ validate, validate ], extensions=[].
      """
      actions = [ "validate", "validate", ]
      extensions = []
      self.failUnlessRaises(ValueError, _ActionSet, actions, extensions)

   def testActionSet_060(self):
      """
      Test with actions=[ bogus ], extensions=[].
      """
      actions = [ "bogus", ]
      extensions = []
      self.failUnlessRaises(ValueError, _ActionSet, actions, extensions)

   def testActionSet_061(self):
      """
      Test with actions=[ bogus, collect ], extensions=[].
      """
      actions = [ "bogus", "collect", ]
      extensions = []
      self.failUnlessRaises(ValueError, _ActionSet, actions, extensions)

   def testActionSet_062(self):
      """
      Test with actions=[ bogus, stage ], extensions=[].
      """
      actions = [ "bogus", "stage", ]
      extensions = []
      self.failUnlessRaises(ValueError, _ActionSet, actions, extensions)

   def testActionSet_063(self):
      """
      Test with actions=[ bogus, store ], extensions=[].
      """
      actions = [ "bogus", "store", ]
      extensions = []
      self.failUnlessRaises(ValueError, _ActionSet, actions, extensions)

   def testActionSet_064(self):
      """
      Test with actions=[ bogus, purge ], extensions=[].
      """
      actions = [ "bogus", "purge", ]
      extensions = []
      self.failUnlessRaises(ValueError, _ActionSet, actions, extensions)

   def testActionSet_065(self):
      """
      Test with actions=[ bogus, all ], extensions=[].
      """
      actions = [ "bogus", "all", ]
      extensions = []
      self.failUnlessRaises(ValueError, _ActionSet, actions, extensions)

   def testActionSet_066(self):
      """
      Test with actions=[ bogus, rebuild ], extensions=[].
      """
      actions = [ "bogus", "rebuild", ]
      extensions = []
      self.failUnlessRaises(ValueError, _ActionSet, actions, extensions)

   def testActionSet_067(self):
      """
      Test with actions=[ bogus, validate ], extensions=[].
      """
      actions = [ "bogus", "validate", ]
      extensions = []
      self.failUnlessRaises(ValueError, _ActionSet, actions, extensions)

   def testActionSet_068(self):
      """
      Test with actions=[ collect, one ], extensions=[ (one, index 50) ].
      """
      actions = [ "collect", "one",  ]
      extensions = [ ExtendedAction("one", "a", "b", 50), ]
      actionSet = _ActionSet(actions, extensions)
      self.failUnless(len(actionSet.actionSet) == 2)
      self.failUnlessEqual(50, actionSet.actionSet[0].index)
      self.failUnlessEqual(None, actionSet.actionSet[0].function)
      self.failUnlessEqual(ExtendedAction("one", "a", "b", 50), actionSet.actionSet[0].extension)
      self.failUnlessEqual(100, actionSet.actionSet[1].index)
      self.failUnlessEqual(executeCollect, actionSet.actionSet[1].function)
      self.failUnlessEqual(None, actionSet.actionSet[1].extension)

   def testActionSet_069(self):
      """
      Test with actions=[ stage, one ], extensions=[ (one, index 50) ].
      """
      actions = [ "stage", "one", ]
      extensions = [ ExtendedAction("one", "a", "b", 50), ]
      actionSet = _ActionSet(actions, extensions)
      self.failUnless(len(actionSet.actionSet) == 2)
      self.failUnlessEqual(50, actionSet.actionSet[0].index)
      self.failUnlessEqual(None, actionSet.actionSet[0].function)
      self.failUnlessEqual(ExtendedAction("one", "a", "b", 50), actionSet.actionSet[0].extension)
      self.failUnlessEqual(200, actionSet.actionSet[1].index)
      self.failUnlessEqual(executeStage, actionSet.actionSet[1].function)
      self.failUnlessEqual(None, actionSet.actionSet[1].extension)

   def testActionSet_070(self):
      """
      Test with actions=[ store, one ], extensions=[ (one, index 50) ].
      """
      actions = [ "store", "one", ]
      extensions = [ ExtendedAction("one", "a", "b", 50), ]
      actionSet = _ActionSet(actions, extensions)
      self.failUnless(len(actionSet.actionSet) == 2)
      self.failUnlessEqual(50, actionSet.actionSet[0].index)
      self.failUnlessEqual(None, actionSet.actionSet[0].function)
      self.failUnlessEqual(ExtendedAction("one", "a", "b", 50), actionSet.actionSet[0].extension)
      self.failUnlessEqual(300, actionSet.actionSet[1].index)
      self.failUnlessEqual(executeStore, actionSet.actionSet[1].function)
      self.failUnlessEqual(None, actionSet.actionSet[1].extension)

   def testActionSet_071(self):
      """
      Test with actions=[ purge, one ], extensions=[ (one, index 50) ].
      """
      actions = [ "purge", "one", ]
      extensions = [ ExtendedAction("one", "a", "b", 50), ]
      actionSet = _ActionSet(actions, extensions)
      self.failUnless(len(actionSet.actionSet) == 2)
      self.failUnlessEqual(50, actionSet.actionSet[0].index)
      self.failUnlessEqual(None, actionSet.actionSet[0].function)
      self.failUnlessEqual(ExtendedAction("one", "a", "b", 50), actionSet.actionSet[0].extension)
      self.failUnlessEqual(400, actionSet.actionSet[1].index)
      self.failUnlessEqual(executePurge, actionSet.actionSet[1].function)
      self.failUnlessEqual(None, actionSet.actionSet[1].extension)

   def testActionSet_072(self):
      """
      Test with actions=[ all, one ], extensions=[ (one, index 50) ].
      """
      actions = [ "all", "one", ]
      extensions = [ ExtendedAction("one", "a", "b", 50), ]
      self.failUnlessRaises(ValueError, _ActionSet, actions, extensions)

   def testActionSet_073(self):
      """
      Test with actions=[ rebuild, one ], extensions=[ (one, index 50) ].
      """
      actions = [ "rebuild", "one", ]
      extensions = [ ExtendedAction("one", "a", "b", 50), ]
      self.failUnlessRaises(ValueError, _ActionSet, actions, extensions)

   def testActionSet_074(self):
      """
      Test with actions=[ validate, one ], extensions=[ (one, index 50) ].
      """
      actions = [ "validate", "one", ]
      extensions = [ ExtendedAction("one", "a", "b", 50), ]
      self.failUnlessRaises(ValueError, _ActionSet, actions, extensions)

   def testActionSet_075(self):
      """
      Test with actions=[ collect, one ], extensions=[ (one, index 150) ].
      """
      actions = [ "collect", "one", ]
      extensions = [ ExtendedAction("one", "a", "b", 150), ]
      actionSet = _ActionSet(actions, extensions)
      self.failUnless(len(actionSet.actionSet) == 2)
      self.failUnlessEqual(100, actionSet.actionSet[0].index)
      self.failUnlessEqual(executeCollect, actionSet.actionSet[0].function)
      self.failUnlessEqual(None, actionSet.actionSet[0].extension)
      self.failUnlessEqual(150, actionSet.actionSet[1].index)
      self.failUnlessEqual(None, actionSet.actionSet[1].function)
      self.failUnlessEqual(ExtendedAction("one", "a", "b", 150), actionSet.actionSet[1].extension)

   def testActionSet_076(self):
      """
      Test with actions=[ stage, one ], extensions=[ (one, index 150) ].
      """
      actions = [ "stage", "one", ]
      extensions = [ ExtendedAction("one", "a", "b", 150), ]
      actionSet = _ActionSet(actions, extensions)
      self.failUnless(len(actionSet.actionSet) == 2)
      self.failUnlessEqual(150, actionSet.actionSet[0].index)
      self.failUnlessEqual(None, actionSet.actionSet[0].function)
      self.failUnlessEqual(ExtendedAction("one", "a", "b", 150), actionSet.actionSet[0].extension)
      self.failUnlessEqual(200, actionSet.actionSet[1].index)
      self.failUnlessEqual(executeStage, actionSet.actionSet[1].function)
      self.failUnlessEqual(None, actionSet.actionSet[1].extension)

   def testActionSet_077(self):
      """
      Test with actions=[ store, one ], extensions=[ (one, index 150) ].
      """
      actions = [ "store", "one", ]
      extensions = [ ExtendedAction("one", "a", "b", 150), ]
      actionSet = _ActionSet(actions, extensions)
      self.failUnless(len(actionSet.actionSet) == 2)
      self.failUnlessEqual(150, actionSet.actionSet[0].index)
      self.failUnlessEqual(None, actionSet.actionSet[0].function)
      self.failUnlessEqual(ExtendedAction("one", "a", "b", 150), actionSet.actionSet[0].extension)
      self.failUnlessEqual(300, actionSet.actionSet[1].index)
      self.failUnlessEqual(executeStore, actionSet.actionSet[1].function)
      self.failUnlessEqual(None, actionSet.actionSet[1].extension)

   def testActionSet_078(self):
      """
      Test with actions=[ purge, one ], extensions=[ (one, index 150) ].
      """
      actions = [ "purge", "one", ]
      extensions = [ ExtendedAction("one", "a", "b", 150), ]
      actionSet = _ActionSet(actions, extensions)
      self.failUnless(len(actionSet.actionSet) == 2)
      self.failUnlessEqual(150, actionSet.actionSet[0].index)
      self.failUnlessEqual(None, actionSet.actionSet[0].function)
      self.failUnlessEqual(ExtendedAction("one", "a", "b", 150), actionSet.actionSet[0].extension)
      self.failUnlessEqual(400, actionSet.actionSet[1].index)
      self.failUnlessEqual(executePurge, actionSet.actionSet[1].function)
      self.failUnlessEqual(None, actionSet.actionSet[1].extension)

   def testActionSet_079(self):
      """
      Test with actions=[ all, one ], extensions=[ (one, index 150) ].
      """
      actions = [ "all", "one", ]
      extensions = [ ExtendedAction("one", "a", "b", 150), ]
      self.failUnlessRaises(ValueError, _ActionSet, actions, extensions)

   def testActionSet_080(self):
      """
      Test with actions=[ rebuild, one ], extensions=[ (one, index 150) ].
      """
      actions = [ "rebuild", "one", ]
      extensions = [ ExtendedAction("one", "a", "b", 150), ]
      self.failUnlessRaises(ValueError, _ActionSet, actions, extensions)

   def testActionSet_081(self):
      """
      Test with actions=[ validate, one ], extensions=[ (one, index 150) ].
      """
      actions = [ "validate", "one", ]
      extensions = [ ExtendedAction("one", "a", "b", 150), ]
      self.failUnlessRaises(ValueError, _ActionSet, actions, extensions)

   def testActionSet_082(self):
      """
      Test with actions=[ collect, one ], extensions=[ (one, index 250) ].
      """
      actions = [ "collect", "one", ]
      extensions = [ ExtendedAction("one", "a", "b", 250), ]
      actionSet = _ActionSet(actions, extensions)
      self.failUnless(len(actionSet.actionSet) == 2)
      self.failUnlessEqual(100, actionSet.actionSet[0].index)
      self.failUnlessEqual(executeCollect, actionSet.actionSet[0].function)
      self.failUnlessEqual(None, actionSet.actionSet[0].extension)
      self.failUnlessEqual(250, actionSet.actionSet[1].index)
      self.failUnlessEqual(None, actionSet.actionSet[1].function)
      self.failUnlessEqual(ExtendedAction("one", "a", "b", 250), actionSet.actionSet[1].extension)

   def testActionSet_083(self):
      """
      Test with actions=[ stage, one ], extensions=[ (one, index 250) ].
      """
      actions = [ "stage", "one", ]
      extensions = [ ExtendedAction("one", "a", "b", 250), ]
      actionSet = _ActionSet(actions, extensions)
      self.failUnless(len(actionSet.actionSet) == 2)
      self.failUnlessEqual(200, actionSet.actionSet[0].index)
      self.failUnlessEqual(executeStage, actionSet.actionSet[0].function)
      self.failUnlessEqual(None, actionSet.actionSet[0].extension)
      self.failUnlessEqual(250, actionSet.actionSet[1].index)
      self.failUnlessEqual(None, actionSet.actionSet[1].function)
      self.failUnlessEqual(ExtendedAction("one", "a", "b", 250), actionSet.actionSet[1].extension)

   def testActionSet_084(self):
      """
      Test with actions=[ store, one ], extensions=[ (one, index 250) ].
      """
      actions = [ "store", "one", ]
      extensions = [ ExtendedAction("one", "a", "b", 250), ]
      actionSet = _ActionSet(actions, extensions)
      self.failUnless(len(actionSet.actionSet) == 2)
      self.failUnlessEqual(250, actionSet.actionSet[0].index)
      self.failUnlessEqual(None, actionSet.actionSet[0].function)
      self.failUnlessEqual(ExtendedAction("one", "a", "b", 250), actionSet.actionSet[0].extension)
      self.failUnlessEqual(300, actionSet.actionSet[1].index)
      self.failUnlessEqual(executeStore, actionSet.actionSet[1].function)
      self.failUnlessEqual(None, actionSet.actionSet[1].extension)

   def testActionSet_085(self):
      """
      Test with actions=[ purge, one ], extensions=[ (one, index 250) ].
      """
      actions = [ "purge", "one", ]
      extensions = [ ExtendedAction("one", "a", "b", 250), ]
      actionSet = _ActionSet(actions, extensions)
      self.failUnless(len(actionSet.actionSet) == 2)
      self.failUnlessEqual(250, actionSet.actionSet[0].index)
      self.failUnlessEqual(None, actionSet.actionSet[0].function)
      self.failUnlessEqual(ExtendedAction("one", "a", "b", 250), actionSet.actionSet[0].extension)
      self.failUnlessEqual(400, actionSet.actionSet[1].index)
      self.failUnlessEqual(executePurge, actionSet.actionSet[1].function)
      self.failUnlessEqual(None, actionSet.actionSet[1].extension)

   def testActionSet_086(self):
      """
      Test with actions=[ all, one ], extensions=[ (one, index 250) ].
      """
      actions = [ "all", "one", ]
      extensions = [ ExtendedAction("one", "a", "b", 250), ]
      self.failUnlessRaises(ValueError, _ActionSet, actions, extensions)

   def testActionSet_087(self):
      """
      Test with actions=[ rebuild, one ], extensions=[ (one, index 250) ].
      """
      actions = [ "rebuild", "one", ]
      extensions = [ ExtendedAction("one", "a", "b", 250), ]
      self.failUnlessRaises(ValueError, _ActionSet, actions, extensions)

   def testActionSet_088(self):
      """
      Test with actions=[ validate, one ], extensions=[ (one, index 250) ].
      """
      actions = [ "validate", "one", ]
      extensions = [ ExtendedAction("one", "a", "b", 250), ]
      self.failUnlessRaises(ValueError, _ActionSet, actions, extensions)

   def testActionSet_089(self):
      """
      Test with actions=[ collect, one ], extensions=[ (one, index 350) ].
      """
      actions = [ "collect", "one", ]
      extensions = [ ExtendedAction("one", "a", "b", 350), ]
      actionSet = _ActionSet(actions, extensions)
      self.failUnless(len(actionSet.actionSet) == 2)
      self.failUnlessEqual(100, actionSet.actionSet[0].index)
      self.failUnlessEqual(executeCollect, actionSet.actionSet[0].function)
      self.failUnlessEqual(None, actionSet.actionSet[0].extension)
      self.failUnlessEqual(350, actionSet.actionSet[1].index)
      self.failUnlessEqual(None, actionSet.actionSet[1].function)
      self.failUnlessEqual(ExtendedAction("one", "a", "b", 350), actionSet.actionSet[1].extension)

   def testActionSet_090(self):
      """
      Test with actions=[ stage, one ], extensions=[ (one, index 350) ].
      """
      actions = [ "stage", "one", ]
      extensions = [ ExtendedAction("one", "a", "b", 350), ]
      actionSet = _ActionSet(actions, extensions)
      self.failUnless(len(actionSet.actionSet) == 2)
      self.failUnlessEqual(200, actionSet.actionSet[0].index)
      self.failUnlessEqual(executeStage, actionSet.actionSet[0].function)
      self.failUnlessEqual(None, actionSet.actionSet[0].extension)
      self.failUnlessEqual(350, actionSet.actionSet[1].index)
      self.failUnlessEqual(None, actionSet.actionSet[1].function)
      self.failUnlessEqual(ExtendedAction("one", "a", "b", 350), actionSet.actionSet[1].extension)

   def testActionSet_091(self):
      """
      Test with actions=[ store, one ], extensions=[ (one, index 350) ].
      """
      actions = [ "store", "one", ]
      extensions = [ ExtendedAction("one", "a", "b", 350), ]
      actionSet = _ActionSet(actions, extensions)
      self.failUnless(len(actionSet.actionSet) == 2)
      self.failUnlessEqual(300, actionSet.actionSet[0].index)
      self.failUnlessEqual(executeStore, actionSet.actionSet[0].function)
      self.failUnlessEqual(None, actionSet.actionSet[0].extension)
      self.failUnlessEqual(350, actionSet.actionSet[1].index)
      self.failUnlessEqual(None, actionSet.actionSet[1].function)
      self.failUnlessEqual(ExtendedAction("one", "a", "b", 350), actionSet.actionSet[1].extension)

   def testActionSet_092(self):
      """
      Test with actions=[ purge, one ], extensions=[ (one, index 350) ].
      """
      actions = [ "purge", "one", ]
      extensions = [ ExtendedAction("one", "a", "b", 350), ]
      actionSet = _ActionSet(actions, extensions)
      self.failUnless(len(actionSet.actionSet) == 2)
      self.failUnlessEqual(350, actionSet.actionSet[0].index)
      self.failUnlessEqual(None, actionSet.actionSet[0].function)
      self.failUnlessEqual(ExtendedAction("one", "a", "b", 350), actionSet.actionSet[0].extension)
      self.failUnlessEqual(400, actionSet.actionSet[1].index)
      self.failUnlessEqual(executePurge, actionSet.actionSet[1].function)
      self.failUnlessEqual(None, actionSet.actionSet[1].extension)

   def testActionSet_093(self):
      """
      Test with actions=[ all, one ], extensions=[ (one, index 350) ].
      """
      actions = [ "all", "one", ]
      extensions = [ ExtendedAction("one", "a", "b", 350), ]
      self.failUnlessRaises(ValueError, _ActionSet, actions, extensions)

   def testActionSet_094(self):
      """
      Test with actions=[ rebuild, one ], extensions=[ (one, index 350) ].
      """
      actions = [ "rebuild", "one", ]
      extensions = [ ExtendedAction("one", "a", "b", 350), ]
      self.failUnlessRaises(ValueError, _ActionSet, actions, extensions)

   def testActionSet_095(self):
      """
      Test with actions=[ validate, one ], extensions=[ (one, index 350) ].
      """
      actions = [ "validate", "one", ]
      extensions = [ ExtendedAction("one", "a", "b", 350), ]
      self.failUnlessRaises(ValueError, _ActionSet, actions, extensions)

   def testActionSet_096(self):
      """
      Test with actions=[ collect, one ], extensions=[ (one, index 450) ].
      """
      actions = [ "collect", "one", ]
      extensions = [ ExtendedAction("one", "a", "b", 450), ]
      actionSet = _ActionSet(actions, extensions)
      self.failUnless(len(actionSet.actionSet) == 2)
      self.failUnlessEqual(100, actionSet.actionSet[0].index)
      self.failUnlessEqual(executeCollect, actionSet.actionSet[0].function)
      self.failUnlessEqual(None, actionSet.actionSet[0].extension)
      self.failUnlessEqual(450, actionSet.actionSet[1].index)
      self.failUnlessEqual(None, actionSet.actionSet[1].function)
      self.failUnlessEqual(ExtendedAction("one", "a", "b", 450), actionSet.actionSet[1].extension)

   def testActionSet_097(self):
      """
      Test with actions=[ stage, one ], extensions=[ (one, index 450) ].
      """
      actions = [ "stage", "one", ]
      extensions = [ ExtendedAction("one", "a", "b", 450), ]
      actionSet = _ActionSet(actions, extensions)
      self.failUnless(len(actionSet.actionSet) == 2)
      self.failUnlessEqual(200, actionSet.actionSet[0].index)
      self.failUnlessEqual(executeStage, actionSet.actionSet[0].function)
      self.failUnlessEqual(None, actionSet.actionSet[0].extension)
      self.failUnlessEqual(450, actionSet.actionSet[1].index)
      self.failUnlessEqual(None, actionSet.actionSet[1].function)
      self.failUnlessEqual(ExtendedAction("one", "a", "b", 450), actionSet.actionSet[1].extension)

   def testActionSet_098(self):
      """
      Test with actions=[ store, one ], extensions=[ (one, index 450) ].
      """
      actions = [ "store", "one", ]
      extensions = [ ExtendedAction("one", "a", "b", 450), ]
      actionSet = _ActionSet(actions, extensions)
      self.failUnless(len(actionSet.actionSet) == 2)
      self.failUnlessEqual(300, actionSet.actionSet[0].index)
      self.failUnlessEqual(executeStore, actionSet.actionSet[0].function)
      self.failUnlessEqual(None, actionSet.actionSet[0].extension)
      self.failUnlessEqual(450, actionSet.actionSet[1].index)
      self.failUnlessEqual(None, actionSet.actionSet[1].function)
      self.failUnlessEqual(ExtendedAction("one", "a", "b", 450), actionSet.actionSet[1].extension)

   def testActionSet_099(self):
      """
      Test with actions=[ purge, one ], extensions=[ (one, index 450) ].
      """
      actions = [ "purge", "one", ]
      extensions = [ ExtendedAction("one", "a", "b", 450), ]
      actionSet = _ActionSet(actions, extensions)
      self.failUnless(len(actionSet.actionSet) == 2)
      self.failUnlessEqual(400, actionSet.actionSet[0].index)
      self.failUnlessEqual(executePurge, actionSet.actionSet[0].function)
      self.failUnlessEqual(None, actionSet.actionSet[0].extension)
      self.failUnlessEqual(450, actionSet.actionSet[1].index)
      self.failUnlessEqual(None, actionSet.actionSet[1].function)
      self.failUnlessEqual(ExtendedAction("one", "a", "b", 450), actionSet.actionSet[1].extension)

   def testActionSet_100(self):
      """
      Test with actions=[ all, one ], extensions=[ (one, index 450) ].
      """
      actions = [ "all", "one", ]
      extensions = [ ExtendedAction("one", "a", "b", 450), ]
      self.failUnlessRaises(ValueError, _ActionSet, actions, extensions)

   def testActionSet_101(self):
      """
      Test with actions=[ rebuild, one ], extensions=[ (one, index 450) ].
      """
      actions = [ "rebuild", "one", ]
      extensions = [ ExtendedAction("one", "a", "b", 450), ]
      self.failUnlessRaises(ValueError, _ActionSet, actions, extensions)

   def testActionSet_102(self):
      """
      Test with actions=[ validate, one ], extensions=[ (one, index 450) ].
      """
      actions = [ "validate", "one", ]
      extensions = [ ExtendedAction("one", "a", "b", 450), ]
      self.failUnlessRaises(ValueError, _ActionSet, actions, extensions)

   def testActionSet_103(self):
      """
      Test with actions=[ one, one ], extensions=[ (one, index 450) ].
      """
      actions = [ "one", "one", ]
      extensions = [ ExtendedAction("one", "a", "b", 450), ]
      actionSet = _ActionSet(actions, extensions)
      self.failUnless(len(actionSet.actionSet) == 2)
      self.failUnlessEqual(450, actionSet.actionSet[0].index)
      self.failUnlessEqual(None, actionSet.actionSet[0].function)
      self.failUnlessEqual(ExtendedAction("one", "a", "b", 450), actionSet.actionSet[0].extension)
      self.failUnlessEqual(450, actionSet.actionSet[1].index)
      self.failUnlessEqual(None, actionSet.actionSet[1].function)
      self.failUnlessEqual(ExtendedAction("one", "a", "b", 450), actionSet.actionSet[1].extension)

   def testActionSet_104(self):
      """
      Test with actions=[ collect, stage, store, purge ], extensions=[].
      """
      actions = [ "collect", "stage", "store", "purge", ]
      extensions = []
      actionSet = _ActionSet(actions, extensions)
      self.failUnless(len(actionSet.actionSet) == 4)
      self.failUnlessEqual(100, actionSet.actionSet[0].index)
      self.failUnlessEqual(executeCollect, actionSet.actionSet[0].function)
      self.failUnlessEqual(None, actionSet.actionSet[0].extension)
      self.failUnlessEqual(200, actionSet.actionSet[1].index)
      self.failUnlessEqual(executeStage, actionSet.actionSet[1].function)
      self.failUnlessEqual(None, actionSet.actionSet[1].extension)
      self.failUnlessEqual(300, actionSet.actionSet[2].index)
      self.failUnlessEqual(executeStore, actionSet.actionSet[2].function)
      self.failUnlessEqual(None, actionSet.actionSet[2].extension)
      self.failUnlessEqual(400, actionSet.actionSet[3].index)
      self.failUnlessEqual(executePurge, actionSet.actionSet[3].function)
      self.failUnlessEqual(None, actionSet.actionSet[3].extension)

   def testActionSet_105(self):
      """
      Test with actions=[ stage, purge, collect, store ], extensions=[].
      """
      actions = [ "stage", "purge", "collect", "store", ]
      extensions = []
      actionSet = _ActionSet(actions, extensions)
      self.failUnless(len(actionSet.actionSet) == 4)
      self.failUnlessEqual(100, actionSet.actionSet[0].index)
      self.failUnlessEqual(executeCollect, actionSet.actionSet[0].function)
      self.failUnlessEqual(None, actionSet.actionSet[0].extension)
      self.failUnlessEqual(200, actionSet.actionSet[1].index)
      self.failUnlessEqual(executeStage, actionSet.actionSet[1].function)
      self.failUnlessEqual(None, actionSet.actionSet[1].extension)
      self.failUnlessEqual(300, actionSet.actionSet[2].index)
      self.failUnlessEqual(executeStore, actionSet.actionSet[2].function)
      self.failUnlessEqual(None, actionSet.actionSet[2].extension)
      self.failUnlessEqual(400, actionSet.actionSet[3].index)
      self.failUnlessEqual(executePurge, actionSet.actionSet[3].function)
      self.failUnlessEqual(None, actionSet.actionSet[3].extension)

   def testActionSet_106(self):
      """
      Test with actions=[ collect, stage, store, purge, one, two, three, four, five ], extensions=[ (index 50, 150, 250, 350, 450)].
      """
      actions = [ "collect", "stage", "store", "purge", "one", "two", "three", "four", "five", ]
      extensions = [ ExtendedAction("one", "a", "b", 50), ExtendedAction("two", "a", "b", 150), 
                     ExtendedAction("three", "a", "b", 250), ExtendedAction("four", "a", "b", 350), 
                     ExtendedAction("five", "a", "b", 450), ]
      actionSet = _ActionSet(actions, extensions)
      self.failUnless(len(actionSet.actionSet) == 9)
      self.failUnlessEqual(50, actionSet.actionSet[0].index)
      self.failUnlessEqual(None, actionSet.actionSet[0].function)
      self.failUnlessEqual(ExtendedAction("one", "a", "b", 50), actionSet.actionSet[0].extension)
      self.failUnlessEqual(100, actionSet.actionSet[1].index)
      self.failUnlessEqual(executeCollect, actionSet.actionSet[1].function)
      self.failUnlessEqual(None, actionSet.actionSet[1].extension)
      self.failUnlessEqual(150, actionSet.actionSet[2].index)
      self.failUnlessEqual(None, actionSet.actionSet[2].function)
      self.failUnlessEqual(ExtendedAction("two", "a", "b", 150), actionSet.actionSet[2].extension)
      self.failUnlessEqual(200, actionSet.actionSet[3].index)
      self.failUnlessEqual(executeStage, actionSet.actionSet[3].function)
      self.failUnlessEqual(None, actionSet.actionSet[3].extension)
      self.failUnlessEqual(250, actionSet.actionSet[4].index)
      self.failUnlessEqual(None, actionSet.actionSet[4].function)
      self.failUnlessEqual(ExtendedAction("three", "a", "b", 250), actionSet.actionSet[4].extension)
      self.failUnlessEqual(300, actionSet.actionSet[5].index)
      self.failUnlessEqual(executeStore, actionSet.actionSet[5].function)
      self.failUnlessEqual(None, actionSet.actionSet[5].extension)
      self.failUnlessEqual(350, actionSet.actionSet[6].index)
      self.failUnlessEqual(None, actionSet.actionSet[6].function)
      self.failUnlessEqual(ExtendedAction("four", "a", "b", 350), actionSet.actionSet[6].extension)
      self.failUnlessEqual(400, actionSet.actionSet[7].index)
      self.failUnlessEqual(executePurge, actionSet.actionSet[7].function)
      self.failUnlessEqual(None, actionSet.actionSet[7].extension)
      self.failUnlessEqual(450, actionSet.actionSet[8].index)
      self.failUnlessEqual(None, actionSet.actionSet[8].function)
      self.failUnlessEqual(ExtendedAction("five", "a", "b", 450), actionSet.actionSet[8].extension)

   def testActionSet_107(self):
      """
      Test with actions=[ one, five, collect, store, three, stage, four, purge, two ], extensions=[ (index 50, 150, 250, 350, 450)].
      """
      actions = [ "one", "five", "collect", "store", "three", "stage", "four", "purge", "two", ]
      extensions = [ ExtendedAction("one", "a", "b", 50), ExtendedAction("two", "a", "b", 150), 
                     ExtendedAction("three", "a", "b", 250), ExtendedAction("four", "a", "b", 350), 
                     ExtendedAction("five", "a", "b", 450), ]
      actionSet = _ActionSet(actions, extensions)
      self.failUnless(len(actionSet.actionSet) == 9)
      self.failUnlessEqual(50, actionSet.actionSet[0].index)
      self.failUnlessEqual(None, actionSet.actionSet[0].function)
      self.failUnlessEqual(ExtendedAction("one", "a", "b", 50), actionSet.actionSet[0].extension)
      self.failUnlessEqual(100, actionSet.actionSet[1].index)
      self.failUnlessEqual(executeCollect, actionSet.actionSet[1].function)
      self.failUnlessEqual(None, actionSet.actionSet[1].extension)
      self.failUnlessEqual(150, actionSet.actionSet[2].index)
      self.failUnlessEqual(None, actionSet.actionSet[2].function)
      self.failUnlessEqual(ExtendedAction("two", "a", "b", 150), actionSet.actionSet[2].extension)
      self.failUnlessEqual(200, actionSet.actionSet[3].index)
      self.failUnlessEqual(executeStage, actionSet.actionSet[3].function)
      self.failUnlessEqual(None, actionSet.actionSet[3].extension)
      self.failUnlessEqual(250, actionSet.actionSet[4].index)
      self.failUnlessEqual(None, actionSet.actionSet[4].function)
      self.failUnlessEqual(ExtendedAction("three", "a", "b", 250), actionSet.actionSet[4].extension)
      self.failUnlessEqual(300, actionSet.actionSet[5].index)
      self.failUnlessEqual(executeStore, actionSet.actionSet[5].function)
      self.failUnlessEqual(None, actionSet.actionSet[5].extension)
      self.failUnlessEqual(350, actionSet.actionSet[6].index)
      self.failUnlessEqual(None, actionSet.actionSet[6].function)
      self.failUnlessEqual(ExtendedAction("four", "a", "b", 350), actionSet.actionSet[6].extension)
      self.failUnlessEqual(400, actionSet.actionSet[7].index)
      self.failUnlessEqual(executePurge, actionSet.actionSet[7].function)
      self.failUnlessEqual(None, actionSet.actionSet[7].extension)
      self.failUnlessEqual(450, actionSet.actionSet[8].index)
      self.failUnlessEqual(None, actionSet.actionSet[8].function)
      self.failUnlessEqual(ExtendedAction("five", "a", "b", 450), actionSet.actionSet[8].extension)


#######################################################################
# Suite definition
#######################################################################

def suite():
   """Returns a suite containing all the test cases in this module."""
   return unittest.TestSuite((
                              unittest.makeSuite(TestFunctions, 'test'), 
                              unittest.makeSuite(TestOptions, 'test'), 
                              unittest.makeSuite(TestActionSet, 'test'), 
                            ))


########################################################################
# Module entry point
########################################################################

# When this module is executed from the command-line, run its tests
if __name__ == '__main__':
   unittest.main()

