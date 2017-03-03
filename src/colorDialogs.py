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

from widgets import ChooseDocScrollView
from simpleDialogs import SizeDialog, DialogBase
from misc import URL
from documents import ColorRGBDocument, ColorRGBLDocument


class RGBDialog(DialogBase):
    def __init__(self, view):
        DialogBase.__init__(self, "RGB Image", ok=True, cancel=True, modal=True, parent=view)

        self.view = view

        w = QtGui.QWidget()
        grid = QtGui.QGridLayout(w)
        # Red
        redGroup = QtGui.QGroupBox("Red")
        redLayout = QtGui.QVBoxLayout()
        self.rDocChooser = ChooseDocScrollView(view)
        redLayout.addWidget(self.rDocChooser)
        redGroup.setLayout(redLayout)
        grid.addWidget(redGroup, 0, 0)
        # Green
        greenGroup = QtGui.QGroupBox("Green")
        greenLayout = QtGui.QVBoxLayout()
        self.gDocChooser = ChooseDocScrollView(view)
        greenLayout.addWidget(self.gDocChooser)
        greenGroup.setLayout(greenLayout)
        grid.addWidget(greenGroup, 0, 1)
        # Blue
        blueGroup = QtGui.QGroupBox("Blue")
        blueLayout = QtGui.QVBoxLayout()
        self.bDocChooser = ChooseDocScrollView(view)
        blueLayout.addWidget(self.bDocChooser)
        blueGroup.setLayout(blueLayout)
        grid.addWidget(blueGroup, 1, 0)
        # Luminance
        luminanceGroup = QtGui.QGroupBox("Luminance")
        luminanceLayout = QtGui.QVBoxLayout()
        luminanceGroup.setLayout(luminanceLayout)
        self.lDocChooser = ChooseDocScrollView(view)
        luminanceLayout.addWidget(self.lDocChooser)
        self.useLuminance = QtGui.QCheckBox("Use Luminance")
        luminanceLayout.addWidget(self.useLuminance)
        grid.addWidget(luminanceGroup, 1, 1)
        self.addWidget(w)

    def slotOk(self):
        self.accept()
        rIndex = self.rDocChooser.getSelectedIndex()
        gIndex = self.gDocChooser.getSelectedIndex()
        bIndex = self.bDocChooser.getSelectedIndex()
        lIndex = self.lDocChooser.getSelectedIndex()
        brightRange = [self.view.documents[rIndex].getBrightRange(), self.view.documents[gIndex].getBrightRange(),
                       self.view.documents[bIndex].getBrightRange()]
        shape = self.view.documents[rIndex].data.shape
        if (shape != self.view.documents[gIndex].data.shape) or (shape != self.view.documents[bIndex].data.shape) or (
                    self.useLuminance.isChecked() and (shape != self.view.documents[lIndex].data.shape)):
            sizeD = SizeDialog(self)
            sizeD.show()
            return
        if self.useLuminance.isChecked():
            brightRange.append(self.view.documents[lIndex].getBrightRange())
            colorDoc = ColorRGBLDocument(self.view,
                                         rgblData=[self.view.documents[rIndex].data, self.view.documents[gIndex].data,
                                                   self.view.documents[bIndex].data, self.view.documents[lIndex].data],
                                         url=URL("/New"), brightRange=brightRange)
        else:
            colorDoc = ColorRGBDocument(self.view,
                                        rgbData=[self.view.documents[rIndex].data, self.view.documents[gIndex].data,
                                                 self.view.documents[bIndex].data], url=URL("/New"),
                                        brightRange=brightRange)

        self.view.addDocument(colorDoc)
