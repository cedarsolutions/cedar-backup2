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
# Purpose  : Provides configuration-related objects.
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# This file was created with a width of 132 characters, and NO tabs.

########################################################################
# Module documentation
########################################################################

"""
Provides configuration-related objects.

Summary
=======

   Cedar Backup stores all of its configuration in an XML document typically
   called C{cback.conf}.  The standard location for this document is in
   C{/etc}, but users can specify a different location if they want to.  

   The C{Config} class is a Python object representation of a Cedar Backup XML
   configuration file.  The representation is two-way: XML data can be used to
   create a C{Config} object, and then changes to the object can be propogated
   back to disk.  A C{Config} object can even be used to create a configuration
   file from scratch programmatically.

   The C{Config} class is intended to be the only Python-language interface to
   Cedar Backup configuration on disk.  Cedar Backup will use the class as its
   internal representation of configuration, and applications external to Cedar
   Backup itself (such as a hypothetical third-party configuration tool written
   in Python or a third party extension module) should also use the class when
   they need to read and write configuration files.

   This module also contains a set of very general XML-parsing and writing
   functions that third-party extensions can use to simplify the job of parsing
   and writing their own configuration.

External Python Libraries
=========================

   This class is one of the few pieces of code in the CedarBackup2 package that
   requires functionality outside of the Python 2.3 standard library.  It
   depends on the XPath functionality provided by the PyXML product in the
   C{xml.xpath} package.

   The PyXML XPath library is not very fast.  This is particularly noticable
   when reading lists of things with the XPath C{[n]} syntax.  Because of this,
   the code below jumps through some performance-improvement hoops that would
   normally not be required when using a faster library.

Backwards Compatibility
=======================

   The configuration file format has changed between Cedar Backup 1.x and Cedar
   Backup 2.x.  Any Cedar Backup 1.x configuration file is also a valid Cedar
   Backup 2.x configuration file.  However, it doesn't work to go the other
   direction, as the 2.x configuration files may contain additional fields that
   are not accepted by older versions of the software.  

XML Configuration Structure
===========================

   A C{Config} object can either be created "empty", or can be created based on
   XML input (either in the form of a string or read in from a file on disk).
   Generally speaking, the XML input I{must} result in a C{Config} object which
   passes the validations laid out below in the I{Validation} section.  

   An XML configuration file is composed of seven sections:

      - I{reference}: specifies reference information about the file (author, revision, etc)
      - I{extensions}: specifies mappings to Cedar Backup extensions (external code)
      - I{options}: specifies global configuration options
      - I{collect}: specifies configuration related to the collect action
      - I{stage}: specifies configuration related to the stage action
      - I{store}: specifies configuration related to the store action
      - I{purge}: specifies configuration related to the purge action

   Each section is represented by an class in this module, and then the overall
   C{Config} class is a composition of the various other classes.  

   Any configuration section that is missing in the XML document (or has not
   been filled into an "empty" document) will just be set to C{None} in the
   object representation.  The same goes for individual fields within each
   configuration section.  Keep in mind that the document might not be
   completely valid if some sections or fields aren't filled in - but that
   won't matter until validation takes place (see the I{Validation} section
   below).

Unicode vs. String Data
=======================

   By default, all string data that comes out of XML documents in Python is
   unicode data (i.e. C{u"whatever"}).  This is fine for many things, but when
   it comes to filesystem paths, it can cause us some problems.  We really want
   strings to be encoded in the filesystem encoding rather than being unicode.
   So, most elements in configuration which represent filesystem paths are
   coverted to plain strings using L{util.encodePath}.  The main exception is
   the various C{absoluteExcludePath} and C{relativeExcludePath} lists.  These
   are I{not} converted, because they are generally only used for filtering,
   not for filesystem operations.

Validation 
==========

   There are two main levels of validation in the C{Config} class and its
   children.  The first is field-level validation.  Field-level validation
   comes into play when a given field in an object is assigned to or updated.
   We use Python's C{property} functionality to enforce specific validations on
   field values, and in some places we even use customized list classes to
   enforce validations on list members.  You should expect to catch a
   C{ValueError} exception when making assignments to configuration class
   fields.

   The second level of validation is post-completion validation.  Certain
   validations don't make sense until a document is fully "complete".  We don't
   want these validations to apply all of the time, because it would make
   building up a document from scratch a real pain.  For instance, we might
   have to do things in the right order to keep from throwing exceptions, etc.

   All of these post-completion validations are encapsulated in the
   L{Config.validate} method.  This method can be called at any time by a
   client, and will always be called immediately after creating a C{Config}
   object from XML data and before exporting a C{Config} object to XML.  This
   way, we get decent ease-of-use but we also don't accept or emit invalid
   configuration files.

   The L{Config.validate} implementation actually takes two passes to
   completely validate a configuration document.  The first pass at validation
   is to ensure that the proper sections are filled into the document.  There
   are default requirements, but the caller has the opportunity to override
   these defaults.

   The second pass at validation ensures that any filled-in section contains
   valid data.  Any section which is not set to C{None} is validated according
   to the rules for that section (see below).

   I{Reference Validations}

   No validations.

   I{Extensions Validations}

   The list of actions may be either C{None} or an empty list C{[]} if desired.
   Each extended action must include a name, a module and a function.  The index
   value is optional.

   I{Options Validations}

   All fields must be filled in.  The rcp command is used as a default value
   for all remote peers in the staging section.  Remote peers can also rely on
   the backup user as the default remote user name if they choose.

   I{Collect Validations}

   The target directory must be filled in.  The collect mode, archive mode and
   ignore file are all optional.  The list of absolute paths to exclude and
   patterns to exclude may be either C{None} or an empty list C{[]} if desired.
   The collect directory list must contain at least one entry.  

   Each collect directory entry must contain an absolute path to collect, and
   then must either be able to take collect mode, archive mode and ignore file
   configuration from the parent C{CollectConfig} object, or must set each
   value on its own.  The list of absolute paths to exclude, relative paths to
   exclude and patterns to exclude may be either C{None} or an empty list C{[]}
   if desired.  Any list of absolute paths to exclude or patterns to exclude
   will be combined with the same list in the C{CollectConfig} object to make
   the complete list for a given directory.

   I{Stage Validations}

   The target directory must be filled in.  There must be at least one peer
   (remote or local) between the two lists of peers.  A list with no entries
   can be either C{None} or an empty list C{[]} if desired.

   Local peers must be completely filled in, including both name and collect
   directory.  Remote peers must also fill in the name and collect directory,
   but can leave the remote user and rcp command unset.  In this case, the
   remote user is assumed to match the backup user from the options section and
   rcp command is taken directly from the options section.

   I{Store Validations}

   The device type and drive speed are optional, and all other values are
   required (missing booleans will be set to defaults, which is OK).

   The image writer functionality in the C{writer} module is supposed to be
   able to handle a device speed of C{None}.  Any caller which needs a "real"
   (non-C{None}) value for the device type can use C{DEFAULT_DEVICE_TYPE},
   which is guaranteed to be sensible.

   I{Purge Validations}

   The list of purge directories may be either C{None} or an empty list C{[]}
   if desired.  All purge directories must contain a path and a retain days
   value.

@sort: ExtendedAction, CollectDir, PurgeDir, LocalPeer, RemotePeer, 
       ReferenceConfig, ExtensionsConfig, OptionsConfig CollectConfig, 
       StageConfig, StoreConfig, PurgeConfig, Config,
       TRUE_BOOLEAN_VALUES, FALSE_BOOLEAN_VALUES, VALID_BOOLEAN_VALUES,
       DEFAULT_DEVICE_TYPE, DEFAULT_MEDIA_TYPE, 
       VALID_DEVICE_TYPES, VALID_MEDIA_TYPES, 
       VALID_COLLECT_MODES, VALID_ARCHIVE_MODES

@var VALID_BOOLEAN_VALUES: List of valid boolean values in XML.
@var TRUE_BOOLEAN_VALUES: List of boolean values in XML representing C{True}.
@var FALSE_BOOLEAN_VALUES: List of boolean values in XML representing C{False}.
@var DEFAULT_DEVICE_TYPE: The default device type.
@var DEFAULT_MEDIA_TYPE: The default media type.
@var VALID_DEVICE_TYPES: List of valid device types.
@var VALID_MEDIA_TYPES: List of valid media types.
@var VALID_COLLECT_MODES: List of valid collect modes.
@var VALID_COMPRESS_MODES: List of valid compress modes.
@var VALID_ARCHIVE_MODES: List of valid archive modes.

@author: Kenneth J. Pronovici <pronovic@ieee.org>
"""

########################################################################
# Imported modules
########################################################################

# System modules
import os
import re
import logging
from StringIO import StringIO

# XML-related modules
from xml.dom.ext.reader import PyExpat
from xml.xpath import Evaluate
from xml.parsers.expat import ExpatError
from xml.dom.minidom import Node
from xml.dom.minidom import getDOMImplementation
from xml.dom.minidom import parseString
from xml.dom.ext import PrettyPrint

# Cedar Backup modules
from CedarBackup2.writer import validateScsiId, validateDriveSpeed
from CedarBackup2.util import UnorderedList, AbsolutePathList, ObjectTypeList, encodePath


########################################################################
# Module-wide constants and variables
########################################################################

logger = logging.getLogger("CedarBackup2.log.config")

TRUE_BOOLEAN_VALUES   = [ "Y", "y", ]
FALSE_BOOLEAN_VALUES  = [ "N", "n", ]
VALID_BOOLEAN_VALUES  = TRUE_BOOLEAN_VALUES + FALSE_BOOLEAN_VALUES

DEFAULT_DEVICE_TYPE   = "cdwriter"
DEFAULT_MEDIA_TYPE    = "cdrw-74"

VALID_DEVICE_TYPES    = [ "cdwriter", ]
VALID_MEDIA_TYPES     = [ "cdr-74", "cdrw-74", "cdr-80", "cdrw-80", ]
VALID_COLLECT_MODES   = [ "daily", "weekly", "incr", ]
VALID_ARCHIVE_MODES   = [ "tar", "targz", "tarbz2", ]
VALID_COMPRESS_MODES  = [ "none", "gzip", "bzip2", ]


########################################################################
# ExtendedAction class definition
########################################################################

class ExtendedAction(object):

   """
   Class representing an extended action.

   As with all of the other classes that represent configuration sections, all
   of these values are optional.  It is up to some higher-level construct to
   decide whether everything they need is filled in.   Some validation is done
   on non-C{None} assignments through the use of the Python C{property()}
   construct.

   Essentially, an extended action needs to allow the following to happen::

      exec("from %s import %s" % (module, function))
      exec("%s(action, configPath")" % function)

   The following restrictions exist on data in this class:

      - The action name must be a non-empty string consisting of lower-case letters and digits.
      - The module must be a non-empty string and a valid Python identifier.
      - The function must be an on-empty string and a valid Python identifier.
      - The index must be a positive integer.

   @sort: __init__, __repr__, __str__, __cmp__, action, module, function, index
   """

   def __init__(self, name=None, module=None, function=None, index=None):
      """
      Constructor for the C{ExtendedAction} class.

      @param name: Name of the extended action
      @param module: Name of the module containing the extended action function
      @param function: Name of the extended action function
      @param index: Index of action, for execution ordering

      @raise ValueError: If one of the values is invalid.
      """
      self._name = None
      self._module = None
      self._function = None
      self._index = None
      self.name = name
      self.module = module
      self.function = function
      self.index = index

   def __repr__(self):
      """
      Official string representation for class instance.
      """
      return "ExtendedAction(%s, %s, %s, %s)" % (self.name, self.module, self.function, self.index)

   def __str__(self):
      """
      Informal string representation for class instance.
      """
      return self.__repr__()

   def __cmp__(self, other):
      """
      Definition of equals operator for this class.
      @param other: Other object to compare to.
      @return: -1/0/1 depending on whether self is C{<}, C{=} or C{>} other.
      """
      if other is None:
         return 1
      if self._name != other._name:
         if self._name < other._name:
            return -1
         else:
            return 1
      if self._module != other._module: 
         if self._module < other._module: 
            return -1
         else:
            return 1
      if self._function != other._function:
         if self._function < other._function:
            return -1
         else:
            return 1
      if self._index != other._index:
         if self._index < other._index:
            return -1
         else:
            return 1
      return 0

   def _setName(self, value):
      """
      Property target used to set the action name.
      The value must be a non-empty string if it is not C{None}.
      It must also consist only of lower-case letters and digits.
      @raise ValueError: If the value is an empty string.
      """
      pattern = re.compile(r"^[a-z0-9]*$")
      if value is not None:
         if len(value) < 1:
            raise ValueError("The action name must be a non-empty string.")
         if not pattern.search(value):
            raise ValueError("The action name must consist of only lower-case letters and digits.")
      self._name = value

   def _getName(self):
      """
      Property target used to get the action name.
      """
      return self._name

   def _setModule(self, value):
      """
      Property target used to set the module name.
      The value must be a non-empty string if it is not C{None}.
      It must also be a valid Python identifier.
      @raise ValueError: If the value is an empty string.
      """
      pattern = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)(\.[A-Za-z_][A-Za-z0-9_]*)*$")
      if value is not None:
         if len(value) < 1:
            raise ValueError("The module name must be a non-empty string.")
         if not pattern.search(value):
            raise ValueError("The module name must be a valid Python identifier.")
      self._module = value

   def _getModule(self):
      """
      Property target used to get the module name.
      """
      return self._module

   def _setFunction(self, value):
      """
      Property target used to set the function name.
      The value must be a non-empty string if it is not C{None}.
      It must also be a valid Python identifier.
      @raise ValueError: If the value is an empty string.
      """
      pattern = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
      if value is not None:
         if len(value) < 1:
            raise ValueError("The function name must be a non-empty string.")
         if not pattern.search(value):
            raise ValueError("The function name must be a valid Python identifier.")
      self._function = value

   def _getFunction(self):
      """
      Property target used to get the function name.
      """
      return self._function

   def _setIndex(self, value):
      """
      Property target used to set the action index.
      The value must be an integer >= 0.
      @raise ValueError: If the value is not valid.
      """
      if value is None:
         self._index = None
      else:
         try:
            value = int(value)
         except TypeError:
            raise ValueError("Action index value must be an integer >= 0.")
         if value < 0:
            raise ValueError("Action index value must be an integer >= 0.")
         self._index = value

   def _getIndex(self):
      """
      Property target used to get the action index.
      """
      return self._index

   name = property(_getName, _setName, None, "Name of the extended action.")
   module = property(_getModule, _setModule, None, "Name of the module containing the extended action function.")
   function = property(_getFunction, _setFunction, None, "Name of the extended action function.")
   index = property(_getIndex, _setIndex, None, "Index of action, for execution ordering.")


########################################################################
# CommandOverride class definition
########################################################################

class CommandOverride(object):

   """
   Class representing a piece of Cedar Backup command override configuration.

   As with all of the other classes that represent configuration sections, all
   of these values are optional.  It is up to some higher-level construct to
   decide whether everything they need is filled in.   Some validation is done
   on non-C{None} assignments through the use of the Python C{property()}
   construct.

   The following restrictions exist on data in this class:

      - The absolute path must be absolute

   @note: Lists within this class are "unordered" for equality comparisons.

   @sort: __init__, __repr__, __str__, __cmp__, command, absolutePath
   """

   def __init__(self, command=None, absolutePath=None):
      """
      Constructor for the C{CommandOverride} class.

      @param command: Name of command to be overridden.
      @param absolutePath: Absolute path of the overrridden command.

      @raise ValueError: If one of the values is invalid.
      """
      self._command = None
      self._absolutePath = None
      self.command = command
      self.absolutePath = absolutePath

   def __repr__(self):
      """
      Official string representation for class instance.
      """
      return "CommandOverride(%s, %s)" % (self.command, self.absolutePath)

   def __str__(self):
      """
      Informal string representation for class instance.
      """
      return self.__repr__()

   def __cmp__(self, other):
      """
      Definition of equals operator for this class.
      @param other: Other object to compare to.
      @return: -1/0/1 depending on whether self is C{<}, C{=} or C{>} other.
      """
      if other is None:
         return 1
      if self._command != other._command: 
         if self._command < other.command:
            return -1
         else:
            return 1 
      if self._absolutePath != other._absolutePath: 
         if self._absolutePath < other.absolutePath:
            return -1
         else:
            return 1 
      return 0

   def _setCommand(self, value):
      """
      Property target used to set the command.
      The value must be a non-empty string if it is not C{None}.
      @raise ValueError: If the value is an empty string.
      """
      if value is not None:
         if len(value) < 1:
            raise ValueError("The command must be a non-empty string.")
      self._command = value

   def _getCommand(self):
      """
      Property target used to get the command.
      """
      return self._command

   def _setAbsolutePath(self, value):
      """
      Property target used to set the absolute path.
      The value must be an absolute path if it is not C{None}.
      It does not have to exist on disk at the time of assignment.
      @raise ValueError: If the value is not an absolute path.
      @raise ValueError: If the value cannot be encoded properly.
      """
      if value is not None:
         if not os.path.isabs(value):
            raise ValueError("Absolute path must be, er, an absolute path.")
      self._absolutePath = encodePath(value)

   def _getAbsolutePath(self):
      """
      Property target used to get the absolute path.
      """
      return self._absolutePath

   command = property(_getCommand, _setCommand, None, doc="Name of command to be overridden.")
   absolutePath = property(_getAbsolutePath, _setAbsolutePath, None, doc="Absolute path of the directory to collect.")


########################################################################
# CollectDir class definition
########################################################################

class CollectDir(object):

   """
   Class representing a Cedar Backup collect directory.

   As with all of the other classes that represent configuration sections, all
   of these values are optional.  It is up to some higher-level construct to
   decide whether everything they need is filled in.   Some validation is done
   on non-C{None} assignments through the use of the Python C{property()}
   construct.

   The following restrictions exist on data in this class:

      - Absolute paths must be absolute
      - The collect mode must be one of the values in L{VALID_COLLECT_MODES}.
      - The archive mode must be one of the values in L{VALID_ARCHIVE_MODES}.
      - The ignore file must be a non-empty string.

   For the C{absoluteExcludePaths} list, validation is accomplished through the
   L{util.AbsolutePathList} list implementation that overrides common list
   methods and transparently does the absolute path validation for us.

   @note: Lists within this class are "unordered" for equality comparisons.

   @sort: __init__, __repr__, __str__, __cmp__, absolutePath, collectMode,
          archiveMode, ignoreFile, absoluteExcludePaths, relativeExcludePaths,
          excludePatterns
   """

   def __init__(self, absolutePath=None, collectMode=None, archiveMode=None, ignoreFile=None,
                absoluteExcludePaths=None, relativeExcludePaths=None, excludePatterns=None):
      """
      Constructor for the C{CollectDir} class.

      @param absolutePath: Absolute path of the directory to collect.
      @param collectMode: Overridden collect mode for this directory.
      @param archiveMode: Overridden archive mode for this directory.
      @param ignoreFile: Overidden ignore file name for this directory.
      @param absoluteExcludePaths: List of absolute paths to exclude.
      @param relativeExcludePaths: List of relative paths to exclude.
      @param excludePatterns: List of regular expression patterns to exclude.

      @raise ValueError: If one of the values is invalid.
      """
      self._absolutePath = None
      self._collectMode = None
      self._archiveMode = None
      self._ignoreFile = None
      self._absoluteExcludePaths = None
      self._relativeExcludePaths = None
      self._excludePatterns = None
      self.absolutePath = absolutePath
      self.collectMode = collectMode
      self.archiveMode = archiveMode
      self.ignoreFile = ignoreFile
      self.absoluteExcludePaths = absoluteExcludePaths
      self.relativeExcludePaths = relativeExcludePaths
      self.excludePatterns = excludePatterns

   def __repr__(self):
      """
      Official string representation for class instance.
      """
      return "CollectDir(%s, %s, %s, %s, %s, %s, %s)" % (self.absolutePath, self.collectMode, 
                                                         self.archiveMode, self.ignoreFile, 
                                                         self.absoluteExcludePaths, 
                                                         self.relativeExcludePaths, 
                                                         self.excludePatterns)

   def __str__(self):
      """
      Informal string representation for class instance.
      """
      return self.__repr__()

   def __cmp__(self, other):
      """
      Definition of equals operator for this class.
      Lists within this class are "unordered" for equality comparisons.
      @param other: Other object to compare to.
      @return: -1/0/1 depending on whether self is C{<}, C{=} or C{>} other.
      """
      if other is None:
         return 1
      if self._absolutePath != other._absolutePath: 
         if self._absolutePath < other.absolutePath:
            return -1
         else:
            return 1 
      if self._collectMode != other._collectMode: 
         if self._collectMode < other._collectMode: 
            return -1
         else:
            return 1 
      if self._archiveMode != other._archiveMode: 
         if self._archiveMode < other._archiveMode: 
            return -1
         else:
            return 1 
      if self._ignoreFile != other._ignoreFile: 
         if self._ignoreFile < other._ignoreFile: 
            return -1
         else:
            return 1 
      if self._absoluteExcludePaths != other._absoluteExcludePaths: 
         if self._absoluteExcludePaths < other._absoluteExcludePaths: 
            return -1
         else:
            return 1 
      if self._relativeExcludePaths != other._relativeExcludePaths:  
         if self._relativeExcludePaths < other._relativeExcludePaths:  
            return -1
         else:
            return 1 
      if self._excludePatterns != other._excludePatterns: 
         if self._excludePatterns < other._excludePatterns: 
            return -1
         else:
            return 1 
      return 0

   def _setAbsolutePath(self, value):
      """
      Property target used to set the absolute path.
      The value must be an absolute path if it is not C{None}.
      It does not have to exist on disk at the time of assignment.
      @raise ValueError: If the value is not an absolute path.
      @raise ValueError: If the value cannot be encoded properly.
      """
      if value is not None:
         if not os.path.isabs(value):
            raise ValueError("Absolute path must be, er, an absolute path.")
      self._absolutePath = encodePath(value)

   def _getAbsolutePath(self):
      """
      Property target used to get the absolute path.
      """
      return self._absolutePath

   def _setCollectMode(self, value):
      """
      Property target used to set the collect mode.
      If not C{None}, the mode must be one of the values in L{VALID_COLLECT_MODES}.
      @raise ValueError: If the value is not valid.
      """
      if value is not None:
         if value not in VALID_COLLECT_MODES:
            raise ValueError("Collect mode must be one of %s." % VALID_COLLECT_MODES)
      self._collectMode = value

   def _getCollectMode(self):
      """
      Property target used to get the collect mode.
      """
      return self._collectMode

   def _setArchiveMode(self, value):
      """
      Property target used to set the archive mode.
      If not C{None}, the mode must be one of the values in L{VALID_ARCHIVE_MODES}.
      @raise ValueError: If the value is not valid.
      """
      if value is not None:
         if value not in VALID_ARCHIVE_MODES:
            raise ValueError("Archive mode must be one of %s." % VALID_ARCHIVE_MODES)
      self._archiveMode = value

   def _getArchiveMode(self):
      """
      Property target used to get the archive mode.
      """
      return self._archiveMode

   def _setIgnoreFile(self, value):
      """
      Property target used to set the ignore file.
      The value must be a non-empty string if it is not C{None}.
      @raise ValueError: If the value is an empty string.
      """
      if value is not None:
         if len(value) < 1:
            raise ValueError("The ignore file must be a non-empty string.")
      self._ignoreFile = value

   def _getIgnoreFile(self):
      """
      Property target used to get the ignore file.
      """
      return self._ignoreFile

   def _setAbsoluteExcludePaths(self, value):
      """
      Property target used to set the absolute exclude paths list.
      Either the value must be C{None} or each element must be an absolute path.
      Elements do not have to exist on disk at the time of assignment.
      @raise ValueError: If the value is not an absolute path.
      """
      if value is None:
         self._absoluteExcludePaths = None
      else:
         try:
            saved = self._absoluteExcludePaths
            self._absoluteExcludePaths = AbsolutePathList()
            self._absoluteExcludePaths.extend(value)
         except Exception, e:
            self._absoluteExcludePaths = saved
            raise e

   def _getAbsoluteExcludePaths(self):
      """
      Property target used to get the absolute exclude paths list.
      """
      return self._absoluteExcludePaths

   def _setRelativeExcludePaths(self, value):
      """
      Property target used to set the relative exclude paths list.
      Elements do not have to exist on disk at the time of assignment.
      """
      if value is None:
         self._relativeExcludePaths = None
      else:
         try:
            saved = self._relativeExcludePaths
            self._relativeExcludePaths = UnorderedList()
            self._relativeExcludePaths.extend(value)
         except Exception, e:
            self._relativeExcludePaths = saved
            raise e

   def _getRelativeExcludePaths(self):
      """
      Property target used to get the relative exclude paths list.
      """
      return self._relativeExcludePaths

   def _setExcludePatterns(self, value):
      """
      Property target used to set the exclude patterns list.
      """
      if value is None:
         self._excludePatterns = None
      else:
         try:
            saved = self._excludePatterns
            self._excludePatterns = UnorderedList()
            self._excludePatterns.extend(value)
         except Exception, e:
            self._excludePatterns = saved
            raise e

   def _getExcludePatterns(self):
      """
      Property target used to get the exclude patterns list.
      """
      return self._excludePatterns

   absolutePath = property(_getAbsolutePath, _setAbsolutePath, None, doc="Absolute path of the directory to collect.")
   collectMode = property(_getCollectMode, _setCollectMode, None, doc="Overridden collect mode for this directory.")
   archiveMode = property(_getArchiveMode, _setArchiveMode, None, doc="Overridden archive mode for this directory.")
   ignoreFile = property(_getIgnoreFile, _setIgnoreFile, None, doc="Overridden ignore file name for this directory.")
   absoluteExcludePaths = property(_getAbsoluteExcludePaths, _setAbsoluteExcludePaths, None, "List of absolute paths to exclude.")
   relativeExcludePaths = property(_getRelativeExcludePaths, _setRelativeExcludePaths, None, "List of relative paths to exclude.")
   excludePatterns = property(_getExcludePatterns, _setExcludePatterns, None, "List of regular expression patterns to exclude.")


########################################################################
# PurgeDir class definition
########################################################################

class PurgeDir(object):

   """
   Class representing a Cedar Backup purge directory.

   As with all of the other classes that represent configuration sections, all
   of these values are optional.  It is up to some higher-level construct to
   decide whether everything they need is filled in.   Some validation is done
   on non-C{None} assignments through the use of the Python C{property()}
   construct.

   The following restrictions exist on data in this class:

      - The absolute path must be an absolute path
      - The retain days value must be an integer >= 0.

   @sort: __init__, __repr__, __str__, __cmp__, absolutePath, retainDays
   """

   def __init__(self, absolutePath=None, retainDays=None):
      """
      Constructor for the C{PurgeDir} class.

      @param absolutePath: Absolute path of the directory to be purged.
      @param retainDays: Number of days content within directory should be retained.

      @raise ValueError: If one of the values is invalid.
      """
      self._absolutePath = None
      self._retainDays = None
      self.absolutePath = absolutePath
      self.retainDays = retainDays

   def __repr__(self):
      """
      Official string representation for class instance.
      """
      return "PurgeDir(%s, %s)" % (self.absolutePath, self.retainDays)

   def __str__(self):
      """
      Informal string representation for class instance.
      """
      return self.__repr__()

   def __cmp__(self, other):
      """
      Definition of equals operator for this class.
      @param other: Other object to compare to.
      @return: -1/0/1 depending on whether self is C{<}, C{=} or C{>} other.
      """
      if other is None:
         return 1
      if self._absolutePath != other._absolutePath: 
         if self._absolutePath < other._absolutePath: 
            return -1
         else:
            return 1
      if self._retainDays != other._retainDays: 
         if self._retainDays < other._retainDays: 
            return -1
         else:
            return 1
      return 0

   def _setAbsolutePath(self, value):
      """
      Property target used to set the absolute path.
      The value must be an absolute path if it is not C{None}.
      It does not have to exist on disk at the time of assignment.
      @raise ValueError: If the value is not an absolute path.
      @raise ValueError: If the value cannot be encoded properly.
      """
      if value is not None:
         if not os.path.isabs(value):
            raise ValueError("Absolute path must, er, be an absolute path.")
      self._absolutePath = encodePath(value)

   def _getAbsolutePath(self):
      """
      Property target used to get the absolute path.
      """
      return self._absolutePath

   def _setRetainDays(self, value):
      """
      Property target used to set the retain days value.
      The value must be an integer >= 0.
      @raise ValueError: If the value is not valid.
      """
      if value is None:
         self._retainDays = None
      else:
         try:
            value = int(value)
         except TypeError:
            raise ValueError("Retain days value must be an integer >= 0.")
         if value < 0:
            raise ValueError("Retain days value must be an integer >= 0.")
         self._retainDays = value

   def _getRetainDays(self):
      """
      Property target used to get the absolute path.
      """
      return self._retainDays

   absolutePath = property(_getAbsolutePath, _setAbsolutePath, None, "Absolute path of directory to purge.")
   retainDays = property(_getRetainDays, _setRetainDays, None, "Number of days content within directory should be retained.")


########################################################################
# LocalPeer class definition
########################################################################

class LocalPeer(object):

   """
   Class representing a Cedar Backup peer.

   As with all of the other classes that represent configuration sections, all
   of these values are optional.  It is up to some higher-level construct to
   decide whether everything they need is filled in.   Some validation is done
   on non-C{None} assignments through the use of the Python C{property()}
   construct.

   The following restrictions exist on data in this class:

      - The peer name must be a non-empty string.
      - The collect directory must be an absolute path.
   
   @sort: __init__, __repr__, __str__, __cmp__, name, collectDir
   """

   def __init__(self, name=None, collectDir=None):
      """
      Constructor for the C{LocalPeer} class.

      @param name: Name of the peer, typically a valid hostname.
      @param collectDir: Collect directory to stage files from on peer.

      @raise ValueError: If one of the values is invalid.
      """
      self._name = None
      self._collectDir = None
      self.name = name
      self.collectDir = collectDir

   def __repr__(self):
      """
      Official string representation for class instance.
      """
      return "LocalPeer(%s, %s)" % (self.name, self.collectDir)

   def __str__(self):
      """
      Informal string representation for class instance.
      """
      return self.__repr__()

   def __cmp__(self, other):
      """
      Definition of equals operator for this class.
      @param other: Other object to compare to.
      @return: -1/0/1 depending on whether self is C{<}, C{=} or C{>} other.
      """
      if other is None:
         return 1
      if self._name != other._name: 
         if self._name < other._name: 
            return -1
         else:
            return 1
      if self._collectDir != other._collectDir:
         if self._collectDir < other._collectDir:
            return -1
         else:
            return 1
      return 0

   def _setName(self, value):
      """
      Property target used to set the peer name.
      The value must be a non-empty string if it is not C{None}.
      @raise ValueError: If the value is an empty string.
      """
      if value is not None:
         if len(value) < 1:
            raise ValueError("The peer name must be a non-empty string.")
      self._name = value

   def _getName(self):
      """
      Property target used to get the peer name.
      """
      return self._name

   def _setCollectDir(self, value):
      """
      Property target used to set the collect directory.
      The value must be an absolute path if it is not C{None}.
      It does not have to exist on disk at the time of assignment.
      @raise ValueError: If the value is not an absolute path.
      @raise ValueError: If the value cannot be encoded properly.
      """
      if value is not None:
         if not os.path.isabs(value):
            raise ValueError("Collect directory must be an absolute path.")
      self._collectDir = encodePath(value)

   def _getCollectDir(self):
      """
      Property target used to get the collect directory.
      """
      return self._collectDir

   name = property(_getName, _setName, None, "Name of the peer, typically a valid hostname.")
   collectDir = property(_getCollectDir, _setCollectDir, None, "Collect directory to stage files from on peer.")


########################################################################
# RemotePeer class definition
########################################################################

class RemotePeer(object):

   """
   Class representing a Cedar Backup peer.

   As with all of the other classes that represent configuration sections, all
   of these values are optional.  It is up to some higher-level construct to
   decide whether everything they need is filled in.   Some validation is done
   on non-C{None} assignments through the use of the Python C{property()}
   construct.

   The following restrictions exist on data in this class:

      - The peer name must be a non-empty string.
      - The collect directory must be an absolute path.
      - The remote user must be a non-empty string.
      - The rcp command must be a non-empty string.

   @sort: __init__, __repr__, __str__, __cmp__, name, collectDir, remoteUser, rcpCommand
   """

   def __init__(self, name=None, collectDir=None, remoteUser=None, rcpCommand=None):
      """
      Constructor for the C{RemotePeer} class.

      @param name: Name of the peer, must be a valid hostname.
      @param collectDir: Collect directory to stage files from on peer.
      @param remoteUser: Name of backup user on remote peer.
      @param rcpCommand: Overridden rcp-compatible copy command for peer.

      @raise ValueError: If one of the values is invalid.
      """
      self._name = None
      self._collectDir = None
      self._remoteUser = None
      self._rcpCommand = None
      self.name = name
      self.collectDir = collectDir
      self.remoteUser = remoteUser
      self.rcpCommand = rcpCommand

   def __repr__(self):
      """
      Official string representation for class instance.
      """
      return "RemotePeer(%s, %s, %s, %s)" % (self.name, self.collectDir, self.remoteUser, self.rcpCommand)

   def __str__(self):
      """
      Informal string representation for class instance.
      """
      return self.__repr__()

   def __cmp__(self, other):
      """
      Definition of equals operator for this class.
      @param other: Other object to compare to.
      @return: -1/0/1 depending on whether self is C{<}, C{=} or C{>} other.
      """
      if other is None:
         return 1
      if self._name != other._name:
         if self._name < other._name:
            return -1
         else:
            return 1
      if self._collectDir != other._collectDir: 
         if self._collectDir < other._collectDir: 
            return -1
         else:
            return 1
      if self._remoteUser != other._remoteUser:
         if self._remoteUser < other._remoteUser:
            return -1
         else:
            return 1
      if self._rcpCommand != other._rcpCommand:
         if self._rcpCommand < other._rcpCommand:
            return -1
         else:
            return 1
      return 0

   def _setName(self, value):
      """
      Property target used to set the peer name.
      The value must be a non-empty string if it is not C{None}.
      @raise ValueError: If the value is an empty string.
      """
      if value is not None:
         if len(value) < 1:
            raise ValueError("The peer name must be a non-empty string.")
      self._name = value

   def _getName(self):
      """
      Property target used to get the peer name.
      """
      return self._name

   def _setCollectDir(self, value):
      """
      Property target used to set the collect directory.
      The value must be an absolute path if it is not C{None}.
      It does not have to exist on disk at the time of assignment.
      @raise ValueError: If the value is not an absolute path.
      @raise ValueError: If the value cannot be encoded properly.
      """
      if value is not None:
         if not os.path.isabs(value):
            raise ValueError("Collect directory must be an absolute path.")
      self._collectDir = encodePath(value)

   def _getCollectDir(self):
      """
      Property target used to get the collect directory.
      """
      return self._collectDir

   def _setRemoteUser(self, value):
      """
      Property target used to set the remote user.
      The value must be a non-empty string if it is not C{None}.
      @raise ValueError: If the value is an empty string.
      """
      if value is not None:
         if len(value) < 1:
            raise ValueError("The remote user must be a non-empty string.")
      self._remoteUser = value

   def _getRemoteUser(self):
      """
      Property target used to get the remote user.
      """
      return self._remoteUser

   def _setRcpCommand(self, value):
      """
      Property target used to set the rcp command.
      The value must be a non-empty string if it is not C{None}.
      @raise ValueError: If the value is an empty string.
      """
      if value is not None:
         if len(value) < 1:
            raise ValueError("The remote user must be a non-empty string.")
      self._rcpCommand = value

   def _getRcpCommand(self):
      """
      Property target used to get the rcp command.
      """
      return self._rcpCommand

   name = property(_getName, _setName, None, "Name of the peer, must be a valid hostname.")
   collectDir = property(_getCollectDir, _setCollectDir, None, "Collect directory to stage files from on peer.")
   remoteUser = property(_getRemoteUser, _setRemoteUser, None, "Name of backup user on remote peer.")
   rcpCommand = property(_getRcpCommand, _setRcpCommand, None, "Overridden rcp-compatible copy command for peer.")


########################################################################
# ReferenceConfig class definition
########################################################################

class ReferenceConfig(object):

   """
   Class representing a Cedar Backup reference configuration.

   The reference information is just used for saving off metadata about
   configuration and exists mostly for backwards-compatibility with Cedar
   Backup 1.x.

   As with all of the other classes that represent configuration sections, all
   of these values are optional.  It is up to some higher-level construct to
   decide whether everything they need is filled in.   We don't do any
   validation on the contents of any of the fields, although we generally
   expect them to be strings.

   @sort: __init__, __repr__, __str__, __cmp__, author, revision, description, generator
   """

   def __init__(self, author=None, revision=None, description=None, generator=None):
      """
      Constructor for the C{ReferenceConfig} class.
      
      @param author: Author of the configuration file.
      @param revision: Revision of the configuration file.
      @param description: Description of the configuration file.
      @param generator: Tool that generated the configuration file.
      """
      self._author = None
      self._revision = None
      self._description = None
      self._generator = None
      self.author = author
      self.revision = revision
      self.description = description
      self.generator = generator

   def __repr__(self):
      """
      Official string representation for class instance.
      """
      return "ReferenceConfig(%s, %s, %s, %s)" % (self.author, self.revision, self.description, self.generator)

   def __str__(self):
      """
      Informal string representation for class instance.
      """
      return self.__repr__()

   def __cmp__(self, other):
      """
      Definition of equals operator for this class.
      @param other: Other object to compare to.
      @return: -1/0/1 depending on whether self is C{<}, C{=} or C{>} other.
      """
      if other is None:
         return 1
      if self._author != other._author:
         if self._author < other._author:
            return -1
         else:
            return 1
      if self._revision != other._revision:
         if self._revision < other._revision:
            return -1
         else:
            return 1
      if self._description != other._description:
         if self._description < other._description:
            return -1
         else:
            return 1
      if self._generator != other._generator:
         if self._generator < other._generator:
            return -1
         else:
            return 1
      return 0

   def _setAuthor(self, value):
      """
      Property target used to set the author value.
      No validations.
      """
      self._author = value

   def _getAuthor(self):
      """
      Property target used to get the author value.
      """
      return self._author

   def _setRevision(self, value):
      """
      Property target used to set the revision value.
      No validations.
      """
      self._revision = value

   def _getRevision(self):
      """
      Property target used to get the revision value.
      """
      return self._revision

   def _setDescription(self, value):
      """
      Property target used to set the description value.
      No validations.
      """
      self._description = value

   def _getDescription(self):
      """
      Property target used to get the description value.
      """
      return self._description

   def _setGenerator(self, value):
      """
      Property target used to set the generator value.
      No validations.
      """
      self._generator = value

   def _getGenerator(self):
      """
      Property target used to get the generator value.
      """
      return self._generator

   author = property(_getAuthor, _setAuthor, None, "Author of the configuration file.")
   revision = property(_getRevision, _setRevision, None, "Revision of the configuration file.")
   description = property(_getDescription, _setDescription, None, "Description of the configuration file.")
   generator = property(_getGenerator, _setGenerator, None, "Tool that generated the configuration file.")


########################################################################
# ExtensionsConfig class definition
########################################################################

class ExtensionsConfig(object):

   """
   Class representing Cedar Backup extensions configuration.

   Extensions configuration is used to specify "extended actions" implemented
   by code external to Cedar Backup.  For instance, a hypothetical third party
   might write extension code to collect Subversion repository data.  If they
   write a properly-formatted extension function, they can use the extension
   configuration to map a command-line Cedar Backup action (i.e. "subversion")
   to their function.
   
   As with all of the other classes that represent configuration sections, all
   of these values are optional.  It is up to some higher-level construct to
   decide whether everything they need is filled in.   Some validation is done
   on non-C{None} assignments through the use of the Python C{property()}
   construct.

   The following restrictions exist on data in this class:

      - The actions list must be a list of C{ExtendedAction} objects.

   @sort: __init__, __repr__, __str__, __cmp__, actions
   """

   def __init__(self, actions=None):
      """
      Constructor for the C{ExtensionsConfig} class.
      @param actions: List of extended actions
      """
      self._actions = None
      self.actions = actions

   def __repr__(self):
      """
      Official string representation for class instance.
      """
      return "ExtensionsConfig(%s)" % self.actions

   def __str__(self):
      """
      Informal string representation for class instance.
      """
      return self.__repr__()

   def __cmp__(self, other):
      """
      Definition of equals operator for this class.
      @param other: Other object to compare to.
      @return: -1/0/1 depending on whether self is C{<}, C{=} or C{>} other.
      """
      if other is None:
         return 1
      if self._actions != other._actions:
         if self._actions < other._actions:
            return -1
         else:
            return 1
      return 0

   def _setActions(self, value):
      """
      Property target used to set the actions list.
      Either the value must be C{None} or each element must be an C{ExtendedAction}.
      @raise ValueError: If the value is not a C{ExtendedAction}
      """
      if value is None:
         self._actions = None
      else:
         try:
            saved = self._actions
            self._actions = ObjectTypeList(ExtendedAction, "ExtendedAction")
            self._actions.extend(value)
         except Exception, e:
            self._actions = saved
            raise e

   def _getActions(self):
      """
      Property target used to get the actions list.
      """
      return self._actions

   actions = property(_getActions, _setActions, None, "List of extended actions.")


########################################################################
# OptionsConfig class definition
########################################################################

class OptionsConfig(object):

   """
   Class representing a Cedar Backup global options configuration.

   The options section is used to store global configuration options and
   defaults that can be applied to other sections. 

   As with all of the other classes that represent configuration sections, all
   of these values are optional.  It is up to some higher-level construct to
   decide whether everything they need is filled in.   Some validation is done
   on non-C{None} assignments through the use of the Python C{property()}
   construct.

   The following restrictions exist on data in this class:

      - The working directory must be an absolute path.  
      - The starting day must be a day of the week in English, i.e. C{"monday"}, C{"tuesday"}, etc.  
      - All of the other values must be non-empty strings if they are set to something other than C{None}.
      - The overrides list must be a list of C{CommandOverride} objects.

   @sort: __init__, __repr__, __str__, __cmp__, startingDay, workingDir, 
         backupUser, backupGroup, rcpCommand, overrides
   """

   def __init__(self, startingDay=None, workingDir=None, backupUser=None, 
                backupGroup=None, rcpCommand=None, overrides=None):
      """
      Constructor for the C{OptionsConfig} class.

      @param startingDay: Day that starts the week.
      @param workingDir: Working (temporary) directory to use for backups.
      @param backupUser: Effective user that backups should run as.
      @param backupGroup: Effective group that backups should run as.
      @param rcpCommand: Default rcp-compatible copy command for staging.
      @param overrides: List of configured command path overrides, if any.

      @raise ValueError: If one of the values is invalid.
      """
      self._startingDay = None
      self._workingDir = None
      self._backupUser = None
      self._backupGroup = None
      self._rcpCommand = None
      self._overrides = None
      self.startingDay = startingDay
      self.workingDir = workingDir
      self.backupUser = backupUser
      self.backupGroup = backupGroup
      self.rcpCommand = rcpCommand
      self.overrides = overrides

   def __repr__(self):
      """
      Official string representation for class instance.
      """
      return "OptionsConfig(%s, %s, %s, %s, %s, %s)" % (self.startingDay, self.workingDir, self.backupUser, 
                                                        self.backupGroup, self.rcpCommand, self.overrides)

   def __str__(self):
      """
      Informal string representation for class instance.
      """
      return self.__repr__()

   def __cmp__(self, other):
      """
      Definition of equals operator for this class.
      @param other: Other object to compare to.
      @return: -1/0/1 depending on whether self is C{<}, C{=} or C{>} other.
      """
      if other is None:
         return 1
      if self._startingDay != other._startingDay:
         if self._startingDay < other._startingDay:
            return -1
         else:
            return 1
      if self._workingDir != other._workingDir:
         if self._workingDir < other._workingDir:
            return -1
         else:
            return 1
      if self._backupUser != other._backupUser:
         if self._backupUser < other._backupUser:
            return -1
         else:
            return 1
      if self._backupGroup != other._backupGroup:
         if self._backupGroup < other._backupGroup:
            return -1
         else:
            return 1
      if self._rcpCommand != other._rcpCommand:
         if self._rcpCommand < other._rcpCommand:
            return -1
         else:
            return 1
      if self._overrides != other._overrides:
         if self._overrides < other._overrides:
            return -1
         else:
            return 1
      return 0

   def _setStartingDay(self, value):
      """
      Property target used to set the starting day.
      If it is not C{None}, the value must be a valid English day of the week,
      one of C{"monday"}, C{"tuesday"}, C{"wednesday"}, etc.
      @raise ValueError: If the value is not a valid day of the week.
      """
      if value is not None:
         if value not in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday", ]:
            raise ValueError("Starting day must be an English day of the week, i.e. \"monday\".")
      self._startingDay = value

   def _getStartingDay(self):
      """
      Property target used to get the starting day.
      """
      return self._startingDay

   def _setWorkingDir(self, value):
      """
      Property target used to set the working directory.
      The value must be an absolute path if it is not C{None}.
      It does not have to exist on disk at the time of assignment.
      @raise ValueError: If the value is not an absolute path.
      @raise ValueError: If the value cannot be encoded properly.
      """
      if value is not None:
         if not os.path.isabs(value):
            raise ValueError("Working directory must be an absolute path.")
      self._workingDir = encodePath(value)

   def _getWorkingDir(self):
      """
      Property target used to get the working directory.
      """
      return self._workingDir

   def _setBackupUser(self, value):
      """
      Property target used to set the backup user.
      The value must be a non-empty string if it is not C{None}.
      @raise ValueError: If the value is an empty string.
      """
      if value is not None:
         if len(value) < 1:
            raise ValueError("Backup user must be a non-empty string.")
      self._backupUser = value

   def _getBackupUser(self):
      """
      Property target used to get the backup user.
      """
      return self._backupUser

   def _setBackupGroup(self, value):
      """
      Property target used to set the backup group.
      The value must be a non-empty string if it is not C{None}.
      @raise ValueError: If the value is an empty string.
      """
      if value is not None:
         if len(value) < 1:
            raise ValueError("Backup group must be a non-empty string.")
      self._backupGroup = value

   def _getBackupGroup(self):
      """
      Property target used to get the backup group.
      """
      return self._backupGroup

   def _setRcpCommand(self, value):
      """
      Property target used to set the rcp command.
      The value must be a non-empty string if it is not C{None}.
      @raise ValueError: If the value is an empty string.
      """
      if value is not None:
         if len(value) < 1:
            raise ValueError("The rcp command must be a non-empty string.")
      self._rcpCommand = value

   def _getRcpCommand(self):
      """
      Property target used to get the rcp command.
      """
      return self._rcpCommand

   def _setOverrides(self, value):
      """
      Property target used to set the command path overrides list.
      Either the value must be C{None} or each element must be a C{CommandOverride}.
      @raise ValueError: If the value is not a C{CommandOverride}
      """
      if value is None:
         self._overrides = None
      else:
         try:
            saved = self._overrides
            self._overrides = ObjectTypeList(CommandOverride, "CommandOverride")
            self._overrides.extend(value)
         except Exception, e:
            self._overrides = saved
            raise e

   def _getOverrides(self):
      """
      Property target used to get the command path overrides list.
      """
      return self._overrides

   startingDay = property(_getStartingDay, _setStartingDay, None, "Day that starts the week.")
   workingDir = property(_getWorkingDir, _setWorkingDir, None, "Working (temporary) directory to use for backups.")
   backupUser = property(_getBackupUser, _setBackupUser, None, "Effective user that backups should run as.")
   backupGroup = property(_getBackupGroup, _setBackupGroup, None, "Effective group that backups should run as.")
   rcpCommand = property(_getRcpCommand, _setRcpCommand, None, "Default rcp-compatible copy command for staging.")
   overrides = property(_getOverrides, _setOverrides, None, "List of configured command path overrides, if any.")


########################################################################
# CollectConfig class definition
########################################################################

class CollectConfig(object):

   """
   Class representing a Cedar Backup collect configuration.

   As with all of the other classes that represent configuration sections, all
   of these values are optional.  It is up to some higher-level construct to
   decide whether everything they need is filled in.   Some validation is done
   on non-C{None} assignments through the use of the Python C{property()}
   construct.

   The following restrictions exist on data in this class:

      - The target directory must be an absolute path.
      - The collect mode must be one of the values in L{VALID_COLLECT_MODES}.
      - The archive mode must be one of the values in L{VALID_ARCHIVE_MODES}.
      - The ignore file must be a non-empty string.
      - Each of the paths in C{absoluteExcludePaths} must be an absolute path
      - The collect directory list must be a list of C{CollectDir} objects.

   For the C{absoluteExcludePaths} list, validation is accomplished through the
   L{util.AbsolutePathList} list implementation that overrides common list
   methods and transparently does the absolute path validation for us.

   For the C{collectDirs} list, validation is accomplished through the
   L{util.ObjectTypeList} list implementation that overrides common list
   methods and transparently ensures that each element is a C{CollectDir}.

   @note: Lists within this class are "unordered" for equality comparisons.

   @sort: __init__, __repr__, __str__, __cmp__, targetDir, 
          collectMode, archiveMode, ignoreFile, absoluteExcludePaths, 
          excludePatterns, collectDirs
   """

   def __init__(self, targetDir=None, collectMode=None, archiveMode=None, ignoreFile=None,
                absoluteExcludePaths=None, excludePatterns=None, collectDirs=None):
      """
      Constructor for the C{CollectConfig} class.

      @param targetDir: Directory to collect files into.
      @param collectMode: Default collect mode.
      @param archiveMode: Default archive mode for collect files.
      @param ignoreFile: Default ignore file name.
      @param absoluteExcludePaths: List of absolute paths to exclude.
      @param excludePatterns: List of regular expression patterns to exclude.
      @param collectDirs: List of collect directories.

      @raise ValueError: If one of the values is invalid.
      """
      self._targetDir = None
      self._collectMode = None
      self._archiveMode = None
      self._ignoreFile = None
      self._absoluteExcludePaths = None
      self._excludePatterns = None
      self._collectDirs = None
      self.targetDir = targetDir
      self.collectMode = collectMode
      self.archiveMode = archiveMode
      self.ignoreFile = ignoreFile
      self.absoluteExcludePaths = absoluteExcludePaths
      self.excludePatterns = excludePatterns
      self.collectDirs = collectDirs

   def __repr__(self):
      """
      Official string representation for class instance.
      """
      return "CollectConfig(%s, %s, %s, %s, %s, %s, %s)" % (self.targetDir, self.collectMode, self.archiveMode, 
                                                            self.ignoreFile, self.absoluteExcludePaths,
                                                            self.excludePatterns, self.collectDirs)

   def __str__(self):
      """
      Informal string representation for class instance.
      """
      return self.__repr__()

   def __cmp__(self, other):
      """
      Definition of equals operator for this class.
      Lists within this class are "unordered" for equality comparisons.
      @param other: Other object to compare to.
      @return: -1/0/1 depending on whether self is C{<}, C{=} or C{>} other.
      """
      if other is None:
         return 1
      if self._targetDir != other._targetDir:
         if self._targetDir < other._targetDir:
            return -1
         else:
            return 1
      if self._collectMode != other._collectMode:
         if self._collectMode < other._collectMode:
            return -1
         else:
            return 1
      if self._archiveMode != other._archiveMode:
         if self._archiveMode < other._archiveMode:
            return -1
         else:
            return 1
      if self._ignoreFile != other._ignoreFile:
         if self._ignoreFile < other._ignoreFile:
            return -1
         else:
            return 1
      if self._absoluteExcludePaths != other._absoluteExcludePaths:
         if self._absoluteExcludePaths < other._absoluteExcludePaths:
            return -1
         else:
            return 1
      if self._excludePatterns != other._excludePatterns:
         if self._excludePatterns < other._excludePatterns:
            return -1
         else:
            return 1
      if self._collectDirs != other._collectDirs:
         if self._collectDirs < other._collectDirs:
            return -1
         else:
            return 1
      return 0

   def _setTargetDir(self, value):
      """
      Property target used to set the target directory.
      The value must be an absolute path if it is not C{None}.
      It does not have to exist on disk at the time of assignment.
      @raise ValueError: If the value is not an absolute path.
      @raise ValueError: If the value cannot be encoded properly.
      """
      if value is not None:
         if not os.path.isabs(value):
            raise ValueError("Target directory must be an absolute path.")
      self._targetDir = encodePath(value)

   def _getTargetDir(self):
      """
      Property target used to get the target directory.
      """
      return self._targetDir

   def _setCollectMode(self, value):
      """
      Property target used to set the collect mode.
      If not C{None}, the mode must be one of L{VALID_COLLECT_MODES}.
      @raise ValueError: If the value is not valid.
      """
      if value is not None:
         if value not in VALID_COLLECT_MODES:
            raise ValueError("Collect mode must be one of %s." % VALID_COLLECT_MODES)
      self._collectMode = value

   def _getCollectMode(self):
      """
      Property target used to get the collect mode.
      """
      return self._collectMode

   def _setArchiveMode(self, value):
      """
      Property target used to set the archive mode.
      If not C{None}, the mode must be one of L{VALID_ARCHIVE_MODES}.
      @raise ValueError: If the value is not valid.
      """
      if value is not None:
         if value not in VALID_ARCHIVE_MODES:
            raise ValueError("Archive mode must be one of %s." % VALID_ARCHIVE_MODES)
      self._archiveMode = value

   def _getArchiveMode(self):
      """
      Property target used to get the archive mode.
      """
      return self._archiveMode

   def _setIgnoreFile(self, value):
      """
      Property target used to set the ignore file.
      The value must be a non-empty string if it is not C{None}.
      @raise ValueError: If the value is an empty string.
      @raise ValueError: If the value cannot be encoded properly.
      """
      if value is not None:
         if len(value) < 1:
            raise ValueError("The ignore file must be a non-empty string.")
      self._ignoreFile = encodePath(value)

   def _getIgnoreFile(self):
      """
      Property target used to get the ignore file.
      """
      return self._ignoreFile

   def _setAbsoluteExcludePaths(self, value):
      """
      Property target used to set the absolute exclude paths list.
      Either the value must be C{None} or each element must be an absolute path.
      Elements do not have to exist on disk at the time of assignment.
      @raise ValueError: If the value is not an absolute path.
      """
      if value is None:
         self._absoluteExcludePaths = None
      else:
         try:
            saved = self._absoluteExcludePaths
            self._absoluteExcludePaths = AbsolutePathList()
            self._absoluteExcludePaths.extend(value)
         except Exception, e:
            self._absoluteExcludePaths = saved
            raise e

   def _getAbsoluteExcludePaths(self):
      """
      Property target used to get the absolute exclude paths list.
      """
      return self._absoluteExcludePaths

   def _setExcludePatterns(self, value):
      """
      Property target used to set the exclude patterns list.
      """
      if value is None:
         self._excludePatterns = None
      else:
         try:
            saved = self._excludePatterns
            self._excludePatterns = UnorderedList()
            self._excludePatterns.extend(value)
         except Exception, e:
            self._excludePatterns = saved
            raise e

   def _getExcludePatterns(self):
      """
      Property target used to get the exclude patterns list.
      """
      return self._excludePatterns

   def _setCollectDirs(self, value):
      """
      Property target used to set the collect dirs list.
      Either the value must be C{None} or each element must be a C{CollectDir}.
      @raise ValueError: If the value is not a C{CollectDir}
      """
      if value is None:
         self._collectDirs = None
      else:
         try:
            saved = self._collectDirs
            self._collectDirs = ObjectTypeList(CollectDir, "CollectDir")
            self._collectDirs.extend(value)
         except Exception, e:
            self._collectDirs = saved
            raise e

   def _getCollectDirs(self):
      """
      Property target used to get the collect dirs list.
      """
      return self._collectDirs

   targetDir = property(_getTargetDir, _setTargetDir, None, "Directory to collect files into.")
   collectMode = property(_getCollectMode, _setCollectMode, None, "Default collect mode.")
   archiveMode = property(_getArchiveMode, _setArchiveMode, None, "Default archive mode for collect files.")
   ignoreFile = property(_getIgnoreFile, _setIgnoreFile, None, "Default ignore file name.")
   absoluteExcludePaths = property(_getAbsoluteExcludePaths, _setAbsoluteExcludePaths, None, "List of absolute paths to exclude.")
   excludePatterns = property(_getExcludePatterns, _setExcludePatterns, None, "List of regular expressions patterns to exclude.")
   collectDirs = property(_getCollectDirs, _setCollectDirs, None, "List of collect directories.")


########################################################################
# StageConfig class definition
########################################################################

class StageConfig(object):

   """
   Class representing a Cedar Backup stage configuration.

   As with all of the other classes that represent configuration sections, all
   of these values are optional.  It is up to some higher-level construct to
   decide whether everything they need is filled in.   Some validation is done
   on non-C{None} assignments through the use of the Python C{property()}
   construct.

   The following restrictions exist on data in this class:

      - The target directory must be an absolute path
      - The list of local peers must contain only C{LocalPeer} objects
      - The list of remote peers must contain only C{RemotePeer} objects

   @note: Lists within this class are "unordered" for equality comparisons.

   @sort: __init__, __repr__, __str__, __cmp__, targetDir, localPeers, remotePeers
   """

   def __init__(self, targetDir=None, localPeers=None, remotePeers=None):
      """
      Constructor for the C{StageConfig} class.

      @param targetDir: Directory to stage files into, by peer name.
      @param localPeers: List of local peers.
      @param remotePeers: List of remote peers.

      @raise ValueError: If one of the values is invalid.
      """
      self._targetDir = None
      self._localPeers = None
      self._remotePeers = None
      self.targetDir = targetDir
      self.localPeers = localPeers
      self.remotePeers = remotePeers

   def __repr__(self):
      """
      Official string representation for class instance.
      """
      return "StageConfig(%s, %s, %s)" % (self.targetDir, self.localPeers, self.remotePeers)

   def __str__(self):
      """
      Informal string representation for class instance.
      """
      return self.__repr__()

   def __cmp__(self, other):
      """
      Definition of equals operator for this class.
      Lists within this class are "unordered" for equality comparisons.
      @param other: Other object to compare to.
      @return: -1/0/1 depending on whether self is C{<}, C{=} or C{>} other.
      """
      if other is None:
         return 1
      if self._targetDir != other._targetDir:
         if self._targetDir < other._targetDir:
            return -1
         else:
            return 1
      if self._localPeers != other._localPeers:
         if self._localPeers < other._localPeers:
            return -1
         else:
            return 1
      if self._remotePeers != other._remotePeers:
         if self._remotePeers < other._remotePeers:
            return -1
         else:
            return 1
      return 0

   def _setTargetDir(self, value):
      """
      Property target used to set the target directory.
      The value must be an absolute path if it is not C{None}.
      It does not have to exist on disk at the time of assignment.
      @raise ValueError: If the value is not an absolute path.
      @raise ValueError: If the value cannot be encoded properly.
      """
      if value is not None:
         if not os.path.isabs(value):
            raise ValueError("Target directory must be an absolute path.")
      self._targetDir = encodePath(value)

   def _getTargetDir(self):
      """
      Property target used to get the target directory.
      """
      return self._targetDir

   def _setLocalPeers(self, value):
      """
      Property target used to set the local peers list.
      Either the value must be C{None} or each element must be a C{LocalPeer}.
      @raise ValueError: If the value is not an absolute path.
      """
      if value is None:
         self._localPeers = None
      else:
         try:
            saved = self._localPeers
            self._localPeers = ObjectTypeList(LocalPeer, "LocalPeer")
            self._localPeers.extend(value)
         except Exception, e:
            self._localPeers = saved
            raise e

   def _getLocalPeers(self):
      """
      Property target used to get the local peers list.
      """
      return self._localPeers

   def _setRemotePeers(self, value):
      """
      Property target used to set the remote peers list.
      Either the value must be C{None} or each element must be a C{RemotePeer}.
      @raise ValueError: If the value is not a C{RemotePeer}
      """
      if value is None:
         self._remotePeers = None
      else:
         try:
            saved = self._remotePeers
            self._remotePeers = ObjectTypeList(RemotePeer, "RemotePeer")
            self._remotePeers.extend(value)
         except Exception, e:
            self._remotePeers = saved
            raise e

   def _getRemotePeers(self):
      """
      Property target used to get the remote peers list.
      """
      return self._remotePeers

   targetDir = property(_getTargetDir, _setTargetDir, None, "Directory to stage files into, by peer name.")
   localPeers = property(_getLocalPeers, _setLocalPeers, None, "List of local peers.")
   remotePeers = property(_getRemotePeers, _setRemotePeers, None, "List of remote peers.")


########################################################################
# StoreConfig class definition
########################################################################

class StoreConfig(object):

   """
   Class representing a Cedar Backup store configuration.

   As with all of the other classes that represent configuration sections, all
   of these values are optional.  It is up to some higher-level construct to
   decide whether everything they need is filled in.   Some validation is done
   on non-C{None} assignments through the use of the Python C{property()}
   construct.

   The following restrictions exist on data in this class:

      - The source directory must be an absolute path.
      - The media type must be one of the values in L{VALID_MEDIA_TYPES}.
      - The device type must be one of the values in L{VALID_DEVICE_TYPES}.
      - The device path must be an absolute path.
      - The SCSI id must be in the form specified by L{writer.validateScsiId}.
      - The drive speed must be an integer >= 1

   The device type field mostly exists for planned future extensions, such as
   support for DVD writers.

   @sort: __init__, __repr__, __str__, __cmp__, sourceDir, 
          mediaType, deviceType, devicePath, deviceScsiId, 
          driveSpeed, checkData, warnMidnite
   """

   def __init__(self, sourceDir=None, mediaType=None, deviceType=None, 
                devicePath=None, deviceScsiId=None, driveSpeed=None,
                checkData=False, warnMidnite=False):
      """
      Constructor for the C{StoreConfig} class.

      @param sourceDir: Directory whose contents should be written to media.
      @param mediaType: Type of the media (see notes above).
      @param deviceType: Type of the device (optional, see notes above).
      @param devicePath: Filesystem device name for writer device, i.e. C{/dev/cdrw}.
      @param deviceScsiId: SCSI id for writer device, i.e. C{[ATA|ATAPI]:scsibus,target,lun}.
      @param driveSpeed: Speed of the drive, i.e. C{2} for 2x drive, etc.
      @param checkData: Whether resulting image should be validated.
      @param warnMidnite: Whether to generate warnings for crossing midnite.

      @raise ValueError: If one of the values is invalid.
      """
      self._sourceDir = None
      self._mediaType = None
      self._deviceType = None
      self._devicePath = None
      self._deviceScsiId = None
      self._driveSpeed = None
      self._checkData = None
      self._warnMidnite = None
      self.sourceDir = sourceDir
      self.mediaType = mediaType
      self.deviceType = deviceType
      self.devicePath = devicePath
      self.deviceScsiId = deviceScsiId
      self.driveSpeed = driveSpeed
      self.checkData = checkData
      self.warnMidnite = warnMidnite

   def __repr__(self):
      """
      Official string representation for class instance.
      """
      return "StoreConfig(%s, %s, %s, %s, %s, %s, %s, %s)" % (self.sourceDir, self.mediaType, self.deviceType,
                                                              self.devicePath, self.deviceScsiId, self.driveSpeed,
                                                              self.checkData, self.warnMidnite)

   def __str__(self):
      """
      Informal string representation for class instance.
      """
      return self.__repr__()

   def __cmp__(self, other):
      """
      Definition of equals operator for this class.
      @param other: Other object to compare to.
      @return: -1/0/1 depending on whether self is C{<}, C{=} or C{>} other.
      """
      if other is None:
         return 1
      if self._sourceDir != other._sourceDir:
         if self._sourceDir < other._sourceDir:
            return -1
         else:
            return 1
      if self._mediaType != other._mediaType:
         if self._mediaType < other._mediaType:
            return -1
         else:
            return 1
      if self._deviceType != other._deviceType:
         if self._deviceType < other._deviceType:
            return -1
         else:
            return 1
      if self._devicePath != other._devicePath:
         if self._devicePath < other._devicePath:
            return -1
         else:
            return 1
      if self._deviceScsiId != other._deviceScsiId:
         if self._deviceScsiId < other._deviceScsiId:
            return -1
         else:
            return 1
      if self._driveSpeed != other._driveSpeed:
         if self._driveSpeed < other._driveSpeed:
            return -1
         else:
            return 1
      if self._checkData != other._checkData:
         if self._checkData < other._checkData:
            return -1
         else:
            return 1
      if self._warnMidnite != other._warnMidnite:
         if self._warnMidnite < other._warnMidnite:
            return -1
         else:
            return 1
      return 0

   def _setSourceDir(self, value):
      """
      Property target used to set the source directory.
      The value must be an absolute path if it is not C{None}.
      It does not have to exist on disk at the time of assignment.
      @raise ValueError: If the value is not an absolute path.
      @raise ValueError: If the value cannot be encoded properly.
      """
      if value is not None:
         if not os.path.isabs(value):
            raise ValueError("Source directory must be an absolute path.")
      self._sourceDir = encodePath(value)

   def _getSourceDir(self):
      """
      Property target used to get the source directory.
      """
      return self._sourceDir

   def _setMediaType(self, value):
      """
      Property target used to set the media type.
      The value must be one of L{VALID_MEDIA_TYPES}.
      @raise ValueError: If the value is not valid.
      """
      if value is not None:
         if value not in VALID_MEDIA_TYPES:
            raise ValueError("Media type must be one of %s." % VALID_MEDIA_TYPES)
      self._mediaType = value

   def _getMediaType(self):
      """
      Property target used to get the media type.
      """
      return self._mediaType

   def _setDeviceType(self, value):
      """
      Property target used to set the device type.
      The value must be one of L{VALID_DEVICE_TYPES}.
      This field mostly exists to support future functionality.
      @raise ValueError: If the value is not valid.
      """
      if value is not None:
         if value not in VALID_DEVICE_TYPES:
            raise ValueError("Device type must be one of %s." % VALID_DEVICE_TYPES)
      self._deviceType = value

   def _getDeviceType(self):
      """
      Property target used to get the device type.
      """
      return self._deviceType

   def _setDevicePath(self, value):
      """
      Property target used to set the device path.
      The value must be an absolute path if it is not C{None}.
      It does not have to exist on disk at the time of assignment.
      @raise ValueError: If the value is not an absolute path.
      @raise ValueError: If the value cannot be encoded properly.
      """
      if value is not None:
         if not os.path.isabs(value):
            raise ValueError("Device path must be an absolute path.")
      self._devicePath = encodePath(value)

   def _getDevicePath(self):
      """
      Property target used to get the device path.
      """
      return self._devicePath

   def _setDeviceScsiId(self, value):
      """
      Property target used to set the SCSI id
      The SCSI id must be valid per L{writer.validateScsiId}.
      @raise ValueError: If the value is not valid.
      """
      if value is None:
         self._deviceScsiId = None
      else:
         self._deviceScsiId = validateScsiId(value)

   def _getDeviceScsiId(self):
      """
      Property target used to get the SCSI id.
      """
      return self._deviceScsiId

   def _setDriveSpeed(self, value):
      """
      Property target used to set the drive speed.
      The drive speed must be valid per L{writer.validateDriveSpeed}.
      @raise ValueError: If the value is not valid.
      """
      self._driveSpeed = validateDriveSpeed(value)

   def _getDriveSpeed(self):
      """
      Property target used to get the drive speed.
      """
      return self._driveSpeed

   def _setCheckData(self, value):
      """
      Property target used to set the check data flag.
      No validations, but we normalize the value to C{True} or C{False}.
      """
      if value:
         self._checkData = True
      else:
         self._checkData = False

   def _getCheckData(self):
      """
      Property target used to get the check data flag.
      """
      return self._checkData

   def _setWarnMidnite(self, value):
      """
      Property target used to set the midnite warning flag.
      No validations, but we normalize the value to C{True} or C{False}.
      """
      if value:
         self._warnMidnite = True
      else:
         self._warnMidnite = False

   def _getWarnMidnite(self):
      """
      Property target used to get the midnite warning flag.
      """
      return self._warnMidnite

   sourceDir = property(_getSourceDir, _setSourceDir, None, "Directory whose contents should be written to media.")
   mediaType = property(_getMediaType, _setMediaType, None, "Type of the media (see notes above).")
   deviceType = property(_getDeviceType, _setDeviceType, None, "Type of the device (optional, see notes above).")
   devicePath = property(_getDevicePath, _setDevicePath, None, "Filesystem device name for writer device.")
   deviceScsiId = property(_getDeviceScsiId, _setDeviceScsiId, None, "SCSI id for writer device.")
   driveSpeed = property(_getDriveSpeed, _setDriveSpeed, None, "Speed of the drive.")
   checkData = property(_getCheckData, _setCheckData, None, "Whether resulting image should be validated.")
   warnMidnite = property(_getWarnMidnite, _setWarnMidnite, None, "Whether to generate warnings for crossing midnite.")


########################################################################
# PurgeConfig class definition
########################################################################

class PurgeConfig(object):

   """
   Class representing a Cedar Backup purge configuration.

   As with all of the other classes that represent configuration sections, all
   of these values are optional.  It is up to some higher-level construct to
   decide whether everything they need is filled in.   Some validation is done
   on non-C{None} assignments through the use of the Python C{property()}
   construct.

   The following restrictions exist on data in this class:

      - The purge directory list must be a list of C{PurgeDir} objects.

   For the C{purgeDirs} list, validation is accomplished through the
   L{util.ObjectTypeList} list implementation that overrides common list
   methods and transparently ensures that each element is a C{PurgeDir}.

   @note: Lists within this class are "unordered" for equality comparisons.

   @sort: __init__, __repr__, __str__, __cmp__, purgeDirs
   """

   def __init__(self, purgeDirs=None):
      """
      Constructor for the C{Purge} class.
      @param purgeDirs: List of purge directories.
      @raise ValueError: If one of the values is invalid.
      """
      self._purgeDirs = None
      self.purgeDirs = purgeDirs

   def __repr__(self):
      """
      Official string representation for class instance.
      """
      return "PurgeConfig(%s)" % self.purgeDirs

   def __str__(self):
      """
      Informal string representation for class instance.
      """
      return self.__repr__()

   def __cmp__(self, other):
      """
      Definition of equals operator for this class.
      Lists within this class are "unordered" for equality comparisons.
      @param other: Other object to compare to.
      @return: -1/0/1 depending on whether self is C{<}, C{=} or C{>} other.
      """
      if other is None:
         return 1
      if self._purgeDirs != other._purgeDirs:
         if self._purgeDirs < other._purgeDirs:
            return -1
         else:
            return 1
      return 0

   def _setPurgeDirs(self, value):
      """
      Property target used to set the purge dirs list.
      Either the value must be C{None} or each element must be a C{PurgeDir}.
      @raise ValueError: If the value is not a C{PurgeDir}
      """
      if value is None:
         self._purgeDirs = None
      else:
         try:
            saved = self._purgeDirs
            self._purgeDirs = ObjectTypeList(PurgeDir, "PurgeDir")
            self._purgeDirs.extend(value)
         except Exception, e:
            self._purgeDirs = saved
            raise e

   def _getPurgeDirs(self):
      """
      Property target used to get the purge dirs list.
      """
      return self._purgeDirs

   purgeDirs = property(_getPurgeDirs, _setPurgeDirs, None, "List of directories to purge.")


########################################################################
# Config class definition
########################################################################

class Config(object):

   ######################
   # Class documentation
   ######################

   """
   Class representing a Cedar Backup XML configuration document.

   The C{Config} class is a Python object representation of a Cedar Backup XML
   configuration file.  It is intended to be the only Python-language interface
   to Cedar Backup configuration on disk for both Cedar Backup itself and for
   external applications.

   The object representation is two-way: XML data can be used to create a
   C{Config} object, and then changes to the object can be propogated back to
   disk.  A C{Config} object can even be used to create a configuration file
   from scratch programmatically.
   
   This class and the classes it is composed from often use Python's
   C{property} construct to validate input and limit access to values.  Some
   validations can only be done once a document is considered "complete"
   (see module notes for more details).  

   Assignments to the various instance variables must match the expected
   type, i.e. C{reference} must be a C{ReferenceConfig}.  The internal check
   uses the built-in C{isinstance} function, so it should be OK to use
   subclasses if you want to.  

   If an instance variable is not set, its value will be C{None}.  When an
   object is initialized without using an XML document, all of the values
   will be C{None}.  Even when an object is initialized using XML, some of
   the values might be C{None} because not every section is required.

   @note: Lists within this class are "unordered" for equality comparisons.

   @sort: __init__, __repr__, __str__, __cmp__, extractXml, validate, 
          reference, extensions, options, collect, stage, store, purge,
          _getReference, _setReference, _getExtensions, _setExtensions, 
          _getOptions, _setOptions, _getCollect, _setCollect, _getStage, 
          _setStage, _getStore, _setStore, _getPurge, _setPurge
   """

   ##############
   # Constructor
   ##############

   def __init__(self, xmlData=None, xmlPath=None, validate=True):
      """
      Initializes a configuration object.

      If you initialize the object without passing either C{xmlData} or
      C{xmlPath}, then configuration will be empty and will be invalid until it
      is filled in properly.

      No reference to the original XML data or original path is saved off by
      this class.  Once the data has been parsed (successfully or not) this
      original information is discarded.

      Unless the C{validate} argument is C{False}, the L{Config.validate}
      method will be called (with its default arguments) against configuration
      after successfully parsing any passed-in XML.  Keep in mind that even if
      C{validate} is C{False}, it might not be possible to parse the passed-in
      XML document if lower-level validations fail.

      @note: It is strongly suggested that the C{validate} option always be set
      to C{True} (the default) unless there is a specific need to read in
      invalid configuration from disk.  

      @param xmlData: XML data representing configuration.
      @type xmlData: String data.

      @param xmlPath: Path to an XML file on disk.
      @type xmlPath: Absolute path to a file on disk.

      @param validate: Validate the document after parsing it.
      @type validate: Boolean true/false.

      @raise ValueError: If both C{xmlData} and C{xmlPath} are passed-in.
      @raise ValueError: If the XML data in C{xmlData} or C{xmlPath} cannot be parsed.
      @raise ValueError: If the parsed configuration document is not valid.
      """
      self._reference = None
      self._extensions = None
      self._options = None
      self._collect = None
      self._stage = None
      self._store = None
      self._purge = None
      self.reference = None
      self.extensions = None
      self.options = None
      self.collect = None
      self.stage = None
      self.store = None
      self.purge = None
      if xmlData is not None and xmlPath is not None:
         raise ValueError("Use either xmlData or xmlPath, but not both.")
      if xmlData is not None:
         self._parseXmlData(xmlData)
         if validate:
            self.validate()
      elif xmlPath is not None:
         xmlData = open(xmlPath).read()
         self._parseXmlData(xmlData)
         if validate:
            self.validate()


   #########################
   # String representations
   #########################

   def __repr__(self):
      """
      Official string representation for class instance.
      """
      return "Config(%s, %s, %s, %s, %s, %s, %s)" % (self.reference, self.extensions, self.options, 
                                                     self.collect, self.stage, self.store, self.purge)

   def __str__(self):
      """
      Informal string representation for class instance.
      """
      return self.__repr__()


   #############################
   # Standard comparison method
   #############################

   def __cmp__(self, other):
      """
      Definition of equals operator for this class.
      Lists within this class are "unordered" for equality comparisons.
      @param other: Other object to compare to.
      @return: -1/0/1 depending on whether self is C{<}, C{=} or C{>} other.
      """
      if other is None:
         return 1
      if self._reference != other._reference:
         if self._reference < other._reference:
            return -1
         else:
            return 1
      if self._extensions != other._extensions:
         if self._extensions < other._extensions:
            return -1
         else:
            return 1
      if self._options != other._options:
         if self._options < other._options:
            return -1
         else:
            return 1
      if self._collect != other._collect:
         if self._collect < other._collect:
            return -1
         else:
            return 1
      if self._stage != other._stage:
         if self._stage < other._stage:
            return -1
         else:
            return 1
      if self._store != other._store:
         if self._store < other._store:
            return -1
         else:
            return 1
      if self._purge != other._purge:
         if self._purge < other._purge:
            return -1
         else:
            return 1
      return 0


   #############
   # Properties
   #############

   def _setReference(self, value):
      """
      Property target used to set the reference configuration value.
      If not C{None}, the value must be a C{ReferenceConfig} object.
      @raise ValueError: If the value is not a C{ReferenceConfig}
      """
      if value is None:
         self._reference = None
      else:
         if not isinstance(value, ReferenceConfig):
            raise ValueError("Value must be a C{ReferenceConfig} object.")
         self._reference = value

   def _getReference(self):
      """
      Property target used to get the reference configuration value.
      """
      return self._reference

   def _setExtensions(self, value):
      """
      Property target used to set the extensions configuration value.
      If not C{None}, the value must be a C{ExtensionsConfig} object.
      @raise ValueError: If the value is not a C{ExtensionsConfig}
      """
      if value is None:
         self._extensions = None
      else:
         if not isinstance(value, ExtensionsConfig):
            raise ValueError("Value must be a C{ExtensionsConfig} object.")
         self._extensions = value

   def _getExtensions(self):
      """
      Property target used to get the extensions configuration value.
      """
      return self._extensions

   def _setOptions(self, value):
      """
      Property target used to set the options configuration value.
      If not C{None}, the value must be a C{OptionsConfig} object.
      @raise ValueError: If the value is not a C{OptionsConfig}
      """
      if value is None:
         self._options = None
      else:
         if not isinstance(value, OptionsConfig):
            raise ValueError("Value must be a C{OptionsConfig} object.")
         self._options = value

   def _getOptions(self):
      """
      Property target used to get the options configuration value.
      """
      return self._options

   def _setCollect(self, value):
      """
      Property target used to set the collect configuration value.
      If not C{None}, the value must be a C{CollectConfig} object.
      @raise ValueError: If the value is not a C{CollectConfig}
      """
      if value is None:
         self._collect = None
      else:
         if not isinstance(value, CollectConfig):
            raise ValueError("Value must be a C{CollectConfig} object.")
         self._collect = value

   def _getCollect(self):
      """
      Property target used to get the collect configuration value.
      """
      return self._collect

   def _setStage(self, value):
      """
      Property target used to set the stage configuration value.
      If not C{None}, the value must be a C{StageConfig} object.
      @raise ValueError: If the value is not a C{StageConfig}
      """
      if value is None:
         self._stage = None
      else:
         if not isinstance(value, StageConfig):
            raise ValueError("Value must be a C{StageConfig} object.")
         self._stage = value

   def _getStage(self):
      """
      Property target used to get the stage configuration value.
      """
      return self._stage

   def _setStore(self, value):
      """
      Property target used to set the store configuration value.
      If not C{None}, the value must be a C{StoreConfig} object.
      @raise ValueError: If the value is not a C{StoreConfig}
      """
      if value is None:
         self._store = None
      else:
         if not isinstance(value, StoreConfig):
            raise ValueError("Value must be a C{StoreConfig} object.")
         self._store = value

   def _getStore(self):
      """
      Property target used to get the store configuration value.
      """
      return self._store

   def _setPurge(self, value):
      """
      Property target used to set the purge configuration value.
      If not C{None}, the value must be a C{PurgeConfig} object.
      @raise ValueError: If the value is not a C{PurgeConfig}
      """
      if value is None:
         self._purge = None
      else:
         if not isinstance(value, PurgeConfig):
            raise ValueError("Value must be a C{PurgeConfig} object.")
         self._purge = value

   def _getPurge(self):
      """
      Property target used to get the purge configuration value.
      """
      return self._purge

   reference = property(_getReference, _setReference, None, "Reference configuration in terms of a C{ReferenceConfig} object.")
   extensions = property(_getExtensions, _setExtensions, None, "Extensions configuration in terms of a C{ExtensionsConfig} object.")
   options = property(_getOptions, _setOptions, None, "Options configuration in terms of a C{OptionsConfig} object.")
   collect = property(_getCollect, _setCollect, None, "Collect configuration in terms of a C{CollectConfig} object.")
   stage = property(_getStage, _setStage, None, "Stage configuration in terms of a C{StageConfig} object.")
   store = property(_getStore, _setStore, None, "Store configuration in terms of a C{StoreConfig} object.")
   purge = property(_getPurge, _setPurge, None, "Purge configuration in terms of a C{PurgeConfig} object.")


   #################
   # Public methods
   #################

   def extractXml(self, xmlPath=None, validate=True):
      """
      Extracts configuration into an XML document.

      If C{xmlPath} is not provided, then the XML document will be returned as
      a string.  If C{xmlPath} is provided, then the XML document will be written
      to the file and C{None} will be returned.

      Unless the C{validate} parameter is C{False}, the L{Config.validate}
      method will be called (with its default arguments) against the
      configuration before extracting the XML.  If configuration is not valid,
      then an XML document will not be extracted.
   
      @note: This function is not particularly fast.  This is most noticable
      when running the regression tests, where the 30 or so extract-related
      tests take nearly 6 seconds on my Duron 850 (over half the total
      config-related test time).  However, I think the performance is adequate
      for our purposes.

      @note: It is strongly suggested that the C{validate} option always be set
      to C{True} (the default) unless there is a specific need to write an
      invalid configuration file to disk.

      @param xmlPath: Path to an XML file to create on disk.
      @type xmlPath: Absolute path to a file.

      @param validate: Validate the document before extracting it.
      @type validate: Boolean true/false.

      @return: XML string data or C{None} as described above.

      @raise ValueError: If configuration within the object is not valid.
      @raise IOError: If there is an error writing to the file.
      @raise OSError: If there is an error writing to the file.
      """
      if validate:
         self.validate()
      xmlData = self._extractXml()
      if xmlPath is not None:
         open(xmlPath, "w").write(xmlData)
         return None
      else:
         return xmlData

   def validate(self, requireOneAction=True, requireReference=False, requireExtensions=False, requireOptions=True, 
                requireCollect=False, requireStage=False, requireStore=False, requirePurge=False):
      """
      Validates configuration represented by the object.

      This method encapsulates all of the validations that should apply to a
      fully "complete" document but are not already taken care of by earlier
      validations.  It also provides some extra convenience functionality which
      might be useful to some people.  The process of validation is laid out in
      the I{Validation} section in the class notes (above).

      @param requireOneAction: Require at least one of the collect, stage, store or purge sections.
      @param requireReference: Require the reference section.
      @param requireExtensions: Require the extensions section.
      @param requireOptions: Require the options section.
      @param requireCollect: Require the collect section.
      @param requireStage: Require the stage section.
      @param requireStore: Require the store section.
      @param requirePurge: Require the purge section.

      @raise ValueError: If one of the validations fails.
      """
      if requireOneAction and (self.collect, self.stage, self.store, self.purge) == (None, None, None, None):
         raise ValueError("At least one of the collect, stage, store and purge sections is required.")
      if requireReference and self.reference is None:
         raise ValueError("The reference is section is required.")
      if requireExtensions and self.extensions is None:
         raise ValueError("The extensions is section is required.")
      if requireOptions and self.options is None:
         raise ValueError("The options is section is required.")
      if requireCollect and self.collect is None:
         raise ValueError("The collect is section is required.")
      if requireStage and self.stage is None:
         raise ValueError("The stage is section is required.")
      if requireStore and self.store is None:
         raise ValueError("The store is section is required.")
      if requirePurge and self.purge is None:
         raise ValueError("The purge is section is required.")
      self._validateContents()


   #####################################
   # High-level methods for parsing XML
   #####################################

   def _parseXmlData(self, xmlData):
      """
      Internal method to parse an XML string into the object.

      This method parses the XML document into a DOM tree (C{xmlDom}) and then
      calls individual static methods to parse each of the individual
      configuration sections.

      Most of the validation we do here has to do with whether the document can
      be parsed and whether any values which exist are valid.  We don't do much
      validation as to whether required elements actually exist unless we have
      to to make sense of the document (instead, that's the job of the
      L{validate} method).

      @note: This function is not particularly fast.  This is most noticable
      when running the regression tests, where the 30 or so parse- related
      tests take nearly 5 seconds on my Duron 850 (nearly half the total
      config-related test time).  However, I think the performance is adequate
      for our purposes.

      @param xmlData: XML data to be parsed
      @type xmlData: String data

      @raise ValueError: If the XML cannot be successfully parsed.
      """
      try:
         xmlDom = PyExpat.Reader().fromString(xmlData)
         parent = readFirstChild(xmlDom, "cb_config")
         self._reference = Config._parseReference(parent)
         self._extensions = Config._parseExtensions(parent)
         self._options = Config._parseOptions(parent)
         self._collect = Config._parseCollect(parent)
         self._stage = Config._parseStage(parent)
         self._store = Config._parseStore(parent)
         self._purge = Config._parsePurge(parent)
      except (IOError, ExpatError), e:
         raise ValueError("Unable to parse XML document: %s" % e)

   def _parseReference(parent):
      """
      Parses a reference configuration section.
      
      We read the following fields::

         author         //cb_config/reference/author
         revision       //cb_config/reference/revision
         description    //cb_config/reference/description
         generator      //cb_config/reference/generator

      @param parent: Parent node to search beneath.

      @return: C{ReferenceConfig} object or C{None} if the section does not exist.
      @raise ValueError: If some filled-in value is invalid.
      """
      reference = None
      section = readFirstChild(parent, "reference")
      if section is not None:
         reference = ReferenceConfig()
         reference.author = readString(section, "author")
         reference.revision = readString(section, "revision")
         reference.description = readString(section, "description")
         reference.generator = readString(section, "generator")
      return reference
   _parseReference = staticmethod(_parseReference)

   def _parseExtensions(parent):
      """
      Parses an extensions configuration section.
      
      We read groups of the following items, one list element per item::

         name                 //cb_config/extensions/action/name
         module               //cb_config/extensions/action/module
         function             //cb_config/extensions/action/function
         index                //cb_config/extensions/action/index
   
      The extended actions are parsed by L{_parseExtendedActions}.

      @param parent: Parent node to search beneath.

      @return: C{ExtensionsConfig} object or C{None} if the section does not exist.
      @raise ValueError: If some filled-in value is invalid.
      """
      extensions = None
      section = readFirstChild(parent, "extensions")
      if section is not None:
         extensions = ExtensionsConfig()
         extensions.actions = Config._parseExtendedActions(section)
      return extensions
   _parseExtensions = staticmethod(_parseExtensions)

   def _parseOptions(parent):
      """
      Parses a options configuration section.

      We read the following fields::

         startingDay    //cb_config/options/starting_day
         workingDir     //cb_config/options/working_dir
         backupUser     //cb_config/options/backup_user
         backupGroup    //cb_config/options/backup_group
         rcpCommand     //cb_config/options/rcp_command

      We also read groups of the following items, one list element per
      item::

         overrides      //cb_config/options/override

      The overrides are parsed by L{_parseOverrides}.

      @param parent: Parent node to search beneath.

      @return: C{OptionsConfig} object or C{None} if the section does not exist.
      @raise ValueError: If some filled-in value is invalid.
      """
      options = None
      section = readFirstChild(parent, "options")
      if section is not None:
         options = OptionsConfig()
         options.startingDay = readString(section, "starting_day")
         options.workingDir = readString(section, "working_dir")
         options.backupUser = readString(section, "backup_user")
         options.backupGroup = readString(section, "backup_group")
         options.rcpCommand = readString(section, "rcp_command")
         options.overrides = Config._parseOverrides(section)
      return options
   _parseOptions = staticmethod(_parseOptions)

   def _parseCollect(parent):
      """
      Parses a collect configuration section.

      We read the following individual fields::

         targetDir            //cb_config/collect/collect_dir
         collectMode          //cb_config/collect/collect_mode
         archiveMode          //cb_config/collect/archive_mode
         ignoreFile           //cb_config/collect/ignore_file

      We also read groups of the following items, one list element per
      item::

         absoluteExcludePaths //cb_config/collect/exclude/abs_path
         excludePatterns      //cb_config/collect/exclude/pattern
         collectDirs          //cb_config/collect/dir
   
      The exclusions are parsed by L{_parseExclusions} and the collect
      directories are parsed by L{_parseCollectDirs}.

      @param parent: Parent node to search beneath.

      @return: C{CollectConfig} object or C{None} if the section does not exist.
      @raise ValueError: If some filled-in value is invalid.
      """
      collect = None
      section = readFirstChild(parent, "collect")
      if section is not None:
         collect = CollectConfig()
         collect.targetDir = readString(section, "collect_dir")
         collect.collectMode = readString(section, "collect_mode")
         collect.archiveMode = readString(section, "archive_mode")
         collect.ignoreFile = readString(section, "ignore_file")
         (collect.absoluteExcludePaths, unused, collect.excludePatterns) = Config._parseExclusions(section)
         collect.collectDirs = Config._parseCollectDirs(section)
      return collect
   _parseCollect = staticmethod(_parseCollect)

   def _parseStage(parent):
      """
      Parses a stage configuration section.

      We read the following individual fields::

         targetDir      //cb_config/stage/staging_dir

      We also read groups of the following items, one list element per
      item::

         localPeers     //cb_config/stage/peer
         remotePeers    //cb_config/stage/peer

      The individual peer entries are parsed by L{_parsePeers}.

      @param parent: Parent node to search beneath.

      @return: C{StageConfig} object or C{None} if the section does not exist.
      @raise ValueError: If some filled-in value is invalid.
      """
      stage = None
      section = readFirstChild(parent, "stage")
      if section is not None:
         stage = StageConfig()
         stage.targetDir = readString(section, "staging_dir")
         (stage.localPeers, stage.remotePeers) = Config._parsePeers(section)
      return stage
   _parseStage = staticmethod(_parseStage)

   def _parseStore(parent):
      """
      Parses a store configuration section.

      We read the following fields::

         sourceDir         //cb_config/store/source_dir
         mediaType         //cb_config/store/media_type
         deviceType        //cb_config/store/device_type
         devicePath        //cb_config/store/target_device
         deviceScsiId      //cb_config/store/target_scsi_id
         driveSpeed        //cb_config/store/drive_speed
         checkData         //cb_config/store/check_data
         warnMidnite       //cb_config/store/warn_midnite

      @param parent: Parent node to search beneath.

      @return: C{StoreConfig} object or C{None} if the section does not exist.
      @raise ValueError: If some filled-in value is invalid.
      """
      store = None
      section = readFirstChild(parent, "store")
      if section is not None:
         store = StoreConfig()
         store.sourceDir = readString(section,  "source_dir")
         store.mediaType = readString(section,  "media_type")
         store.deviceType = readString(section,  "device_type")
         store.devicePath = readString(section,  "target_device")
         store.deviceScsiId = readString(section,  "target_scsi_id")
         store.driveSpeed = readInteger(section, "drive_speed")
         store.checkData = readBoolean(section, "check_data")
         store.warnMidnite = readBoolean(section, "warn_midnite")
      return store
   _parseStore = staticmethod(_parseStore)

   def _parsePurge(parent):
      """
      Parses a purge configuration section.

      We read groups of the following items, one list element per
      item::

         purgeDirs     //cb_config/purge/dir

      The individual directory entries are parsed by L{_parsePurgeDirs}.

      @param parent: Parent node to search beneath.

      @return: C{PurgeConfig} object or C{None} if the section does not exist.
      @raise ValueError: If some filled-in value is invalid.
      """
      purge = None
      section = readFirstChild(parent, "purge")
      if section is not None:
         purge = PurgeConfig()
         purge.purgeDirs = Config._parsePurgeDirs(section)
      return purge
   _parsePurge = staticmethod(_parsePurge)

   def _parseExtendedActions(parent):
      """
      Reads extended actions data from immediately beneath the parent.

      We read the following individual fields from each extended action::

         name        name
         module      module
         function    function
         index       index

      @param parent: Parent node to search beneath.

      @return: List of extended actions.
      @raise ValueError: If the data at the location can't be read
      """
      lst = []
      for entry in readChildren(parent, "action"):
         if entry.nodeType == Node.ELEMENT_NODE:
            action = ExtendedAction()
            action.name = readString(entry, "name")
            action.module = readString(entry, "module")
            action.function = readString(entry, "function")
            action.index = readString(entry, "index")
            lst.append(action);
      if lst == []:
         lst = None
      return lst
   _parseExtendedActions = staticmethod(_parseExtendedActions)

   def _parseExclusions(parent):
      """
      Reads exclusions data from immediately beneath the parent.

      We read groups of the following items, one list element per item::

         absolute    exclude/abs_path
         relative    exclude/rel_path
         patterns    exclude/pattern

      If there are none of some pattern (i.e. no relative path items) then
      C{None} will be returned for that item in the tuple.  

      This method can be used to parse exclusions on both the collect
      configuration level and on the collect directory level within collect
      configuration.

      @param parent: Parent node to search beneath.

      @return: Tuple of (absolute, relative, patterns) exclusions.
      """
      section = readFirstChild(parent, "exclude")
      if section is None:
         return (None, None, None)
      else:
         absolute = readStringList(section, "abs_path")
         relative = readStringList(section, "rel_path")
         patterns = readStringList(section, "pattern")
         return (absolute, relative, patterns)
   _parseExclusions = staticmethod(_parseExclusions)

   def _parseOverrides(parent):
      """
      Reads a list of C{CommandOverride} objects from immediately beneath the parent.

      We read the following individual fields::

         command                 command 
         absolutePath            abs_path

      @param parent: Parent node to search beneath.

      @return: List of C{CommandOverride} objects or C{None} if none are found.
      @raise ValueError: If some filled-in value is invalid.
      """
      lst = []
      for entry in readChildren(parent, "override"):
         if entry.nodeType == Node.ELEMENT_NODE:
            override = CommandOverride()
            override.command = readString(entry, "command")
            override.absolutePath = readString(entry, "abs_path")
            lst.append(override)
      if lst == []:
         lst = None
      return lst
   _parseOverrides = staticmethod(_parseOverrides)

   def _parseCollectDirs(parent):
      """
      Reads a list of C{CollectDir} objects from immediately beneath the parent.

      We read the following individual fields::

         absolutePath            abs_path
         collectMode             mode I{or} collect_mode
         archiveMode             archive_mode
         ignoreFile              ignore_file

      The collect mode is a special case.  Just a C{mode} tag is accepted for
      backwards compatibility, but we prefer C{collect_mode} for consistency
      with the rest of the config file and to avoid confusion with the archive
      mode.  If both are provided, only C{mode} will be used.

      We also read groups of the following items, one list element per
      item::

         absoluteExcludePaths    exclude/abs_path
         relativeExcludePaths    exclude/rel_path
         excludePatterns         exclude/pattern

      The exclusions are parsed by L{_parseExclusions}.

      @param parent: Parent node to search beneath.

      @return: List of C{CollectDir} objects or C{None} if none are found.
      @raise ValueError: If some filled-in value is invalid.
      """
      lst = []
      for entry in readChildren(parent, "dir"):
         if entry.nodeType == Node.ELEMENT_NODE:
            cdir = CollectDir()
            cdir.absolutePath = readString(entry, "abs_path")
            cdir.collectMode = readString(entry, "mode")
            if cdir.collectMode is None:
               cdir.collectMode = readString(entry, "collect_mode")
            cdir.archiveMode = readString(entry, "archive_mode")
            cdir.ignoreFile = readString(entry, "ignore_file")
            (cdir.absoluteExcludePaths, cdir.relativeExcludePaths, cdir.excludePatterns) = Config._parseExclusions(entry)
            lst.append(cdir)
      if lst == []:
         lst = None
      return lst
   _parseCollectDirs = staticmethod(_parseCollectDirs)

   def _parsePurgeDirs(parent):
      """
      Reads a list of C{PurgeDir} objects from immediately beneath the parent.

      We read the following individual fields::

         absolutePath            <baseExpr>/abs_path
         retainDays              <baseExpr>/retain_days

      @param parent: Parent node to search beneath.

      @return: List of C{PurgeDir} objects or C{None} if none are found.
      @raise ValueError: If the data at the location can't be read
      """
      lst = []
      for entry in readChildren(parent, "dir"):
         if entry.nodeType == Node.ELEMENT_NODE:
            cdir = PurgeDir()
            cdir.absolutePath = readString(entry, "abs_path")
            cdir.retainDays = readInteger(entry, "retain_days")
            lst.append(cdir)
      if lst == []:
         lst = None
      return lst
   _parsePurgeDirs = staticmethod(_parsePurgeDirs)

   def _parsePeers(parent):
      """
      Reads remote and local peer data from immediately beneath the parent.

      We read the following individual fields for both remote
      and local peers::

         name        name
         collectDir  collect_dir

      We also read the following individual fields for remote peers
      only::

         remoteUser  backup_user
         rcpCommand  rcp_command

      Additionally, the value in the C{type} field is used to determine whether
      this entry is a remote peer.  If the type is C{"remote"}, it's a remote
      peer, and if the type is C{"local"}, it's a remote peer.

      If there are none of one type of peer (i.e. no local peers) then C{None}
      will be returned for that item in the tuple.  

      @param parent: Parent node to search beneath.

      @return: Tuple of (local, remote) peer lists.
      @raise ValueError: If the data at the location can't be read
      """
      localPeers = []
      remotePeers = []
      for entry in readChildren(parent, "peer"):
         if entry.nodeType == Node.ELEMENT_NODE:
            peerType = readString(entry, "type")
            if peerType == "local":
               localPeer = LocalPeer()
               localPeer.name = readString(entry, "name")
               localPeer.collectDir = readString(entry, "collect_dir")
               localPeers.append(localPeer)
            elif peerType == "remote":
               remotePeer = RemotePeer()
               remotePeer.name = readString(entry, "name")
               remotePeer.collectDir = readString(entry, "collect_dir")
               remotePeer.remoteUser = readString(entry, "backup_user")
               remotePeer.rcpCommand = readString(entry, "rcp_command")
               remotePeers.append(remotePeer)
      if localPeers == []:
         localPeers = None
      if remotePeers == []:
         remotePeers = None
      return (localPeers, remotePeers)
   _parsePeers = staticmethod(_parsePeers)


   ########################################
   # High-level methods for generating XML
   ########################################

   def _extractXml(self):
      """
      Internal method to extract configuration into an XML string.

      This method assumes that the internal L{validate} method has been called
      prior to extracting the XML, if the caller cares.  No validation will be
      done internally.

      As a general rule, fields that are set to C{None} will be extracted into
      the document as empty tags.  The same goes for container tags that are
      filled based on lists - if the list is empty or C{None}, the container
      tag will be empty.
      """
      impl = getDOMImplementation()
      xmlDom = impl.createDocument(None, "cb_config", None)
      parentNode = xmlDom.documentElement
      Config._addReference(xmlDom, parentNode, self.reference)
      Config._addExtensions(xmlDom, parentNode, self.extensions)
      Config._addOptions(xmlDom, parentNode, self.options)
      Config._addCollect(xmlDom, parentNode, self.collect)
      Config._addStage(xmlDom, parentNode, self.stage)
      Config._addStore(xmlDom, parentNode, self.store)
      Config._addPurge(xmlDom, parentNode, self.purge)
      xmlBuffer = StringIO()
      PrettyPrint(xmlDom, xmlBuffer)
      xmlData = xmlBuffer.getvalue()
      xmlBuffer.close()
      xmlDom.unlink()
      return xmlData

   def _addReference(xmlDom, parentNode, referenceConfig):
      """
      Adds a <reference> configuration section as the next child of a parent.

      We add the following fields to the document::

         author         //cb_config/reference/author
         revision       //cb_config/reference/revision
         description    //cb_config/reference/description
         generator      //cb_config/reference/generator

      If C{referenceConfig} is C{None}, then no container will be added.

      @param xmlDom: DOM tree as from C{impl.createDocument()}.
      @param parentNode: Parent that the section should be appended to.
      @param referenceConfig: Reference configuration section to be added to the document.
      """
      if referenceConfig is not None:
         sectionNode = addContainerNode(xmlDom, parentNode, "reference")
         addStringNode(xmlDom, sectionNode, "author", referenceConfig.author)
         addStringNode(xmlDom, sectionNode, "revision", referenceConfig.revision)
         addStringNode(xmlDom, sectionNode, "description", referenceConfig.description)
         addStringNode(xmlDom, sectionNode, "generator", referenceConfig.generator)
   _addReference = staticmethod(_addReference)

   def _addExtensions(xmlDom, parentNode, extensionsConfig):
      """
      Adds an <extensions> configuration section as the next child of a parent.

      We add groups of the following items, one list element per item::

         actions        //cb_config/extensions/action

      The extended action entries are added by L{_addExtendedAction}.

      If C{extensionsConfig} is C{None}, then no container will be added.

      @param xmlDom: DOM tree as from C{impl.createDocument()}.
      @param parentNode: Parent that the section should be appended to.
      @param extensionsConfig: Extensions configuration section to be added to the document.
      """
      if extensionsConfig is not None:
         sectionNode = addContainerNode(xmlDom, parentNode, "extensions")
         if extensionsConfig.actions is not None:
            for action in extensionsConfig.actions:
               Config._addExtendedAction(xmlDom, sectionNode, action)
   _addExtensions = staticmethod(_addExtensions)

   def _addOptions(xmlDom, parentNode, optionsConfig):
      """
      Adds a <options> configuration section as the next child of a parent.

      We add the following fields to the document::

         startingDay    //cb_config/options/starting_day
         workingDir     //cb_config/options/working_dir
         backupUser     //cb_config/options/backup_user
         backupGroup    //cb_config/options/backup_group
         rcpCommand     //cb_config/options/rcp_command

      We also add groups of the following items, one list element per
      item::

         overrides      //cb_config/options/override

      The individual collect directories are added by L{_addOverride}.

      If C{optionsConfig} is C{None}, then no container will be added.

      @param xmlDom: DOM tree as from C{impl.createDocument()}.
      @param parentNode: Parent that the section should be appended to.
      @param optionsConfig: Options configuration section to be added to the document.
      """
      if optionsConfig is not None:
         sectionNode = addContainerNode(xmlDom, parentNode, "options")
         addStringNode(xmlDom, sectionNode, "starting_day", optionsConfig.startingDay)
         addStringNode(xmlDom, sectionNode, "working_dir", optionsConfig.workingDir)
         addStringNode(xmlDom, sectionNode, "backup_user", optionsConfig.backupUser)
         addStringNode(xmlDom, sectionNode, "backup_group", optionsConfig.backupGroup)
         addStringNode(xmlDom, sectionNode, "rcp_command", optionsConfig.rcpCommand)
         if optionsConfig.overrides is not None:
            for override in optionsConfig.overrides:
               Config._addOverride(xmlDom, sectionNode, override)
   _addOptions = staticmethod(_addOptions)

   def _addCollect(xmlDom, parentNode, collectConfig):
      """
      Adds a <collect> configuration section as the next child of a parent.

      We add the following fields to the document::

         targetDir            //cb_config/collect/collect_dir
         collectMode          //cb_config/collect/collect_mode
         archiveMode          //cb_config/collect/archive_mode
         ignoreFile           //cb_config/collect/ignore_file

      We also add groups of the following items, one list element per
      item::

         absoluteExcludePaths //cb_config/collect/exclude/abs_path
         excludePatterns      //cb_config/collect/exclude/pattern
         collectDirs          //cb_config/collect/dir

      The individual collect directories are added by L{_addCollectDir}.
   
      If C{collectConfig} is C{None}, then no container will be added.

      @param xmlDom: DOM tree as from C{impl.createDocument()}.
      @param parentNode: Parent that the section should be appended to.
      @param collectConfig: Collect configuration section to be added to the document.
      """
      if collectConfig is not None:
         sectionNode = addContainerNode(xmlDom, parentNode, "collect")
         addStringNode(xmlDom, sectionNode, "collect_dir", collectConfig.targetDir)
         addStringNode(xmlDom, sectionNode, "collect_mode", collectConfig.collectMode)
         addStringNode(xmlDom, sectionNode, "archive_mode", collectConfig.archiveMode)
         addStringNode(xmlDom, sectionNode, "ignore_file", collectConfig.ignoreFile)
         if ((collectConfig.absoluteExcludePaths is not None and collectConfig.absoluteExcludePaths != []) or
             (collectConfig.excludePatterns is not None and collectConfig.excludePatterns != [])):
            excludeNode = addContainerNode(xmlDom, sectionNode, "exclude")
            if collectConfig.absoluteExcludePaths is not None:
               for absolutePath in collectConfig.absoluteExcludePaths:
                  addStringNode(xmlDom, excludeNode, "abs_path", absolutePath)
            if collectConfig.excludePatterns is not None:
               for pattern in collectConfig.excludePatterns:
                  addStringNode(xmlDom, excludeNode, "pattern", pattern)
         if collectConfig.collectDirs is not None:
            for collectDir in collectConfig.collectDirs:
               Config._addCollectDir(xmlDom, sectionNode, collectDir)
   _addCollect = staticmethod(_addCollect)

   def _addStage(xmlDom, parentNode, stageConfig):
      """
      Adds a <stage> configuration section as the next child of a parent.

      We add the following fields to the document::

         targetDir      //cb_config/stage/staging_dir

      We also add groups of the following items, one list element per
      item::

         localPeers     //cb_config/stage/peer
         remotePeers    //cb_config/stage/peer

      The individual local and remote peer entries are added by
      L{_addLocalPeer} and L{_addRemotePeer}, respectively.

      If C{stageConfig} is C{None}, then no container will be added.

      @param xmlDom: DOM tree as from C{impl.createDocument()}.
      @param parentNode: Parent that the section should be appended to.
      @param stageConfig: Stage configuration section to be added to the document.
      """
      if stageConfig is not None:
         sectionNode = addContainerNode(xmlDom, parentNode, "stage")
         addStringNode(xmlDom, sectionNode, "staging_dir", stageConfig.targetDir)
         if stageConfig.localPeers is not None:
            for localPeer in stageConfig.localPeers:
               Config._addLocalPeer(xmlDom, sectionNode, localPeer)
         if stageConfig.remotePeers is not None:
            for remotePeer in stageConfig.remotePeers:
               Config._addRemotePeer(xmlDom, sectionNode, remotePeer)
   _addStage = staticmethod(_addStage)

   def _addStore(xmlDom, parentNode, storeConfig):
      """
      Adds a <store> configuration section as the next child of a parent.

      We add the following fields to the document::

         sourceDir         //cb_config/store/source_dir
         mediaType         //cb_config/store/media_type
         deviceType        //cb_config/store/device_type
         devicePath        //cb_config/store/target_device
         deviceScsiId      //cb_config/store/target_scsi_id
         driveSpeed        //cb_config/store/drive_speed
         checkData         //cb_config/store/check_data
         warnMidnite       //cb_config/store/warn_midnite

      If C{storeConfig} is C{None}, then no container will be added.

      @param xmlDom: DOM tree as from C{impl.createDocument()}.
      @param parentNode: Parent that the section should be appended to.
      @param storeConfig: Store configuration section to be added to the document.
      """
      if storeConfig is not None:
         sectionNode = addContainerNode(xmlDom, parentNode, "store")
         addStringNode(xmlDom, sectionNode, "source_dir", storeConfig.sourceDir)
         addStringNode(xmlDom, sectionNode, "media_type", storeConfig.mediaType)
         addStringNode(xmlDom, sectionNode, "device_type", storeConfig.deviceType)
         addStringNode(xmlDom, sectionNode, "target_device", storeConfig.devicePath)
         addStringNode(xmlDom, sectionNode, "target_scsi_id", storeConfig.deviceScsiId)
         addIntegerNode(xmlDom, sectionNode, "drive_speed", storeConfig.driveSpeed)
         addBooleanNode(xmlDom, sectionNode, "check_data", storeConfig.checkData)
         addBooleanNode(xmlDom, sectionNode, "warn_midnite", storeConfig.warnMidnite)
   _addStore = staticmethod(_addStore)

   def _addPurge(xmlDom, parentNode, purgeConfig):
      """
      Adds a <purge> configuration section as the next child of a parent.

      We add the following fields to the document::

         purgeDirs     //cb_config/purge/dir

      The individual directory entries are added by L{_addPurgeDir}.

      If C{purgeConfig} is C{None}, then no container will be added.

      @param xmlDom: DOM tree as from C{impl.createDocument()}.
      @param parentNode: Parent that the section should be appended to.
      @param purgeConfig: Purge configuration section to be added to the document.
      """
      if purgeConfig is not None:
         sectionNode = addContainerNode(xmlDom, parentNode, "purge")
         if purgeConfig.purgeDirs is not None:
            for purgeDir in purgeConfig.purgeDirs:
               Config._addPurgeDir(xmlDom, sectionNode, purgeDir)
   _addPurge = staticmethod(_addPurge)

   def _addExtendedAction(xmlDom, parentNode, action):
      """
      Adds an extended action container as the next child of a parent.

      We add the following fields to the document::

         name        action/name
         module      action/module
         function    action/function
         index       action/index

      The <action> node itself is created as the next child of the parent node.
      This method only adds one action node.  The parent must loop for each action
      in the C{ExtensionsConfig} object.

      If C{action} is C{None}, this method call will be a no-op.

      @param xmlDom: DOM tree as from C{impl.createDocument()}.
      @param parentNode: Parent that the section should be appended to.
      @param action: Purge directory to be added to the document.
      """
      if action is not None:
         sectionNode = addContainerNode(xmlDom, parentNode, "action")
         addStringNode(xmlDom, sectionNode, "name", action.name)
         addStringNode(xmlDom, sectionNode, "module", action.module)
         addStringNode(xmlDom, sectionNode, "function", action.function)
         addIntegerNode(xmlDom, sectionNode, "index", action.index)
   _addExtendedAction = staticmethod(_addExtendedAction)

   def _addOverride(xmlDom, parentNode, override):
      """
      Adds a command override container as the next child of a parent.

      We add the following fields to the document::

         command                 override/command
         absolutePath            override/abs_path
   
      The <override> node itself is created as the next child of the parent
      node.  This method only adds one override node.  The parent must loop for
      each override in the C{OptionsConfig} object.

      If C{override} is C{None}, this method call will be a no-op.

      @param xmlDom: DOM tree as from C{impl.createDocument()}.
      @param parentNode: Parent that the section should be appended to.
      @param override: Command override to be added to the document.
      """
      if override is not None:
         sectionNode = addContainerNode(xmlDom, parentNode, "override")
         addStringNode(xmlDom, sectionNode, "command", override.command)
         addStringNode(xmlDom, sectionNode, "abs_path", override.absolutePath)
   _addOverride = staticmethod(_addOverride)

   def _addCollectDir(xmlDom, parentNode, collectDir):
      """
      Adds a collect directory container as the next child of a parent.

      We add the following fields to the document::

         absolutePath            dir/abs_path
         collectMode             dir/collect_mode
         archiveMode             dir/archive_mode
         ignoreFile              dir/ignore_file
   
      Note that an original XML document might have listed the collect mode
      using the C{mode} tag, since we accept both C{collect_mode} and C{mode}.
      However, here we'll only emit the preferred C{collect_mode} tag.

      We also add groups of the following items, one list element per item::

         absoluteExcludePaths    dir/exclude/abs_path
         relativeExcludePaths    dir/exclude/rel_path
         excludePatterns         dir/exclude/pattern

      The <dir> node itself is created as the next child of the parent node.
      This method only adds one collect directory node.  The parent must loop
      for each collect directory in the C{CollectConfig} object.

      If C{collectDir} is C{None}, this method call will be a no-op.

      @param xmlDom: DOM tree as from C{impl.createDocument()}.
      @param parentNode: Parent that the section should be appended to.
      @param collectDir: Collect directory to be added to the document.
      """
      if collectDir is not None:
         sectionNode = addContainerNode(xmlDom, parentNode, "dir")
         addStringNode(xmlDom, sectionNode, "abs_path", collectDir.absolutePath)
         addStringNode(xmlDom, sectionNode, "collect_mode", collectDir.collectMode)
         addStringNode(xmlDom, sectionNode, "archive_mode", collectDir.archiveMode)
         addStringNode(xmlDom, sectionNode, "ignore_file", collectDir.ignoreFile)
         if ((collectDir.absoluteExcludePaths is not None and collectDir.absoluteExcludePaths != []) or
             (collectDir.relativeExcludePaths is not None and collectDir.relativeExcludePaths != []) or
             (collectDir.excludePatterns is not None and collectDir.excludePatterns != [])):
            excludeNode = addContainerNode(xmlDom, sectionNode, "exclude")
            if collectDir.absoluteExcludePaths is not None:
               for absolutePath in collectDir.absoluteExcludePaths:
                  addStringNode(xmlDom, excludeNode, "abs_path", absolutePath)
            if collectDir.relativeExcludePaths is not None:
               for relativePath in collectDir.relativeExcludePaths:
                  addStringNode(xmlDom, excludeNode, "rel_path", relativePath)
            if collectDir.excludePatterns is not None:
               for pattern in collectDir.excludePatterns:
                  addStringNode(xmlDom, excludeNode, "pattern", pattern)
   _addCollectDir = staticmethod(_addCollectDir)

   def _addLocalPeer(xmlDom, parentNode, localPeer):
      """
      Adds a local peer container as the next child of a parent.

      We add the following fields to the document::

         name        peer/name
         collectDir  peer/collect_dir

      Additionally, C{peer/type} is filled in with C{"local"}, since this is a
      local peer.

      The <peer> node itself is created as the next child of the parent node.
      This method only adds one peer node.  The parent must loop for each peer
      in the C{StageConfig} object.

      If C{localPeer} is C{None}, this method call will be a no-op.

      @param xmlDom: DOM tree as from C{impl.createDocument()}.
      @param parentNode: Parent that the section should be appended to.
      @param localPeer: Purge directory to be added to the document.
      """
      if localPeer is not None:
         sectionNode = addContainerNode(xmlDom, parentNode, "peer")
         addStringNode(xmlDom, sectionNode, "name", localPeer.name)
         addStringNode(xmlDom, sectionNode, "type", "local")
         addStringNode(xmlDom, sectionNode, "collect_dir", localPeer.collectDir)
   _addLocalPeer = staticmethod(_addLocalPeer)

   def _addRemotePeer(xmlDom, parentNode, remotePeer):
      """
      Adds a remote peer container as the next child of a parent.

      We add the following fields to the document::

         name        peer/name
         collectDir  peer/collect_dir
         remoteUser  peer/backup_user
         rcpCommand  peer/rcp_command

      Additionally, C{peer/type} is filled in with C{"remote"}, since this is a
      remote peer.

      The <peer> node itself is created as the next child of the parent node.
      This method only adds one peer node.  The parent must loop for each peer
      in the C{StageConfig} object.

      If C{remotePeer} is C{None}, this method call will be a no-op.

      @param xmlDom: DOM tree as from C{impl.createDocument()}.
      @param parentNode: Parent that the section should be appended to.
      @param remotePeer: Purge directory to be added to the document.
      """
      if remotePeer is not None:
         sectionNode = addContainerNode(xmlDom, parentNode, "peer")
         addStringNode(xmlDom, sectionNode, "name", remotePeer.name)
         addStringNode(xmlDom, sectionNode, "type", "remote")
         addStringNode(xmlDom, sectionNode, "collect_dir", remotePeer.collectDir)
         addStringNode(xmlDom, sectionNode, "backup_user", remotePeer.remoteUser)
         addStringNode(xmlDom, sectionNode, "rcp_command", remotePeer.rcpCommand)
   _addRemotePeer = staticmethod(_addRemotePeer)

   def _addPurgeDir(xmlDom, parentNode, purgeDir):
      """
      Adds a purge directory container as the next child of a parent.

      We add the following fields to the document::

         absolutePath            dir/abs_path
         retainDays              dir/retain_days

      The <dir> node itself is created as the next child of the parent node.
      This method only adds one purge directory node.  The parent must loop for
      each purge directory in the C{PurgeConfig} object.

      If C{purgeDir} is C{None}, this method call will be a no-op.

      @param xmlDom: DOM tree as from C{impl.createDocument()}.
      @param parentNode: Parent that the section should be appended to.
      @param purgeDir: Purge directory to be added to the document.
      """
      if purgeDir is not None:
         sectionNode = addContainerNode(xmlDom, parentNode, "dir")
         addStringNode(xmlDom, sectionNode, "abs_path", purgeDir.absolutePath)
         addIntegerNode(xmlDom, sectionNode, "retain_days", purgeDir.retainDays)
   _addPurgeDir = staticmethod(_addPurgeDir)


   #################################################
   # High-level methods used for validating content
   #################################################

   def _validateContents(self):
      """
      Validates configuration contents per rules discussed in module
      documentation.

      This is the second pass at validation.  It ensures that any filled-in
      section contains valid data.  Any sections which is not set to C{None} is
      validated per the rules for that section, laid out in the module
      documentation (above).

      @raise ValueError: If configuration is invalid.
      """
      self._validateReference()
      self._validateExtensions()
      self._validateOptions()
      self._validateCollect()
      self._validateStage()
      self._validateStore()
      self._validatePurge()

   def _validateReference(self):
      """
      Validates reference configuration.
      There are currently no reference-related validations.
      @raise ValueError: If reference configuration is invalid.
      """
      pass

   def _validateExtensions(self):
      """
      Validates extensions configuration.

      The list of actions may be either C{None} or an empty list C{[]} if
      desired.  Each extended action must include a name, a module, a 
      function and an index.

      @raise ValueError: If reference configuration is invalid.
      """
      if self.extensions is not None:
         if self.extensions.actions is not None:
            for action in self.extensions.actions:
               if action.name is None:
                  raise ValueError("Each extended action must set a name.")
               if action.module is None:
                  raise ValueError("Each extended action must set a module.")
               if action.function is None:
                  raise ValueError("Each extended action must set a function.")
               if action.index is None:
                  raise ValueError("Each extended action must set an index.")

   def _validateOptions(self):
      """
      Validates options configuration.

      All fields must be filled in.  The rcp command is used as a default value
      for all remote peers in the staging section.  Remote peers can also rely
      on the backup user as the default remote user name if they choose.

      @raise ValueError: If reference configuration is invalid.
      """
      if self.options is not None:
         if self.options.startingDay is None:
            raise ValueError("Options section starting day must be filled in.")
         if self.options.workingDir is None:
            raise ValueError("Options section working directory must be filled in.")
         if self.options.backupUser is None:
            raise ValueError("Options section backup user must be filled in.")
         if self.options.backupGroup is None:
            raise ValueError("Options section backup group must be filled in.")
         if self.options.rcpCommand is None:
            raise ValueError("Options section remote copy command must be filled in.")

   def _validateCollect(self):
      """
      Validates collect configuration.

      The target directory must be filled in.  The collect mode, archive mode
      and ignore file are all optional.  The list of absolute paths to exclude
      and patterns to exclude may be either C{None} or an empty list C{[]} if
      desired.  The collect directory list must contain at least one entry.  

      Each collect directory entry must contain an absolute path to collect,
      and then must either be able to take collect mode, archive mode and
      ignore file configuration from the parent C{CollectConfig} object, or
      must set each value on its own.  The list of absolute paths to exclude,
      relative paths to exclude and patterns to exclude may be either C{None}
      or an empty list C{[]} if desired.  Any list of absolute paths to exclude
      or patterns to exclude will be combined with the same list in the
      C{CollectConfig} object to make the complete list for a given directory.

      @raise ValueError: If collect configuration is invalid.
      """
      if self.collect is not None:
         if self.collect.targetDir is None:
            raise ValueError("Collect section target directory must be filled in.")
         if self.collect.collectDirs is None or len(self.collect.collectDirs) < 1:
            raise ValueError("Collect section must contain at least one collect directory.")
         for collectDir in self.collect.collectDirs:
            if collectDir.absolutePath is None:
               raise ValueError("Each collect directory must set an absolute path.")
            if self.collect.collectMode is None and collectDir.collectMode is None:
               raise ValueError("Collect mode must either be set in parent collect section or individual collect directory.")
            if self.collect.archiveMode is None and collectDir.archiveMode is None:
               raise ValueError("Archive mode must either be set in parent collect section or individual collect directory.")
            if self.collect.ignoreFile is None and collectDir.ignoreFile is None:
               raise ValueError("Ignore file must either be set in parent collect section or individual collect directory.")

   def _validateStage(self):
      """
      Validates stage configuration.

      The target directory must be filled in.  There must be at least one peer
      (remote or local) between the two lists of peers.  A list with no entries
      can be either C{None} or an empty list C{[]} if desired.

      Local peers must be completely filled in, including both name and collect
      directory.  Remote peers must also fill in the name and collect
      directory, but can leave the remote user and rcp command unset.  In this
      case, the remote user is assumed to match the backup user from the
      options section and rcp command is taken directly from the options
      section.

      @raise ValueError: If stage configuration is invalid.
      """
      if self.stage is not None:
         if self.stage.targetDir is None:
            raise ValueError("Stage section target directory must be filled in.")
         if self.stage.localPeers is None and self.stage.remotePeers is None:
            raise ValueError("Stage section must contain at least one backup peer.")
         if self.stage.localPeers is None and self.stage.remotePeers is not None:
            if len(self.stage.remotePeers) < 1:
               raise ValueError("Stage section must contain at least one backup peer.")
         elif self.stage.localPeers is not None and self.stage.remotePeers is None:
            if len(self.stage.localPeers) < 1:
               raise ValueError("Stage section must contain at least one backup peer.")
         elif self.stage.localPeers is not None and self.stage.remotePeers is not None:
            if len(self.stage.localPeers) + len(self.stage.remotePeers) < 1:
               raise ValueError("Stage section must contain at least one backup peer.")
         if self.stage.localPeers is not None:
            for localPeer in self.stage.localPeers:
               if localPeer.name is None:
                  raise ValueError("Local peers must set a name.")
               if localPeer.collectDir is None:
                  raise ValueError("Local peers must set a collect directory.")
         if self.stage.remotePeers is not None:
            for remotePeer in self.stage.remotePeers:
               if remotePeer.name is None:
                  raise ValueError("Remote peers must set a name.")
               if remotePeer.collectDir is None:
                  raise ValueError("Remote peers must set a collect directory.")
               if (self.options is None or self.options.backupUser is None) and remotePeer.remoteUser is None: # redundant
                  raise ValueError("Remote user must either be set in options section or individual remote peer.")
               if (self.options is None or self.options.rcpCommand is None) and remotePeer.rcpCommand is None: # redundant
                  raise ValueError("Remote copy command must either be set in options section or individual remote peer.")

   def _validateStore(self):
      """
      Validates store configuration.

      The device type, drive speed are optional, and all other values are
      required (missing booleans will be set to defaults, which is OK).

      The image writer functionality in the C{writer} module is supposed to be
      able to handle a device speed of C{None}.  Any caller which needs a
      "real" (non-C{None}) value for the device type can use
      C{DEFAULT_DEVICE_TYPE}, which is guaranteed to be sensible.

      @raise ValueError: If store configuration is invalid.
      """
      if self.store is not None:
         if self.store.sourceDir is None:
            raise ValueError("Store section source directory must be filled in.")
         if self.store.mediaType is None:
            raise ValueError("Store section media type must be filled in.")
         if self.store.devicePath is None:
            raise ValueError("Store section device path must be filled in.")
         if self.store.deviceScsiId is None:
            raise ValueError("Store section SCSI id must be filled in.")

   def _validatePurge(self):
      """
      Validates purge configuration.

      The list of purge directories may be either C{None} or an empty list
      C{[]} if desired.  All purge directories must contain a path and a retain
      days value.

      @raise ValueError: If purge configuration is invalid.
      """
      if self.purge is not None:
         if self.purge.purgeDirs is not None:
            for purgeDir in self.purge.purgeDirs:
               if purgeDir.absolutePath is None:
                  raise ValueError("Each purge directory must set an absolute path.")
               if purgeDir.retainDays is None:
                  raise ValueError("Each purge directory must set a retain days value.")


########################################################################
# Public utility functions
########################################################################

##########################
# readChildren() function
##########################

def readChildren(parent, name):
   """
   Returns a list of nodes with a given name immediately beneath the
   parent.

   By "immediately beneath" the parent, we mean from among nodes that are
   direct children of the passed-in parent node.  

   Underneath, we use the Python C{getElementsByTagName} method, which is
   pretty cool, but which (surprisingly?) returns a list of all children
   with a given name below the parent, at any level.  We just prune that
   list to include only children whose C{parentNode} matches the passed-in
   parent.

   @param parent: Parent node to search beneath.
   @param name: Name of nodes to search for.

   @return: List of child nodes with correct parent, or an empty list if
   no matching nodes are found.
   """
   lst = []
   if parent is not None:
      result = parent.getElementsByTagName(name)
      for entry in result:
         if entry.parentNode is parent:
            lst.append(entry)
   return lst


############################
# readFirstChild() function
############################

def readFirstChild(parent, name):
   """
   Returns the first child with a given name immediately beneath the parent.

   By "immediately beneath" the parent, we mean from among nodes that are
   direct children of the passed-in parent node.  

   @param parent: Parent node to search beneath.
   @param name: Name of node to search for.

   @return: First properly-named child of parent, or C{None} if no matching nodes are found.
   """
   result = readChildren(parent, name)
   if result is None or result == []:
      return None
   return result[0]


############################
# readStringList() function
############################

def readStringList(parent, name):
   """
   Returns a list of the string contents associated with nodes with a given
   name immediately beneath the parent.

   By "immediately beneath" the parent, we mean from among nodes that are
   direct children of the passed-in parent node.  

   First, we find all of the nodes using L{readChildren}, and then we
   retrieve the "string contents" of each of those nodes.  The returned list
   has one entry per matching node.  We assume that string contents of a
   given node belong to the first C{TEXT_NODE} child of that node.  Nodes
   which have no C{TEXT_NODE} children are not represented in the returned
   list.

   @param parent: Parent node to search beneath.
   @param name: Name of node to search for.

   @return: List of strings as described above, or C{None} if no matching nodes are found.
   """
   lst = []
   result = readChildren(parent, name)
   for entry in result:
      if entry.hasChildNodes:
         for child in entry.childNodes:
            if child.nodeType == Node.TEXT_NODE:
               lst.append(child.nodeValue)
               break
   if lst == []:
      lst = None
   return lst


########################
# readString() function
########################

def readString(parent, name):
   """
   Returns string contents of the first child with a given name immediately
   beneath the parent.

   By "immediately beneath" the parent, we mean from among nodes that are
   direct children of the passed-in parent node.  We assume that string
   contents of a given node belong to the first C{TEXT_NODE} child of that
   node.

   @param parent: Parent node to search beneath.
   @param name: Name of node to search for.

   @return: String contents of node or C{None} if no matching nodes are found.
   """
   result = readStringList(parent, name)
   if result is None:
      return None
   return result[0]


#########################
# readInteger() function
#########################

def readInteger(parent, name):
   """
   Returns integer contents of the first child with a given name immediately
   beneath the parent.

   By "immediately beneath" the parent, we mean from among nodes that are
   direct children of the passed-in parent node.  

   @param parent: Parent node to search beneath.
   @param name: Name of node to search for.

   @return: Integer contents of node or C{None} if no matching nodes are found.
   @raise ValueError: If the string at the location can't be converted to an integer.
   """
   result = readString(parent, name)
   if result is None:
      return None
   else:
      return int(result)


#########################
# readBoolean() function
#########################

def readBoolean(parent, name):
   """
   Returns boolean contents of the first child with a given name immediately
   beneath the parent.

   By "immediately beneath" the parent, we mean from among nodes that are
   direct children of the passed-in parent node.  

   The string value of the node must be one of the values in L{VALID_BOOLEAN_VALUES}.

   @param parent: Parent node to search beneath.
   @param name: Name of node to search for.

   @return: Boolean contents of node or C{None} if no matching nodes are found.
   @raise ValueError: If the string at the location can't be converted to a boolean.
   """
   result = readString(parent, name)
   if result is None:
      return None
   else:
      if result in TRUE_BOOLEAN_VALUES:
         return True
      elif result in FALSE_BOOLEAN_VALUES:
         return False
      else:
         raise ValueError("Boolean values must be one of %s." % VALID_BOOLEAN_VALUES)


##############################
# addContainerNode() function
##############################

def addContainerNode(xmlDom, parentNode, nodeName):
   """
   Adds a container node as the next child of a parent node.

   @param xmlDom: DOM tree as from C{impl.createDocument()}.
   @param parentNode: Parent node to create child for.
   @param nodeName: Name of the new container node.

   @return: Reference to the newly-created node.
   """
   containerNode = xmlDom.createElement(nodeName)
   parentNode.appendChild(containerNode)
   return containerNode


###########################
# addStringNode() function
###########################

def addStringNode(xmlDom, parentNode, nodeName, nodeValue):
   """
   Adds a text node as the next child of a parent, to contain a string.

   If the C{nodeValue} is None, then the node will be created, but will be
   empty (i.e. will contain no text node child).

   @param xmlDom: DOM tree as from C{impl.createDocument()}.
   @param parentNode: Parent node to create child for.
   @param nodeName: Name of the new container node.
   @param nodeValue: The value to put into the node.

   @return: Reference to the newly-created node.
   """
   containerNode = addContainerNode(xmlDom, parentNode, nodeName)
   if nodeValue is not None:
      textNode = xmlDom.createTextNode(nodeValue)
      containerNode.appendChild(textNode)
   return containerNode


############################
# addIntegerNode() function
############################

def addIntegerNode(xmlDom, parentNode, nodeName, nodeValue):
   """
   Adds a text node as the next child of a parent, to contain an integer.

   If the C{nodeValue} is None, then the node will be created, but will be
   empty (i.e. will contain no text node child).

   The integer will be converted to a string using "%d".  The result will be
   added to the document via L{addStringNode}.

   @param xmlDom: DOM tree as from C{impl.createDocument()}.
   @param parentNode: Parent node to create child for.
   @param nodeName: Name of the new container node.
   @param nodeValue: The value to put into the node.

   @return: Reference to the newly-created node.
   """
   if nodeValue is None:
      return addStringNode(xmlDom, parentNode, nodeName, None)
   else:
      return addStringNode(xmlDom, parentNode, nodeName, "%d" % nodeValue)


############################
# addBooleanNode() function
############################

def addBooleanNode(xmlDom, parentNode, nodeName, nodeValue):
   """
   Adds a text node as the next child of a parent, to contain a boolean.

   If the C{nodeValue} is None, then the node will be created, but will be
   empty (i.e. will contain no text node child).

   Boolean C{True}, or anything else interpreted as C{True} by Python, will
   be converted to a string "Y".  Anything else will be converted to a
   string "N".  The result is added to the document via L{addStringNode}.

   @param xmlDom: DOM tree as from C{impl.createDocument()}.
   @param parentNode: Parent node to create child for.
   @param nodeName: Name of the new container node.
   @param nodeValue: The value to put into the node.

   @return: Reference to the newly-created node.
   """
   if nodeValue is None:
      return addStringNode(xmlDom, parentNode, nodeName, None)
   else:
      if nodeValue:
         return addStringNode(xmlDom, parentNode, nodeName, "Y")
      else:
         return addStringNode(xmlDom, parentNode, nodeName, "N")
