# vim: set ft=make:
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
#              C E D A R
#          S O L U T I O N S       "Software done right."
#           S O F T W A R E
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# Author   : Kenneth J. Pronovici <pronovic@ieee.org>
# Language : Make
# Project  : Cedar Backup, release 2
# Revision : $Id$
# Purpose  : Developer "private" makefile for CedarBackup2 package
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# This file was created with a width of 132 characters using 8-space tabs.

########
# Notes
########

# This file is the one that I will use for my personal development
# effort.  It has a number of rules in it that no one else will use,
# and it will not be included in any of the public distributions of
# CedarBackup2.


########################
# Programs and commands
########################

CD                = cd
CP                = cp
EPYDOC            = epydoc
MKDIR             = mkdir
PYCHECKER         = PYTHONVER=2.3 pychecker
PYTHON            = python2.3
RM                = rm
SETUP             = $(PYTHON) ./setup.py
SUDO              = sudo
TAR               = tar
VALIDATE          = util/validate
VERSION           = `cat CedarBackup2/release.py | grep '^VERSION' | awk -F\" '{print $$2}'`
URL               = `cat CedarBackup2/release.py | grep URL | awk -F\" '{print $$2}'`


############
# Locations
############

DOC_DIR           = ./doc
DIST_DIR          = ./build
MANUAL_SRC        = ./manual
SDIST_DIR         = $(DIST_DIR)/sdist
INTERFACE_DIR     = $(DOC_DIR)/interface
INTERFACE_TEMPDIR = $(DOC_DIR)/interface/tmp
MANUAL_DIR        = $(DOC_DIR)/manual


###################
# High-level rules
###################

all: 

clean: docclean distribclean 
	-@find . -name "*.pyc" | xargs rm -f

# This uses the "full" argument to get all tests
test:
	@$(SUDO) -v
	@$(PYTHON) util/test.py full

# This leaves off "full" and gets on the tests most end-users would run
usertest:
	@$(PYTHON) util/test.py


##################################
# Stylistic and function checking
##################################
# Pycheck catches a lot of different things.  It's kind of like lint for
# Python.  A few warnings are expected.  The main check rule only checks the
# implementation in CedarBackup2/.  The other rule checks all of the python
# code in the system.

check: 
	-@$(PYCHECKER) --config pycheckrc CedarBackup2/*.py CedarBackup2/extend/*.py

allcheck: 
	-@$(PYCHECKER) --config pycheckrc CedarBackup2/*.py CedarBackup2/extend/*.py test/*.py util/*.py


################
# Documentation
################

# Aliases, since I can't remember what to type. :)
docs: doc
docsclean: docclean
epydoc: interface-html
interface: interface-doc
book: manual

doc: interface-doc manual-doc

interface-doc: interface-html 

interface-html: $(INTERFACE_DIR)
	@$(EPYDOC) --name "CedarBackup2" --target $(INTERFACE_DIR) --url $(URL) CedarBackup2/

manual-doc: $(MANUAL_DIR)
	@$(CD) $(MANUAL_SRC) && $(MAKE) install

# For convenience, this rule builds chunk only
manual: 
	-@$(CD) $(MANUAL_SRC) && $(MAKE) manual-chunk && $(MAKE) install-manual-chunk

validate: 
	-@$(VALIDATE) $(MANUAL_SRC)/src/book.xml

docclean:
	-@$(CD) $(MANUAL_SRC) && $(MAKE) clean
	-@$(RM) -rf $(INTERFACE_DIR)
	-@$(RM) -rf $(INTERFACE_TEMPDIR)
	-@$(RM) -rf $(MANUAL_DIR)

$(MANUAL_DIR):
	@$(MKDIR) -p $(MANUAL_DIR)

$(INTERFACE_DIR):
	@$(MKDIR) -p $(INTERFACE_DIR)

$(INTERFACE_TEMPDIR):
	@$(MKDIR) -p $(INTERFACE_TEMPDIR)


################
# Distributions
################
# The rules in this section build a Python source distribution, and then
# also that same source distribution named appropriately for Debian (the
# Debian packages are maintained via cvs-buildpackage as usual).  This
# keeps cedar-backup2 from being a Debian native package, and also making
# it easier for someone to do an NMU if/when this ends up in Debian proper.

distrib: doc sdist debdist docdist

distribclean: sdistclean debdistclean
	-@$(RM) -f MANIFEST 
	-@$(RM) -rf $(DIST_DIR)

sdist: $(SDIST_DIR)
	@$(SETUP) sdist --dist-dir $(SDIST_DIR)
	@$(CP) $(SDIST_DIR)/CedarBackup2-$(VERSION).tar.gz ../

$(SDIST_DIR):
	@$(MKDIR) -p $(SDIST_DIR)

sdistclean: 
	@$(RM) -f $(SDIST_DIR)/CedarBackup2-$(VERSION).tar.gz

debdist: sdist
	@$(CP) $(SDIST_DIR)/CedarBackup2-$(VERSION).tar.gz $(SDIST_DIR)/cedar-backup2_$(VERSION).orig.tar.gz
	@$(CP) $(SDIST_DIR)/cedar-backup2_$(VERSION).orig.tar.gz ../

debdistclean: 
	@$(RM) -f $(SDIST_DIR)/cedar-backup2_$(VERSION).orig.tar.gz 

docdist: 
	@$(TAR) -zcvf ../htmldocs.tar.gz doc/manual doc/interface

.PHONY: all clean unittest test check pychecker pycheck doc docclean interface-doc manual-doc distrib sdist sdistclean debdist debdistclean

