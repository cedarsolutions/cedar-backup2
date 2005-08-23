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
# Copyright (c) 2005 Kenneth J. Pronovici.
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
# Project  : Official Cedar Backup Extensions
# Revision : $Id$
# Purpose  : Provides an extension to back up Subversion repositories.
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# This file was created with a width of 132 characters, and NO tabs.

########################################################################
# Module documentation
########################################################################

"""
Provides an extension to back up Subversion databases.

This is a Cedar Backup extension used to back up Subversion repositories via
the Cedar Backup command line.  It requires a new configurations section
<subversion> and is intended to be run either immediately before or immediately
after the standard collect action.  Aside from its own configuration, it
requires the options and collect configuration sections in the standard Cedar
Backup configuration file.

There are two different kinds of Subversion repositories at this writing: BDB
(Berkeley Database) and FSFS (a "filesystem within a filesystem").  I
personally only use the BDB version, because when I started using Subversion,
that's all there was.  It turns out that FSFS repositories can be backed up
either the same way as BDB repositories (via C{svnadmin dump}) or can be backed
up just like any other set of directories.  

Only use this extension for FSFS repositories if you want to use C{svnadmin
dump} for backups.  Use the normal collect action otherwise.  It's simpler, and
possibly less prone to problems like updates to the repository in the middle of
a backup.

Each repository can be backed using the same collect modes allowed for
filesystems in the standard Cedar Backup collect action: weekly, daily,
incremental.  

@author: Kenneth J. Pronovici <pronovic@ieee.org>
"""

########################################################################
# Imported modules
########################################################################

# System modules
import os
import logging
import pickle
from bz2 import BZ2File
from gzip import GzipFile

# XML-related modules
from xml.dom.ext.reader import PyExpat
from xml.xpath import Evaluate
from xml.parsers.expat import ExpatError
from xml.dom.minidom import Node
from xml.dom.minidom import getDOMImplementation
from xml.dom.minidom import parseString
from xml.dom.ext import PrettyPrint

# Cedar Backup modules
from CedarBackup2.config import addContainerNode, addStringNode
from CedarBackup2.config import readChildren, readFirstChild, readString
from CedarBackup2.config import VALID_COLLECT_MODES, VALID_COMPRESS_MODES
from CedarBackup2.action import isStartOfWeek, buildNormalizedPath
from CedarBackup2.util import executeCommand, ObjectTypeList, encodePath, changeOwnership


########################################################################
# Module-wide constants and variables
########################################################################

logger = logging.getLogger("CedarBackup2.log.extend.subversion")

SVNLOOK_COMMAND      = [ "svnlook", ]
SVNADMIN_COMMAND     = [ "svnadmin", ]

REVISION_PATH_EXTENSION = "svnlast"


########################################################################
# Repository class definition
########################################################################

class Repository(object):

   """
   Class representing generic Subversion repository configuration..

   This is a base class used for validation later.  All subversion repository
   configuration (no matter how many types there are) must inherit from this
   class.

   The following restrictions exist on data in this class:

      - The respository path must be absolute.
      - The collect mode must be one of the values in L{VALID_COLLECT_MODES}.
      - The compress mode must be one of the values in L{VALID_COMPRESS_MODES}.

   @sort: __init__, __repr__, __str__, __cmp__, repositoryPath, collectMode, compressMode
   """

   def __init__(self, repositoryPath=None, collectMode=None, compressMode=None):
      """
      Constructor for the C{Repository} class.

      You should never directly instantiate this class.
      
      @param repositoryPath: Absolute path to a Subversion repository on disk.
      @param collectMode: Overridden collect mode for this directory.
      @param compressMode: Overridden compression mode for this directory.
      """
      self._repositoryType = None
      self._repositoryPath = None
      self._collectMode = None
      self._compressMode = None
      self.repositoryPath = repositoryPath
      self.collectMode = collectMode
      self.compressMode = compressMode

   def __repr__(self):
      """
      Official string representation for class instance.
      """
      return "Repository(%s, %s, %s)" % (self.repositoryPath, self.collectMode, self.compressMode)

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
      if self._repositoryType != other._repositoryType:
         if self._repositoryType < other._repositoryType:
            return -1
         else:
            return 1
      if self._repositoryPath != other._repositoryPath:
         if self._repositoryPath < other._repositoryPath:
            return -1
         else:
            return 1
      if self._collectMode != other._collectMode:
         if self._collectMode < other._collectMode:
            return -1
         else:
            return 1
      if self._compressMode != other._compressMode:
         if self._compressMode < other._compressMode:
            return -1
         else:
            return 1
      return 0

   def _getRepositoryType(self):
      """
      Property target used to get the repository type.
      """
      return self._repositoryType

   def _setRepositoryPath(self, value):
      """
      Property target used to set the repository path.
      The value must be an absolute path if it is not C{None}.
      It does not have to exist on disk at the time of assignment.
      @raise ValueError: If the value is not an absolute path.
      @raise ValueError: If the value cannot be encoded properly.
      """
      if value is not None:
         if not os.path.isabs(value):
            raise ValueError("Repository path must be an absolute path.")
      self._repositoryPath = encodePath(value)

   def _getRepositoryPath(self):
      """
      Property target used to get the repository path.
      """
      return self._repositoryPath

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

   def _setCompressMode(self, value):
      """
      Property target used to set the compress mode.
      If not C{None}, the mode must be one of the values in L{VALID_COMPRESS_MODES}.
      @raise ValueError: If the value is not valid.
      """
      if value is not None:
         if value not in VALID_COMPRESS_MODES:
            raise ValueError("Compress mode must be one of %s." % VALID_COMPRESS_MODES)
      self._compressMode = value

   def _getCompressMode(self):
      """
      Property target used to get the compress mode.
      """
      return self._compressMode

   repositoryType = property(_getRepositoryType, None, None, doc="Type of this repository.")
   repositoryPath = property(_getRepositoryPath, _setRepositoryPath, None, doc="Path to the repository to collect.")
   collectMode = property(_getCollectMode, _setCollectMode, None, doc="Overridden collect mode for this repository.")
   compressMode = property(_getCompressMode, _setCompressMode, None, doc="Overridden compress mode for this repository.")


########################################################################
# BDBRepository class definition
########################################################################

class BDBRepository(Repository):

   """
   Class representing Subversion BDB (Berkeley Database) repository configuration.

   The Subversion configuration information is used for backing up single
   Subversion repository in BDB form.

   The following restrictions exist on data in this class:

      - The respository path must be absolute.
      - The collect mode must be one of the values in L{VALID_COLLECT_MODES}.
      - The compress mode must be one of the values in L{VALID_COMPRESS_MODES}.

   @sort: __init__, __repr__, __str__, __cmp__, repositoryPath, collectMode, compressMode
   """

   def __init__(self, repositoryPath=None, collectMode=None, compressMode=None):
      """
      Constructor for the C{BDBRepository} class.
      
      @param repositoryPath: Absolute path to a Subversion repository on disk.
      @param collectMode: Overridden collect mode for this directory.
      @param compressMode: Overridden compression mode for this directory.
      """
      super(BDBRepository, self).__init__(repositoryPath, collectMode, compressMode)
      self._repositoryType = "BDB"

   def __repr__(self):
      """
      Official string representation for class instance.
      """
      return "BDBRepository(%s, %s, %s)" % (self.repositoryPath, self.collectMode, self.compressMode)


########################################################################
# FSFSRepository class definition
########################################################################

class FSFSRepository(Repository):

   """
   Class representing Subversion FSFS repository configuration.

   The Subversion configuration information is used for backing up single
   Subversion repository in FSFS form.

   The following restrictions exist on data in this class:

      - The respository path must be absolute.
      - The collect mode must be one of the values in L{VALID_COLLECT_MODES}.
      - The compress mode must be one of the values in L{VALID_COMPRESS_MODES}.

   @sort: __init__, __repr__, __str__, __cmp__, repositoryPath, collectMode, compressMode
   """

   def __init__(self, repositoryPath=None, collectMode=None, compressMode=None):
      """
      Constructor for the C{FSFSRepository} class.
      
      @param repositoryPath: Absolute path to a Subversion repository on disk.
      @param collectMode: Overridden collect mode for this directory.
      @param compressMode: Overridden compression mode for this directory.
      """
      super(FSFSRepository, self).__init__(repositoryPath, collectMode, compressMode)
      self._repositoryType = "FSFS"

   def __repr__(self):
      """
      Official string representation for class instance.
      """
      return "FSFSRepository(%s, %s, %s)" % (self.repositoryPath, self.collectMode, self.compressMode)


########################################################################
# SubversionConfig class definition
########################################################################

class SubversionConfig(object):

   """
   Class representing Subversion configuration.

   Subversion configuration is used for backing up Subversion repositories.

   The following restrictions exist on data in this class:

      - The collect mode must be one of the values in L{VALID_COLLECT_MODES}.
      - The compress mode must be one of the values in L{VALID_COMPRESS_MODES}.
      - The repositories list must be a list of C{Repository} objects.

   For the C{repositories} list, validation is accomplished through the
   L{util.ObjectTypeList} list implementation that overrides common list
   methods and transparently ensures that each element is a C{Repository}.

   @note: Lists within this class are "unordered" for equality comparisons.

   @sort: __init__, __repr__, __str__, __cmp__, collectMode, compressMode, repositories
   """

   def __init__(self, collectMode=None, compressMode=None, repositories=None):
      """
      Constructor for the C{SubversionConfig} class.

      @param collectMode: Default collect mode.
      @param compressMode: Default compress mode.
      @param repositories: List of Subversion repositories to back up.

      @raise ValueError: If one of the values is invalid.
      """
      self._collectMode = None
      self._compressMode = None
      self._repositories = None
      self.collectMode = collectMode
      self.compressMode = compressMode
      self.repositories = repositories

   def __repr__(self):
      """
      Official string representation for class instance.
      """
      return "SubversionConfig(%s, %s, %s)" % (self.collectMode, self.compressMode, self.repositories)

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
      if self._collectMode != other._collectMode:
         if self._collectMode < other._collectMode:
            return -1
         else:
            return 1
      if self._compressMode != other._compressMode:
         if self._compressMode < other._compressMode:
            return -1
         else:
            return 1
      if self._repositories != other._repositories:
         if self._repositories < other._repositories:
            return -1
         else:
            return 1
      return 0

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

   def _setCompressMode(self, value):
      """
      Property target used to set the compress mode.
      If not C{None}, the mode must be one of the values in L{VALID_COMPRESS_MODES}.
      @raise ValueError: If the value is not valid.
      """
      if value is not None:
         if value not in VALID_COMPRESS_MODES:
            raise ValueError("Compress mode must be one of %s." % VALID_COMPRESS_MODES)
      self._compressMode = value

   def _getCompressMode(self):
      """
      Property target used to get the compress mode.
      """
      return self._compressMode

   def _setRepositories(self, value):
      """
      Property target used to set the repositorieslist.
      Either the value must be C{None} or each element must be a C{Repository}.
      @raise ValueError: If the value is not a C{Repository}
      """
      if value is None:
         self._repositories = None
      else:
         try:
            saved = self._repositories
            self._repositories = ObjectTypeList(Repository, "Repository")
            self._repositories.extend(value)
         except Exception, e:
            self._repositories = saved
            raise e

   def _getRepositories(self):
      """
      Property target used to get the repositories list.
      """
      return self._repositories

   collectMode = property(_getCollectMode, _setCollectMode, None, doc="Default collect mode.")
   compressMode = property(_getCompressMode, _setCompressMode, None, doc="Default compress mode.")
   repositories = property(_getRepositories, _setRepositories, None, doc="List of Subversion repositories to back up.")


########################################################################
# LocalConfig class definition
########################################################################

class LocalConfig(object):

   """
   Class representing this extension's configuration document.

   This is not a general-purpose configuration object like the main Cedar
   Backup configuration object.  Instead, it just knows how to parse and emit
   Subversion-specific configuration values.  Third parties who need to read
   and write configuration related to this extension should access it through
   the constructor, C{validate} and C{addConfig} methods.

   @note: Lists within this class are "unordered" for equality comparisons.

   @sort: __init__, __repr__, __str__, __cmp__, subversion, validate, addConfig
   """

   def __init__(self, xmlData=None, xmlPath=None, validate=True):
      """
      Initializes a configuration object.

      If you initialize the object without passing either C{xmlData} or
      C{xmlPath} then configuration will be empty and will be invalid until it
      is filled in properly.

      No reference to the original XML data or original path is saved off by
      this class.  Once the data has been parsed (successfully or not) this
      original information is discarded.

      Unless the C{validate} argument is C{False}, the L{LocalConfig.validate}
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
      self._subversion = None
      self.subversion = None
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

   def __repr__(self):
      """
      Official string representation for class instance.
      """
      return "LocalConfig(%s)" % (self.subversion)

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
      if self._subversion != other._subversion:
         if self._subversion < other._subversion:
            return -1
         else:
            return 1
      return 0

   def _setSubversion(self, value):
      """
      Property target used to set the subversion configuration value.
      If not C{None}, the value must be a C{SubversionConfig} object.
      @raise ValueError: If the value is not a C{SubversionConfig}
      """
      if value is None:
         self._subversion = None
      else:
         if not isinstance(value, SubversionConfig):
            raise ValueError("Value must be a C{SubversionConfig} object.")
         self._subversion = value

   def _getSubversion(self):
      """
      Property target used to get the subversion configuration value.
      """
      return self._subversion

   subversion = property(_getSubversion, _setSubversion, None, "Subversion configuration in terms of a C{SubversionConfig} object.")

   def validate(self):
      """
      Validates configuration represented by the object.

      Subversion configuration must be filled in.  Within that, the collect
      mode and compress mode are both optional, but the list of repositories
      must contain at least one entry.

      Each BDB or FSFS repository must contain a repository path, and then must
      be either able to take collect mode and compress mode configuration from
      the parent C{SubversionConfig} object, or must set each value on its own.
      We don't look at any other kinds of repositories that might be in the
      list.

      @raise ValueError: If one of the validations fails.
      """
      if self.subversion is None:
         raise ValueError("Subversion section is required.")
      if self.subversion.repositories is None or len(self.subversion.repositories) < 1:
         raise ValueError("At least one repository must be configured.")
      for repository in self.subversion.repositories:
         if repository.repositoryType in [ "BDB", "FSFS", ]:
            if repository.repositoryPath is None:
               raise ValueError("Each repository directory must set a repository path.")
            if self.subversion.collectMode is None and repository.collectMode is None:
               raise ValueError("Collect mode must either be set in parent section or individual repository.")
            if self.subversion.compressMode is None and repository.compressMode is None:
               raise ValueError("Compress mode must either be set in parent section or individual repository.")

   def addConfig(self, xmlDom, parentNode):
      """
      Adds a <subversion> configuration section as the next child of a parent.

      Third parties should use this function to write configuration related to
      this extension.

      We add the following fields to the document::

         collectMode    //cb_config/subversion/collectMode
         compressMode   //cb_config/subversion/compressMode

      We also add groups of the following items, one list element per
      item::

         repository     //cb_config/subversion/repository

      @param xmlDom: DOM tree as from C{impl.createDocument()}.
      @param parentNode: Parent that the section should be appended to.
      """
      if self.subversion is not None:
         sectionNode = addContainerNode(xmlDom, parentNode, "subversion")
         addStringNode(xmlDom, sectionNode, "collect_mode", self.subversion.collectMode)
         addStringNode(xmlDom, sectionNode, "compress_mode", self.subversion.compressMode)
         if self.subversion.repositories is not None:
            for repository in self.subversion.repositories:
               LocalConfig._addRepository(xmlDom, sectionNode, repository)

   def _parseXmlData(self, xmlData):
      """
      Internal method to parse an XML string into the object.

      This method parses the XML document into a DOM tree (C{xmlDom}) and then
      calls a static method to parse the subversion configuration section.

      @param xmlData: XML data to be parsed
      @type xmlData: String data

      @raise ValueError: If the XML cannot be successfully parsed.
      """
      try:
         xmlDom = PyExpat.Reader().fromString(xmlData)
         parent = readFirstChild(xmlDom, "cb_config")
         self._subversion = LocalConfig._parseSubversion(parent)
      except (IOError, ExpatError), e:
         raise ValueError("Unable to parse XML document: %s" % e)

   def _parseSubversion(parent):
      """
      Parses a subversion configuration section.
      
      We read the following individual fields::

         collectMode    //cb_config/subversion/collect_mode
         compressMode   //cb_config/subversion/compress_mode

      We also read groups of the following item, one list element per
      item::

         repositories   //cb_config/subversion/repository

      The repositories are parsed by L{_parseRepositories}.

      @param parent: Parent node to search beneath.

      @return: C{SubversionConfig} object or C{None} if the section does not exist.
      @raise ValueError: If some filled-in value is invalid.
      """
      subversion = None
      section = readFirstChild(parent, "subversion")
      if section is not None:
         subversion = SubversionConfig()
         subversion.collectMode = readString(section, "collect_mode")
         subversion.compressMode = readString(section, "compress_mode")
         subversion.repositories = LocalConfig._parseRepositories(section)
      return subversion
   _parseSubversion = staticmethod(_parseSubversion)

   def _parseRepositories(parent):
      """
      Reads a list of C{Repository} objects from immediately beneath the parent.

      We read the following individual fields::

         repositoryType          type
         repositoryPath          abs_path
         collectMode             collect_mode
         compressMode            compess_mode 

      The type field is optional, and if it isn't there we assume a BDB
      repositories.  Note that we will currently ignore any repository listing
      which has a set type other than C{["BDB", "FSFS", ]}.  However, we will
      log a warning if we do this.

      @param parent: Parent node to search beneath.

      @return: List of C{Repository} objects or C{None} if none are found.
      @raise ValueError: If some filled-in value is invalid.
      """
      lst = []
      for entry in readChildren(parent, "repository"):
         if entry.nodeType == Node.ELEMENT_NODE:
            repositoryType = readString(entry, "type")
            if repositoryType in [ None, "BDB", ]:    # BDB is the default type 
               repository = BDBRepository()
               repository.repositoryPath = readString(entry, "abs_path")
               repository.collectMode = readString(entry, "collect_mode")
               repository.compressMode = readString(entry, "compress_mode")
               lst.append(repository)
            elif repositoryType == "FSFS":
               repository = FSFSRepository()
               repository.repositoryPath = readString(entry, "abs_path")
               repository.collectMode = readString(entry, "collect_mode")
               repository.compressMode = readString(entry, "compress_mode")
               lst.append(repository)
            else:
               logger.warn("Warning: Ignoring Subversion repository with unknown type [%s]." % repositoryType)
      if lst == []:
         lst = None
      return lst
   _parseRepositories = staticmethod(_parseRepositories)

   def _addRepository(xmlDom, parentNode, repository):
      """
      Adds a repository container as the next child of a parent.

      We add the following fields to the document::

         repositoryType          repository/type
         repositoryPath          repository/abs_path
         collectMode             repository/collect_mode
         compressMode            repository/compress_mode

      The <repository> node itself is created as the next child of the parent
      node.  This method only adds one repository node.  The parent must loop
      for each repository in the C{SubversionConfig} object.

      If C{repository} is C{None}, this method call will be a no-op.

      @param xmlDom: DOM tree as from C{impl.createDocument()}.
      @param parentNode: Parent that the section should be appended to.
      @param repository: Repository to be added to the document.
      """
      if repository is not None:
         sectionNode = addContainerNode(xmlDom, parentNode, "repository")
         addStringNode(xmlDom, sectionNode, "type", repository.repositoryType)
         addStringNode(xmlDom, sectionNode, "abs_path", repository.repositoryPath)
         addStringNode(xmlDom, sectionNode, "collect_mode", repository.collectMode)
         addStringNode(xmlDom, sectionNode, "compress_mode", repository.compressMode)
   _addRepository = staticmethod(_addRepository)


########################################################################
# Public functions
########################################################################

###########################
# executeAction() function
###########################

def executeAction(configPath, options, config):
   """
   Executes the Subversion backup action.

   @param configPath: Path to configuration file on disk.
   @type configPath: String representing a path on disk.

   @param options: Program command-line options.
   @type options: Options object.

   @param config: Program configuration.
   @type config: Config object.

   @raise ValueError: Under many generic error conditions
   @raise IOError: If a backup could not be written for some reason.
   """
   logger.debug("Executing Subversion extended action.")
   if config.options is None or config.collect is None:
      raise ValueError("Cedar Backup configuration is not properly filled in.")
   local = LocalConfig(xmlPath=configPath)
   todayIsStart = isStartOfWeek(config.options.startingDay)
   fullBackup = options.full or todayIsStart
   logger.debug("Full backup flag is [%s]" % fullBackup)
   if local.subversion.repositories is not None:
      for repository in local.subversion.repositories:
         logger.debug("Working with repository [%s]." % repository.repositoryPath)
         if repository.repositoryType in ["BDB", "FSFS", ]:
            collectMode = _getCollectMode(local, repository)
            compressMode = _getCompressMode(local, repository)
            revisionPath = _getRevisionPath(config, repository)
            backupPath = _getBackupPath(config, repository, compressMode)
            if fullBackup or (collectMode in ['daily', 'incr', ]) or (collectMode == 'weekly' and todayIsStart):
               logger.debug("Repository meets criteria to be backed up today.")
               _backupRepository(config, repository.repositoryType,
                                 repository.repositoryPath, backupPath, 
                                 revisionPath, fullBackup, collectMode, compressMode)
            else:
               logger.debug("Repository will not be backed up, per collect mode.")
         else:
            logger.debug("Repository will not be backed up, since it is not type BDB or FSFS.")
         logger.info("Completed backing up Subversion repository [%s]." % repository.repositoryPath)
   logger.info("Executed the Subversion extended action successfully.")

def _getCollectMode(local, repository):
   """
   Gets the collect mode that should be used for a repository.
   Use repository's if possible, otherwise take from subversion section.
   @param repository: BDBRepository object.
   @return: Collect mode to use.
   """
   if repository.collectMode is None:
      collectMode = local.subversion.collectMode
   else:
      collectMode = repository.collectMode
   logger.debug("Collect mode is [%s]" % collectMode)
   return collectMode

def _getCompressMode(local, repository):
   """
   Gets the compress mode that should be used for a repository.
   Use repository's if possible, otherwise take from subversion section.
   @param local: LocalConfig object.
   @param repository: BDBRepository object.
   @return: Compress mode to use.
   """
   if repository.compressMode is None:
      compressMode = local.subversion.compressMode
   else:
      compressMode = repository.compressMode
   logger.debug("Compress mode is [%s]" % compressMode)
   return compressMode

def _getRevisionPath(config, repository):
   """
   Gets the path to the revision file associated with a repository.
   @param config: Config object.
   @param repository: BDBRepository object.
   @return: Absolute path to the revision file associated with the repository.
   """
   normalized = buildNormalizedPath(repository.repositoryPath)
   filename = "%s.%s" % (normalized, REVISION_PATH_EXTENSION)
   revisionPath = os.path.join(config.options.workingDir, filename)
   logger.debug("Revision file path is [%s]" % revisionPath)
   return revisionPath

def _getBackupPath(config, repository, compressMode):
   """
   Gets the backup file path (including correct extension) associated with a repository.
   @param config: Config object.
   @param repository: BDBRepository object.
   @param compressMode: Compress mode to use for this repository.
   @return: Absolute path to the backup file associated with the repository.
   """
   filename = "svndump-%s.txt" % buildNormalizedPath(repository.repositoryPath)
   if compressMode == 'gzip':
      filename = "%s.gz" % filename
   elif compressMode == 'bzip2':
      filename = "%s.bz2" % filename
   backupPath = os.path.join(config.collect.targetDir, filename)
   logger.debug("Backup file path is [%s]" % backupPath)
   return backupPath

def _backupRepository(config, repositoryType, repositoryPath, backupPath, revisionPath, fullBackup, collectMode, compressMode):
   """
   Backs up an individual Subversion repository (either BDB or FSFS).

   This internal method wraps the public methods and adds some functionality
   to work better with the extended action itself.

   @param config: Cedar Backup configuration.
   @param repositoryType: Type of the repository (assumed to be BDB or FSFS).
   @param repositoryPath: Path to Subversion repository to back up.
   @param backupPath: Path to backup file that will be written.
   @param revisionPath: Path used to store incremental revision information.
   @param fullBackup: Indicates whether this should be a full backup.
   @param collectMode: Collect mode to use.
   @param compressMode: Compress mode to use.
    
   @raise ValueError: If some value is missing or invalid.
   @raise IOError: If there is a problem executing the Subversion dump.
   """
   if collectMode != "incr" or fullBackup:
      startRevision = 0
      endRevision = getYoungestRevision(repositoryPath)
      logger.debug("Using full backup, revision: (%d, %d)." % (startRevision, endRevision))
   else:
      if fullBackup:
         startRevision = 0
         endRevision = getYoungestRevision(repositoryPath)
      else:
         startRevision = _loadLastRevision(revisionPath) + 1
         endRevision = getYoungestRevision(repositoryPath)
         if startRevision > endRevision:
            logger.info("No need to back up repository [%s]; no new revisions." % repositoryPath)
            return
      logger.debug("Using incremental backup, revision: (%d, %d)." % (startRevision, endRevision))
   outputFile = _getOutputFile(backupPath, compressMode)
   try:
      if repositoryType == "BDB":
         backupBDBRepository(repositoryPath, outputFile, startRevision, endRevision)
      else:
         backupFSFSRepository(repositoryPath, outputFile, startRevision, endRevision)
   finally:
      outputFile.close()
   if not os.path.exists(backupPath):
      raise IOError("Dump file [%s] does not seem to exist after backup completed." % backupPath)
   changeOwnership(backupPath, config.options.backupUser, config.options.backupGroup)
   if collectMode == "incr":
      _writeLastRevision(config, revisionPath, endRevision)

def _getOutputFile(backupPath, compressMode):
   """
   Opens the output file used for saving the Subversion dump.

   If the compress mode is "gzip", we'll open a C{GzipFile}, and if the
   compress mode is "bzip2", we'll open a C{BZ2File}.  Otherwise, we'll just
   return an object from the normal C{open()} method.

   @param backupPath: Path to file to open.
   @param compressMode: Compress mode of file ("none", "gzip", "bzip").

   @return: Output file object.
   """
   if compressMode == "gzip":
      return GzipFile(backupPath, "w")
   elif compressMode == "bzip2":
      return BZ2File(backupPath, "w")
   else:
      return open(backupPath, "w")

def _loadLastRevision(revisionPath):
   """
   Loads the indicated revision file from disk into an integer.

   If we can't load the revision file successfully (either because it doesn't
   exist or for some other reason), then a revision of -1 will be returned -
   but the condition will be logged.  This way, we err on the side of backing
   up too much, because anyone using this will presumably be adding 1 to the
   revision, so they don't duplicate any backups.

   @param revisionPath: Path to the revision file on disk.

   @return: Integer representing last backed-up revision, -1 on error or if none can be read.
   """
   if not os.path.isfile(revisionPath):
      startRevision = -1
      logger.debug("Revision file [%s] does not exist on disk." % revisionPath)
   else:
      try:
         startRevision = pickle.load(open(revisionPath, "r"))
         logger.debug("Loaded revision file [%s] from disk: %d." % (revisionPath, startRevision))
      except:
         startRevision = -1
         logger.error("Failed loading revision file [%s] from disk." % revisionPath)
   return startRevision

def _writeLastRevision(config, revisionPath, endRevision):
   """
   Writes the end revision to the indicated revision file on disk.

   If we can't write the revision file successfully for any reason, we'll log
   the condition but won't throw an exception.

   @param config: Config object.
   @param revisionPath: Path to the revision file on disk.
   @param endRevision: Last revision backed up on this run.
   """
   try:
      pickle.dump(endRevision, open(revisionPath, "w"))
      changeOwnership(revisionPath, config.options.backupUser, config.options.backupGroup)
      logger.debug("Wrote new revision file [%s] to disk: %d." % (revisionPath, endRevision))
   except:
      logger.error("Failed to write revision file [%s] to disk." % revisionPath)


#################################
# backupBDBRepository() function
#################################

def backupBDBRepository(repositoryPath, backupFile, startRevision=None, endRevision=None):
   """
   Backs up an individual Subversion BDB repository.

   The starting and ending revision values control an incremental backup.  If
   the starting revision is not passed in, then revision zero (the start of the
   repository) is assumed.  If the ending revision is not passed in, then the
   youngest revision in the database will be used as the endpoint.

   The backup data will be written into the passed-in back file.  Normally,
   this would be an object as returned from C{open}, but it is possible to use
   something like a C{GzipFile} to write compressed output.  The caller is
   responsible for closing the passed-in backup file.

   @note: This function should either be run as root or as the owner of the
   Subversion repository.

   @note: It is apparently I{not} a good idea to interrupt this function.
   Sometimes, this leaves the repository in a "wedged" state, which requires
   recovery using C{svnadmin recover}.

   @param repositoryPath: Path to Subversion repository to back up
   @type repositoryPath: String path representing Subversion BDB repository on disk.

   @param backupFile: Python file object to use for writing backup.
   @type backupFile: Python file object as from C{open()} or C{file()}.
   
   @param startRevision: Starting repository revision to back up (for incremental backups)
   @type startRevision: Integer value >= 0.

   @param endRevision: Ending repository revision to back up (for incremental backups)
   @type endRevision: Integer value >= 0.

   @raise ValueError: If some value is missing or invalid.
   @raise IOError: If there is a problem executing the Subversion dump.
   """
   if startRevision is None:
      startRevision = 0
   if endRevision is None:
      endRevision = getYoungestRevision(repositoryPath)
   if int(startRevision) < 0:
      raise ValueError("Start revision must be >= 0.")
   if int(endRevision) < 0:
      raise ValueError("End revision must be >= 0.")
   if startRevision > endRevision:
      raise ValueError("Start revision must be <= end revision.")
   args = [ "dump", "--quiet", "-r%s:%s" % (startRevision, endRevision), "--incremental", repositoryPath, ]
   result = executeCommand(SVNADMIN_COMMAND, args, returnOutput=False, ignoreStderr=True, doNotLog=True, outputFile=backupFile)[0]
   if result != 0:
      raise IOError("Error [%d] executing Subversion dump for BDB repository [%s]." % (result, repositoryPath))
   logger.debug("Completed dumping subversion repository [%s]." % repositoryPath)


##################################
# backupFSFSRepository() function
##################################

def backupFSFSRepository(repositoryPath, backupFile, startRevision=None, endRevision=None):
   """
   Backs up an individual Subversion FSFS repository.

   The starting and ending revision values control an incremental backup.  If
   the starting revision is not passed in, then revision zero (the start of the
   repository) is assumed.  If the ending revision is not passed in, then the
   youngest revision in the database will be used as the endpoint.

   The backup data will be written into the passed-in back file.  Normally,
   this would be an object as returned from C{open}, but it is possible to use
   something like a C{GzipFile} to write compressed output.  The caller is
   responsible for closing the passed-in backup file.

   You should only use this function to back up an FSFS repository if you want
   to use C{svnadmin dump} for your backup.  Use a normal filesystem copy
   otherwise.  That will be simpler, and possibly less prone to problems like
   updates to the repository in the middle of a backup.

   @note: This function should either be run as root or as the owner of the
   Subversion repository.

   @param repositoryPath: Path to Subversion repository to back up
   @type repositoryPath: String path representing Subversion FSFS repository on disk.

   @param backupFile: Python file object to use for writing backup.
   @type backupFile: Python file object as from C{open()} or C{file()}.
   
   @param startRevision: Starting repository revision to back up (for incremental backups)
   @type startRevision: Integer value >= 0.

   @param endRevision: Ending repository revision to back up (for incremental backups)
   @type endRevision: Integer value >= 0.

   @raise ValueError: If some value is missing or invalid.
   @raise IOError: If there is a problem executing the Subversion dump.
   """
   if startRevision is None:
      startRevision = 0
   if endRevision is None:
      endRevision = getYoungestRevision(repositoryPath)
   if int(startRevision) < 0:
      raise ValueError("Start revision must be >= 0.")
   if int(endRevision) < 0:
      raise ValueError("End revision must be >= 0.")
   if startRevision > endRevision:
      raise ValueError("Start revision must be <= end revision.")
   args = [ "dump", "--quiet", "-r%s:%s" % (startRevision, endRevision), "--incremental", repositoryPath, ]
   result = executeCommand(SVNADMIN_COMMAND, args, returnOutput=False, ignoreStderr=True, doNotLog=True, outputFile=backupFile)[0]
   if result != 0:
      raise IOError("Error [%d] executing Subversion dump for FSFS repository [%s]." % (result, repositoryPath))
   logger.debug("Completed dumping subversion repository [%s]." % repositoryPath)


#################################
# getYoungestRevision() function
#################################

def getYoungestRevision(repositoryPath):
   """
   Gets the youngest (newest) revision in a Subversion repository using C{svnlook}.

   @note: This function should either be run as root or as the owner of the
   Subversion repository.

   @param repositoryPath: Path to Subversion repository to look in.
   @type repositoryPath: String path representing Subversion BDB repository on disk.

   @return: Youngest revision as an integer.
   
   @raise ValueError: If there is a problem parsing the C{svnlook} output.
   @raise IOError: If there is a problem executing the C{svnlook} command.
   """
   args = [ 'youngest', repositoryPath, ]
   (result, output) = executeCommand(SVNLOOK_COMMAND, args, returnOutput=True, ignoreStderr=True)
   if result != 0:
      raise IOError("Error [%d] executing 'svnlook youngest' for repository [%s]." % (result, repositoryPath))
   if len(output) != 1:
      raise ValueError("Unable to parse 'svnlook youngest' output.")
   return int(output[0])

