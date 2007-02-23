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
import os
import logging
import tempfile

# Cedar Backup modules 
from CedarBackup2.release import AUTHOR, EMAIL, VERSION, DATE, COPYRIGHT
from CedarBackup2.util import displayBytes, convertSize, mount, unmount
from CedarBackup2.util import UNIT_SECTORS, UNIT_BYTES
from CedarBackup2.config import Config
from CedarBackup2.filesystem import FilesystemList, BackupFileList, compareDigestMaps, normalizeDir
from CedarBackup2.cli import Options, setupLogging, setupPathResolver
from CedarBackup2.cli import DEFAULT_CONFIG, DEFAULT_LOGFILE, DEFAULT_OWNERSHIP, DEFAULT_MODE
from CedarBackup2.actions.constants import STORE_INDICATOR
from CedarBackup2.actions.store import createWriter, consistencyCheck, writeStoreIndicator
from CedarBackup2.actions.util import findDailyDirs
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

   Also, a few extra command line options that we accept are really ignored
   underneath.  I just don't care about that for a tool like this.
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
   it is interactive.  Underlying Cedar Backup functionality uses the logging
   mechanism exclusively.

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
   fd.write(" Cedar Backup 'span' tool.\n")
   fd.write("\n")
   fd.write(" This Cedar Backup utility spans staged data between multiple discs.\n")
   fd.write(" It is a utility, not an extension, and requires user interaction.\n")
   fd.write("\n")
   fd.write(" The following switches are accepted, mostly to set up underlying\n")
   fd.write(" Cedar Backup functionality:\n")
   fd.write("\n")
   fd.write("   -h, --help     Display this usage/help listing\n")
   fd.write("   -V, --version  Display version information\n")
   fd.write("   -b, --verbose  Print verbose output as well as logging to disk\n")
   fd.write("   -c, --config   Path to config file (default: %s)\n" % DEFAULT_CONFIG)
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
   print ""
   print "================================================";
   print "           Cedar Backup 'span' tool"
   print "================================================";
   print ""
   print "This the Cedar Backup span tool.  It is used to split up staging"
   print "data when that staging data does not fit onto a single disc."
   print ""
   print "This utility operates using Cedar Backup configuration.  Configuration"
   print "specifies which staging directory to look at and which writer device"
   print "and media type to use."
   print ""
   if not _getYesNoAnswer("Continue?", default="Y"):
      return
   print "==="

   print ""
   print "Cedar Backup store configuration looks like this:"
   print ""
   print "   Source Directory...: %s" % config.store.sourceDir
   print "   Media Type.........: %s" % config.store.mediaType
   print "   Device Type........: %s" % config.store.deviceType
   print "   Device Path........: %s" % config.store.devicePath
   print "   Device SCSI ID.....: %s" % config.store.deviceScsiId
   print "   Drive Speed........: %s" % config.store.driveSpeed
   print "   Check Data Flag....: %s" % config.store.checkData
   print "   No Eject Flag......: %s" % config.store.noEject
   print ""
   if not _getYesNoAnswer("Is this OK?", default="Y"):
      return
   print "==="

   (writer, mediaCapacity) = _getWriter(config)

   print ""
   print "Please wait, indexing the source directory (this may take a while)..."
   (dailyDirs, fileList) = _findDailyDirs(config.store.sourceDir)
   print "==="

   print ""
   print "The following daily staging directories have not yet been written to disc:"
   print ""
   for dailyDir in dailyDirs:
      print "   %s" % dailyDir

   totalSize = fileList.totalSize()
   print ""
   print "The total size of the data in these directories is %s." % displayBytes(totalSize)
   print ""
   if not _getYesNoAnswer("Continue?", default="Y"):
      return
   print "==="

   print ""
   print "Based on configuration, the capacity of your media is %s." % displayBytes(mediaCapacity)

   print ""
   print "Since estimates are not perfect and there is some uncertainly in"
   print "media capacity calculations, it is good to have a \"cushion\","
   print "a percentage of capacity to set aside.  The cushion reduces the"
   print "capacity of your media, so a 1.5% cushion leaves 98.5% remaining."
   print ""
   cushion = _getFloat("What cushion percentage?", default=4.5)
   print "==="

   realCapacity = ((100.0 - cushion)/100.0) * mediaCapacity
   minimumDiscs = (totalSize/realCapacity) + 1;
   print ""
   print "The real capacity, taking into account the %.2f%% cushion, is %s." % (cushion, displayBytes(realCapacity))
   print "It will take at least %d disc(s) to store your %s of data." % (minimumDiscs, displayBytes(totalSize))
   print ""
   if not _getYesNoAnswer("Continue?", default="Y"):
      return
   print "==="
   
   happy = False
   while not happy:
      print ""
      print "Which algorithm do you want to use to span your data across"
      print "multiple discs?"
      print ""
      print "The following algorithms are available:"
      print ""
      print "   first....: The \"first-fit\" algorithm"
      print "   best.....: The \"best-fit\" algorithm"
      print "   worst....: The \"worst-fit\" algorithm"
      print "   alternate: The \"alternate-fit\" algorithm"
      print ""
      print "If you don't like the results you will have a chance to try a"
      print "different one later."
      print ""
      algorithm = _getChoiceAnswer("Which algorithm?", "worst", [ "first", "best", "worst", "alternate",])
      print "==="

      print ""
      print "Please wait, generating file lists (this may take a while)..."
      spanSet = fileList.generateSpan(capacity=realCapacity, algorithm="%s_fit" % algorithm)
      print "==="

      print ""
      print "Using the \"%s-fit\" algorithm, Cedar Backup can split your data" % algorithm
      print "into %d discs." % len(spanSet)
      print ""
      counter = 0
      for item in spanSet:
         counter += 1
         print "Disc %d: %d files, %s, %.2f%% utilization" % (counter, len(item.fileList), 
                                                              displayBytes(item.size), item.utilization)
      print ""
      if _getYesNoAnswer("Accept this solution?", default="Y"):
         happy = True
      print "==="

   print ""
   _getReturn("Please place the first disc in your backup device.\nPress return when ready.")
   print "==="

   counter = 0
   for spanItem in spanSet:
      counter += 1
      _writeDisc(config, writer, spanItem)
      print ""
      _getReturn("Please replace the disc in your backup device.\nPress return when ready.")
      print "==="

   writeStoreIndicator(config, dailyDirs)

   print ""
   print "Completed writing all discs."


############################
# _findDailyDirs() function
############################

def _findDailyDirs(stagingDir):
   """
   Returns a list of all daily staging directories that have not yet been
   stored.

   The store indicator file C{cback.store} will be written to a daily staging
   directory once that directory is written to disc.  So, this function looks
   at each daily staging directory within the configured staging directory, and
   returns a list of those which do not contain the indicator file.

   Returned is a tuple containing two items: a list of daily staging
   directories, and a BackupFileList containing all files among those staging
   directories.

   @param stagingDir: Configured staging directory 

   @return: Tuple (staging dirs, backup file list)
   """
   results = findDailyDirs(stagingDir, STORE_INDICATOR)
   fileList = BackupFileList()
   for item in results:
      fileList.addDirContents(item)
   return (results, fileList)


########################
# _getWriter() function
########################

def _getWriter(config):
   """
   Gets a writer and media capacity from store configuration.
   Returned is a writer and a media capacity in bytes.
   @param config: Cedar Backup configuration
   @return: Tuple of (writer, mediaCapacity) 
   """
   writer = createWriter(config)
   mediaCapacity = convertSize(writer.media.capacity, UNIT_SECTORS, UNIT_BYTES)
   return (writer, mediaCapacity)


########################
# _writeDisc() function
########################

def _writeDisc(config, writer, spanItem):
   """
   Writes a span item to disc.
   @param config: Cedar Backup configuration
   @param writer: Writer to use
   @param spanItem: Span item to write
   """
   print ""
   print "Initializing image..."
   writer.initializeImage(newDisc=True, tmpdir=config.options.workingDir)
   for path in spanItem.fileList:
      graftPoint = os.path.dirname(path.replace(config.store.sourceDir, "", 1))
      writer.addImageEntry(path, graftPoint)
   print "Writing image to disc..."
   writer.writeImage()
   if config.store.checkData:
      print "Running consistency check..."
      _consistencyCheck(config, spanItem.fileList)
   print "Write process is complete."


###############################
# _consistencyCheck() function
###############################

def _consistencyCheck(config, fileList):
   """
   Runs a consistency check against media in the backup device.

   The function mounts the device at a temporary mount point in the working
   directory, and then compares the passed-in file list's digest map with the
   one generated from the disc.  The two lists should be identical.

   If no exceptions are thrown, there were no problems with the consistency
   check.

   @warning: The implementation of this function is very UNIX-specific.

   @param config: Config object.
   @param fileList: BackupFileList whose contents to check against

   @raise ValueError: If the check fails
   @raise IOError: If there is a problem working with the media.
   """
   logger.debug("Running consistency check.")
   mountPoint = tempfile.mkdtemp(dir=config.options.workingDir)
   try:
      mount(config.store.devicePath, mountPoint, "iso9660")
      discList = BackupFileList()
      discList.addDirContents(mountPoint)
      sourceList = BackupFileList()
      sourceList.extend(fileList)
      discListDigest = discList.generateDigestMap(stripPrefix=normalizeDir(mountPoint))
      sourceListDigest = sourceList.generateDigestMap(stripPrefix=normalizeDir(config.store.sourceDir))
      compareDigestMaps(sourceListDigest, discListDigest, verbose=True)
      logger.info("Consistency check completed.  No problems found.")
   finally:
      unmount(mountPoint, True, 5, 1)  # try 5 times, and remove mount point when done 


#########################################################################
# User interface utilities
########################################################################

def _getYesNoAnswer(prompt, default):
   """
   Get a yes/no answer from the user.
   The default will be placed at the end of the prompt.
   A "Y" or "y" is considered yes, anything else no.
   A blank (empty) response results in the default.
   @param prompt: Prompt to show.
   @param default: Default to set if the result is blank
   @return: Boolean true/false corresponding to Y/N
   """
   if default == "Y":
      prompt = "%s [Y/n]: " % prompt
   else:
      prompt = "%s [y/N]: " % prompt
   answer = raw_input(prompt)
   if answer in [ None, "", ]:
      answer = default
   if answer[0] in [ "Y", "y", ]:
      return True
   else:
      return False

def _getChoiceAnswer(prompt, default, validChoices):
   """
   Get a particular choice from the user.
   The default will be placed at the end of the prompt.
   The function loops until getting a valid choice.
   A blank (empty) response results in the default.
   @param prompt: Prompt to show.
   @param default: Default to set if the result is None or blank.
   @param validChoices: List of valid choices (strings)
   @return: Valid choice from user.
   """
   prompt = "%s [%s]: " % (prompt, default)
   answer = raw_input(prompt)
   if answer in [ None, "", ]:
      answer = default
   while answer not in validChoices:
      print "Choice must be one of %s" % validChoices
      answer = raw_input(prompt)
   return answer

def _getFloat(prompt, default):
   """
   Get a floating point number from the user.
   The default will be placed at the end of the prompt.
   The function loops until getting a valid floating point number.
   A blank (empty) response results in the default.
   @param prompt: Prompt to show.
   @param default: Default to set if the result is None or blank.
   @return: Floating point number from user
   """
   prompt = "%s [%.2f]: " % (prompt, default)
   while True:
      answer = raw_input(prompt)
      if answer in [ None, "" ]:
         return default
      else:
         try:
            return float(answer)
         except ValueError:
            print "Enter a floating point number."

def _getReturn(prompt):
   """
   Get a return key from the user.
   @param prompt: Prompt to show.
   """
   raw_input(prompt)


#########################################################################
# Main routine
########################################################################

if __name__ == "__main__":
   result = cli()
   sys.exit(result)

