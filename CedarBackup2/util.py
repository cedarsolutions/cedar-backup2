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
# Purpose  : Provides general-purpose utilities.
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# This file was created with a width of 132 characters, and NO tabs.

########################################################################
# Module documentation
########################################################################

"""
Provides general-purpose utilities. 
@author: Kenneth J. Pronovici <pronovic@ieee.org>
"""


########################################################################
# Imported modules
########################################################################

import popen2
import logging
import pwd
import grp


########################################################################
# Module-wide constants and variables
########################################################################

logger = logging.getLogger("CedarBackup2.util")


########################################################################
# Public functions
########################################################################

#######################
# getUidGid() function
#######################

def getUidGid(user, group):
   """
   Get the uid/gid associated with a user/group pair

   @param user: User name
   @type user: User name as a string

   @param group: Group name
   @type group: Group name as a string

   @return Tuple (uid, gid) matching passed-in user and group.
   @raise ValueError: If the ownership user/group values are invalid
   """
   try:
      uid = pwd.getpwnam(user)[2]
      gid = grp.getgrnam(group)[2]
      logger.debug("Translated user/group %s/%s into uid/gid %d/%d." % (user, group, uid, gid))
      return (uid, gid)
   except Exception, e:
      logger.debug("Error looking up uid and gid for user/group %s/%s: %s" % (user, group, e))
      raise ValueError("Unable to lookup up uid and gid for passed in user/group.")


############################
# executeCommand() function
############################

def executeCommand(command, args, returnOutput=False):
   """
   Executes a shell command, hopefully in a safe way (UNIX-specific).

   This function exists to replace direct calls to os.popen() in the Cedar
   Backup code.  It's not safe to call a function such as os.popen() with
   untrusted arguments, since that can cause problems if the string contains
   non-safe variables or other constructs (imagine that the argument is
   $WHATEVER, but $WHATEVER contains something like "; rm -fR ~/; echo" in the
   current environment).

   It's safer to use popen4 (or popen2 or popen3) and pass a list rather than a
   string for the first argument.  When called this way, popen4 will use the
   list's first item as the command and the remainder of the list's items as
   arguments to that command.

   Under the normal case, the function will return a tuple of (status, None)
   where the status is the wait-encoded return status of the call per the
   Popen4 documentation.  If returnOutput is passed in as true, the function
   will return a tuple of (status, output) where output is a list of strings,
   one entry per line in the intermingled combination of stdout and stderr from
   the command.  Output is always logged to the logger.info() target, regardless
   of whether it's returned.

   @note: I know that it's a bit confusing that the command and the arguments
   are both lists.  I could have just required the caller to pass in one big
   list.  However, I think it makes some sense to keep the command (the
   constant part of what we're executing, i.e. "scp -B") separate from its
   arguments, even if they both end up looking kind of similar.

   @note: You cannot redirect output (i.e. 2>&1, 2>/dev/null, etc.) using this
   function.  The redirection string would be passed to the command just like
   any other argument.

   @param command: Shell command to execute
   @type command: List of individual arguments that make up the command

   @param args: List of arguments to the command
   @type args: List of additional arguments to the command

   @param returnOutput: Indicates whether to return the output of the command
   @type returnOutput: Boolean True or False

   @return Tuple of (result, output) as described above.
   """
   logger.debug("Executing command [%s] with args %s." % (command, args))
   output = []
   fields = command[:]        # make sure to copy it so we don't destroy it
   fields.extend(args)
   pipe = popen2.Popen4(fields)
   pipe.tochild.close()       # we'll never write to it, and this way we don't confuse anything.
   while True:
      line = pipe.fromchild.readline()
      if not line: break
      if returnOutput: output.append(line)
      logger.info(line[:-1])  # this way the log will (hopefully) get updated in realtime
   if returnOutput:
      return (pipe.wait(), output)
   else:
      return (pipe.wait(), None)

