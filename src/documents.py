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

from PyQt4 import QtCore, QtGui
import numpy
import scipy.ndimage

import time
import os

from misc import URL
import undo
import imageLib


class Document:
    """Base document that gets inherited."""

    def __init__(self, view, url=None, type="base"):
        """
        @param view: View object
        @param url: URL
        @param type: which kind of document this is.
        """
        self.view = view
        self.url = url
        # XXX: Move the url rename to view.addDocument?
        # if(url != None):
        #    view.fixName(self.url)
        self.type = type
        # Should be set by actual doc init
        self.image = None
        self.pixmap = None
        self.display = False
        self.lastAction = "Original"

    def getType(self):
        """
        @return: The type of document this is.
        """
        return self.type

    def getURL(self):
        """
        @return: returns document url.
        """
        return self.url;

    def getPixmap(self):
        """
        @return: document's pixmap
        """
        return self.pixmap

    def regenPixmap(self):
        """
        Regenerates the documents pixmap.
        """
        if self.display == False:
            return
        self.pixmap = self.makePixmap(self.view.inverted, self.view.zoomLevel)

    def makePixmap(self, inverted, zoomLevel):
        """
        Make the document's pixmap
        @param inverted: If to make the pixmap inverted.
        @type inverted: bool
        @param zoomLevel: How much to zoom the image.
        @type zoomLevel: number
        """
        startTime = time.time()
        image = self.image.copy()
        if inverted == 1:
            image.invertPixels()

        # zooming
        # XXX: Use QImage.scale instead?
        tmpPixmap = QtGui.QPixmap.fromImage(image)
        pixmap = tmpPixmap.scaled(int(image.width() * zoomLevel), int(image.height() * zoomLevel))
        print "TIME Document.makePixmap() " + str(time.time() - startTime) + " s"
        return pixmap

    def isColor(self):
        """
            @return: True if a color image, False if not.
        """
        return False

    def refresh(self, regenStats=False):
        """
        Regenerates the image, pixmap, and optional the stats.

        @param regenStats: True if should regen the image stats, False if not.
        """
        if regenStats == True:
            self.regenStats()
        self.regenImage()
        self.regenPixmap()
        if self.view.getCurrentDocument() == self:
            # XXX: Don't think I need switchedTab
            self.view.switchedTab()
            self.view.resizeRepaintScrollView()


class NormalDocument(Document):
    """
    Class for normal black and white document.
    """

    def __init__(self, view, data, brightRange=None, header=None, url=URL(fullPath="/tmp/New"), display=True):
        """
        @param view: View object
        @param data: The image data
        @type data: numpy array
        @param brightRange: Background and Range
        @type brightRange: 1x2 array numbers
        @param header: The documents header
        @param url: The documents url
        @param display: If the object should generate stuff for display 
        @type display: boolean
        """
        startTime = time.time()
        Document.__init__(self, view, url, "normal")
        # Use just image data from fits or sbig and generate image based on options set.
        self.display = display
        self.data = data
        self.header = header
        # stats
        self.brightRange = brightRange
        # Needs to be up here for autoContrast()
        self.undo = undo.Undo()
        self.regenStats()
        if (self.brightRange == None and self.header != None):
            self.brightRange = imageLib.extractBrightRange(self.header)
        if (self.brightRange == None):
            self.brightRange = self.autoContrast()
            print self.brightRange

        self.regenImage()
        self.regenPixmap()
        print "TIME NormalDocument.__init__() " + str(time.time() - startTime) + " s"

    def copy(self, x=None, y=None, width=None, height=None):
        """
        @param x: x coord for selection
        @param y: y coord for selection
        @param width: width of selection
        @param height: height of selection
        @return: A copy or selection copy of this document.
        """
        # XXX: Copy header to
        if (x == None or y == None or width == None or height == None) or \
           (x < 0 or x + width < 0 or x + width >= self.data.shape[1]) or \
           (y < 0 or y + height < 0 or y + height >= self.data.shape[0]):
            d = numpy.array(self.data)
        else:
            ya = y;
            yb = y + height + 1
            xa = x
            xb = x + width + 1
            if xa > xb:
                xa = xb - 1
                xb = x + 1
            if ya > yb:
                ya = yb - 1
                yb = y + 1
            d = numpy.array(self.data[ya:yb, xa:xb])
        doc = NormalDocument(self.view, d, self.brightRange, None, URL(url=self.url), self.display)
        return doc

    def regenStats(self):
        """
        Regenerate documents stats.
        """
        startTime = time.time()
        self.min = self.data.min()
        self.max = self.data.max()

        # XXX: Histogram should be done with less bins
        # if(self.max < 1000):
        self.hist = scipy.ndimage.histogram(numpy.cast[numpy.uint32](self.data), 0, int(self.max + 1),
                                            int(self.max + 1))
        # else:
        #    self.hist = scipy.ndimage.histogram(self.data, 0, int(self.max+1), 1000)
        self.background = self.data.mean()
        print self.brightRange
        if self.brightRange != None and self.brightRange[1] > self.max:
            self.brightRange = self.autoContrast()
        print "TIME: NormalDocument.regenStats() " + str(time.time() - startTime) + " s"

    def getShape(self):
        """
        @return: shape of document
        """
        return self.data.shape

    def autoContrast(self):
        """
        @return: [background, range]
        """
        return imageLib.autoContrast(self.hist, self.data.shape[0], self.data.shape[1])

    def getBrightRange(self):
        """
        @return: Current [background, range]
        """
        return self.brightRange

    def setBrightRange(self, brightRange):
        """
        Sets background and range for the document.
        """
        if brightRange[1] > self.max:
            brightRange[1] = self.max
        self.brightRange = brightRange

    def getHistogram(self):
        """
        @return: numpy array histogram of data.
        """
        return self.hist

    def getHeader(self):
        return self.header

    def regenImage(self):
        startTime = time.time()
        if self.display == False:
            return
        tmpData = imageLib.reduceToVisual(self.data, self.brightRange)
        tmpData = numpy.repeat(tmpData.flat, 4)
        self.buffer = tmpData.tostring()
        # XXX: Fix test endian bitorder
        self.image = QtGui.QImage(self.buffer, self.data.shape[1], self.data.shape[0], QtGui.QImage.Format_RGB32)
        print "TIME: NormalDocument.regenImage() " + str(time.time() - startTime) + " s"

    def replaceData(self, newdata, actionString):
        """If actionSTring is None no undo data is saved."""
        if actionString != None:
            self.undo.setUndo(self, self.getBrightRange(), newdata)
            self.lastAction = actionString
        self.data = newdata


class ColorRGBDocument(Document):
    """Red Green Blue Color Document"""

    def __init__(self, view, rgbData, brightRange=None, headers=None, url=URL(fullPath="/tmp/NewRGB"), display=True):
        """
        @param view: View object
        @param rgbData: three image data for each channel red, green, blue.
        @type rgbData: [red_data, green_data, blue_data]
        @type brightRange: [red_br, green_br, blue_br]
        @type headers: [red_header, green_header, blue_header]
        @param url: Document url
        @param display: If should do extra stuff for display.
        """
        startTime = time.time()
        Document.__init__(self, view, url, "color_rgb")
        self.display = display
        self.rgb = []
        rgbTextOrder = ["Red", "Green", "Blue"]
        for i in range(3):
            tempBR = None
            if (brightRange != None):
                tempBR = brightRange[i]
            header = None
            if (headers != None):
                header = headers[i]
            self.rgb.append(NormalDocument(view, rgbData[i], header=header, url=URL(fullPath="/tmp/" + rgbTextOrder[i]),
                                           brightRange=tempBR, display=False))
        self.undo = undo.UndoRGB()
        # self.regenStats() #Don't need this called on each document creation
        self.regenImage()
        self.regenPixmap()
        print "TIME: ColorRGBDocument.__init__() " + str(time.time() - startTime) + " s"

    def copy(self, x=None, y=None, width=None, height=None):
        """
        @param x: x coord for selection
        @param y: y coord for selection
        @param width: width of selection
        @param height: height of selection
        @return: A copy or selection copy of this document.
        """
        # XXX: Copy header
        if (x == None or y == None or width == None or height == None) or \
           (x < 0 or x + width < 0 or x + width >= self.rgb[0].data.shape[1]) or \
           (y < 0 or y + height < 0 or y + height >= self.rgb[0].data.shape[0]):
            r = numpy.array(self.rgb[0].data)
            g = numpy.array(self.rgb[1].data)
            b = numpy.array(self.rgb[2].data)
        else:
            ya = y
            yb = y + height + 1
            xa = x
            xb = x + width + 1
            if xa > xb:
                xa = xb - 1
                xb = x + 1
            if ya > yb:
                ya = yb - 1
                yb = y + 1
            r = numpy.array(self.rgb[0].data[ya:yb, xa:xb])
            g = numpy.array(self.rgb[1].data[ya:yb, xa:xb])
            b = numpy.array(self.rgb[2].data[ya:yb, xa:xb])
        doc = ColorRGBDocument(self.view, [r, g, b], self.getBrightRange(), None, URL(url=self.url), self.display)
        return doc

    def regenStats(self):
        for doc in self.rgb:
            doc.regenStats()

    def getShape(self):
        return self.rgb[0].data.shape

    def autoContrast(self):
        t = []
        for doc in self.rgb:
            t.append(doc.autoContrast())
        return t

    def getBrightRange(self):
        t = []
        for doc in self.rgb:
            t.append(doc.getBrightRange())
        return t

    def setBrightRange(self, brightRange):
        for i in range(len(brightRange)):
            self.rgb[i].setBrightRange(brightRange[i])

    def getHistogram(self):
        t = []
        for doc in self.rgb:
            t.append(doc.getHistogram())
        return t

    def getHeader(self):
        t = []
        for doc in self.rgb:
            t.append(doc.getHeader())
        return t

    def regenImage(self):
        startTime = time.time()
        if self.display == False:
            return
        colorParts = []
        br = self.getBrightRange()
        for i in range(len(self.rgb)):
            colorParts.append(imageLib.reduceToVisual(self.rgb[i].data, br[i]))
        t = imageLib.reducedRGBtoBufferQImage(colorParts)
        self.buffer = t[0]
        self.image = t[1]
        print "TIME: ColorRGBDocument.regenImage() " + str(time.time() - startTime) + " s"

    def replaceData(self, rgbData, actionString):
        """If actionString is None, no undo data is saved"""
        if actionString != None:
            self.undo.setUndo(self, self.getBrightRange(), rgbData)
            self.lastAction = actionString
        for i in range(len(self.rgb)):
            if rgbData[i] != None:
                self.rgb[i].replaceData(rgbData[i], None)

    def isColor(self):
        return True


class ColorRGBLDocument(ColorRGBDocument):
    """ Red, Green, Blue, Lumanance document. Similar to RGB except with lumance."""

    def __init__(self, view, rgblData, brightRange=None, headers=None, url=URL(fullPath="/tmp/NewLRGB"), display=True):
        Document.__init__(self, view, url, "color_rgbl")
        self.rgb = []
        self.display = display
        rgbTextOrder = ["Red", "Green", "Blue", "Luminance"]
        for i in range(4):
            tempBR = None
            if brightRange != None:
                tempBR = brightRange[i]
            header = None
            if headers != None:
                header = headers[i]
            self.rgb.append(
                NormalDocument(view, rgblData[i], header=header, url=URL(fullPath="/tmp/" + rgbTextOrder[i]),
                               brightRange=tempBR, display=False))
        self.undo = undo.UndoRGB()
        self.regenStats()
        self.regenImage()
        self.regenPixmap()

    def copy(self, x=None, y=None, width=None, height=None):
        """
        @param x: x coord for selection
        @param y: y coord for selection
        @param width: width of selection
        @param height: height of selection
        @return: A copy or selection copy of this document.
        """
        # XXX: Copy header
        if (x == None or y == None or width == None or height == None) or \
           (x < 0 or x + width < 0 or x + width >= self.rgb[0].data.shape[1]) or \
           (y < 0 or y + height < 0 or y + height >= self.rgb[0].data.shape[0]):
            r = numpy.array(self.rgb[0].data)
            g = numpy.array(self.rgb[1].data)
            b = numpy.array(self.rgb[2].data)
            l = numpy.array(self.rgb[3].data)
        else:
            ya = y
            yb = y + height + 1
            xa = x
            xb = x + width + 1
            if xa > xb:
                xa = xb - 1
                xb = x + 1
            if ya > yb:
                ya = yb - 1
                yb = y + 1
            r = numpy.array(self.rgb[0].data[ya:yb, xa:xb])
            g = numpy.array(self.rgb[1].data[ya:yb, xa:xb])
            b = numpy.array(self.rgb[2].data[ya:yb, xa:xb])
            l = numpy.array(self.rgb[3].data[ya:yb, xa:xb])
        doc = ColorRGBLDocument(self.view, [r, g, b, l], self.getBrightRange(), None, URL(url=self.url), self.display)
        return doc

    def regenImage(self):
        startTime = time.time()
        if self.display == False:
            return
        colorParts = []
        br = self.getBrightRange()
        for i in range(len(self.rgb)):
            colorParts.append(imageLib.reduceToVisual(self.rgb[i].data, br[i]) / 255.)
        t = imageLib.toHSL(colorParts[0], colorParts[1], colorParts[2])
        t = imageLib.toRGB(t[0], t[1], colorParts[3])
        t = imageLib.reducedRGBtoBufferQImage(
            [numpy.cast[numpy.uint8](t[0] * 255.), numpy.cast[numpy.uint8](t[1] * 255.),
             numpy.cast[numpy.uint8](t[2] * 255.)])
        self.buffer = t[0]
        self.image = t[1]
        print "TIME: ColorRGBLDocument.regenImage() " + str(time.time() - startTime) + " s"
