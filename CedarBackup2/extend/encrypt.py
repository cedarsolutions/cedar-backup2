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
# Copyright (c) 2007 Kenneth J. Pronovici.
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
# Purpose  : Provides an extension to encrypt staging directories.
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

########################################################################
# Module documentation
########################################################################

"""
Provides an extension to encrypt staging directories.

When this extension is executed, all backed-up files in the configured Cedar
Backup staging directory will be encrypted using gpg.  Any directory which has
already been encrypted (as indicated by the C{cback.encrypt} file) will be
ignored.

This extension requires a new configuration section <encrypt> and is intended
to be run immediately after the standard stage action.  Aside from its own
configuration, it requires the options and staging configuration sections in
the standard Cedar Backup configuration file.

@author: Kenneth J. Pronovici <pronovic@ieee.org>
"""

########################################################################
# Imported modules
########################################################################

# System modules
import os
import logging

# Cedar Backup modules
from CedarBackup2.filesystem import FilesystemList
from CedarBackup2.util import resolveCommand, executeCommand
from CedarBackup2.util import encodePath, changeOwnership
from CedarBackup2.xmlutil import createInputDom, addContainerNode, addStringNode
from CedarBackup2.xmlutil import isElement, readChildren, readFirstChild, readString, readStringList


########################################################################
# Module-wide constants and variables
########################################################################

logger = logging.getLogger("CedarBackup2.log.extend.encrypt")

GPG_COMMAND = [ "gpg", ]
VALID_ENCRYPT_MODES = [ "gpg", ]
ENCRYPT_INDICATOR = "cback.encrypt"
INDICATOR_PATTERNS = [ "cback\..*", ]


########################################################################
# EncryptConfig class definition
########################################################################

class EncryptConfig(object):

   """
   Class representing encrypt configuration.

   Encrypt configuration is used for encrypting staging directories.

   The following restrictions exist on data in this class:

      - The encrypt mode must be one of the values in L{VALID_ENCRYPT_MODES}
      - The encrypt target value must be a non-empty string

   @sort: __init__, __repr__, __str__, __cmp__, encryptMode, encryptTarget
   """

   def __init__(self, encryptMode=None, encryptTarget=None):
      """
      Constructor for the C{EncryptConfig} class.

      @param encryptMode: Encryption mode
      @param encryptTarget: Encryption target (for instance, GPG recipient)

      @raise ValueError: If one of the values is invalid.
      """
      self._encryptMode = None
      self._encryptTarget = None
      self.encryptMode = encryptMode
      self.encryptTarget = encryptTarget

   def __repr__(self):
      """
      Official string representation for class instance.
      """
      return "EncryptConfig(%s, %s)" % (self.encryptMode, self.encryptTarget)

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
      if self._encryptMode != other._encryptMode:
         if self._encryptMode < other._encryptMode:
            return -1
         else:
            return 1
      if self._encryptTarget != other._encryptTarget:
         if self._encryptTarget < other._encryptTarget:
            return -1
         else:
            return 1
      return 0

   def _setEncryptMode(self, value):
      """
      Property target used to set the encrypt mode.
      If not C{None}, the mode must be one of the values in L{VALID_ENCRYPT_MODES}.
      @raise ValueError: If the value is not valid.
      """
      if value is not None:
         if value not in VALID_ENCRYPT_MODES:
            raise ValueError("Encrypt mode must be one of %s." % VALID_ENCRYPT_MODES)
      self._encryptMode = value

   def _getEncryptMode(self):
      """
      Property target used to get the encrypt mode.
      """
      return self._encryptMode

   def _setEncryptTarget(self, value):
      """
      Property target used to set the encrypt target.
      """
      if value is not None:
         if len(value) < 1:
            raise ValueError("Encrypt target must be non-empty string.")
      self._encryptTarget = value

   def _getEncryptTarget(self):
      """
      Property target used to get the encrypt target.
      """
      return self._encryptTarget

   encryptMode = property(_getEncryptMode, _setEncryptMode, None, doc="Encrypt mode.")
   encryptTarget = property(_getEncryptTarget, _setEncryptTarget, None, doc="Encrypt target (i.e. GPG recipient).")


########################################################################
# LocalConfig class definition
########################################################################

class LocalConfig(object):

   """
   Class representing this extension's configuration document.

   This is not a general-purpose configuration object like the main Cedar
   Backup configuration object.  Instead, it just knows how to parse and emit
   encrypt-specific configuration values.  Third parties who need to read and
   write configuration related to this extension should access it through the
   constructor, C{validate} and C{addConfig} methods.

   @note: Lists within this class are "unordered" for equality comparisons.

   @sort: __init__, __repr__, __str__, __cmp__, encrypt, validate, addConfig
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
      self._encrypt = None
      self.encrypt = None
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
      return "LocalConfig(%s)" % (self.encrypt)

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
      if self._encrypt != other._encrypt:
         if self._encrypt < other._encrypt:
            return -1
         else:
            return 1
      return 0

   def _setEncrypt(self, value):
      """
      Property target used to set the encrypt configuration value.
      If not C{None}, the value must be a C{EncryptConfig} object.
      @raise ValueError: If the value is not a C{EncryptConfig}
      """
      if value is None:
         self._encrypt = None
      else:
         if not isinstance(value, EncryptConfig):
            raise ValueError("Value must be a C{EncryptConfig} object.")
         self._encrypt = value

   def _getEncrypt(self):
      """
      Property target used to get the encrypt configuration value.
      """
      return self._encrypt

   encrypt = property(_getEncrypt, _setEncrypt, None, "Encrypt configuration in terms of a C{EncryptConfig} object.")

   def validate(self):
      """
      Validates configuration represented by the object.

      Encrypt configuration must be filled in.  Within that, both the encrypt
      mode and encrypt target must be filled in.

      @raise ValueError: If one of the validations fails.
      """
      if self.encrypt is None:
         raise ValueError("Encrypt section is required.")
      if self.encrypt.encryptMode is None:
         raise ValueError("Encrypt mode must be set.")
      if self.encrypt.encryptTarget is None:
         raise ValueError("Encrypt target must be set.")

   def addConfig(self, xmlDom, parentNode):
      """
      Adds an <encrypt> configuration section as the next child of a parent.

      Third parties should use this function to write configuration related to
      this extension.

      We add the following fields to the document::

         encryptMode    //cb_config/encrypt/encrypt_mode
         encryptTarget  //cb_config/encrypt/encrypt_target

      @param xmlDom: DOM tree as from C{impl.createDocument()}.
      @param parentNode: Parent that the section should be appended to.
      """
      if self.encrypt is not None:
         sectionNode = addContainerNode(xmlDom, parentNode, "encrypt")
         addStringNode(xmlDom, sectionNode, "encrypt_mode", self.encrypt.encryptMode)
         addStringNode(xmlDom, sectionNode, "encrypt_target", self.encrypt.encryptTarget)

   def _parseXmlData(self, xmlData):
      """
      Internal method to parse an XML string into the object.

      This method parses the XML document into a DOM tree (C{xmlDom}) and then
      calls a static method to parse the encrypt configuration section.

      @param xmlData: XML data to be parsed
      @type xmlData: String data

      @raise ValueError: If the XML cannot be successfully parsed.
      """
      (xmlDom, parentNode) = createInputDom(xmlData)
      self._encrypt = LocalConfig._parseEncrypt(parentNode)

   def _parseEncrypt(parent):
      """
      Parses an encrypt configuration section.
      
      We read the following individual fields::

         encryptMode    //cb_config/encrypt/encrypt_mode
         encryptTarget  //cb_config/encrypt/encrypt_target

      @param parent: Parent node to search beneath.

      @return: C{EncryptConfig} object or C{None} if the section does not exist.
      @raise ValueError: If some filled-in value is invalid.
      """
      encrypt = None
      section = readFirstChild(parent, "encrypt")
      if section is not None:
         encrypt = EncryptConfig()
         encrypt.encryptMode = readString(section, "encrypt_mode")
         encrypt.encryptTarget = readString(section, "encrypt_target")
      return encrypt
   _parseEncrypt = staticmethod(_parseEncrypt)


########################################################################
# Public functions
########################################################################

###########################
# executeAction() function
###########################

def executeAction(configPath, options, config):
   """
   Executes the encrypt backup action.

   @param configPath: Path to configuration file on disk.
   @type configPath: String representing a path on disk.

   @param options: Program command-line options.
   @type options: Options object.

   @param config: Program configuration.
   @type config: Config object.

   @raise ValueError: Under many generic error conditions
   @raise IOError: If there are I/O problems reading or writing files
   """
   logger.debug("Executing encrypt extended action.")
   if config.options is None or config.stage is None:
      raise ValueError("Cedar Backup configuration is not properly filled in.")
   local = LocalConfig(xmlPath=configPath)
   dailyDirs = _findDailyDirs(stagingDir=config.stage.targetDir)
   for dailyDir in dailyDirs:
      _encryptDailyDir(dailyDir, local.encrypt.encryptMode, local.encrypt.encryptTarget, 
                       config.options.backupUser, config.options.backupGroup)
      _writeIndicator(dailyDir, config.options.backupUser, config.options.backupGroup)
   logger.info("Executed the encrypt extended action successfully.")


############################
# _findDailyDirs() function
############################

def _findDailyDirs(stagingDir):
   """
   Returns a list of all daily staging directories that have not yet been
   encrypted.

   The encrypt indicator file C{cback.encrypt} will be written to a daily
   staging directory once that directory is encrypted.  So, this function looks
   at each daily staging directory within the configured staging directory, and
   returns a list of those which do not contain the indicator file.

   @param stagingDir: Configured staging directory (config.targetDir)

   @return: List of absolute paths to daily staging directories.
   """
   results = FilesystemList()
   yearDirs = FilesystemList()
   yearDirs.excludeFiles = True
   yearDirs.excludeLinks = True
   yearDirs.addDirContents(path=stagingDir, recursive=False, addSelf=False)
   for yearDir in yearDirs:
      monthDirs = FilesystemList()
      monthDirs.excludeFiles = True
      monthDirs.excludeLinks = True
      monthDirs.addDirContents(path=yearDir, recursive=False, addSelf=False)
      for monthDir in monthDirs:
         dailyDirs = FilesystemList()
         dailyDirs.excludeFiles = True
         dailyDirs.excludeLinks = True
         dailyDirs.addDirContents(path=monthDir, recursive=False, addSelf=False)
         for dailyDir in dailyDirs:
            if os.path.exists(os.path.join(dailyDir, ENCRYPT_INDICATOR)):
               logger.debug("Skipping directory [%s]; already encrypted." % dailyDir)
            else:
               logger.debug("Adding [%s] to list of directories to operate on." % dailyDir)
               results.append(dailyDir) # just put it in the list, no fancy operations
   return results


#################################
# _writeIndicatorFile() function
#################################

def _writeIndicator(dailyDir, backupUser, backupGroup):
   """
   Writes the encrypt indicator file into a daily staging directory.
   @param dailyDir: Daily staging directory
   @param backupUser: User that indicator file should be owned by
   @param backupGroup: Group that indicator file should be owned by
   """
   filename = os.path.join(dailyDir, ENCRYPT_INDICATOR)
   logger.debug("Writing encrypt indicator [%s]." % filename)
   try:
      open(filename, "w").write("")
      changeOwnership(filename, backupUser, backupGroup)
   except Exception, e:
      logger.error("Error writing encrypt indicator: %s" % e)


##############################
# _encryptDailyDir() function
##############################

def _encryptDailyDir(dailyDir, encryptMode, encryptTarget, backupUser, backupGroup):
   """
   Encrypts the contents of a daily staging directory.

   Files that match INDICATOR_PATTERNS (i.e. C{"cback.store"},
   C{"cback.stage"}, etc.) are assumed to be indicator files and are ignored.
   All other files are encrypted.

   The only valid encrypt mode is C{"gpg"}.

   @param dailyDir: Daily directory to encrypt
   @param encryptMode: Encryption mode (only "gpg" is allowed)
   @param encryptTarget: Encryption target (GPG recipient for "gpg" mode)
   @param backupUser: User that target files should be owned by
   @param backupGroup: Group that target files should be owned by

   @raise ValueError: If the encrypt mode is not supported.
   @raise ValueError: If the daily staging directory does not exist.
   """
   logger.debug("Begin encrypting contents of [%s]." % dailyDir)
   if not os.path.isdir(dailyDir):
      raise ValueError("Daily directory [%s] is not a directory or does not exist." % dailyDir);
   fileList = FilesystemList()
   fileList.excludeDirs = True
   fileList.excludeLinks = True
   fileList.excludeBasenamePatterns = INDICATOR_PATTERNS
   fileList.addDirContents(dailyDir)
   for path in fileList:
      _encryptFile(path, encryptMode, encryptTarget, backupUser, backupGroup, removeSource=True)
   logger.debug("Completed encrypting contents of [%s]." % dailyDir)


##########################
# _encryptFile() function
##########################

def _encryptFile(sourcePath, encryptMode, encryptTarget, backupUser, backupGroup, removeSource=False):
   """
   Encrypts the source file using the indicated mode.

   The encrypted file will be owned by the indicated backup user and group.  If
   C{removeSource} is C{True}, then the source file will be removed after it is
   successfully encrypted.

   Currently, only the C{"gpg"} encrypt mode is supported.

   @param sourcePath: Absolute path of the source file to encrypt
   @param encryptMode: Encryption mode (only "gpg" is allowed)
   @param encryptTarget: Encryption target (GPG recipient)
   @param backupUser: User that target files should be owned by
   @param backupGroup: Group that target files should be owned by
   @param removeSource: Indicates whether to remove the source file

   @return: Path to the newly-created encrypted file.

   @raise ValueError: If an invalid encrypt mode is passed in.
   @raise IOError: If there is a problem accessing, encrypting or removing the source file.
   """
   if not os.path.exists(sourcePath):
      raise ValueError("Source path [%s] does not exist." % sourcePath);
   if encryptMode == 'gpg':
      encryptedPath = _encryptFileWithGpg(sourcePath, recipient=encryptTarget)
   else:
      raise ValueError("Unknown encrypt mode [%s]" % encryptMode);
   changeOwnership(encryptedPath, backupUser, backupGroup)
   if removeSource:
      if os.path.exists(sourcePath):
         try: 
            os.remove(sourcePath)
            logger.debug("Completed removing old file [%s]." % sourcePath)
         except: 
            raise IOError("Failed to remove file [%s] after encrypting it." % (sourcePath))
   return encryptedPath


#################################
# _encryptFileWithGpg() function
#################################

def _encryptFileWithGpg(sourcePath, recipient):
   """
   Encrypts the indicated source file using GPG.

   The encrypted file will be in GPG's binary output format and will have the
   same name as the source file plus a C{".gpg"} extension.  The source file
   will not be modified or removed by this function call.

   @param sourcePath: Absolute path of file to be encrypted.
   @param recipient: Recipient name to be passed to GPG's C{"-r"} option
   
   @return: Path to the newly-created encrypted file.

   @raise IOError: If there is a problem encrypting the file.
   """
   encryptedPath = "%s.gpg" % sourcePath
   command = resolveCommand(GPG_COMMAND)
   args = [ "-e", "-r", recipient, "-o", encryptedPath, sourcePath, ]
   result = executeCommand(command, args)[0]
   if result != 0:
      raise IOError("Error [%d] calling [%s] to encrypt [%s]." % (result, command, sourcePath))
   if not os.path.exists(encryptedPath):
      raise IOError("After call to [%s], encrypted file [%s] does not exist." % (command, encryptedPath))
   logger.debug("Completed encrypting file [%s] to [%s]." % (sourcePath, encryptedPath))
   return encryptedPath
   
