# pygopherd -- Gopher-based protocol server in Python
# module: Special handling for URLs
# Copyright (C) 2002 John Goerzen
# <jgoerzen@complete.org>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import SocketServer
import re
import os, stat, os.path, mimetypes
from pygopherd import protocols, gopherentry, handlers
from pygopherd.handlers.base import BaseHandler

class HTMLURLHandler(BaseHandler):
    """Will take requests for a URL-like selector and generate
    a HTML page redirecting people to the actual URL.

    This implementation adheres to the proposal as specified at
    http://www.complete.org/mailinglists/archives/gopher-200202/msg00033.html
    """
    
    def isrequestsecure(self):
        """For URLs, it is valid to have .., //, etc in the URLs."""
        return self.canhandlerequest() and \
               self.selector.find("\0") == -1 and \
               self.selector.find("\n") == -1 and \
               self.selector.find("\t") == -1 and \
               self.selector.find('"') == -1 and \
               self.selector.find("\r") == -1

    def canhandlerequest(self):
        """We can handle the request if it's for something that starts
        with http or https."""
        return re.search("^(/|)URL:.+://", self.selector)

    def getentry(self):
        if not self.entry:
            self.entry = gopherentry.GopherEntry(self.selector, self.config)
            self.entry.name = self.selector
            self.entry.mimetype = 'text/html'
            self.entry.type = 'h'
        return self.entry

    # We have nothing to prepare.

    def write(self, wfile):
        url = self.selector[4:]         # Strip off URL:
        if self.selector[0] == '/':
            url = self.selector[5:]
        outdoc = "<HTML><HEAD>\n"
        outdoc += '<META HTTP-EQUIV="refresh" content="5;URL=%s">' % url
        outdoc += "</HEAD><BODY>\n"
        outdoc += """
        You are following a link from gopher to a website.  You will be
        automatically taken to the web site shortly.  If you do not get
        sent there, plesae click """
        outdoc += '<A HREF="%s">here</A> ' % url
        outdoc += """to go to the web site.
        <P>
        The URL linked is:
        <P>"""
        outdoc += '<A HREF="%s">%s</A>' % (url, url)
        outdoc += """<P>
        Thanks for using gopher!
        <P>
        Document generated by pygopherd handlers.url.HTMLURLHandler
        </BODY></HTML>"""
        wfile.write(outdoc)

class URLTypeRewriter(BaseHandler):
    """Will take URLs that start with a file type (ie,
    /1/devel/offlineimap) and remove the type (/devel/offlineimap).  Useful
    if you want to make relative links in both gopher and http space in
    a single document."""

    def canhandlerequest(self):
        return len(self.selector) >= 3 and \
               self.selector[0] == '/' and \
               self.selector[2] == '/'

    def gethandler(self):
        handlerlist = [x for x in handlers.HandlerMultiplexer.handlers if
                       x != URLTypeRewriter]
        return handlers.HandlerMultiplexer.getHandler(self.selector[2:],
                                             self.searchrequest, self.protocol,
                                             self.config, handlerlist)
    
