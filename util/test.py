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
# Purpose  : Run all of the unit tests for the project.
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# This file was created with a width of 132 characters, and NO tabs.

########################################################################
# Notes
########################################################################

"""
Run all of the CedarBackup2 unit tests.

We run all of the unit tests here at once so we can get one big success or
failure result, rather than 20 different smaller results that we somehow have
to aggregate together to get the "big picture".  This is done by creating and
running one big unit test suite based on the suites in the individual unit test
modules.

The composite suite is always run using the TextTestRunner at verbosity level
1, which prints one dot (".") on the screen for each test run.  This output is
the same as one would get when using unittest.main() in an individual test.

If possible, I try to run the unit tests using psyco.  It typically gets me a
net speed-up on processor-intensive operations.

Generally, I'm trying to keep all of the "special" validation logic (i.e. did
we find the right Python, did we find the right libraries, etc.) in this code
rather than in the individual unit tests so they're more focused on what to
test than how their environment should be configured.

We want to make sure the tests use the modules in the current source tree, not
any versions previously-installed elsewhere, if possible.  We don't actually
import the modules here, but we warn if the wrong ones would be found.  (The
filesystem.py check below is just one example of one of the files we would
expect to find in the CedarBackup2 directory.)

We also want to make sure we are running the correct 'test' package - not one
found elsewhere on the user's path - since 'test' could be a relatively common
name for a package.  (The filesystemtests.py import below is just one example
of one of the files we would expect to find in the CedarBackup2 unittest
directory.)

@author: Kenneth J. Pronovici <pronovic@ieee.org>
"""

########################################################################
# Imported modules
########################################################################

import sys
import os
import unittest


##################
# main() function
##################

def main():

   """
   Main routine for program.
   """

   # Check the Python version.  We require 2.3 or greater.
   try:
      if map(int, [sys.version_info[0], sys.version_info[1]]) < [2, 3]:
         print "Python version 2.3 or greater required, sorry."
         sys.exit(1)
   except:
      # sys.version_info isn't available before 2.0
      print "Python version 2.3 or greater required, sorry."
      sys.exit(1)

   # Check for the correct CedarBackup2 location
   if os.path.exists(os.path.join(".", "CedarBackup2", "filesystem.py")):
      sys.path.insert(0, ".")
   elif os.path.basename(os.getcwd()) == "test" and os.path.exists(os.path.join("..", "CedarBackup2", "filesystem.py")):
      sys.path.insert(0, "..")
   else:
      print "WARNING: CedarBackup2 modules were not found in the expected"
      print "location.  If the import succeeds, you may be using an"
      print "unexpected version of CedarBackup2."
      print ""

   # Import the unit test modules
   try:
      if os.path.exists(os.path.join(".", "test", "filesystemtests.py")):
         sys.path.insert(0, ".")
      elif os.path.basename(os.getcwd()) == "test" and os.path.exists(os.path.join("..", "test", "filesystemtests.py")):
         sys.path.insert(0, "..")
      else:
         print "WARNING: CedarBackup2 unit test modules were not found in"
         print "the expected location.  If the import succeeds, you may be"
         print "using an unexpected version of the test suite."
         print ""
      import test.knapsacktests as knapsacktests
      import test.filesystemtests as filesystemtests
   except ImportError, e:
      print "Failed to import CedarBackup2 unit test module: %s" % e
      print "You must either run the unit tests from the CedarBackup2 source"
      print "tree, or properly set the PYTHONPATH enviroment variable."
      sys.exit(1)

   # Print a starting banner
   print "\n*** Running CedarBackup2 unit tests."

   # Import psycho if possible
   try:
      import psyco
      psyco.full()
      print "*** Note: using pyscho for speedup, since it's available."
   except: pass

   # Create and run the test suite
   print ""
   suite = unittest.TestSuite((knapsacktests.suite(), filesystemtests.suite()))
#   suite = unittest.TestSuite((filesystemtests.suite(),))
   unittest.TextTestRunner(verbosity=1).run(suite)
   print ""


########################################################################
# Module entry point
########################################################################

# Run the main routine if the module is executed rather than sourced
if __name__ == '__main__':
   main()

