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
# Purpose  : Provides package initialization
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# This file was created with a width of 132 characters, and NO tabs.

########################################################################
# Module documentation
########################################################################

"""
Implements secure remote and local backups to CD-R or CD-RW.

Cedar Backup is a Python package that supports secure backups of files
on local and remote hosts to CD-R or CD-RW media.  The package is
focused around weekly backups to a single disc, with the expectation
that the disc will be changed or overwritten at the beginning of each
week.  If your hardware is new enough, the script can write multisession
discs, allowing you to add to a disc in a daily fashion.  Directories
are backed up using GNU tar(1) and may be compressed using several
different methods.

@author Kenneth J. Pronovici <pronovic@ieee.org>
"""

########################################################################
# Package initialization
########################################################################

# Using 'from CedarBackup2 import *' will just import the modules listed
# in the __all__ variable.

__all__ = [ 'release', ]

