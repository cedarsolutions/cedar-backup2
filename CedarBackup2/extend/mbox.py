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
# Copyright (c) 2006 Kenneth J. Pronovici.
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
# Purpose  : Provides an extension to back up mbox email files.
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

########################################################################
# Module documentation
########################################################################

"""
Provides an extension to back up mbox email files.

Backing up email
================

   Email folders (often stored as mbox flatfiles) are not well-suited being backed
   up with an incremental backup like the one offered by Cedar Backup.  This is
   because mbox files often change on a daily basis, forcing the incremental
   backup process to back them up every day in order to avoid losing data.  This
   can result in quite a bit of wasted space when backing up large folders.  (Note
   that the alternative maildir format does not share this problem, since it
   typically uses one file per message.)

   One solution to this problem is to design a smarter incremental backup process,
   which backs up baseline content on the first day of the week, and then backs up
   only new messages added to that folder on every other day of the week.  This way,
   the backup for any single day is only as large as the messages placed into the 
   folder on that day.  The backup isn't as "perfect" as the incremental backup
   process, because it doesn't preserve information about messages deleted from
   the backed-up folder.  However, it should be much more space-efficient, and
   in a recovery situation, it seems better to restore too much data rather
   than too little.

What is this extension?
=======================

   This is a Cedar Backup extension used to back up mbox email files via the Cedar
   Backup command line.  Individual mbox files or directories containing mbox
   files can be backed up using the same collect modes allowed for filesystems in
   the standard Cedar Backup collect action: weekly, daily, incremental.  It 
   implements the "smart" incremental backup process discussed above, using 
   functionality provided by the C{grepmail} utility.

   This extension requires a new configuration section <mbox> and is intended to
   be run either immediately before or immediately after the standard collect
   action.  Aside from its own configuration, it requires the options and collect
   configuration sections in the standard Cedar Backup configuration file.

   The mbox action is conceptually similar to the standard collect action,
   except that mbox directories are not collected recursively.  This implies
   some configuration changes (i.e. there's no need for global exclusions or an
   ignore file).

@author: Kenneth J. Pronovici <pronovic@ieee.org>
"""

########################################################################
# Imported modules
########################################################################

# System modules
import os
import logging
import datetime
from bz2 import BZ2File
from gzip import GzipFile

# Cedar Backup modules
from CedarBackup2.config import createInputDom, addContainerNode, addStringNode
from CedarBackup2.config import isElement, readChildren, readFirstChild, readString
from CedarBackup2.config import VALID_COLLECT_MODES, VALID_COMPRESS_MODES
from CedarBackup2.action import isStartOfWeek, buildNormalizedPath
from CedarBackup2.util import resolveCommand, executeCommand
from CedarBackup2.util import ObjectTypeList, UnorderedList, encodePath, changeOwnership
from CedarBackup2.xmlutil import readStringList, readString


########################################################################
# Module-wide constants and variables
########################################################################

logger = logging.getLogger("CedarBackup2.log.extend.mbox")

GREPMAIL_COMMAND = [ "grepmail", ]
REVISION_PATH_EXTENSION = "mboxlast"


########################################################################
# MboxFile class definition
########################################################################

class MboxFile(object):

   """
   Class representing mbox file configuration..

   The following restrictions exist on data in this class:

      - The absolute path must be absolute.
      - The collect mode must be one of the values in L{VALID_COLLECT_MODES}.
      - The compress mode must be one of the values in L{VALID_COMPRESS_MODES}.

   @sort: __init__, __repr__, __str__, __cmp__, absolutePath, collectMode, compressMode
   """

   def __init__(self, absolutePath=None, collectMode=None, compressMode=None):
      """
      Constructor for the C{MboxFile} class.

      You should never directly instantiate this class.
      
      @param absolutePath: Absolute path to an mbox file on disk.
      @param collectMode: Overridden collect mode for this directory.
      @param compressMode: Overridden compression mode for this directory.
      """
      self._absolutePath = None
      self._collectMode = None
      self._compressMode = None
      self.absolutePath = absolutePath
      self.collectMode = collectMode
      self.compressMode = compressMode

   def __repr__(self):
      """
      Official string representation for class instance.
      """
      return "MboxFile(%s, %s, %s)" % (self.absolutePath, self.collectMode, self.compressMode)

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

   absolutePath = property(_getAbsolutePath, _setAbsolutePath, None, doc="Absolute path to the mbox file.")
   collectMode = property(_getCollectMode, _setCollectMode, None, doc="Overridden collect mode for this mbox file.")
   compressMode = property(_getCompressMode, _setCompressMode, None, doc="Overridden compress mode for this mbox file.")


########################################################################
# MboxDir class definition
########################################################################

class MboxDir(object):

   """
   Class representing mbox directory configuration..

   The following restrictions exist on data in this class:

      - The absolute path must be absolute.
      - The collect mode must be one of the values in L{VALID_COLLECT_MODES}.
      - The compress mode must be one of the values in L{VALID_COMPRESS_MODES}.

   Unlike collect directory configuration, this is the only place exclusions
   are allowed (no global exclusions at the <mbox> configuration level).  Also,
   we only allow relative exclusions and there is no configured ignore file.
   This is because mbox directory backups are not recursive.

   @sort: __init__, __repr__, __str__, __cmp__, absolutePath, collectMode, 
          compressMode, relativeExcludePaths, excludePatterns
   """

   def __init__(self, absolutePath=None, collectMode=None, compressMode=None,
                relativeExcludePaths=None, excludePatterns=None):
      """
      Constructor for the C{MboxDir} class.

      You should never directly instantiate this class.
      
      @param absolutePath: Absolute path to a mbox file on disk.
      @param collectMode: Overridden collect mode for this directory.
      @param compressMode: Overridden compression mode for this directory.
      @param relativeExcludePaths: List of relative paths to exclude.
      @param excludePatterns: List of regular expression patterns to exclude
      """
      self._absolutePath = None
      self._collectMode = None
      self._compressMode = None
      self._relativeExcludePaths = None
      self._excludePatterns = None
      self.absolutePath = absolutePath
      self.collectMode = collectMode
      self.compressMode = compressMode
      self.relativeExcludePaths = relativeExcludePaths
      self.excludePatterns = excludePatterns

   def __repr__(self):
      """
      Official string representation for class instance.
      """
      return "MboxDir(%s, %s, %s, %s, %s)" % (self.absolutePath, self.collectMode, self.compressMode,
                                              self.relativeExcludePaths, self.excludePatterns)

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

   absolutePath = property(_getAbsolutePath, _setAbsolutePath, None, doc="Absolute path to the mbox directory.")
   collectMode = property(_getCollectMode, _setCollectMode, None, doc="Overridden collect mode for this mbox directory.")
   compressMode = property(_getCompressMode, _setCompressMode, None, doc="Overridden compress mode for this mbox directory.")
   relativeExcludePaths = property(_getRelativeExcludePaths, _setRelativeExcludePaths, None, "List of relative paths to exclude.")
   excludePatterns = property(_getExcludePatterns, _setExcludePatterns, None, "List of regular expression patterns to exclude.")


########################################################################
# MboxConfig class definition
########################################################################

class MboxConfig(object):

   """
   Class representing mbox configuration.

   Mbox configuration is used for backing up mbox email files.

   The following restrictions exist on data in this class:

      - The collect mode must be one of the values in L{VALID_COLLECT_MODES}.
      - The compress mode must be one of the values in L{VALID_COMPRESS_MODES}.
      - The C{mboxFiles} list must be a list of C{MboxFile} objects
      - The C{mboxDirs} list must be a list of C{MboxDir} objects

   For the C{mboxFiles} and C{mboxDirs} lists, validation is accomplished
   through the L{util.ObjectTypeList} list implementation that overrides common
   list methods and transparently ensures that each element is of the proper
   type.

   Unlike collect configuration, no global exclusions are allowed on this
   level.  We only allow relative exclusions at the mbox directory level.
   Also, there is no configured ignore file.  This is because mbox directory
   backups are not recursive.

   @note: Lists within this class are "unordered" for equality comparisons.

   @sort: __init__, __repr__, __str__, __cmp__, collectMode, compressMode, mboxFiles, mboxDirs
   """

   def __init__(self, collectMode=None, compressMode=None, mboxFiles=None, mboxDirs=None):
      """
      Constructor for the C{MboxConfig} class.

      @param collectMode: Default collect mode.
      @param compressMode: Default compress mode.
      @param mboxFiles: List of mbox files to back up
      @param mboxDirs: List of mbox directories to back up

      @raise ValueError: If one of the values is invalid.
      """
      self._collectMode = None
      self._compressMode = None
      self._mboxFiles = None
      self._mboxDirs = None
      self.collectMode = collectMode
      self.compressMode = compressMode
      self.mboxFiles = mboxFiles
      self.mboxDirs = mboxDirs

   def __repr__(self):
      """
      Official string representation for class instance.
      """
      return "MboxConfig(%s, %s, %s, %s)" % (self.collectMode, self.compressMode, self.mboxFiles, self.mboxDirs)

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
      if self._mboxFiles != other._mboxFiles:
         if self._mboxFiles < other._mboxFiles:
            return -1
         else:
            return 1
      if self._mboxDirs != other._mboxDirs:
         if self._mboxDirs < other._mboxDirs:
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

   def _setMboxFiles(self, value):
      """
      Property target used to set the mboxFiles list.
      Either the value must be C{None} or each element must be an C{MboxFile}.
      @raise ValueError: If the value is not an C{MboxFile}
      """
      if value is None:
         self._mboxFiles = None
      else:
         try:
            saved = self._mboxFiles
            self._mboxFiles = ObjectTypeList(MboxFile, "MboxFile")
            self._mboxFiles.extend(value)
         except Exception, e:
            self._mboxFiles = saved
            raise e

   def _getMboxFiles(self):
      """
      Property target used to get the mboxFiles list.
      """
      return self._mboxFiles

   def _setMboxDirs(self, value):
      """
      Property target used to set the mboxDirs list.
      Either the value must be C{None} or each element must be an C{MboxDir}.
      @raise ValueError: If the value is not an C{MboxDir}
      """
      if value is None:
         self._mboxDirs = None
      else:
         try:
            saved = self._mboxDirs
            self._mboxDirs = ObjectTypeList(MboxDir, "MboxDir")
            self._mboxDirs.extend(value)
         except Exception, e:
            self._mboxDirs = saved
            raise e

   def _getMboxDirs(self):
      """
      Property target used to get the mboxDirs list.
      """
      return self._mboxDirs

   collectMode = property(_getCollectMode, _setCollectMode, None, doc="Default collect mode.")
   compressMode = property(_getCompressMode, _setCompressMode, None, doc="Default compress mode.")
   mboxFiles = property(_getMboxFiles, _setMboxFiles, None, doc="List of mbox files to back up.")
   mboxDirs = property(_getMboxDirs, _setMboxDirs, None, doc="List of mbox directories to back up.")


########################################################################
# LocalConfig class definition
########################################################################

class LocalConfig(object):

   """
   Class representing this extension's configuration document.

   This is not a general-purpose configuration object like the main Cedar
   Backup configuration object.  Instead, it just knows how to parse and emit
   Mbox-specific configuration values.  Third parties who need to read and
   write configuration related to this extension should access it through the
   constructor, C{validate} and C{addConfig} methods.

   @note: Lists within this class are "unordered" for equality comparisons.

   @sort: __init__, __repr__, __str__, __cmp__, mbox, validate, addConfig
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
      self._mbox = None
      self.mbox = None
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
      return "LocalConfig(%s)" % (self.mbox)

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
      if self._mbox != other._mbox:
         if self._mbox < other._mbox:
            return -1
         else:
            return 1
      return 0

   def _setMbox(self, value):
      """
      Property target used to set the mbox configuration value.
      If not C{None}, the value must be a C{MboxConfig} object.
      @raise ValueError: If the value is not a C{MboxConfig}
      """
      if value is None:
         self._mbox = None
      else:
         if not isinstance(value, MboxConfig):
            raise ValueError("Value must be a C{MboxConfig} object.")
         self._mbox = value

   def _getMbox(self):
      """
      Property target used to get the mbox configuration value.
      """
      return self._mbox

   mbox = property(_getMbox, _setMbox, None, "Mbox configuration in terms of a C{MboxConfig} object.")

   def validate(self):
      """
      Validates configuration represented by the object.

      Mbox configuration must be filled in.  Within that, the collect mode and
      compress mode are both optional, but the list of repositories must
      contain at least one entry.

      Each configured file or directory must contain an absolute path, and then
      must be either able to take collect mode and compress mode configuration
      from the parent C{MboxConfig} object, or must set each value on its own.

      @raise ValueError: If one of the validations fails.
      """
      if self.mbox is None:
         raise ValueError("Mbox section is required.")
      if ((self.mbox.mboxFiles is None or len(self.mbox.mboxFiles) < 1) and \
          (self.mbox.mboxDirs is None or len(self.mbox.mboxDirs) < 1)):
         raise ValueError("At least one mbox file or directory must be configured.")
      if self.mbox.mboxFiles is not None:
         for mboxFile in self.mbox.mboxFiles:
            if mboxFile.absolutePath is None:
               raise ValueError("Each mbox file must set an absolute path.")
            if self.mbox.collectMode is None and mboxFile.collectMode is None:
               raise ValueError("Collect mode must either be set in parent mbox section or individual mbox file.")
            if self.mbox.compressMode is None and mboxFile.compressMode is None:
               raise ValueError("Compress mode must either be set in parent mbox section or individual mbox file.")
      if self.mbox.mboxDirs is not None:
         for mboxDir in self.mbox.mboxDirs:
            if mboxDir.absolutePath is None:
               raise ValueError("Each mbox directory must set an absolute path.")
            if self.mbox.collectMode is None and mboxDir.collectMode is None:
               raise ValueError("Collect mode must either be set in parent mbox section or individual mbox directory.")
            if self.mbox.compressMode is None and mboxDir.compressMode is None:
               raise ValueError("Compress mode must either be set in parent mbox section or individual mbox directory.")

   def addConfig(self, xmlDom, parentNode):
      """
      Adds an <mbox> configuration section as the next child of a parent.

      Third parties should use this function to write configuration related to
      this extension.

      We add the following fields to the document::

         collectMode    //cb_config/mbox/collectMode
         compressMode   //cb_config/mbox/compressMode

      We also add groups of the following items, one list element per
      item::

         mboxFiles      //cb_config/mbox/file
         mboxDirs       //cb_config/mbox/dir

      The mbox files and mbox directories are added by L{_addMboxFile} and
      L{_addMboxDir}.

      @param xmlDom: DOM tree as from C{impl.createDocument()}.
      @param parentNode: Parent that the section should be appended to.
      """
      if self.mbox is not None:
         sectionNode = addContainerNode(xmlDom, parentNode, "mbox")
         addStringNode(xmlDom, sectionNode, "collect_mode", self.mbox.collectMode)
         addStringNode(xmlDom, sectionNode, "compress_mode", self.mbox.compressMode)
         if self.mbox.mboxFiles is not None:
            for mboxFile in self.mbox.mboxFiles:
               LocalConfig._addMboxFile(xmlDom, sectionNode, mboxFile)
         if self.mbox.mboxDirs is not None:
            for mboxDir in self.mbox.mboxDirs:
               LocalConfig._addMboxDir(xmlDom, sectionNode, mboxDir)

   def _parseXmlData(self, xmlData):
      """
      Internal method to parse an XML string into the object.

      This method parses the XML document into a DOM tree (C{xmlDom}) and then
      calls a static method to parse the mbox configuration section.

      @param xmlData: XML data to be parsed
      @type xmlData: String data

      @raise ValueError: If the XML cannot be successfully parsed.
      """
      (xmlDom, parentNode) = createInputDom(xmlData)
      self._mbox = LocalConfig._parseMbox(parentNode)

   def _parseMbox(parent):
      """
      Parses an mbox configuration section.
      
      We read the following individual fields::

         collectMode    //cb_config/mbox/collect_mode
         compressMode   //cb_config/mbox/compress_mode

      We also read groups of the following item, one list element per
      item::

         mboxFiles      //cb_config/mbox/file
         mboxDirs       //cb_config/mbox/dir

      The mbox files are parsed by L{_parseMboxFiles} and the mbox
      directories are parsed by L{_parseMboxDirs}.

      @param parent: Parent node to search beneath.

      @return: C{MboxConfig} object or C{None} if the section does not exist.
      @raise ValueError: If some filled-in value is invalid.
      """
      mbox = None
      section = readFirstChild(parent, "mbox")
      if section is not None:
         mbox = MboxConfig()
         mbox.collectMode = readString(section, "collect_mode")
         mbox.compressMode = readString(section, "compress_mode")
         mbox.mboxFiles = LocalConfig._parseMboxFiles(section)
         mbox.mboxDirs = LocalConfig._parseMboxDirs(section)
      return mbox
   _parseMbox = staticmethod(_parseMbox)

   def _parseMboxFiles(parent):
      """
      Reads a list of C{MboxFile} objects from immediately beneath the parent.

      We read the following individual fields::

         absolutePath            abs_path
         collectMode             collect_mode
         compressMode            compess_mode 

      @param parent: Parent node to search beneath.

      @return: List of C{MboxFile} objects or C{None} if none are found.
      @raise ValueError: If some filled-in value is invalid.
      """
      lst = []
      for entry in readChildren(parent, "file"):
         if isElement(entry):
            mboxFile = MboxFile()
            mboxFile.absolutePath = readString(entry, "abs_path")
            mboxFile.collectMode = readString(entry, "collect_mode")
            mboxFile.compressMode = readString(entry, "compress_mode")
            lst.append(mboxFile)
      if lst == []:
         lst = None
      return lst
   _parseMboxFiles = staticmethod(_parseMboxFiles)

   def _parseMboxDirs(parent):
      """
      Reads a list of C{MboxDir} objects from immediately beneath the parent.

      We read the following individual fields::

         absolutePath            abs_path
         collectMode             collect_mode
         compressMode            compess_mode 

      We also read groups of the following items, one list element per
      item::

         relativeExcludePaths    exclude/rel_path
         excludePatterns         exclude/pattern

      The exclusions are parsed by L{_parseExclusions}.

      @param parent: Parent node to search beneath.

      @return: List of C{MboxDir} objects or C{None} if none are found.
      @raise ValueError: If some filled-in value is invalid.
      """
      lst = []
      for entry in readChildren(parent, "dir"):
         if isElement(entry):
            mboxDir = MboxDir()
            mboxDir.absolutePath = readString(entry, "abs_path")
            mboxDir.collectMode = readString(entry, "collect_mode")
            mboxDir.compressMode = readString(entry, "compress_mode")
            (mboxDir.relativeExcludePaths, mboxDir.excludePatterns) = LocalConfig._parseExclusions(entry)
            lst.append(mboxDir)
      if lst == []:
         lst = None
      return lst
   _parseMboxDirs = staticmethod(_parseMboxDirs)

   def _parseExclusions(parentNode):
      """
      Reads exclusions data from immediately beneath the parent.

      We read groups of the following items, one list element per item::

         relative    exclude/rel_path
         patterns    exclude/pattern

      If there are none of some pattern (i.e. no relative path items) then
      C{None} will be returned for that item in the tuple.  

      @param parentNode: Parent node to search beneath.

      @return: Tuple of (relative, patterns) exclusions.
      """
      section = readFirstChild(parentNode, "exclude")
      if section is None:
         return (None, None)
      else:
         relative = readStringList(section, "rel_path")
         patterns = readStringList(section, "pattern")
         return (relative, patterns)
   _parseExclusions = staticmethod(_parseExclusions)

   def _addMboxFile(xmlDom, parentNode, mboxFile):
      """
      Adds an mbox file container as the next child of a parent.

      We add the following fields to the document::

         absolutePath            file/abs_path
         collectMode             file/collect_mode
         compressMode            file/compress_mode

      The <file> node itself is created as the next child of the parent node.
      This method only adds one mbox file node.  The parent must loop for each
      mbox file in the C{MboxConfig} object.

      If C{mboxFile} is C{None}, this method call will be a no-op.

      @param xmlDom: DOM tree as from C{impl.createDocument()}.
      @param parentNode: Parent that the section should be appended to.
      @param mboxFile: MboxFile to be added to the document.
      """
      if mboxFile is not None:
         sectionNode = addContainerNode(xmlDom, parentNode, "file")
         addStringNode(xmlDom, sectionNode, "abs_path", mboxFile.absolutePath)
         addStringNode(xmlDom, sectionNode, "collect_mode", mboxFile.collectMode)
         addStringNode(xmlDom, sectionNode, "compress_mode", mboxFile.compressMode)
   _addMboxFile = staticmethod(_addMboxFile)

   def _addMboxDir(xmlDom, parentNode, mboxDir):
      """
      Adds an mbox directory container as the next child of a parent.

      We add the following fields to the document::

         absolutePath            dir/abs_path
         collectMode             dir/collect_mode
         compressMode            dir/compress_mode

      We also add groups of the following items, one list element per item::

         relativeExcludePaths    dir/exclude/rel_path
         excludePatterns         dir/exclude/pattern

      The <dir> node itself is created as the next child of the parent node.
      This method only adds one mbox directory node.  The parent must loop for
      each mbox directory in the C{MboxConfig} object.

      If C{mboxDir} is C{None}, this method call will be a no-op.

      @param xmlDom: DOM tree as from C{impl.createDocument()}.
      @param parentNode: Parent that the section should be appended to.
      @param mboxDir: MboxDir to be added to the document.
      """
      if mboxDir is not None:
         sectionNode = addContainerNode(xmlDom, parentNode, "dir")
         addStringNode(xmlDom, sectionNode, "abs_path", mboxDir.absolutePath)
         addStringNode(xmlDom, sectionNode, "collect_mode", mboxDir.collectMode)
         addStringNode(xmlDom, sectionNode, "compress_mode", mboxDir.compressMode)
         if ((mboxDir.relativeExcludePaths is not None and mboxDir.relativeExcludePaths != []) or
             (mboxDir.excludePatterns is not None and mboxDir.excludePatterns != [])):
            excludeNode = addContainerNode(xmlDom, sectionNode, "exclude")
            if mboxDir.relativeExcludePaths is not None:
               for relativePath in mboxDir.relativeExcludePaths:
                  addStringNode(xmlDom, excludeNode, "rel_path", relativePath)
            if mboxDir.excludePatterns is not None:
               for pattern in mboxDir.excludePatterns:
                  addStringNode(xmlDom, excludeNode, "pattern", pattern)
   _addMboxDir = staticmethod(_addMboxDir)


########################################################################
# Public functions
########################################################################

###########################
# executeAction() function
###########################

def executeAction(configPath, options, config):
   """
   Executes the mbox backup action.

   @param configPath: Path to configuration file on disk.
   @type configPath: String representing a path on disk.

   @param options: Program command-line options.
   @type options: Options object.

   @param config: Program configuration.
   @type config: Config object.

   @raise ValueError: Under many generic error conditions
   @raise IOError: If a backup could not be written for some reason.
   """
   logger.debug("Executing mbox extended action.")
   newRevision = datetime.today()  # mark here so all actions are after this date/time
   if config.options is None or config.collect is None:
      raise ValueError("Cedar Backup configuration is not properly filled in.")
   local = LocalConfig(xmlPath=configPath)
   todayIsStart = isStartOfWeek(config.options.startingDay)
   fullBackup = options.full or todayIsStart
   logger.debug("Full backup flag is [%s]" % fullBackup)
   if local.mbox.mboxFiles is not None:
      for mboxFile in local.mbox.mboxFiles:
         logger.debug("Working with mbox file [%s]" % mboxFile.absolutePath)
         collectMode = _getCollectMode(local, mboxFile)
         compressMode = _getCompressMode(local, mboxFile)
         lastRevision = _loadLastRevision(local, mboxFile, fullBackup, collectMode)
         if fullBackup or (collectMode in ['daily', 'incr', ]) or (collectMode == 'weekly' and todayIsStart):
            logger.debug("Mbox file meets criteria to be backed up today.")
            _backupMboxFile(config, mboxFile.absolutePath, lastRevision, fullBackup, collectMode, compressMode)
         else:
            logger.debug("Mbox file will not be backed up, per collect mode.")
         if collectMode == 'incr':
            _writeLastRevision(config, newRevision)
         logger.info("Completed backing up mbox file [%s]." % mboxFile.absolutePath)
   if local.mbox.mboxDirs is not None:
      for mboxDir in local.mbox.mboxDirs:
         logger.debug("Working with mbox directory [%s]" % mboxDir.absolutePath)
         collectMode = _getCollectMode(local, mboxDir)
         compressMode = _getCompressMode(local, mboxDir)
         lastRevision = _loadLastRevision(local, mboxFile, fullBackup, collectMode)
         (excludePaths, excludePatterns) = _getExclusions(config, mboxDir)
         if fullBackup or (collectMode in ['daily', 'incr', ]) or (collectMode == 'weekly' and todayIsStart):
            logger.debug("Mbox directory meets criteria to be backed up today.")
            _backupMboxDir(config, mboxDir.absolutePath, lastRevision, fullBackup, collectMode, 
                           compressMode, excludePaths, excludePatterns)
         else:
            logger.debug("Mbox directory will not be backed up, per collect mode.")
         if collectMode == 'incr':
            _writeLastRevision(config, newRevision)
         logger.info("Completed backing up mbox directory [%s]." % mboxDir.absolutePath)
   logger.info("Executed the mbox extended action successfully.")

def _getCollectMode(local, item):
   """
   Gets the collect mode that should be used for an mbox file or directory. 
   Use file- or directory-specific value if possible, otherwise take from mbox section.
   @param local: LocalConfig object.
   @param item: Mbox file or directory
   @return: Collect mode to use.
   """
   if item.collectMode is None:
      collectMode = local.mbox.collectMode
   else:
      collectMode = item.collectMode
   logger.debug("Collect mode is [%s]" % collectMode)
   return collectMode

def _getCompressMode(local, item):
   """
   Gets the compress mode that should be used for an mbox file or directory.
   Use file- or directory-specific value if possible, otherwise take from mbox section.
   @param local: LocalConfig object.
   @param item: Mbox file or directory
   @return: Compress mode to use.
   """
   if item.compressMode is None:
      compressMode = local.mbox.compressMode
   else:
      compressMode = item.compressMode
   logger.debug("Compress mode is [%s]" % compressMode)
   return compressMode

def _getRevisionPath(config, item):
   """
   Gets the path to the revision file associated with a repository.
   @param config: LocalConfig object.
   @param item: Mbox file or directory
   @return: Absolute path to the revision file associated with the repository.
   """
   normalized = buildNormalizedPath(item.absolutePath)
   filename = "%s.%s" % (normalized, REVISION_PATH_EXTENSION)
   revisionPath = os.path.join(config.options.workingDir, filename)
   logger.debug("Revision file path is [%s]" % revisionPath)
   return revisionPath

def _loadLastRevision(config, item, fullBackup, collectMode):
   """
   Loads the last revision date for this item from disk and returns it.

   If this is a full backup, or if the revision file cannot be loaded for some
   reason, then C{None} is returned.  This indicates that there is no previous
   revision, so the entire mail file or directory should be backed up.

   @param config: LocalConfig object.
   @param item: Mbox file or directory
   @param fullBackup: Indicates whether this is a full backup
   @param collectMode: Indicates the collect mode for this item

   @return: Revision date as a datetime.datetime object or C{None}.
   """
   revisionPath = _getRevisionPath(config, item)
   if fullBackup:
      revisionDate = None
      logger.debug("Revision file ignored because this is a full backup.")
   elif collectMode in ['weekly', 'daily']:
      revisionDate = None
      logger.debug("No revision file based on collect mode [%s]." % collectMode)
   else:
      logger.debug("Revision file will be used for non-full incremental backup.")
      if not os.path.isfile(revisionPath):
         revisionDate = None
         logger.debug("Revision file [%s] does not exist on disk." % revisionPath)
      else:
         try:
            revisionDate = pickle.load(open(revisionPath, "r"))
            logger.debug("Loaded revision file [%s] from disk: [%s]" % (revisionPath, revisionDate))
         except:
            revisionDate = None
            logger.error("Failed loading revision file [%s] from disk." % revisionPath)
   return revisionDate

def _writeLastRevision(config, lastRevision):
   """
   Writes last revision to the revision file on disk.

   If we can't write the revision file successfully for any reason, we'll log
   the condition but won't throw an exception.

   @param config: Config object.
   @param lastRevision: Revision date as a datetime.datetime object.
   """
   revisionPath = _getRevisionPath(config, item)
   try:
      pickle.dump(lastRevision, open(revisionPath, "w"))
      changeOwnership(revisionPath, config.options.backupUser, config.options.backupGroup)
      logger.debug("Wrote new revision file [%s] to disk: [%d]" % (revisionPath, lastRevision))
   except:
      logger.error("Failed to write revision file [%s] to disk." % revisionPath)

def _getExclusions(config, mboxDir):
   """
   Gets exclusions (file and patterns) associated with an mbox directory.

   The returned files value is a list of absolute paths to be excluded from the
   backup for a given directory.  It is derived from the mbox directory's
   relative exclude paths.
   
   The returned patterns value is a list of patterns to be excluded from the
   backup for a given directory.  It is derived from the mbox directory's list
   of patterns.

   @param config: Config object.
   @param mboxDir: Mbox directory object.

   @return: Tuple (files, patterns) indicating what to exclude.
   """
   paths = []
   if mboxDir.relativeExcludePaths is not None:
      for relativePath in mboxDir.relativeExcludePaths:
         paths.append(os.path.join(mboxDir.absolutePath, relativePath))
   patterns = []
   if mboxDir.excludePatterns is not None:
      patterns.extend(mboxDir.excludePatterns)
   logger.debug("Exclude paths: %s" % paths)
   logger.debug("Exclude patterns: %s" % patterns)
   return(paths, patterns)

def _backupMboxFile(config, absolutePath, lastRevision, fullBackup, 
                    collectMode, compressMode):
   """
   Backs up an individual mbox file.

   @param config: Cedar Backup configuration.
   @param absolutePath: Path to mbox file to back up.
   @param lastRevision: Date of last backup as datetime.datetime
   @param fullBackup: Indicates whether this should be a full backup.
   @param collectMode: Collect mode to use.
   @param compressMode: Compress mode to use.
    
   @raise ValueError: If some value is missing or invalid.
   @raise IOError: If there is a problem backing up the mbox file.
   """
   pass

def _backupMboxDir(config, absolutePath, lastRevision, fullBackup, collectMode, 
                   compressMode, excludePaths, excludePatterns):
   """
   Backs up a directory containing mbox files.

   @param config: Cedar Backup configuration.
   @param absolutePath: Path to mbox directory to back up.
   @param lastRevision: Date of last backup as datetime.datetime
   @param fullBackup: Indicates whether this should be a full backup.
   @param collectMode: Collect mode to use.
   @param compressMode: Compress mode to use.
   @param excludePaths: List of absolute paths to exclude.
   @param excludePatterns: List of patterns to exclude.
    
   @raise ValueError: If some value is missing or invalid.
   @raise IOError: If there is a problem backing up the mbox file.
   """
   pass

