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
# Purpose  : Provides an extension to back up MySQL databases.
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# This file was created with a width of 132 characters, and NO tabs.

########################################################################
# Module documentation
########################################################################

"""
Provides an extension to back up MySQL databases.

This is a Cedar Backup extension used to back up MySQL databases via the Cedar
Backup command line.  It requires a new configurations section <mysql> and is
intended to be run either immediately before or immediately after the standard
collect action.  Aside from its own configuration, it requires the options and
collect configuration sections in the standard Cedar Backup configuration file.

The backup is done via the C{mysqldump} command included with the MySQL
product.  Output is always to a file compressed using C{gzip}.  Administrators
can configure the extension either to back up all databases or to back up only
specific databases.  

Note that this code always produces a full backup.  There is currently no
facility for making incremental backups.  If/when someone has a need for this
and can describe how to do it, I'll update this extension or provide another.

You should always make C{/etc/cback.conf} unreadble to non-root users once you
place mysql configuration into it, since mysql configuration will contain
information about available MySQL databases, usernames and passwords.

Unfortunately, use of this extension I{will} expose usernames and passwords in
the process listing (via C{ps}) when the backup is running.  This is because
none of the official MySQL backup scripts provide a good way to specify
password other than via the C{--password} command-line option.

@author: Kenneth J. Pronovici <pronovic@ieee.org>
"""

########################################################################
# Imported modules
########################################################################

# System modules
import os
import logging
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
from CedarBackup2.config import Config
from CedarBackup2.util import executeCommand, ObjectTypeList


########################################################################
# Module-wide constants and variables
########################################################################

logger = logging.getLogger("CedarBackup2.log.extend.mysql")
MYSQLDUMP_COMMAND = [ "mysqldump", ]


########################################################################
# MysqlConfig class definition
########################################################################

class MysqlConfig(object):

   """
   Class representing a Cedar Backup MySQL configuration.
   The MySQL configuration information is used for backing up MySQL databases.
   @sort: __init__, __repr__, __str__, __cmp__, user, password, all, databases
   """

   def __init__(self, user=None, password=None, all=None, databases=None):
      """
      Constructor for the C{MysqlConfig} class.
      
      @param user: User to execute backup as.
      @param password: Password associated with user.
      @param all: Indicates whether to back up all databases.
      @param databases: List of databases to back up.
      """
      self._user = None
      self._password = None
      self._all = None
      self._databases = None
      self.user = user
      self.password = password
      self.all = all
      self.databases = databases

   def __repr__(self):
      """
      Official string representation for class instance.
      """
      return "MysqlConfig(%s, %s, %s, %s)" % (self.user, self.password, self.all, self.databases)

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
      if self._user != other._user:
         if self._user < other._user:
            return -1
         else:
            return 1
      if self._password != other._password:
         if self._password < other._password:
            return -1
         else:
            return 1
      if self._all != other._all:
         if self._all < other._all:
            return -1
         else:
            return 1
      if self._databases != other._databases:
         if self._databases < other._databases:
            return -1
         else:
            return 1
      return 0

   def _setUser(self, value):
      """
      Property target used to set the user value.
      """
      if value is not None:
         if len(value) < 1:
            raise ValueError("User must be non-empty string.")
      self._user = value

   def _getUser(self):
      """
      Property target used to get the user value.
      """
      return self._user

   def _setPassword(self, value):
      """
      Property target used to set the password value.
      """
      if value is not None:
         if len(value) < 1:
            raise ValueError("Password must be non-empty string.")
      self._password = value

   def _getPassword(self):
      """
      Property target used to get the password value.
      """
      return self._password

   def _setAll(self, value):
      """
      Property target used to set the 'all' flag.
      No validations, but we normalize the value to C{True} or C{False}.
      """
      if value:
         self._all = True
      else:
         self._all = False

   def _getAll(self):
      """
      Property target used to get the 'all' flag.
      """
      return self._all

   def _setDatabases(self, value):
      """
      Property target used to set the databases list.
      Either the value must be C{None} or each element must be a string.
      @raise ValueError: If the value is not a string.
      """
      if value is None:
         self._databases = None
      else:
         for database in value:
            if len(database) < 1:
               raise ValueError("Each database must be a non-empty string.")
         try:
            saved = self._databases
            self._databases = ObjectTypeList(basestring, "string")
            self._databases.extend(value)
         except Exception, e:
            self._databases = saved
            raise e

   def _getDatabases(self):
      """
      Property target used to get the databases list.
      """
      return self._databases

   user = property(_getUser, _setUser, None, "User to execute backup as.")
   password = property(_getPassword, _setPassword, None, "Password associated with user.")
   all = property(_getAll, _setAll, None, "Indicates whether to back up all databases.")
   databases = property(_getDatabases, _setDatabases, None, "List of databases to back up.")


########################################################################
# LocalConfig class definition
########################################################################

class LocalConfig(object):

   """
   Class representing this extension's configuration document.

   This is not a general-purpose configuration object like the main Cedar
   Backup configuration object.  Instead, it just knows how to parse and emit
   configuration values.  Third parties who need to read and write
   configuration related to this extension should access it through the
   constructor, C{validate} and C{addConfig} methods.

   @note: Lists within this class are "unordered" for equality comparisons.

   @sort: __init__, __repr__, __str__, __cmp__, mysql, validate, addConfig
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
      self._mysql = None
      self.mysql = None
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
      return "LocalConfig(%s)" % (self.mysql)

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
      if self._mysql != other._mysql:
         if self._mysql < other._mysql:
            return -1
         else:
            return 1
      return 0

   def _setMysql(self, value):
      """
      Property target used to set the mysql configuration value.
      If not C{None}, the value must be a C{MysqlConfig} object.
      @raise ValueError: If the value is not a C{MysqlConfig}
      """
      if value is None:
         self._mysql = None
      else:
         if not isinstance(value, MysqlConfig):
            raise ValueError("Value must be a C{MysqlConfig} object.")
         self._mysql = value

   def _getMysql(self):
      """
      Property target used to get the mysql configuration value.
      """
      return self._mysql

   mysql = property(_getMysql, _setMysql, None, "Mysql configuration in terms of a C{MysqlConfig} object.")

   def validate(self):
      """
      Validates configuration represented by the object.

      Basically, the user and password must be filled in, and then if the 'all'
      flag I{is} set, no databases are allowed, and if the 'all' flag is I{not}
      set, at least one database is required.

      @raise ValueError: If one of the validations fails.
      """
      if self.mysql is None:
         raise ValueError("Mysql section is required.")
      if self.mysql.user is None:
         raise ValueError("Mysql user value is required.")
      if self.mysql.password is None:
         raise ValueError("Mysql password value is required.")
      if self.mysql.all:
         if self.mysql.databases is not None and self.mysql.databases != []:
            raise ValueError("Databases cannot be specified if 'all' flag is set.")
      else:
         if self.mysql.databases is None or len(self.mysql.databases) < 1:
            raise ValueError("At least one database must be indicated if 'all' flag is not set.")

   def addConfig(self, xmlDom, parentNode):
      """
      Adds a <mysql> configuration section as the next child of a parent.

      Third parties should use this function to write configuration related to
      this extension.

      We add the following fields to the document::

         user           //cb_config/mysql/user
         password       //cb_config/mysql/password
         all            //cb_config/mysql/all

      We also add groups of the following items, one list element per
      item::

         database       //cb_config/mysql/database

      @param xmlDom: DOM tree as from C{impl.createDocument()}.
      @param parentNode: Parent that the section should be appended to.
      """
      if self.mysql is not None:
         sectionNode = Config.addContainerNode(xmlDom, parentNode, "mysql")
         Config.addStringNode(xmlDom, sectionNode, "user", self.mysql.user)
         Config.addStringNode(xmlDom, sectionNode, "password", self.mysql.password)
         Config.addBooleanNode(xmlDom, sectionNode, "all", self.mysql.all)
         if self.mysql.databases is not None:
            for database in self.mysql.databases:
               Config.addStringNode(xmlDom, sectionNode, "database", database)

   def _parseXmlData(self, xmlData):
      """
      Internal method to parse an XML string into the object.

      This method parses the XML document into a DOM tree (C{xmlDom}) and then
      calls a static method to parse the mysql configuration section.

      @param xmlData: XML data to be parsed
      @type xmlData: String data

      @raise ValueError: If the XML cannot be successfully parsed.
      """
      try:
         xmlDom = PyExpat.Reader().fromString(xmlData)
         parent = Config.readFirstChild(xmlDom, "cb_config")
         self._mysql = LocalConfig._parseMysql(parent)
      except (IOError, ExpatError), e:
         raise ValueError("Unable to parse XML document: %s" % e)

   def _parseMysql(parent):
      """
      Parses a mysql configuration section.
      
      We read the following fields::

         user           //cb_config/mysql/user
         password       //cb_config/mysql/password
         all            //cb_config/mysql/all

      We also read groups of the following item, one list element per
      item::

         databases      //cb_config/mysql/database

      @param parent: Parent node to search beneath.

      @return: C{ReferenceConfig} object or C{None} if the section does not exist.
      @raise ValueError: If some filled-in value is invalid.
      """
      mysql = None
      section = Config.readFirstChild(parent, "mysql")
      if section is not None:
         mysql = MysqlConfig()
         mysql.user = Config.readString(section, "user")
         mysql.password = Config.readString(section, "password")
         mysql.all = Config.readBoolean(section, "all")
         mysql.databases = Config.readStringList(section, "database")
      return mysql
   _parseMysql = staticmethod(_parseMysql)


########################################################################
# Public functions
########################################################################

###########################
# executeBackup() function
###########################

def executeBackup(configPath, options, config):
   """
   Executes the MySQL backup action.

   @param configPath: Path to configuration file on disk.
   @type configPath: String representing a path on disk.

   @param options: Program command-line options.
   @type options: Options object.

   @param config: Program configuration.
   @type config: Config object.

   @raise ValueError: Under many generic error conditions
   @raise IOError: If a backup could not be written for some reason.
   """
   logger.debug("Executing MySQL extended action.")
   if config.options is None or config.collect is None:
      raise ValueError("Cedar Backup configuration is not properly filled in.")
   local = LocalConfig(xmlPath=configPath)
   if local.mysql.all:
      logger.info("Backing up all databases.")
      _backupDatabase(config.collect.collectDir, local.mysql.user, local.mysql.password, None)
   else:
      logger.debug("Backing up %d individual databases." % len(local.mysql.databases))
      for database in local.mysql.databases:
         logger.info("Backing up database [%s]." % database)
         _backupDatabase(config.collect.collectDir, local.mysql.user, local.mysql.password, name=database)
   logger.info("Executed the MySQL extended action successfully.")

def _backupDatabase(targetDir, user, password, name=None, compress=True):
   """
   Backs up an individual MySQL database, or all databases.

   @param targetDir:  Directory into which backups should be written.
   @param user: User to use for connecting to the database.
   @param password: Password associated with user.
   @param name: Name of database, or C{None} for all databases.

   @return: Name of the generated backup file.

   @raise ValueError: If some value is missing or invalid.
   @raise IOError: If there is a problem executing the MySQL dump.
   """
   args = _buildDumpArgs(user, password, name)
   (outputFile, filename) = _getOutputFile(targetDir, name, compress)
   try:
      result = executeCommand(MYSQLDUMP_COMMAND, args, returnOutput=False, ignoreStderr=True, outputFile=outputFile)[0]
      if result != 0:
         raise IOError("Error [%d] executing MySQL database dump.")
   finally:
      outputFile.close()
   if not os.path.exists(filename):
      raise IOError("Dump file [%s] does not seem to exist after backup completed." % filename)

def _buildDumpArgs(user, password, name):
   """
   Builds list of arguments to be passed to C{mysqldump} command.

   @param user: User to use for connecting to the database.
   @param password: Password associated with user.
   @param name: Name of database, or C{None} for all databases.

   @raise ValueError: If some value is missing or invalid.
   """
   if user is None or password is None:
      raise ValueError("User and password are required.")
   args = [ "-all", "--flush-logs", "--opt", "--user=%s" % user, "--password=%s" % password, ]
   if name is None:
      args.insert(0, "--all-databases")
   else:
      args.insert(0, "--databases")
      args.append(name)
   return args

def _getOutputFile(targetDir, name, compress=True):
   """
   Opens the output file used for saving the MySQL dump.

   The filename is either C{"mysqldump.txt"} or C{"mysqldump-name.txt"}.  The
   C{".gz"} extension is added if C{compress} is C{True}. 

   @param targetDir: Target directory to write file in.
   @param name: Name of the database (if any)
   @param compress: Indicates whether to write compressed output.

   @return: Tuple of (Output file object, filename)
   """
   if name is None:
      filename = os.path.join(targetDir, "mysqldump.txt")
   else:
      filename = os.path.join(targetDir, "mysqldump-%s.txt" % name)
   if compress:
      filename = "%s.gz" % filename
   logger.debug("MySQL dump file will be [%s]." % filename)
   if compress:
      outputFile = GzipFile(filename, "w")
   else:
      outputFile = open(filename, "w")
   return (outputFile, filename)

