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
# Author   : Kenneth J. Pronovici <pronovic@ieee.org>
# Language : Python (>= 2.3)
# Project  : Cedar Backup, release 2
# Revision : $Id$
# Purpose  : Python distutils setup script
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

########################################################################
# Imported modules
########################################################################

from distutils.core import setup
from CedarBackup2.release import AUTHOR, EMAIL, VERSION, COPYRIGHT, URL


########################################################################
# Setup configuration
########################################################################


LONG_DESCRIPTION = """
Cedar Backup is a Python package that supports secure backups of files
on local and remote hosts to CD-R or CD-RW media.  The package is
focused around weekly backups to a single disc, with the expectation
that the disc will be changed or overwritten at the beginning of each
week.  If your hardware is new enough, the script can write multisession
discs, allowing you to add to a disc in a daily fashion.   Directories
are backed up using tar and may be compressed using gzip or bzip2.
"""

setup (
   name             = 'CedarBackup2',
   version          = VERSION,
   description      = 'Implements secure remote and local backups to CD-R or CD-RW.',
   long_description = LONG_DESCRIPTION,
   keywords         = ('secure', 'local', 'remote', 'backup', 'scp', 'CD-R'), 
   author           = AUTHOR,
   author_email     = EMAIL,
   url              = URL,
   license          = "Copyright (c) %s %s.  Licensed under the GNU GPL." % (COPYRIGHT, AUTHOR),
   platforms        = ('Any',),
   packages         = ['CedarBackup2',],
   scripts          = ['cback',], 
)

