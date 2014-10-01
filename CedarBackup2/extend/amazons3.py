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
# Copyright (c) 2014 Kenneth J. Pronovici.
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
# Language : Python (>= 2.5)
# Project  : Official Cedar Backup Extensions
# Revision : $Id$
# Purpose  : "Store" type extension that writes data to Amazon S3.
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

########################################################################
# Module documentation
########################################################################

"""
Store-type extension that writes data to Amazon S3.

This extension requires a new configuration section <amazons3> and is intended
to be run immediately after the standard stage action, replacing the standard
store action.  Aside from its own configuration, it requires the options and
staging configuration sections in the standard Cedar Backup configuration file.

This extension relies on the U{{Amazon S3Tools} <http://s3tools.org/>} package.
It is a very thin wrapper around the C{s3cmd put} command.  Before you use this
extension, you need to set up your Amazon S3 account and configure C{s3cmd} as
detailed in the U{{HOWTO} <http://s3tools.org/s3cmd-howto>}.  The configured
backup user will run the C{s3cmd} program, so make sure you configure S3 Tools
as that user, and not root.

It's up to you how to configure the S3 Tools connection to Amazon, but I
recommend that you configure GPG encrpytion using a strong passphrase.  One way
to generate a strong passphrase is using your random number generator, i.e.
C{dd if=/dev/urandom count=20 bs=1 | xxd -ps}.  (See U{{StackExchange}
<http://security.stackexchange.com/questions/14867/gpg-encryption-security>}
for more details about that advice.) If decide to use encryption, make sure you
save off the passphrase in a safe place, so you can get at your backup data
later if you need to.

This extension was written for and tested on Linux.  I do not expect it to
work on non-UNIX platforms.

@author: Kenneth J. Pronovici <pronovic@ieee.org>
"""

########################################################################
# Imported modules
########################################################################

# System modules
import os
import logging
import tempfile

# Cedar Backup modules
from CedarBackup2.util import resolveCommand, executeCommand
from CedarBackup2.xmlutil import createInputDom, addContainerNode, addStringNode
from CedarBackup2.xmlutil import readFirstChild, readString
from CedarBackup2.actions.util import findDailyDirs, writeIndicatorFile


########################################################################
# Module-wide constants and variables
########################################################################

logger = logging.getLogger("CedarBackup2.log.extend.amazons3")

S3CMD_COMMAND = [ "s3cmd", ]
STORE_INDICATOR = "cback.amazons3"


########################################################################
# AmazonS3Config class definition
########################################################################

class AmazonS3Config(object):

   """
   Class representing Amazon S3 configuration.

   Amazon S3 configuration is used for storing staging directories
   in Amazon's cloud storage using the C{s3cmd} tool.

   The following restrictions exist on data in this class:

      - The s3Bucket value must be a non-empty string

   @sort: __init__, __repr__, __str__, __cmp__, s3Bucket
   """

   def __init__(self, s3Bucket=None):
      """
      Constructor for the C{AmazonS3Config} class.

      @param s3Bucket: Name of the Amazon S3 bucket in which to store the data

      @raise ValueError: If one of the values is invalid.
      """
      self._s3Bucket = None
      self.s3Bucket = s3Bucket

   def __repr__(self):
      """
      Official string representation for class instance.
      """
      return "AmazonS3Config(%s)" % (self.s3Bucket)

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
      if self.s3Bucket != other.s3Bucket:
         if self.s3Bucket < other.s3Bucket:
            return -1
         else:
            return 1
      return 0

   def _setS3Bucket(self, value):
      """
      Property target used to set the S3 bucket.
      """
      if value is not None:
         if len(value) < 1:
            raise ValueError("S3 bucket must be non-empty string.")
      self._s3Bucket = value

   def _getS3Bucket(self):
      """
      Property target used to get the S3 bucket.
      """
      return self._s3Bucket

   s3Bucket = property(_getS3Bucket, _setS3Bucket, None, doc="Amazon S3 Bucket")


########################################################################
# LocalConfig class definition
########################################################################

class LocalConfig(object):

   """
   Class representing this extension's configuration document.

   This is not a general-purpose configuration object like the main Cedar
   Backup configuration object.  Instead, it just knows how to parse and emit
   amazons3-specific configuration values.  Third parties who need to read and
   write configuration related to this extension should access it through the
   constructor, C{validate} and C{addConfig} methods.

   @note: Lists within this class are "unordered" for equality comparisons.

   @sort: __init__, __repr__, __str__, __cmp__, amazons3, validate, addConfig
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
      self._amazons3 = None
      self.amazons3 = None
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
      return "LocalConfig(%s)" % (self.amazons3)

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
      if self.amazons3 != other.amazons3:
         if self.amazons3 < other.amazons3:
            return -1
         else:
            return 1
      return 0

   def _setAmazonS3(self, value):
      """
      Property target used to set the amazons3 configuration value.
      If not C{None}, the value must be a C{AmazonS3Config} object.
      @raise ValueError: If the value is not a C{AmazonS3Config}
      """
      if value is None:
         self._amazons3 = None
      else:
         if not isinstance(value, AmazonS3Config):
            raise ValueError("Value must be a C{AmazonS3Config} object.")
         self._amazons3 = value

   def _getAmazonS3(self):
      """
      Property target used to get the amazons3 configuration value.
      """
      return self._amazons3

   amazons3 = property(_getAmazonS3, _setAmazonS3, None, "AmazonS3 configuration in terms of a C{AmazonS3Config} object.")

   def validate(self):
      """
      Validates configuration represented by the object.

      AmazonS3 configuration must be filled in.  Within that, the s3Bucket target must be filled in

      @raise ValueError: If one of the validations fails.
      """
      if self.amazons3 is None:
         raise ValueError("AmazonS3 section is required.")
      if self.amazons3.s3Bucket is None:
         raise ValueError("AmazonS3 s3Bucket must be set.")

   def addConfig(self, xmlDom, parentNode):
      """
      Adds an <amazons3> configuration section as the next child of a parent.

      Third parties should use this function to write configuration related to
      this extension.

      We add the following fields to the document::

         s3Bucket    //cb_config/amazons3/s3_bucket

      @param xmlDom: DOM tree as from C{impl.createDocument()}.
      @param parentNode: Parent that the section should be appended to.
      """
      if self.amazons3 is not None:
         sectionNode = addContainerNode(xmlDom, parentNode, "amazons3")
         addStringNode(xmlDom, sectionNode, "s3_bucket", self.amazons3.s3Bucket)

   def _parseXmlData(self, xmlData):
      """
      Internal method to parse an XML string into the object.

      This method parses the XML document into a DOM tree (C{xmlDom}) and then
      calls a static method to parse the amazons3 configuration section.

      @param xmlData: XML data to be parsed
      @type xmlData: String data

      @raise ValueError: If the XML cannot be successfully parsed.
      """
      (xmlDom, parentNode) = createInputDom(xmlData)
      self._amazons3 = LocalConfig._parseAmazonS3(parentNode)

   @staticmethod
   def _parseAmazonS3(parent):
      """
      Parses an amazons3 configuration section.
      
      We read the following individual fields::

         s3Bucket    //cb_config/amazons3/s3_bucket

      @param parent: Parent node to search beneath.

      @return: C{AmazonS3Config} object or C{None} if the section does not exist.
      @raise ValueError: If some filled-in value is invalid.
      """
      amazons3 = None
      section = readFirstChild(parent, "amazons3")
      if section is not None:
         amazons3 = AmazonS3Config()
         amazons3.s3Bucket = readString(section, "s3_bucket")
      return amazons3


########################################################################
# Public functions
########################################################################

###########################
# executeAction() function
###########################

def executeAction(configPath, options, config):
   """
   Executes the amazons3 backup action.

   @param configPath: Path to configuration file on disk.
   @type configPath: String representing a path on disk.

   @param options: Program command-line options.
   @type options: Options object.

   @param config: Program configuration.
   @type config: Config object.

   @raise ValueError: Under many generic error conditions
   @raise IOError: If there are I/O problems reading or writing files
   """
   logger.debug("Executing amazons3 extended action.")
   if config.options is None or config.stage is None:
      raise ValueError("Cedar Backup configuration is not properly filled in.")
   local = LocalConfig(xmlPath=configPath)
   dailyDirs = findDailyDirs(config.stage.targetDir, STORE_INDICATOR)
   for dailyDir in dailyDirs:
      _storeDailyDir(config.stage.targetDir, dailyDir, local.amazons3.s3Bucket)
      writeIndicatorFile(dailyDir, STORE_INDICATOR, config.options.backupUser, config.options.backupGroup)
   logger.info("Executed the amazons3 extended action successfully.")


########################################################################
# Utility functions
########################################################################

############################
# _storeDailyDir() function
############################

def _storeDailyDir(stagingDir, dailyDir, s3Bucket):
   """
   Store the contents of a daily staging directory to a bucket in the Amazon S3 cloud.
   @param stagingDir: Configured staging directory (config.targetDir)
   @param dailyDir: Daily directory to store in the cloud
   @param s3Bucket: The Amazon S3 bucket to use as the target
   """
   s3BucketUrl = _deriveS3BucketUrl(stagingDir, dailyDir, s3Bucket)
   _clearExistingBackup(s3BucketUrl)
   _writeDailyDir(dailyDir, s3BucketUrl)


##############################
# _deriveBucketUrl() function
##############################

def _deriveS3BucketUrl(stagingDir, dailyDir, s3Bucket):
   """
   Derive the correct bucket URL for a daily directory.
   @param stagingDir: Configured staging directory (config.targetDir)
   @param dailyDir: Daily directory to store
   @param s3Bucket: The Amazon S3 bucket to use as the target
   @return: S3 bucket URL, with no trailing slash
   """
   subdir = dailyDir.replace(stagingDir, "")
   if subdir.startswith("/"):
      subdir = subdir[1:]
   return "s3://%s/%s" % (s3Bucket, dailyDir)


##################################
# _clearExistingBackup() function
##################################

def _clearExistingBackup(s3BucketUrl):
   """
   Clear any existing backup files for a daily directory.
   @param s3BucketUrl: S3 bucket URL derived for the daily directory
   """
   emptydir = tempfile.mkdtemp()
   try:
      command = resolveCommand(S3CMD_COMMAND)
      args = [ "sync", "--no-encrypt", "--recursive", "--delete-removed", emptydir + "/", s3BucketUrl + "/", ]
      result = executeCommand(command, args)[0]
      if result != 0:
         raise IOError("Error [%d] calling s3Cmd to clear existing backup [%s]." % (result, s3BucketUrl))
   finally:
      if os.path.exists(emptydir):
         os.rmdir(emptydir)


############################
# _writeDailyDir() function
############################

def _writeDailyDir(dailyDir, s3BucketUrl):
   """
   Write the daily directory out to the Amazon S3 cloud.
   @param dailyDir: Daily directory to store
   @param s3BucketUrl: S3 bucket URL derived for the daily directory
   """
   command = resolveCommand(S3CMD_COMMAND)
   args = [ "put", "--recursive", dailyDir + "/", s3BucketUrl + "/", ]
   result = executeCommand(command, args)[0]
   if result != 0:
      raise IOError("Error [%d] calling s3Cmd to store daily directory [%s]." % (result, s3BucketUrl))

