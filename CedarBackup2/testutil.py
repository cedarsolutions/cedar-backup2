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
# Purpose  : Provides unit-testing utilities.
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# This file was created with a width of 132 characters, and NO tabs.

########################################################################
# Module documentation
########################################################################

"""
Provides unit-testing utilities. 

These utilities are kept here, separate from util.py, because they provide
common functionality that I do not want exported "publicly" once Cedar Backup
is installed on a system.  They are only used for unit testing, and are only
useful within the source tree.

Many of these functions are in here because they are "good enough" for unit
test work but are not robust enough to be real public functions.  Others (like
L{removedir} do what they are supposed to, but I don't want responsibility for
making them available to others.

@sort: findResources, buildPath, removedir, extractTar, changeFileAge,
       getMaskAsMode, getLogin, failUnlessAssignRaises

@author: Kenneth J. Pronovici <pronovic@ieee.org>
"""


########################################################################
# Imported modules
########################################################################

import os
import tarfile
import time
import getpass


########################################################################
# Public functions
########################################################################

###########################
# findResources() function
###########################

def findResources(resources, dataDirs):
   """
   Returns a dictionary of locations for various resources.
   @param resources: List of required resources.
   @param dataDirs: List of data directories to search within for resources.
   @return: Dictionary mapping resource name to resource path.
   @raise Exception: If some resource cannot be found.
   """
   mapping = { }
   for resource in resources:
      for resourceDir in dataDirs:
         path = os.path.join(resourceDir, resource);
         if os.path.exists(path):
            mapping[resource] = path
            break
      else:
         raise Exception("Unable to find resource [%s]." % resource)
   return mapping


#######################
# buildPath() function
#######################

def buildPath(components):
   """
   Builds a complete path from a list of components.
   For instance, constructs C{"/a/b/c"} from C{["/a", "b", "c",]}.
   @param components: List of components.
   @returns: String path constructed from components.
   """
   path = components[0]
   for component in components[1:]:
      path = os.path.join(path, component)
   return path


#######################
# removedir() function
#######################

def removedir(tree):
   """
   Recursively removes an entire directory.
   This is basically taken from an example on python.com.  
   @param tree: Directory tree to remove.
   """
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


########################
# extractTar() function
########################

def extractTar(tmpdir, filepath):
   """
   Extracts the indicated tar file to the indicated tmpdir.
   @param tmpdir: Temp directory to extract to.
   @param filepath: Path to tarfile to extract.
   """
   tar = tarfile.open(filepath)
   for tarinfo in tar:
      tar.extract(tarinfo, tmpdir)


###########################
# changeFileAge() function
###########################

def changeFileAge(file, subtract=None):
   """
   Changes a file age using the C{os.utime} function.
   @param subtract: Number of seconds to subtract from the current time.
   """
   if subtract is None:
      os.utime(file, None)
   else:
      newTime = time.time() - subtract
      os.utime(file, (newTime, newTime))


###########################
# getMaskAsMode() function
###########################

def getMaskAsMode():
   """
   Returns the user's current umask inverted to a mode.
   A mode is mostly a bitwise inversion of a mask, i.e. mask 002 is mode 775.
   @return: Umask converted to a mode, as an integer.
   """
   umask = os.umask(0777)
   os.umask(umask)
   return int(~umask & 0777)  # invert, then use only lower bytes


######################
# getLogin() function
######################

def getLogin():
   """
   Returns the name of the currently-logged in user.  This might fail under
   some circumstances - but if it does, our tests would fail anyway.
   """
   return getpass.getuser()


####################################
# failUnlessAssignRaises() function
####################################

def failUnlessAssignRaises(testCase, exception, object, property, value):
   """
   Equivalent of C{failUnlessRaises}, but used for property assignments instead.

   It's nice to be able to use C{failUnlessRaises} to check that a method call
   raises the exception that you expect.  Unfortunately, this method can't be
   used to check Python propery assignments, even though these property
   assignments are actually implemented underneath as methods.

   This function (which can be easily called by unit test classes) provides an
   easy way to wrap the assignment checks.  It's not pretty, or as intuitive as
   the original check it's modeled on, but it does work.

   Let's assume you make this method call:

      testCase.failUnlessAssignRaises(ValueError, collectDir, "absolutePath", absolutePath)

   If you do this, a test case failure will be raised unless the assignment:

      collectDir.absolutePath = absolutePath

   fails with a C{ValueError} exception.  The failure message differentiates
   between the case where no exception was raised and the case where the wrong
   exception was raised.

   @note: Internally, the C{missed} and C{instead} variables are used rather
   than directly calling C{testCase.fail} upon noticing a problem because the
   act of "failure" itself generates an exception that would be caught by the
   general C{except} clause.

   @param testCase: PyUnit test case object (i.e. self).
   @param exception: Exception that is expected to be raised.
   @param object: Object whose property is to be assigned to.
   @param property: Name of the property, as a string.
   @param value: Value that is to be assigned to the property.

   @see: L{unittest.TestCase.failUnlessRaises}
   """
   missed = False
   instead = None
   try:
      exec "object.%s = value" % property
      missed = True
   except exception: pass
   except Exception, e: instead = e
   if missed:
      testCase.fail("Expected assignment to raise %s, but got no exception." % (exception.__name__))
   if instead is not None:
      testCase.fail("Expected assignment to raise %s, but got %s instead." % (ValueError, instead.__class__.__name__))

