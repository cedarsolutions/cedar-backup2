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
from CedarBackup2.util import executeCommand, convertSize, UNIT_BYTES, UNIT_SECTORS
from CedarBackup2.writer import validateScsiId


########################################################################
# Module-wide constants and variables
########################################################################

logger = logging.getLogger("CedarBackup2.image")
MKISOFS_CMD          = [ "mkisofs", ]


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
      operating systems and platforms.  A "sensible subset" of the C{mkisofs}
      functionality is made available through the public interface, allowing
      callers to set a variety of basic options such as publisher id,
      application id, etc. as well as specify exactly which files and
      directories they want included in their image.

      By default, the image is created using the Rock Ridge protocol (using the
      C{-r} option to C{mkisofs}) because Rock Ridge discs are generally more
      useful on UN*X filesystems than standard ISO 9660 images.  However,
      callers can fall back to the default C{mkisofs} functionality by setting
      the C{useRockRidge} instance variable to C{False}.  Note, however, that
      this option is not well-tested.

      The class also includes some functionality that attempts to "prune" a
      defined image to fit in a certain amount of free space.  This should help
      callers who want to write a disc, even if they can't fit everything they
      want on it.  

   Where Files and Directories are Placed in the Image
   ===================================================

      Although this class is implemented in terms of the C{mkisofs} program,
      its "image contents" semantics are slightly different than the original
      C{mkisofs} semantics.  The difference is that files and directories are
      added to the image with some additional information about their source
      directory kept intact.  I feel that this behavior (described in more
      detail below) is more consistent than the original C{mkisofs} behavior.
      However, to be fair, it is not quite as flexible.

      As an example, suppose you add the file C{/etc/profile} to your image and
      you do not configure a graft point.  The file C{/profile} will be created
      in the image.  The behavior for directories is similar.  For instance,
      suppose that you add C{/etc/X11} to the image and do not configure a
      graft point.  In this case, the directory C{/X11} will be created in the
      image, even if the original C{/etc/X11} directory is empty.  I{This
      behavior differs from the standard C{mkisofs} behavior!}

      If a graft point is configured, it will be used to modify the point at
      which a file or directory is added into an image.  Using the examples
      from above, let's assume you set a graft point of C{base} when adding
      C{/etc/profile} and C{/etc/X11} to your image.  In this case, the file
      C{/base/profile} and the directory C{/base/X11} would be added to the
      image.  Again, this behavior differs somewhat from the original
      C{mkisofs} behavior.  It is arguably more "consistent", but is probably
      less flexible in a general sense.

   @sort: __init__, addEntry, getEstimatedSize, _getEstimatedSize, writeImage, pruneImage
          _pruneImage, _calculateSizes, _buildEntries, _expandEntries, _buildDirEntries
          _buildGeneralArgs, _buildSizeArgs, _buildWriteArgs, 
          device, boundaries, graftPoint, useRockRidge, applicationId, 
          biblioFile, publisherId, preparerId, volumeId
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
      will not be written.  The boundaries tuple is in terms of ISO sectors, as
      built by an image writer class and returned in a L{writer.MediaCapacity}
      object.

      @param device: Name of the device that the image will be written to
      @type device: Either be a filesystem path or a SCSI address

      @param boundaries: Session boundaries as required by C{mkisofs}
      @type boundaries: Tuple C{(last_sess_start,next_sess_start)} as returned from C{cdrecord -msinfo}

      @param graftPoint: Default graft point for this page.
      @type graftPoint: String representing a graft point path (see L{addEntry}).
      """
      self._device = None
      self._boundaries = None
      self._graftPoint = None
      self._useRockRidge = True
      self._applicationId = None
      self._biblioFile = None
      self._publisherId = None
      self._preparerId = None
      self._volumeId = None
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


   #############
   # Properties
   #############

   def _setDevice(self, value):
      """
      Property target used to set the device value.
      If not C{None}, the value can be either an absolute path or a SCSI id.
      @raise ValueError: If the value is not valid
      """
      try:
         if value is None:
            self._device = None
         else:
            if os.path.isabs(value):
               self._device = value
            else:
               self._device = validateScsiId(value)
      except ValueError:
         raise ValueError("Device must either be an absolute path or a valid SCSI id.")

   def _getDevice(self):
      """
      Property target used to get the device value.
      """
      return self._device

   def _setBoundaries(self, value):
      """
      Property target used to set the boundaries tuple.
      If not C{None}, the value must be a tuple of two integers.
      @raise ValueError: If the tuple values are not integers.
      @raise IndexError: If the tuple does not contain enough elements.
      """
      if value is None:
         self._boundaries = None
      else:
         self._boundaries = (int(value[0]), int(value[1]))

   def _getBoundaries(self):
      """
      Property target used to get the boundaries value.
      """
      return self._boundaries

   def _setGraftPoint(self, value):
      """
      Property target used to set the graft point.
      The value must be a non-empty string if it is not C{None}.
      @raise ValueError: If the value is an empty string.
      """
      if value is not None:
         if len(value) < 1:
            raise ValueError("The graft point must be a non-empty string.")
      self._graftPoint = value

   def _getGraftPoint(self):
      """
      Property target used to get the graft point.
      """
      return self._graftPoint

   def _setUseRockRidge(self, value):
      """
      Property target used to set the use RockRidge flag.
      No validations, but we normalize the value to C{True} or C{False}.
      """
      if value:
         self._useRockRidge = True
      else:
         self._useRockRidge = False

   def _getUseRockRidge(self):
      """
      Property target used to get the use RockRidge flag.
      """
      return self._useRockRidge

   def _setApplicationId(self, value):
      """
      Property target used to set the application id.
      The value must be a non-empty string if it is not C{None}.
      @raise ValueError: If the value is an empty string.
      """
      if value is not None:
         if len(value) < 1:
            raise ValueError("The application id must be a non-empty string.")
      self._applicationId = value

   def _getApplicationId(self):
      """
      Property target used to get the application id.
      """
      return self._applicationId

   def _setBiblioFile(self, value):
      """
      Property target used to set the biblio file.
      The value must be a non-empty string if it is not C{None}.
      @raise ValueError: If the value is an empty string.
      """
      if value is not None:
         if len(value) < 1:
            raise ValueError("The biblio file must be a non-empty string.")
      self._biblioFile = value

   def _getBiblioFile(self):
      """
      Property target used to get the biblio file.
      """
      return self._biblioFile

   def _setPublisherId(self, value):
      """
      Property target used to set the publisher id.
      The value must be a non-empty string if it is not C{None}.
      @raise ValueError: If the value is an empty string.
      """
      if value is not None:
         if len(value) < 1:
            raise ValueError("The publisher id must be a non-empty string.")
      self._publisherId = value

   def _getPublisherId(self):
      """
      Property target used to get the publisher id.
      """
      return self._publisherId

   def _setPreparerId(self, value):
      """
      Property target used to set the preparer id.
      The value must be a non-empty string if it is not C{None}.
      @raise ValueError: If the value is an empty string.
      """
      if value is not None:
         if len(value) < 1:
            raise ValueError("The preparer id must be a non-empty string.")
      self._preparerId = value

   def _getPreparerId(self):
      """
      Property target used to get the preparer id.
      """
      return self._preparerId

   def _setVolumeId(self, value):
      """
      Property target used to set the volume id.
      The value must be a non-empty string if it is not C{None}.
      @raise ValueError: If the value is an empty string.
      """
      if value is not None:
         if len(value) < 1:
            raise ValueError("The volume id must be a non-empty string.")
      self._volumeId = value

   def _getVolumeId(self):
      """
      Property target used to get the volume id.
      """
      return self._volumeId

   device = property(_getDevice, _setDevice, None, "Device that image will be written to (device path or SCSI id).")
   boundaries = property(_getBoundaries, _setBoundaries, None, "Session boundaries as required by C{mkisofs}.")
   graftPoint = property(_getGraftPoint, _setGraftPoint, None, "Default image-wide graft point (see L{addEntry} for details).")
   useRockRidge = property(_getUseRockRidge, _setUseRockRidge, None, "Indicates whether to use RockRidge (default is C{True}).")
   applicationId = property(_getApplicationId, _setApplicationId, None, "Optionally specifies the ISO header application id value.")
   biblioFile = property(_getBiblioFile, _setBiblioFile, None, "Optionally specifies the ISO bibliographic file name.")
   publisherId = property(_getPublisherId, _setPublisherId, None, "Optionally specifies the ISO header publisher id value.")
   preparerId = property(_getPreparerId, _setPreparerId, None, "Optionally specifies the ISO header preparer id value.")
   volumeId = property(_getVolumeId, _setVolumeId, None, "Optionally specifies the ISO header volume id value.")


   #########################
   # General public methods
   #########################

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
      instance variable.  If neither the method parameter or object-wide value
      is set, the path will be written at the image root.  The graft point
      behavior is determined by the value which is in effect I{at the time this
      method is called}, so you I{must} set the object-wide value before
      calling this method for the first time, or your image may not be
      consistent.  

      @note: You I{cannot} use the local C{graftPoint} parameter to "turn off"
      an object-wide instance variable by setting it to C{None}.  Python's
      default argument functionality buys us a lot, but it can't make this
      method psychic. :)

      @param path: File or directory to be added to the image
      @type path: String representing a path on disk

      @param graftPoint: Graft point to be used when adding this entry
      @type graftPoint: String representing a graft point path, as described above

      @raise ValueError: If path is not a file or directory, or does not exist.
      @raise ValueError: If the path has already been added, and override is not set.
      """
      if not override:
         if path in self.entries.keys():
            raise ValueError("Path has already been added to the image.")
      if os.path.islink(path):
         raise ValueError("Path must not be a link.") 
      if os.path.isdir(path):
         if graftPoint is not None:
            self.entries[path] = os.path.join(graftPoint, os.path.basename(path))
         elif self.graftPoint is not None: 
            self.entries[path] = os.path.join(self.graftPoint, os.path.basename(path))
         else:
            self.entries[path] = os.path.basename(path)
      elif os.path.isfile(path):
         if graftPoint is not None:
            self.entries[path] = graftPoint
         elif self.graftPoint is not None:
            self.entries[path] = self.graftPoint
         else:
            self.entries[path] = None
      else:
         raise ValueError("Path must be a file or a directory.")

   def getEstimatedSize(self):
      """
      Returns the estimated size (in bytes) of the ISO image.

      This is implemented via the C{-print-size} option to C{mkisofs}, so it
      might take a bit of time to execute.  However, the result is as accurate
      as we can get, since it takes into account all of the ISO overhead, the
      true cost of directories in the structure, etc, etc.

      @return: Estimated size of the image, in bytes.

      @raise IOError: If there is a problem calling C{mkisofs}.
      @raise ValueError: If there are no filesystem entries in the image
      """
      if len(self.entries.keys()) == 0:
         raise ValueError("Image does not contain any entries.")
      return self._getEstimatedSize(self.entries)

   def _getEstimatedSize(self, entries):
      """
      Returns the estimated size (in bytes) for the passed-in entries dictionary.
      @return: Estimated size of the image, in bytes.
      @raise IOError: If there is a problem calling C{mkisofs}.
      """
      args = self._buildSizeArgs(entries)
      (result, output) = executeCommand(MKISOFS_CMD, args, returnOutput=True, ignoreStderr=True)
      if result != 0:
         raise IOError("Error (%d) executing mkisofs command to estimate size." % result)
      if len(output) != 1:
         raise IOError("Unable to parse mkisofs output.")
      try:
         sectors = float(output[0])
         size = convertSize(sectors, UNIT_SECTORS, UNIT_BYTES)
         return size
      except: 
         raise IOError("Unable to parse mkisofs output.")

   def writeImage(self, imagePath):
      """
      Writes this image to disk using the image path.

      @param imagePath: Path to write image out as
      @type imagePath: String representing a path on disk

      @raise IOError: If there is an error writing the image to disk.
      @raise ValueError: If there are no filesystem entries in the image
      """
      if len(self.entries.keys()) == 0:
         raise ValueError("Image does not contain any entries.")
      args = self._buildWriteArgs(self.entries, imagePath)
      (result, output) = executeCommand(MKISOFS_CMD, args, returnOutput=False)
      if result != 0:
         raise IOError("Error (%d) executing mkisofs command to build image." % result)


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
      list of composite files internally.  

      @note: This process is destructive.  Once you prune an image, you can't
      get it back in its original form without rebuilding it from scratch.
      However, the object will be unchanged unless this method call returns
      successfully.

      @param capacity: Capacity to prune to
      @type capacity: Integer capacity, in bytes

      @return: Estimated size of the image, in bytes, as from L{getEstimatedSize}.

      @raise IOError: If we can't prune to fit the image into the capacity.
      @raise ValueError: If there are no filesystem entries in the image
      """
      if len(self.entries.keys()) == 0:
         raise ValueError("Image does not contain any entries.")
      entries = self._pruneImage(capacity)
      self.entries = entries
      return self.getEstimatedSize()

   def _pruneImage(self, capacity):
      """
      Prunes the image to fit a certain capacity, in bytes.

      This is an internal method.  It mainly exists so we can adequately
      document the pruning procedure without burdening external callers with
      details about exactly how it's done.

      To be successful, we have to build an entries dictionary such that the
      resulting ISO image uses C{capacity} or fewer bytes.  We determine a
      target overall file size, use a knapsack algorithm to hit that target
      size, and then check whether the resulting image would fit in our
      capacity.  If it would fit, then we build a new entries dictionary and
      return it.  Otherwise we try a few more times, giving up after four
      attempts.

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
      certainly be small enough).

      @param capacity: Capacity to prune to
      @type capacity: Integer capacity, in bytes

      @return: Pruned entries dictionary safe to apply to self.entries
      @raise IOError: If we can't prune to fit the image into the capacity.
      """
      expanded = self._expandEntries(self.entries) 
      (sizeMap, fileSize) = IsoImage._calculateSizes(expanded)
      estimatedSize = self._getEstimatedSize(self.entries)
      overhead = estimatedSize - fileSize
      if overhead > capacity:
         raise IOError("Required overhead (%.0f) exceeds available capacity (%.0f)." % (overhead, float(capacity)))
      for factor in [ 1.0, 0.98, 0.95, 0.90 ]:
         targetSize = (capacity - overhead) * factor
         (items, used) = worstFit(sizeMap, targetSize)
         if len(items) == 0 or used == 0:
            raise IOError("Unable to fit any entries into available capacity.")
         prunedEntries = IsoImage._buildEntries(expanded, items)
         estimatedSize = self._getEstimatedSize(prunedEntries)
         if(estimatedSize <= capacity):
            return prunedEntries
      raise IOError("Unable to prune image to fit the capacity after four tries.")

   def _calculateSizes(entries):
      """
      Calculates sizes for files in an entries dictionary.

      The resulting map contains true sizes for each file in the list of
      entries, and the total is the sum of all of these sizes.  The map also
      contains zero size for each link and directory in the original list of
      entries.  This way, the process of calculating sizes doesn't lose any
      information (it's up to the caller to pass in an entries list that
      contains only things they care about).  In any case, an entry which
      doesn't exist on disk is completely ignored.

      @param entries: An entries map (expanded via L{_expandEntries})

      @return: Tuple (map, total) where map is suitable for passing to a knapsack function.
      """
      table = { }
      total = 0
      for entry in entries:
         if os.path.exists(entry):
            if os.path.isfile(entry) and not os.path.islink(entry):
               size = float(os.stat(entry).st_size)
               table[entry] = (entry, size)
               total += size
            else:
               table[entry] = (entry, 0)
      return (table, total)
   _calculateSizes = staticmethod(_calculateSizes)

   def _buildEntries(entries, items):
      """
      Builds an entries dictionary.
      
      The result is basically the intersection of the passed-in entries
      dictionary with the keys that are in the list.  The passed-in entries
      dictionary will not be modified.  The items list is assumed to be a
      subset of the list of keys in the entries dictionary and you'll get a
      C{KeyError} if that's not true.

      @param entries: Entries dictionary to work from
      @param items: List of items to be used as keys into the dictionary

      @return: New entries dictionary that contains only the keys in the list
      @raise KeyError: If the items doesn't match up properly with entries.
      """
      newEntries = { }
      for i in items:
         newEntries[i] = entries[i]
      return newEntries
   _buildEntries = staticmethod(_buildEntries)

   def _expandEntries(entries):
      """
      Expands entries in an image to include only files.

      Most of the time, we will add only directories to an image, with an
      occassional file here and there.  However, we need to get at the files in
      the each directory in order to prune to fit a particular capacity.  So,
      this function goes through the the various entries and expands every
      directory it finds.  The result is an "equivalent" entries dictionary
      that verbosely includes every file and link that would have been included
      originally, along with its associated graft point (if any).  

      There is one trick: we can't associate the same graft point with a file
      as with its parent directory, since this would lose information (such as
      the directory the file was in, especially if it was deeply nested).  We
      sometimes need to tack the name of a directory onto the end of the graft
      point so the result will be equivalent.

      Here's an example: if directory C{/opt/ken/dir1} had graft point
      C{/base}, then the directory would become C{/base/dir1} in the image and
      individual files might be C{/base/dir1/file1}, C{/base/dir1/file2}, etc.
      Because of our specialized graft-point handling for directories, this
      works in the simple case.  However, once you work your way into nested
      directories, it breaks down.  In order to get C{/base/dir1/dir2/file1},
      we need to recognize that the prefix is really C{dir2} and tack that onto
      the graft point.  

      Besides this, there are a few other hoops we have to jump through.  In
      particular, we need to include soft links in the image, but
      non-recursively (i.e. we don't want to traverse soft links to
      directories).  Also, while we don't normally want bare directories in the
      image (because the files in those directories will already have been
      added) we need to be careful not to lose empty directories, which will
      get pruned by a simplistic algorithm simply because they don't contain
      any indexed files.  The bare directories are added with a graft point
      including their own name, to force C{mkisofs} to create them.

      @note: Behavior of this function is probably UN*X-specific.

      @return: Expanded entries dictionary.
      """
      newEntries = { }
      for entry in entries:
         if os.path.isfile(entry):
            newEntries[entry] = entries[entry]
         elif os.path.isdir(entry):
            fsList = FilesystemList()
            fsList.addDirContents(entry)
            for item in fsList:
               if os.path.islink(item) or os.path.isfile(item):
                  if entries[entry] is None:
                     newEntries[item] = None
                  else:
                     subdir = os.path.dirname(item.replace(entry, "", 1))
                     graft = os.path.join(entries[entry].strip(os.sep), subdir.strip(os.sep))
                     newEntries[item] = graft.strip(os.sep)
               elif os.path.os.path.isdir(item) and os.listdir(item) == []:
                  if entries[entry] is None:
                     newEntries[item] = os.path.basename(item)
                  else:
                     subdir = os.path.dirname(item.replace(entry, "", 1))
                     graft = os.path.join(entries[entry].strip(os.sep), subdir.strip(os.sep), os.path.basename(item))
                     newEntries[item] = graft.strip(os.sep)
      return newEntries
   _expandEntries = staticmethod(_expandEntries)


   #########################################
   # Methods used to build mkisofs commands
   #########################################

   def _buildDirEntries(entries):
      """
      Uses an entries dictionary to build a list of directory locations for use
      by C{mkisofs}.

      We build a list of entries that can be passed to C{mkisofs}.  Each entry is
      either raw (if no graft point was configured) or in graft-point form as
      described above (if a graft point was configured).  The dictionary keys
      are the path names, and the values are the graft points, if any.

      @param entries: Dictionary of image entries (i.e. self.entries)

      @return: List of directory locations for use by C{mkisofs}
      """
      dirEntries = []
      for key in entries.keys():
         if entries[key] is None:
            dirEntries.append(key)
         else:
            dirEntries.append("%s/=%s" % (entries[key].strip(os.sep), key))
      return dirEntries
   _buildDirEntries = staticmethod(_buildDirEntries)

   def _buildGeneralArgs(self):
      """
      Builds a list of general arguments to be passed to a C{mkisofs} command.

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
      Builds a list of arguments to be passed to a C{mkisofs} command.

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

   def _buildWriteArgs(self, entries, imagePath):
      """
      Builds a list of arguments to be passed to a C{mkisofs} command.

      The various instance variables (C{applicationId}, etc.) are filled into
      the list of arguments if they are set.  The command will be built to write
      an image to disk.

      By default, we will build a RockRidge disc.  If you decide to change
      this, think hard about whether you know what you're doing.  This option
      is not well-tested.

      @param entries: Dictionary of image entries (i.e. self.entries)

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
      args.extend(self._buildDirEntries(entries))
      return args

