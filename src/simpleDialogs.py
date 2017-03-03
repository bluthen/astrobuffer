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

import imageLib
import math
import numpy
from documents import NormalDocument
from config import Config
from widgets import ChooseDocScrollView, ChooseDocsScrollView, ChooseColorRGBLChannel


class DialogBase(QtGui.QDialog):
    def __init__(self, title, ok=False, cancel=False, apply=False, user1=False, user2=False, modal=False, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setModal(int(modal))
        self.grid = QtGui.QGridLayout(self)
        w = QtGui.QWidget()
        self.setWindowTitle(title)
        self.user1Button = None
        self.user2Button = None
        # Ok, Cancel, User1, User2 Buttons
        self.buttonBox = QtGui.QDialogButtonBox()
        self.grid.addWidget(self.buttonBox, 1, 0)
        if ok:
            self.okButton = self.buttonBox.addButton("Ok", QtGui.QDialogButtonBox.AcceptRole)
            self.okButton.clicked.connect(self.slotOk)
        if apply:
            self.applyButton = self.buttonBox.addButton("Apply", QtGui.QDialogButtonBox.ApplyRole)
            self.applyButton.clicked.connect(self.slotApply)
        if cancel:
            self.cancelButton = self.buttonBox.addButton("Cancel", QtGui.QDialogButtonBox.RejectRole)
            self.cancelButton.clicked.connect(self.slotCancel)
        if user1:
            self.user1Button = self.buttonBox.addButton("User1", QtGui.QDialogButtonBox.ActionRole)
            self.user1Button.clicked.connect(self.slotUser1)
        if user2:
            self.user2Button = self.buttonBox.addButton("User2", QtGui.QDialogButtonBox.ActionRole)
            self.user2Button.clicked.connect(self.slotUser2)

    def addWidget(self, widget):
        self.grid.addWidget(widget, 0, 0)

    def setUser1ButtonText(self, text):
        self.user1Button.setText(text)

    def setUser2ButtonText(self, text):
        self.user2Button.setText(text)

    def setCancelButtonText(self, text):
        self.cancelButton.setText(text)

    def enableCancelButton(self, enabled):
        self.cancelButton.setEnabled(enabled)

    def enableApplyButton(self, enabled):
        self.cancelButton.setEnabled(enabled)

    def enableOkButton(self, enabled):
        self.okButton.setEnabled(enabled)

    def enableUser1Button(self, enabled):
        self.user1Button.setEnabled(enabled)

    def enableUser2Button(self, enabled):
        self.user2Button.setEnabled(enabled)

    def slotOk(self):
        self.slotApply()
        self.accept()

    def slotApply(self):
        pass

    def slotCancel(self):
        self.reject()

    def slotUser1(self):
        pass

    def slotUser2(self):
        pass


class NewDialog(DialogBase):
    def __init__(self, main):
        DialogBase.__init__(self, "New", ok=True, cancel=True, modal=True, parent=main)

        self.main = main
        w = QtGui.QWidget()
        grid = QtGui.QGridLayout(w)
        xdimLabel = QtGui.QLabel("X dim:")
        grid.addWidget(xdimLabel, 0, 0)
        self.xdim = QtGui.QSpinBox()
        self.xdim.setMinimum(1)
        self.xdim.setMaximum(99999)
        self.xdim.setValue(1)
        grid.addWidget(self.xdim, 0, 1)

        ydimLabel = QtGui.QLabel("Y dim:")
        grid.addWidget(ydimLabel, 1, 0)
        self.ydim = QtGui.QSpinBox()
        self.ydim.setMinimum(1)
        self.ydim.setMaximum(99999)
        self.ydim.setValue(1)
        grid.addWidget(self.ydim, 1, 1)

        valueLabel = QtGui.QLabel("Value:")
        grid.addWidget(valueLabel, 2, 0)
        self.value = QtGui.QDoubleSpinBox()
        self.value.setMinimum(0.)
        self.value.setMaximum(99999.)
        self.value.setSingleStep(0.1)
        grid.addWidget(self.value, 2, 1)
        self.addWidget(w)

    def slotOk(self):
        data = numpy.ones((self.ydim.value(), self.xdim.value()), Config().getIDataType()) * self.value.value()
        doc = NormalDocument(self.main.view, data)
        self.main.view.addDocument(doc)
        self.accept()


class OKDialog(DialogBase):
    def __init__(self, parent, caption, message):
        DialogBase.__init__(self, caption, ok=True, modal=True, parent=parent)

        label = QtGui.QLabel(message)
        self.addWidget(label)


class SizeDialog(OKDialog):
    def __init__(self, parent):
        OKDialog.__init__(self, parent, "Error",
                          "This operation requires that all involved images be of same dimensions.")


class ImageInfoDialog(DialogBase):
    def __init__(self, view):
        DialogBase.__init__(self, "Image Info", parent=view, ok=False, cancel=False, user1=True)
        self.view = view
        curDoc = self.view.getCurrentDocument()
        # TESTING
        if curDoc.getURL == None:
            print "url is none"
        print curDoc.getURL().getFileName()
        # END TEST
        self.setUser1ButtonText("Show Header")
        w = QtGui.QWidget()
        layout = QtGui.QVBoxLayout()
        w.setLayout(layout)
        self.label1 = QtGui.QLabel("Name: " + str(curDoc.getURL().getFileName()))
        layout.addWidget(self.label1)
        self.label2 = QtGui.QLabel("Size: " + str(curDoc.getShape()[1]) + "x" + str(curDoc.getShape()[0]))
        layout.addWidget(self.label2)

        self.addWidget(w)

    def documentChanged(self):
        print "ImageInfoDialog - documentChanged"
        curDoc = self.view.getCurrentDocument()
        if curDoc == None:
            self.hide()
            return
        self.label1.setText("Name: " + str(curDoc.getURL().getFileName()))
        self.label2.setText("Size: " + str(curDoc.getShape()[1]) + "x" + str(curDoc.getShape()[0]))

    def slotUser1(self):
        print "DEBUG: ImageInfoDialog - slotUser1"
        hd = HeaderDialog(self, self.view)
        hd.show()


class HeaderDialog(DialogBase):
    def __init__(self, parent, view):
        DialogBase.__init__(self, "Header", ok=True, cancel=False, modal=True, parent=parent)
        self.view = view
        w = QtGui.QWidget()
        layout = QtGui.QVBoxLayout()
        w.setLayout(layout)
        infoLabel = QtGui.QLabel(
            "This header is the header from the original file, any change you made to the current image is not reflected in this header info.")
        layout.addWidget(infoLabel)
        if self.view.getCurrentDocument().getType() == "normal":
            header = self.view.getCurrentDocument().getHeader()
            if header == None:
                return
        else:
            headers = self.view.getCurrentDocument().getHeader()
            if headers[0] == None:
                return
            else:
                header = headers[0]
        rows = len(header)
        table = QtGui.QTableWidget(rows, 3)
        table.setHorizontalHeaderLabels(QtCore.QStringList("Field,Value,Comment".split(",")))
        i = 0
        for key, values in header.iteritems():
            table.setItem(i, 0, QtGui.QTableWidgetItem(key))
            table.setItem(i, 1, QtGui.QTableWidgetItem(str(values[0])))
            table.setItem(i, 2, QtGui.QTableWidgetItem(values[1]))
            i += 1
        table.resizeColumnsToContents()
        layout.addWidget(table)
        self.addWidget(w)


class ResizeCanvasDialog(DialogBase):
    def __init__(self, view):
        DialogBase.__init__(self, "Resize Canvas", ok=True, cancel=True, modal=True, parent=view)
        self.view = view
        self.setWindowTitle("Resize Canvas - " + str(self.view.getCurrentDocument().getURL().getFileName()))
        w = QtGui.QWidget()
        grid = QtGui.QGridLayout(w)
        canvasXLabel = QtGui.QLabel("Canvas X:")
        grid.addWidget(canvasXLabel, 0, 0)
        self.sizeX = QtGui.QSpinBox()
        self.sizeX.setMinimum(0)
        self.sizeX.setMaximum(999999)
        self.sizeX.setValue(self.view.getCurrentDocument().getShape()[1])
        grid.addWidget(self.sizeX, 0, 1)

        canvasYLabel = QtGui.QLabel("Canvas Y:")
        grid.addWidget(canvasYLabel, 1, 0)
        self.sizeY = QtGui.QSpinBox()
        self.sizeY.setMinimum(0)
        self.sizeY.setMaximum(999999)
        self.sizeY.setValue(self.view.getCurrentDocument().getShape()[0])
        grid.addWidget(self.sizeY, 1, 1)
        self.centerCanvas = QtGui.QCheckBox("Keep center in the center")
        grid.addWidget(self.centerCanvas, 2, 0)

        self.addWidget(w)

    def slotApply(self):
        sizeXValue = self.sizeX.value()
        sizeYValue = self.sizeY.value()
        if sizeXValue == 0 and sizeYValue == 0:
            return
        self.sizeX.setValue(1.)
        self.sizeY.setValue(1.)
        if self.view.getCurrentDocument().getType() == "color_rgb" or self.view.getCurrentDocument().getType() == "color_rgbl":
            num = 3
            if self.view.getCurrentDocument().getType() == "color_rgb":
                rgb = [None, None, None]
            else:
                # RGBL
                rgb = [None, None, None, None]
                num = 4
            for i in range(num):
                rgb[i] = imageLib.resizeCanvas(self.view.getCurrentDocument().rgb[i].data, sizeXValue, sizeYValue,
                                               self.centerCanvas)
            self.view.getCurrentDocument().replaceData(rgb, "ResizeCanvas")
        else:
            self.view.getCurrentDocument().replaceData(
                imageLib.resizeCanvas(self.view.getCurrentDocument().data, sizeXValue, sizeYValue,
                                      self.centerCanvas.isChecked()), "ResizeCanvas")
        self.view.getCurrentDocument().refresh(True)

    def slotOk(self):
        self.accept()
        self.slotApply()


class ScaleDialog(DialogBase):
    def __init__(self, view):
        DialogBase.__init__(self, "Scale Image", ok=True, apply=True, cancel=True, modal=True, parent=view)

        self.view = view

        w = QtGui.QWidget()
        grid = QtGui.QGridLayout(w)

        self.setWindowTitle("Scale Image - " + str(self.view.getCurrentDocument().getURL().getFileName()))
        self.shape = self.view.getCurrentDocument().getShape()
        scaleXLabel = QtGui.QLabel("Scale X:")
        grid.addWidget(scaleXLabel, 0, 0)
        self.scaleX = QtGui.QDoubleSpinBox()
        self.scaleX.setMinimum(0.0)
        self.scaleX.setMaximum(100.0)
        self.scaleX.setValue(1.0)
        self.scaleX.setSingleStep(0.01)
        self.scaleX.valueChanged.connect(self.slotScaleXChange)
        grid.addWidget(self.scaleX, 0, 1)

        sizeScaleXLabel = QtGui.QLabel(" Size Scale X:")
        grid.addWidget(sizeScaleXLabel, 1, 0)
        self.sizeScaleX = QtGui.QSpinBox()
        self.sizeScaleX.setMaximum(999999)
        self.sizeScaleX.setMinimum(0)
        self.sizeScaleX.setValue(self.shape[1])
        self.sizeScaleX.valueChanged.connect(self.slotSizeScaleXChange)
        grid.addWidget(self.sizeScaleX, 1, 1)

        scaleYLabel = QtGui.QLabel("Scale Y:")
        grid.addWidget(scaleYLabel, 2, 0)
        self.scaleY = QtGui.QDoubleSpinBox()
        self.scaleY.setMinimum(0.0)
        self.scaleY.setMaximum(100.0)
        self.scaleY.setValue(1.0)
        self.scaleY.setSingleStep(0.01)
        self.scaleY.valueChanged.connect(self.slotScaleYChange)
        grid.addWidget(self.scaleY, 2, 1)

        sizeScaleYLabel = QtGui.QLabel(" Size Scale Y:")
        grid.addWidget(sizeScaleYLabel, 3, 0)
        self.sizeScaleY = QtGui.QSpinBox()
        self.sizeScaleY.setMaximum(999999)
        self.sizeScaleY.setMinimum(0);
        self.sizeScaleY.setValue(self.shape[0])
        self.sizeScaleY.valueChanged.connect(self.slotSizeScaleYChange)
        grid.addWidget(self.sizeScaleY, 3, 1)

        if self.view.getCurrentDocument().getType() == "color_rgb":
            self.chooseColor = ChooseColorRGBLChannel(luminance=False)
            grid.addWidget(self.chooseColor, 4, 0)
        elif self.view.getCurrentDocument().getType() == "color_rgbl":
            self.chooseColor = ChooseColorRGBLChannel(luminance=True)
            grid.addWidget(self.chooseColor, 4, 0)
        else:
            self.expandCanvas = QtGui.QCheckBox("Fit Canvas")
            grid.addWidget(self.expandCanvas, 4, 0)
        self.addWidget(w)

    def slotScaleXChange(self, value):
        self.sizeScaleX.setValue(int(value * self.shape[1]))

    def slotScaleYChange(self, value):
        self.sizeScaleY.setValue(int(value * self.shape[0]))

    def slotSizeScaleXChange(self, value):
        self.scaleX.setValue(float(value) / float(self.shape[1]))

    def slotSizeScaleYChange(self, value):
        self.scaleY.setValue(float(value) / float(self.shape[0]))

    def slotApply(self):
        scaleXValue = self.scaleX.value()
        scaleYValue = self.scaleY.value()
        if scaleXValue == 1. and scaleYValue == 1.:
            return
        self.scaleX.setValue(1.)
        self.scaleY.setValue(1.)
        if self.view.getCurrentDocument().getType() == "color_rgb" or self.view.getCurrentDocument().getType() == "color_rgbl":
            if len(self.chooseColor.getSelectedChannels()) == 0:
                # XXX: Maybe give a info box explaining you have to pick a color.
                return
            if self.view.getCurrentDocument().getType() == "color_rgb":
                rgb = [None, None, None]
            else:
                # RGBL
                rgb = [None, None, None, None]
            for i in self.chooseColor.getSelectedChannels():
                rgb[i] = imageLib.scale(self.view.getCurrentDocument().rgb[i].data, scaleXValue, scaleYValue, False)
            self.view.getCurrentDocument().replaceData(rgb, "Scale")
        else:
            self.view.getCurrentDocument().replaceData(
                imageLib.scale(self.view.getCurrentDocument().data, scaleXValue, scaleYValue,
                               self.expandCanvas.isChecked()), "Scale")
        self.view.getCurrentDocument().refresh(True)

    def slotOk(self):
        self.accept()
        self.slotApply()


class ShiftDialog(DialogBase):
    def __init__(self, view):
        DialogBase.__init__(self, "Shift Image", ok=True, apply=True, cancel=True, modal=True, parent=view)

        self.view = view
        if self.view.getCurrentDocument().getType() == "color_rgb" or self.view.getCurrentDocument().getType() == "color_rgbl":
            sizeX = self.view.getCurrentDocument().rgb[0].data.shape[1]
            sizeY = self.view.getCurrentDocument().rgb[0].data.shape[0]
        else:
            sizeX = self.view.getCurrentDocument().data.shape[1]
            sizeY = self.view.getCurrentDocument().data.shape[0]
        self.setWindowTitle("Shift Image - " + str(self.view.getCurrentDocument().getURL().getFileName()))
        w = QtGui.QWidget()
        grid = QtGui.QGridLayout()
        w.setLayout(grid)
        shiftXLabel = QtGui.QLabel("Shift X:")
        grid.addWidget(shiftXLabel, 0, 0)
        self.shiftX = QtGui.QDoubleSpinBox()
        self.shiftX.setMinimum(-sizeX)
        self.shiftX.setMaximum(sizeX)
        self.shiftX.setValue(0.0)
        self.shiftX.setSingleStep(0.01)
        grid.addWidget(self.shiftX, 0, 1)

        shiftYLabel = QtGui.QLabel("Shift Y:")
        grid.addWidget(shiftYLabel, 1, 0)
        self.shiftY = QtGui.QDoubleSpinBox()
        self.shiftY.setMinimum(-sizeY)
        self.shiftY.setMaximum(sizeY)
        self.shiftY.setValue(0.0)
        self.shiftY.setSingleStep(0.01)
        grid.addWidget(self.shiftY, 1, 1)

        if self.view.getCurrentDocument().getType() == "color_rgb":
            self.chooseColor = ChooseColorRGBLChannel(luminance=False)
            grid.addWidget(self.chooseColor, 2, 0)
        elif self.view.getCurrentDocument().getType() == "color_rgbl":
            self.chooseColor = ChooseColorRGBLChannel(luminance=True)
            grid.addWidget(self.chooseColor, 2, 0)
        self.addWidget(w)

    def slotApply(self):
        shiftXValue = self.shiftX.value()
        shiftYValue = self.shiftY.value()
        if shiftYValue == 0. and shiftXValue == 0.:
            return
        self.shiftX.setValue(0.)
        self.shiftY.setValue(0.)
        if self.view.getCurrentDocument().getType() == "color_rgb" or self.view.getCurrentDocument().getType() == "color_rgbl":
            if len(self.chooseColor.getSelectedChannels()) == 0:
                # XXX: Maybe give a info box explaining you have to pick a color.
                return
            if self.view.getCurrentDocument().getType() == "color_rgb":
                rgb = [None, None, None]
            else:
                # RGBL
                rgb = [None, None, None, None]
            for i in self.chooseColor.getSelectedChannels():
                rgb[i] = imageLib.shift(self.view.getCurrentDocument().rgb[i].data, shiftXValue, shiftYValue)
            self.view.getCurrentDocument().replaceData(rgb, "Shift")
        else:
            self.view.getCurrentDocument().replaceData(
                imageLib.shift(self.view.getCurrentDocument().data, shiftXValue, shiftYValue), "Shift")
        self.view.getCurrentDocument().refresh(True)

    def slotOk(self):
        self.accept()
        self.slotApply()


class RotateDialog(DialogBase):
    def __init__(self, view):
        DialogBase.__init__(self, "Rotate Image", ok=True, apply=True, cancel=True, modal=True, parent=view)

        self.view = view
        self.setWindowTitle("Rotate Image - " + str(self.view.getCurrentDocument().getURL().getFileName()))

        w = QtGui.QWidget()
        grid = QtGui.QGridLayout(w)
        rotateLabel = QtGui.QLabel("Rotate:")
        grid.addWidget(rotateLabel, 0, 0)
        self.rotate = QtGui.QDoubleSpinBox()
        self.rotate.setMinimum(-360.0)
        self.rotate.setMaximum(360.0)
        self.rotate.setValue(0.0)
        self.rotate.setSingleStep(0.01)
        grid.addWidget(self.rotate, 0, 1)
        buttonGroup = QtGui.QButtonGroup()
        buttonBox = QtGui.QGroupBox()
        buttonLayout = QtGui.QHBoxLayout()
        buttonBox.setLayout(buttonLayout)
        grid.addWidget(buttonBox, 1, 0, 1, 2)
        self.radians = QtGui.QRadioButton("Radians")
        buttonGroup.addButton(self.radians)
        buttonLayout.addWidget(self.radians)
        self.degrees = QtGui.QRadioButton("Degrees")
        buttonGroup.addButton(self.degrees)
        buttonLayout.addWidget(self.degrees)
        self.radians.toggle()
        if self.view.getCurrentDocument().getType() == "color_rgb":
            self.chooseColor = ChooseColorRGBLChannel(luminance=False)
            grid.addWidget(self.chooseColor, 2, 0, 1, 2)
        elif self.view.getCurrentDocument().getType() == "color_rgbl":
            self.chooseColor = ChooseColorRGBLChannel(luminance=True)
            grid.addWidget(self.chooseColor, 2, 0, 1, 2)
        else:
            self.expandCanvas = QtGui.QCheckBox("Fit Canvas")
            grid.addWidget(self.expandCanvas, 2, 0, 1, 2)
        self.addWidget(w)

    def slotApply(self):
        rot = self.rotate.value()
        if rot == 0.:
            return
        self.rotate.setValue(0.)
        if self.degrees.isChecked():
            print rot
            rot = rot * math.pi / 180
        if self.view.getCurrentDocument().getType() == "color_rgb" or self.view.getCurrentDocument().getType() == "color_rgbl":
            if len(self.chooseColor.getSelectedChannels()) == 0:
                # XXX: Maybe give a info box explaining you have to pick a color.
                return
            if self.view.getCurrentDocument().getType() == "color_rgb":
                rgb = [None, None, None]
            else:
                # RGBL
                rgb = [None, None, None, None]
            for i in self.chooseColor.getSelectedChannels():
                rgb[i] = imageLib.rotate(self.view.getCurrentDocument().rgb[i].data, rot, False)
            self.view.getCurrentDocument().replaceData(rgb, "Rotate")
        else:
            self.view.getCurrentDocument().replaceData(
                imageLib.rotate(self.view.getCurrentDocument().data, rot, self.expandCanvas.isChecked()), "Rotate")
        self.view.getCurrentDocument().refresh(True)

    def slotOk(self):
        self.slotApply()
        self.accept()


class PowerDialog(DialogBase):
    def __init__(self, view):
        DialogBase.__init__(self, "Power", ok=True, apply=True, cancel=True, modal=True, parent=view)
        self.view = view
        self.setWindowTitle("Power - " + str(self.view.getCurrentDocument().getURL().getFileName()))
        w = QtGui.QWidget()
        grid = QtGui.QGridLayout(w)
        powerLabel = QtGui.QLabel("Power:")
        grid.addWidget(powerLabel, 0, 0)
        self.power = QtGui.QDoubleSpinBox()
        self.power.setMinimum(0.0)
        self.power.setMaximum(100.0)
        self.power.setValue(1.0)
        self.power.setSingleStep(0.01)
        grid.addWidget(self.power, 0, 1)
        if self.view.getCurrentDocument().getType() == "color_rgb":
            self.chooseColor = ChooseColorRGBLChannel(luminance=False)
            grid.addWidget(self.chooseColor, 1, 0)
        elif self.view.getCurrentDocument().getType() == "color_rgbl":
            self.chooseColor = ChooseColorRGBLChannel(luminance=True)
            grid.addWidget(self.chooseColor, 1, 0)
        self.addWidget(w)

    def slotApply(self):
        power = self.power.value()
        if (power == 1.):
            return
        self.power.setValue(1.)
        if self.view.getCurrentDocument().getType() == "color_rgb" or self.view.getCurrentDocument().getType() == "color_rgbl":
            if len(self.chooseColor.getSelectedChannels()) == 0:
                # XXX: Maybe give a info box explaining you have to pick a color.
                return
            if self.view.getCurrentDocument().getType() == "color_rgb":
                rgb = [None, None, None]
            else:
                # RGBL
                rgb = [None, None, None, None]
            for i in self.chooseColor.getSelectedChannels():
                rgb[i] = imageLib.power(self.view.getCurrentDocument().rgb[i].data, power)
            self.view.getCurrentDocument().replaceData(rgb, "Power")
        else:
            self.view.getCurrentDocument().replaceData(imageLib.power(self.view.getCurrentDocument().data, power),
                                                       "Power")
        self.view.getCurrentDocument().refresh(True)

    def slotOk(self):
        self.accept()
        self.slotApply()


class BinDialog(DialogBase):
    def __init__(self, view):
        DialogBase.__init__(self, "Bin Pixels", ok=True, apply=True, cancel=True, modal=True, parent=view)

        self.view = view
        self.setWindowTitle("Bin Pixels - " + str(self.view.getCurrentDocument().getURL().getFileName()))
        w = QtGui.QWidget()
        grid = QtGui.QGridLayout(w)
        binPixelsLabel = QtGui.QLabel("Bin Pixels:")
        grid.addWidget(binPixelsLabel, 0, 0)
        self.pixels = QtGui.QSpinBox()
        self.pixels.setMinimum(2)
        self.pixels.setMaximum(99999)
        grid.addWidget(self.pixels, 0, 1)
        self.addWidget(w)

    def slotApply(self):
        pixels = self.pixels.value()
        self.view.getCurrentDocument().replaceData(imageLib.bin(self.view.getCurrentDocument().data, pixels), "Power")
        self.view.getCurrentDocument().refresh(True)

    def slotOk(self):
        self.accept()
        self.slotApply()


class DDPDialog(DialogBase):
    def __init__(self, view):
        DialogBase.__init__(self, "DDP", ok=True, cancel=True, modal=True, parent=view)
        self.view = view
        self.setWindowTitle("DDP - " + str(self.view.getCurrentDocument().getURL().getFileName()))
        w = QtGui.QWidget()
        grid = QtGui.QGridLayout(w)
        aValueLabel = QtGui.QLabel("A Value:")
        grid.addWidget(aValueLabel, 0, 0)
        self.a = QtGui.QSpinBox()
        self.a.setValue(1)
        self.a.setMinimum(1)
        self.a.setMaximum(999999)
        grid.addWidget(self.a, 0, 1)
        bValueLabel = QtGui.QLabel("B Value:")
        grid.addWidget(bValueLabel, 2, 0)
        self.b = QtGui.QSpinBox()
        self.b.setMaximum(999999)
        self.b.setMinimum(1)
        self.b.setValue(1)
        grid.addWidget(self.b, 2, 1)
        if self.view.getCurrentDocument().getType() == "color_rgb":
            self.chooseColor = ChooseColorRGBLChannel(luminance=False)
            grid.addWidget(self.chooseColor, 3, 0)
            self.a.setValue(int(self.view.getCurrentDocument().rgb[0].background / 2))
            self.b.setValue(int(0.10 * self.view.getCurrentDocument().rgb[0].background))
        elif self.view.getCurrentDocument().getType() == "color_rgbl":
            self.chooseColor = ChooseColorRGBLChannel(luminance=True)
            grid.addWidget(self.chooseColor, 3, 0)
            self.a.setValue(int(self.view.getCurrentDocument().rgb[0].background / 2))
            self.b.setValue(int(0.10 * self.view.getCurrentDocument().rgb[0].background))
        else:
            self.a.setValue(int(self.view.getCurrentDocument().background / 2))
            self.b.setValue(int(0.10 * self.view.getCurrentDocument().background))
        self.edgeEmphasis = QtGui.QCheckBox("Edge Emphasis")
        self.edgeEmphasis.setChecked(True);
        grid.addWidget(self.edgeEmphasis, 4, 0)
        self.addWidget(w)

    def slotApply(self):
        aValue = self.a.value()
        bValue = self.b.value()
        if aValue == 0 or bValue == 0:
            return
        if self.view.getCurrentDocument().getType() == "color_rgb" or self.view.getCurrentDocument().getType() == "color_rgbl":
            if len(self.chooseColor.getSelectedChannels()) == 0:
                # XXX: Maybe give a info box explaining you have to pick a color.
                return
            if self.view.getCurrentDocument().getType() == "color_rgb":
                rgb = [None, None, None]
            else:
                # RGBL
                rgb = [None, None, None, None]
            for i in self.chooseColor.getSelectedChannels():
                rgb[i] = imageLib.DDP(self.view.getCurrentDocument().rgb[i].data, aValue, bValue,
                                      self.edgeEmphasis.isChecked())
            self.view.getCurrentDocument().replaceData(rgb, "DDP")
        else:
            self.view.getCurrentDocument().replaceData(
                imageLib.DDP(self.view.getCurrentDocument().data, aValue, bValue, self.edgeEmphasis.isChecked()), "DDP")
        self.view.getCurrentDocument().refresh(True)

    def slotOk(self):
        self.accept()
        self.slotApply()


class ChooserDocDialog(DialogBase):
    def __init__(self, view, title, infoText, multipleSelect=False):
        DialogBase.__init__(self, title, ok=True, cancel=True, modal=True, parent=view)

        self.view = view

        self.multipleSelect = multipleSelect
        w = QtGui.QWidget()
        grid = QtGui.QGridLayout(w)
        infoLabel = QtGui.QLabel(infoText)
        grid.addWidget(infoLabel, 0, 0)
        if multipleSelect:
            self.scrollView = ChooseDocsScrollView(view, [view.getCurrentDocIndex()])
        else:
            self.scrollView = ChooseDocScrollView(view, [view.getCurrentDocIndex()])
        grid.addWidget(self.scrollView, 1, 0)
        self.addWidget(w)

    def getSelectedIndex(self):
        """ returns number of list of numbers if multipleSelect=True"""
        if self.multipleSelect:
            return self.scrollView.getSelectedIndexes()
        else:
            return self.scrollView.getSelectedIndex()


class SumDialog(ChooserDocDialog):
    def __init__(self, view):
        ChooserDocDialog.__init__(self, view, "Sum Images", "Select an image to sum against.")

    def slotOk(self):
        i = self.getSelectedIndex()
        if self.view.getCurrentDocument().data.shape != self.view.documents[i].data.shape:
            sizeD = SizeDialog(self)
            sizeD.show()
            return
        self.accept()
        self.view.getCurrentDocument().replaceData(
            imageLib.sum(self.view.getCurrentDocument().data, self.view.documents[i].data), "Sum")
        self.view.getCurrentDocument().refresh(True)


class QuadraticSumDialog(ChooserDocDialog):
    def __init__(self, view):
        ChooserDocDialog.__init__(self, view, "Quadratic Sum", "Select image(s) to sum with.", multipleSelect=True)

    def slotOk(self):
        indexes = self.getSelectedIndex()
        for i in indexes:
            if self.view.getCurrentDocument().data.shape != self.view.documents[i].data.shape:
                sizeD = SizeDialog(self)
                sizeD.show()
                return
        self.accept()
        self.view.getCurrentDocument().replaceData(
            imageLib.quadsum(self.view.getCurrentDocument().data, indexes, self.view.documents), "Average")
        self.view.getCurrentDocument().refresh(True)


class AverageDialog(ChooserDocDialog):
    def __init__(self, view):
        ChooserDocDialog.__init__(self, view, "Average Images", "Select an image(s) to average against.",
                                  multipleSelect=True)

    def slotOk(self):
        indexes = self.getSelectedIndex()
        for i in indexes:
            if self.view.getCurrentDocument().data.shape != self.view.documents[i].data.shape:
                sizeD = SizeDialog(self)
                sizeD.show()
                return
        self.accept()
        self.view.getCurrentDocument().replaceData(
            imageLib.average(self.view.getCurrentDocument().data, indexes, self.view.documents), "Average")
        self.view.getCurrentDocument().refresh(True)


class SubtractDialog(ChooserDocDialog):
    def __init__(self, view):
        ChooserDocDialog.__init__(self, view, "Subtract Images", "Select an image to subtract against.")

    def slotOk(self):
        i = self.getSelectedIndex()
        if self.view.getCurrentDocument().data.shape != self.view.documents[i].data.shape:
            sizeD = SizeDialog(self)
            sizeD.show()
            return
        self.accept()
        self.view.getCurrentDocument().replaceData(
            imageLib.subtract(self.view.getCurrentDocument().data, self.view.documents[i].data), "Subtract")
        self.view.getCurrentDocument().refresh(True)


class MultiplyDialog(ChooserDocDialog):
    def __init__(self, view):
        ChooserDocDialog.__init__(self, view, "Multiply Images", "Select an image to multiply against.")

    def slotOk(self):
        i = self.getSelectedIndex()
        if self.view.getCurrentDocument().data.shape != self.view.documents[i].data.shape:
            sizeD = SizeDialog(self)
            sizeD.show()
            return
        self.accept()
        self.view.getCurrentDocument().replaceData(
            imageLib.multiply(self.view.getCurrentDocument().data, self.view.documents[i].data), "Multiply")
        self.view.getCurrentDocument().refresh(True)


class DivideDialog(DialogBase):
    def __init__(self, view):
        DialogBase.__init__(self, "Divide Images", ok=True, cancel=True, modal=True, parent=view)

        self.view = view

        w = QtGui.QWidget()
        grid = QtGui.QGridLayout(w)
        infoLabel = QtGui.QLabel("Select an image to divide against.")
        grid.addWidget(infoLabel, 0, 0)

        self.scrollView = ChooseDocScrollView(view, [view.getCurrentDocIndex()])
        grid.addWidget(self.scrollView, 1, 0)
        self.meanRatio = QtGui.QCheckBox("Do 60% mean ratio (Flats)")
        self.meanRatio.toggle()
        grid.addWidget(self.meanRatio, 2, 0)
        self.addWidget(w)

    def slotOk(self):
        i = self.scrollView.getSelectedIndex()
        if self.view.getCurrentDocument().data.shape != self.view.documents[i].data.shape:
            sizeD = SizeDialog(self)
            sizeD.show()
            return
        self.accept()
        self.view.getCurrentDocument().replaceData(
            imageLib.divide(self.view.getCurrentDocument().data, self.view.documents[i].data,
                            self.meanRatio.isChecked()), "Divide")
        self.view.getCurrentDocument().refresh(True)


class LesserDialog(ChooserDocDialog):
    def __init__(self, view):
        ChooserDocDialog.__init__(self, view, "Lesser", "Select an image to run lesser against.")

    def slotOk(self):
        i = self.getSelectedIndex()
        if self.view.getCurrentDocument().data.shape != self.view.documents[i].data.shape:
            sizeD = SizeDialog(self)
            sizeD.show()
            return
        self.accept()
        self.view.getCurrentDocument().replaceData(
            imageLib.lesser(self.view.getCurrentDocument().data, self.view.documents[i].data), "Lesser")
        self.view.getCurrentDocument().refresh(True)
