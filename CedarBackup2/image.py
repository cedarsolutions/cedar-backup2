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
# Purpose  : Provides ISO image-related objects.
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# This file was created with a width of 132 characters, and NO tabs.

########################################################################
# Module documentation
########################################################################

"""
Provides ISO image-related objects.
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
from CedarBackup2.knapsack import worstFit
from CedarBackup2.util import executeCommand


########################################################################
# Module-wide constants and variables
########################################################################

logger = logging.getLogger("CedarBackup2.image")

MKISOFS_CMD          = "mkisofs"
MKISOFS_SECTOR_SIZE  = 2048       # Size of an ISO sector generated by mkisofs

BYTES_PER_KBYTE      = 1024.0
KBYTES_PER_MBYTE     = 1024.0
BYTES_PER_MBYTE      = BYTES_PER_KBYTE * KBYTES_PER_MBYTE


########################################################################
# IsoImage class definition
########################################################################

class IsoImage(object):

   ######################
   # Class documentation
   ######################

   """
   Represents an ISO filesystem image.

   Summary
   =======

      This object represents an ISO 9660 filesystem image.  It is implemented
      in terms of the C{mkisofs} program, which has been ported to many
      operating systems and platforms.  A "sensible subset" of the mkisofs
      functionality is made available through the public interface, allowing
      callers to set a variety of basic options such as publisher id,
      application id, etc. as well as specify exactly which files and
      directories they want included in their image.

      By default, the image is created using the Rock Ridge protocol (using the
      C{-r} option to mkisofs) because Rock Ridge discs are generally more
      useful on UN*X filesystems than standard ISO 9660 images.  However,
      callers can fall back to the default mkisofs functionality by setting the
      C{useRockRidge} instance variable to C{False}.  

      In any case, since soft links are ignored by mkisofs by default, they
      will be ignored here, too.

      The class also includes some functionality that attempts to "prune" a
      defined image to fit in a certain amount of free space.  This should help
      callers who want to write a disc, even if they can't fit everything they
      want on it.  Note, however, that this option is not well-tested.

   Graft Points
   ============

      It possible to graft a path into an ISO image at a point other than the
      root directory of the image using either the object-wide C{graftPoint}
      instance variable or the C{graftPoint} parameter to this method.  

      The mkisofs documentation has this to say about graft points::

          ...it is possible to graft the paths at points other than the root
          directory, and it is possible to graft files or directories onto the
          cdrom image with names different than what they have in the source
          filesystem.  This is easiest to illustrate with a couple of examples.
          Let's start by assuming that a local file ../old.lis exists, and you
          wish to include it in the cdrom image.

               foo/bar/=../old.lis

          will include the file old.lis in the cdrom image at /foo/bar/old.lis,
          while

               foo/bar/xxx=../old.lis

          will include the file old.lis in the cdrom image at /foo/bar/xxx.
          The same sort of syntax can be used with directories as well.
          mkisofs will create any directories required such that the graft
          points exist on the cdrom image - the directories do not need to
          appear in one of the paths. 

      For our purposes, to include the file C{../old.lis} at
      C{/foo/bar/old.lis}, you would call::

          addEntry(path="../old.lis", graftPoint="foo/bar")

      You could also set an object-wide graft point using the C{graftPoint}
      instance variable.   If a graft point is not set, the default behavior is
      used.

   @ivar graftPoint: Default image-wide graft point (see L{addEntry} for details).
   @ivar useRockRidge: Indicates whether to use the RockRidge protocol (default is True).
   @ivar applicationId: Optionally specifies the ISO header application id value.
   @ivar biblioFile: Optionally specifies ISO bibliographic file name.
   @ivar publisherId: Optionally specifies the ISO header publisher id value.
   @ivar preparerId: Optionally specifies the ISO header preparer id value.
   @ivar volumeId: Optionally specifies the ISO header volume id value.
   """

   ##############
   # Constructor
   ##############

   def __init__(self, device=None, boundaries=None, graftPoint=None):
      """
      Initializes an empty ISO image object.

      Only the most commonly-used configuration items can be set using this
      constructor.  If you have a need to change the others, do so immediately
      after creating your object.

      The device and boundaries values are both required in order to write
      multisession discs.  If either is missing or C{None}, a multisession disc
      will not be written.

      @param device: Name of the device that the image will be written to
      @type device: Either be a filesystem path (C{"/dev/cdrw"}) or a SCSI address (C{"[ATA:]scsibus,target,lun"}).

      @param boundaries: Session boundaries as required by C{mkisofs}
      @type boundaries: Tuple (last_sess_start,next_sess_start) as returned from C{cdrecord -msinfo}

      @param graftPoint: Default graft point for this page.
      @type graftPoint: String representing a graft point path (see L{addEntry}).
      """
      self.entries = { }
      self.device = device
      self.boundaries = boundaries
      self.graftPoint = graftPoint
      self.useRockRidge = True
      self.applicationId = None
      self.biblioFile = None
      self.publisherId = None
      self.preparerId = None
      self.volumeId = None
      logger.debug("Created new ISO image object.")


   #########################
   # General public methods
   #########################

   def writeImage(self, imagePath):
      """
      Writes this image to disk using the image path.

      @param imagePath: Path to write image out as
      @type imagePath: String representing a path on disk

      @raise IOError: If there is an error writing the image to disk.
      """
      args = self._buildWriteArgs(imagePath)
      result = executeCommand(MKISOFS_CMD, args)
      if result != 0:
         raise IOError("Error executing mkisofs command to build image." % result)

   def getEstimatedSize(self):
      """
      Returns the estimated size (in bytes) of the ISO image.

      This is implemented via the C{-print-size} option to C{mkisofs}, so it
      might take a bit of time to execute.  However, the result is as accurate
      as we can get, since it takes into account all of the ISO overhead, the
      true cost of directories in the structure, etc, etc.

      @return: Estimated size of the image, in bytes.
      @raise IOError: If there is a problem calling mkisofs.
      """
      return self._getEstimatedSize(self.entries)

   def _getEstimatedSize(self, entries):
      """
      Returns the estimated size (in bytes) for the passed-in entries dictionary.
      @return: Estimated size of the image, in bytes.
      @raise IOError: If there is a problem calling mkisofs.
      """
      args = self._buildSizeArgs(entries)
      (result, output) = executeCommand(MKISOFS_CMD, args, returnOutput=True)
      if result != 0:
         raise IOError("Error executing mkisofs command to estimate size." % result)
      if len(output) != 1:
         raise IOError("Unable to parse mkisofs output.")
      try:
         sectors = int(output[0])
         size = sectors * MKISOFS_SECTOR_SIZE
         return size
      except: 
         raise IOError("Unable to parse mkisofs output.")

   def addEntry(self, path, graftPoint=None, override=False):
      """
      Adds an individual file or directory into the ISO image.

      The path must exist and must be a file or a directory.  By default, the
      entry will be placed into the image at the root directory, but this
      behavior can be overridden using the C{graftPoint} parameter or instance
      variable.

      @note: An exception will be thrown if the path has already been added to
      the image, unless the C{override} parameter is set to C{True}.

      @note: The method C{graftPoints} parameter overrides the object-wide
      instance variable.  If neither the method parameter or object-wide values
      is set, the path will be written at the image root.  The graft point
      behavior is determined by what value is in effect I{at the time this
      method is called}, so you I{must} set the object-wide value before
      calling this method for the first time, or your image may not be
      consistent.

      @param path: File or directory to be added to the image
      @type path: String representing a path on disk

      @param graftPoint: Graft point to be used when adding this entry
      @type graftPoint: String representing a graft point path, as described above

      @raise ValueError: If path is not a file or directory, or does not exist.
      @raise ValueError: If the path has already been added, and override is not set.
      """
      if os.path.islink(path) or (not os.path.isdir(path) and not os.path.isfile(path)):
         raise ValueError("Path must be an existing file or directory (not a link).")
      if not override:
         if path in self.entries.keys:
            raise ValueError("Path has already been added to the image.")
      if graftPoint is not None:
         self.entries[path] = graftPoint
      else:
         self.entries[path] = self.graftPoint   # self.graftPoint might be None


   ######################
   # Prune functionality
   ######################

   def pruneImage(self, capacity):
      """
      Prunes the image to fit a certain capacity, in bytes.

      The contents of the image will be pruned in an attempt to fit the image
      into the indicated capacity.  The pruning process is iterative and might
      take a number of attempts to get right because we can't always be sure
      what overhead the ISO protocol will add.  We'll only try a certain number
      of times before giving up and raising an C{IOError} exception.

      @note: Pruning an image has the effect of expanding any directory to its
      list of composite files internally.  This could slow down your mkisofs
      call (but it should still work).

      @note: This process is destructive.  Once you prune an image, you can't
      get it back in its original form without rebuilding it from scratch.
      However, the object should be unchanged unless it returns successfully.

      @param capacity: Capacity to prune to
      @type pruneCapacity: Integer capacity, in bytes

      @return: Estimated size of the image, in bytes, as from L{getEstimatedSize}.
      @raise IOError: If we can't prune to fit the image into the capacity.
      """
      if len(self.entries) > 0:
         entries = self._pruneImage(capacity)
         self.entries = entries
      return self.getEstimatedSize()

   def _pruneImage(self, capacity):
      """
      Prunes the image to fit a certain capacity, in bytes.

      This is an internal method.  It mainly exists so we can adequately
      document the pruning procedure without telling external callers exactly
      how it's done.

      To be successful, we have to build an entries dictionary such that the
      resulting ISO image uses C{capacity} or fewer bytes.  We determine a
      target overall file size, use a knapsack algorithm to hit that capacity,
      and then check whether the resulting image would fit in our capacity.  If
      it would fit, then we build a new entries dictionary and return it.
      Otherwise we try a few more times, giving up after four attempts.

      The trick is figuring out how to determine the target overall file size,
      by which we mean the target size among the files represented by the list
      of entries.  This size doesn't map directly to the capacity, because it
      doesn't take into account overhead related to the ISO image or to storing
      directories and links (which look "empty" on the filesystem).

      The first step is to establish a relationship between the size of the
      files in the image and the size of the image itself.  The size of the
      image minus the size of the files gives us a value for approximate
      overhead required to create the image.  Assuming that the overhead won't
      get any larger if the number of entries shrinks, our new target overall
      file size is the capacity minus the overhead.  Initially, we try to
      generate our list of entries using the original target capacity.  If that
      doesn't work, we make a few additional passes, subtracting off a bit more
      capacity each time.

      We always consider it to be an error if we are unable to fit any files
      into the image.  That's important to notice, because if no files fit,
      that accidentally could look like success to us (the image would
      certainly be small enough, unless the overhead exceeds the capacity).

      @param capacity: Capacity to prune to
      @type pruneCapacity: Integer capacity, in bytes

      @return: Pruned entries dictionary safe to apply to self.entries
      @raise IOError: If we can't prune to fit the image into the capacity.
      """
      expanded = self._expandEntries() 
      (sizeMap, fileSize) = IsoImage._calculateSizes(expanded)
      estimatedSize = self._getEstimatedSize(self.entries)
      overhead = estimatedSize - fileSize
      if overhead >= capacity:   # use >= just to be safe
         raise IOError("Required overhead exceeds available capacity.")

      targetSize = capacity - overhead
      (items, used) = worstFit(sizeMap, targetSize)
      if len(items) == 0 or used == 0:
         raise IOError("Unable to fit any entries into available capacity.")
      prunedEntries = IsoImage._buildEntries(expanded, items)
      estimatedSize = self._getEstimatedSize(prunedEntries)
      if(estimatedSize <= capacity):
         return prunedEntries

      targetSize = (capacity - overhead) * 0.95
      (items, used) = worstFit(sizeMap, targetSize)
      if len(items) == 0 or used == 0:
         raise IOError("Unable to fit any entries into available capacity.")
      prunedEntries = IsoImage._buildEntries(expanded, items)
      estimatedSize = self._getEstimatedSize(prunedEntries)
      if(estimatedSize <= capacity):
         return prunedEntries

      targetSize = (capacity - overhead) * 0.90
      (items, used) = worstFit(sizeMap, targetSize)
      if len(items) == 0 or used == 0:
         raise IOError("Unable to fit any entries into available capacity.")
      prunedEntries = IsoImage._buildEntries(expanded, items)
      estimatedSize = self._getEstimatedSize(prunedEntries)
      if(estimatedSize <= capacity):
         return prunedEntries

      targetSize = (capacity - overhead) * 0.80
      (items, used) = worstFit(sizeMap, targetSize)
      if len(items) == 0 or used == 0:
         raise IOError("Unable to fit any entries into available capacity.")
      prunedEntries = IsoImage._buildEntries(expanded, items)
      estimatedSize = self._getEstimatedSize(prunedEntries)
      if(estimatedSize <= capacity):
         return prunedEntries

      raise IOError("Unable to prune image to fit the capacity after four tries.")

   def _expandEntries(self):
      """
      Expands entries in an image to include only files.

      Most of the time, we will add only directories to an image, with an
      occassional file here and there.  However, we need to get at the files in
      the each directory in order to prune to fit a particular capacity.  So,
      this function goes through the the various entries and expands every
      directory it finds.  The result is an "equivalent" entries dictionary
      that verbosely includes every file that would have been included
      originally, along with its associated graft point (if any).

      @return: Expanded entries dictionary.
      """
      newEntries = { }
      for entry in self.entries:
         if not os.path.islink(entry):
            if os.path.isfile(entry):
               newEntries[entry] = self.entries[entry]
            elif os.path.isdir(entry):
               fsList = FilesystemList()
               fsList.excludeLinks = True
               fsList.excludeDirs = True
               fsList.addDirContents(entry)
               for item in fsList:
                  newEntries[item] = self.entries[entry]
      return newEntries

   def _calculateSizes(entries):
      """
      Calculates sizes for files in an entries dictionary.

      The entries dictionary is assumed to have been "expanded", so that it
      contains only files.  The resulting map is suitable for passing to a
      knapsack function; the total includes all files.

      @param entries: An entries map (expanded via L{_expandEntries})

      @return: Tuple (map, total) where map is suitable for passing to a knapsack function.
      """
      table = { }
      total = 0
      for entry in entries:
         size = os.stat(entry).st_size
         table[entry] = (entry, size)
         total += size
      return (table, total)
   _calculateSizes = staticmethod(_calculateSizes)

   def _buildEntries(entries, items):
      """
      Builds an entries dictionary.
      
      The result is basically the intersection of the passed-in entries
      dictionary with the keys that are in the list.  The passed-in entries
      dictionary will not be modified.

      @param entries: Entries dictionary to work from
      @param items: List of items to be used as keys into the dictionary

      @return: New entries dictionary that contains only the keys in the list
      """
      newEntries = { }
      for i in items:
         newEntries[i] = entries[i]
      return entries
   _buildEntries = staticmethod(_buildEntries)


   #########################################
   # Methods used to build mkisofs commands
   #########################################

   def _buildDirEntries(entries):
      """
      Uses an entries dictionary to build a list of directory locations for use
      by mkisofs.

      We build a list of entries that can be passed to mkisofs.  Each entry is
      either raw (if no graft point was configured) or in graft-point form as
      described above (if a graft point was configured).  The dictionary keys
      are the path names, and the values are the graft points, if any.

      @param entries: Dictionary of image entries (i.e. self.entries)

      @return: List of directory locations for use by mkisofs
      """
      dirEntries = []
      for key in entries.keys:
         if entries[key] is None:
            dirEntries.append(key)
         else:
            dirEntries.append("%s/=%s/ " % (entries[key], key))
      return dirEntries
   _buildDirEntries = staticmethod(_buildDirEntries)

   def _buildGeneralArgs(self):
      """
      Builds a list of general arguments to be passed to a mkisofs command.

      The various instance variables (C{applicationId}, etc.) are filled into
      the list of arguments if they are set.
      By default, we will build a RockRidge disc.  If you decide to change
      this, think hard about whether you know what you're doing.  This option
      is not well-tested.

      @return: List suitable for passing to L{util.executeCommand} as C{args}.
      """
      args = []
      if self.applicationId is not None:
         args.append("-A")
         args.append(self.applicationId)
      if self.biblioFile is not None:
         args.append("-biblio")
         args.append(self.biblioFile)
      if self.publisherId is not None:
         args.append("-publisher")
         args.append(self.publisherId)
      if self.preparerId is not None:
         args.append("-p")
         args.append(self.preparerId)
      if self.volumeId is not None:
         args.append("-V")
         args.append(self.volumeId)
      return args

   def _buildSizeArgs(self, entries):
      """
      Builds a list of arguments to be passed to a mkisofs command.

      The various instance variables (C{applicationId}, etc.) are filled into
      the list of arguments if they are set.  The command will be built to just
      return size output (a simple count of sectors via the C{-print-size} option),
      rather than an image file on disk.

      By default, we will build a RockRidge disc.  If you decide to change
      this, think hard about whether you know what you're doing.  This option
      is not well-tested.

      @param entries: Dictionary of image entries (i.e. self.entries)

      @return: List suitable for passing to L{util.executeCommand} as C{args}.
      """
      args = self._buildGeneralArgs()
      args.append("-print-size")
      args.append("-graft-points")
      if self.useRockRidge:
         args.append("-r")
      if self.device is not None and self.boundaries is not None:
         args.append("-C")
         args.append("%d,%d" % (self.boundaries[0], self.boundaries[1]))
         args.append("-M")
         args.append(self.device)
      args.extend(self._buildDirEntries(entries))
      return args

   def _buildWriteArgs(self, imagePath):
      """
      Builds a list of arguments to be passed to a mkisofs command.

      The various instance variables (C{applicationId}, etc.) are filled into
      the list of arguments if they are set.  The command will be built to write
      an image to disk.

      By default, we will build a RockRidge disc.  If you decide to change
      this, think hard about whether you know what you're doing.  This option
      is not well-tested.

      @param imagePath: Path to write image out as
      @type imagePath: String representing a path on disk

      @return: List suitable for passing to L{util.executeCommand} as C{args}.
      """
      args = self._buildGeneralArgs()
      args.append("-graft-points")
      if self.useRockRidge:
         args.append("-r")
      args.append("-o")
      args.append(imagePath)
      if self.device is not None and self.boundaries is not None:
         args.append("-C")
         args.append("%d,%d" % (self.boundaries[0], self.boundaries[1]))
         args.append("-M")
         args.append(self.device)
      args.extend(self._buildDirEntries(self.entries))
      return args

