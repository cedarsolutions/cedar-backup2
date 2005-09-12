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
# Purpose  : Provides command-line interface implementation.
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# This file was created with a width of 132 characters, and NO tabs.

########################################################################
# Module documentation
########################################################################

"""
Provides command-line interface implementation for the cback script.

Summary
=======

   The functionality in this module encapsulates the command-line interface for
   the cback script.  The cback script itself is very short, basically just an
   invokation of one function implemented here.  That, in turn, makes it
   simpler to validate the command line interface (for instance, it's easier to
   run pychecker against a module, and unit tests are easier, too).

   The objects and functions implemented in this module are probably not useful
   to any code external to Cedar Backup.   Anyone else implementing their own
   command-line interface would have to reimplement (or at least enhance) all
   of this anyway.

Backwards Compatibility
=======================

   The command line interface has changed between Cedar Backup 1.x and Cedar
   Backup 2.x.  Some new switches have been added, and the actions have become
   simple arguments rather than switches (which is a much more standard command
   line format).  Old 1.x command lines are generally no longer valid.

@var DEFAULT_CONFIG: The default configuration file.
@var DEFAULT_LOGFILE: The default log file path.
@var DEFAULT_OWNERSHIP: Default ownership for the logfile.
@var DEFAULT_MODE: Default file permissions mode on the logfile.
@var VALID_ACTIONS: List of valid actions.
@var COMBINE_ACTIONS: List of actions which can be combined with other actions.
@var NONCOMBINE_ACTIONS: List of actions which cannot be combined with other actions.

@sort: cli, Options, DEFAULT_CONFIG, DEFAULT_LOGFILE, DEFAULT_OWNERSHIP, 
       DEFAULT_MODE, VALID_ACTIONS, COMBINE_ACTIONS, NONCOMBINE_ACTIONS

@author: Kenneth J. Pronovici <pronovic@ieee.org>
"""

########################################################################
# Imported modules
########################################################################

# System modules
import sys
import os
import logging
import getopt

# Cedar Backup modules
from CedarBackup2.release import AUTHOR, EMAIL, VERSION, DATE, COPYRIGHT
from CedarBackup2.util import RestrictedContentList, PathResolverSingleton
from CedarBackup2.util import splitCommandLine, getFunctionReference, getUidGid, encodePath
from CedarBackup2.config import Config
from CedarBackup2.action import executeCollect, executeStage, executeStore, executePurge, executeRebuild, executeValidate


########################################################################
# Module-wide constants and variables
########################################################################

logger = logging.getLogger("CedarBackup2.log.cli")

DISK_LOG_FORMAT    = "%(asctime)s --> [%(levelname)-7s] %(message)s"
DISK_OUTPUT_FORMAT = "%(message)s"
SCREEN_LOG_FORMAT  = "%(message)s"
SCREEN_LOG_STREAM  = sys.stdout
DATE_FORMAT        = "%Y-%m-%dT%H:%M:%S %Z"

DEFAULT_CONFIG     = "/etc/cback.conf"
DEFAULT_LOGFILE    = "/var/log/cback.log"
DEFAULT_OWNERSHIP  = [ "root", "adm", ]
DEFAULT_MODE       = 0640

COLLECT_INDEX      = 100
STAGE_INDEX        = 200
STORE_INDEX        = 300
PURGE_INDEX        = 400

VALID_ACTIONS      = [ "collect", "stage", "store", "purge", "rebuild", "validate", "all", ]
COMBINE_ACTIONS    = [ "collect", "stage", "store", "purge", ]
NONCOMBINE_ACTIONS = [ "rebuild", "validate", "all", ]

SHORT_SWITCHES     = "hVbqc:fl:o:m:Ods"
LONG_SWITCHES      = [ 'help', 'version', 'verbose', 'quiet', 
                       'config=', 'full', 'logfile=', 'owner=', 
                       'mode=', 'output', 'debug', 'stack', ]


#######################################################################
# Public functions
#######################################################################

#################
# cli() function
#################

def cli():
   """
   Implements the command-line interface for the C{cback} script.

   Essentially, this is the "main routine" for the cback script.  It does all
   of the argument processing for the script, and then sets about executing the
   indicated actions.

   As a general rule, only the actions indicated on the command line will be
   executed.   We will accept any of the standard actions and any of the
   configured extended actions (which makes action list verification a two-
   step process).

   The C{'all'} action has a special meaning.  Normally, it means that the
   standard set of actions (collect, stage, store, purge) will all be executed,
   in that order.  Extended actions will be ignored as part of the C{'all'}
   action.

   Raised exceptions always result in an immediate return.  Otherwise, we
   generally return when all specified actions have been completed.  Actions
   are ignored if the help, version or validate flags are set.

   A different error code is returned for each type of failure:

      - C{1}: The Python interpreter version is < 2.3
      - C{2}: Error processing command-line arguments
      - C{3}: Error configuring logging
      - C{4}: Error parsing indicated configuration file
      - C{5}: Backup was interrupted with a CTRL-C or similar
      - C{6}: Error executing specified backup actions

   @note: This function contains a good amount of logging at the INFO level,
   because this is the right place to document high-level flow of control (i.e.
   what the command-line options were, what config file was being used, etc.)
   
   @note: We assume that anything that I{must} be seen on the screen is logged
   at the ERROR level.  Errors that occur before logging can be configured are
   written to C{sys.stderr}.

   @return: Error code as described above.
   """
   try:
      if map(int, [sys.version_info[0], sys.version_info[1]]) < [2, 3]:
         sys.stderr.write("Python version 2.3 or greater required.\n")
         return 1
   except:
      # sys.version_info isn't available before 2.0
      sys.stderr.write("Python version 2.3 or greater required.\n")
      return 1

   try:
      options = Options(argumentList=sys.argv[1:])
      logger.info("Specified command-line actions: " % options.actions)
   except Exception, e:
      _usage()
      sys.stderr.write(" *** Error: %s\n" % e)
      return 2

   if options.help:
      _usage()
      return 0
   if options.version:
      _version()
      return 0

   try:
      logfile = _setupLogging(options)
   except Exception, e:
      sys.stderr.write("Error setting up logging: %s\n" % e)
      return 3

   logger.info("Cedar Backup run started.")
   logger.info("Options were [%s]" % options)
   logger.info("Logfile is [%s]" % logfile)

   if options.config is None:
      logger.debug("Using default configuration file.")
      configPath = DEFAULT_CONFIG
   else:
      logger.debug("Using user-supplied configuration file.")
      configPath = options.config

   try:
      logger.info("Configuration path is [%s]" % configPath)
      config = Config(xmlPath=configPath)
      _setupPathResolver(config)
      if config.extensions is not None:
         actionSet = _ActionSet(options.actions, config.extensions.actions)
      else:
         actionSet = _ActionSet(options.actions, None)
   except Exception, e:
      logger.error("Error reading or handling configuration: %s" % e)
      logger.info("Cedar Backup run completed with status 4.")
      return 4

   if options.stacktrace:
      actionSet.executeActions(configPath, options, config)
   else:
      try:
         actionSet.executeActions(configPath, options, config)
      except KeyboardInterrupt:
         logger.error("Backup interrupted.")
         logger.info("Cedar Backup run completed with status 5.")
         return 5
      except Exception, e:
         logger.error("Error executing backup: %s" % e)
         logger.info("Cedar Backup run completed with status 6.")
         return 6

   logger.info("Cedar Backup run completed with status 0.")
   return 0


########################################################################
# Action-related class definition
########################################################################

####################
# _ActionItem class
####################

class _ActionItem(object):

   """
   Class representing a single action to be executed.

   This class represents a single action to be executed, and understands how to
   execute those actions.   

   Standard actions ("built-in" actions like collect, stage, etc.) are
   instantiated in terms of a direct function reference, i.e.  to
   C{executeCollect}.  Extended actions are instantiated in terms of an
   C{ExtendedAction} object taken from configuration.

   The two different actions are executed directly.  In the case of standard
   actions, the function reference is called directly.  In the case of extended
   actions, a function reference is first derived (using
   L{getFunctionReference}) and then called.

   The standard actions will generally use the options and config values.  We
   also pass in the config path so that extensions modules can re-parse
   configuration if they want to, to add in extra information.

   @note: The comparison operators for this class have been implemented to only
   compare based on the index value, and ignore all other values.  This is so
   that the action set list can be easily sorted by index.

   @sort: __init__, index, module, function 
   """

   def __init__(self, index, function=None, extension=None):
      """
      Default constructor.
      @param index: Index of the item (or C{None}).
      @param function: Reference to function associated with item.
      @param extension: C{ExtendedAction} object associated with item.
      """
      self.index = index
      self.function = function
      self.extension = extension

   def __cmp__(self, other):
      """
      Definition of equals operator for this class.
      The only thing we compare is the item's index.  
      @param other: Other object to compare to.
      @return: -1/0/1 depending on whether self is C{<}, C{=} or C{>} other.
      """
      if other is None:
         return 1
      if self.index != other.index:
         if self.index < other.index:
            return -1
         else:
            return 1 
      return 0

   def executeAction(self, configPath, options, config):
      """
      Executes the action associated with an item.

      See class notes for more details on how the action is executed.

      @param configPath: Path to configuration file on disk.
      @param options: Command-line options to be passed to action.
      @param config: Parsed configuration to be passed to action.

      @raise Exception: If there is a problem executing the action.
      """
      if self.function is not None:
         self.function(configPath, options, config)
      else:
         function = getFunctionReference(self.extension.module, self.extension.function)
         function(configPath, options, config)


###################
# _ActionSet class
###################

class _ActionSet(object):

   """
   Class representing a set of actions to be executed.

   This class does two different things.  First, it ensures that the actions
   specified on the command-line are sensible.  The command-line can only list
   either standard actions or extended actions specified in configuration.
   Also, certain actions (in L{NONCOMBINE_ACTIONS}) cannot be combined with
   other actions.  

   Second, it enforces an execution order on the specified actions.  Any time
   actions are combined on the command line (either standard actions or
   extended actions), we must make sure they get executed in a sensible order.

   @sort: __init__, executeActions
   """

   def __init__(self, actions, extensions):
      """
      Constructor for the C{_ActionSet} class.

      @param actions: Names of actions specified on the command-line.
      @param extensions: List of extended actions (i.e. config.extensions.actions)

      @raise ValueError: If one of the specified actions is invalid.
      """
      extensionDict = {}
      if extensions is not None:
         for extension in extensions:
            extensionDict[extension.name] = extension
      _ActionSet._validateActions(actions, extensionDict.keys())
      self.actionSet = _ActionSet._buildActionSet(actions, extensionDict)

   def _validateActions(actions, extensionNames):
      """
      Validate that the set of specified actions is sensible.

      Any specified action must either be a standard action or must be among
      the extended actions defined in configuration.  The actions from within
      L{NONCOMBINE_ACTIONS} may not be combined with other actions.

      @param actions: Names of actions specified on the command-line.
      @param extensionNames: Names of extensions specified in configuration.

      @raise ValueError: If one or more configured actions are not valid.
      """
      if extensionNames is None: 
         extensionNames = []
      if actions is None or actions == []:
         raise ValueError("No actions specified.")
      for action in actions:
         if action not in VALID_ACTIONS and action not in extensionNames:
            raise ValueError("Action [%s] is not a valid action or extended action." % action)
      for action in NONCOMBINE_ACTIONS:
         if action in actions and actions != [ action, ]:
            raise ValueError("Action [%s] may not be combined with other actions." % action)
   _validateActions = staticmethod(_validateActions)

   def _buildActionSet(actions, extensionDict):
      """
      Build set of actions to be executed.

      The set of actions is built in the proper order, so C{executeActions}
      spin through the set without thinking about it.  Since we've already validated
      that the set of actions is sensible, we don't take any precautions here to
      make sure things are combined properly.  If the action is listed, it will
      be "scheduled" for implementation.

      Every item in the action set is an C{_ActionItem}.

      @param actions: Names of actions specified on the command-line.
      @param extensionDict: Dictionary mapping extension name to C{ExtendedAction} object.

      @return: Set of action items in proper order.
      """
      actionSet = []
      for action in actions:
         if extensionDict.has_key(action):
            actionSet.append(_ActionItem(extensionDict[action].index, extension=extensionDict[action]))
         elif action == 'collect':
            actionSet.append(_ActionItem(COLLECT_INDEX, function=executeCollect))
         elif action == 'stage':
            actionSet.append(_ActionItem(STAGE_INDEX, function=executeStage))
         elif action == 'store':
            actionSet.append(_ActionItem(STORE_INDEX, function=executeStore))
         elif action == 'purge':
            actionSet.append(_ActionItem(PURGE_INDEX, function=executePurge))
         elif action == 'rebuild':
            actionSet.append(_ActionItem(None, function=executeRebuild))
         elif action == 'validate':
            actionSet.append(_ActionItem(None, function=executeValidate))
         elif action == 'all':
            actionSet.append(_ActionItem(COLLECT_INDEX, function=executeCollect))
            actionSet.append(_ActionItem(STAGE_INDEX, function=executeStage))
            actionSet.append(_ActionItem(STORE_INDEX, function=executeStore))
            actionSet.append(_ActionItem(PURGE_INDEX, function=executePurge))
      actionSet.sort()  # sort the actions in order by index
      return actionSet
   _buildActionSet = staticmethod(_buildActionSet)

   def executeActions(self, configPath, options, config):
      """
      Executes all actions and extended actions, in the proper order.
   
      The built-in actions will generally use the options and config values.
      We also pass in the config path so that extensions modules can re-parse
      configuration if they want to, to add in extra information.

      @param configPath: Path to configuration file on disk.
      @param options: Command-line options to be passed to action functions.
      @param config: Parsed configuration to be passed to action functions.

      @raise Exception: If there is a problem executing the actions.
      """
      for actionItem in self.actionSet:
         actionItem.executeAction(configPath, options, config)


#######################################################################
# Utility functions
#######################################################################

####################
# _usage() function
####################

def _usage(fd=sys.stderr):
   """
   Prints usage information for the cback script.
   @param fd: File descriptor used to print information.
   @note: The C{fd} is used rather than C{print} to facilitate unit testing.
   """
   fd.write("\n")
   fd.write(" Usage: cback [switches] action(s)\n")
   fd.write("\n")
   fd.write(" The following switches are accepted:\n")
   fd.write("\n")
   fd.write("   -h, --help     Display this usage/help listing\n")
   fd.write("   -V, --version  Display version information\n")
   fd.write("   -b, --verbose  Print verbose output as well as logging to disk\n")
   fd.write("   -q, --quiet    Run quietly (display no output to the screen)\n")
   fd.write("   -c, --config   Path to config file (default: %s)\n" % DEFAULT_CONFIG)
   fd.write("   -f, --full     Perform a full backup, regardless of configuration\n")
   fd.write("   -l, --logfile  Path to logfile (default: %s)\n" % DEFAULT_LOGFILE)
   fd.write("   -o, --owner    Logfile ownership, user:group (default: %s:%s)\n" % (DEFAULT_OWNERSHIP[0], DEFAULT_OWNERSHIP[1]))
   fd.write("   -m, --mode     Octal logfile permissions mode (default: %o)\n" % DEFAULT_MODE)
   fd.write("   -O, --output   Record some sub-command (i.e. tar) output to the log\n")
   fd.write("   -d, --debug    Write debugging information to the log (implies --output)\n")
   fd.write("   -s, --stack    Dump a Python stack trace instead of swallowing exceptions\n")
   fd.write("\n")
   fd.write(" The following actions may be specified:\n")
   fd.write("\n")
   fd.write("   all            Take all normal actions (collect, stage, store, purge)\n")
   fd.write("   collect        Take the collect action\n")
   fd.write("   stage          Take the stage action\n")
   fd.write("   store          Take the store action\n")
   fd.write("   purge          Take the purge action\n")
   fd.write("   rebuild        Rebuild \"this week's\" disc if possible\n")
   fd.write("   validate       Validate configuration only\n")
   fd.write("\n")
   fd.write(" You may also specify extended actions that have been defined in\n")
   fd.write(" configuration.\n")
   fd.write("\n")
   fd.write(" You must specify at least one action to take.  More than one of\n")
   fd.write(" the \"collect\", \"stage\", \"store\" or \"purge\" actions and/or\n")
   fd.write(" extended actions may be specified in any arbitrary order; they\n")
   fd.write(" will be executed in a sensible order.  The \"all\", \"rebuild\"\n")
   fd.write(" or \"validate\" actions may not be combined with other actions.\n")
   fd.write("\n")


######################
# _version() function
######################

def _version(fd=sys.stdout):
   """
   Prints version information for the cback script.
   @param fd: File descriptor used to print information.
   @note: The C{fd} is used rather than C{print} to facilitate unit testing.
   """
   fd.write("\n")
   fd.write(" Cedar Backup version %s, released %s.\n" % (VERSION, DATE))
   fd.write("\n")
   fd.write(" Copyright (c) %s %s <%s>.\n" % (COPYRIGHT, AUTHOR, EMAIL))
   fd.write(" This is free software; there is NO warranty.  See the\n")
   fd.write(" GNU General Public License version 2 for copying conditions.\n")
   fd.write("\n")
   fd.write(" Use the --help option for usage information.\n")
   fd.write("\n")


###########################
# _setupLogging() function
###########################

def _setupLogging(options):
   """
   Set up logging based on command-line options.

   There are two kinds of logging: flow logging and output logging.  Output
   logging contains information about system commands executed by Cedar Backup,
   for instance the calls to C{mkisofs} or C{mount}, etc.  Flow logging
   contains error and informational messages used to understand program flow.
   Flow log messages and output log messages are written to two different
   loggers target (C{CedarBackup2.log} and C{CedarBackup2.output}).  Flow log
   messages are written at the ERROR, INFO and DEBUG log levels, while output
   log messages are generally only written at the INFO log level.

   By default, output logging is disabled.  When the C{options.output} or
   C{options.debug} flags are set, output logging will be written to the
   configured logfile.  Output logging is never written to the screen.

   By default, flow logging is enabled at the ERROR level to the screen and at
   the INFO level to the configured logfile.  If the C{options.quiet} flag is
   set, flow logging is enabled at the INFO level to the configured logfile
   only (i.e. no output will be sent to the screen).  If the C{options.verbose}
   flag is set, flow logging is enabled at the INFO level to both the screen
   and the configured logfile.  If the C{options.debug} flag is set, flow
   logging is enabled at the DEBUG level to both the screen and the configured
   logfile.

   @param options: Command-line options.
   @type options: L{Options} object

   @return: Path to logfile on disk.
   """
   logfile = _setupLogfile(options)
   _setupFlowLogging(logfile, options)
   _setupOutputLogging(logfile, options)
   return logfile

def _setupLogfile(options):
   """
   Sets up and creates logfile as needed.

   If the logfile already exists on disk, it will be left as-is, under the
   assumption that it was created with appropriate ownership and permissions.
   If the logfile does not exist on disk, it will be created as an empty file.
   Ownership and permissions will remain at their defaults unless user/group
   and/or mode are set in the options.  We ignore errors setting the indicated
   user and group.

   @note: This function is vulnerable to a race condition.  If the log file
   does not exist when the function is run, it will attempt to create the file
   as safely as possible (using C{O_CREAT}).  If two processes attempt to
   create the file at the same time, then one of them will fail.  In practice,
   this shouldn't really be a problem, but it might happen occassionally if two
   instances of cback run concurrently or if cback collides with logrotate or
   something.

   @param options: Command-line options.

   @return: Path to logfile on disk.
   """
   if options.logfile is None:
      logfile = DEFAULT_LOGFILE
   else:
      logfile = options.logfile
   if not os.path.exists(logfile):
      if options.mode is None: 
         os.fdopen(os.open(logfile, os.O_CREAT|os.O_APPEND, DEFAULT_MODE)).write("")
      else:
         os.fdopen(os.open(logfile, os.O_CREAT|os.O_APPEND, options.mode)).write("")
      try:
         if options.owner is None or len(options.owner) < 2:
            (uid, gid) = getUidGid(DEFAULT_OWNERSHIP[0], DEFAULT_OWNERSHIP[1])
         else:
            (uid, gid) = getUidGid(options.owner[0], options.owner[1])
         os.chown(logfile, uid, gid)
      except: pass
   return logfile

def _setupFlowLogging(logfile, options):
   """
   Sets up flow logging.
   @param logfile: Path to logfile on disk.
   @param options: Command-line options.
   """
   flowLogger = logging.getLogger("CedarBackup2.log")
   flowLogger.setLevel(logging.DEBUG)    # let the logger see all messages
   _setupDiskFlowLogging(flowLogger, logfile, options)
   _setupScreenFlowLogging(flowLogger, options)

def _setupOutputLogging(logfile, options):
   """
   Sets up command output logging.
   @param logfile: Path to logfile on disk.
   @param options: Command-line options.
   """
   outputLogger = logging.getLogger("CedarBackup2.output")
   outputLogger.setLevel(logging.DEBUG)      # let the logger see all messages
   _setupDiskOutputLogging(outputLogger, logfile, options)

def _setupDiskFlowLogging(flowLogger, logfile, options):
   """
   Sets up on-disk flow logging.
   @param flowLogger: Python flow logger object.
   @param logfile: Path to logfile on disk.
   @param options: Command-line options.
   """
   formatter = logging.Formatter(fmt=DISK_LOG_FORMAT, datefmt=DATE_FORMAT)
   handler = logging.FileHandler(logfile, mode="a")
   handler.setFormatter(formatter)
   if options.debug:
      handler.setLevel(logging.DEBUG)
   else:
      handler.setLevel(logging.INFO)
   flowLogger.addHandler(handler)

def _setupScreenFlowLogging(flowLogger, options):
   """
   Sets up on-screen flow logging.
   @param flowLogger: Python flow logger object.
   @param options: Command-line options.
   """
   formatter = logging.Formatter(fmt=SCREEN_LOG_FORMAT)
   handler = logging.StreamHandler(strm=SCREEN_LOG_STREAM)
   handler.setFormatter(formatter)
   if options.quiet:
      handler.setLevel(logging.CRITICAL)  # effectively turn it off
   elif options.verbose:
      if options.debug:
         handler.setLevel(logging.DEBUG)
      else:
         handler.setLevel(logging.INFO)
   else:
      handler.setLevel(logging.ERROR)
   flowLogger.addHandler(handler)

def _setupDiskOutputLogging(outputLogger, logfile, options):
   """
   Sets up on-disk command output logging.
   @param outputLogger: Python command output logger object.
   @param logfile: Path to logfile on disk.
   @param options: Command-line options.
   """
   formatter = logging.Formatter(fmt=DISK_OUTPUT_FORMAT, datefmt=DATE_FORMAT)
   handler = logging.FileHandler(logfile, mode="a")
   handler.setFormatter(formatter)
   if options.debug or options.output:
      handler.setLevel(logging.DEBUG)
   else:
      handler.setLevel(logging.CRITICAL)  # effectively turn it off
   outputLogger.addHandler(handler)


################################
# _setupPathResolver() function
################################

def _setupPathResolver(config):
   """
   Set up the path resolver singleton based on configuration.

   Cedar Backup's path resolver is implemented in terms of a singleton, the
   L{PathResolverSingleton} class.  This function takes options configuration,
   converts it into the dictionary form needed by the singleton, and then
   initializes the singleton.  After that, any function that needs to resolve
   the path of a command can use the singleton.

   @param config: Configuration
   @type config: L{Config} object
   """
   mapping = {}
   if config.options.overrides is not None:
      for override in config.options.overrides:
         mapping[override.command] = override.absolutePath
   singleton = PathResolverSingleton()
   singleton.fill(mapping)


#########################################################################
# Options class definition
########################################################################

class Options(object):

   ######################
   # Class documentation
   ######################

   """
   Class representing command-line options for the cback script.

   The C{Options} class is a Python object representation of the command-line
   options of the cback script.  

   The object representation is two-way: a command line string or a list of
   command line arguments can be used to create an C{Options} object, and then
   changes to the object can be propogated back to a list of command-line
   arguments or to a command-line string.  An C{Options} object can even be
   created from scratch programmatically (if you have a need for that).

   There are two main levels of validation in the C{Options} class.  The first
   is field-level validation.  Field-level validation comes into play when a
   given field in an object is assigned to or updated.  We use Python's
   C{property} functionality to enforce specific validations on field values,
   and in some places we even use customized list classes to enforce
   validations on list members.  You should expect to catch a C{ValueError}
   exception when making assignments to fields if you are programmatically
   filling an object.

   The second level of validation is post-completion validation.  Certain
   validations don't make sense until an object representation of options is
   fully "complete".  We don't want these validations to apply all of the time,
   because it would make building up a valid object from scratch a real pain.
   For instance, we might have to do things in the right order to keep from
   throwing exceptions, etc.

   All of these post-completion validations are encapsulated in the
   L{Options.validate} method.  This method can be called at any time by a
   client, and will always be called immediately after creating a C{Options}
   object from a command line and before exporting a C{Options} object back to
   a command line.  This way, we get acceptable ease-of-use but we also don't
   accept or emit invalid command lines.

   @note: Lists within this class are "unordered" for equality comparisons.

   @sort: __init__, __repr__, __str__, __cmp__
   """

   ##############
   # Constructor
   ##############

   def __init__(self, argumentList=None, argumentString=None, validate=True):
      """
      Initializes an options object.

      If you initialize the object without passing either C{argumentList} or
      C{argumentString}, the object will be empty and will be invalid until it
      is filled in properly.

      No reference to the original arguments is saved off by this class.  Once
      the data has been parsed (successfully or not) this original information
      is discarded.

      The argument list is assumed to be a list of arguments, not including the
      name of the command, something like C{sys.argv[1:]}.  If you pass
      C{sys.argv} instead, things are not going to work.

      The argument string will be parsed into an argument list by the
      L{util.splitCommandLine} function (see the documentation for that
      function for some important notes about its limitations).  There is an
      assumption that the resulting list will be equivalent to C{sys.argv[1:]},
      just like C{argumentList}.

      Unless the C{validate} argument is C{False}, the L{Options.validate}
      method will be called (with its default arguments) after successfully
      parsing any passed-in command line.  This validation ensures that
      appropriate actions, etc. have been specified.  Keep in mind that even if
      C{validate} is C{False}, it might not be possible to parse the passed-in
      command line, so an exception might still be raised.

      @note: The command line format is specified by the L{_usage} function.
      Call L{_usage} to see a usage statement for the cback script.

      @note: It is strongly suggested that the C{validate} option always be set
      to C{True} (the default) unless there is a specific need to read in
      invalid command line arguments.

      @param argumentList: Command line for a program.
      @type argumentList: List of arguments, i.e. C{sys.argv}

      @param argumentString: Command line for a program.
      @type argumentString: String, i.e. "cback --verbose stage store"

      @param validate: Validate the command line after parsing it.
      @type validate: Boolean true/false.

      @raise getopt.GetoptError: If the command-line arguments could not be parsed.
      @raise ValueError: If the command-line arguments are invalid.
      """
      self._help = False
      self._version = False
      self._verbose = False
      self._quiet = False
      self._config = None
      self._full = False
      self._logfile = None
      self._owner = None
      self._mode = None
      self._output = False
      self._debug = False
      self._stacktrace = False
      self._actions = None
      self.actions = []    # initialize to an empty list; remainder are OK
      if argumentList is not None and argumentString is not None:
         raise ValueError("Use either argumentList or argumentString, but not both.")
      if argumentString is not None:
         argumentList = splitCommandLine(argumentString)
      if argumentList is not None:
         self._parseArgumentList(argumentList)
         if validate:
            self.validate()


   #########################
   # String representations
   #########################

   def __repr__(self):
      """
      Official string representation for class instance.
      """
      return self.buildArgumentString(validate=False)

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
      if self._help != other._help:
         if self._help < other._help:
            return -1
         else:
            return 1
      if self._version != other._version:
         if self._version < other._version:
            return -1
         else:
            return 1
      if self._verbose != other._verbose:
         if self._verbose < other._verbose:
            return -1
         else:
            return 1
      if self._quiet != other._quiet:
         if self._quiet < other._quiet:
            return -1
         else:
            return 1
      if self._config != other._config:
         if self._config < other._config:
            return -1
         else:
            return 1
      if self._full != other._full:
         if self._full < other._full:
            return -1
         else:
            return 1
      if self._logfile != other._logfile:
         if self._logfile < other._logfile:
            return -1
         else:
            return 1
      if self._owner != other._owner:
         if self._owner < other._owner:
            return -1
         else:
            return 1
      if self._mode != other._mode:
         if self._mode < other._mode:
            return -1
         else:
            return 1
      if self._output != other._output:
         if self._output < other._output:
            return -1
         else:
            return 1
      if self._debug != other._debug:
         if self._debug < other._debug:
            return -1
         else:
            return 1
      if self._stacktrace != other._stacktrace:
         if self._stacktrace < other._stacktrace:
            return -1
         else:
            return 1
      if self._actions != other._actions:
         if self._actions < other._actions:
            return -1
         else:
            return 1
      return 0


   #############
   # Properties
   #############

   def _setHelp(self, value):
      """
      Property target used to set the help flag.
      No validations, but we normalize the value to C{True} or C{False}.
      """
      if value:
         self._help = True
      else:
         self._help = False

   def _getHelp(self):
      """
      Property target used to get the help flag.
      """
      return self._help

   def _setVersion(self, value):
      """
      Property target used to set the version flag.
      No validations, but we normalize the value to C{True} or C{False}.
      """
      if value:
         self._version = True
      else:
         self._version = False

   def _getVersion(self):
      """
      Property target used to get the version flag.
      """
      return self._version

   def _setVerbose(self, value):
      """
      Property target used to set the verbose flag.
      No validations, but we normalize the value to C{True} or C{False}.
      """
      if value:
         self._verbose = True
      else:
         self._verbose = False

   def _getVerbose(self):
      """
      Property target used to get the verbose flag.
      """
      return self._verbose

   def _setQuiet(self, value):
      """
      Property target used to set the quiet flag.
      No validations, but we normalize the value to C{True} or C{False}.
      """
      if value:
         self._quiet = True
      else:
         self._quiet = False

   def _getQuiet(self):
      """
      Property target used to get the quiet flag.
      """
      return self._quiet

   def _setConfig(self, value):
      """
      Property target used to set the config parameter.
      """
      if value is not None:
         if len(value) < 1:
            raise ValueError("The config parameter must be a non-empty string.") 
      self._config = value

   def _getConfig(self):
      """
      Property target used to get the config parameter.
      """
      return self._config

   def _setFull(self, value):
      """
      Property target used to set the full flag.
      No validations, but we normalize the value to C{True} or C{False}.
      """
      if value:
         self._full = True
      else:
         self._full = False

   def _getFull(self):
      """
      Property target used to get the full flag.
      """
      return self._full

   def _setLogfile(self, value):
      """
      Property target used to set the logfile parameter.
      @raise ValueError: If the value cannot be encoded properly.
      """
      if value is not None:
         if len(value) < 1:
            raise ValueError("The logfile parameter must be a non-empty string.") 
      self._logfile = encodePath(value)

   def _getLogfile(self):
      """
      Property target used to get the logfile parameter.
      """
      return self._logfile

   def _setOwner(self, value):
      """
      Property target used to set the owner parameter.
      If not C{None}, the owner must be a C{(user,group)} tuple or list.
      Strings (and inherited children of strings) are explicitly disallowed.
      The value will be normalized to a tuple.
      @raise ValueError: If the value is not valid.
      """
      if value is None:
         self._owner = None
      else:
         if isinstance(value, str):
            raise ValueError("Must specify user and group tuple for owner parameter.")
         if len(value) != 2:
            raise ValueError("Must specify user and group tuple for owner parameter.")
         if len(value[0]) < 1 or len(value[1]) < 1:
            raise ValueError("User and group tuple values must be non-empty strings.")
         self._owner = (value[0], value[1])

   def _getOwner(self):
      """
      Property target used to get the owner parameter.
      The parameter is a tuple of C{(user, group)}.
      """
      return self._owner

   def _setMode(self, value):
      """
      Property target used to set the mode parameter.
      """
      if value is None:
         self._mode = None
      else:
         try:
            if isinstance(value, str):
               value = int(value, 8)
            else:
               value = int(value)
         except TypeError:
            raise ValueError("Mode must be an octal integer >= 0, i.e. 644.")
         if value < 0:
            raise ValueError("Mode must be an octal integer >= 0. i.e. 644.")
         self._mode = value

   def _getMode(self):
      """
      Property target used to get the mode parameter.
      """
      return self._mode

   def _setOutput(self, value):
      """
      Property target used to set the output flag.
      No validations, but we normalize the value to C{True} or C{False}.
      """
      if value:
         self._output = True
      else:
         self._output = False

   def _getOutput(self):
      """
      Property target used to get the output flag.
      """
      return self._output

   def _setDebug(self, value):
      """
      Property target used to set the debug flag.
      No validations, but we normalize the value to C{True} or C{False}.
      """
      if value:
         self._debug = True
      else:
         self._debug = False

   def _getDebug(self):
      """
      Property target used to get the debug flag.
      """
      return self._debug

   def _setStacktrace(self, value):
      """
      Property target used to set the stacktrace flag.
      No validations, but we normalize the value to C{True} or C{False}.
      """
      if value:
         self._stacktrace = True
      else:
         self._stacktrace = False

   def _getStacktrace(self):
      """
      Property target used to get the stacktrace flag.
      """
      return self._stacktrace

   def _setActions(self, value):
      """
      Property target used to set the actions list.
      We don't restrict the contents of actions.  They're validated somewhere else.
      @raise ValueError: If the value is not valid.
      """
      if value is None:
         self._actions = None
      else:
         try:
            saved = self._actions
            self._actions = []
            self._actions.extend(value)
         except Exception, e:
            self._actions = saved
            raise e

   def _getActions(self):
      """
      Property target used to get the actions list.
      """
      return self._actions

   help = property(_getHelp, _setHelp, None, "Command-line help (C{-h,--help}) flag.")
   version = property(_getVersion, _setVersion, None, "Command-line version (C{-V,--version}) flag.")
   verbose = property(_getVerbose, _setVerbose, None, "Command-line verbose (C{-b,--verbose}) flag.")
   quiet = property(_getQuiet, _setQuiet, None, "Command-line quiet (C{-q,--quiet}) flag.")
   config = property(_getConfig, _setConfig, None, "Command-line configuration file (C{-c,--config}) parameter.")
   full = property(_getFull, _setFull, None, "Command-line full-backup (C{-f,--full}) flag.")
   logfile = property(_getLogfile, _setLogfile, None, "Command-line logfile (C{-l,--logfile}) parameter.")
   owner = property(_getOwner, _setOwner, None, "Command-line owner (C{-o,--owner}) parameter, as tuple C{(user,group)}.")
   mode = property(_getMode, _setMode, None, "Command-line mode (C{-m,--mode}) parameter.")
   output = property(_getOutput, _setOutput, None, "Command-line output (C{-O,--output}) flag.")
   debug = property(_getDebug, _setDebug, None, "Command-line debug (C{-d,--debug}) flag.")
   stacktrace = property(_getStacktrace, _setStacktrace, None, "Command-line stacktrace (C{-s,--stack}) flag.")
   actions = property(_getActions, _setActions, None, "Command-line actions list.")


   ##################
   # Utility methods
   ##################

   def validate(self):
      """
      Validates command-line options represented by the object.

      Unless C{--help} or C{--version} are supplied, at least one action must
      be specified.  Other validations (as for allowed values for particular
      options) will be taken care of at assignment time by the properties
      functionality.

      @note: The command line format is specified by the L{_usage} function.
      Call L{_usage} to see a usage statement for the cback script.

      @raise ValueError: If one of the validations fails.
      """
      if not self.help and not self.version:
         if self.actions is None or len(self.actions) == 0:
            raise ValueError("At least one action must be specified.")

   def buildArgumentList(self, validate=True):
      """
      Extracts options into a list of command line arguments.

      The original order of the various arguments (if, indeed, the object was
      initialized with a command-line) is not preserved in this generated
      argument list.   Besides that, the argument list is normalized to use the
      long option names (i.e. --version rather than -V).  The resulting list
      will be suitable for passing back to the constructor in the
      C{argumentList} parameter.  Unlike L{buildArgumentString}, string
      arguments are not quoted here, because there is no need for it.  

      Unless the C{validate} parameter is C{False}, the L{Options.validate}
      method will be called (with its default arguments) against the
      options before extracting the command line.  If the options are not valid,
      then an argument list will not be extracted.

      @note: It is strongly suggested that the C{validate} option always be set
      to C{True} (the default) unless there is a specific need to extract an
      invalid command line.

      @param validate: Validate the options before extracting the command line.
      @type validate: Boolean true/false.

      @return: List representation of command-line arguments.
      @raise ValueError: If options within the object are invalid.
      """
      if validate:
         self.validate()
      argumentList = []
      if self._help:
         argumentList.append("--help")
      if self.version:
         argumentList.append("--version")
      if self.verbose:
         argumentList.append("--verbose")
      if self.quiet:
         argumentList.append("--quiet")
      if self.config is not None:
         argumentList.append("--config")
         argumentList.append(self.config)
      if self.full:
         argumentList.append("--full")
      if self.logfile is not None:
         argumentList.append("--logfile")
         argumentList.append(self.logfile)
      if self.owner is not None:
         argumentList.append("--owner")
         argumentList.append("%s:%s" % (self.owner[0], self.owner[1]))
      if self.mode is not None:
         argumentList.append("--mode")
         argumentList.append("%o" % self.mode)
      if self.output:
         argumentList.append("--output")
      if self.debug:
         argumentList.append("--debug")
      if self.stacktrace:
         argumentList.append("--stack")
      if self.actions is not None:
         for action in self.actions:
            argumentList.append(action)
      return argumentList

   def buildArgumentString(self, validate=True):
      """
      Extracts options into a string of command-line arguments.

      The original order of the various arguments (if, indeed, the object was
      initialized with a command-line) is not preserved in this generated
      argument string.   Besides that, the argument string is normalized to use
      the long option names (i.e. --version rather than -V) and to quote all
      string arguments with double quotes (C{"}).  The resulting string will be
      suitable for passing back to the constructor in the C{argumentString}
      parameter.

      Unless the C{validate} parameter is C{False}, the L{Options.validate}
      method will be called (with its default arguments) against the options
      before extracting the command line.  If the options are not valid, then
      an argument string will not be extracted.

      @note: It is strongly suggested that the C{validate} option always be set
      to C{True} (the default) unless there is a specific need to extract an
      invalid command line.

      @param validate: Validate the options before extracting the command line.
      @type validate: Boolean true/false.

      @return: String representation of command-line arguments.
      @raise ValueError: If options within the object are invalid.
      """
      if validate:
         self.validate()
      argumentString = ""
      if self._help:
         argumentString += "--help "
      if self.version:
         argumentString += "--version "
      if self.verbose:
         argumentString += "--verbose "
      if self.quiet:
         argumentString += "--quiet "
      if self.config is not None:
         argumentString += "--config \"%s\" " % self.config
      if self.full:
         argumentString += "--full "
      if self.logfile is not None:
         argumentString += "--logfile \"%s\" " % self.logfile
      if self.owner is not None:
         argumentString += "--owner \"%s:%s\" " % (self.owner[0], self.owner[1])
      if self.mode is not None:
         argumentString += "--mode %o " % self.mode
      if self.output:
         argumentString += "--output "
      if self.debug:
         argumentString += "--debug "
      if self.stacktrace:
         argumentString += "--stack "
      if self.actions is not None:
         for action in self.actions:
            argumentString +=  "\"%s\" " % action
      return argumentString

   def _parseArgumentList(self, argumentList):
      """
      Internal method to parse a list of command-line arguments.

      Most of the validation we do here has to do with whether the arguments
      can be parsed and whether any values which exist are valid.  We don't do
      any validation as to whether required elements exist or whether elements
      exist in the proper combination (instead, that's the job of the
      L{validate} method).
   
      For any of the options which supply parameters, if the option is
      duplicated with long and short switches (i.e. C{-l} and a C{--logfile})
      then the long switch is used.  If the same option is duplicated with the
      same switch (long or short), then the last entry on the command line is
      used.

      @param argumentList: List of arguments to a command.
      @type argumentList: List of arguments to a command, i.e. C{sys.argv[1:]}

      @raise ValueError: If the argument list cannot be successfully parsed.
      """
      switches = { }
      opts, self.actions = getopt.getopt(argumentList, SHORT_SWITCHES, LONG_SWITCHES)
      for o,a in opts:  # push the switches into a hash
         switches[o] = a
      if switches.has_key("-h") or switches.has_key("--help"):
         self.help = True
      if switches.has_key("-V") or switches.has_key("--version"):
         self.version = True
      if switches.has_key("-b") or switches.has_key("--verbose"):
         self.verbose = True
      if switches.has_key("-q") or switches.has_key("--quiet"):
         self.quiet = True
      if switches.has_key("-c"):
         self.config = switches["-c"]
      if switches.has_key("--config"):
         self.config = switches["--config"]
      if switches.has_key("-f") or switches.has_key("--full"):
         self.full = True
      if switches.has_key("-l"):
         self.logfile = switches["-l"]
      if switches.has_key("--logfile"):
         self.logfile = switches["--logfile"]
      if switches.has_key("-o"):
         self.owner = switches["-o"].split(":", 1)
      if switches.has_key("--owner"):
         self.owner = switches["--owner"].split(":", 1)
      if switches.has_key("-m"):
         self.mode = switches["-m"]
      if switches.has_key("--mode"):
         self.mode = switches["--mode"]
      if switches.has_key("-O") or switches.has_key("--output"):
         self.output = True
      if switches.has_key("-d") or switches.has_key("--debug"):
         self.debug = True
      if switches.has_key("-s") or switches.has_key("--stack"):
         self.stacktrace = True


#########################################################################
# Main routine
########################################################################

if __name__ == "__main__":
   result = cli()
   sys.exit(result)

