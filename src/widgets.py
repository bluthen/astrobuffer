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

from PyQt4 import Qt, QtCore, QtGui
import PyQt4.Qwt5 as Qwt5
import numpy
from config import Config


class OpenRecentAction(QtGui.QMenu):
    openRecent = QtCore.pyqtSignal(str)

    def __init__(self):
        QtGui.QMenu.__init__(self, "Open Recent...")
        self.numRemember = 15
        self.recentList = []
        self.actions = []
        self.loadRecent()
        self.triggered.connect(self.slotTriggeredItem)

    def slotTriggeredItem(self, action):
        self.openRecent.emit(str(action.text()))

    def openedFile(self, file):
        found = -1
        for i in range(len(self.recentList)):
            if self.recentList[i] == file:
                found = i
        if found >= 0:
            del self.recentList[found]
        self.recentList.insert(0, file)
        while len(self.recentList) > 20:
            self.recentList.pop()
        self.saveRecent()
        self.loadRecent()

    def saveRecent(self):
        config = Config().getSettingsObj()
        config.beginGroup("Recently Opened")
        config.setValue("itemCount", QtCore.QVariant(len(self.recentList)))
        for i in range(len(self.recentList)):
            config.setValue("item" + str(i), QtCore.QVariant(self.recentList[i]))
        config.endGroup()
        config.sync()

    def loadRecent(self):
        config = Config().getSettingsObj()
        config.beginGroup("Recently Opened")
        itemCount = config.value("itemCount").toInt()[0]
        self.recentList = []
        for i in range(itemCount):
            self.recentList.append(str(config.value("item" + str(i)).toString()))
            if i >= len(self.actions):
                self.actions.append(self.addAction(self.recentList[i]))
            else:
                self.actions[i].setText(self.recentList[i])
        config.endGroup()


class SelectAction(QtGui.QMenu):
    triggeredItem = QtCore.pyqtSignal(QtGui.QAction)
    # XXX: Show checkbox Icon on current item
    def __init__(self, title, choices, defaultChecked):
        """ defaultChecked is which idx should be checked by default """
        QtGui.QMenu.__init__(self, title)
        cList = choices.split(",")
        self.items = []
        self.zoomGroup = QtGui.QActionGroup(self)
        for choice in cList:
            self.items.append(self.zoomGroup.addAction(self.addAction(choice)))
        for item in self.items:
            item.setCheckable(True)

        self.items[defaultChecked].setChecked(True)
        self.zoomGroup.triggered.connect(self.slotTriggeredItem)
        self.idx = 0

    def setCurrentItem(self, idx):
        if idx >= len(self.items):
            self.idx = len(self.items) - 1
        elif idx < 0:
            self.idx = 0
        else:
            self.idx = idx
        self.items[self.idx].setChecked(True)

    def getCurrentItem(self):
        return self.items[self.idx]

    def getCurrentIdx(self):
        return self.idx

    def size(self):
        return len(self.items)

    def slotTriggeredItem(self, action):
        idx = 0
        for a in self.items:
            if a == action:
                break
            idx += 1
        self.idx = idx
        self.triggeredItem.emit(action)


class ChooseColorRGBLChannel(QtGui.QGroupBox):
    def __init__(self, luminance=False):
        QtGui.QGroupBox.__init__(self, "Apply to channel")

        layout = QtGui.QHBoxLayout()
        self.setLayout(layout)
        buttonGroup = QtGui.QButtonGroup()

        self.red = QtGui.QCheckBox("Red")
        buttonGroup.addButton(self.red)
        layout.addWidget(self.red)
        self.green = QtGui.QCheckBox("Green")
        buttonGroup.addButton(self.green)
        layout.addWidget(self.green)
        self.blue = QtGui.QCheckBox("Blue")
        buttonGroup.addButton(self.blue)
        layout.addWidget(self.blue)
        self.luminance = None
        if luminance:
            self.luminance = QtGui.QCheckBox("Luminance")
            buttonGroup.addButton(self.luminance)
            layout.addWidget(self.luminance)

    def getSelectedChannels(self):
        """getSelectedChannels() - returns [#, #, ..] where # is 0, 1, 2, 3 for red, green, blue, luminance"""
        channels = []
        if self.red.isChecked():
            channels.append(0)
        if self.green.isChecked():
            channels.append(1)
        if self.blue.isChecked():
            channels.append(2)
        if self.luminance != None and self.luminance.isChecked():
            channels.append(3)

        return channels


class ChooseDocScrollView(QtGui.QScrollArea):
    def __init__(self, view, omit=[], defaultOne=True):
        QtGui.QScrollArea.__init__(self)

        buttonGroup = QtGui.QButtonGroup()
        w = QtGui.QWidget()
        layout = QtGui.QVBoxLayout()
        w.setLayout(layout)
        self.rbuttons = []
        self.rbuttonsIndex = []

        for i in range(len(view.documents)):
            omitFlag = False
            for index in omit:
                if (i == index):
                    omitFlag = True
            if (view.documents[i].getType() != "normal"):
                omitFlag = True
            if (omitFlag == False):
                print "chooser - " + str(i)
                rbutton = QtGui.QRadioButton(view.documents[i].getURL().getFileName())
                layout.addWidget(rbutton)
                buttonGroup.addButton(rbutton)
                self.rbuttons.append(rbutton)
                self.rbuttonsIndex.append(i)
        if defaultOne and len(self.rbuttons) > 0:
            self.rbuttons[0].toggle()
        self.setWidget(w)

    def getSelectedIndex(self):
        for i in range(len(self.rbuttons)):
            if self.rbuttons[i].isChecked():
                return self.rbuttonsIndex[i]
        return None


class ChooseDocsScrollView(QtGui.QScrollArea):
    def __init__(self, view, omit=[]):
        QtGui.QScrollArea.__init__(self)

        w = QtGui.QWidget()
        layout = QtGui.QVBoxLayout()
        w.setLayout(layout)
        self.cboxes = []
        self.cboxesIndex = []

        for i in range(len(view.documents)):
            omitFlag = False
            for index in omit:
                if i == index:
                    omitFlag = True
            if view.documents[i].getType() != "normal":
                omitFlag = True
            if omitFlag == False:
                cbutton = QtGui.QCheckBox(view.documents[i].getURL().getFileName())
                layout.addWidget(cbutton)
                self.cboxes.append(cbutton)
                self.cboxesIndex.append(i)
        self.setWidget(w)

    def getSelectedIndexes(self):
        a = []
        for i in range(len(self.cboxes)):
            if self.cboxes[i].isChecked():
                a.append(self.cboxesIndex[i])
        return a


class ContrastChooser(QtGui.QWidget):
    def __init__(self, parent, title, histData, rangePoints):
        QtGui.QWidget.__init__(self, parent)

        self.histData = histData

        min = 0
        max = histData.shape[0]
        grid = QtGui.QGridLayout(self)
        self.graph = Qwt5.QwtPlot(Qwt5.QwtText(title))
        grid.addWidget(self.graph, 0, 0)
        self.curve = Qwt5.QwtPlotCurve("Selection")
        self.curveFunc = Qwt5.QwtPlotCurve("SelectionFunc")

        self.curve.attach(self.graph)
        self.curveFunc.attach(self.graph)
        selectMin = int(rangePoints[0])
        selectMax = int(rangePoints[1])
        # if(selectMax < 1000):
        self.curve.setData(range(selectMin, selectMax),
                           numpy.clip(histData[selectMin:selectMax + 1], 1, histData[selectMin:selectMax].max()))
        # else:
        #    a=int(selectMax/1000)
        #    sm=int(selectMin/a)
        #    sx=int(selectMax/a)
        #    self.curve.setData(range(sm, sx, a), self.histData[sm:sx])

        # self.curveFunc.setData(range(selectMin,selectMax), numpy.array(range(0, selectMax-selectMin), numpy.float32)*255.0/(selectMax-selectMin))
        self.graph.setAxisTitle(Qwt5.QwtPlot.xBottom, "Pixel Value")
        self.graph.setAxisTitle(Qwt5.QwtPlot.yLeft, "Number of Pixels")
        self.graph.setAxisScaleEngine(Qwt5.QwtPlot.yLeft, Qwt5.QwtLog10ScaleEngine())
        # self.graph.enableAxis(Qwt5.QwtPlot.yRight)
        # self.graph.setAxisScale(Qwt5.QwtPlot.yRight, 0, 255)

        # Markers
        self.minMarker = Qwt5.QwtPlotMarker()
        self.minMarker.setLineStyle(Qwt5.QwtPlotMarker.VLine)
        self.minMarker.setLinePen(QtGui.QPen(QtCore.Qt.blue, 1, QtCore.Qt.DashDotLine))
        self.minMarker.setValue(selectMin, 1)
        self.minMarker.attach(self.graph)

        self.maxMarker = Qwt5.QwtPlotMarker()
        self.maxMarker.setLineStyle(Qwt5.QwtPlotMarker.VLine)
        self.maxMarker.setLinePen(QtGui.QPen(QtCore.Qt.blue, 1, QtCore.Qt.DashDotLine))
        self.maxMarker.setValue(selectMax, 1)
        self.maxMarker.attach(self.graph)

        # Slider
        # XXX: Sliders shouldn't be so exact so could have a larger range than int.
        self.graph.replot()
        minLayout = QtGui.QHBoxLayout()
        grid.addLayout(minLayout, 1, 0)
        minLabel = QtGui.QLabel("Min:")
        minLayout.addWidget(minLabel)
        self.minSlider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.minSlider.setRange(0, max)
        self.minSlider.setValue(selectMin)
        minLayout.addWidget(self.minSlider)

        maxLayout = QtGui.QHBoxLayout()
        grid.addLayout(maxLayout, 2, 0)
        maxLabel = QtGui.QLabel("Max:")
        maxLayout.addWidget(maxLabel)
        self.maxSlider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.maxSlider.setRange(0, max)
        self.maxSlider.setValue(selectMax)
        maxLayout.addWidget(self.maxSlider)

        # Spin boxes
        spinLayout = QtGui.QHBoxLayout()
        grid.addLayout(spinLayout, 3, 0)
        spinMinLabel = QtGui.QLabel("Min:")
        spinLayout.addWidget(spinMinLabel)
        self.minSpinBox = QtGui.QSpinBox()
        self.minSpinBox.setMinimum(0)
        self.minSpinBox.setMaximum(max)
        self.minSpinBox.setValue(selectMin)
        spinLayout.addWidget(self.minSpinBox)

        spinLayout = QtGui.QHBoxLayout()
        spinMaxLabel = QtGui.QLabel("Max:")
        grid.addLayout(spinLayout, 4, 0)
        spinLayout.addWidget(spinMaxLabel)
        self.maxSpinBox = QtGui.QSpinBox()
        self.maxSpinBox.setMinimum(0)
        self.maxSpinBox.setMaximum(max)
        self.maxSpinBox.setValue(selectMax)
        spinLayout.addWidget(self.maxSpinBox)

        # Connect slider and spinbox together
        self.minSlider.sliderMoved.connect(self.minSpinBox.setValue)
        self.maxSlider.sliderMoved.connect(self.maxSpinBox.setValue)
        self.minSpinBox.valueChanged.connect(self.minSlider.setValue)
        self.maxSpinBox.valueChanged.connect(self.maxSlider.setValue)

        # Connect spinbox with histogram
        self.minSpinBox.valueChanged.connect(self.slotChangeHist)
        self.maxSpinBox.valueChanged.connect(self.slotChangeHist)

    def getRange(self):
        return [self.minSpinBox.value(), self.maxSpinBox.value()]

    def slotChangeHist(self):
        if self.minSpinBox.value() >= self.maxSpinBox.value():
            return
        selectMin = self.minSpinBox.value()
        selectMax = self.maxSpinBox.value()
        self.curve.setData(range(selectMin, selectMax), numpy.clip(self.histData[selectMin:selectMax + 1], 1,
                                                                   self.histData[selectMin:selectMax].max()))
        # self.curveFunc.setData(range(selectMin,selectMax), numpy.array(range(0, selectMax-selectMin), numpy.float32)*255.0/(selectMax-selectMin))
        self.minMarker.setValue(selectMin, 1)
        self.maxMarker.setValue(selectMax, 1)

        self.graph.replot()

    def rangeChange(self, rangePoints):
        self.minSpinBox.setValue(rangePoints[0])
        self.maxSpinBox.setValue(rangePoints[1])

    def documentChanged(self, histData, rangePoints):
        print "ContrastChooser - documentChanged"
        self.histData = histData
        max = histData.shape[0]
        self.minSpinBox.setMaximum(max)
        self.maxSpinBox.setMaximum(max)
        self.minSlider.setMaximum(max)
        self.maxSlider.setMaximum(max)
        self.rangeChange([rangePoints[0], rangePoints[1]])
