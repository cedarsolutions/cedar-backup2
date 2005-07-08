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
Implements local and remote backups to CD-R/CD-RW media.

Cedar Backup is a Python package that supports backups of files on local and
remote hosts to CD-R or CD-RW media over a secure network connection.  Cedar
Backup also includes extensions that understand how to back up MySQL databases
and Subversion repositories, and it can be easily extended to support other
data sources, as well.

The package is focused around weekly backups to a single disc, with the
expectation that the disc will be changed or overwritten at the beginning of
each week.  If your hardware is new enough, Cedar Backup can write multisession
discs, allowing you to add to a disc in a daily fashion.  Directories are
backed up using tar and may be compressed using gzip or bzip2.

@author: Kenneth J. Pronovici <pronovic@ieee.org>
"""


########################################################################
# Package initialization
########################################################################

# Using 'from CedarBackup2 import *' will just import the modules listed
# in the __all__ variable.

__all__ = [ 'release', 'cli', 'actions', 'util', 'knapsack', 
            'filesystem', 'peer', 'image', 'writer', 'config', 
            'extend', ] 

