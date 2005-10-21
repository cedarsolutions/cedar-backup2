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
# Copyright (c) 2004-2005 Kenneth J. Pronovici.
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
# Purpose  : Provides general XML-related functionality.
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

########################################################################
# Module documentation
########################################################################

"""
Provides general XML-related functionality.

This module is one of the few pieces of code in the CedarBackup2 package that
requires functionality outside of the Python 2.3 standard library.   It
requires the PyXML package, mostly for the pretty-print functionality provided
there.

The PyXML XPath library is not very fast.  This is particularly noticable when
reading lists of things with the XPath C{[n]} syntax.  Because of this, we
completely avoid XPath, and the code below jumps through some
performance-improvement hoops that would normally not be required when using a
faster library.

@sort: readChildren, readFirstChild, readStringList, readString, readInteger,
       readBoolean, addContainerNode, addStringNode, addIntegerNode,
       addBooleanNode, TRUE_BOOLEAN_VALUES, FALSE_BOOLEAN_VALUES,
       VALID_BOOLEAN_VALUES

@var TRUE_BOOLEAN_VALUES: List of boolean values in XML representing C{True}.
@var FALSE_BOOLEAN_VALUES: List of boolean values in XML representing C{False}.
@var VALID_BOOLEAN_VALUES: List of valid boolean values in XML.

@author: Kenneth J. Pronovici <pronovic@ieee.org>
"""

########################################################################
# Imported modules
########################################################################

# System modules
import logging

# XML-related modules
from xml.dom.minidom import Node


########################################################################
# Module-wide constants and variables
########################################################################

logger = logging.getLogger("CedarBackup2.log.xml")

TRUE_BOOLEAN_VALUES   = [ "Y", "y", ]
FALSE_BOOLEAN_VALUES  = [ "N", "n", ]
VALID_BOOLEAN_VALUES  = TRUE_BOOLEAN_VALUES + FALSE_BOOLEAN_VALUES


########################################################################
# Public utility functions
########################################################################

##########################
# readChildren() function
##########################

def readChildren(parent, name):
   """
   Returns a list of nodes with a given name immediately beneath the
   parent.

   By "immediately beneath" the parent, we mean from among nodes that are
   direct children of the passed-in parent node.  

   Underneath, we use the Python C{getElementsByTagName} method, which is
   pretty cool, but which (surprisingly?) returns a list of all children
   with a given name below the parent, at any level.  We just prune that
   list to include only children whose C{parentNode} matches the passed-in
   parent.

   @param parent: Parent node to search beneath.
   @param name: Name of nodes to search for.

   @return: List of child nodes with correct parent, or an empty list if
   no matching nodes are found.
   """
   lst = []
   if parent is not None:
      result = parent.getElementsByTagName(name)
      for entry in result:
         if entry.parentNode is parent:
            lst.append(entry)
   return lst


############################
# readFirstChild() function
############################

def readFirstChild(parent, name):
   """
   Returns the first child with a given name immediately beneath the parent.

   By "immediately beneath" the parent, we mean from among nodes that are
   direct children of the passed-in parent node.  

   @param parent: Parent node to search beneath.
   @param name: Name of node to search for.

   @return: First properly-named child of parent, or C{None} if no matching nodes are found.
   """
   result = readChildren(parent, name)
   if result is None or result == []:
      return None
   return result[0]


############################
# readStringList() function
############################

def readStringList(parent, name):
   """
   Returns a list of the string contents associated with nodes with a given
   name immediately beneath the parent.

   By "immediately beneath" the parent, we mean from among nodes that are
   direct children of the passed-in parent node.  

   First, we find all of the nodes using L{readChildren}, and then we
   retrieve the "string contents" of each of those nodes.  The returned list
   has one entry per matching node.  We assume that string contents of a
   given node belong to the first C{TEXT_NODE} child of that node.  Nodes
   which have no C{TEXT_NODE} children are not represented in the returned
   list.

   @param parent: Parent node to search beneath.
   @param name: Name of node to search for.

   @return: List of strings as described above, or C{None} if no matching nodes are found.
   """
   lst = []
   result = readChildren(parent, name)
   for entry in result:
      if entry.hasChildNodes():
         for child in entry.childNodes:
            if child.nodeType == Node.TEXT_NODE:
               lst.append(child.nodeValue)
               break
   if lst == []:
      lst = None
   return lst


########################
# readString() function
########################

def readString(parent, name):
   """
   Returns string contents of the first child with a given name immediately
   beneath the parent.

   By "immediately beneath" the parent, we mean from among nodes that are
   direct children of the passed-in parent node.  We assume that string
   contents of a given node belong to the first C{TEXT_NODE} child of that
   node.

   @param parent: Parent node to search beneath.
   @param name: Name of node to search for.

   @return: String contents of node or C{None} if no matching nodes are found.
   """
   result = readStringList(parent, name)
   if result is None:
      return None
   return result[0]


#########################
# readInteger() function
#########################

def readInteger(parent, name):
   """
   Returns integer contents of the first child with a given name immediately
   beneath the parent.

   By "immediately beneath" the parent, we mean from among nodes that are
   direct children of the passed-in parent node.  

   @param parent: Parent node to search beneath.
   @param name: Name of node to search for.

   @return: Integer contents of node or C{None} if no matching nodes are found.
   @raise ValueError: If the string at the location can't be converted to an integer.
   """
   result = readString(parent, name)
   if result is None:
      return None
   else:
      return int(result)


#########################
# readBoolean() function
#########################

def readBoolean(parent, name):
   """
   Returns boolean contents of the first child with a given name immediately
   beneath the parent.

   By "immediately beneath" the parent, we mean from among nodes that are
   direct children of the passed-in parent node.  

   The string value of the node must be one of the values in L{VALID_BOOLEAN_VALUES}.

   @param parent: Parent node to search beneath.
   @param name: Name of node to search for.

   @return: Boolean contents of node or C{None} if no matching nodes are found.
   @raise ValueError: If the string at the location can't be converted to a boolean.
   """
   result = readString(parent, name)
   if result is None:
      return None
   else:
      if result in TRUE_BOOLEAN_VALUES:
         return True
      elif result in FALSE_BOOLEAN_VALUES:
         return False
      else:
         raise ValueError("Boolean values must be one of %s." % VALID_BOOLEAN_VALUES)


##############################
# addContainerNode() function
##############################

def addContainerNode(xmlDom, parentNode, nodeName):
   """
   Adds a container node as the next child of a parent node.

   @param xmlDom: DOM tree as from C{impl.createDocument()}.
   @param parentNode: Parent node to create child for.
   @param nodeName: Name of the new container node.

   @return: Reference to the newly-created node.
   """
   containerNode = xmlDom.createElement(nodeName)
   parentNode.appendChild(containerNode)
   return containerNode


###########################
# addStringNode() function
###########################

def addStringNode(xmlDom, parentNode, nodeName, nodeValue):
   """
   Adds a text node as the next child of a parent, to contain a string.

   If the C{nodeValue} is None, then the node will be created, but will be
   empty (i.e. will contain no text node child).

   @param xmlDom: DOM tree as from C{impl.createDocument()}.
   @param parentNode: Parent node to create child for.
   @param nodeName: Name of the new container node.
   @param nodeValue: The value to put into the node.

   @return: Reference to the newly-created node.
   """
   containerNode = addContainerNode(xmlDom, parentNode, nodeName)
   if nodeValue is not None:
      textNode = xmlDom.createTextNode(nodeValue)
      containerNode.appendChild(textNode)
   return containerNode


############################
# addIntegerNode() function
############################

def addIntegerNode(xmlDom, parentNode, nodeName, nodeValue):
   """
   Adds a text node as the next child of a parent, to contain an integer.

   If the C{nodeValue} is None, then the node will be created, but will be
   empty (i.e. will contain no text node child).

   The integer will be converted to a string using "%d".  The result will be
   added to the document via L{addStringNode}.

   @param xmlDom: DOM tree as from C{impl.createDocument()}.
   @param parentNode: Parent node to create child for.
   @param nodeName: Name of the new container node.
   @param nodeValue: The value to put into the node.

   @return: Reference to the newly-created node.
   """
   if nodeValue is None:
      return addStringNode(xmlDom, parentNode, nodeName, None)
   else:
      return addStringNode(xmlDom, parentNode, nodeName, "%d" % nodeValue)


############################
# addBooleanNode() function
############################

def addBooleanNode(xmlDom, parentNode, nodeName, nodeValue):
   """
   Adds a text node as the next child of a parent, to contain a boolean.

   If the C{nodeValue} is None, then the node will be created, but will be
   empty (i.e. will contain no text node child).

   Boolean C{True}, or anything else interpreted as C{True} by Python, will
   be converted to a string "Y".  Anything else will be converted to a
   string "N".  The result is added to the document via L{addStringNode}.

   @param xmlDom: DOM tree as from C{impl.createDocument()}.
   @param parentNode: Parent node to create child for.
   @param nodeName: Name of the new container node.
   @param nodeValue: The value to put into the node.

   @return: Reference to the newly-created node.
   """
   if nodeValue is None:
      return addStringNode(xmlDom, parentNode, nodeName, None)
   else:
      if nodeValue:
         return addStringNode(xmlDom, parentNode, nodeName, "Y")
      else:
         return addStringNode(xmlDom, parentNode, nodeName, "N")

