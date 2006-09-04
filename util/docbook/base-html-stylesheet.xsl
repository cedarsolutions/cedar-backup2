<!--
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
#              C E D A R
#          S O L U T I O N S       "Software done right."
#           S O F T W A R E
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# Author   : Kenneth J. Pronovici <pronovic@ieee.org>
# Language : XSLT
# Project  : Cedar Backup, release 2
# Revision : $Id$
# Purpose  : General stylesheet used by other format-specific sheets.
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
-->
<!--
   This stylesheet was originally taken from the Subversion project's book
   (http://svnbook.red-bean.com/) and has been modifed for use with Cedar
   Backup.

   The original stylesheet was (c) 2000-2006 CollabNet (see CREDITS).

   I have no major changes to this stylesheet.
-->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version='1.0'>

  <xsl:param name="html.stylesheet">styles.css</xsl:param>
  <xsl:param name="toc.section.depth">3</xsl:param>
  <xsl:param name="annotate.toc">0</xsl:param>

  <xsl:template match="sect1" mode="toc">
    <xsl:param name="toc-context" select="."/>
    <xsl:call-template name="subtoc">
      <xsl:with-param name="toc-context" select="$toc-context"/>
      <xsl:with-param name="nodes" 
        select="sect2|refentry|bridgehead[$bridgehead.in.toc != 0]"/>
    </xsl:call-template>
  </xsl:template>

  <xsl:template match="sect2" mode="toc">
    <xsl:param name="toc-context" select="."/>

    <xsl:call-template name="subtoc">
      <xsl:with-param name="toc-context" select="$toc-context"/>
      <xsl:with-param name="nodes" 
        select="sect3|refentry|bridgehead[$bridgehead.in.toc != 0]"/>
    </xsl:call-template>
  </xsl:template>

</xsl:stylesheet>
