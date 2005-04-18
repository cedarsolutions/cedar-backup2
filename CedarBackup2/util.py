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
# This file was created with a width of 132 characters, and NO tabs.

########################################################################
# Module documentation
########################################################################

"""
Provides general-purpose utilities. 

@sort: AbsolutePathList, ObjectTypeList, convertSize, getUidGid, changeOwnership, 
       splitCommandLine, executeCommand, calculateFileAge, encodePath, 
       ISO_SECTOR_SIZE, BYTES_PER_SECTOR, 
       BYTES_PER_KBYTE, BYTES_PER_MBYTE, BYTES_PER_GBYTE, KBYTES_PER_MBYTE, MBYTES_PER_GBYTE, 
       SECONDS_PER_MINUTE, MINUTES_PER_HOUR, HOURS_PER_DAY, SECONDS_PER_DAY, 
       UNIT_BYTES, UNIT_KBYTES, UNIT_MBYTES, UNIT_SECTORS

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
import popen2
import logging
import pwd
import grp
import string


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
UNIT_SECTORS       = 3

MTAB_FILE          = "/etc/mtab"
DEV_NULL_PATH      = "/dev/null"

MOUNT_CMD          = [ "mount", ]
UMOUNT_CMD         = [ "umount", ]


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
   """

   def append(self, item):
      """
      Overrides the standard C{append} method.
      @raise ValueError: If item is not an absolute path.
      """
      if not os.path.isabs(item):
         raise ValueError("Item must be an absolute path.")
      list.append(self, item)

   def insert(self, index, item):
      """
      Overrides the standard C{insert} method.
      @raise ValueError: If item is not an absolute path.
      """
      if not os.path.isabs(item):
         raise ValueError("Item must be an absolute path.")
      list.insert(self, index, item)

   def extend(self, seq):
      """
      Overrides the standard C{insert} method.
      @raise ValueError: If any item is not an absolute path.
      """
      for item in seq:
         if not os.path.isabs(item):
            raise ValueError("All items must be absolute paths.")
      list.extend(self, seq)


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
# Pipe class definition
########################################################################

class Pipe(popen2.Popen4):

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

   I really wish there were a prettier way to do this.  Unfortunately, I need
   access to the guts of the constructor implementation because of the way the
   pipe process is forked, etc.  It doesn't work to just call the superclass
   constructor and then modify a few things afterwards.  Even worse, I have to
   access private C{popen2} module members C{_cleanup} and C{_active} in order
   to duplicate the implementation.  Hopefully that will continue to work. :(
   
   @copyright: Some of this code, prior to customization, was originally part
   of the Python 2.3 codebase.  Python code is copyright (c) 2001, 2002 Python
   Software Foundation; All Rights Reserved.
   """
   
   def __init__(self, cmd, bufsize=-1, ignoreStderr=False):
      if not ignoreStderr:
         popen2.Popen4.__init__(self, cmd, bufsize)
      else:
         popen2._cleanup()
         p2cread, p2cwrite = os.pipe()
         c2pread, c2pwrite = os.pipe()
         self.pid = os.fork()
         if self.pid == 0: # Child
            os.dup2(p2cread, 0)
            os.dup2(c2pwrite, 1)
            null = os.open(DEV_NULL_PATH, os.O_RDWR)
            os.dup2(null, 2)
            os.close(null)
            self._run_child(cmd)
         os.close(p2cread)
         self.tochild = os.fdopen(p2cwrite, 'w', bufsize)
         os.close(c2pwrite)
         self.fromchild = os.fdopen(c2pread, 'r', bufsize)
         popen2._active.append(self)
      self.tochild.close()       # we'll never write to it, and this way we don't confuse anything.


########################################################################
# Public functions
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
      - C{UNIT_KBYTES} - Kilobytes, where 1kB = 1024B
      - C{UNIT_MBYTES} - Megabytes, where 1MB = 1024kB
      - C{UNIT_SECTORS} - Sectors, where 1 sector = 2048B

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

   @param user: User name
   @type user: User name as a string

   @param group: Group name
   @type group: Group name as a string

   @return: Tuple C{(uid, gid)} matching passed-in user and group.
   @raise ValueError: If the ownership user/group values are invalid
   """
   try:
      uid = pwd.getpwnam(user)[2]
      gid = grp.getgrnam(group)[2]
      logger.debug("Translated [%s:%s] into [%d:%d]." % (user, group, uid, gid))
      return (uid, gid)
   except Exception, e:
      logger.debug("Error looking up uid and gid for [%s:%s]: %s" % (user, group, e))
      raise ValueError("Unable to lookup up uid and gid for passed in user/group.")


#############################
# changeOwnership() function
#############################

def changeOwnership(path, user, group):
   """
   Changes ownership of path to match the user and group.
   @param path: Path whose ownership to change.
   @param user: User which owns file.
   @param group: Group which owns file.
   """
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

   @return: List of arguments, suitable for passing to L{popen2.Popen4}.
   """
   fields = re.findall('[^ "]+|"[^"]+"', commandLine)
   fields = map(lambda field: field.replace('"', ''), fields)
   return fields


############################
# executeCommand() function
############################

def executeCommand(command, args, returnOutput=False, ignoreStderr=False, doNotLog=False, outputFile=None):
   """
   Executes a shell command, hopefully in a safe way (UNIX-specific).

   This function exists to replace direct calls to L{os.popen()} in the Cedar
   Backup code.  It's not safe to call a function such as L{os.popen()} with
   untrusted arguments, since that can cause problems if the string contains
   non-safe variables or other constructs (imagine that the argument is
   C{$WHATEVER}, but C{$WHATEVER} contains something like C{"; rm -fR ~/;
   echo"} in the current environment).

   It's safer to use C{popen4} (or C{popen2} or C{popen3}) and pass a list
   rather than a string for the first argument.  When called this way,
   C{popen4} will use the list's first item as the command and the remainder of
   the list's items as arguments to that command.  What this function uses is
   actually a customized L{Pipe} class that inherits from C{popen2.Popen4}.

   Under the normal case, this function will return a tuple of C{(status,
   None)} where the status is the wait-encoded return status of the call per
   the L{popen2.Popen4} documentation.  If C{returnOutput} is passed in as
   C{True}, the function will return a tuple of C{(status, output)} where
   C{output} is a list of strings, one entry per line in the output from the
   command.  Output is always logged to the C{ouputLogger.info()} target,
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

   @param devicePath: Path of device to be mounted.
   @param mountPoint: Path that device should be mounted at.
   @param fsType: Type of the filesystem assumed to be available via the device.

   @raise IOError: If the device cannot be mounted.
   """
   if fsType is None:
      args = [ devicePath, mountPoint ]
   else:
      args = [ "-t", fsType, devicePath, mountPoint ]
   result = executeCommand(MOUNT_CMD, args, returnOutput=False, ignoreStderr=True)[0]
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

   @param mountPoint: Mount point to be unmounted.
   @param removeAfter: Remove the mount point after unmounting it.
   @param attempts: Number of times to attempt the unmount.
   @param waitSeconds: Number of seconds to wait between repeated attempts.

   @raise IOError: If the mount point is still mounted after attempts are exhausted.
   """
   if os.path.ismount(mountPoint):
      for attempt in range(0, attempts):
         logger.debug("Making attempt %d to unmount [%s]." % (attempt, mountPoint))
         result = executeCommand(UMOUNT_CMD, [ mountPoint, ], returnOutput=False, ignoreStderr=True)[0]
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

   @note: As a special case, if C{path} is C{None}, then this function will
   return C{None}.

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

