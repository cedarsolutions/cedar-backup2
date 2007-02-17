#!/usr/bin/env python
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
# Project  : Cedar Backup, release 2
# Revision : $Id$
# Purpose  : Spans staged data among multiple discs
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

########################################################################
# Notes
########################################################################

"""
Spans staged data among multiple discs

This is the Cedar Backup span tool.  It is intended for use by people who stage
more data than can fit on a single disc.  It allows a user to split staged data
among more than one disc.  It can't be an extension because it requires user
input when switching media.

Most configuration is taken from the Cedar Backup configuration file,
specifically the store section.  A few pieces of configuration are taken
directly from the user.

@author: Kenneth J. Pronovici <pronovic@ieee.org>
"""

########################################################################
# Imported modules and constants
########################################################################

# System modules
import sys
import logging

# Cedar Backup modules 
from CedarBackup2.release import AUTHOR, EMAIL, VERSION, DATE, COPYRIGHT
from CedarBackup2.config import Config
from CedarBackup2.cli import Options, setupLogging, setupPathResolver
from CedarBackup2.cli import DEFAULT_CONFIG, DEFAULT_LOGFILE, DEFAULT_OWNERSHIP, DEFAULT_MODE
from CedarBackup2.knapsack import firstFit, bestFit, worstFit, alternateFit


########################################################################
# Module-wide constants and variables
########################################################################

logger = logging.getLogger("CedarBackup2.log.tools.span")


#######################################################################
# SpanOptions class
#######################################################################

class SpanOptions(Options):

   """
   Tool-specific command-line options.

   Most of the cback command-line options are exactly what we need here --
   logfile path, permissions, verbosity, etc.  However, we need to make a few
   tweaks since we don't accept any actions.
   """

   def validate(self):
      """
      Validates command-line options represented by the object.
      There are no validations here, because we don't use any actions.
      @raise ValueError: If one of the validations fails.
      """
      pass


#######################################################################
# Public functions
#######################################################################

#################
# cli() function
#################

def cli():
   """
   Implements the command-line interface for the C{cback-span} script.

   Essentially, this is the "main routine" for the cback-span script.  It does
   all of the argument processing for the script, and then also implements the
   tool functionality.

   This function looks pretty similiar to C{CedarBackup2.cli.cli()}.  It's not
   easy to refactor this code to make it reusable and also readable, so I've
   decided to just live with the duplication.

   A different error code is returned for each type of failure:

      - C{1}: The Python interpreter version is < 2.3
      - C{2}: Error processing command-line arguments
      - C{3}: Error configuring logging
      - C{4}: Error parsing indicated configuration file
      - C{5}: Backup was interrupted with a CTRL-C or similar
      - C{6}: Error executing other parts of the script

   @note: This script uses print rather than logging to the INFO level, because
   it is interactive.  Underlying functionality uses the logging mechanism
   exclusively.

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
      options = SpanOptions(argumentList=sys.argv[1:])
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
      logfile = setupLogging(options)
   except Exception, e:
      sys.stderr.write("Error setting up logging: %s\n" % e)
      return 3

   logger.info("Cedar Backup 'span' utility run started.")
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
      setupPathResolver(config)
   except Exception, e:
      logger.error("Error reading or handling configuration: %s" % e)
      logger.info("Cedar Backup 'span' utility run completed with status 4.")
      return 4

   if options.stacktrace:
      _executeAction(options, config)
   else:
      try:
         _executeAction(options, config)
      except KeyboardInterrupt:
         logger.error("Backup interrupted.")
         logger.info("Cedar Backup 'span' utility run completed with status 5.")
         return 5
      except Exception, e:
         logger.error("Error executing backup: %s" % e)
         logger.info("Cedar Backup 'span' utility run completed with status 6.")
         return 6

   logger.info("Cedar Backup 'span' utility run completed with status 0.")
   return 0


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
   fd.write(" Usage: cback-span [switches]\n")
   fd.write("\n")
   fd.write(" This Cedar Backup utility spans staged data between multiple discs.\n")
   fd.write(" It is a utility, not an extension, and requires user interaction.\n")
   fd.write("\n")
   fd.write(" The following switches are accepted, mostly to set up underlying\n")
   fd.write(" Cedar Backup functionality:\n")
   fd.write("\n")
   fd.write("   -h, --help     Display this usage/help listing\n")
   fd.write("   -V, --version  Display version information\n")
   fd.write("   -c, --config   Path to config file (default: %s)\n" % DEFAULT_CONFIG)
   fd.write("   -b, --verbose  Print verbose output as well as logging to disk\n")
   fd.write("   -l, --logfile  Path to logfile (default: %s)\n" % DEFAULT_LOGFILE)
   fd.write("   -o, --owner    Logfile ownership, user:group (default: %s:%s)\n" % (DEFAULT_OWNERSHIP[0], DEFAULT_OWNERSHIP[1]))
   fd.write("   -m, --mode     Octal logfile permissions mode (default: %o)\n" % DEFAULT_MODE)
   fd.write("   -O, --output   Record some sub-command (i.e. tar) output to the log\n")
   fd.write("   -d, --debug    Write debugging information to the log (implies --output)\n")
   fd.write("   -s, --stack    Dump a Python stack trace instead of swallowing exceptions\n")
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
   fd.write(" Cedar Backup 'span' tool.\n")
   fd.write(" Included with Cedar Backup version %s, released %s.\n" % (VERSION, DATE))
   fd.write("\n")
   fd.write(" Copyright (c) %s %s <%s>.\n" % (COPYRIGHT, AUTHOR, EMAIL))
   fd.write(" See CREDITS for a list of included code and other contributors.\n")
   fd.write(" This is free software; there is NO warranty.  See the\n")
   fd.write(" GNU General Public License version 2 for copying conditions.\n")
   fd.write("\n")
   fd.write(" Use the --help option for usage information.\n")
   fd.write("\n")


############################
# _executeAction() function
############################

def _executeAction(options, config):
   """
   Implements the guts of the cback-span tool.

   @param options: Program command-line options.
   @type options: SpanOptions object.

   @param config: Program configuration.
   @type config: Config object.

   @raise Exception: Under many generic error conditions
   """
   pass


#########################################################################
# Main routine
########################################################################

if __name__ == "__main__":
   result = cli()
   sys.exit(result)

