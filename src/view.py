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

from PyQt4 import QtCore, QtGui

from documents import NormalDocument, ColorRGBDocument, ColorRGBLDocument
from contrastDialog import ContrastDialog, ColorRGBContrastDialog, ColorRGBLContrastDialog
from simpleDialogs import ImageInfoDialog
import misc
from misc import URL
from astropy.io import fits
import numpy
from config import Config


class View(QtGui.QWidget):
    def __init__(self, window, app):
        QtGui.QWidget.__init__(self, window)
        self.app = app

        # Run-time settings
        self.inverted = 0
        self.zoomLevel = 1.0
        self.blinksPerSecond = 0
        self.blinkThread = Blinker(self)
        self.contrastDialog = None
        self.colorRGBContrastDialog = None
        self.colorRGBLContrastDialog = None
        self.imageInfoDialog = None

        self.window = window

        layout = QtGui.QVBoxLayout(self)
        self.tabBar = QtGui.QTabBar()
        self.documents = []
        self.tabBar.addTab("Empty")
        self.tabBar.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

        # Tab popup
        self.tabpopup = QtGui.QMenu(self.tabBar)
        # XXX: Use stdaction close
        # XXX: Add rename to popup
        self.popupTabIndex = None
        rename = QtGui.QAction("Rename", self.tabpopup, triggered=self.slotPopupRenameTab)
        self.tabpopup.addAction(rename)
        rename.setEnabled(True)

        close = QtGui.QAction("Close", self.tabpopup, triggered=self.slotPopupCloseTab)
        self.tabpopup.addAction(close)
        close.setEnabled(True)

        self.tabBar.currentChanged.connect(self.switchedTab)
        # self.tabBar.mouseDoubleClick.connect(self.renameTab)
        self.tabBar.customContextMenuRequested.connect(self.doTabContextMenu)
        # self.tabBar.customContextMenuRequested.connect(self.doTabContextMenu)
        layout.addWidget(self.tabBar)
        self.imageArea = ImageLabel(self)
        self.scrollArea = QtGui.QScrollArea(self)
        self.scrollArea.setWidget(self.imageArea)
        # self.scrollArea.setSizePolicy(QtGui.QSizePolicy.Ignored, QtGui.QSizePolicy.Ignored)
        layout.addWidget(self.scrollArea)

        # Magnification Dialog
        self.magDialog = QtGui.QDialog(self)
        self.magDialog.setWindowTitle("Magnification box")
        page = QtGui.QVBoxLayout()
        self.mag = MagWidget(self)
        spinBox = QtGui.QSpinBox()
        spinBox.setMaximum(5)
        spinBox.setMinimum(2)
        spinBox.setSingleStep(1)
        page.addWidget(self.mag)
        page.addWidget(spinBox)
        self.magDialog.setLayout(page)
        spinBox.valueChanged.connect(self.mag.setMagLevel)
        self.imageArea.mouseMoved.connect(self.mag.newPosition)

        # Status bar
        self.statusBar = QtGui.QStatusBar(self)
        self.statusBar.showMessage("Status bar")
        # self.statusBar.setItemAlignment(1, Qt.AlignLeft|Qt.AlignVCenter)
        layout.addWidget(self.statusBar)
        self.imageArea.mouseMoved.connect(self.changeCords)

        # Set some initial values
        self.inverted = 0
        self.zoomLevelValue = 1
        # blinkThread

    def changeCords(self, x, y):
        statusStr = "["
        statusStr += str(int(x / self.zoomLevel)) + ","
        statusStr += str(int(y / self.zoomLevel))
        if (self.getCurrentDocument().getType() == "normal"):
            statusStr += "," + str(self.getCurrentDocument().data[int(y / self.zoomLevel), int(x / self.zoomLevel)])
        statusStr += "]"
        self.statusBar.showMessage(statusStr)

    def slotPopupRenameTab(self):
        self.renameTab(self.popupTabIndex)

    def slotPopupCloseTab(self):
        self.closeTab(self.popupTabIndex)

    def doTabContextMenu(self, point):
        print "DEBUG: doTabContextMenu called: " + str(point.x()) + ", " + str(point.y())
        tab = self.tabBar.tabAt(point)
        if (tab >= 0):
            print "DEBUG: doTabContextMenu - " + str(tab)
            # XXX: Allow popup on non selected tab
            self.popupTabIndex = tab
            self.tabpopup.exec_(QtGui.QCursor.pos())

    def renameTab(self, index):
        if (index == None):
            index = self.getCurrentDocIndex()
        if len(self.documents) == 0:
            return
        r = QtGui.QInputDialog.getText(self, "Rename", "Change name to", QtGui.QLineEdit.Normal,
                                       str(self.documents[index].getURL().getFileName()))
        if (r[1] == True and r[0] != None and str(r[0]) != "" and str(
                self.documents[index].getURL().getFileName()) != str(r[0])):
            print "Renaming tab and document url."
            url = URL(fullPath="/" + r[0])
            self.fixName(url)
            self.documents[index].url = url
            self.tabBar.setTabText(index, url.getFileName())
        self.popupTabIndex = None

    def switchedTab(self):
        self.imageArea.selectNone()
        if ((self.contrastDialog != None and self.contrastDialog.isVisible()) or (
                self.colorRGBContrastDialog != None and self.colorRGBContrastDialog.isVisible()) or (
                self.colorRGBLContrastDialog != None and self.colorRGBLContrastDialog.isVisible())):
            self.doContrastDialog()
        if self.imageInfoDialog != None and self.imageInfoDialog.isVisible():
            self.imageInfoDialog.documentChanged()
        self.window.changedEnabled()
        self.resizeRepaintScrollView()

    def setAllBrightRange(self, range):
        for document in self.documents:
            if document.getType() == "normal":
                document.setBrightRange(range)
                document.refresh()

    def getCurrentDocument(self):
        if len(self.documents) > 0:
            return self.documents[self.tabBar.currentIndex()]
        else:
            return None

    def getCurrentDocIndex(self):
        return self.tabBar.currentIndex()

    def saveDocument(self, url):
        print "saveDocument"
        try:
            ext = url.getExtension()
            if ext == ".fit" or ext == ".fts" or ext == ".fits":
                print "Saving Fits file"
                if self.getCurrentDocument().getType() == "normal":
                    print "normal document"
                    hdu = fits.PrimaryHDU(self.getCurrentDocument().data)
                    hdu.header["BACKGRD"] = (self.getCurrentDocument().getBrightRange()[0])
                    hdu.header["RANGE"] = (self.getCurrentDocument().getBrightRange()[1])
                    hdulist = fits.HDUList([hdu])
                    hdulist.writeto(url.getFullPath(), clobber=True)
                elif self.getCurrentDocument().getType() == "color_rgb" or self.getCurrentDocument().getType() == "color_rgbl":
                    if self.getCurrentDocument().getType() == "color_rgb":
                        abcolor = "RGB"
                    else:
                        abcolor = "RGBL"
                    print "color document"
                    hduR = fits.PrimaryHDU(self.getCurrentDocument().rgb[0].data)
                    hduR.header["ABCOLOR"] = (abcolor, "AstroBuffer color key")
                    hduR.header["BACKGRD"] = (self.getCurrentDocument().getBrightRange()[0][0])
                    hduR.header["RANGE"] = (self.getCurrentDocument().getBrightRange()[0][1])
                    hduG = fits.ImageHDU(self.getCurrentDocument().rgb[1].data)
                    hduG.header["ABCOLOR"] = (abcolor, "AstroBuffer color key")
                    hduG.header["BACKGRD"] = (self.getCurrentDocument().getBrightRange()[1][0])
                    hduG.header["RANGE"] = (self.getCurrentDocument().getBrightRange()[1][1])
                    hduB = fits.ImageHDU(self.getCurrentDocument().rgb[2].data)
                    hduB.header["ABCOLOR"] = (abcolor, "AstroBuffer color key")
                    hduB.header["BACKGRD"] = (self.getCurrentDocument().getBrightRange()[2][0])
                    hduB.header["RANGE"] = (self.getCurrentDocument().getBrightRange()[2][1])
                    if (self.getCurrentDocument().getType() == "color_rgb"):
                        hdulist = fits.HDUList([hduR, hduG, hduB])
                        hdulist.writeto(url.getFullPath(), clobber=True)
                    else:
                        hduL = fits.ImageHDU(self.getCurrentDocument().rgb[3].data)
                        hduL.header["ABCOLOR"] = (abcolor, "AstroBuffer color key")
                        hduL.header["BACKGRD"] = (self.getCurrentDocument().getBrightRange()[3][0])
                        hduL.header["RANGE"] = (self.getCurrentDocument().getBrightRange()[3][1])
                        hdulist = fits.HDUList([hduR, hduG, hduB, hduL])
                        hdulist.writeto(url.getFullPath(), clobber=True)
            else:
                good = self.getCurrentDocument().image.save(url.getFullPath())
                print good
                if good == False:
                    raise Exception("Save failed")
        except:
            raise

    def openDocument(self, url):
        # if open good
        data_header = []
        print "DEBUG: view.openDocument() - " + url.getFullPath()
        file = open(url.getFullPath())
        line = file.read(30)
        file.close()
        # TODO: Find a better way to detect if fits or sbig
        try:
            # FITS Test
            if line[0:6] == "SIMPLE" or line[0:8] == "XTENSION":
                # FITS
                # If using fits
                os.environ["NUMERIX"] = "numpy"
                hdulist = fits.open(url.getFullPath())
                for hdu in hdulist:
                    if hdu.name == "PRIMARY" or isinstance(hdu, fits.hdu.image.ImageHDU):
                        data_header.append([hdu.data, misc.fixFITSHeader(hdu.header)])
                hdulist.close()
            else:
                type = line.split("\x0a\x0d", 1)
                test = type[0].split(" ", 1)
                if test[1] == "Compressed Image" or test[1] == "Image":
                    # SBIG
                    try:
                        from cPySBIG import cPySBIG

                        sbig = cPySBIG(url.getFullPath())
                        data_header.append([sbig.getData(), misc.fixSBIGHeader(sbig.getHeaders())])
                    except ImportError:
                        raise ImageNullException("Couldn't read file, missing cPySBIG module.")
                else:
                    raise ImageNullException("Couldn't read file")
        except IndexError:
            raise ImageNullException("Couldn't read file")

        # self.addDocument(NormalDocument(self, url, data))
        # XXX: Consider if I should actually be doing this multiplying.
        # XXX: Used for fits images that might be small float numbers because
        # XXX: app expects larger ranges.
        abcolor = None
        try:
            values = data_header[0][1]["ABCOLOR"]
            abcolor = values[0].strip()
        except KeyError:
            pass
        except:
            raise
        if len(data_header) == 3 and abcolor != None and abcolor == "RGB":
            turl = URL(url=url)
            headers = [data_header[0][1], data_header[1][1], data_header[2][1]]
            self.addDocument(
                ColorRGBDocument(view=self, rgbData=[data_header[0][0], data_header[1][0], data_header[2][0]],
                                 headers=headers, url=turl))
        elif len(data_header) == 4 and abcolor != None and (abcolor == "LRGB" or abcolor == "RGBL"):
            turl = URL(url=url)
            headers = [data_header[0][1], data_header[1][1], data_header[2][1], data_header[3][1]]
            self.addDocument(ColorRGBLDocument(view=self,
                                               rgblData=[data_header[0][0], data_header[1][0], data_header[2][0],
                                                         data_header[3][0]], headers=headers, url=turl))
        else:
            for datas in data_header:
                turl = URL(url=url)
                datamax = datas[0].max()
                if datamax < 1000:
                    print "max is less than 1000"
                    r = 1000.0 / datamax
                    data = numpy.multiply(datas[0], r)
                self.addDocument(NormalDocument(view=self, data=numpy.cast[Config().getIDataType()](datas[0]), url=turl,
                                                header=datas[1]))

    def fixName(self, url):
        i = 0
        filename = str(url.getFileName())
        good = False
        tmpName = ""
        while good == False:
            good = True
            for doc in self.documents:
                if i == 0:
                    tmpName = filename
                else:
                    tmpName = filename + " (" + str(i) + ")"
                if doc.url.getFileName() == tmpName:
                    i += 1
                    good = False
        if i != 0:
            url.setFileName(filename + " (" + str(i) + ")")

    def addDocument(self, document):
        self.fixName(document.getURL())
        # XXX: Something is messed up, if you open a non-color then color, the non-color options are there.
        # XXX: This needs to be done better
        print "view.addDocument()"
        if len(self.documents) == 0:
            self.tabBar.removeTab(0)
        self.documents.append(document)
        self.tabBar.addTab(document.getURL().getFileName())
        print "view.addDocument() - 2"
        self.tabBar.setCurrentIndex(len(self.documents) - 1)
        print "view.addDocument() - 3"
        self.switchedTab()
        self.resizeRepaintScrollView()

    def resizeRepaintScrollView(self):
        doc = self.getCurrentDocument()
        if doc != None:
            self.imageArea.resize(doc.getPixmap().width(), doc.getPixmap().height())
        else:
            self.imageArea.resize(0, 0)
        self.imageArea.update()
        self.mag.update()

    def invert(self):
        if self.inverted == 0:
            self.inverted = 1
        else:
            self.inverted = 0
        self.updateDocPixmaps()

    def setZoomLevel(self, amount):
        self.imageArea.selectNone()
        self.zoomLevel = amount
        self.updateDocPixmaps()

    def updateDocPixmaps(self):
        for doc in self.documents:
            doc.regenPixmap()
        self.resizeRepaintScrollView()

    def closeTab(self, index=None):
        if index == None:
            index = self.tabBar.currentIndex()
        if len(self.documents) > 0:
            t = self.documents[index]
            t.undo.cleanup()
            del self.documents[index]
            self.tabBar.removeTab(index)
            self.resizeRepaintScrollView()
            if len(self.documents) == 0:
                self.tabBar.addTab("Empty")
            self.switchedTab()
        self.popupTabIndex = None

    def closeAllTabs(self):
        docl = range(len(self.documents))
        docl.reverse()
        for i in docl:
            del self.documents[i]
        docl = range(self.tabBar.count())
        docl.reverse()
        for i in docl:
            self.tabBar.removeTab(i)
        self.tabBar.addTab("Empty")
        self.switchedTab()

    def setBlinksPerSecond(self, amount):
        self.blinksPerSecond = amount
        print "Doing set blinks per second"
        print self.blinkThread.running()
        if self.blinksPerSecond != 0 and self.blinkThread.running() == 0:
            self.blinkThread.start()
            print "After thread start"

    def doBlink(self):
        self.app.lock()
        currentIndex = self.tabBar.currentIndex()
        tab = 0
        if currentIndex < self.tabBar.count() - 1:
            currentIndex += 1
            tabIdx = currentIndex
        self.tabBar.setCurrentIndex(tabIdx)
        self.resizeRepaintScrollView()
        self.app.unlock()

    def doContrastDialog(self):
        if self.getCurrentDocument() == None:
            if self.colorRGBContrastDialog != None:
                self.colorRGBContrastDialog.hide()
            if self.colorRGBLContrastDialog != None:
                self.colorRGBLContrastDialog.hide()
            if self.contrastDialog != None:
                self.contrastDialog.hide()
            return
        if self.getCurrentDocument().getType() == "color_rgb":
            if self.contrastDialog != None:
                self.contrastDialog.hide()
            if self.colorRGBContrastDialog == None:
                self.colorRGBContrastDialog = ColorRGBContrastDialog(self)
            else:
                self.colorRGBContrastDialog.documentChanged()
            if self.colorRGBLContrastDialog != None:
                self.colorRGBLContrastDialog.hide()
            self.colorRGBContrastDialog.show()
        elif self.getCurrentDocument().getType() == "color_rgbl":
            if self.contrastDialog != None:
                self.contrastDialog.hide()
            if self.colorRGBContrastDialog != None:
                self.colorRGBContrastDialog.hide()
            if self.colorRGBLContrastDialog == None:
                self.colorRGBLContrastDialog = ColorRGBLContrastDialog(self)
            else:
                self.colorRGBLContrastDialog.documentChanged()
            self.colorRGBLContrastDialog.show()
        else:
            if self.contrastDialog == None:
                self.contrastDialog = ContrastDialog(self)
            else:
                self.contrastDialog.documentChanged()
            if self.colorRGBContrastDialog != None:
                self.colorRGBContrastDialog.hide()
            if self.colorRGBLContrastDialog != None:
                self.colorRGBLContrastDialog.hide()
            self.contrastDialog.show()

    def doImageInfoDialog(self):
        if self.imageInfoDialog == None:
            self.imageInfoDialog = ImageInfoDialog(self)
        else:
            self.imageInfoDialog.documentChanged()
        self.imageInfoDialog.show()


class ImageNullException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value


class Blinker(QtCore.QThread):
    def __init__(self, view):
        QtCore.QThread.__init__(self)
        self.view = view

    def run(self):
        while self.view.blinksPerSecond != 0:
            self.view.doBlink()
            self.msleep(1000 / self.view.blinksPerSecond)


class ImageLabel(QtGui.QWidget):
    mouseMoved = QtCore.pyqtSignal(int, int)

    def __init__(self, view):
        QtGui.QWidget.__init__(self)
        self.setMouseTracking(1)
        self.setSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Maximum)
        self.view = view
        self.pressX = None
        self.pressY = None
        self.releaseX = None
        self.releaseY = None
        self.hasReleased = False
        self.setCursor(QtCore.Qt.CrossCursor)
        self.timer = time.time()

    def selectNone(self):
        self.pressX = None
        self.pressY = None
        self.releaseX = None
        self.releaseY = None

    def getSelection(self):
        if self.pressX == None or self.pressY == None or self.releaseX == None or self.releaseY == None:
            return None
        zl = self.view.zoomLevel
        x = int(self.pressX / zl)
        y = int(self.pressY / zl)
        width = int(self.releaseX / zl - self.pressX / zl)
        height = int(self.releaseY / zl - self.pressY / zl)
        return [x, y, width, height]

    def mousePressEvent(self, event):
        doc = self.view.getCurrentDocument()
        if doc != None:
            pixmap = doc.getPixmap()
            if event.x() < pixmap.width() and event.y() < pixmap.height() and event.x() >= 0 and event.y() >= 0:
                self.pressX = event.x()
                self.pressY = event.y()
                self.releaseX = None
                self.releaseY = None
                self.hasReleased = False

    def mouseReleaseEvent(self, event):
        doc = self.view.getCurrentDocument()
        if doc != None:
            pixmap = doc.getPixmap()
            if event.x() < pixmap.width():
                self.releaseX = event.x()
            else:
                self.releaseX = pixmap.width() - 1
            if event.y() < pixmap.height():
                self.releaseY = event.y()
            else:
                self.releaseY = pixmap.height() - 1
            if self.releaseX < 0:
                self.releaseX = 0
            if self.releaseY < 0:
                self.releaseY = 0

        if self.pressX == self.releaseX or self.pressY == self.releaseY:
            self.pressX = None
            self.pressY = None
        self.hasReleased = True
        self.update()

    def paintEvent(self, event):
        if self.view.getCurrentDocument() != None:
            pixmap = self.view.getCurrentDocument().getPixmap()
            painter = QtGui.QPainter(self)
            painter.drawPixmap(0, 0, pixmap)
            if self.pressX != None and self.pressY != None and self.releaseX != None and self.releaseY != None:
                if self.pressX < pixmap.width() and self.pressY < pixmap.height() and self.releaseX < pixmap.width() and self.releaseY < pixmap.height():
                    painter.setPen(QtGui.QColor("hot pink"))
                    w = self.releaseX - self.pressX
                    h = self.releaseY - self.pressY
                    if self.pressX + w == 0:
                        w += 1
                    if self.pressY + h == 0:
                        h += 1
                    # painter.drawRect(self.pressX, self.pressY, self.releaseX-self.pressX, self.releaseY - self.pressY)
                    painter.drawRect(self.pressX, self.pressY, w, h)
                else:
                    self.pressX = None
                    self.pressY = None
                    self.releaseX = None
                    self.releaseY = None

    def mouseMoveEvent(self, event):
        doc = self.view.getCurrentDocument()

        if doc != None:
            pixmap = doc.getPixmap()
            if self.hasReleased == False:
                if event.x() < pixmap.width():
                    self.releaseX = event.x()
                else:
                    self.releaseX = pixmap.width() - 1
                if event.y() < pixmap.height():
                    self.releaseY = event.y()
                else:
                    self.releaseY = pixmap.height() - 1
                if self.releaseX < 0:
                    self.releaseX = 0
                if self.releaseY < 0:
                    self.releaseY = 0

                if self.pressX != None and self.pressY != None:
                    self.update()

                    # Need to do this outside mouse move, because you sh0uld be able to hold it on the outside
                #                    if(time.time()-self.timer > 0.10):
                #                        p=self.pos()
                #                        vsize = self.view.scrollArea.viewport().size()
                #                        dx=1.0
                #                        dy=1.0
                #                        if(event.x() > -p.x()):
                #                            dx=float(event.x() - vsize.width()-p.x())/2000.0
                #                            if(dx < 0):
                #                                dx=1.0
                #                        else:
                #                            dx=-(float(-p.x()-event.x())/2000.0)
                #                            if(dx > 0):
                #                                dx=1.0
                #                        if(event.y() > -p.y()):
                #                            dy=float(event.y() - vsize.height()-p.y())/2000.0
                #                            if(dx > 0):
                #                                dx=1.0
                #                        else:
                #                            dy=-(float(-p.y() - event.y())/2000.0)
                #                            if(dy > 0):
                #                                dy=1.0
                #                        print "-- "+str(event.x())+", "+str(event.y())
                #
                #                        sb=self.view.scrollArea.horizontalScrollBar()
                #                        a=sb.sliderPosition()+int(dx*float(sb.maximum()-sb.minimum()))
                #                        if(a < 0):
                #                            a=0
                #                        if(a > sb.maximum()):
                #                            a=sb.maximum()
                #                        print "-- a = "+str(a)
                #                        sb.setValue(a)
                #
                #                        sb=self.view.scrollArea.verticalScrollBar()
                #                        a=sb.sliderPosition()+int(dy*float(sb.maximum()-sb.minimum()))
                #                        if(a < 0):
                #                            a=0
                #                        if(a > sb.maximum()):
                #                            a=sb.maximum()
                #                        print "-- a = "+str(a)
                #                        sb.setValue(a)
                #
                #                    self.timer=time.time()
            if event.x() < pixmap.width() and event.y() < pixmap.height() and event.x() >= 0 and event.y() >= 0:
                self.mouseMoved.emit(event.x(), event.y())


class MagWidget(QtGui.QWidget):
    def __init__(self, view):
        QtGui.QWidget.__init__(self)
        self.view = view
        self.x = 0
        self.y = 0
        self.magLevel = 2
        self.setMinimumSize(150, 150)
        # self.setMaximumSize(150,150)

    def setMagLevel(self, magLevel):
        self.magLevel = magLevel
        self.update()

    def newPosition(self, x, y):
        self.x = x
        self.y = y
        if self.isVisible():
            self.update()

    def paintEvent(self, event):
        width = self.size().width()
        height = self.size().height()
        doc = self.view.getCurrentDocument()
        if doc != None:
            m = QtGui.QMatrix()
            m.scale(self.magLevel, self.magLevel)
            p = QtGui.QPainter(self)
            p.setWorldTransform(QtGui.QTransform(m))
            pixmap = doc.getPixmap()
            ox = 0
            oy = 0
            sx = self.x - (width / (2 * self.magLevel))
            sy = self.y - (height / (2 * self.magLevel))
            sh = height / self.magLevel
            sw = width / self.magLevel
            if (sx < 0):
                ox = abs(sx)
                sx = 0
                sw = sw - ox
            if (sy < 0):
                oy = abs(sy)
                sy = 0
                sh = sh - oy
            p.drawPixmap(ox, oy, pixmap, sx, sy, sw, sh)
