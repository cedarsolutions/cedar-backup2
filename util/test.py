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
# Purpose  : Run all of the unit tests for the project.
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

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

Generally, I'm trying to keep all of the "special" validation logic (i.e. did
we find the right Python, did we find the right libraries, etc.) in this code
rather than in the individual unit tests so they're more focused on what to
test than how their environment should be configured.

We want to make sure the tests use the modules in the current source tree, not
any versions previously-installed elsewhere, if possible.  We don't actually
import the modules here, but we warn if the wrong ones would be found.  We also
want to make sure we are running the correct 'test' package - not one found
elsewhere on the user's path - since 'test' could be a relatively common name
for a package.

Finally, this script might be used by people who won't have an environment that
allows running all of the tests, especially certain tests related to remote
connectivity, loopback filesystems, etc.  Most people should run the script
with no arguments.  This will result in a "reduced feature set" test suite with
no surprising system, kernel or network dependencies.  People who understand
what they're doing can put "full" as one of the arguments on the command-line,
and they'll get all of the available tests (or they can dig further and
explicitly set certain environment variables to get more precise control over
what will be tested).

@note: Even if you run this test with the C{python2.3} interpreter, some of the
individual unit tests require the C{python} interpreter.  In particular, the
utility tests (in test/utiltests.py) use brief Python script snippets with
known results to verify the behavior of C{executeCommand}.

@author: Kenneth J. Pronovici <pronovic@ieee.org>
"""

########################################################################
# Imported modules
########################################################################

import sys
import os
import logging
import unittest


##################
# main() function
##################

def main():

   """
   Main routine for program.
   @return: Integer 0 upon success, integer 1 upon failure.
   """

   # Check the Python version.  We require 2.3 or greater.
   try:
      if map(int, [sys.version_info[0], sys.version_info[1]]) < [2, 3]:
         print "Python version 2.3 or greater required, sorry."
         return 1
   except:
      # sys.version_info isn't available before 2.0
      print "Python version 2.3 or greater required, sorry."
      return 1

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
      import test.utiltests as utiltests
      import test.knapsacktests as knapsacktests
      import test.filesystemtests as filesystemtests
      import test.peertests as peertests
      import test.imagetests as imagetests
      import test.writertests as writertests
      import test.configtests as configtests
      import test.clitests as clitests
      import test.mysqltests as mysqltests
      import test.subversiontests as subversiontests
      import test.mboxtests as mboxtests
   except ImportError, e:
      print "Failed to import CedarBackup2 unit test module: %s" % e
      print "You must either run the unit tests from the CedarBackup2 source"
      print "tree, or properly set the PYTHONPATH enviroment variable."
      return 1

   # Set flags in the environment to control tests
   if "full" in sys.argv:
      os.environ["PEERTESTS_FULL"] = "Y"
      os.environ["IMAGETESTS_FULL"] = "Y"
   else:
      os.environ["PEERTESTS_FULL"] = "N"
      os.environ["IMAGETESTS_FULL"] = "N"

   # Set up logging to discard everything
   handler = logging.FileHandler(filename="/dev/null")
   handler.setLevel(logging.NOTSET)
   logger = logging.getLogger("CedarBackup2")
   logger.setLevel(logging.NOTSET)
   logger.addHandler(handler)

   # Print a starting banner
   print "\n*** Running CedarBackup2 unit tests."

   # Create and run the test suite
   print ""
   suite = unittest.TestSuite((
                               utiltests.suite(),
                               knapsacktests.suite(), 
                               filesystemtests.suite(),
                               peertests.suite(),
                               imagetests.suite(),
                               writertests.suite(),
                               configtests.suite(),
                               clitests.suite(),
                               mysqltests.suite(),
                               subversiontests.suite(),
                               mboxtests.suite(),
                              ))
   result = unittest.TextTestRunner(verbosity=1).run(suite)
   print ""
   if not result.wasSuccessful():
      return 1
   else:
      return 0


########################################################################
# Module entry point
########################################################################

# Run the main routine if the module is executed rather than sourced
if __name__ == '__main__':
   result = main()
   sys.exit(result)

