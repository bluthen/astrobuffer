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

from config import Config
from simpleDialogs import DialogBase


class SettingsDialog(DialogBase):
    def __init__(self, parent):
        DialogBase.__init__(self, "Settings", ok=True, cancel=True, apply=True, parent=parent, modal=True)
        tabWidget = QtGui.QTabWidget()
        self.general = GeneralSettingsWidget()
        tabWidget.addTab(self.general, "General")
        self.addWidget(tabWidget)

    def slotCancel(self):
        self.general.startSettings()
        self.reject()

    def slotApply(self):
        self.general.saveSettings()

    def slotOk(self):
        self.slotApply()
        self.accept()


class GeneralSettingsWidget(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)
        layout = QtGui.QVBoxLayout()
        self.setLayout(layout)
        buttonBox = QtGui.QGroupBox("Image Precision")

        buttonLayout = QtGui.QHBoxLayout()
        buttonBox.setLayout(buttonLayout)
        buttonGroup = QtGui.QButtonGroup()
        self.f32button = QtGui.QRadioButton("Float32")
        self.f64button = QtGui.QRadioButton("Float64")
        buttonGroup.addButton(self.f32button)
        buttonGroup.addButton(self.f64button)
        buttonLayout.addWidget(self.f32button)
        buttonLayout.addWidget(self.f64button)
        layout.addWidget(buttonBox)
        self.startSettings()

    def startSettings(self):
        if Config().getPrecision() == 64:
            self.f64button.toggle()
        else:
            self.f32button.toggle()

    def saveSettings(self):
        prec = 32
        if self.f64button.isChecked():
            prec = 64
        Config().setPrecision(prec)
