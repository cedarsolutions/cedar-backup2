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

   The C{Configuration} class is a Python object representation of a Cedar
   Backup XML configuration file.  The representation is two-way: XML data can
   be used to create a C{Configuration} object, and then changes to the object
   can be propogated back to disk.  A C{Configuration} object can even be used
   to create a configuration file from scratch programmatically.

   The C{Configuration} class is intended to be the only Python-language
   interface to Cedar Backup configuration on disk.  Cedar Backup will use the
   class as its internal representation of configuration, and applications
   external to Cedar Backup itself (such as a hypothetical third-party
   configuration tool written in Python) should also use the class when they
   need to read and write configuration files.

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

   A C{Configuration} object can either be created "empty", or can be created
   based on XML input (either in the form of a string or read in from a file on
   disk).  Generally speaking, the XML input I{must} result in a
   C{Configuration} object which passes the validations laid out below in the
   I{Validation} section.  

   An XML configuration file is composed of six sections:

      - I{reference}: specifies reference information about the file (author, revision, etc)
      - I{options}: specifies global configuration options
      - I{collect}: specifies configuration related to the collect action
      - I{stage}: specifies configuration related to the stage action
      - I{store}: specifies configuration related to the store action
      - I{purge}: specifies configuration related to the purge action

   Each section is represented by an class in this module, and then the overall
   C{Configuration} class is a composition of the various other classes.  

   Any configuration section that is missing in the XML document (or has not
   been filled into an "empty" document) will just be set to C{None} in the
   object representation.  The same goes for individual fields within each
   configuration section.  Keep in mind that the document might not be
   completely valid if some sections or fields aren't filled in - but that
   won't matter until validation takes place (see the I{Validation} section
   below).

Validation 
==========

   There are two main levels of validation in the C{Configuration} object and
   its children.  The first is field-level validation.  Field-level validation
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
   L{Configuration.validate} method.  This method can be called at any time by
   a client, and will always be called immediately after creating a
   C{Configuration} object from XML data and before exporting a
   C{Configuration} object to XML.  This way, we get acceptable ease-of-use but
   we also don't accept or emit invalid configuration files.

   The L{Configuration.validate} implementation actually takes three passes to
   completely validate a configuration document.  The first pass at validation
   is to ensure that the proper sections are filled into the document.  There
   are default requirements, but the caller has the opportunity to override
   these defaults.

   The second pass at validation ensures that any filled-in section contains
   valid data.  Any section which is not set to C{None} is validated according
   to the rules for that section (see below).

   The third pass does some convenience validations which aren't strictly
   related to the format or contents of the configuration document, but might
   be useful anyway.  For example, there is an option to check that all local
   paths exist, and another to check that all hostnames to remote peers are
   valid.  All of these convenience validations are disabled by default, and
   can be re-enabled individually by the caller.

   I{Reference Validations}

   No validations.

   I{Options Validations}

   All fields must be filled in.  The rcp command is used as a default value
   for all remote peers in the staging section.  Remote peers can also rely
   on the backup user as the default remote user name if they choose.

   I{Collect Validations}

   The target directory must be filled in.  The collect mode, archive mode
   and ignore file are all optional.  The list of absolute paths to exclude
   and patterns to exclude may be either C{None} or an empty list C{[]} if
   desired.  The collect directory list must contain at least one entry.  

   Each collect directory entry must contain an absolute path to collect,
   and then must either be able to take collect mode, archive mode and
   ignore file configuration from the parent C{CollectConfig} object, or
   must set each value on its own.  The list of absolute paths to exclude,
   relative paths to exclude and patterns to exclude may be either C{None}
   or an empty list C{[]} if desired.  Any list of absolute paths to
   exclude or patterns to exclude will be combined with the same list in the
   C{CollectConfig} object to make the complete list for a given directory.

   I{Stage Validations}

   The target directory must be filled in.  There must be at least one peer
   (remote or local) between the two lists of peers.  A list with no entries
   can be either C{None} or an empty list C{[]} if desired.

   Local peers must be completely filled in, including both name and collect
   directory.  Remote peers must also fill in the name and collect
   directory, but can leave the remote user and rcp command unset.  In this
   case, the remote user is assumed to match the backup user from the
   options section and rcp command is taken directly from the options
   section.

   I{Store Validations}

   The device type and drive speed are optional, and all other values
   are required.  

   The image writer functionality in the C{writer} module is supposed to be
   able to handle a device speed of C{None}.  Any caller which needs a
   "real" (non-C{None}) value for the device type can use
   C{DEFAULT_DEVICE_TYPE}, which is guaranteed to be sensible.

   I{Purge Validations}

   The list of purge directories may be either C{None} or an empty
   list C{[]} if desired.  All purge directories must contain a path
   and a retain days value.

@sort: LocalPeer, RemotePeer, CollectDir, PurgeDir, ReferenceConfig, OptionsConfig
       CollectConfig, StageConfig, StoreConfig, PurgeConfig, Configuration,
       DEFAULT_DEVICE_TYPE, VALID_DEVICE_TYPES, VALID_MEDIA_TYPES

@var DEFAULT_DEVICE_TYPE: The default device type.
@var VALID_DEVICE_TYPES: List of valid device types.
@var VALID_MEDIA_TYPES: List of valid media types.

@author: Kenneth J. Pronovici <pronovic@ieee.org>
"""

########################################################################
# Imported modules
########################################################################

# System modules
import os
import logging

# Cedar Backup modules
from CedarBackup2.writer import validateScsiId, validateDriveSpeed
from CedarBackup2.util import AbsolutePathList, ObjectTypeList


########################################################################
# Module-wide constants and variables
########################################################################

logger = logging.getLogger("CedarBackup2.config")

DEFAULT_DEVICE_TYPE = "cdwriter"
VALID_DEVICE_TYPES  = [ "cdwriter", ]
VALID_MEDIA_TYPES   = [ "cdr-74", "cdrw-74", "cdr-80", "cdrw-80", ]


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
         self._relativeExcludePaths = []
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
         self._excludePatterns = []
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
         self._excludePatterns = []
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
      - The device path must be an absolute path.
      - The SCSI id must be in the form specified by L{writer.validateScsiId}.
      - The drive speed must be an integer >= 1

   The device type field mostly exists for planned future extensions, such as
   support for DVD writers.

   @sort: sourceDir, mediaType, deviceType, devicePath, deviceScsiId, driveSpeed, checkData
   """

   def __init__(self, sourceDir=None, mediaType=None, deviceType=None, 
                devicePath=None, deviceScsiId=None, driveSpeed=None, checkData=False):
      """
      Constructor for the C{StoreConfig} class.

      @param sourceDir: Directory whose contents should be written to media.
      @param mediaType: Type of the media (see notes above).
      @param deviceType: Type of the device (optional, see notes above).
      @param devicePath: Filesystem device name for writer device, i.e. C{/dev/cdrw}.
      @param deviceScsiId: SCSI id for writer device, i.e. C{[ATA]:scsibus,target,lun}.
      @param driveSpeed: Speed of the drive, i.e. C{2} for 2x drive, etc.
      @param checkData: Boolean indicating whether resulting image should be validated.

      @raise ValueError: If one of the values is invalid.
      """
      self._sourceDir = None
      self._mediaType = None
      self._deviceType = None
      self._devicePath = None
      self._deviceScsiId = None
      self._driveSpeed = None
      self._checkData = None
      self.sourceDir = sourceDir
      self.mediaType = mediaType
      self.deviceType = deviceType
      self.devicePath = devicePath
      self.deviceScsiId = deviceScsiId
      self.driveSpeed = driveSpeed
      self.checkData = checkData

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

   sourceDir = property(_getSourceDir, _setSourceDir, None, "Directory whose contents should be written to media.")
   mediaType = property(_getMediaType, _setMediaType, None, "Type of the media (see notes above).")
   deviceType = property(_getDeviceType, _setDeviceType, None, "Type of the device (optional, see notes above).")
   devicePath = property(_getDevicePath, _setDevicePath, None, "Filesystem device name for writer device.")
   deviceScsiId = property(_getDeviceScsiId, _setDeviceScsiId, None, "SCSI id for writer device.")
   driveSpeed = property(_getDriveSpeed, _setDriveSpeed, None, "Speed of the drive.")
   checkData = property(_getCheckData, _setCheckData, None, "Boolean indicating whether resulting image should be validated.")


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
# Configuration class definition
########################################################################

class Configuration(object):

   ######################
   # Class documentation
   ######################

   """
   Class representing a Cedar Backup XML configuration document.

   The C{Configuration} class is a Python object representation of a Cedar
   Backup XML configuration file.  It is intended to be the only Python-
   language interface to Cedar Backup configuration on disk for both Cedar
   Backup itself and for external applications.

   The object representation is two-way: XML data can be used to create a
   C{Configuration} object, and then changes to the object can be propogated
   back to disk.  A C{Configuration} object can even be used to create a
   configuration file from scratch programmatically.
   
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

      Unless the C{validate} argument is C{False}, the
      L{Configuration.validate} method will be called (with its default
      arguments) against configuration after successfully parsing any passed-in
      XML.  Keep in mind that even if C{validate} is C{False}, it might not be
      possible to parse the passed-in XML document if lower-level validations
      fail.

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
         # parse XML data in the string
         if validate:
            self.validate()
      elif xmlPath is not None:
         # parse XML data in the file
         if validate:
            self.validate()


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

      Unless the C{validate} parameter is C{False}, the
      L{Configuration.validate} method will be called (with its default
      arguments) against the configuration before extracting the XML.  If
      configuration is not valid, then an XML document will not be extracted.

      @note: It is strongly suggested that the C{validate} option always be set
      to C{True} (the default) unless there is a specific need to write an
      invalid configuration file to disk.

      @param xmlPath: Path to an XML file to create on disk.
      @type xmlPath: Absolute path to a file.

      @param validate: Validate the document before extracting it.
      @type validate: Boolean true/false.

      @return: XML string data or C{None} as described above.

      @raise ValueError: If configuration is not valid.
      @raise IOError: If there is an error writing to the file.
      @raise OSError: If there is an error writing to the file.
      """
      pass

   def validate(self, checkPaths=False, checkPermissions=False, checkHostnames=False,
                requireOneAction=True, requireReference=False, requireOptions=True, 
                requireCollect=False, requireStage=False, requireStore=False, requirePurge=False):
      """
      Validates configuration represented by the object.

      This method encapsulates all of the validations that should apply to a
      fully "complete" document but are not already taken care of by earlier
      validations.  It also provides some extra convenience functionality which
      might be useful to some people.  The process of validation is laid out in
      the I{Validation} section in the class notes (above).

      @param checkPaths: Check that all local paths are valid and exist in the system.
      @param checkPermissions: Check that permissions allow us to read all local paths.
      @param checkHostnames: Check that configured remote peer hostnames appear to be valid.
      @param requireOneAction: Require at least one of the collect, stage, store or purge sections.
      @param requireReference: Require the reference section.
      @param requireOptions: Require the options section.
      @param requireCollect: Require the collect section.
      @param requireStage: Require the stage section.
      @param requireStore: Require the store section.
      @param requirePurge: Require the purge section.
      """
      pass

