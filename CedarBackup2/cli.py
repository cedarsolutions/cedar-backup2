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

@sort: Options, DEFAULT_CONFIG, DEFAULT_LOGFILE, DEFAULT_OWNERSHIP, 
       DEFAULT_MODE, VALID_ACTIONS, COMBINE_ACTIONS, NONCOMBINE_ACTIONS

@author: Kenneth J. Pronovici <pronovic@ieee.org>
"""

########################################################################
# Imported modules
########################################################################

# System modules
import sys
import logging
import getopt

# Cedar Backup modules
from CedarBackup2.release import VERSION, DATE, COPYRIGHT
from CedarBackup2.util import RestrictedContentList, splitCommandLine


########################################################################
# Module-wide constants and variables
########################################################################

logger = logging.getLogger("CedarBackup2.cli")

DEFAULT_CONFIG     = "/etc/cback.conf"
DEFAULT_LOGFILE    = "/var/log/cback.log"
DEFAULT_OWNERSHIP  = "root:adm"
DEFAULT_MODE       = 0640

VALID_ACTIONS      = [ "collect", "stage", "store", "purge", "rebuild", "validate", "all", ]
COMBINE_ACTIONS    = [ "collect", "stage", "store", "purge", ]
NONCOMBINE_ACTIONS = [ "rebuild", "validate", "all", ]

SHORT_SWITCHES     = "hVbqc:fl:o:m:Od"
LONG_SWITCHES      = [ 'help', 'version', 'verbose', 'quiet', 
                       'config=', 'full', 'logfile=', 'owner=', 
                       'mode=', 'output', 'debug', ]


#######################################################################
# Functions
#######################################################################

###################
# usage() function
###################

def usage(fd=sys.stderr):
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
   fd.write("   -c, --config   Path to config file (default: %s)" % DEFAULT_CONFIG)
   fd.write("   -f, --full     Perform a full backup, regardless of configuration\n")
   fd.write("   -l, --logfile  Path to logfile (default: %s)" % DEFAULT_LOGFILE)
   fd.write("   -o, --owner    Logfile ownership, user:group (default: %s)" % DEFAULT_OWNERSHIP)
   fd.write("   -m, --mode     Octal logfile permissions mode (default: %o)" % DEFAULT_MODE)
   fd.write("   -O, --output   Record some sub-command (i.e. tar) output to the log\n")
   fd.write("   -d, --debug    Write debugging information to the log (implies --output)\n")
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
   fd.write(" You must specify at least one action to take.  More than one of\n")
   fd.write(" the \"collect\", \"stage\", \"store\" or \"purge\" actions may be \n")
   fd.write(" specified in any arbitrary order; they will be executed in a \n")
   fd.write(" sensible order.  The \"all\", \"rebuild\" or \"validate\" \n")
   fd.write(" actions may not be combined with other actions.\n")
   fd.write("\n")


#####################
# version() function
#####################

def version(fd=sys.stdout):
   """
   Prints version information for the cback script.
   @param fd: File descriptor used to print information.
   @note: The C{fd} is used rather than C{print} to facilitate unit testing.
   """
   fd.write("\n")
   fd.write(" Cedar Backup version %s, released %s." % (VERSION, DATE))
   fd.write("\n")
   fd.write(" Copyright (c) %s Kenneth J. Pronovici <pronovic@ieee.org>." % COPYRIGHT)
   fd.write(" This is free software; there is NO warranty.  See the\n")
   fd.write(" GNU General Public License version 2 for copying conditions.\n")
   fd.write("\n")
   fd.write(" Use the --help option for usage information.\n")
   fd.write("\n")


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

      @note: The command line format is specified by the L{usage} function.
      Call L{usage} to see a usage statement for the cback script.

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
      argumentString = self.buildArgumentString(validate=False)
      return "Config(argumentString=%s)" % argumentString

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
      """
      if value is not None:
         if len(value) < 1:
            raise ValueError("The logfile parameter must be a non-empty string.") 
      self._logfile = value

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

   def _setActions(self, value):
      """
      Property target used to set the actions list.
      This list is maintained as unordered for the purposes of comparison.
      If not C{None}, the action list must contain only values in L{VALID_ACTIONS}.
      @raise ValueError: If the value is not valid.
      """
      if value is None:
         self._actions = None
      else:
         try:
            saved = self._actions
            self._actions = RestrictedContentList(VALID_ACTIONS, "Options.VALID_ACTIONS")
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
   verbose = property(_getVerbose, _setVerbose, None, "Command-line help (C{-b,--verbose}) flag.")
   quiet = property(_getQuiet, _setQuiet, None, "Command-line help (C{-q,--quiet}) flag.")
   config = property(_getConfig, _setConfig, None, "Command-line help (C{-c,--config}) parameter.")
   full = property(_getFull, _setFull, None, "Command-line help (C{-f,--full}) flag.")
   logfile = property(_getLogfile, _setLogfile, None, "Command-line help (C{-l,--logfile}) parameter.")
   owner = property(_getOwner, _setOwner, None, "Command-line owner (C{-o,--owner}) parameter, as tuple C{(user,group)}.")
   mode = property(_getMode, _setMode, None, "Command-line mode (C{-m,--mode}) parameter.")
   output = property(_getOutput, _setOutput, None, "Command-line output (C{-O,--output}) flag.")
   debug = property(_getDebug, _setDebug, None, "Command-line debug (C{-d,--debug}) flag.")
   actions = property(_getActions, _setActions, None, "Command-line actions list.")


   ##################
   # Utility methods
   ##################

   def validate(self):
      """
      Validates command-line options represented by the object.

      Unless C{--help} or C{--version} are supplied, at least one action must
      be specified.  Actions from among L{COMBINE_ACTIONS} may be combined in
      any arbitrary order.  The actions from within L{NONCOMBINE_ACTIONS} may
      not be combined with other actions.

      Other validations (as for allowed values for particular options) will be
      taken care of at assignment time by the properties functionality.

      @note: The command line format is specified by the L{usage} function.
      Call L{usage} to see a usage statement for the cback script.

      @raise ValueError: If one of the validations fails.
      """
      if not self.help and not self.version:
         if self.actions is None or len(self.actions) == 0:
            raise ValueError("At least one action must be specified.")
      for action in NONCOMBINE_ACTIONS:
         if action in self.actions and self.actions != [ action, ]:
            raise ValueError("Action %s may not be combined with other actions." % action)

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

