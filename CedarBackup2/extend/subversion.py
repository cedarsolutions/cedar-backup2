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
(Berkeley Database) and fsfs (a more CVS-like "filesystem within a filesystem").
I personally only use the BDB version, because when I started using Subversion,
that's all there was.  This extension only backs up BDB repositories.  If I
ever start using fsfs, I'll add another function to back up that kind of 
repository as well.  (Feel free to contribute code if you would like to see
fsfs supported.)

Each repository can be backed using the same collect modes allowed for
filesystems in the standard Cedar Backup collect action: weekly, daily,
incremental.  

@var VALID_COMPRESS_MODES: List of valid compression modes.

@author: Kenneth J. Pronovici <pronovic@ieee.org>
"""

########################################################################
# Imported modules
########################################################################

# System modules
import os
import logging
from bz2 import BZ2File

# XML-related modules
from xml.dom.ext.reader import PyExpat
from xml.xpath import Evaluate
from xml.parsers.expat import ExpatError
from xml.dom.minidom import Node
from xml.dom.minidom import getDOMImplementation
from xml.dom.minidom import parseString
from xml.dom.ext import PrettyPrint

# Cedar Backup modules
from CedarBackup2.config import Config, VALID_COLLECT_MODES
from CedarBackup2.util import executeCommand, ObjectTypeList, encodePath


########################################################################
# Module-wide constants and variables
########################################################################

logger = logging.getLogger("CedarBackup2.log.extend.subversion")

SVNLOOK_COMMAND      = [ "svnlook", ]
SVNADMIN_COMMAND     = [ "svnadmin", ]

VALID_COMPRESS_MODES = [ "gzip", "bzip2", ]


########################################################################
# Repository class definition
########################################################################

class Repository(object):

   """
   Class representing generic Subversion repository configuration..

   This is a base class used for validation later.  All subversion repository
   configuration (no matter how many types there are) must inherit from this
   class.
   """

   def __init__(self):
      """
      Constructor for the C{Repository} class.
      """
      raise NotImplementedError("Repository may not be instantiated.")


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
      self._repositoryType = "BDB"
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
      return "BDBRepository(%s, %s, %s)" % (self.repositoryPath, self.collectMode, self.compressMode)

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
      For this class, this value is always "BDB".
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

   repositoryType = property(_getRepositoryType, None, None, doc="Type of this repository (BDB).")
   repositoryPath = property(_getRepositoryPath, _setRepositoryPath, None, doc="Path to the repository to collect.")
   collectMode = property(_getCollectMode, _setCollectMode, None, doc="Overridden collect mode for this repository.")
   compressMode = property(_getCompressMode, _setCompressMode, None, doc="Overridden compress mode for this repository.")


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

      Each BDB repository must contain a repository path, and then must be
      either able to take collect mode and compress mode configuration from the
      parent C{SubversionConfig} object, or must set each value on its own.  We
      don't look at any other kinds of repositories that might be in the list.

      @raise ValueError: If one of the validations fails.
      """
      if self.subversion is None:
         raise ValueError("Subversion section is required.")
      if self.subversion.repositories is None or len(self.subversion.repositories) < 1:
         raise ValueError("At least one repository must be configured.")
      for repository in self.subversion.repositories:
         if repository.repositoryType == "BDB":
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
         sectionNode = Config.addContainerNode(xmlDom, parentNode, "subversion")
         Config.addStringNode(xmlDom, sectionNode, "collect_mode", self.subversion.collectMode)
         Config.addStringNode(xmlDom, sectionNode, "compress_mode", self.subversion.compressMode)
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
         parent = Config.readFirstChild(xmlDom, "cb_config")
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
      section = Config.readFirstChild(parent, "subversion")
      if section is not None:
         subversion = SubversionConfig()
         subversion.collectMode = Config.readString(section, "collect_mode")
         subversion.compressMode = Config.readString(section, "compress_mode")
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
      which has a set type other than C{"BDB"}.  However, we will log a warning
      if we do this.

      @param parent: Parent node to search beneath.

      @return: List of C{Repository} objects or C{None} if none are found.
      @raise ValueError: If some filled-in value is invalid.
      """
      lst = []
      for entry in Config.readChildren(parent, "repository"):
         if entry.nodeType == Node.ELEMENT_NODE:
            repositoryType = Config.readString(entry, "type")
            if repositoryType in [ None, "BDB", ]:    # BDB is the default type 
               repository = BDBRepository()
               repository.repositoryPath = Config.readString(entry, "abs_path")
               repository.collectMode = Config.readString(entry, "collect_mode")
               repository.compressMode = Config.readString(entry, "compress_mode")
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
         sectionNode = Config.addContainerNode(xmlDom, parentNode, "repository")
         Config.addStringNode(xmlDom, sectionNode, "type", repository.repositoryType)
         Config.addStringNode(xmlDom, sectionNode, "abs_path", repository.repositoryPath)
         Config.addStringNode(xmlDom, sectionNode, "collect_mode", repository.collectMode)
         Config.addStringNode(xmlDom, sectionNode, "compress_mode", repository.compressMode)
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
   logger.info("Executed the Subversion extended action successfully.")

