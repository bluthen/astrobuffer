# AstroBuffer - Astrophotography software
# Copyright (C) 2007,2008,2017 Russell Valentine
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import os
import time
import cPickle
import tempfile


def getExtension(filename):
    ext = os.path.splitext(str(filename))
    return ext[1].lower()


def fixFITSHeader(header):
    """fixFITSHeader(head) returns the an fits header in form {key: [value, comment], ..}"""
    newHeader = {}
    for key in header.keys():
        value = header[key]
        comment = header.comments[key]
        newHeader[key] = [value, comment]
    return newHeader


def fixSBIGHeader(header):
    """fixSBIGHeader(head) returns the an sbig header in form {key: [value, comment], ..}"""
    newHeader = {}
    for key, value in header.iteritems():
        newHeader[key.upper()] = [value, '']
    return newHeader


def pickle(object):
    """pickle(object) - Pickles the object returns temp file object"""
    startTime = time.time()
    kfile = tempfile.TemporaryFile()
    kfile.seek(0)
    cPickle.dump(object, kfile, protocol=cPickle.HIGHEST_PROTOCOL)
    kfile.seek(0)
    print "TIME: pickle() " + str(time.time() - startTime) + " s"
    return kfile


def unpickle(tempfile):
    """unpickle(tempfile) - unpickles object from open filed object tempfile oposite of pickle() returns original pickled object."""
    startTime = time.time()
    tempfile.seek(0)
    object = cPickle.load(tempfile)
    tempfile.seek(0)
    print "TIME: unpickle() " + str(time.time() - startTime) + " s"
    return object


class URL:
    def __init__(self, fullPath=None, url=None):
        fp = fullPath
        if url:
            fp = url.getFullPath()
        self.setFullPath(fp)

    def setFullPath(self, path):
        self.fullPath = str(path)
        idx = self.fullPath.rfind(os.sep)
        if idx >= 0 and idx < len(self.fullPath):
            self.fileName = self.fullPath[idx + 1:]
        else:
            raise Exception("Couldn't extract filename from full path.")
        self.ext = getExtension(self.fileName)

    def setFileName(self, fileName):
        idx = self.fullPath.rfind(os.sep)
        fp = self.fullPath[:idx + 1] + fileName
        self.setFullPath(fp)

    def getFileName(self):
        return self.fileName

    def getExtension(self):
        return self.ext

    def getFullPath(self):
        return self.fullPath

    def getDirPath(self):
        idx = self.fullPath.rfind(os.sep)
        return self.fullPath[:idx]

    def empty(self):
        if self.fullPath:
            return False
        else:
            return True
