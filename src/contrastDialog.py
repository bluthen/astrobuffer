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

from PyQt4 import Qt, QtGui, QtCore
import PyQt4.Qwt5 as Qwt5

import numpy
from widgets import ContrastChooser
from simpleDialogs import DialogBase

# XXX: This dialog needs cleaning up, more like the color one.
class ContrastDialog2(DialogBase):
    def __init__(self, parent):
        DialogBase.__init__(self, "Adjust Contrast", ok=True, apply=True, cancel=True, user1=True, modal=False,
                            parent=parent)

        self.parent = parent
        curDoc = self.parent.getCurrentDocument()
        # TESTING
        if curDoc.getURL == None:
            print "url is none"
        print curDoc.getURL()
        print curDoc.getURL().getFileName()
        # END TEST
        self.setWindowTitle("Adjust Contrast - " + str(curDoc.getURL().getFileName()))
        max = curDoc.getHistogram().shape[0]
        brightRange = curDoc.getBrightRange()

        self.setUser1ButtonText("Auto")
        w = QtGui.QWidget()
        layout = QtGui.QVBoxLayout()
        w.setLayout(layout)
        page = self.makeVBoxMainWidget()

        self.qhist1 = Qwt5.QwtPlot(Qwt5.QwtText("Entire Image"))
        layout.addWidget(self.qhist1)
        self.curve1 = Qwt5.QwtPlotCurve("Entire Image")
        self.curve1.attach(self.qhist1)
        self.curve1.setData(range(len(curDoc.getHistogram())),
                            numpy.clip(curDoc.getHistogram(), 1, curDoc.getHistogram().max()))
        # set data and set zeros to ones because the logarithmic graphing does weird stuff with the zeros
        self.qhist1.setAxisTitle(Qwt5.QwtPlot.xBottom, "Pixel Value")
        self.qhist1.setAxisTitle(Qwt5.QwtPlot.yLeft, "Number of Pixels")
        self.qhist1.setAxisScaleEngine(Qwt5.QwtPlot.yLeft, Qwt5.QwtLog10ScaleEngine())
        self.qhist1.replot()

        self.qhist2 = Qwt5.QwtPlot(Qwt5.QwtText("Selection"))
        layout.addWidget(self.qhist2)
        self.curve2 = Qwt5.QwtPlotCurve("Selection")
        self.curve2.attach(self.qhist2)
        tmpHist = curDoc.getHistogram()
        t2m = int(brightRange[0])
        t2ma = int(brightRange[1] + 1)
        self.curve2.setData(range(t2m, t2ma), numpy.clip(tmpHist[t2m:t2ma], 1, tmpHist[t2m:t2ma].max()))
        self.qhist2.setAxisTitle(Qwt5.QwtPlot.xBottom, "Pixel Value")
        self.qhist2.setAxisTitle(Qwt5.QwtPlot.yLeft, "Number of Pixels")
        self.qhist2.setAxisScaleEngine(Qwt5.QwtPlot.yLeft, Qwt5.QwtLog10ScaleEngine())
        self.qhist2.replot()

        # Blue marker historgram 1
        self.blue1min = Qwt5.QwtPlotMarker()
        self.blue1min.setLineStyle(Qwt5.QwtPlotMarker.VLine)
        self.blue1min.setLinePen(QtGui.QPen(Qt.blue, 1, Qt.DashDotLine))
        self.blue1min.setValue(t2m, 1)
        self.blue1min.attach(self.qhist1)

        self.blue1max = Qwt5.QwtPlotMarker()
        self.blue1max.setLineStyle(Qwt5.QwtPlotMarker.VLine)
        self.blue1max.setLinePen(QtGui.QPen(Qt.blue, 1, Qt.DashDotLine))
        self.blue1max.setValue(t2ma, 1)
        self.blue1max.attach(self.qhist1)

        self.qhist1.replot()

        # Bluemarker histogram 2
        self.blue2min = Qwt5.QwtPlotMarker()
        self.blue2min.setLineStyle(Qwt5.QwtPlotMarker.VLine)
        self.blue2min.setLinePen(QtGui.QPen(Qt.blue, 1, Qt.DashDotLine))
        self.blue2min.setValue(t2m, 1)
        self.blue2min.attach(self.qhist2)

        self.blue2max = Qwt5.QwtPlotMarker()
        self.blue2max.setLineStyle(Qwt5.QwtPlotMarker.VLine)
        self.blue2max.setLinePen(QtGui.QPen(Qt.blue, 1, Qt.DashDotLine))
        self.blue2max.setValue(t2ma, 1)
        self.blue2max.attach(self.qhist2)

        self.qhist2.replot()

        hlayout = QtGUI.QHBoxLayout()
        layout.addLayout(hlayout)
        minLabel = QtGui.QLabel("Min:")
        hlayout.addWidget(minLabel)
        self.minSlider = QtGui.QSlider()
        self.minSlider.setMinimum(0)
        self.minSlider.setMaximum(max)
        self.minSlider.setValue(brightRange[0])
        self.minSlider.setOrientation(Qt.Horizontal)
        hlayout.addWidget(self.minSlider)
        layout.addWidget(w1)

        hlayout = QtGui.QHBoxLayout()
        layout.addLayout(hlayout)
        hlayout.addWidget(QtGui.QLabel("Max:"))
        self.maxSlider = QtGui.QSlider()
        self.maxSlider.setMinimum(0)
        self.maxSlider.setMaximum(max)
        self.maxSlider.setValue(brightRange[1])
        self.maxSlider.setOrientation(Qt.Horizontal)
        hlayout.addWidget(self.maxSlider)

        hlayout = QtGui.QHBoxLayout()
        layout.addLayout(hlayout)
        self.allCheck = QtGui.QCheckBox("Changes Effect All Images")
        hlayout.addWidget(self.allCheck)
        # QLabel("Changes Effect All Images", bottomBox)
        hlayout = QtGui.QGridLayout()
        layout.addLayout(hlayout)
        hlayout.addWidget(QtGui.QLabel("Min:"), 0, 0)
        self.minSpinBox = QtGui.QSpinBox()
        self.minSpinBox.setMinimum(0)
        self.minSpinBox.setMaximum(max)
        self.minSpinBox.setValue(brightRange[0])
        hlayout.addWidget(self.minSpinBox, 0, 1)
        hlayout.addWidget(QtGui.QLabel("Max:"), 1, 0)
        self.maxSpinBox = QSpinBox()
        self.maxSpinBox.setMinimum(0)
        self.maxSpinBox.setMaximum(max)
        self.maxSpinBox.setValue(brightRange[1])
        self.minSlider.sliderMoved.connect(self.minSpinBox.setValue)
        self.maxSlider.sliderMoved.connect(self.maxSpinBox.setValue)
        self.minSpinBox.valueChanged.connect(self.minSlider.setValue)
        self.maxSpinBox.valueChanged.connect(self.maxSlider.setValue)
        self.minSpinBox.valueChanged.connect(self.slotChangeHist)
        self.maxSpinBox.valueChanged.connect(self.slotChangeHist)
        self.addWidget(w)

    def documentChanged(self):
        print "ContrastDialog - documentChanged"
        curDoc = self.parent.getCurrentDocument()
        if (curDoc == None):
            self.hide()
            return
        brightRange = curDoc.getBrightRange()
        self.setWindowTitle("Adjust Contrast - " + str(curDoc.getURL().getFileName()))
        self.curve1.setData(range(0, len(curDoc.getHistogram())),
                            numpy.clip(curDoc.getHistogram(), 1, curDoc.getHistogram().max()))
        self.curve2.setData(range(brightRange[0], brightRange[1]),
                            numpy.clip(curDoc.getHistogram(), 1, curDoc.getHistogram().max()))
        self.minSpinBox.setMaxValue(curDoc.getHistogram().shape[0])
        self.minSlider.setMaxValue(curDoc.getHistogram().shape[0])
        self.maxSpinBox.setMaxValue(curDoc.getHistogram().shape[0])
        self.maxSlider.setMaxValue(curDoc.getHistogram().shape[0])
        self.minSpinBox.setValue(brightRange[0])
        self.maxSpinBox.setValue(brightRange[1])
        self.qhist1.replot()
        self.qhist2.replot()

    def slotChangeHist(self):
        if self.minSpinBox.value() >= self.maxSpinBox.value():
            return
        curDoc = self.parent.getCurrentDocument()
        self.curve2.setData(range(self.minSpinBox.value(), self.maxSpinBox.value() + 1),
                            numpy.clip(curDoc.getHistogram()[self.minSpinBox.value():self.maxSpinBox.value() + 1], 1,
                                       curDoc.getHistogram()[
                                       self.minSpinBox.value():self.maxSpinBox.value() + 1].max()))
        self.blue2min.setValue(self.minSpinBox.value(), 1)
        self.blue2max.setValue(self.maxSpinBox.value(), 1)
        self.qhist2.replot()
        self.blue1min.setValue(self.minSpinBox.value(), 1)
        self.blue1max.setValue(self.maxSpinBox.value(), 1)
        self.qhist1.replot()

    def slotOk(self):
        self.slotApply()
        self.accept()

    def slotApply(self):
        newValue = [self.minSpinBox.value(), self.maxSpinBox.value()]
        if self.allCheck.isChecked():
            self.parent.setAllBrightRange(newValue)
        else:
            if self.parent.getCurrentDocument().getBrightRange() != newValue:
                self.parent.getCurrentDocument().setBrightRange(newValue)
                self.parent.getCurrentDocument().refresh()

    def slotUser1(self):
        curDoc = self.parent.getCurrentDocument()
        range = curDoc.autoContrast()
        self.minSpinBox.setValue(range[0])
        self.maxSpinBox.setValue(range[1])

    def finished(self):
        pass


class ContrastDialog(DialogBase):
    def __init__(self, view):
        DialogBase.__init__(self, "Adjust Contrast", parent=view, cancel=True, ok=True, modal=False, apply=True,
                            user1=True)

        self.view = view
        curDoc = self.view.getCurrentDocument()
        self.setWindowTitle("Adjust Contrast - " + str(curDoc.getURL().getFileName()))
        brightRange = curDoc.getBrightRange()

        histogram = curDoc.getHistogram()
        tabWidget = QtGui.QTabWidget()
        self.addWidget(tabWidget)
        self.chooser = ContrastChooser(None, "Selection", histogram, brightRange)
        tabWidget.addTab(self.chooser, "Contrast")

        self.setUser1ButtonText("Auto")

    def slotApply(self):
        t = self.chooser.getRange()
        if self.view.getCurrentDocument().getBrightRange() != t:
            self.view.getCurrentDocument().setBrightRange(t)
            self.view.getCurrentDocument().refresh()

    # Auto Contrast
    def slotUser1(self):
        curDoc = self.view.getCurrentDocument()
        range = curDoc.autoContrast()
        self.chooser.rangeChange(range)

    def documentChanged(self):
        curDoc = self.view.getCurrentDocument()
        brightRange = curDoc.getBrightRange()
        histogram = curDoc.getHistogram()
        self.chooser.documentChanged(histogram, brightRange)


class ColorRGBContrastDialog(DialogBase):
    def __init__(self, view):
        DialogBase.__init__(self, "Adjust Contrast", parent=view, cancel=True, ok=True, modal=False, apply=True,
                            user1=True)

        self.view = view
        curDoc = self.view.getCurrentDocument()
        self.setWindowTitle("Adjust Contrast - " + str(curDoc.getURL().getFileName()))
        brightRange = curDoc.getBrightRange()

        histograms = curDoc.getHistogram()
        self.tabWidget = QtGui.QTabWidget()
        self.addWidget(self.tabWidget)
        self.redChooser = ContrastChooser(None, "Red", histograms[0], brightRange[0])
        self.greenChooser = ContrastChooser(None, "Green", histograms[1], brightRange[1])
        self.blueChooser = ContrastChooser(None, "Blue", histograms[2], brightRange[2])
        self.tabWidget.addTab(self.redChooser, "Red")
        self.tabWidget.addTab(self.greenChooser, "Green")
        self.tabWidget.addTab(self.blueChooser, "Blue")

        self.setUser1ButtonText("Auto")

    def addTab(self, widget, label):
        self.tabWidget.addTab(widget, label)

    def slotApply(self):
        t = []
        t.append(self.redChooser.getRange())
        t.append(self.greenChooser.getRange())
        t.append(self.blueChooser.getRange())
        if (self.view.getCurrentDocument().getBrightRange() != t):
            self.view.getCurrentDocument().setBrightRange(t)
            self.view.getCurrentDocument().refresh()

    def slotUser1(self):
        curDoc = self.view.getCurrentDocument()
        ranges = curDoc.autoContrast()
        self.redChooser.rangeChange(ranges[0])
        self.greenChooser.rangeChange(ranges[1])
        self.blueChooser.rangeChange(ranges[2])

    def documentChanged(self):
        curDoc = self.view.getCurrentDocument()
        brightRange = curDoc.getBrightRange()
        histograms = curDoc.getHistogram()
        self.redChooser.documentChanged(histograms[0], brightRange[0])
        self.greenChooser.documentChanged(histograms[1], brightRange[1])
        self.blueChooser.documentChanged(histograms[2], brightRange[2])


class ColorRGBLContrastDialog(ColorRGBContrastDialog):
    def __init__(self, view):
        ColorRGBContrastDialog.__init__(self, view)
        brightRange = self.view.getCurrentDocument().getBrightRange()
        histograms = self.view.getCurrentDocument().getHistogram()
        self.luminanceChooser = ContrastChooser(None, "Luminance", histograms[3], brightRange[3])
        self.addTab(self.luminanceChooser, "Luminance")

    def slotApply(self):
        t = []
        t.append(self.redChooser.getRange())
        t.append(self.greenChooser.getRange())
        t.append(self.blueChooser.getRange())
        t.append(self.luminanceChooser.getRange())
        if (self.view.getCurrentDocument().getBrightRange() != t):
            self.view.getCurrentDocument().setBrightRange(t)
            self.view.getCurrentDocument().refresh()

    def slotAutoContrast(self):
        curDoc = self.view.getCurrentDocument()
        ranges = curDoc.autoContrast()
        self.redChooser.rangeChange(ranges[0])
        self.greenChooser.rangeChange(ranges[1])
        self.blueChooser.rangeChange(ranges[2])
        self.luminanceChooser.rangeChange(ranges[3])

    def documentChanged(self):
        curDoc = self.view.getCurrentDocument()
        brightRange = curDoc.getBrightRange()
        histograms = curDoc.getHistogram()
        self.redChooser.documentChanged(histograms[0], brightRange[0])
        self.greenChooser.documentChanged(histograms[1], brightRange[1])
        self.blueChooser.documentChanged(histograms[2], brightRange[2])
        self.luminanceChooser.documentChanged(histograms[3], brightRange[3])
