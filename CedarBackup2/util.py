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
# Portions copyright (c) 2001, 2002 Python Software Foundation.
# All Rights Reserved.
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
# Purpose  : Provides general-purpose utilities.
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

########################################################################
# Module documentation
########################################################################

"""
Provides general-purpose utilities. 

@sort: AbsolutePathList, ObjectTypeList, PathResolverSingleton, 
       convertSize, getUidGid, changeOwnership, splitCommandLine, 
       resolveCommand, executeCommand, calculateFileAge, encodePath, nullDevice,
       deriveDayOfWeek, isStartOfWeek, buildNormalizedPath, 
       validateScsiId, validateDevice, validateDriveSpeed,
       ISO_SECTOR_SIZE, BYTES_PER_SECTOR, 
       BYTES_PER_KBYTE, BYTES_PER_MBYTE, BYTES_PER_GBYTE, KBYTES_PER_MBYTE, MBYTES_PER_GBYTE, 
       SECONDS_PER_MINUTE, MINUTES_PER_HOUR, HOURS_PER_DAY, SECONDS_PER_DAY, 
       UNIT_BYTES, UNIT_KBYTES, UNIT_MBYTES, UNIT_GBYTES, UNIT_SECTORS

@var ISO_SECTOR_SIZE: Size of an ISO image sector, in bytes.
@var BYTES_PER_SECTOR: Number of bytes (B) per ISO sector.
@var BYTES_PER_KBYTE: Number of bytes (B) per kilobyte (kB).
@var BYTES_PER_MBYTE: Number of bytes (B) per megabyte (MB).
@var BYTES_PER_GBYTE: Number of bytes (B) per megabyte (GB).
@var KBYTES_PER_MBYTE: Number of kilobytes (kB) per megabyte (MB).
@var MBYTES_PER_GBYTE: Number of megabytes (MB) per gigabyte (GB).
@var SECONDS_PER_MINUTE: Number of seconds per minute.
@var MINUTES_PER_HOUR: Number of minutes per hour.
@var HOURS_PER_DAY: Number of hours per day.
@var SECONDS_PER_DAY: Number of seconds per day.
@var UNIT_BYTES: Constant representing the byte (B) unit for conversion.
@var UNIT_KBYTES: Constant representing the kilobyte (kB) unit for conversion.
@var UNIT_MBYTES: Constant representing the megabyte (MB) unit for conversion.
@var UNIT_GBYTES: Constant representing the gigabyte (GB) unit for conversion.
@var UNIT_SECTORS: Constant representing the ISO sector unit for conversion.

@author: Kenneth J. Pronovici <pronovic@ieee.org>
"""


########################################################################
# Imported modules
########################################################################

import sys
import math
import os
import re
import time
import logging
import string

try:
   import pwd
   import grp
   _UID_GID_AVAILABLE = True   
except ImportError:
   _UID_GID_AVAILABLE = False   

try:
   from subprocess import Popen
   _PIPE_IMPLEMENTATION = "subprocess.Popen"
except ImportError:
   try:
      from popen2 import Popen4
      _PIPE_IMPLEMENTATION = "popen2.Popen4"
   except ImportError:
      raise ImportError("Unable to import either subprocess.Popen or popen2.Popen4 for use by Pipe class.")


########################################################################
# Module-wide constants and variables
########################################################################

logger = logging.getLogger("CedarBackup2.log.util")
outputLogger = logging.getLogger("CedarBackup2.output")

ISO_SECTOR_SIZE    = 2048.0   # in bytes
BYTES_PER_SECTOR   = ISO_SECTOR_SIZE

BYTES_PER_KBYTE    = 1024.0
KBYTES_PER_MBYTE   = 1024.0
MBYTES_PER_GBYTE   = 1024.0
BYTES_PER_MBYTE    = BYTES_PER_KBYTE * KBYTES_PER_MBYTE
BYTES_PER_GBYTE    = BYTES_PER_MBYTE * MBYTES_PER_GBYTE

SECONDS_PER_MINUTE = 60
MINUTES_PER_HOUR   = 60
HOURS_PER_DAY      = 24
SECONDS_PER_DAY    = SECONDS_PER_MINUTE * MINUTES_PER_HOUR * HOURS_PER_DAY

UNIT_BYTES         = 0
UNIT_KBYTES        = 1
UNIT_MBYTES        = 2
UNIT_GBYTES        = 4
UNIT_SECTORS       = 3

MTAB_FILE          = "/etc/mtab"

MOUNT_COMMAND      = [ "mount", ]
UMOUNT_COMMAND     = [ "umount", ]


########################################################################
# UnorderedList class definition
########################################################################

class UnorderedList(list):

   """
   Class representing an "unordered list".

   An "unordered list" is a list in which only the contents matter, not the
   order in which the contents appear in the list.  
   
   For instance, we might be keeping track of set of paths in a list, because
   it's convenient to have them in that form.  However, for comparison
   purposes, we would only care that the lists contain exactly the same
   contents, regardless of order.  

   I have come up with two reasonable ways of doing this, plus a couple more
   that would work but would be a pain to implement.  My first method is to
   copy and sort each list, comparing the sorted versions.  This will only work
   if two lists with exactly the same members are guaranteed to sort in exactly
   the same order.  The second way would be to create two Sets and then compare
   the sets.  However, this would lose information about any duplicates in
   either list.  I've decided to go with option #1 for now.  I'll modify this
   code if I run into problems in the future.

   We override the original C{__eq__}, C{__ne__}, C{__ge__}, C{__gt__},
   C{__le__} and C{__lt__} list methods to change the definition of the various
   comparison operators.  In all cases, the comparison is changed to return the
   result of the original operation I{but instead comparing sorted lists}.
   This is going to be quite a bit slower than a normal list, so you probably
   only want to use it on small lists.
   """

   def __eq__(self, other):
      """
      Definition of C{==} operator for this class.
      @param other: Other object to compare to.
      @return: True/false depending on whether C{self == other}.
      """
      if other is None:
         return False
      selfSorted = self[:]
      otherSorted = other[:]
      selfSorted.sort()
      otherSorted.sort()
      return selfSorted.__eq__(otherSorted)

   def __ne__(self, other):
      """
      Definition of C{!=} operator for this class.
      @param other: Other object to compare to.
      @return: True/false depending on whether C{self != other}.
      """
      if other is None:
         return True
      selfSorted = self[:]
      otherSorted = other[:]
      selfSorted.sort()
      otherSorted.sort()
      return selfSorted.__ne__(otherSorted)

   def __ge__(self, other):
      """
      Definition of S{>=} operator for this class.
      @param other: Other object to compare to.
      @return: True/false depending on whether C{self >= other}.
      """
      if other is None:
         return True
      selfSorted = self[:]
      otherSorted = other[:]
      selfSorted.sort()
      otherSorted.sort()
      return selfSorted.__ge__(otherSorted)

   def __gt__(self, other):
      """
      Definition of C{>} operator for this class.
      @param other: Other object to compare to.
      @return: True/false depending on whether C{self > other}.
      """
      if other is None:
         return True
      selfSorted = self[:]
      otherSorted = other[:]
      selfSorted.sort()
      otherSorted.sort()
      return selfSorted.__gt__(otherSorted)

   def __le__(self, other):
      """
      Definition of S{<=} operator for this class.
      @param other: Other object to compare to.
      @return: True/false depending on whether C{self <= other}.
      """
      if other is None:
         return False
      selfSorted = self[:]
      otherSorted = other[:]
      selfSorted.sort()
      otherSorted.sort()
      return selfSorted.__le__(otherSorted)

   def __lt__(self, other):
      """
      Definition of C{<} operator for this class.
      @param other: Other object to compare to.
      @return: True/false depending on whether C{self < other}.
      """
      if other is None:
         return False
      selfSorted = self[:]
      otherSorted = other[:]
      selfSorted.sort()
      otherSorted.sort()
      return selfSorted.__lt__(otherSorted)


########################################################################
# AbsolutePathList class definition
########################################################################

class AbsolutePathList(UnorderedList):

   """
   Class representing a list of absolute paths.

   This is an unordered list.

   We override the C{append}, C{insert} and C{extend} methods to ensure that
   any item added to the list is an absolute path.  

   Each item added to the list is encoded using L{encodePath}.  If we don't do
   this, we have problems trying certain operations between strings and unicode
   objects, particularly for "odd" filenames that can't be encoded in standard
   ASCII.
   """

   def append(self, item):
      """
      Overrides the standard C{append} method.
      @raise ValueError: If item is not an absolute path.
      """
      if not os.path.isabs(item):
         raise ValueError("Item must be an absolute path.")
      list.append(self, encodePath(item))

   def insert(self, index, item):
      """
      Overrides the standard C{insert} method.
      @raise ValueError: If item is not an absolute path.
      """
      if not os.path.isabs(item):
         raise ValueError("Item must be an absolute path.")
      list.insert(self, index, encodePath(item))

   def extend(self, seq):
      """
      Overrides the standard C{insert} method.
      @raise ValueError: If any item is not an absolute path.
      """
      for item in seq:
         if not os.path.isabs(item):
            raise ValueError("All items must be absolute paths.")
      for item in seq:
         list.append(self, encodePath(item))


########################################################################
# ObjectTypeList class definition
########################################################################

class ObjectTypeList(UnorderedList):

   """
   Class representing a list containing only objects with a certain type.

   This is an unordered list.

   We override the C{append}, C{insert} and C{extend} methods to ensure that
   any item added to the list matches the type that is requested.  The
   comparison uses the built-in C{isinstance}, which should allow subclasses of
   of the requested type to be added to the list as well.

   The C{objectName} value will be used in exceptions, i.e. C{"Item must be a
   CollectDir object."} if C{objectName} is C{"CollectDir"}.
   """
   
   def __init__(self, objectType, objectName):
      """
      Initializes a typed list for a particular type.
      @param objectType: Type that the list elements must match.
      @param objectName: Short string containing the "name" of the type.
      """
      self.objectType = objectType
      self.objectName = objectName

   def append(self, item):
      """
      Overrides the standard C{append} method.
      @raise ValueError: If item does not match requested type.
      """
      if not isinstance(item, self.objectType):
         raise ValueError("Item must be a %s object." % self.objectName)
      list.append(self, item)

   def insert(self, index, item):
      """
      Overrides the standard C{insert} method.
      @raise ValueError: If item does not match requested type.
      """
      if not isinstance(item, self.objectType):
         raise ValueError("Item must be a %s object." % self.objectName)
      list.insert(self, index, item)

   def extend(self, seq):
      """
      Overrides the standard C{insert} method.
      @raise ValueError: If item does not match requested type.
      """
      for item in seq:
         if not isinstance(item, self.objectType):
            raise ValueError("All items must be %s objects." % self.objectName)
      list.extend(self, seq)


########################################################################
# RestrictedContentList class definition
########################################################################

class RestrictedContentList(UnorderedList):

   """
   Class representing a list containing only object with certain values.

   This is an unordered list.

   We override the C{append}, C{insert} and C{extend} methods to ensure that
   any item added to the list is among the valid values.  We use a standard
   comparison, so pretty much anything can be in the list of valid values.

   The C{valuesDescr} value will be used in exceptions, i.e. C{"Item must be
   one of values in VALID_ACTIONS"} if C{valuesDescr} is C{"VALID_ACTIONS"}.

   @note:  This class doesn't make any attempt to trap for nonsensical
   arguments.  All of the values in the values list should be of the same type
   (i.e. strings).  Then, all list operations also need to be of that type
   (i.e. you should always insert or append just strings).  If you mix types --
   for instance lists and strings -- you will likely see AttributeError
   exceptions or other problems.
   """
   
   def __init__(self, valuesList, valuesDescr):
      """
      Initializes a list restricted to containing certain values.
      @param valuesList: List of valid values.
      @param valuesDescr: Short string describing list of values.
      """
      self.valuesList = valuesList
      self.valuesDescr = valuesDescr

   def append(self, item):
      """
      Overrides the standard C{append} method.
      @raise ValueError: If item is not in the values list.
      """
      if item not in self.valuesList:
         raise ValueError("Item must be one of values in %s." % self.valuesDescr)
      list.append(self, item)

   def insert(self, index, item):
      """
      Overrides the standard C{insert} method.
      @raise ValueError: If item is not in the values list.
      """
      if item not in self.valuesList:
         raise ValueError("Item must be one of values in %s." % self.valuesDescr)
      list.insert(self, index, item)

   def extend(self, seq):
      """
      Overrides the standard C{insert} method.
      @raise ValueError: If item is not in the values list.
      """
      for item in seq:
         if item not in self.valuesList:
            raise ValueError("Item must be one of values in %s." % self.valuesDescr)
      list.extend(self, seq)


########################################################################
# RegexMatchList class definition
########################################################################

class RegexMatchList(UnorderedList):

   """
   Class representing a list containing only strings that match a regular expression.

   If C{emptyAllowed} is passed in as C{False}, then empty strings are
   explicitly disallowed, even if they happen to match the regular expression.
   (C{None} values are always disallowed, since string operations are not
   permitted on C{None}.)

   This is an unordered list.

   We override the C{append}, C{insert} and C{extend} methods to ensure that
   any item added to the list matches the indicated regular expression.  

   @note: If you try to put values that are not strings into the list, you will
   likely get either TypeError or AttributeError exceptions as a result.
   """
   
   def __init__(self, valuesRegex, emptyAllowed=True):
      """
      Initializes a list restricted to containing certain values.
      @param valuesRegex: Regular expression that must be matched, as a string
      @param emptyAllowed: Indicates whether empty or None values are allowed.
      """
      self.valuesRegex = valuesRegex
      self.emptyAllowed = emptyAllowed
      self.pattern = re.compile(self.valuesRegex)

   def append(self, item):
      """
      Overrides the standard C{append} method.
      @raise ValueError: If item is None
      @raise ValueError: If item is empty and empty values are not allowed
      @raise ValueError: If item does not match the configured regular expression
      """
      if item is None or (not self.emptyAllowed and item == ""):
         raise ValueError("Item must be non-empty.")
      if not self.pattern.search(item):
         raise ValueError("Item must match regular expression [%s]." % self.valuesRegex)
      list.append(self, item)

   def insert(self, index, item):
      """
      Overrides the standard C{insert} method.
      @raise ValueError: If item is None
      @raise ValueError: If item is empty and empty values are not allowed
      @raise ValueError: If item does not match the configured regular expression
      """
      if item is None or (not self.emptyAllowed and item == ""):
         raise ValueError("Item must be non-empty.")
      if not self.pattern.search(item):
         raise ValueError("Item must match regular expression [%s]." % self.valuesRegex)
      list.insert(self, index, item)

   def extend(self, seq):
      """
      Overrides the standard C{insert} method.
      @raise ValueError: If any item is None
      @raise ValueError: If any item is empty and empty values are not allowed
      @raise ValueError: If any item does not match the configured regular expression
      """
      for item in seq:
         if item is None or (not self.emptyAllowed and item == ""):
            raise ValueError("Item must be non-empty.")
         if not self.pattern.search(item):
            raise ValueError("Item must match regular expression [%s]." % self.valuesRegex)
      list.extend(self, seq)


########################################################################
# PathResolverSingleton class definition
########################################################################

class PathResolverSingleton:

   """
   Singleton used for resolving executable paths.

   Various functions throughout Cedar Backup (including extensions) need a way
   to resolve the path of executables that they use.  For instance, the image
   functionality needs to find the C{mkisofs} executable, and the Subversion
   extension needs to find the C{svnlook} executable.  Cedar Backup's original
   behavior was to assume that the simple name (C{"svnlook"} or whatever) was
   available on the caller's C{$PATH}, and to fail otherwise.   However, this
   turns out to be less than ideal, since for instance the root user might not
   always have executables like C{svnlook} in its path.

   One solution is to specify a path (either via an absolute path or some sort
   of path insertion or path appending mechanism) that would apply to the
   C{executeCommand()} function.  This is not difficult to implement, but it
   seem like kind of a "big hammer" solution.  Besides that, it might also
   represent a security flaw (for instance, I prefer not to mess with root's
   C{$PATH} on the application level if I don't have to).
   
   The alternative is to set up some sort of configuration for the path to
   certain executables, i.e. "find C{svnlook} in C{/usr/local/bin/svnlook}" or
   whatever.  This PathResolverSingleton aims to provide a good solution to the
   mapping problem.  Callers of all sorts (extensions or not) can get an
   instance of the singleton.  Then, they call the C{lookup} method to try and
   resolve the executable they are looking for.  Through the C{lookup} method,
   the caller can also specify a default to use if a mapping is not found.
   This way, with no real effort on the part of the caller, behavior can neatly
   degrade to something equivalent to the current behavior if there is no
   special mapping or if the singleton was never initialized in the first
   place.  

   Even better, extensions automagically get access to the same resolver
   functionality, and they don't even need to understand how the mapping
   happens.  All extension authors need to do is document what executables
   their code requires, and the standard resolver configuration section will
   meet their needs.

   The class should be initialized once through the constructor somewhere in
   the main routine.  Then, the main routine should call the L{fill} method to
   fill in the resolver's internal structures.  Everyone else who needs to
   resolve a path will get an instance of the class using L{getInstance} and
   will then just call the L{lookup} method.

   @cvar _instance: Holds a reference to the singleton
   @ivar _mapping: Internal mapping from resource name to path.
   """

   _instance = None     # Holds a reference to singleton instance

   class _Helper:
      """Helper class to provide a singleton factory method."""
      def __call__(self, *args, **kw):
         if PathResolverSingleton._instance is None:
            object = PathResolverSingleton()
            PathResolverSingleton._instance = object
         return PathResolverSingleton._instance
    
   getInstance = _Helper()    # Method that callers will use to get an instance

   def __init__(self):
      """Singleton constructor, which just creates the singleton instance."""
      if PathResolverSingleton._instance is not None:
         raise RuntimeError("Only one instance of PathResolverSingleton is allowed!")
      PathResolverSingleton._instance = self
      self._mapping = { }

   def lookup(self, name, default=None):
      """
      Looks up name and returns the resolved path associated with the name.
      @param name: Name of the path resource to resolve.
      @param default: Default to return if resource cannot be resolved.
      @return: Resolved path associated with name, or default if name can't be resolved.
      """
      value = default
      if name in self._mapping.keys():
         value = self._mapping[name]
      logger.debug("Resolved command [%s] to [%s]." % (name, value))
      return value

   def fill(self, mapping):
      """
      Fills in the singleton's internal mapping from name to resource.
      @param mapping: Mapping from resource name to path.
      @type mapping: Dictionary mapping name to path, both as strings.
      """
      self._mapping = { }
      for key in mapping.keys():
         self._mapping[key] = mapping[key]
      

########################################################################
# Pipe class definition
########################################################################

if _PIPE_IMPLEMENTATION == "subprocess.Popen":

   from subprocess import STDOUT, PIPE

   class Pipe(Popen):
      """
      Specialized pipe class for use by C{executeCommand}.

      The L{executeCommand} function needs a specialized way of interacting
      with a pipe.  First, C{executeCommand} only reads from the pipe, and
      never writes to it.  Second, C{executeCommand} needs a way to discard all
      output written to C{stderr}, as a means of simulating the shell
      C{2>/dev/null} construct.  

      All of this functionality is provided (in Python 2.4 or later) by the
      C{subprocess.Popen} class, so when that class is available, we'll use it.
      Otherwise, there's another implementation based on L{popen2.Popen4},
      which unfortunately only works on UNIX platforms.
      """
      def __init__(self, cmd, bufsize=-1, ignoreStderr=False):
         stderr = STDOUT
         if ignoreStderr:
            devnull = nullDevice()
            stderr = os.open(devnull, os.O_RDWR) 
         Popen.__init__(self, shell=False, args=cmd, bufsize=bufsize, stdin=None, stdout=PIPE, stderr=stderr)
         self.fromchild = self.stdout  # for compatibility with original interface based on popen2.Popen4

else: # _PIPE_IMPLEMENTATION == "popen2.Popen4" 

   from popen2 import _cleanup, _active

   class Pipe(Popen4):
      """
      Specialized pipe class for use by C{executeCommand}.

      The L{executeCommand} function needs a specialized way of interacting with a
      pipe that isn't satisfied by the standard C{Popen3} and C{Popen4} classes in
      C{popen2}.  First, C{executeCommand} only reads from the pipe, and never
      writes to it.  Second, C{executeCommand} needs a way to discard all output
      written to C{stderr}, as a means of simulating the shell C{2>/dev/null}
      construct.  

      This class inherits from C{Popen4}.  If the C{ignoreStderr} flag is passed in
      as C{False}, then the standard C{Popen4} constructor will be called and
      C{stdout} and C{stderr} will be intermingled in the output.  

      Otherwise, we'll call a custom version of the constructor which was
      basically stolen from the real constructor in C{python2.3/Lib/popen2.py}.
      This custom constructor will redirect the C{stderr} file descriptor to
      C{/dev/null}.  I've done this based on a suggestion from Donn Cave on
      comp.lang.python.

      In either case, the C{tochild} file object is always closed before returning
      from the constructor, since it is never needed by C{executeCommand}.

      I really wish there were a prettier way to do this.  Unfortunately, I
      need access to the guts of the constructor implementation because of the
      way the pipe process is forked, etc.  It doesn't work to just call the
      superclass constructor and then modify a few things afterwards.  Even
      worse, I have to access private C{popen2} module members C{_cleanup} and
      C{_active} in order to duplicate the implementation.  

      Hopefully this whole thing will continue to work properly.  At least we
      can use the other L{subprocess.Popen}-based implementation when that
      class is available.
      
      @copyright: Some of this code, prior to customization, was originally part
      of the Python 2.3 codebase.  Python code is copyright (c) 2001, 2002 Python
      Software Foundation; All Rights Reserved.
      """
      
      def __init__(self, cmd, bufsize=-1, ignoreStderr=False):
         if not ignoreStderr:
            Popen4.__init__(self, cmd, bufsize)
         else:
            _cleanup()
            p2cread, p2cwrite = os.pipe()
            c2pread, c2pwrite = os.pipe()
            self.pid = os.fork()
            if self.pid == 0: # Child
               os.dup2(p2cread, 0)
               os.dup2(c2pwrite, 1)
               devnull = nullDevice()
               null = os.open(devnull, os.O_RDWR)
               os.dup2(null, 2)
               os.close(null)
               self._run_child(cmd)
            os.close(p2cread)
            self.tochild = os.fdopen(p2cwrite, 'w', bufsize)
            os.close(c2pwrite)
            self.fromchild = os.fdopen(c2pread, 'r', bufsize)
            _active.append(self)
         self.tochild.close()       # we'll never write to it, and this way we don't confuse anything.


########################################################################
# General utility functions
########################################################################

#########################
# convertSize() function
#########################

def convertSize(size, fromUnit, toUnit):
   """
   Converts a size in one unit to a size in another unit.

   This is just a convenience function so that the functionality can be
   implemented in just one place.  Internally, we convert values to bytes and
   then to the final unit.

   The available units are:

      - C{UNIT_BYTES} - Bytes
      - C{UNIT_KBYTES} - Kilobytes, where 1 kB = 1024 B
      - C{UNIT_MBYTES} - Megabytes, where 1 MB = 1024 kB
      - C{UNIT_GBYTES} - Gigabytes, where 1 GB = 1024 MB
      - C{UNIT_SECTORS} - Sectors, where 1 sector = 2048 B

   @param size: Size to convert
   @type size: Integer or float value in units of C{fromUnit} 

   @param fromUnit: Unit to convert from
   @type fromUnit: One of the units listed above

   @param toUnit: Unit to convert to
   @type toUnit: One of the units listed above

   @return: Number converted to new unit, as a float.
   @raise ValueError: If one of the units is invalid.
   """
   if fromUnit == UNIT_BYTES:
      byteSize = float(size)
   elif fromUnit == UNIT_KBYTES:
      byteSize = float(size) * BYTES_PER_KBYTE
   elif fromUnit == UNIT_MBYTES:
      byteSize = float(size) * BYTES_PER_MBYTE
   elif fromUnit == UNIT_GBYTES:
      byteSize = float(size) * BYTES_PER_GBYTE
   elif fromUnit == UNIT_SECTORS:
      byteSize = float(size) * BYTES_PER_SECTOR
   else:
      raise ValueError("Unknown 'from' unit %d." % fromUnit)
   if toUnit == UNIT_BYTES:
      return byteSize
   elif toUnit == UNIT_KBYTES:
      return byteSize / BYTES_PER_KBYTE
   elif toUnit == UNIT_MBYTES:
      return byteSize / BYTES_PER_MBYTE
   elif toUnit == UNIT_GBYTES:
      return byteSize / BYTES_PER_GBYTE
   elif toUnit == UNIT_SECTORS:
      return byteSize / BYTES_PER_SECTOR
   else:
      raise ValueError("Unknown 'to' unit %d." % toUnit)


##########################
# displayBytes() function
##########################

def displayBytes(bytes, digits=2):
   """
   Format a byte quantity so it can be sensibly displayed.

   It's rather difficult to look at a number like "72372224 bytes" and get any
   meaningful information out of it.  It would be more useful to see something
   like "72.37 MB".  That's what this function does.  Any time you want to display
   a byte value, i.e.::

      print "Size: %s bytes" % bytes

   Call this function instead::

      print "Size: %s" % displayBytes(bytes)

   What comes out will be sensibly formatted.  The indicated number of digits
   will be listed after the decimal point, rounded based on whatever rules are
   used by Python's standard C{%f} string format specifier.

   @param bytes: Byte quantity.
   @type bytes: Integer number of bytes.

   @param digits: Number of digits to display after the decimal point.
   @type digits: Integer value, typically 2-5.

   @return: String, formatted for sensible display.
   """
   bytes = float(bytes)
   if math.fabs(bytes) < BYTES_PER_KBYTE:
      format = "%.0f bytes"
      value = bytes
   elif math.fabs(bytes) < BYTES_PER_MBYTE:
      format = "%." + "%d" % digits + "f kB"
      value = bytes / BYTES_PER_KBYTE
   elif math.fabs(bytes) < BYTES_PER_GBYTE:
      format = "%." + "%d" % digits + "f MB"
      value = bytes / BYTES_PER_MBYTE
   else:
      format = "%." + "%d" % digits + "f GB"
      value = bytes / BYTES_PER_GBYTE
   return format % value


##################################
# getFunctionReference() function
##################################

def getFunctionReference(module, function):
   """
   Gets a reference to a named function.

   This does some hokey-pokey to get back a reference to a dynamically named
   function.  For instance, say you wanted to get a reference to the
   C{os.path.isdir} function.  You could use::
   
      myfunc = getFunctionReference("os.path", "isdir")

   Although we won't bomb out directly, behavior is pretty much undefined if
   you pass in C{None} or C{""} for either C{module} or C{function}.

   The only validation we enforce is that whatever we get back must be
   callable.  

   I derived this code based on the internals of the Python unittest
   implementation.  I don't claim to completely understand how it works.

   @param module: Name of module associated with function.
   @type module: Something like "os.path" or "CedarBackup2.util"

   @param function: Name of function
   @type function: Something like "isdir" or "getUidGid"

   @return: Reference to function associated with name.

   @raise ImportError: If the function cannot be found. 
   @raise ValueError: If the resulting reference is not callable.

   @copyright: Some of this code, prior to customization, was originally part
   of the Python 2.3 codebase.  Python code is copyright (c) 2001, 2002 Python
   Software Foundation; All Rights Reserved.
   """
   parts = []
   if module is not None and module != "":
      parts = module.split(".")
   if function is not None and function != "":
      parts.append(function);
   copy = parts[:]
   while copy:
      try:
         module = __import__(string.join(copy, "."))
         break
      except ImportError:
         del copy[-1]
         if not copy: raise
      parts = parts[1:]
   obj = module
   for part in parts:
      obj = getattr(obj, part) 
   if not callable(obj):
      raise ValueError("Reference to %s.%s is not callable." % (module, function))
   return obj


#######################
# getUidGid() function
#######################

def getUidGid(user, group):
   """
   Get the uid/gid associated with a user/group pair

   This is a no-op if user/group functionality is not available on the platform.

   @param user: User name
   @type user: User name as a string

   @param group: Group name
   @type group: Group name as a string

   @return: Tuple C{(uid, gid)} matching passed-in user and group.
   @raise ValueError: If the ownership user/group values are invalid
   """
   if _UID_GID_AVAILABLE:
      try:
         uid = pwd.getpwnam(user)[2]
         gid = grp.getgrnam(group)[2]
         logger.debug("Translated [%s:%s] into [%d:%d]." % (user, group, uid, gid))
         return (uid, gid)
      except Exception, e:
         logger.debug("Error looking up uid and gid for [%s:%s]: %s" % (user, group, e))
         raise ValueError("Unable to lookup up uid and gid for passed in user/group.")
   else:
      return (0,0)


#############################
# changeOwnership() function
#############################

def changeOwnership(path, user, group):
   """
   Changes ownership of path to match the user and group.
   This is a no-op if user/group functionality is not available on the platform.
   @param path: Path whose ownership to change.
   @param user: User which owns file.
   @param group: Group which owns file.
   """
   if _UID_GID_AVAILABLE:
      if os.getuid() != 0:
         logger.debug("Not root, so not attempting to change owner on [%s]." % path)
      else:
         try:
            (uid, gid) = getUidGid(user, group)
            os.chown(path, uid, gid)
         except Exception, e:
            logger.error("Error changing ownership of [%s]: %s" % (path, e))


##############################
# splitCommandLine() function
##############################

def splitCommandLine(commandLine):
   """
   Splits a command line string into a list of arguments.

   Unfortunately, there is no "standard" way to parse a command line string,
   and it's actually not an easy problem to solve portably (essentially, we
   have to emulate the shell argument-processing logic).  This code only
   respects double quotes (C{"}) for grouping arguments, not single quotes
   (C{'}).  Make sure you take this into account when building your command
   line.

   Incidentally, I found this particular parsing method while digging around in
   Google Groups, and I tweaked it for my own use.

   @param commandLine: Command line string
   @type commandLine: String, i.e. "cback --verbose stage store"

   @return: List of arguments, suitable for passing to L{popen2}.
   """
   fields = re.findall('[^ "]+|"[^"]+"', commandLine)
   fields = map(lambda field: field.replace('"', ''), fields)
   return fields


############################
# resolveCommand() function
############################

def resolveCommand(command):
   """
   Resolves the real path to a command through the path resolver mechanism.

   Both extensions and standard Cedar Backup functionality need a way to
   resolve the "real" location of various executables.  Normally, they assume
   that these executables are on the system path, but some callers need to
   specify an alternate location.  

   Ideally, we want to handle this configuration in a central location.  The
   Cedar Backup path resolver mechanism (a singleton called
   L{PathResolverSingleton}) provides the central location to store the
   mappings.  This function wraps access to the singleton, and is what all
   functions (extensions or standard functionality) should call if they need to
   find a command.
   
   The passed-in command must actually be a list, in the standard form used by
   all existing Cedar Backup code (something like C{["svnlook", ]}).  The
   lookup will actually be done on the first element in the list, and the
   returned command will always be in list form as well.

   If the passed-in command can't be resolved or no mapping exists, then the
   command itself will be returned unchanged.  This way, we neatly fall back on
   default behavior if we have no sensible alternative.

   @param command: Command to resolve.
   @type command: List form of command, i.e. C{["svnlook", ]}.

   @return: Path to command or just command itself if no mapping exists.
   """
   singleton = PathResolverSingleton.getInstance()
   name = command[0]
   result = command[:]
   result[0] = singleton.lookup(name, name)
   return result


############################
# executeCommand() function
############################

def executeCommand(command, args, returnOutput=False, ignoreStderr=False, doNotLog=False, outputFile=None):
   """
   Executes a shell command, hopefully in a safe way.

   This function exists to replace direct calls to L{os.popen()} in the Cedar
   Backup code.  It's not safe to call a function such as L{os.popen()} with
   untrusted arguments, since that can cause problems if the string contains
   non-safe variables or other constructs (imagine that the argument is
   C{$WHATEVER}, but C{$WHATEVER} contains something like C{"; rm -fR ~/;
   echo"} in the current environment).

   Instead, it's safer to pass a list of arguments in the style supported bt
   C{popen2} or C{popen4}.  This function actually uses a specialized C{Pipe}
   class implemented using either C{subprocess.Popen} or C{popen2.Popen4}.

   Under the normal case, this function will return a tuple of C{(status,
   None)} where the status is the wait-encoded return status of the call per
   the L{popen2.Popen4} documentation.  If C{returnOutput} is passed in as
   C{True}, the function will return a tuple of C{(status, output)} where
   C{output} is a list of strings, one entry per line in the output from the
   command.  Output is always logged to the C{outputLogger.info()} target,
   regardless of whether it's returned.

   By default, C{stdout} and C{stderr} will be intermingled in the output.
   However, if you pass in C{ignoreStderr=True}, then only C{stdout} will be
   included in the output.  

   The C{doNotLog} parameter exists so that callers can force the function to
   not log command output to the debug log.  Normally, you would want to log.
   However, if you're using this function to write huge output files (i.e.
   database backups written to C{stdout}) then you might want to avoid putting
   all that information into the debug log.

   The C{outputFile} parameter exists to make it easier for a caller to push
   output into a file, i.e. as a substitute for redirection to a file.  If this
   value is passed in, each time a line of output is generated, it will be
   written to the file using C{outputFile.write()}.  At the end, the file
   descriptor will be flushed using C{outputFile.flush()}.  The caller
   maintains responsibility for closing the file object appropriately.

   @note: I know that it's a bit confusing that the command and the arguments
   are both lists.  I could have just required the caller to pass in one big
   list.  However, I think it makes some sense to keep the command (the
   constant part of what we're executing, i.e. C{"scp -B"}) separate from its
   arguments, even if they both end up looking kind of similar.

   @note: You cannot redirect output via shell constructs (i.e. C{>file},
   C{2>/dev/null}, etc.) using this function.  The redirection string would be
   passed to the command just like any other argument.  However, you can
   implement the equivalent to redirection using C{ignoreStderr} and
   C{outputFile}, as discussed above.

   @param command: Shell command to execute
   @type command: List of individual arguments that make up the command

   @param args: List of arguments to the command
   @type args: List of additional arguments to the command

   @param returnOutput: Indicates whether to return the output of the command
   @type returnOutput: Boolean C{True} or C{False}

   @param doNotLog: Indicates that output should not be logged.
   @type doNotLog: Boolean C{True} or C{False}

   @param outputFile: File object that all output should be written to.
   @type outputFile: File object as returned from C{open()} or C{file()}.

   @return: Tuple of C{(result, output)} as described above.
   """
   logger.debug("Executing command %s with args %s." % (command, args))
   outputLogger.info("Executing command %s with args %s." % (command, args))
   if doNotLog:
      logger.debug("Note: output will not be logged, per the doNotLog flag.")
      outputLogger.info("Note: output will not be logged, per the doNotLog flag.")
   output = []
   fields = command[:]        # make sure to copy it so we don't destroy it
   fields.extend(args)
   try:
      pipe = Pipe(fields, ignoreStderr=ignoreStderr)
      while True:
         line = pipe.fromchild.readline()
         if not line: break
         if returnOutput: output.append(line)
         if outputFile is not None: outputFile.write(line)
         if not doNotLog: outputLogger.info(line[:-1])  # this way the log will (hopefully) get updated in realtime
      if outputFile is not None: 
         try: # note, not every file-like object can be flushed
            outputFile.flush()
         except: pass
      if returnOutput:
         return (pipe.wait(), output)
      else:
         return (pipe.wait(), None)
   except OSError, e:
      try:
         if returnOutput:
            if output != []:
               return (pipe.wait(), output)
            else:
               return (pipe.wait(), [ e, ])
         else:
            return (pipe.wait(), None)
      except UnboundLocalError:  # pipe not set
         if returnOutput:
            return (256, [])
         else:
            return (256, None)


##############################
# calculateFileAge() function
##############################

def calculateFileAge(file):
   """
   Calculates the age (in days) of a file.

   The "age" of a file is the amount of time since the file was last used, per
   the most recent of the file's C{st_atime} and C{st_mtime} values.

   Technically, we only intend this function to work with files, but it will
   probably work with anything on the filesystem.

   @param file: Path to a file on disk.

   @return: Age of the file in days.
   @raise OSError: If the file doesn't exist.
   """
   currentTime = int(time.time())
   fileStats = os.stat(file)
   lastUse = max(fileStats.st_atime, fileStats.st_mtime)  # "most recent" is "largest" 
   ageInDays = (currentTime - lastUse) / SECONDS_PER_DAY
   return ageInDays


###################
# mount() function
###################

def mount(devicePath, mountPoint, fsType):
   """
   Mounts the indicated device at the indicated mount point.

   For instance, to mount a CD, you might use device path C{/dev/cdrw}, mount
   point C{/media/cdrw} and filesystem type C{iso9660}.  You can safely use any
   filesystem type that is supported by C{mount} on your platform.  If the type
   is C{None}, we'll attempt to let C{mount} auto-detect it.  This may or may
   not work on all systems.

   @note: This only works on platforms that have a concept of "mounting" a
   filesystem through a command-line C{"mount"} command, like UNIXes.  It
   won't work on Windows.

   @param devicePath: Path of device to be mounted.
   @param mountPoint: Path that device should be mounted at.
   @param fsType: Type of the filesystem assumed to be available via the device.

   @raise IOError: If the device cannot be mounted.
   """
   if fsType is None:
      args = [ devicePath, mountPoint ]
   else:
      args = [ "-t", fsType, devicePath, mountPoint ]
   command = resolveCommand(MOUNT_COMMAND)
   result = executeCommand(command, args, returnOutput=False, ignoreStderr=True)[0]
   if result != 0:
      raise IOError("Error [%d] mounting [%s] at [%s] as [%s]." % (result, devicePath, mountPoint, fsType))


#####################
# unmount() function
#####################

def unmount(mountPoint, removeAfter=False, attempts=1, waitSeconds=0):
   """
   Unmounts whatever device is mounted at the indicated mount point.

   Sometimes, it might not be possible to unmount the mount point immediately,
   if there are still files open there.  Use the C{attempts} and C{waitSeconds}
   arguments to indicate how many unmount attempts to make and how many seconds
   to wait between attempts.  If you pass in zero attempts, no attempts will be
   made (duh).

   If the indicated mount point is not really a mount point per
   C{os.path.ismount()}, then it will be ignored.  This seems to be a safer
   check then looking through C{/etc/mtab}, since C{ismount()} is already in
   the Python standard library and is documented as working on all POSIX
   systems.

   If C{removeAfter} is C{True}, then the mount point will be removed using
   C{os.rmdir()} after the unmount action succeeds.  If for some reason the
   mount point is not a directory, then it will not be removed.

   @note: This only works on platforms that have a concept of "mounting" a
   filesystem through a command-line C{"mount"} command, like UNIXes.  It
   won't work on Windows.

   @param mountPoint: Mount point to be unmounted.
   @param removeAfter: Remove the mount point after unmounting it.
   @param attempts: Number of times to attempt the unmount.
   @param waitSeconds: Number of seconds to wait between repeated attempts.

   @raise IOError: If the mount point is still mounted after attempts are exhausted.
   """
   if os.path.ismount(mountPoint):
      for attempt in range(0, attempts):
         logger.debug("Making attempt %d to unmount [%s]." % (attempt, mountPoint))
         command = resolveCommand(UMOUNT_COMMAND)
         result = executeCommand(command, [ mountPoint, ], returnOutput=False, ignoreStderr=True)[0]
         if result != 0:
            logger.error("Error [%d] unmounting [%s] on attempt %d." % (result, mountPoint, attempt))
         elif os.path.ismount(mountPoint):
            logger.error("After attempt %d, [%s] is still mounted." % (attempt, mountPoint))
         else:
            logger.debug("Successfully unmounted [%s] on attempt %d." % (mountPoint, attempt))
            break  # this will cause us to skip the loop else: clause
         if attempt+1 < attempts:  # i.e. this isn't the last attempt
            if waitSeconds > 0:
               logger.info("Sleeping %d second(s) before next unmount attempt." % waitSeconds)
               time.sleep(waitSeconds)
      else:
         if os.path.ismount(mountPoint):
            raise IOError("Unable to unmount [%s] after %d attempts." % (mountPoint, attempts))
         logger.info("Mount point [%s] seems to have finally gone away." % mountPoint)
      if os.path.isdir(mountPoint) and removeAfter:
         logger.debug("Removing mount point [%s]." % mountPoint)
         os.rmdir(mountPoint)


###########################
# deviceMounted() function
###########################

def deviceMounted(devicePath):
   """
   Indicates whether a specific filesystem device is currently mounted.

   We determine whether the device is mounted by looking through the system's
   C{mtab} file.  This file shows every currently-mounted filesystem, ordered
   by device.  We only do the check if the C{mtab} file exists and is readable.
   Otherwise, we assume that the device is not mounted.

   @note: This only works on platforms that have a concept of an mtab file
   to show mounted volumes, like UNIXes.  It won't work on Windows.

   @param devicePath: Path of device to be checked

   @return: True if device is mounted, false otherwise.
   """
   if os.path.exists(MTAB_FILE) and os.access(MTAB_FILE, os.R_OK):
      realPath = os.path.realpath(devicePath)
      lines = open(MTAB_FILE).readlines()
      for line in lines:
         (mountDevice, mountPoint, remainder) = line.split(None, 2)
         if mountDevice in [ devicePath, realPath, ]:
            logger.debug("Device [%s] is mounted at [%s]." % (devicePath, mountPoint))
            return True
   return False


########################
# encodePath() function
########################

def encodePath(path):

   """
   Safely encodes a filesystem path.

   Many Python filesystem functions, such as C{os.listdir}, behave differently
   if they are passed unicode arguments versus simple string arguments.  For
   instance, C{os.listdir} generally returns unicode path names if it is passed
   a unicode argument, and string pathnames if it is passed a string argument.

   However, this behavior often isn't as consistent as we might like.  As an example,
   C{os.listdir} "gives up" if it finds a filename that it can't properly encode
   given the current locale settings.  This means that the returned list is
   a mixed set of unicode and simple string paths.  This has consequences later,
   because other filesystem functions like C{os.path.join} will blow up if they
   are given one string path and one unicode path.

   On comp.lang.python, Martin v. Löwis explained the C{os.listdir} behavior
   like this::

      The operating system (POSIX) does not have the inherent notion that file
      names are character strings. Instead, in POSIX, file names are primarily
      byte strings. There are some bytes which are interpreted as characters
      (e.g. '\x2e', which is '.', or '\x2f', which is '/'), but apart from
      that, most OS layers think these are just bytes.

      Now, most *people* think that file names are character strings.  To
      interpret a file name as a character string, you need to know what the
      encoding is to interpret the file names (which are byte strings) as
      character strings.

      There is, unfortunately, no operating system API to carry the notion of a
      file system encoding. By convention, the locale settings should be used
      to establish this encoding, in particular the LC_CTYPE facet of the
      locale. This is defined in the environment variables LC_CTYPE, LC_ALL,
      and LANG (searched in this order).

      If LANG is not set, the "C" locale is assumed, which uses ASCII as its
      file system encoding. In this locale, '\xe2\x99\xaa\xe2\x99\xac' is not a
      valid file name (at least it cannot be interpreted as characters, and
      hence not be converted to Unicode).

      Now, your Python script has requested that all file names *should* be
      returned as character (ie. Unicode) strings, but Python cannot comply,
      since there is no way to find out what this byte string means, in terms
      of characters.

      So we have three options:

      1. Skip this string, only return the ones that can be converted to Unicode. 
         Give the user the impression the file does not exist.
      2. Return the string as a byte string
      3. Refuse to listdir altogether, raising an exception (i.e. return nothing)

      Python has chosen alternative 2, allowing the application to implement 1
      or 3 on top of that if it wants to (or come up with other strategies,
      such as user feedback).

   As a solution, he suggests that rather than passing unicode paths into the
   filesystem functions, that I should sensibly encode the path first.  That is
   what this function accomplishes.  Any function which takes a filesystem path
   as an argument should encode it first, before using it for any other purpose.

   I confess I still don't completely understand how this works.  On a system
   with filesystem encoding "ISO-8859-1", a path C{u"\xe2\x99\xaa\xe2\x99\xac"}
   is converted into the string C{"\xe2\x99\xaa\xe2\x99\xac"}.  However, on a
   system with a "utf-8" encoding, the result is a completely different string:
   C{"\xc3\xa2\xc2\x99\xc2\xaa\xc3\xa2\xc2\x99\xc2\xac"}.  A quick test where I
   write to the first filename and open the second proves that the two strings
   represent the same file on disk, which is all I really care about.

   @note: As a special case, if C{path} is C{None}, then this function will
   return C{None}.

   @note: To provide several examples of encoding values, my Debian sarge box
   with an ext3 filesystem has Python filesystem encoding C{ISO-8859-1}.  User
   Anarcat's Debian box with a xfs filesystem has filesystem encoding
   C{ANSI_X3.4-1968}.  Both my iBook G4 running Mac OS X 10.4 and user Dag
   Rende's SuSE 9.3 box both have filesystem encoding C{UTF-8}.

   @note: Just because a filesystem has C{UTF-8} encoding doesn't mean that it
   will be able to handle all extended-character filenames.  For instance,
   certain extended-character (but not UTF-8) filenames -- like the ones in the
   regression test tar file C{test/data/tree13.tar.gz} -- are not valid under
   Mac OS X, and it's not even possible to extract them from the tarfile on
   that platform.

   @param path: Path to encode

   @return: Path, as a string, encoded appropriately
   @raise ValueError: If the path cannot be encoded properly.
   """
   if path is None:
      return path
   try:
      if isinstance(path, unicode):
         encoding = sys.getfilesystemencoding() or sys.getdefaultencoding()
         path = path.encode(encoding)
      return path
   except UnicodeError:
      raise ValueError("Path could not be safely encoded as %s." % encoding)


########################
# nullDevice() function
########################

def nullDevice():
   """
   Attempts to portably return the null device on this system.

   The null device is something like C{/dev/null} on a UNIX system.  The name
   varies on other platforms.

   In Python 2.4 and better, we can use C{os.devnull}.  Since we want to be
   portable to python 2.3, getting the value in earlier versions of Python
   takes some screwing around.  Basically, this function will only work on
   either UNIX-like systems (the default) or Windows.
   """
   try:
      return os.devnull
   except AttributeError: 
      import platform
      if platform.platform().startswith("Windows"):
         return "NUL"
      else:
         return "/dev/null"


##############################
# deriveDayOfWeek() function
##############################

def deriveDayOfWeek(dayName):
   """
   Converts English day name to numeric day of week as from C{time.localtime}.

   For instance, the day C{monday} would be converted to the number C{0}.

   @param dayName: Day of week to convert
   @type dayName: string, i.e. C{"monday"}, C{"tuesday"}, etc.

   @returns: Integer, where Monday is 0 and Sunday is 6; or -1 if no conversion is possible.
   """
   if dayName.lower() == "monday":
      return 0
   elif dayName.lower() == "tuesday":
      return 1
   elif dayName.lower() == "wednesday":
      return 2
   elif dayName.lower() == "thursday":
      return 3
   elif dayName.lower() == "friday":
      return 4
   elif dayName.lower() == "saturday":
      return 5
   elif dayName.lower() == "sunday":
      return 6
   else:
      return -1  # What else can we do??  Thrown an exception, I guess.


###########################
# isStartOfWeek() function
###########################

def isStartOfWeek(startingDay):
   """
   Indicates whether "today" is the backup starting day per configuration.

   If the current day's English name matches the indicated starting day, then
   today is a starting day.

   @param startingDay: Configured starting day.
   @type startingDay: string, i.e. C{"monday"}, C{"tuesday"}, etc.

   @return: Boolean indicating whether today is the starting day.
   """
   value = time.localtime().tm_wday == deriveDayOfWeek(startingDay)
   if value:
      logger.debug("Today is the start of the week.")
   else:
      logger.debug("Today is NOT the start of the week.")
   return value


#################################
# buildNormalizedPath() function
#################################

def buildNormalizedPath(absPath):
   """
   Returns a "normalized" path based on an absolute path.

   A "normalized" path has its leading C{'/'} or C{'.'} characters removed, and
   then converts all remaining whitespace and C{'/'} characters to the C{'_'}
   character.   As a special case, the absolute path C{/} will be normalized to
   just C{'-'}.

   @param absPath: Absolute path

   @return: Normalized path.
   """
   if absPath == os.sep:
      return "-"
   else:
      normalized = absPath
      normalized = re.sub("^\.", "", normalized)
      normalized = re.sub("^\/", "", normalized)
      normalized = re.sub("\/", "-", normalized)
      normalized = re.sub("\s", "_", normalized)
      return normalized
   

########################################################################
# Functions used to portably validate certain kinds of values
########################################################################

############################
# validateDevice() function
############################

def validateDevice(device, unittest=False):
   """
   Validates a configured device.
   The device must be an absolute path, must exist, and must be writable.
   The unittest flag turns off validation of the device on disk.
   @param device: Filesystem device path.
   @param unittest: Indicates whether we're unit testing.
   @return: Device as a string, for instance C{"/dev/cdrw"}
   @raise ValueError: If the device value is invalid.
   @raise ValueError: If some path cannot be encoded properly.
   """
   if device is None:
      raise ValueError("Device must be filled in.")
   device = encodePath(device)
   if not os.path.isabs(device):
      raise ValueError("Backup device must be an absolute path.")
   if not unittest and not os.path.exists(device):
      raise ValueError("Backup device must exist on disk.")
   if not unittest and not os.access(device, os.W_OK):
      raise ValueError("Backup device is not writable by the current user.")
   return device


############################
# validateScsiId() function
############################

def validateScsiId(scsiId):
   """
   Validates a SCSI id string.
   SCSI id must be a string in the form C{[<method>:]scsibus,target,lun}.
   For Mac OS X (Darwin), we also accept the form C{IO.*Services[/N]}.
   @note: For consistency, if C{None} is passed in, C{None} will be returned.
   @param scsiId: SCSI id for the device.
   @return: SCSI id as a string, for instance C{"ATA:1,0,0"}
   @raise ValueError: If the SCSI id string is invalid.
   """
   if scsiId is not None:
      pattern = re.compile(r"^\s*(.*:)?\s*[0-9][0-9]*\s*,\s*[0-9][0-9]*\s*,\s*[0-9][0-9]*\s*$")
      if not pattern.search(scsiId):
         pattern = re.compile(r"^\s*IO.*Services(\/[0-9][0-9]*)?\s*$")
         if not pattern.search(scsiId):
            raise ValueError("SCSI id is not in a valid form.")
   return scsiId


################################
# validateDriveSpeed() function
################################

def validateDriveSpeed(driveSpeed):
   """
   Validates a drive speed value.
   Drive speed must be an integer which is >= 1.
   @note: For consistency, if C{None} is passed in, C{None} will be returned.
   @param driveSpeed: Speed at which the drive writes.
   @return: Drive speed as an integer
   @raise ValueError: If the drive speed value is invalid.
   """
   if driveSpeed is None:
      return None
   try:
      intSpeed = int(driveSpeed)
   except TypeError:
      raise ValueError("Drive speed must be an integer >= 1.")
   if intSpeed < 1:
      raise ValueError("Drive speed must an integer >= 1.")
   return intSpeed

