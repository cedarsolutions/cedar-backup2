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
# Purpose  : Provides package initialization
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

########################################################################
# Module documentation
########################################################################

"""
Implements local and remote backups to CD or DVD media.

Cedar Backup is a software package designed to manage system backups for a pool
of local and remote machines.  Cedar Backup understands how to back up
filesystem data as well as MySQL and PostgreSQL databases and Subversion
repositories.  It can also be easily extended to support other kinds of data
sources.

Cedar Backup is focused around weekly backups to a single CD or DVD disc, with
the expectation that the disc will be changed or overwritten at the beginning
of each week.  If your hardware is new enough, Cedar Backup can write
multisession discs, allowing you to add incremental data to a disc on a daily
basis.

Besides offering command-line utilities to manage the backup process, Cedar
Backup provides a well-organized library of backup-related functionality,
written in the Python programming language.

@author: Kenneth J. Pronovici <pronovic@ieee.org>
"""


########################################################################
# Package initialization
########################################################################

# Using 'from CedarBackup2 import *' will just import the modules listed
# in the __all__ variable.

__all__ = [ 'actions', 'cli', 'config', 'extend', 'filesystem', 'knapsack', 
            'peer', 'release', 'tools', 'util', 'writers', ]
