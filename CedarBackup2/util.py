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
# Purpose  : Provides general-purpose utilities.
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# This file was created with a width of 132 characters, and NO tabs.

########################################################################
# Module documentation
########################################################################

"""
Provides general-purpose utilities. 

@sort: AbsolutePathList, ObjectTypeList, convertSize, 
       getUidGid, splitCommandLine, executeCommand, calculateFileAge,
       ISO_SECTOR_SIZE, BYTES_PER_KBYTE, KBYTES_PER_MBYTE, BYTES_PER_MBYTE,
       BYTES_PER_SECTOR, SECONDS_PER_MINUTE, MINUTES_PER_HOUR, HOURS_PER_DAY, 
       SECONDS_PER_DAY, UNIT_BYTES, UNIT_KBYTES, UNIT_MBYTES, UNIT_SECTORS

@var ISO_SECTOR_SIZE: Size of an ISO image sector, in bytes.
@var BYTES_PER_KBYTE: Number of bytes (B) per kilobyte (kB).
@var KBYTES_PER_MBYTE: Number of kilobytes (kB) per megabyte (MB).
@var BYTES_PER_MBYTE: Number of bytes (B) per megabyte (MB).
@var BYTES_PER_SECTOR: Number of bytes (B) per ISO sector.
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

import os
import re
import time
import popen2
import logging
import pwd
import grp


########################################################################
# Module-wide constants and variables
########################################################################

logger = logging.getLogger("CedarBackup2.util")

ISO_SECTOR_SIZE    = 2048.0   # in bytes

BYTES_PER_KBYTE    = 1024.0
KBYTES_PER_MBYTE   = 1024.0
BYTES_PER_MBYTE    = BYTES_PER_KBYTE * KBYTES_PER_MBYTE
BYTES_PER_SECTOR   = ISO_SECTOR_SIZE

SECONDS_PER_MINUTE = 60
MINUTES_PER_HOUR   = 60
HOURS_PER_DAY      = 24
SECONDS_PER_DAY    = SECONDS_PER_MINUTE * MINUTES_PER_HOUR * HOURS_PER_DAY

UNIT_BYTES         = 0
UNIT_KBYTES        = 1
UNIT_MBYTES        = 2
UNIT_SECTORS       = 3


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
      logger.debug("Translated user/group %s/%s into uid/gid %d/%d." % (user, group, uid, gid))
      return (uid, gid)
   except Exception, e:
      logger.debug("Error looking up uid and gid for user/group %s/%s: %s" % (user, group, e))
      raise ValueError("Unable to lookup up uid and gid for passed in user/group.")


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

def executeCommand(command, args, returnOutput=False, ignoreStderr=False):
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
   the list's items as arguments to that command.

   Under the normal case, this function will return a tuple of C{(status,
   None)} where the status is the wait-encoded return status of the call per
   the L{popen2.Popen4} documentation.  If C{returnOutput} is passed in as
   C{True}, the function will return a tuple of C{(status, output)} where
   C{output} is a list of strings, one entry per line in the output from the
   command.  Output is always logged to the C{logger.info()} target, regardless
   of whether it's returned.

   By default, C{stdout} and C{stderr} will be intermingled in the output.
   However, if you pass in C{ignoreStderr=True}, then only C{stdout} will be
   included in the output.  This is implemented by using L{popen2.Popen4} in
   the normal case and L{popen2.Popen3} if C{stderr} is to be ignored.

   @note: I know that it's a bit confusing that the command and the arguments
   are both lists.  I could have just required the caller to pass in one big
   list.  However, I think it makes some sense to keep the command (the
   constant part of what we're executing, i.e. C{"scp -B"}) separate from its
   arguments, even if they both end up looking kind of similar.

   @note: You cannot redirect output (i.e. C{2>&1}, C{2>/dev/null}, etc.) using
   this function.  The redirection string would be passed to the command just
   like any other argument.  However, you can implement C{2>/dev/null} by using
   C{ignoreStderr=True}, as discussed above.

   @param command: Shell command to execute
   @type command: List of individual arguments that make up the command

   @param args: List of arguments to the command
   @type args: List of additional arguments to the command

   @param returnOutput: Indicates whether to return the output of the command
   @type returnOutput: Boolean C{True} or C{False}

   @return: Tuple of C{(result, output)} as described above.
   """
   logger.debug("Executing command [%s] with args %s." % (command, args))
   output = []
   fields = command[:]        # make sure to copy it so we don't destroy it
   fields.extend(args)
   if ignoreStderr:
      pipe = popen2.Popen3(fields, capturestderr=True)
   else:
      pipe = popen2.Popen4(fields)
   pipe.tochild.close()       # we'll never write to it, and this way we don't confuse anything.
   while True:
      line = pipe.fromchild.readline()
      if not line: break
      if returnOutput: output.append(line)
      logger.info(line[:-1])  # this way the log will (hopefully) get updated in realtime
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

   @return: Age of the file in days.
   @raise OSError: If the file doesn't exist.
   """
   currentTime = int(time.time())
   fileStats = os.stat(file)
   lastUse = max(fileStats.st_atime, fileStats.st_mtime)  # "most recent" is "largest" 
   ageInDays = (currentTime - lastUse) / SECONDS_PER_DAY
   return ageInDays

