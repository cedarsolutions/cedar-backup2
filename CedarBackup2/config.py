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
   C{/etc}, but users can specify a different location if they want to.  The
   C{cback.dtd} file included with the source distribution is an SGML DTD which
   specifies the format of C{cback.conf}.

   The C{Config} class is a Python object representation of a Cedar Backup XML
   configuration file.  The representation is two-way: XML data can be used to
   create a C{Config} object, and then changes to the object can be propogated
   back to disk.  A C{Config} object can even be used to create a configuration
   file from scratch programmatically.

   The C{Config} class is intended to be the only Python-language interface to
   Cedar Backup configuration on disk.  Cedar Backup will use the class as its
   internal representation of configuration, and applications external to Cedar
   Backup itself (such as a hypothetical third-party configuration tool written
   in Python) should also use the class when they need to read and write
   configuration files.

External Python Libraries
=========================

   This class is one of the few pieces of code in the CedarBackup2 package that
   requires functionality outside of the Python 2.3 standard library.  It
   depends on the XPath functionality provided by the PyXML product in the
   C{xml.xpath} package.

Backwards Compatibility
=======================

   The configuration file format has changed between Cedar Backup 1.x and Cedar
   Backup 2.x.  Any Cedar Backup 1.x configuration file is also a valid Cedar
   Backup 2.x configuration file.  However, it doesn't work to go the other
   direction, as the 2.x configuration files may contain additional fields that
   are not accepted by older versions of the software.  

   For instance, the 2.x software allows global absolute path exclusions,
   global regular expression exclusions, and directory-specific absolute path,
   relative path and regular expression exclusions; while the 1.x software only
   allows directory-specific absolute path exclusions.  There are also some
   cases where the 2.x software allows certain values (such as the ignore file)
   to be specified at a high-level and then overridden at a lower level where
   in the 1.x software these values are only allowed at a single point in
   configuration.

XML Configuration Structure
===========================

   A C{Config} object can either be created "empty", or can be created based on
   XML input (either in the form of a string or read in from a file on disk).
   Generally speaking, the XML input I{must} result in a C{Config} object which
   passes the validations laid out below in the I{Validation} section.  

   An XML configuration file is composed of six sections:

      - I{reference}: specifies reference information about the file (author, revision, etc)
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
   way, we get acceptable ease-of-use but we also don't accept or emit invalid
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

   The device type and drive speed and capacity mode are optional, and all
   other values are required (missing booleans will be set to defaults, which
   is OK).

   The image writer functionality in the C{writer} module is supposed to be
   able to handle a device speed of C{None}.  Any caller which needs a "real"
   (non-C{None}) value for the device type can use C{DEFAULT_DEVICE_TYPE},
   which is guaranteed to be sensible.

   I{Purge Validations}

   The list of purge directories may be either C{None} or an empty list C{[]}
   if desired.  All purge directories must contain a path and a retain days
   value.

@sort: LocalPeer, RemotePeer, CollectDir, PurgeDir, ReferenceConfig, OptionsConfig
       CollectConfig, StageConfig, StoreConfig, PurgeConfig, Config,
       DEFAULT_DEVICE_TYPE, DEFAULT_MEDIA_TYPE, DEFAULT_CAPACITY_MODE, 
       VALID_DEVICE_TYPES, VALID_MEDIA_TYPES, VALID_CAPACITY_MODES

@var DEFAULT_DEVICE_TYPE: The default device type.
@var DEFAULT_MEDIA_TYPE: The default media type.
@var DEFAULT_CAPACITY_MODE: The default capacity mode.
@var VALID_DEVICE_TYPES: List of valid device types.
@var VALID_MEDIA_TYPES: List of valid media types.
@var VALID_CAPACITY_MODES: List of valid capacity modes.

@author: Kenneth J. Pronovici <pronovic@ieee.org>
"""

########################################################################
# Imported modules
########################################################################

# System modules
import os
import logging

# XML-related modules
from xml.dom.ext.reader import PyExpat
from xml.xpath import Evaluate
from xml.parsers.expat import ExpatError
from xml.dom.minidom import getDOMImplementation
from xml.dom.minidom import parseString
from xml.dom.ext import PrettyPrint

# Cedar Backup modules
from CedarBackup2.writer import validateScsiId, validateDriveSpeed
from CedarBackup2.util import UnorderedList, AbsolutePathList, ObjectTypeList


########################################################################
# Module-wide constants and variables
########################################################################

logger = logging.getLogger("CedarBackup2.config")

DEFAULT_DEVICE_TYPE   = "cdwriter"
DEFAULT_MEDIA_TYPE    = "cdrw-74"
DEFAULT_CAPACITY_MODE = "fail"

VALID_DEVICE_TYPES    = [ "cdwriter", ]
VALID_MEDIA_TYPES     = [ "cdr-74", "cdrw-74", "cdr-80", "cdrw-80", ]
VALID_CAPACITY_MODES  = [ "fail", "discard", "overwrite", "rebuild", "rewrite", ]


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
      - The collect mode must be one of C{"daily"}, C{"weekly"} or C{"incr"}.  
      - The archive mode must be one of C{"tar"}, C{"targz"} or C{"tarbz2"}.
      - The ignore file must be a non-empty string.

   For the C{absoluteExcludePaths} list, validation is accomplished through the
   L{util.AbsolutePathList} list implementation that overrides common list
   methods and transparently does the absolute path validation for us.

   @note: Lists within this class are "unordered" for equality comparisons.

   @sort: absolutePath, collectMode, archiveMode, ignoreFile, absoluteExcludePaths, relativeExcludePaths, excludePatterns
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

   def __cmp__(self, other):
      """
      Definition of equals operator for this class.
      Lists within this class are "unordered" for equality comparisons.
      @param other: Other object to compare to.
      @return: -1/0/1 depending on whether self is C{<}, C{=} or C{>} other.
      """
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
      """
      if value is not None:
         if not os.path.isabs(value):
            raise ValueError("Absolute path must be, er, an absolute path.")
      self._absolutePath = value

   def _getAbsolutePath(self):
      """
      Property target used to get the absolute path.
      """
      return self._absolutePath

   def _setCollectMode(self, value):
      """
      Property target used to set the collect mode.
      If not C{None}, the mode must be one of C{"daily"}, C{"weekly"} or C{"incr"}.
      @raise ValueError: If the value is not valid.
      """
      if value is not None:
         if value not in ["daily", "weekly", "incr", ]:
            raise ValueError("Collect mode must be one of \"daily\", \"weekly\" or \"incr\".")
      self._collectMode = value

   def _getCollectMode(self):
      """
      Property target used to get the collect mode.
      """
      return self._collectMode

   def _setArchiveMode(self, value):
      """
      Property target used to set the archive mode.
      If not C{None}, the mode must be one of C{"tar"}, C{"targz"} or C{"tarbz2"}.
      @raise ValueError: If the value is not valid.
      """
      if value is not None:
         if value not in ["daily", "weekly", "incr", ]:
            raise ValueError("Archive mode must be one of \"daily\", \"weekly\" or \"incr\".")
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
         self._absoluteExcludePaths = AbsolutePathList()
         self._absoluteExcludePaths.extend(value)

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
         self._relativeExcludePaths = UnorderedList()
         self._relativeExcludePaths.extend(value)

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
         self._excludePatterns = UnorderedList()
         self._excludePatterns.extend(value)

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

   @sort: absolutePath, retainDays
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

   def __cmp__(self, other):
      """
      Definition of equals operator for this class.
      @param other: Other object to compare to.
      @return: -1/0/1 depending on whether self is C{<}, C{=} or C{>} other.
      """
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
      """
      if value is not None:
         if not os.path.isabs(value):
            raise ValueError("Absolute path must, er, be an absolute path.")
      self._absolutePath = value

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
         return self._retainDays

   def _getRetainDays(self):
      """
      Property target used to get the absolute path.
      """
      return self._retainDays

   absolutePath = property(_getAbsolutePath, _setAbsolutePath, None, "Absolute path of directory to purge.")
   retainDays = property(_getAbsolutePath, _setAbsolutePath, None, "Number of days content within directory should be retained.")


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
   
   @sort: name, collectDir
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

   def __cmp__(self, other):
      """
      Definition of equals operator for this class.
      @param other: Other object to compare to.
      @return: -1/0/1 depending on whether self is C{<}, C{=} or C{>} other.
      """
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
      """
      if value is not None:
         if not os.path.isabs(value):
            raise ValueError("Collect directory must be an absolute path.")
      self._collectDir = value

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

   @sort: name, collectDir, remoteUser, rcpCommand
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

   def __cmp__(self, other):
      """
      Definition of equals operator for this class.
      @param other: Other object to compare to.
      @return: -1/0/1 depending on whether self is C{<}, C{=} or C{>} other.
      """
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
      """
      if value is not None:
         if not os.path.isabs(value):
            raise ValueError("Collect directory must be an absolute path.")
      self._collectDir = value

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

   @sort: author, revision, description, generator
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

   def __cmp__(self, other):
      """
      Definition of equals operator for this class.
      @param other: Other object to compare to.
      @return: -1/0/1 depending on whether self is C{<}, C{=} or C{>} other.
      """
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

   @sort: startingDay, workingDir, backupUser, backupGroup, rcpCommand
   """

   def __init__(self, startingDay=None, workingDir=None, backupUser=None, backupGroup=None, rcpCommand=None):
      """
      Constructor for the C{OptionsConfig} class.

      @param startingDay: Day that starts the week.
      @param workingDir: Working (temporary) directory to use for backups.
      @param backupUser: Effective user that backups should run as.
      @param backupGroup: Effective group that backups should run as.
      @param rcpCommand: Default rcp-compatible copy command for staging.

      @raise ValueError: If one of the values is invalid.
      """
      self._startingDay = None
      self._workingDir = None
      self._backupUser = None
      self._backupGroup = None
      self._rcpCommand = None
      self.startingDay = startingDay
      self.workingDir = workingDir
      self.backupUser = backupUser
      self.backupGroup = backupGroup
      self.rcpCommand = rcpCommand

   def __cmp__(self, other):
      """
      Definition of equals operator for this class.
      @param other: Other object to compare to.
      @return: -1/0/1 depending on whether self is C{<}, C{=} or C{>} other.
      """
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
            raise ValueError("Starting day must be and English day of the week, i.e. \"monday\".")
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
      """
      if value is not None:
         if not os.path.isabs(value):
            raise ValueError("Working directory must be an absolute path.")
      self._workingDir = value

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

   startingDay = property(_getStartingDay, _setStartingDay, None, "Day that starts the week.")
   workingDir = property(_getWorkingDir, _setWorkingDir, None, "Working (temporary) directory to use for backups.")
   backupUser = property(_getBackupUser, _setBackupUser, None, "Effective user that backups should run as.")
   backupGroup = property(_getBackupGroup, _setBackupGroup, None, "Effective group that backups should run as.")
   rcpCommand = property(_getRcpCommand, _setRcpCommand, None, "Default rcp-compatible copy command for staging.")


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
      - The collect mode must be one of C{"daily"}, C{"weekly"} or C{"incr"}.  
      - The archive mode must be one of C{"tar"}, C{"targz"} or C{"tarbz2"}.
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

   @sort: targetDir, collectMode, archiveMode, ignoreFile, absoluteExcludePaths, excludePatterns, collectDirs
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

   def __cmp__(self, other):
      """
      Definition of equals operator for this class.
      Lists within this class are "unordered" for equality comparisons.
      @param other: Other object to compare to.
      @return: -1/0/1 depending on whether self is C{<}, C{=} or C{>} other.
      """
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
      """
      if value is not None:
         if not os.path.isabs(value):
            raise ValueError("Target directory must be an absolute path.")
      self._targetDir = value

   def _getTargetDir(self):
      """
      Property target used to get the target directory.
      """
      return self._targetDir

   def _setCollectMode(self, value):
      """
      Property target used to set the collect mode.
      If not C{None}, the mode must be one of C{"daily"}, C{"weekly"} or C{"incr"}.
      @raise ValueError: If the value is not valid.
      """
      if value is not None:
         if value not in ["daily", "weekly", "incr", ]:
            raise ValueError("Collect mode must be one of \"daily\", \"weekly\" or \"incr\".")
      self._collectMode = value

   def _getCollectMode(self):
      """
      Property target used to get the collect mode.
      """
      return self._collectMode

   def _setArchiveMode(self, value):
      """
      Property target used to set the archive mode.
      If not C{None}, the mode must be one of C{"tar"}, C{"targz"} or C{"tarbz2"}.
      @raise ValueError: If the value is not valid.
      """
      if value is not None:
         if value not in ["daily", "weekly", "incr", ]:
            raise ValueError("Archive mode must be one of \"daily\", \"weekly\" or \"incr\".")
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
         self._absoluteExcludePaths = AbsolutePathList()
         self._absoluteExcludePaths.extend(value)

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
         self._excludePatterns = UnorderedList()
         self._excludePatterns.extend(value)

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
         self._collectDirs = ObjectTypeList(CollectDir, "CollectDir")
         self._collectDirs.extend(value)

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

   @sort: targetDir, localPeers, remotePeers
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

   def __cmp__(self, other):
      """
      Definition of equals operator for this class.
      Lists within this class are "unordered" for equality comparisons.
      @param other: Other object to compare to.
      @return: -1/0/1 depending on whether self is C{<}, C{=} or C{>} other.
      """
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
      """
      if value is not None:
         if not os.path.isabs(value):
            raise ValueError("Target directory must be an absolute path.")
      self._targetDir = value

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
         self._localPeers = ObjectTypeList(LocalPeer, "LocalPeer")
         self._localPeers.extend(value)

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
         self._remotePeers = ObjectTypeList(RemotePeer, "RemotePeer")
         self._remotePeers.extend(value)

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
      - The media type must be one of the values in C{VALID_MEDIA_TYPES}.
      - The device type must be one of the values in C{VALID_DEVICE_TYPES}.
      - The capacity mode must be one of the values in C{VALID_CAPACITY_MODES}.
      - The device path must be an absolute path.
      - The SCSI id must be in the form specified by L{writer.validateScsiId}.
      - The drive speed must be an integer >= 1

   The device type field mostly exists for planned future extensions, such as
   support for DVD writers.

   @sort: sourceDir, mediaType, deviceType, devicePath, deviceScsiId, 
          driveSpeed, checkData, safeOverwrite, capacityMode
   """

   def __init__(self, sourceDir=None, mediaType=None, deviceType=None, 
                devicePath=None, deviceScsiId=None, driveSpeed=None,
                checkData=False, safeOverwrite=False, capacityMode=None):
      """
      Constructor for the C{StoreConfig} class.

      @param sourceDir: Directory whose contents should be written to media.
      @param mediaType: Type of the media (see notes above).
      @param deviceType: Type of the device (optional, see notes above).
      @param devicePath: Filesystem device name for writer device, i.e. C{/dev/cdrw}.
      @param deviceScsiId: SCSI id for writer device, i.e. C{[ATA]:scsibus,target,lun}.
      @param driveSpeed: Speed of the drive, i.e. C{2} for 2x drive, etc.
      @param checkData: Indicates whether resulting image should be validated.
      @param safeOverwrite: Indicates whether safe-overwrite checking is enabled.
      @param capacityMode: Controls behavior when media runs out of capacity.

      @raise ValueError: If one of the values is invalid.
      """
      self._sourceDir = None
      self._mediaType = None
      self._deviceType = None
      self._devicePath = None
      self._deviceScsiId = None
      self._driveSpeed = None
      self._checkData = None
      self._safeOverwrite = None
      self._capacityMode = None
      self.sourceDir = sourceDir
      self.mediaType = mediaType
      self.deviceType = deviceType
      self.devicePath = devicePath
      self.deviceScsiId = deviceScsiId
      self.driveSpeed = driveSpeed
      self.checkData = checkData
      self.safeOverwrite = safeOverwrite
      self.capacityMode = capacityMode

   def __cmp__(self, other):
      """
      Definition of equals operator for this class.
      @param other: Other object to compare to.
      @return: -1/0/1 depending on whether self is C{<}, C{=} or C{>} other.
      """
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
      if self._safeOverwrite != other._safeOverwrite:
         if self._safeOverwrite < other._safeOverwrite:
            return -1
         else:
            return 1
      if self._capacityMode != other._capacityMode:
         if self._capacityMode < other._capacityMode:
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
      """
      if value is not None:
         if not os.path.isabs(value):
            raise ValueError("Source directory must be an absolute path.")
      self._sourceDir = value

   def _getSourceDir(self):
      """
      Property target used to get the source directory.
      """
      return self._sourceDir

   def _setMediaType(self, value):
      """
      Property target used to set the media type.
      The value must be one of C{VALID_MEDIA_TYPES}.
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
      The value must be one of C{VALID_DEVICE_TYPES}.
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
      """
      if value is not None:
         if not os.path.isabs(value):
            raise ValueError("Device path must be an absolute path.")
      self._devicePath = value

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
         self._scsiId = None
      else:
         self._scsiId = validateScsiId(value)

   def _getDeviceScsiId(self):
      """
      Property target used to get the SCSI id.
      """
      return self._scsiId

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

   def _setSafeOverwrite(self, value):
      """
      Property target used to set the safe overwrite flag.
      No validations, but we normalize the value to C{True} or C{False}.
      """
      if value:
         self._safeOverwrite = True
      else:
         self._safeOverwrite = False

   def _getSafeOverwrite(self):
      """
      Property target used to get the safe overwrite flag.
      """
      return self._safeOverwrite

   def _setCapacityMode(self, value):
      """
      Property target used to set the capacity mode.
      The value must be one of C{VALID_CAPACITY_MODES}.
      @raise ValueError: If the value is not valid.
      """
      if value is not None:
         if value not in VALID_CAPACITY_MODES:
            raise ValueError("Capacity mode must be one of %s." % VALID_CAPACITY_MODES)
      self._capacityMode = value

   def _getCapacityMode(self):
      """
      Property target used to get the capacity mode.
      """
      return self._capacityMode

   sourceDir = property(_getSourceDir, _setSourceDir, None, "Directory whose contents should be written to media.")
   mediaType = property(_getMediaType, _setMediaType, None, "Type of the media (see notes above).")
   deviceType = property(_getDeviceType, _setDeviceType, None, "Type of the device (optional, see notes above).")
   devicePath = property(_getDevicePath, _setDevicePath, None, "Filesystem device name for writer device.")
   deviceScsiId = property(_getDeviceScsiId, _setDeviceScsiId, None, "SCSI id for writer device.")
   driveSpeed = property(_getDriveSpeed, _setDriveSpeed, None, "Speed of the drive.")
   checkData = property(_getCheckData, _setCheckData, None, "Indicates whether resulting image should be validated.")
   safeOverwrite = property(_getSafeOverwrite, _setSafeOverwrite, None, "Indicates whether safe-overwrite checking is enabled.")
   capacityMode = property(_getCapacityMode, _setCapacityMode, None, "Controls behavior when media runs out of capacity.")


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

   @sort: purgeDirs
   """

   def __init__(self, purgeDirs=None):
      """
      Constructor for the C{Purge} class.
      @param purgeDirs: List of purge directories.
      @raise ValueError: If one of the values is invalid.
      """
      self._purgeDirs = None
      self.purgeDirs = purgeDirs

   def __cmp__(self, other):
      """
      Definition of equals operator for this class.
      Lists within this class are "unordered" for equality comparisons.
      @param other: Other object to compare to.
      @return: -1/0/1 depending on whether self is C{<}, C{=} or C{>} other.
      """
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
         self._purgeDirs = ObjectTypeList(PurgeDir, "PurgeDir")
         self._purgeDirs.extend(value)

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
   configuration file.  It is intended to be the only Python- language
   interface to Cedar Backup configuration on disk for both Cedar Backup itself
   and for external applications.

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

   @sort: __init__, extractXml, validate, reference, options, collect, stage, store, purge
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
      self._options = None
      self._collect = None
      self._stage = None
      self._store = None
      self._purge = None
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
      if self._reference != other._reference:
         if self._reference < other._reference:
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

   reference = property(_getReference, _getReference, None, "Reference configuration in terms of a C{ReferenceConfig} object.")
   options = property(_getOptions, _getOptions, None, "Options configuration in terms of a C{OptionsConfig} object.")
   collect = property(_getCollect, _getCollect, None, "Collect configuration in terms of a C{CollectConfig} object.")
   stage = property(_getStage, _getStage, None, "Stage configuration in terms of a C{StageConfig} object.")
   store = property(_getStore, _getStore, None, "Store configuration in terms of a C{StoreConfig} object.")
   purge = property(_getPurge, _getPurge, None, "Purge configuration in terms of a C{PurgeConfig} object.")


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

   def validate(self, requireOneAction=True, requireReference=False, requireOptions=True, 
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


   ########################################
   # Internal methods used for parsing XML
   ########################################

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

      @param xmlData: XML data to be parsed
      @type xmlData: String data

      @raise ValueError: If the XML cannot be successfully parsed.
      """
      try:
         xmlDom = PyExpat.Reader().fromString(xmlData)
         self._reference = Config._parseReference(xmlDom)
         self._options = Config._parseOptions(xmlDom)
         self._collect = Config._parseCollect(xmlDom)
         self._stage = Config._parseStage(xmlDom)
         self._store = Config._parseStore(xmlDom)
         self._purge = Config._parsePurge(xmlDom)
      except (IOError, ExpatError), e:
         raise ValueError("Unable to parse XML document: %s" % e)

   def _parseReference(xmlDom):
      """
      Parses a reference configuration section.
      
      We read the following fields::

         author         //cb_config/reference/author
         revision       //cb_config/reference/revision
         description    //cb_config/reference/description
         generator      //cb_config/reference/generator

      @return: C{ReferenceConfig} object or C{None} if the section does not exist.
      @raise ValueError: If some filled-in value is invalid.
      """
      reference = None
      if Config._nodeExists(xmlDom, "//cb_config/reference"):
         reference = ReferenceConfig()
         reference.author = Config._readString(xmlDom, "//cb_config/reference/author")
         reference.revision = Config._readString(xmlDom, "//cb_config/reference/revision")
         reference.description = Config._readString(xmlDom, "//cb_config/reference/description")
         reference.generator = Config._readString(xmlDom, "//cb_config/reference/generator")
      return reference
   _parseReference = staticmethod(_parseReference)

   def _parseOptions(xmlDom):
      """
      Parses a options configuration section.

      We read the following fields::

         startingDay    //cb_config/options/starting_day
         workingDir     //cb_config/options/working_dir
         backupUser     //cb_config/options/backup_user
         backupGroup    //cb_config/options/backup_group
         rcpCommand     //cb_config/options/rcp_command

      @return: C{OptionsConfig} object or C{None} if the section does not exist.
      @raise ValueError: If some filled-in value is invalid.
      """
      options = None
      if Config._nodeExists(xmlDom, "//cb_config/options"):
         options = OptionsConfig()
         options.startingDay = Config._readString(xmlDom, "//cb_config/options/starting_day")
         options.workingDir = Config._readString(xmlDom, "//cb_config/options/working_dir")
         options.backupUser = Config._readString(xmlDom, "//cb_config/options/backup_user")
         options.backupGroup = Config._readString(xmlDom, "//cb_config/options/backup_group")
         options.rcpCommand = Config._readString(xmlDom, "//cb_config/options/rcp_command")
      return options
   _parseOptions = staticmethod(_parseOptions)

   def _parseCollect(xmlDom):
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
   
      The individual collect directory entries are parsed by
      L{_parseCollectDir}.

      @return: C{CollectConfig} object or C{None} if the section does not exist.
      @raise ValueError: If some filled-in value is invalid.
      """
      collect = None
      if Config._nodeExists(xmlDom, "//cb_config/collect"):
         collect = CollectConfig()
         collect.targetDir = Config._readString(xmlDom, "//cb_config/collect/collect_dir")
         collect.collectMode = Config._readString(xmlDom, "//cb_config/collect/mode")
         collect.archiveMode = Config._readString(xmlDom, "//cb_config/collect/archive_mode")
         collect.ignoreFile = Config._readString(xmlDom, "//cb_config/collect/ignore_file")
         collect.absoluteExcludePaths = Config._readList(xmlDom, "//cb_config/collect/exclude/abs_path", Config._readString)
         collect.excludePatterns = Config._readList(xmlDom, "//cb_config/collect/exclude/pattern", Config._readString)
         collect.collectDirs = Config._readList(xmlDom, "//cb_config/collect/dir", Config._parseCollectDir)
      return collect
   _parseCollect = staticmethod(_parseCollect)

   def _parseStage(xmlDom):
      """
      Parses a stage configuration section.

      We read the following individual fields::

         targetDir      //cb_config/stage/staging_dir

      We also read groups of the following items, one list element per
      item::

         localPeers     //cb_config/stage/peer
         remotePeers    //cb_config/stage/peer

      The individual peer entries are parsed by L{_parseLocalPeer} and
      L{_parseRemotePeer}.  Since remote and local peers each have the same
      expression (they're both in C{peer} nodes), these functions each ignore
      entries matching the expression which aren't of the correct type.

      @return: C{StageConfig} object or C{None} if the section does not exist.
      @raise ValueError: If some filled-in value is invalid.
      """
      stage = None
      if Config._nodeExists(xmlDom, "//cb_config/stage"):
         stage = StageConfig()
         stage.targetDir = Config._readString(xmlDom, "//cb_config/stage/staging_dir")
         stage.localPeers = Config._readList(xmlDom, "//cb_config/stage/peer", Config._parseLocalPeer)      # ignores remote
         stage.remotePeers = Config._readList(xmlDom, "//cb_config/stage/peer", Config._parseRemotePeer)    # ignores local
      return stage
   _parseStage = staticmethod(_parseStage)

   def _parseStore(xmlDom):
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
         safeOverwrite     //cb_config/store/safe_overwrite
         capacityMode      //cb_config/store/capacity_mode

      @return: C{StoreConfig} object or C{None} if the section does not exist.
      @raise ValueError: If some filled-in value is invalid.
      """
      store = None
      if Config._nodeExists(xmlDom, "//cb_config/store"):
         store = StoreConfig()
         store.sourceDir = Config._readString(xmlDom,  "//cb_config/store/source_dir")
         store.mediaType = Config._readString(xmlDom,  "//cb_config/store/media_type")
         store.deviceType = Config._readString(xmlDom,  "//cb_config/store/device_type")
         store.devicePath = Config._readString(xmlDom,  "//cb_config/store/target_device")
         store.deviceScsiId = Config._readString(xmlDom,  "//cb_config/store/target_scsi_id")
         store.driveSpeed = Config._readInteger(xmlDom, "//cb_config/store/drive_speed")
         store.checkData = Config._readInteger(xmlDom, "//cb_config/store/check_data")
         store.safeOverwrite = Config._readBoolean(xmlDom, "//cb_config/store/safe_overwrite")
         store.capacityMode = Config._readString(xmlDom,  "//cb_config/store/capacity_mode")
      return store
   _parseStore = staticmethod(_parseStore)

   def _parsePurge(xmlDom):
      """
      Parses a purge configuration section.

      We read groups of the following items, one list element per
      item::

         purgeDirs     //cb_config/purge/dir

      The individual directory entries are parsed by L{_parsePurgeDir}.

      @return: C{PurgeConfig} object or C{None} if the section does not exist.
      @raise ValueError: If some filled-in value is invalid.
      """
      purge = None
      if Config._nodeExists(xmlDom, "//cb_config/purge"):
         purge = PurgeConfig()
         purge.purgeDirs = Config._readList(xmlDom, "//cb_config/purge/dir", Config._parsePurgeDir)
      return purge
   _parsePurge = staticmethod(_parsePurge)

   def _parseCollectDir(xmlDom, baseExpr):
      """
      Reads a C{CollectDir} object from the DOM tree using the specified expression.

      This method takes a simplified expression, i.e. C{"//one/two/three"}.  

      We read the following individual fields::

         absolutePath            <baseExpr>/abs_path
         collectMode             <baseExpr>/mode
         archiveMode             <baseExpr>/archive_mode
         ignoreFile              <baseExpr>/ignore_file

      We also read groups of the following items, one list element per
      item::

         absoluteExcludePaths    <baseExpr>/exclude/abs_path
         relativeExcludePaths    <baseExpr>/exclude/rel_path
         excludePatterns         <baseExpr>/exclude/pattern

      @param xmlDom: DOM tree to search within.
      @param baseExpr: Base XPath expression describing location to read.

      @return: C{CollectDir} object based on data at location, or C{None} if the node is not found.
      @raise ValueError: If the data at the location can't be read
      """
      collectDir = None
      if Config._nodeExists(xmlDom, baseExpr):
         collectDir = CollectDir()
         collectDir.absolutePath = Config._readString(xmlDom, "%s/abs_path" % baseExpr)
         collectDir.collectMode = Config._readString(xmlDom, "%s/mode" % baseExpr)
         collectDir.archiveMode = Config._readString(xmlDom, "%s/archive_mode" % baseExpr)
         collectDir.ignoreFile = Config._readString(xmlDom, "%s/ignore_file" % baseExpr)
         collectDir.absoluteExcludePaths = Config._readList(xmlDom, "%s/exclude/abs_path" % baseExpr, Config._readString)
         collectDir.relativeExcludePaths = Config._readList(xmlDom, "%s/exclude/rel_path" % baseExpr, Config._readString)
         collectDir.excludePatterns = Config._readList(xmlDom, "%s/exclude/pattern" % baseExpr, Config._readString)
      return collectDir
   _parseCollectDir = staticmethod(_parseCollectDir)

   def _parsePurgeDir(xmlDom, baseExpr):
      """
      Reads a C{PurgeDir} object from the DOM tree using the specified expression.

      This method takes a simplified expression, i.e. C{"//one/two/three"}.  

      We read the following individual fields::

         absolutePath            <baseExpr>/abs_path
         retainDays              <baseExpr>/retain_days

      @param xmlDom: DOM tree to search within.
      @param baseExpr: Base XPath expression describing location to read.

      @return: C{PurgeDir} object based on data at location, or C{None} if the node is not found.
      @raise ValueError: If the data at the location can't be read
      """
      purgeDir = None
      if Config._nodeExists(xmlDom, baseExpr):
         purgeDir = PurgeDir()
         purgeDir.absolutePath = Config._readString(xmlDom, "%s/abs_path" % baseExpr)
         purgeDir.retainDays = Config._readInteger(xmlDom, "%s/retain_days" % baseExpr)
      return purgeDir
   _parsePurgeDir = staticmethod(_parsePurgeDir)

   def _parseLocalPeer(xmlDom, baseExpr):
      """
      Reads a C{LocalPeer} object from the DOM tree using the specified expression.

      This method takes a simplified expression, i.e. C{"//one/two/three"}.  

      We read the following individual fields::

         name        <baseExpr>/name
         collectDir  <baseExpr>/collect_dir

      Additionally, the value in C{<baseDir>/type} is used to determine whether
      this entry is a local peer.  If the type is C{"local"}, it's a local
      peer.  Any other kinds of peers are ignored.

      @param xmlDom: DOM tree to search within.
      @param baseExpr: Base XPath expression describing location to read.

      @return: C{LocalPeer} object based on data at location, or C{None} if not a local peer.
      @raise ValueError: If the data at the location can't be read
      """
      localPeer = None
      if Config._nodeExists(xmlDom, baseExpr):
         peerType = Config._readString(xmlDom, "%s/type" % baseExpr)
         if peerType == "local":
            localPeer = LocalPeer()
            localPeer.name = Config._readString(xmlDom, "%s/name" % baseExpr)
            localPeer.collectDir = Config._readString(xmlDom, "%s/collect_dir" % baseExpr)
      return localPeer
   _parseLocalPeer = staticmethod(_parseLocalPeer)

   def _parseRemotePeer(xmlDom, baseExpr):
      """
      Reads a C{RemotePeer} object from the DOM tree using the specified expression.

      This method takes a simplified expression, i.e. C{"//one/two/three"}.  

      We read the following individual fields::

         name        <baseExpr>/name
         collectDir  <baseExpr>/collect_dir
         remoteUser  <baseExpr>/backup_user
         rcpCommand  <baseExpr>/rcp_command

      Additionally, the value in C{<baseDir>/type} is used to determine whether
      this entry is a remote peer.  If the type is C{"remote"}, it's a remote
      peer.  Any other kinds of peers are ignored.

      @param xmlDom: DOM tree to search within.
      @param baseExpr: Base XPath expression describing location to read.

      @return: C{RemotePeer} object based on data at location, or C{None} if not a remote peer.
      @raise ValueError: If the data at the location can't be read
      """
      remotePeer = None
      if Config._nodeExists(xmlDom, baseExpr):
         peerType = Config._readString(xmlDom, "%s/type" % baseExpr)
         if peerType == "remote":
            remotePeer = RemotePeer()
            remotePeer.name = Config._readString(xmlDom, "%s/name" % baseExpr)
            remotePeer.collectDir = Config._readString(xmlDom, "%s/collect_dir" % baseExpr)
            remotePeer.remoteUser = Config._readString(xmlDom, "%s/backup_user" % baseExpr)
            remotePeer.rcpCommand = Config._readString(xmlDom, "%s/rcp_command" % baseExpr)
      return remotePeer
   _parseRemotePeer = staticmethod(_parseRemotePeer)

   def _nodeExists(xmlDom, expr):
      """
      Indicates whether a particular location exists in a DOM tree.
      This method takes a simplified expression, i.e. C{"//one/two/three"}.
      @param xmlDom: DOM tree to search within.
      @param expr: XPath expression describing location to read.
      @return: Boolean true/false depending on whether node exists.
      """
      result = Evaluate("string(%s)" % expr, xmlDom.documentElement)
      if result == []:
         return False
      return True
   _nodeExists = staticmethod(_nodeExists)

   def _readString(xmlDom, expr):
      """
      Reads a string from the DOM tree using the specified expression.
      This method takes a simplified expression, i.e. C{"//one/two/three"}.
      @param xmlDom: DOM tree to search within.
      @param expr: XPath expression describing location to read.
      @return: String value at location specified by C{expr}, or C{None}.
      """
      result = Evaluate("string(%s)" % expr, xmlDom.documentElement)
      if len(result) >= 1:
         return result[0]
      else:
         return None
   _readString = staticmethod(_readString)

   def _readInteger(xmlDom, expr):
      """
      Reads an integer from the DOM tree using the specified expression.
      This method takes a simplified expression, i.e. C{"//one/two/three"}.
      @param xmlDom: DOM tree to search within.
      @param expr: XPath expression describing location to read.
      @return: Integer value at location specified by C{expr}, or C{None}.
      @raise ValueError: If the string at the location can't be converted to an integer.
      """
      result = Config._readString(xmlDom, expr)
      if result is None:
         return None
      else:
         return int(result)
   _readInteger = staticmethod(_readInteger)

   def _readBoolean(xmlDom, expr):
      """
      Reads a boolean value from the DOM tree using the specified expression.
      This method takes a simplified expression, i.e. C{"//one/two/three"}.
      Booleans must be one-character strings: C{"Y"}, C{"y"}, C{"N"} or C{"n"}.
      @param expr: XPath expression describing location to read.
      @return: Boolean value at location specified by C{expr}, or C{None}.
      @raise ValueError: If the string at the location can't be converted to a boolean.
      """
      result = Config._readString(xmlDom, expr)
      if result is None:
         return None
      else:
         if len(result) != 1 or result not in ["Y", "y", "N", "n", ]:
            raise ValueError("Boolean values must be ['Y', 'y', 'N', 'n'].")
         if result in ['Y', 'y']:
            return True
         else:
            return False
   _readBoolean = staticmethod(_readBoolean)

   def _readList(xmlDom, baseExpr, func):
      """
      Reads a list of elements with the given expression, using C{func}.

      If there are no elements matching the expression, then C{[]} is returned.
      Otherwise, C{func} will be called once (with a valid expression) for each
      elements matching the base expression.  

      The C{func} must have the same form as L{_readString}.  If it returns
      C{None}, then that particular result will be ignored.  This gives the
      function a way to say "whoops, this location doesn't apply to me" without
      throwing an exception and killing the parse process.

      @param xmlDom: DOM tree to search within.
      @param baseExpr: Base XPath expression describing location to read.
      @param func: Function to call to read an individual item.

      @return: List of elements, one per item matching the base expression.
      """
      elements = []
      result = Evaluate("string(%s)" % baseExpr, xmlDom.documentElement)
      indices = range(1, len(result)+1)
      for i in indices:
         result = func(xmlDom, "%s[%d]" % (baseExpr, i))
         if result is not None:
            elements.append(result)
      return elements
   _readList = staticmethod(_readList)


   ###########################################
   # Internal methods used for generating XML
   ###########################################

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
      Config._addOptions(xmlDom, parentNode, self.options)
      Config._addCollect(xmlDom, parentNode, self.collect)
      Config._addStage(xmlDom, parentNode, self.stage)
      Config._addStore(xmlDom, parentNode, self.store)
      Config._addPurge(xmlDom, parentNode, self.purge)
      xmlData = PrettyPrint(xmlDom)
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

      If C{referenceConfig} is C{None}, then an empty <reference> container
      will be added.

      @param xmlDom: DOM tree as from C{impl.createDocument()}.
      @param parentNode: Parent that the section should be appended to.
      @param referenceConfig: Reference configuration section to be added to the document.
      """
      sectionNode = Config._addContainerNode(xmlDom, parentNode, "reference")
      if referenceConfig is not None:
         Config._addStringNode(xmlDom, sectionNode, "author", referenceConfig.author)
         Config._addStringNode(xmlDom, sectionNode, "revision", referenceConfig.revision)
         Config._addStringNode(xmlDom, sectionNode, "description", referenceConfig.description)
         Config._addStringNode(xmlDom, sectionNode, "generator", referenceConfig.generator)
   _addReference = staticmethod(_addReference)

   def _addOptions(xmlDom, parentNode, optionsConfig):
      """
      Adds a <options> configuration section as the next child of a parent.

      We add the following fields to the document::

         startingDay    //cb_config/options/starting_day
         workingDir     //cb_config/options/working_dir
         backupUser     //cb_config/options/backup_user
         backupGroup    //cb_config/options/backup_group
         rcpCommand     //cb_config/options/rcp_command

      If C{optionsConfig} is C{None}, then an empty <options> container will be
      added.

      @param xmlDom: DOM tree as from C{impl.createDocument()}.
      @param parentNode: Parent that the section should be appended to.
      @param optionsConfig: Options configuration section to be added to the document.
      """
      sectionNode = Config._addContainerNode(xmlDom, parentNode, "options")
      if optionsConfig is not None:
         Config._addStringNode(xmlDom, sectionNode, "starting_day", optionsConfig.startingDay)
         Config._addStringNode(xmlDom, sectionNode, "working_dir", optionsConfig.workingDir)
         Config._addStringNode(xmlDom, sectionNode, "backup_user", optionsConfig.backupUser)
         Config._addStringNode(xmlDom, sectionNode, "backup_group", optionsConfig.backupGroup)
         Config._addStringNode(xmlDom, sectionNode, "rcp_command", optionsConfig.rcpCommand)
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
   
      If C{collectConfig} is C{None}, then an empty <collect> container will be
      added.

      @param xmlDom: DOM tree as from C{impl.createDocument()}.
      @param parentNode: Parent that the section should be appended to.
      @param collectConfig: Collect configuration section to be added to the document.
      """
      sectionNode = Config._addContainerNode(xmlDom, parentNode, "collect")
      if collectConfig is not None:
         Config._addStringNode(xmlDom, sectionNode, "collect_dir", collectConfig.targetDir)
         Config._addStringNode(xmlDom, sectionNode, "collect_mode", collectConfig.collectMode)
         Config._addStringNode(xmlDom, sectionNode, "archive_mode", collectConfig.archiveMode)
         Config._addStringNode(xmlDom, sectionNode, "ignore_file", collectConfig.ignoreFile)
         excludeNode = Config._addContainerNode(xmlDom, sectionNode, "exclude")
         for absolutePath in collectConfig.absoluteExcludePaths:
            Config._addStringNode(xmlDom, excludeNode, "abs_path", absolutePath)
         for pattern in collectConfig.excludePatterns:
            Config._addStringNode(xmlDom, excludeNode, "pattern", pattern)
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

      If C{stageConfig} is C{None}, then an empty <stage> container will be
      added.

      @param xmlDom: DOM tree as from C{impl.createDocument()}.
      @param parentNode: Parent that the section should be appended to.
      @param stageConfig: Stage configuration section to be added to the document.
      """
      sectionNode = Config._addContainerNode(xmlDom, parentNode, "stage")
      if stageConfig is not None:
         Config._addStringNode(xmlDom, sectionNode, "staging_dir", stageConfig.targetDir)
         for localPeer in stageConfig.localPeers:
            Config._addLocalPeer(xmlDom, sectionNode, localPeer)
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
         safeOverwrite     //cb_config/store/safe_overwrite
         capacityMode      //cb_config/store/capacity_mode

      If C{storeConfig} is C{None}, then an empty <store> container will be
      added.

      @param xmlDom: DOM tree as from C{impl.createDocument()}.
      @param parentNode: Parent that the section should be appended to.
      @param storeConfig: Store configuration section to be added to the document.
      """
      sectionNode = Config._addContainerNode(xmlDom, parentNode, "store")
      if storeConfig is not None:
         Config._addStringNode(xmlDom, sectionNode, "sourceDir", storeConfig.sourceDir)
         Config._addStringNode(xmlDom, sectionNode, "mediaType", storeConfig.mediaType)
         Config._addStringNode(xmlDom, sectionNode, "deviceType", storeConfig.deviceType)
         Config._addStringNode(xmlDom, sectionNode, "devicePath", storeConfig.devicePath)
         Config._addStringNode(xmlDom, sectionNode, "deviceScsiId", storeConfig.deviceScsiId)
         Config._addIntegerNode(xmlDom, sectionNode, "driveSpeed", storeConfig.driveSpeed)
         Config._addBooleanNode(xmlDom, sectionNode, "checkData", storeConfig.checkData)
         Config._addBooleanNode(xmlDom, sectionNode, "safeOverwrite", storeConfig.safeOverwrite)
         Config._addStringNode(xmlDom, sectionNode, "capacityMode", storeConfig.capacityMode)
   _addStore = staticmethod(_addStore)

   def _addPurge(xmlDom, parentNode, purgeConfig):
      """
      Adds a <purge> configuration section as the next child of a parent.

      We add the following fields to the document::

         purgeDirs     //cb_config/purge/dir

      The individual directory entries are added by L{_addPurgeDir}.

      If C{purgeConfig} is C{None}, then an empty <purge> container will be
      added.

      @param xmlDom: DOM tree as from C{impl.createDocument()}.
      @param parentNode: Parent that the section should be appended to.
      @param purgeConfig: Purge configuration section to be added to the document.
      """
      sectionNode = Config._addContainerNode(xmlDom, parentNode, "purge")
      if purgeConfig is not None:
         for purgeDir in purgeConfig.purgeDirs:
            Config._addPurgeDir(xmlDom, sectionNode, purgeDir)
   _addPurge = staticmethod(_addPurge)

   def _addCollectDir(xmlDom, parentNode, collectDir):
      """
      Adds a collect directory container as the next child of a parent.

      We add the following fields to the document::

         absolutePath            dir/abs_path
         collectMode             dir/mode
         archiveMode             dir/archive_mode
         ignoreFile              dir/ignore_file

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
         sectionNode = Config._addContainerNode(xmlDom, parentNode, "dir")
         Config._addStringNode(xmlDom, sectionNode, "abs_path", collectDir.absolutePath)
         Config._addStringNode(xmlDom, sectionNode, "mode", collectDir.collectMode)
         Config._addStringNode(xmlDom, sectionNode, "archive_mode", collectDir.archiveMode)
         Config._addStringNode(xmlDom, sectionNode, "ignore_file", collectDir.ignoreFile)
         excludeNode = Config._addContainerNode(xmlDom, sectionNode, "exclude")
         for absolutePath in collectDir.absoluteExcludePaths:
            Config._addStringNode(xmlDom, excludeNode, "abs_path", absolutePath)
         for relativePath in collectDir.relativeExcludePaths:
            Config._addStringNode(xmlDom, excludeNode, "rel_path", relativePath)
         for pattern in collectDir.excludePatterns:
            Config._addStringNode(xmlDom, excludeNode, "pattern", pattern)
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
         sectionNode = Config._addContainerNode(xmlDom, parentNode, "peer")
         Config._addStringNode(xmlDom, sectionNode, "name", localPeer.name)
         Config._addStringNode(xmlDom, sectionNode, "collect_dir", localPeer.collectDir)
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
         sectionNode = Config._addContainerNode(xmlDom, parentNode, "peer")
         Config._addStringNode(xmlDom, sectionNode, "name", remotePeer.name)
         Config._addStringNode(xmlDom, sectionNode, "collect_dir", remotePeer.collectDir)
         Config._addStringNode(xmlDom, sectionNode, "backup_user", remotePeer.remoteUser)
         Config._addStringNode(xmlDom, sectionNode, "rcp_command", remotePeer.rcpCommand)
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
         sectionNode = Config._addContainerNode(xmlDom, parentNode, "dir")
         Config._addStringNode(xmlDom, sectionNode, "abs_path", purgeDir.absolutePath)
         Config._addStringNode(xmlDom, sectionNode, "retain_days", purgeDir.retainDays)
   _addPurgeDir = staticmethod(_addPurgeDir)

   def _addContainerNode(xmlDom, parentNode, nodeName):
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
   _addContainerNode = staticmethod(_addContainerNode)

   def _addStringNode(xmlDom, parentNode, nodeName, nodeValue):
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
      containerNode = Config._addContainerNode(xmlDom, parentNode, nodeName)
      if nodeValue is not None:
         textNode = xmlDom.createTextNode(nodeValue)
         containerNode.appendChild(textNode)
      return containerNode
   _addStringNode = staticmethod(_addStringNode)

   def _addIntegerNode(xmlDom, parentNode, nodeName, nodeValue):
      """
      Adds a text node as the next child of a parent, to contain an integer.

      If the C{nodeValue} is None, then the node will be created, but will be
      empty (i.e. will contain no text node child).

      The integer will be converted to a string using "%d".  The result will be
      added to the document via L{_addStringNode}.

      @param xmlDom: DOM tree as from C{impl.createDocument()}.
      @param parentNode: Parent node to create child for.
      @param nodeName: Name of the new container node.
      @param nodeValue: The value to put into the node.
   
      @return: Reference to the newly-created node.
      """
      if nodeValue is None:
         return Config._addStringNode(xmlDom, parentNode, nodeName, None)
      else:
         return Config._addStringNode(xmlDom, parentNode, nodeName, "%d" % nodeValue)
   _addIntegerNode = staticmethod(_addIntegerNode)

   def _addBooleanNode(xmlDom, parentNode, nodeName, nodeValue):
      """
      Adds a text node as the next child of a parent, to contain a boolean.

      If the C{nodeValue} is None, then the node will be created, but will be
      empty (i.e. will contain no text node child).

      Boolean C{True}, or anything else interpreted as C{True} by Python, will
      be converted to a string "Y".  Anything else will be converted to a
      string "N".  The result is added to the document via L{_addStringNode}.

      @param xmlDom: DOM tree as from C{impl.createDocument()}.
      @param parentNode: Parent node to create child for.
      @param nodeName: Name of the new container node.
      @param nodeValue: The value to put into the node.
   
      @return: Reference to the newly-created node.
      """
      if nodeValue is None:
         return Config._addStringNode(xmlDom, parentNode, nodeName, None)
      else:
         if nodeValue:
            return Config._addStringNode(xmlDom, parentNode, nodeName, "Y")
         else:
            return Config._addStringNode(xmlDom, parentNode, nodeName, "N")
   _addBooleanNode = staticmethod(_addBooleanNode)


   ###############################################
   # Internal methods used for validating content
   ###############################################

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

   def _validateOptions(self):
      """
      Validates options configuration.

      All fields must be filled in.  The rcp command is used as a default value
      for all remote peers in the staging section.  Remote peers can also rely
      on the backup user as the default remote user name if they choose.

      @raise ValueError: If reference configuration is invalid.
      """
      if self.options.startingData is None:
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
      if self.collect.targetDir is None:
         raise ValueError("Collect section target directory must be filled in.")
      if len(self.collect.collectDirs) < 1:
         raise ValueError("Collect section must contain at least one collect directory.")
      if self.collect.collectDirs is not None:
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
      if self.stage.targetDir is None:
         raise ValueError("Stage section target directory must be filled in.")
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
            if self.options.backupUser is None and remotePeer.remoteUser is None:   # redundant, per options validations
               raise ValueError("Remote user must either be set in options section or individual remote peer.")
            if self.options.rcpCommand is None and remotePeer.rcpCommand is None:   # redundant, per options validations
               raise ValueError("Remote copy command must either be set in options section or individual remote peer.")

   def _validateStore(self):
      """
      Validates store configuration.

      The device type and drive speed and capacity mode are optional, and all
      other values are required (missing booleans will be set to defaults,
      which is OK).

      The image writer functionality in the C{writer} module is supposed to be
      able to handle a device speed of C{None}.  Any caller which needs a
      "real" (non-C{None}) value for the device type can use
      C{DEFAULT_DEVICE_TYPE}, which is guaranteed to be sensible.

      @raise ValueError: If store configuration is invalid.
      """
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
      if self.purge.purgeDirs is not None:
         for purgeDir in self.purge.purgeDirs:
            if purgeDir.absolutePath is None:
               raise ValueError("Each purge directory must set an absolute path.")
            if purgeDir.retainDays is None:
               raise ValueError("Each purge directory must set a retain days value.")

