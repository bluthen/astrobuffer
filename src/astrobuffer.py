#!/bin/env python2

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
import gc
import sys
import traceback
from StringIO import StringIO
import re

from PyQt4 import QtCore, QtGui

from misc import URL
from view import View, ImageNullException
from simpleDialogs import ScaleDialog, ShiftDialog, ImageInfoDialog, RotateDialog, QuadraticSumDialog, SumDialog, \
    SubtractDialog, AverageDialog, DivideDialog, BinDialog, MultiplyDialog, LesserDialog, OKDialog, NewDialog, \
    PowerDialog, ResizeCanvasDialog, DDPDialog
from alignDialogs import AlignDialog1, MakeCenterDialog
from colorDialogs import RGBDialog
from convolutionDialog import ConvolutionDialog
from settingsDialog import SettingsDialog
from config import Config
from widgets import SelectAction, OpenRecentAction
from aboutDialog import AboutDialog
import math
import numpy
import imageLib
from documents import NormalDocument


class AstroBufferWindow(QtGui.QMainWindow):
    def __init__(self, app):
        QtGui.QMainWindow.__init__(self)
        self.app = app
        # self.setIcon(QPixmap('icons/astrobuffer-128.png'))

        #
        # File
        #
        self.fileMenu = self.menuBar().addMenu("&File")
        self.fileNew = QtGui.QAction("&New", self.fileMenu, shortcut=QtGui.QKeySequence.New, triggered=self.slotFileNew)
        self.fileMenu.addAction(self.fileNew)

        self.fileOpen = QtGui.QAction("&Open...", self.fileMenu, shortcut=QtGui.QKeySequence.Open,
                                      triggered=self.slotFileOpen)
        self.fileOpen.setStatusTip("Open a file")
        self.fileMenu.addAction(self.fileOpen)

        self.fileOpenRecent = OpenRecentAction()
        self.fileMenu.addMenu(self.fileOpenRecent)
        self.fileOpenRecent.openRecent.connect(self.slotFileOpenRecent)

        self.fileMenu.addSeparator()

        self.fileSaveAs = QtGui.QAction("&Save As", self.fileMenu, shortcut=QtGui.QKeySequence.SaveAs,
                                        triggered=self.slotFileSaveAs)
        self.fileMenu.addAction(self.fileSaveAs)

        self.fileMenu.addSeparator()

        self.fileClose = QtGui.QAction("&Close", self.fileMenu, shortcut=QtGui.QKeySequence.Close,
                                       triggered=self.slotFileClose)
        self.fileMenu.addAction(self.fileClose)
        self.fileClose.setEnabled(0)

        self.fileCloseAll = QtGui.QAction("&Close All Tabs", self.fileMenu, triggered=self.slotFileCloseAll)
        self.fileMenu.addAction(self.fileCloseAll)
        self.fileCloseAll.setEnabled(0)

        self.fileMenu.addSeparator()

        self.fileQuit = QtGui.QAction("&Quit", self.fileMenu, shortcut=QtGui.QKeySequence.mnemonic("&Quit"),
                                      triggered=self.slotFileQuit)
        self.fileMenu.addAction(self.fileQuit)

        #
        # Edit
        #
        self.editMenu = self.menuBar().addMenu("&Edit")
        self.editUndo = QtGui.QAction("&Undo", self.editMenu, shortcut=QtGui.QKeySequence.Undo,
                                      triggered=self.slotEditUndo)
        self.editMenu.addAction(self.editUndo)

        self.editRedo = QtGui.QAction("&Redo", self.editMenu, shortcut=QtGui.QKeySequence.Redo,
                                      triggered=self.slotEditRedo)
        self.editMenu.addAction(self.editRedo)

        self.editMenu.addSeparator()

        self.clipboardDoc = None
        self.editCopy = QtGui.QAction("&Copy", self.editMenu, shortcut=QtGui.QKeySequence.Copy,
                                      triggered=self.slotEditCopy)
        self.editMenu.addAction(self.editCopy)

        self.editPaste = QtGui.QAction("&Paste", self.editMenu, shortcut=QtGui.QKeySequence.Paste,
                                       triggered=self.slotEditPaste)
        self.editMenu.addAction(self.editPaste)
        self.editPaste.setEnabled(0)

        #
        # View
        #

        self.viewMenu = self.menuBar().addMenu("&View")
        self.viewActualSize = QtGui.QAction("&Actual Size", self.viewMenu, triggered=self.slotViewActualSize)
        self.viewMenu.addAction(self.viewActualSize)
        self.viewActualSize.setEnabled(0)

        self.viewFitToPage = QtGui.QAction("&Fit to Page", self.viewMenu, triggered=self.slotViewFitToPage)
        self.viewMenu.addAction(self.viewFitToPage)
        self.viewFitToPage.setEnabled(0)

        self.viewZoomIn = QtGui.QAction("Zoom &In", self.viewMenu, shortcut=QtGui.QKeySequence.ZoomIn,
                                        triggered=self.slotViewZoomIn)
        self.viewMenu.addAction(self.viewZoomIn)
        self.viewZoomIn.setEnabled(0)

        self.viewZoomOut = QtGui.QAction("Zoom &Out", self.viewMenu, shortcut=QtGui.QKeySequence.ZoomOut,
                                         triggered=self.slotViewZoomOut)
        self.viewMenu.addAction(self.viewZoomOut)
        self.viewZoomOut.setEnabled(0)

        # XXX
        self.percentExp = re.compile('%')
        self.viewZoom = SelectAction("Zoom", "12.5%,25%,50%,100%,150%,200%,250%,300%", 3)
        self.viewMenu.addMenu(self.viewZoom)
        self.viewZoom.triggeredItem.connect(self.slotViewZoom)
        self.viewZoom.setCurrentItem(3)
        self.viewZoom.setEnabled(0)
        self.viewMagDialog = QtGui.QAction("Show Mag Dialog", self.viewMenu, triggered=self.slotViewMagDialog)
        self.viewMenu.addAction(self.viewMagDialog)
        self.viewMagDialog.setEnabled(1)

        self.viewImageInfo = QtGui.QAction("Image Info", self.viewMenu, triggered=self.slotViewImageInfo)
        self.viewMenu.addAction(self.viewImageInfo)
        self.viewImageInfo.setEnabled(0)

        #
        # Tools
        #

        #
        # Visual
        #

        self.inverted = 0
        self.visualMenu = self.menuBar().addMenu("&Visual")
        self.toolsInvert = QtGui.QAction("Invert Black<->White", self.visualMenu, triggered=self.slotToolsInvert)
        self.visualMenu.addAction(self.toolsInvert)
        self.toolsInvert.setEnabled(0)

        self.visualMenu.addSeparator()

        self.toolsContrast = QtGui.QAction("Adjust Contrast", self.visualMenu, triggered=self.slotToolsContrast)
        self.visualMenu.addAction(self.toolsContrast)
        self.toolsContrast.setEnabled(0)

        self.toolsDDP = QtGui.QAction("DDP", self.visualMenu, triggered=self.slotToolsDDP)
        self.visualMenu.addAction(self.toolsDDP)

        self.visualMenu.addSeparator()

        self.toolsRGB = QtGui.QAction("RGB", self.visualMenu, triggered=self.slotToolsRGB)
        self.visualMenu.addAction(self.toolsRGB)

        self.toolsDRGB = QtGui.QAction("Decompose RGB", self.visualMenu, triggered=self.slotToolsDRGB)
        self.visualMenu.addAction(self.toolsDRGB)

        # XXX
        # self.toolsBlink= QtGui.QAction("Blink Images", triggered=self.slotToolsBlink)
        # self.visualMenu.addAction(self.toolsBlink)
        # self.toolsBlink = KSelectAction(i18n("Blink Images"), KShortcut.null(), self.actionCollection(), "tools_blink")
        # self.toolsBlink.activated.connect(self.slotToolsBlink)
        # blnkStr = ""
        # for i in range(11):
        #    blnkStr += str(i)+" blinks/second,"
        # self.toolsBlink.setItems(QStringList.split(",", blnkStr))
        # self.toolsBlink.setCurrentItem(0)
        # self.toolsBlink.setEnabled(0)

        #
        # Math
        #

        self.mathMenu = self.menuBar().addMenu("&Math")

        self.toolsSum = QtGui.QAction("Sum", self.mathMenu, triggered=self.slotToolsSum)
        self.mathMenu.addAction(self.toolsSum)

        self.toolsQuadraticSum = QtGui.QAction("Quadratic Sum", self.mathMenu, triggered=self.slotToolsQuadraticSum)
        self.mathMenu.addAction(self.toolsQuadraticSum)

        self.toolsSubtract = QtGui.QAction("Subtract", self.mathMenu, triggered=self.slotToolsSubtract)
        self.mathMenu.addAction(self.toolsSubtract)

        self.toolsAverage = QtGui.QAction("Average", self.mathMenu, triggered=self.slotToolsAverage)
        self.mathMenu.addAction(self.toolsAverage)

        self.toolsDivide = QtGui.QAction("Divide(flat)", self.mathMenu, triggered=self.slotToolsDivide)
        self.mathMenu.addAction(self.toolsDivide)

        self.toolsMultiply = QtGui.QAction("Multiply", self.mathMenu, triggered=self.slotToolsMultiply)
        self.mathMenu.addAction(self.toolsMultiply)

        self.toolsLesser = QtGui.QAction("Lesser", self.mathMenu, triggered=self.slotToolsLesser)
        self.mathMenu.addAction(self.toolsLesser)

        self.mathMenu.addSeparator()

        self.toolsConvolution = QtGui.QAction("Convolution", self.mathMenu, triggered=self.slotToolsConvolution)
        self.mathMenu.addAction(self.toolsConvolution)

        self.toolsPower = QtGui.QAction("Power", self.mathMenu, triggered=self.slotToolsPower)
        self.mathMenu.addAction(self.toolsPower)

        #
        # Manipulate
        #

        self.manMenu = self.menuBar().addMenu("M&anipulate")

        self.toolsResizeCanvas = QtGui.QAction("Resize Canvas", self.manMenu, triggered=self.slotToolsResizeCanvas)
        self.manMenu.addAction(self.toolsResizeCanvas)

        self.toolsScale = QtGui.QAction("Scale", self.manMenu, triggered=self.slotToolsScale)
        self.manMenu.addAction(self.toolsScale)

        self.toolsShift = QtGui.QAction("Shift", self.manMenu, triggered=self.slotToolsShift)
        self.manMenu.addAction(self.toolsShift)

        self.toolsRotate = QtGui.QAction("Rotate", self.manMenu, triggered=self.slotToolsRotate)
        self.manMenu.addAction(self.toolsRotate)

        self.toolsBin = QtGui.QAction("Bin Pixels", self.manMenu, triggered=self.slotToolsBin)
        self.manMenu.addAction(self.toolsBin)

        self.manMenu.addSeparator()

        self.toolsMakeCenter = QtGui.QAction("Make Center", self.manMenu, triggered=self.slotToolsMakeCenter)
        self.manMenu.addAction(self.toolsMakeCenter)

        self.toolsAlign = QtGui.QAction("Align Images", self.manMenu, triggered=self.slotToolsAlign)
        self.manMenu.addAction(self.toolsAlign)

        self.manMenu.addSeparator()

        self.toolsDuplicate = QtGui.QAction("Duplicate", self.manMenu, triggered=self.slotToolsDuplicate)
        self.manMenu.addAction(self.toolsDuplicate)

        #        self.toolsGC = QtGui.QAction("GC", self.manMenu)
        #        self.toolsGC.triggered.connect(self.slotToolsGC)
        #        self.manMenu.addAction(self.toolsGC)
        #        self.toolsGC.setEnabled(1)

        #
        # Settings
        #
        self.settingsMenu = self.menuBar().addMenu("&Settings")
        self.settingsPreferences = QtGui.QAction("Preferences", self.settingsMenu,
                                                 triggered=self.slotSettingsPreferences)
        self.settingsMenu.addAction(self.settingsPreferences)

        #
        # Help
        #

        self.helpMenu = self.menuBar().addMenu("&Help")
        self.helpAbout = QtGui.QAction("About AstroBuffer", self.helpMenu, triggered=self.slotHelpAbout)
        self.helpMenu.addAction(self.helpAbout)


        # XXX
        self.view = View(self, app)
        self.setCentralWidget(self.view)

        self.setWindowTitle("AstroBuffer")

        self.slotFileCloseAll()
        # XXX
        size = Config().getGeometry()
        if size.width() > 100:
            self.resize(size)
        else:
            self.resize(QtCore.QSize(400, 400))

        self.app.aboutToQuit.connect(self.queryExit)

    def closeEvent(self, event):
        # XXX: If any image modified prompt if want to really exit
        self.app.quit()

    def queryExit(self):
        print "queryExit()"
        for doc in self.view.documents:
            doc.undo.cleanup()
        Config().setGeometry(self.size())
        # self.fileOpenRecent.saveEntries(Config().config(), QString("Recent"))
        # return True

    def changedEnabled(self):
        # XXX: Menus don't get updated if load noncolor then color
        self.disable3Actions()
        self.disable2Actions()
        self.disable1Actions()
        if len(self.view.documents) >= 1:
            self.enable1Actions()
            print "changedEnabled() - " + str(len(self.view.documents)) + " " + str(
                self.view.getCurrentDocument().isColor())
            if self.view.getCurrentDocument().isColor() == False:
                print "changedEnabled() - Enabling noncolor options"
                if len(self.view.documents) >= 2:
                    self.enable2Actions()
                if len(self.view.documents) >= 3:
                    self.enable3Actions()
            if self.view.getCurrentDocument().isColor() == True:
                print "changedEnabled() - Enabling color options"
                self.enableColorActions()

    def enableColorActions(self):
        self.toolsDRGB.setEnabled(1)

    def enable1Actions(self):
        self.fileClose.setEnabled(1)
        self.fileSaveAs.setEnabled(1)
        self.fileCloseAll.setEnabled(1)
        self.editUndo.setEnabled(1)
        self.editRedo.setEnabled(1)
        self.editCopy.setEnabled(1)
        self.viewActualSize.setEnabled(1)
        self.viewZoomIn.setEnabled(1)
        self.viewZoomOut.setEnabled(1)
        self.viewZoom.setEnabled(1)
        self.viewImageInfo.setEnabled(1)
        self.toolsInvert.setEnabled(1)
        self.toolsContrast.setEnabled(1)
        self.toolsResizeCanvas.setEnabled(1)
        self.toolsScale.setEnabled(1)
        self.toolsShift.setEnabled(1)
        self.toolsRotate.setEnabled(1)
        self.toolsConvolution.setEnabled(1)
        self.toolsPower.setEnabled(1)
        self.toolsDDP.setEnabled(1)
        if self.view.getCurrentDocument().isColor() == False:
            self.toolsMakeCenter.setEnabled(1)
            self.toolsBin.setEnabled(1)
        self.toolsDuplicate.setEnabled(1)
        # self.toolsDataReduction.setEnabled(1)
        # self.toolsShowKnown.setEnabled(1)

    def disable1Actions(self):
        print "disable1Actions()"
        self.fileClose.setEnabled(0)
        self.fileSaveAs.setEnabled(0)
        self.fileCloseAll.setEnabled(0)
        self.editUndo.setEnabled(0)
        self.editRedo.setEnabled(0)
        self.editCopy.setEnabled(0)
        self.viewActualSize.setEnabled(0)
        self.viewZoomIn.setEnabled(0)
        self.viewZoomOut.setEnabled(0)
        self.viewZoom.setEnabled(0)
        self.viewImageInfo.setEnabled(0)
        self.toolsInvert.setEnabled(0)
        self.toolsContrast.setEnabled(0)
        self.toolsResizeCanvas.setEnabled(0)
        self.toolsScale.setEnabled(0)
        self.toolsShift.setEnabled(0)
        self.toolsRotate.setEnabled(0)
        self.toolsConvolution.setEnabled(0)
        self.toolsPower.setEnabled(0)
        self.toolsBin.setEnabled(0)
        self.toolsDDP.setEnabled(0)
        self.toolsMakeCenter.setEnabled(0)
        self.toolsDRGB.setEnabled(0)
        self.toolsDuplicate.setEnabled(0)
        # self.toolsDataReduction.setEnabled(0)
        # self.toolsShowKnown.setEnabled(0)

    def enable2Actions(self):
        # self.toolsBlink.setEnabled(1)
        self.toolsAlign.setEnabled(1)
        self.toolsSum.setEnabled(1)
        self.toolsQuadraticSum.setEnabled(1)
        self.toolsSubtract.setEnabled(1)
        self.toolsAverage.setEnabled(1)
        self.toolsDivide.setEnabled(1)
        self.toolsMultiply.setEnabled(1)
        self.toolsLesser.setEnabled(1)
        # self.toolsColorCompare.setEnabled(1)
        # self.toolsMovingDetection.setEnabled(1)

    def disable2Actions(self):
        print "disable2Actions()"
        # self.toolsBlink.setEnabled(0)
        self.toolsAlign.setEnabled(0)
        self.toolsSum.setEnabled(0)
        self.toolsQuadraticSum.setEnabled(0)
        self.toolsSubtract.setEnabled(0)
        self.toolsAverage.setEnabled(0)
        self.toolsDivide.setEnabled(0)
        self.toolsMultiply.setEnabled(0)
        self.toolsLesser.setEnabled(0)
        # self.toolsColorCompare.setEnabled(0)
        # self.toolsMovingDetection.setEnabled(0)

    def enable3Actions(self):
        self.toolsRGB.setEnabled(1)

    def disable3Actions(self):
        print "disable3Actions()"
        self.toolsRGB.setEnabled(0)

    def slotFileOpen(self):
        try:
            dir = Config().getSaveDir()
            fileNames = QtGui.QFileDialog.getOpenFileNames(self, "Open Image", dir,
                                                           "FITS and SBIG (*.fit *.fts *.fits *.st9 *.st7)")
            print "slotFileOpen() -- fileNames"
            print fileNames
            count = 0
            for file in fileNames:
                url = URL(fullPath=str(file))
                if not url.empty():
                    self.view.openDocument(url)
                    self.fileOpenRecent.openedFile(url.getFullPath())
                if count == 0:
                    Config().setSaveDir(url.getDirPath())
                count = count + 1
        except Exception, e:
            ok = OKDialog(self, "Problem opening file(s)", e.__str__())
            traceback.print_exc(file=sys.stdout)
            ok.show()

    def slotFileOpenRecent(self, file):
        url = URL(fullPath=str(file))
        try:
            self.view.openDocument(url)
            self.fileOpenRecent.openedFile(url.getFullPath())
        except ImageNullException:
            ok = OKDialog(self, "Problem opening file(s)", "Could not read file.")
            ok.show()

    def slotFileSaveAs(self):
        try:
            supportedImages = QtGui.QImageWriter.supportedImageFormats()
            imgFilters = ""
            c = 0
            for i in supportedImages:
                if c != 0:
                    imgFilters += " "
                imgFilters += "*." + str(i)
                c += 1
            if imgFilters:
                imgFilters = "FITS (*.fit *.fts *.fits);;Images (" + imgFilters + ")"
            else:
                imgFilters = "FITS (*.fit *.fts *.fits)"
            # Remember previous save spot
            dir = Config().getSaveDir()
            filename = str(QtGui.QFileDialog.getSaveFileName(self, "Save Image", dir, imgFilters))
            if filename:
                print "-- Save: *" + filename + "*"
                url = URL(fullPath=filename)
                if not url.empty():
                    self.view.saveDocument(url)
                    Config().setSaveDir(url.getDirPath())
        except:
            ok = OKDialog(self, "Problem saving file", "Could not save file.")
            ok.show()
            raise

    def slotFileNew(self):
        t = NewDialog(self)
        t.show()

    def slotFileClose(self):
        self.view.closeTab()
        if len(self.view.documents) < 1:
            self.disable1Actions()
        if len(self.view.documents) < 2:
            self.disable2Actions()
        if len(self.view.documents) < 3:
            self.disable3Actions()

    def slotFileCloseAll(self):
        self.view.closeAllTabs()
        self.disable3Actions()
        self.disable2Actions()
        self.disable1Actions()

    def slotFileQuit(self):
        self.app.postEvent(self, QtGui.QCloseEvent())

    def slotEditUndo(self):
        self.view.getCurrentDocument().undo.undo(self.view.getCurrentDocument())
        # TODO: Probably check if an actuall undo was done before refreshing
        self.view.getCurrentDocument().refresh(True)

    def slotEditRedo(self):
        self.view.getCurrentDocument().undo.redo(self.view.getCurrentDocument())
        # TODO: Probably check if an actuall redo was done before refreshing
        self.view.getCurrentDocument().refresh(True)

    def slotEditCopy(self):
        self.editPaste.setEnabled(1);
        s = self.view.imageArea.getSelection()
        if s == None:
            self.clipboardDoc = self.view.getCurrentDocument().copy()
        else:
            self.clipboardDoc = self.view.getCurrentDocument().copy(s[0], s[1], s[2], s[3])

    def slotEditPaste(self):
        self.view.addDocument(self.clipboardDoc.copy())

    def slotViewActualSize(self):
        self.viewZoom.setCurrentItem(3)
        self.slotViewZoom(self.viewZoom.getCurrentItem())

    def slotViewFitToPage(self):
        pass

    def slotViewZoomIn(self):
        self.viewZoom.setCurrentItem(self.viewZoom.getCurrentIdx() + 1)
        self.slotViewZoom(self.viewZoom.getCurrentItem())

    def slotViewZoomOut(self):
        self.viewZoom.setCurrentItem(self.viewZoom.getCurrentIdx() - 1)
        self.slotViewZoom(self.viewZoom.getCurrentItem())

    def slotViewZoom(self, action):
        amount = action.text()
        famount = self.percentExp.sub('', str(amount))
        self.view.setZoomLevel(float(famount) / 100.0)
        if self.viewZoom.getCurrentIdx() == 0:
            self.viewZoomOut.setEnabled(0)
        else:
            self.viewZoomOut.setEnabled(1)
        if self.viewZoom.getCurrentIdx() == self.viewZoom.size() - 1:
            self.viewZoomIn.setEnabled(0)
        else:
            self.viewZoomIn.setEnabled(1)

    def slotViewMagDialog(self):
        self.view.magDialog.show()

    def slotViewImageInfo(self):
        self.view.doImageInfoDialog()

    def slotToolsInvert(self):
        self.view.invert()

    def slotToolsContrast(self):
        self.view.doContrastDialog()

    def slotToolsBlink(self, numBlnks):
        self.view.setBlinksPerSecond(int(numBlnks))

    def slotToolsResizeCanvas(self):
        rcd = ResizeCanvasDialog(self.view)
        rcd.show()

    def slotToolsScale(self):
        sd = ScaleDialog(self.view)
        sd.show()

    def slotToolsShift(self):
        sd = ShiftDialog(self.view)
        sd.show()

    def slotToolsRotate(self):
        rd = RotateDialog(self.view)
        rd.show()

    def slotToolsConvolution(self):
        cd = ConvolutionDialog(self.view)
        cd.show()

    def slotToolsPower(self):
        pd = PowerDialog(self.view)
        pd.show()

    def slotToolsDDP(self):
        dd = DDPDialog(self.view)
        dd.show()

    def slotToolsMakeCenter(self):
        mcd = MakeCenterDialog(self.view)
        mcd.show()

    def slotToolsAlign(self):
        ad = AlignDialog1(self.view)
        ad.show()

    def slotToolsSum(self):
        sd = SumDialog(self.view)
        sd.show()

    def slotToolsQuadraticSum(self):
        qsd = QuadraticSumDialog(self.view)
        qsd.show()

    def slotToolsSubtract(self):
        sd = SubtractDialog(self.view)
        sd.show()

    def slotToolsAverage(self):
        ad = AverageDialog(self.view)
        ad.show()

    def slotToolsDivide(self):
        dd = DivideDialog(self.view)
        dd.show()

    def slotToolsMultiply(self):
        md = MultiplyDialog(self.view)
        md.show()

    def slotToolsBin(self):
        md = BinDialog(self.view)
        md.show()

    def slotToolsLesser(self):
        ld = LesserDialog(self.view)
        ld.show()

    def slotToolsRGB(self):
        rgbd = RGBDialog(self.view)
        rgbd.show()

    def slotToolsDRGB(self):
        if self.view.getCurrentDocument().isColor() == True:
            doc = self.view.getCurrentDocument()
            br = doc.getBrightRange()
            rdoc = NormalDocument(self.view, numpy.array(doc.rgb[0].data), brightRange=br[0], url=URL("/tmp/red"))
            self.view.addDocument(rdoc)
            gdoc = NormalDocument(self.view, numpy.array(doc.rgb[1].data), brightRange=br[1], url=URL("/tmp/green"))
            self.view.addDocument(gdoc)
            bdoc = NormalDocument(self.view, numpy.array(doc.rgb[2].data), brightRange=br[2], url=URL("/tmp/blue"))
            self.view.addDocument(bdoc)
            if doc.getType() == "color_rgbl":
                ldoc = NormalDocument(self.view, numpy.array(doc.rgb[3].data), brightRange=br[3],
                                      url=URL("/tmp/luminance"))
                self.view.addDocument(ldoc)

    def slotToolsDuplicate(self):
        doc = self.view.getCurrentDocument().copy()
        self.view.addDocument(doc)

    def slotToolsGC(self):
        gc.set_debug(gc.DEBUG_LEAK)
        gc.collect()

    def slotSettingsShowToolBar(self):
        if self.settingsShowToolBar.isChecked():
            self.toolBar("mainToolBar").show()
        else:
            self.toolBar("mainToolBar").hide()

    def slotSettingsConfigureToolbars(self):
        pass

    def slotSettingsPreferences(self):
        # XXX
        # if KConfigDialog.showDialog("settings"):
        #    return
        sd = SettingsDialog(self)
        sd.show()

    def slotHelpAbout(self):
        ad = AboutDialog(self)
        ad.show()


def excepthook(type, value, trackbackobj):
    lines = traceback.format_exception(type, value, trackbackobj)
    msg = "\n".join(lines)
    # KMessageBox.error(None, msg)
    sep = "------------------------------------------------------------------------------------------"
    print >> sys.stderr, msg
    # Probably need better dialog box
    w = QtGui.QWidget()
    QtGui.QMessageBox.critical(w, "AstroBuffer", sep + "\n" + str(type) + ":" + str(value) + "\n" + sep + "\n" + msg)


if __name__ == "__main__":
    sys.excepthook = excepthook

    # aboutData = KAboutData("astrobuffer", "AstroBuffer", "0.11", "KDE Astrophotography Application", KAboutData.License_GPL, "(c) 2007 Russell E. Valentine", None, "http://coldstonelabs.org", "russ@coldstonelabs.org");
    # aboutData.addAuthor("Russell Valentine", "Main Programmer", "russ@coldstonelabs.org", "http://coldstonelabs.org/");
    # KCmdLineArgs.init(sys.argv, aboutData)
    app = QtGui.QApplication(sys.argv)
    path = os.path.abspath(os.path.dirname(sys.argv[0]))
    app.setWindowIcon(QtGui.QIcon(path + os.sep + "../icons/astrobuffer-128.png"))
    global window
    window = AstroBufferWindow(app)
    window.show()
    sys.exit(app.exec_())
