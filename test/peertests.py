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
# Purpose  : Tests peer functionality.
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# This file was created with a width of 132 characters, and NO tabs.

########################################################################
# Module documentation
########################################################################

"""
Unit tests for CedarBackup2/peer.py.

Code Coverage
=============

   This module contains individual tests for most of the public functions
   and classes implemented in peer.py: the C{LocalPeer} and C{RemotePeer} 
   classes and C{executeCommand()} function.  The C{getUidGid} function is
   not tested because it's trivial.

   There are some parts of this functionality that can't be tested easily.  For
   instance, the stage code allows the caller to change ownership on files.
   Generally, this can only be done by root, and we won't be running these
   tests as root.  We'll have to hope that the code that tests the way
   permissions are changed gives us enough coverage.

   Network-related testing also causes us problems.  In order to test the
   RemotePeer, we need a "remote" host that we can rcp to and from.  We want to
   fall back on using localhost and the current user, but that might not be
   safe or appropriate.  The compromise is that the remote peer tests will only
   be run if PEERTESTS_REMOTE is set to "Y" in the environment.

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
import sys
import unittest
from CedarBackup2.peer import getUidGid, executeCommand, LocalPeer, RemotePeer


#######################################################################
# Module-wide configuration and constants
#######################################################################

DATA_DIRS = [ './data', './test/data' ]
RESOURCES = [ "tree1.tar.gz", "tree2.tar.gz", "tree3.tar.gz", "tree4.tar.gz", "tree5.tar.gz",
              "tree6.tar.gz", "tree7.tar.gz", "tree8.tar.gz", "tree9.tar.gz", "tree10.tar.gz", ]

INVALID_FILE = "bogus"         # This file name should never exist


####################
# Utility functions
####################

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

def extractTar(tmpdir, filepath):
   """Extracts the indicated tar file to self.tmpdir."""
   tar = tarfile.open(filepath)
   for tarinfo in tar:
      tar.extract(tarinfo, tmpdir)

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
      command="echo"
      args=[]
      (result, output) = executeCommand(command, args, returnOutput=False)
      self.failUnlessEqual(0, result)
      self.failUnlessEqual(None, output)

   def testExecuteCommand_002(self):
      """
      Execute a command that should succeed, one argument, returnOutput=False
      Command-line: python -V
      """
      command="python"
      args=["-V", ]
      (result, output) = executeCommand(command, args, returnOutput=False)
      self.failUnlessEqual(0, result)
      self.failUnlessEqual(None, output)

   def testExecuteCommand_003(self):
      """
      Execute a command that should succeed, two arguments, returnOutput=False
      Command-line: python -c "import sys; print sys.argv[1:]; sys.exit(0)"
      """
      command="python"
      args=["-c", "import sys; print sys.argv[1:]; sys.exit(0)", ]
      (result, output) = executeCommand(command, args, returnOutput=False)
      self.failUnlessEqual(0, result)
      self.failUnlessEqual(None, output)

   def testExecuteCommand_004(self):
      """
      Execute a command that should succeed, three arguments, returnOutput=False
      Command-line: python -c "import sys; print sys.argv[1:]; sys.exit(0)" first
      """
      command="python"
      args=["-c", "import sys; print sys.argv[1:]; sys.exit(0)", "first", ]
      (result, output) = executeCommand(command, args, returnOutput=False)
      self.failUnlessEqual(0, result)
      self.failUnlessEqual(None, output)

   def testExecuteCommand_005(self):
      """
      Execute a command that should succeed, four arguments, returnOutput=False
      Command-line: python -c "import sys; print sys.argv[1:]; sys.exit(0)" first second
      """
      command="python"
      args=["-c", "import sys; print sys.argv[1:]; sys.exit(0)", "first", "second", ]
      (result, output) = executeCommand(command, args, returnOutput=False)
      self.failUnlessEqual(0, result)
      self.failUnlessEqual(None, output)

   def testExecuteCommand_005(self):
      """
      Execute a command that should fail, returnOutput=False
      Command-line: python -c "import sys; print sys.argv[1:]; sys.exit(1)"
      """
      command="python"
      args=["-c", "import sys; print sys.argv[1:]; sys.exit(1)", ]
      (result, output) = executeCommand(command, args, returnOutput=False)
      self.failIfEqual(0, result)
      self.failUnlessEqual(None, output)

   def testExecuteCommand_006(self):
      """
      Execute a command that should fail, more arguments, returnOutput=False
      Command-line: python -c "import sys; print sys.argv[1:]; sys.exit(1)" first second
      """
      command="python"
      args=["-c", "import sys; print sys.argv[1:]; sys.exit(1)", "first", "second", ]
      (result, output) = executeCommand(command, args, returnOutput=False)
      self.failIfEqual(0, result)
      self.failUnlessEqual(None, output)

   def testExecuteCommand_009(self):
      """
      Execute a command that should succeed, no arguments, returnOutput=True
      Command-line: echo
      """
      command="echo"
      args=[]
      (result, output) = executeCommand(command, args, returnOutput=True)
      self.failUnlessEqual(0, result)
      self.failUnlessEqual(1, len(output))
      self.failUnlessEqual("\n", output[0])

   def testExecuteCommand_010(self):
      """
      Execute a command that should succeed, one argument, returnOutput=True
      Command-line: python -V
      """
      command="python"
      args=["-V", ]
      (result, output) = executeCommand(command, args, returnOutput=True)
      self.failUnlessEqual(0, result)
      self.failUnlessEqual(1, len(output))
      self.failUnless(output[0].startswith("Python"))

   def testExecuteCommand_011(self):
      """
      Execute a command that should succeed, two arguments, returnOutput=True
      Command-line: python -c "import sys; print ''; sys.exit(0)"
      """
      command="python"
      args=["-c", "import sys; print ''; sys.exit(0)", ]
      (result, output) = executeCommand(command, args, returnOutput=True)
      self.failUnlessEqual(0, result)
      self.failUnlessEqual(1, len(output))
      self.failUnlessEqual("\n", output[0])

   def testExecuteCommand_012(self):
      """
      Execute a command that should succeed, three arguments, returnOutput=True
      Command-line: python -c "import sys; print '%s' % (sys.argv[1]); sys.exit(0)" first
      """
      command="python"
      args=["-c", "import sys; print '%s' % (sys.argv[1]); sys.exit(0)", "first", ]
      (result, output) = executeCommand(command, args, returnOutput=True)
      self.failUnlessEqual(0, result)
      self.failUnlessEqual(1, len(output))
      self.failUnlessEqual("first\n", output[0])

   def testExecuteCommand_013(self):
      """
      Execute a command that should succeed, four arguments, returnOutput=True
      Command-line: python -c "import sys; print '%s' % sys.argv[1]; print '%s' % sys.argv[2]; sys.exit(0)" first second
      """
      command="python"
      args=["-c", "import sys; print '%s' % sys.argv[1]; print '%s' % sys.argv[2]; sys.exit(0)", "first", "second", ]
      (result, output) = executeCommand(command, args, returnOutput=True)
      self.failUnlessEqual(0, result)
      self.failUnlessEqual(2, len(output))
      self.failUnlessEqual("first\n", output[0])
      self.failUnlessEqual("second\n", output[1])

   def testExecuteCommand_005(self):
      """
      Execute a command that should fail, returnOutput=True
      Command-line: python -c "import sys; print ''; sys.exit(1)"
      """
      command="python"
      args=["-c", "import sys; print ''; sys.exit(1)", ]
      (result, output) = executeCommand(command, args, returnOutput=True)
      self.failIfEqual(0, result)
      self.failUnlessEqual(1, len(output))
      self.failUnlessEqual("\n", output[0])

   def testExecuteCommand_006(self):
      """
      Execute a command that should fail, more arguments, returnOutput=True
      Command-line: python -c "import sys; print '%s' % sys.argv[1]; print '%s' % sys.argv[2]; sys.exit(1)" first second
      """
      command="python"
      args=["-c", "import sys; print '%s' % sys.argv[1]; print '%s' % sys.argv[2]; sys.exit(1)", "first", "second", ]
      (result, output) = executeCommand(command, args, returnOutput=True)
      self.failIfEqual(0, result)
      self.failUnlessEqual(2, len(output))
      self.failUnlessEqual("first\n", output[0])
      self.failUnlessEqual("second\n", output[1])


######################
# TestLocalPeer class
######################

class TestLocalPeer(unittest.TestCase):

   """Tests for the LocalPeer class."""

   ################
   # Setup methods
   ################

   def setUp(self):
      pass

   def tearDown(self):
      pass

   ###########################
   # Test basic functionality
   ###########################

   def testBasic_001(self):
      """
      Make sure exception is thrown for non-absolute collect directory.
      """
      pass

   def testBasic_002(self):
      """
      Make sure attributes are set properly for valid constructor input.
      """
      pass


   ###############################
   # Test checkCollectIndicator()
   ###############################

   def testCheckCollectIndicator_001(self):
      """
      Attempt to check collect indicator with non-existent collect directory.
      """
      pass

   def testCheckCollectIndicator_002(self):
      """
      Attempt to check collect indicator with non-readable collect directory.
      """
      pass

   def testCheckCollectIndicator_003(self):
      """
      Attempt to check collect indicator collect indicator file that does not exist.
      """
      pass

   def testCheckCollectIndicator_004(self):
      """
      Attempt to check collect indicator collect indicator file that does exist.
      """
      pass


   #############################
   # Test writeStageIndicator()
   #############################

   def testWriteStageIndicator_001(self):
      """
      Attempt to write stage indicator with non-existent collect directory.
      """
      pass

   def testWriteStageIndicator_002(self):
      """
      Attempt to write stage indicator with non-writable collect directory.
      """
      pass

   def testWriteStageIndicator_003(self):
      """
      Attempt to write stage indicator in a valid directory.
      """
      pass


   ###################
   # Test stagePeer()
   ###################

   def testStagePeer_001(self):
      """
      Attempt to stage files with non-existent collect directory.
      """
      pass

   def testStagePeer_002(self):
      """
      Attempt to stage files with non-readable collect directory.
      """
      pass

   def testStagePeer_003(self):
      """
      Attempt to stage files with non-absolute target directory.
      """
      pass

   def testStagePeer_004(self):
      """
      Attempt to stage files with non-existent target directory.
      """
      pass

   def testStagePeer_005(self):
      """
      Attempt to stage files with non-writable target directory.
      """
      pass

   def testStagePeer_006(self):
      """
      Attempt to stage files with empty collect directory.
      """
      pass

   def testStagePeer_007(self):
      """
      Attempt to stage files with non-empty collect directory.
      """
      pass

   def testStagePeer_008(self):
      """
      Attempt to stage files with non-empty collect directory containing links and directories.
      """
      pass

   def testStagePeer_009(self):
      """
      Attempt to stage files with non-empty collect directory and attempt to set valid permissions.
      """
      pass

   def testStagePeer_010(self):
      """
      Attempt to stage files with non-empty collect directory and attempt to set invalid permissions.
      """
      pass


######################
# TestRemotePeer class
######################

class TestRemotePeer(unittest.TestCase):

   """Tests for the RemotePeer class."""

   ################
   # Setup methods
   ################

   def setUp(self):
      pass

   def tearDown(self):
      pass


   ############################
   # Tests basic functionality
   ############################

   def testBasic_001(self):
      """
      Make sure exception is thrown for non-absolute collect directory.
      """
      pass

   def testBasic_002(self):
      """
      Make sure attributes are set properly for valid constructor input.
      """
      pass


   ###############################
   # Test checkCollectIndicator()
   ###############################

   def testCheckCollectIndicator_001(self):
      """
      Attempt to check collect indicator with invalid hostname.
      """
      pass

   def testCheckCollectIndicator_002(self):
      """
      Attempt to check collect indicator with invalid remote user.
      """
      pass

   def testCheckCollectIndicator_003(self):
      """
      Attempt to check collect indicator with invalid rcp command.
      """
      pass

   def testCheckCollectIndicator_004(self):
      """
      Attempt to stage files with a valid rcp command that will have
      connectivity problems.
      """
      pass

   def testCheckCollectIndicator_005(self):
      """
      Attempt to check collect indicator with non-existent collect directory.
      """
      pass

   def testCheckCollectIndicator_006(self):
      """
      Attempt to check collect indicator with non-readable collect directory.
      """
      pass

   def testCheckCollectIndicator_007(self):
      """
      Attempt to check collect indicator collect indicator file that does not exist.
      """
      pass

   def testCheckCollectIndicator_008(self):
      """
      Attempt to check collect indicator collect indicator file that does exist.
      """
      pass


   #############################
   # Test writeStageIndicator()
   #############################

   def testWriteStageIndicator_001(self):
      """
      Attempt to write stage indicator with invalid hostname.
      """
      pass

   def testWriteStageIndicator_002(self):
      """
      Attempt to write stage indicator with invalid remote user.
      """
      pass

   def testWriteStageIndicator_003(self):
      """
      Attempt to write stage indicator with invalid rcp command.
      """
      pass

   def testWriteStageIndicator_004(self):
      """
      Attempt to stage files with a valid rcp command that will have
      connectivity problems.
      """
      pass

   def testWriteStageIndicator_005(self):
      """
      Attempt to write stage indicator with non-existent collect directory.
      """
      pass

   def testWriteStageIndicator_006(self):
      """
      Attempt to write stage indicator with non-writable collect directory.
      """
      pass

   def testWriteStageIndicator_007(self):
      """
      Attempt to write stage indicator in a valid directory.
      """
      pass


   ###################
   # Test stagePeer()
   ###################

   def testStagePeer_001(self):
      """
      Attempt to stage files with invalid hostname.
      """
      pass

   def testStagePeer_002(self):
      """
      Attempt to stage files with invalid remote user.
      """
      pass

   def testStagePeer_003(self):
      """
      Attempt to stage files with invalid rcp command.
      """
      pass

   def testStagePeer_004(self):
      """
      Attempt to stage files with a valid rcp command that will have
      connectivity problems.
      """
      pass

   def testStagePeer_005(self):
      """
      Attempt to stage files with non-existent collect directory.
      """
      pass

   def testStagePeer_006(self):
      """
      Attempt to stage files with non-readable collect directory.
      """
      pass

   def testStagePeer_007(self):
      """
      Attempt to stage files with non-absolute target directory.
      """
      pass

   def testStagePeer_008(self):
      """
      Attempt to stage files with non-existent target directory.
      """
      pass

   def testStagePeer_009(self):
      """
      Attempt to stage files with non-writable target directory.
      """
      pass

   def testStagePeer_010(self):
      """
      Attempt to stage files with empty collect directory.
      """
      pass

   def testStagePeer_011(self):
      """
      Attempt to stage files with non-empty collect directory.
      """
      pass

   def testStagePeer_012(self):
      """
      Attempt to stage files with non-empty collect directory containing links and directories.
      """
      pass

   def testStagePeer_013(self):
      """
      Attempt to stage files with non-empty collect directory and attempt to set valid permissions.
      """
      pass

   def testStagePeer_014(self):
      """
      Attempt to stage files with non-empty collect directory and attempt to set invalid permissions.
      """
      pass


#######################################################################
# Suite definition
#######################################################################

def suite():
   """Returns a suite containing all the test cases in this module."""
   return unittest.TestSuite((
                              unittest.makeSuite(TestFunctions, 'test'),
                              unittest.makeSuite(TestLocalPeer, 'test'),
                              unittest.makeSuite(TestRemotePeer, 'test'), 
                            ))


########################################################################
# Module entry point
########################################################################

# When this module is executed from the command-line, run its tests
if __name__ == '__main__':
   unittest.main()

