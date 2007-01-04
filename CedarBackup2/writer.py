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
# Purpose  : Provides interface backwards compatibility.
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

########################################################################
# Module documentation
########################################################################

"""
Provides interface backwards compatibility.

In Cedar Backup 2.10.0, a refactoring effort took place while adding code to
support DVD hardware.  Since the ISO image functionality (image.py) was
more-or-less directly tied to the CD writer implementation (writer.py), that
functionality was consolidated into cdwriter.py.  (A few utilities were placed
into util.py instead).  This mostly-empty file remains to preserve the Cedar
Backup 2 library interface.

@deprecated: This functionality has been moved to the cdwriter and util modules.

@author: Kenneth J. Pronovici <pronovic@ieee.org>
"""

########################################################################
# Imported modules
########################################################################

from CedarBackup2.util import validateScsiId, validateDriveSpeed
from CedarBackup2.cdwriter import MediaDefinition, MediaCapacity, CdWriter
from CedarBackup2.cdwriter import MEDIA_CDRW_74, MEDIA_CDR_74, MEDIA_CDRW_80, MEDIA_CDR_80

