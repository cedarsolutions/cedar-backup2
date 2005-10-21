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
# Portions Copyright (c) 2000 Fourthought Inc, USA.
# All Rights Reserved.
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

What I'm trying to do here is abstract much of the functionality that directly
accesses the DOM tree.  This is not so much to "protect" the other code from
the DOM, but to standardize the way it's used.  It will also help extension
authors write code that easily looks more like the rest of Cedar Backup.

This module is one of the few pieces of code in the CedarBackup2 package that
requires functionality outside of the Python 2.3 standard library.   It
requires the PyXML package, mostly for the pretty-print functionality provided
there.

@sort: createInputDom, createOutputDom, serializeDom, isElement, readChildren, 
       readFirstChild, readStringList, readString, readInteger, readBoolean,
       addContainerNode, addStringNode, addIntegerNode, addBooleanNode,
       TRUE_BOOLEAN_VALUES, FALSE_BOOLEAN_VALUES, VALID_BOOLEAN_VALUES

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
from StringIO import StringIO

# XML-related modules
from xml.parsers.expat import ExpatError
from xml.dom.minidom import Node
from xml.dom.minidom import getDOMImplementation
from xml.dom.minidom import parseString


########################################################################
# Module-wide constants and variables
########################################################################

logger = logging.getLogger("CedarBackup2.log.xml")

TRUE_BOOLEAN_VALUES   = [ "Y", "y", ]
FALSE_BOOLEAN_VALUES  = [ "N", "n", ]
VALID_BOOLEAN_VALUES  = TRUE_BOOLEAN_VALUES + FALSE_BOOLEAN_VALUES


########################################################################
# Functions for creating and parsing DOM trees
########################################################################

def createInputDom(xmlData, name="cb_config"):
   """
   Creates a DOM tree based on reading an XML string.
   @param name: Assumed base name of the document (root node name).
   @return: Tuple (xmlDom, parentNode) for the parsed document
   @raise ValueError: If the document can't be parsed.
   """
   try:
      xmlDom = parseString(xmlData)
      parentNode = readFirstChild(xmlDom, name)
      return (xmlDom, parentNode)
   except (IOError, ExpatError), e:
      raise ValueError("Unable to parse XML document: %s" % e)

def createOutputDom(name="cb_config"):
   """
   Creates a DOM tree used for writing an XML document.
   @param name: Base name of the document (root node name).
   @return: Tuple (xmlDom, parentNode) for the new document
   """
   impl = getDOMImplementation()
   xmlDom = impl.createDocument(None, name, None)
   return (xmlDom, xmlDom.documentElement)


########################################################################
# Functions for reading values out of XML documents
########################################################################

def isElement(node):
   """
   Returns True or False depending on whether the XML node is an element node.
   """
   return node.nodeType == Node.ELEMENT_NODE

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


########################################################################
# Functions for writing values into XML documents
########################################################################

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


########################################################################
# Functions for serializing DOM trees
########################################################################

def serializeDom(xmlDom, indent=3):
   """
   Serializes a DOM tree and returns the result in a string.

   @note: It turns out that the PrettyPrint() function is the only thing we
   rely on from the larger PyXML distribution that is not part of the Python
   standard library.  I'd love to get rid of it in favor of something  like the
   minidom toprettyxml() function.  However, it just doesn't work.  The XML
   generated by toprettyxml() just isn't too "pretty" and doesn't look anything
   like what we need.

   @copyright: Some of this code, prior to customization, was originally part
   of the PyXML codebase, and before that was part of the 4DOM suite developed
   by Fourthought, Inc.  This code is Copyright (c) 2000 Fourthought Inc, USA;
   All Rights Reserved.

   @param xmlDom: XML DOM tree to serialize
   @param indent: Number of spaces to indent

   @return: String form of DOM tree, pretty-printed.
   """
   xmlBuffer = StringIO()
   _PrettyPrint(xmlDom, xmlBuffer, indent=indent*" ")
   xmlData = xmlBuffer.getvalue()
   xmlBuffer.close()
   return xmlData 

def _PrettyPrint(xmlDom, stream, indent='  '):
   """
   Pretty-prints an XML document in a sensible way.
   @param xmlDom: XML DOM tree to pretty-print
   @param stream: Output string to use (could be StringIO, even)
   @param indent: Indent string to use for each level of indentation
   """
   visitor = PrintVisitor(stream, "UTF-8", indent, [], {})
   visitor.visit(xmlDom)
   stream.write('\n')
   return

import string
import re

XML_NAMESPACE = "http://www.w3.org/XML/1998/namespace"
XMLNS_NAMESPACE = "http://www.w3.org/2000/xmlns/"
XHTML_NAMESPACE = "http://www.w3.org/1999/xhtml"

class PrintVisitor(object):
    def __init__(self, stream, encoding, indent='', plainElements=None,
                 nsHints=None, isXhtml=0, force8bit=0):
        self.stream = stream
        self.encoding = encoding
        # Namespaces
        self._namespaces = [{}]
        self._nsHints = nsHints or {}
        # PrettyPrint
        self._indent = indent
        self._depth = 0
        self._inText = 0
        self._plainElements = plainElements or []
        # HTML support
        self._html = None
        self._isXhtml = isXhtml
        self.force8bit = force8bit
        return

    def _write(self, text):
        if self.force8bit:
            obj = strobj_to_utf8str(text, self.encoding)
        else:
            obj = utf8_to_code(text, self.encoding)
        self.stream.write(obj)
        return

    def _tryIndent(self):
        if not self._inText and self._indent:
            self._write('\n' + self._indent*self._depth)
        return

    def visit(self, node):
        if self._html is None:
            # Set HTMLDocument flag here for speed
            self._html = hasattr(node.ownerDocument, 'getElementsByName')

        if node.nodeType == Node.ELEMENT_NODE:
            return self.visitElement(node)

        elif node.nodeType == Node.ATTRIBUTE_NODE:
            return self.visitAttr(node)

        elif node.nodeType == Node.TEXT_NODE:
            return self.visitText(node)

        elif node.nodeType == Node.CDATA_SECTION_NODE:
            return self.visitCDATASection(node)

        elif node.nodeType == Node.ENTITY_REFERENCE_NODE:
            return self.visitEntityReference(node)

        elif node.nodeType == Node.ENTITY_NODE:
            return self.visitEntity(node)

        elif node.nodeType == Node.PROCESSING_INSTRUCTION_NODE:
            return self.visitProcessingInstruction(node)

        elif node.nodeType == Node.COMMENT_NODE:
            return self.visitComment(node)

        elif node.nodeType == Node.DOCUMENT_NODE:
            return self.visitDocument(node)

        elif node.nodeType == Node.DOCUMENT_TYPE_NODE:
            return self.visitDocumentType(node)

        elif node.nodeType == Node.DOCUMENT_FRAGMENT_NODE:
            return self.visitDocumentFragment(node)

        elif node.nodeType == Node.NOTATION_NODE:
            return self.visitNotation(node)

        # It has a node type, but we don't know how to handle it
        raise Exception("Unknown node type: %s" % repr(node))

    def visitNodeList(self, node, exclude=None):
        for curr in node:
            curr is not exclude and self.visit(curr)
        return

    def visitNamedNodeMap(self, node):
        for item in node.values():
            self.visit(item)
        return

    def visitAttr(self, node):
        if node.namespaceURI == XMLNS_NAMESPACE:
            # Skip namespace declarations
            return
        self._write(' ' + node.name)
        value = node.value
        if value or not self._html:
            text = TranslateCdata(value, self.encoding)
            text, delimiter = TranslateCdataAttr(text)
            self.stream.write("=%s%s%s" % (delimiter, text, delimiter))
        return

    def visitProlog(self):
        self._write("<?xml version='1.0' encoding='%s'?>" % (
            self.encoding or 'utf-8'
            ))
        self._inText = 0
        return

    def visitDocument(self, node):
        not self._html and self.visitProlog()
        node.doctype and self.visitDocumentType(node.doctype)
        self.visitNodeList(node.childNodes, exclude=node.doctype)
        return

    def visitDocumentFragment(self, node):
        self.visitNodeList(node.childNodes)
        return

    def visitElement(self, node):
        self._namespaces.append(self._namespaces[-1].copy())
        inline = node.tagName in self._plainElements
        not inline and self._tryIndent()
        self._write('<%s' % node.tagName)
        if self._isXhtml or not self._html:
            namespaces = ''
            if self._isXhtml:
                nss = {'xml': XML_NAMESPACE, None: XHTML_NAMESPACE}
            else:
                nss = GetAllNs(node)
            if self._nsHints:
                self._nsHints.update(nss)
                nss = self._nsHints
                self._nsHints = {}
            del nss['xml']
            for prefix in nss.keys():
                if not self._namespaces[-1].has_key(prefix) or self._namespaces[-1][prefix] != nss[prefix]:
                    nsuri, delimiter = TranslateCdataAttr(nss[prefix])
                    if prefix:
                        xmlns = " xmlns:%s=%s%s%s" % (prefix, delimiter,nsuri,delimiter)
                    else:
                        xmlns = " xmlns=%s%s%s" % (delimiter,nsuri,delimiter)
                    namespaces = namespaces + xmlns

                self._namespaces[-1][prefix] = nss[prefix]
            self._write(namespaces)
        for attr in node.attributes.values():
            self.visitAttr(attr)
        if len(node.childNodes):
            self._write('>')
            self._depth = self._depth + 1
            self.visitNodeList(node.childNodes)
            self._depth = self._depth - 1
            if not self._html or (node.tagName not in HTML_FORBIDDEN_END):
                not (self._inText and inline) and self._tryIndent()
                self._write('</%s>' % node.tagName)
        elif not self._html:
            self._write('/>')
        elif node.tagName not in HTML_FORBIDDEN_END:
            self._write('></%s>' % node.tagName)
        else:
            self._write('>')
        del self._namespaces[-1]
        self._inText = 0
        return

    def visitText(self, node):
        text = node.data
        if self._indent:
            text = string.strip(text) and text
        if text:
            text = TranslateCdata(text, self.encoding)
            self.stream.write(text)
            self._inText = 1
        return

    def visitDocumentType(self, doctype):
        if not doctype.systemId and not doctype.publicId: return
        self._tryIndent()
        self._write('<!DOCTYPE %s' % doctype.name)
        if doctype.systemId and '"' in doctype.systemId:
            system = "'%s'" % doctype.systemId
        else:
            system = '"%s"' % doctype.systemId
        if doctype.publicId and '"' in doctype.publicId:
            # We should probably throw an error
            # Valid characters:  <space> | <newline> | <linefeed> |
            #                    [a-zA-Z0-9] | [-'()+,./:=?;!*#@$_%]
            public = "'%s'" % doctype.publicId
        else:
            public = '"%s"' % doctype.publicId
        if doctype.publicId and doctype.systemId:
            self._write(' PUBLIC %s %s' % (public, system))
        elif doctype.systemId:
            self._write(' SYSTEM %s' % system)
        if doctype.entities or doctype.notations:
            self._write(' [')
            self._depth = self._depth + 1
            self.visitNamedNodeMap(doctype.entities)
            self.visitNamedNodeMap(doctype.notations)
            self._depth = self._depth - 1
            self._tryIndent()
            self._write(']>')
        else:
            self._write('>')
        self._inText = 0
        return

    def visitEntity(self, node):
        """Visited from a NamedNodeMap in DocumentType"""
        self._tryIndent()
        self._write('<!ENTITY %s' % (node.nodeName))
        node.publicId and self._write(' PUBLIC %s' % node.publicId)
        node.systemId and self._write(' SYSTEM %s' % node.systemId)
        node.notationName and self._write(' NDATA %s' % node.notationName)
        self._write('>')
        return

    def visitNotation(self, node):
        """Visited from a NamedNodeMap in DocumentType"""
        self._tryIndent()
        self._write('<!NOTATION %s' % node.nodeName)
        node.publicId and self._write(' PUBLIC %s' % node.publicId)
        node.systemId and self._write(' SYSTEM %s' % node.systemId)
        self._write('>')
        return

    def visitCDATASection(self, node):
        self._tryIndent()
        self._write('<![CDATA[%s]]>' % (node.data))
        self._inText = 0
        return

    def visitComment(self, node):
        self._tryIndent()
        self._write('<!--%s-->' % (node.data))
        self._inText = 0
        return

    def visitEntityReference(self, node):
        self._write('&%s;' % node.nodeName)
        self._inText = 1
        return

    def visitProcessingInstruction(self, node):
        self._tryIndent()
        self._write('<?%s %s?>' % (node.target, node.data))
        self._inText = 0
        return

#The following stanza courtesy Martin von Loewis
import codecs # Python 1.6+ only
from types import UnicodeType
def utf8_to_code(text, encoding):
  encoder = codecs.lookup(encoding)[0] # encode,decode,reader,writer
  if type(text) is not UnicodeType:
      text = unicode(text, "utf-8")
  return encoder(text)[0] # result,size
def strobj_to_utf8str(text, encoding):
  if string.upper(encoding) not in ["UTF-8", "ISO-8859-1", "LATIN-1"]:
      raise ValueError("Invalid encoding: %s"%encoding)
  encoder = codecs.lookup(encoding)[0] # encode,decode,reader,writer
  if type(text) is not UnicodeType:
      text = unicode(text, "utf-8")
  #FIXME
  return str(encoder(text)[0])

g_cdataCharPattern = re.compile('[&<]|]]>')
g_charToEntity = {
        '&': '&amp;',
        '<': '&lt;',
        ']]>': ']]&gt;',
        }

ILLEGAL_LOW_CHARS = '[\x01-\x08\x0B-\x0C\x0E-\x1F]'
ILLEGAL_HIGH_CHARS = '\xEF\xBF[\xBE\xBF]'
XML_ILLEGAL_CHAR_PATTERN = re.compile('%s|%s'%(ILLEGAL_LOW_CHARS, ILLEGAL_HIGH_CHARS))

def TranslateCdataAttr(characters):
    '''Handles normalization and some intelligence about quoting'''
    if not characters:
        return '', "'"
    if "'" in characters:
        delimiter = '"'
        new_chars = re.sub('"', '&quot;', characters)
    else:
        delimiter = "'"
        new_chars = re.sub("'", '&apos;', characters)
    #FIXME: There's more to normalization
    #Convert attribute new-lines to character entity
    # characters is possibly shorter than new_chars (no entities)
    if "\n" in characters:
        new_chars = re.sub('\n', '&#10;', new_chars)
    return new_chars, delimiter

#Note: Unicode object only for now
def TranslateCdata(characters, encoding='UTF-8', prev_chars='', markupSafe=0,
                   charsetHandler=utf8_to_code):
    """
    charsetHandler is a function that takes a string or unicode object as the
    first argument, representing the string to be procesed, and an encoding
    specifier as the second argument.  It must return a string or unicode
    object
    """
    if not characters:
        return ''
    if not markupSafe:
        if g_cdataCharPattern.search(characters):
            new_string = g_cdataCharPattern.subn(
                lambda m, d=g_charToEntity: d[m.group()],
                characters)[0]
        else:
            new_string = characters
        if prev_chars[-2:] == ']]' and characters[0] == '>':
            new_string = '&gt;' + new_string[1:]
    else:
        new_string = characters
    #Note: use decimal char entity rep because some browsers are broken
    #FIXME: This will bomb for high characters.  Should, for instance, detect
    #The UTF-8 for 0xFFFE and put out &#xFFFE;
    if XML_ILLEGAL_CHAR_PATTERN.search(new_string):
        new_string = XML_ILLEGAL_CHAR_PATTERN.subn(
            lambda m: '&#%i;' % ord(m.group()),
            new_string)[0]
    new_string = charsetHandler(new_string, encoding)
    return new_string

HTML_FORBIDDEN_END = ['AREA', 'BASE', 'BASEFONT', 'BR', 'COL', 'FRAME', 'HR', 'IMG', 'INPUT', 'ISINDEX', 'LINK', 'META', 'PARAM']

def GetAllNs(node):
    #The xml namespace is implicit
    nss = {'xml': XML_NAMESPACE}
    if node.nodeType == Node.ATTRIBUTE_NODE and node.ownerElement:
        return GetAllNs(node.ownerElement)
    if node.nodeType == Node.ELEMENT_NODE:
        if node.namespaceURI:
            nss[node.prefix] = node.namespaceURI
        for attr in node.attributes.values():
            if attr.namespaceURI == XMLNS_NAMESPACE:
                if attr.localName == 'xmlns':
                    nss[None] = attr.value
                else:
                    nss[attr.localName] = attr.value
            elif attr.namespaceURI:
                nss[attr.prefix] = attr.namespaceURI
    if node.parentNode:
        #Inner NS/Prefix mappings take precedence over outer ones
        parent_nss = GetAllNs(node.parentNode)
        parent_nss.update(nss)
        nss = parent_nss
    return nss

