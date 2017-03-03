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

from config import Config
import numpy
import imageLib
import math
import string

from simpleDialogs import DialogBase


class MatrixTable(QtGui.QTableWidget):
    radiusChanged = QtCore.pyqtSignal()

    def __init__(self):
        QtGui.QTableWidget.__init__(self, 1, 1)
        self.setItem(0, 0, QtGui.QTableWidgetItem("0"))
        self.setRadius(1)
        self.valueChanged(self.valueChanged2)

    def setRadius(self, r):
        headers = ""
        for i in range(-r, r + 1):
            headers += str(i)
            if (i != r):
                headers += ","
        n = self.rowCount()
        self.setColumnCount(2 * r + 1)
        self.setRowCount(2 * r + 1)
        if n < 2 * r + 1:
            for i in range(0, 2 * r + 1):
                if i <= n - 1:
                    m = n
                else:
                    m = 0
                for j in range(m, 2 * r + 1):
                    self.setItem(i, j, QtGui.QTableWidgetItem("0"))
        for i in range(2 * r + 1):
            self.resizeRowToContents(i)
        headersList = QtCore.QStringList(headers.split(","))
        self.setHorizontalHeaderLabels(headersList)
        self.setVerticalHeaderLabels(headersList)
        print "MatrixTable.setRadius sending out emit"
        self.radiusChanged.emit()

    def getMatrix(self):
        t = []
        num = self.rowCount()
        for i in range(num):
            row = []
            for j in range(num):
                try:
                    a = float(self.item(i, j).text())
                    row.append(a)
                except:
                    row.append(0.)
            t.append(row)
            row = []
        return numpy.array(t, Config().getIDataType())

    def setMatrix(self, matrix):
        t = []
        num = self.rowCount()
        n = len(matrix)
        m = len(matrix[0])
        for i in range(n):
            for j in range(m):
                self.setItem(i, j, QtGui.QTableWidgetItem(str(matrix[i][j])))
                self.valueChanged2(i, j)

    def valueChanged2(self, row, col):
        try:
            t = float(self.item(row, col).text())
        except:
            t = 0
        self.item(row, col).setText(str(t))
        self.resizeColumnToContents(col)


class ZerosItem(QtGui.QListWidgetItem):
    def __init__(self):
        QtGui.QListWidgetItem.__init__(self, "*Zeros")

    def allowSum(self):
        return -2

    def isCustomItem(self):
        return False

    def getName(self):
        # Only used for custom
        return ""

    def allowSTDDev(self):
        return False

    def getMatrix(self, radius, stddev):
        # Allow change of stddev
        t = numpy.zeros((2 * radius + 1, 2 * radius + 1))
        return numpy.array(t, Config().getIDataType())


class GaussianBlurItem(QtGui.QListWidgetItem):
    def __init__(self):
        QtGui.QListWidgetItem.__init__(self, "*Gaussian Blur")

    def allowSum(self):
        # -2: Disabled Off
        # -1: Disabled On
        # 0: Enabled
        # 1: Enabled On
        # 2: Enabled Off
        return -1

    def isCustomItem(self):
        return False

    def getName(self):
        # Only used for custom
        return ""

    def allowSTDDev(self):
        return True

    def getMatrix(self, radius, stddev):
        # Allow change of stddev
        t = numpy.arange(-radius, radius + 1)
        t = (1. / (stddev * (2. * math.pi) ** (1. / 2.))) * math.e ** -(t ** 2. / (2. * stddev ** 2.))
        t = (t / t[0]).round(1)
        return numpy.array(numpy.outer(t, t), Config().getIDataType())


class LoGItem(QtGui.QListWidgetItem):
    def __init__(self):
        QtGui.QListWidgetItem.__init__(self, "*Laplacian of Gaussian")

    def allowSum(self):
        # -2: Disabled Off
        # -1: Disabled On
        # 0: Enabled
        # 1: Enabled On
        # 2: Enabled Off
        return -2

    def isCustomItem(self):
        return False

    def getName(self):
        # Only used for custom
        return ""

    def allowSTDDev(self):
        return True

    def getMatrix(self, radius, stddev):
        # Allow change of stddev
        t = numpy.arange(-radius, radius + 1)
        t = numpy.zeros((2 * radius + 1, 2 * radius + 1), Config().getIDataType())
        xa = 0
        for x in range(-radius, radius + 1):
            ya = 0
            for y in range(-radius, radius + 1):
                t[xa, ya] = -(1. / (math.pi * stddev ** 4.)) * (
                    1 - (x ** 2. + y ** 2.) / (2. * stddev ** 2.)) * math.e ** (
                -(x ** 2. + y ** 2) / (2. * stddev ** 2))
                ya += 1
            xa += 1
        t = ((100 / t[radius, radius]) * t).round(1)
        return t


class BlankCustomItem(QtGui.QListWidgetItem):
    def __init__(self, name=None):
        QtGui.QListWidgetItem.__init__(self, "*Custom")

    def isCustomItem(self):
        return False

    def getName(self):
        # Only used for custom
        return ""

    def allowSum(self):
        # -2: Disabled Off
        # -1: Disabled On
        # 0: Enabled
        # 1: Enabled On
        # 2: Enabled Off
        return 0

    def allowSTDDev(self):
        return False

    def getMatrix(self, radius, stddev):
        return None


class CustomItem(QtGui.QListWidgetItem):
    def __init__(self, name, matrix, sum):
        QtGui.QListWidgetItem.__init__(self, name)
        self.name = name
        self.matrix = matrix
        self.sum = sum

    def isCustomItem(self):
        return True

    def getName(self):
        return self.name

    def allowSum(self):
        return self.sum

    def allowSTDDev(self):
        return False

    def getMatrix(self, radius=None, stddev=None):
        return self.matrix


class ConvolutionDialog(DialogBase):
    def __init__(self, view):
        DialogBase.__init__(self, "Convolution Dialog", cancel=True, ok=True, modal=True, parent=view)
        # XXX: Fix infinite set radius loop
        self.view = view
        w = QtGui.QWidget()
        hbox = QtGui.QHBoxLayout(w)
        self.lbox = QtGui.QListWidget()
        hbox.addWidget(self.lbox)
        self.lbox.addItem(GaussianBlurItem())
        self.lbox.addItem(LoGItem())
        self.lbox.addItem(ZerosItem())
        hbox.addWidget(self.lbox)
        bcustom = BlankCustomItem()
        self.lbox.addItem(bcustom)
        self.lboxpopup = QtGui.QMenu(self.lbox)
        delete = QtGui.QAction("Delete", self.lboxpopup, triggered=self.slotDeleteItem)
        self.lboxpopup.addAction(delete)

        self.customItems = self.readItemsConfig()
        for item in self.customItems:
            self.lbox.addItem(item)
        # XXX: Load items from config
        self.lbox.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.lbox.itemSelectionChanged.connect(self.selectionChanged)
        self.lbox.customContextMenuRequested.connect(self.doLboxPopup)
        vbox = QtGui.QVBoxLayout()
        hbox.addLayout(vbox)
        # table
        self.table = MatrixTable()
        vbox.addWidget(self.table)
        self.table.radiusChanged.connect(self.selectionChanged)
        # Radius
        hbox2 = QtGui.QHBoxLayout()
        vbox.addLayout(hbox2)
        hbox2.addWidget(QtGui.QLabel("Radius:"))
        self.radius = QtGui.QSpinBox()
        self.radius.setMinimum(1)
        self.radius.setMaximum(50)
        hbox2.addWidget(self.radius)
        self.radius.valueChanged.connect(self.table.setRadius)
        # Stddev
        hbox3 = QtGui.QHBoxLayout()
        vbox.addLayout(hbox3)
        self.stddevLabel = QtGui.QLabel("Standard Deviation:")
        hbox3.addWidget(self.stddevLabel)
        self.stddev = QtGui.QDoubleSpinBox()
        self.stddev.setMinimum(0.0)
        self.stddev.setMaximum(100.0)
        self.stddev.setSingleStep(0.01)
        self.stddev.setValue(1.0)
        hbox3.addWidget(self.stddev)
        self.stddev.valueChanged.connect(self.selectionChanged)
        # Sum=1
        self.sumCheckBox = QtGui.QCheckBox("Make sum of matrix equal one")
        vbox.addWidget(self.sumCheckBox)
        # Label
        hbox3 = QtGui.QHBoxLayout()
        vbox.addLayout(hbox3)
        hbox3.addWidget(QtGui.QLabel("Label:"))
        self.label = QtGui.QLineEdit()
        hbox3.addWidget(self.label)
        self.saveButton = QtGui.QPushButton()
        self.saveButton.setText("Save")
        hbox3.addWidget(self.saveButton)
        self.saveButton.clicked.connect(self.saveItem)
        self.addWidget(w)

        # Set to custom
        self.lbox.setCurrentItem(bcustom)

    def doLboxPopup(self, pos):
        item = self.lbox.itemAt(pos)
        if item.isCustomItem():
            self.lboxpopup.exec_(QtGui.QCursor.pos())

    def slotDeleteItem(self):
        print "delete item"
        self.lbox.removeItemWidget(self.lbox.currentItem())
        self.writeItemsConfig()

    def saveItem(self):
        label = str(self.label.text())
        if label == "":
            return
        if self.sumCheckBox.isChecked():
            allowSum = 1
        else:
            allowSum = 2
        item = CustomItem(label, self.table.getMatrix(), allowSum)
        # If name exists save over.
        replaced = False
        for it in range(len(self.customItems)):
            if self.customItems[it].getName() == label:
                print "replace in list"
                row = self.lbox.row(self.customItems[it])
                self.lbox.removeItemWidget(self.customItems[it])
                self.lbox.insertItem(row, item)
                self.customItems.remove(self.customItems[it])
                replaced = True
                break
        if replaced == False:
            print "Inserting into list"
            self.lbox.addItem(item)
        self.customItems.append(item)
        self.lbox.setCurrentItem(item)
        # XXX: Save to config
        self.writeItemsConfig()

    def writeItemsConfig(self):
        print "Saving custom items to config"
        config = Config().getSettingsObj()
        config.beginGroup("User Convolution Items")
        itemCount = len(self.customItems)
        print itemCount
        config.setValue("itemCount", QtCore.QVariant(itemCount))
        for i in range(itemCount):
            print "writeItemsConfig. item =" + str(i)
            cols = len(self.customItems[i].getMatrix())
            config.setValue("item" + str(i) + "clength", QtCore.QVariant(cols))
            config.setValue("item" + str(i) + "name", QtCore.QVariant(self.customItems[i].getName()))
            config.setValue("item" + str(i) + "allowsum", QtCore.QVariant(self.customItems[i].allowSum()))
            t = ""
            for j in self.customItems[i].getMatrix().flat:
                t = t + str(j) + ","
            config.setValue("item" + str(i) + "matrix", QtCore.QVariant(t))
        config.endGroup()
        config.sync()

    def readItemsConfig(self):
        items = []
        config = Config().getSettingsObj()
        config.beginGroup("User Convolution Items")
        itemCount = config.value("itemCount").toInt()[0]
        for i in range(itemCount):
            cols = config.value("item" + str(i) + "clength").toInt()[0]
            name = str(config.value("item" + str(i) + "name").toString())
            allowSum = config.value("item" + str(i) + "allowsum").toInt()[0]
            matrixEntries = str(config.value("item" + str(i) + "matrix").toString())
            print matrixEntries
            mlist = string.split(matrixEntries, ",")[0:-1]
            matrix = []
            for j in mlist:
                matrix.append(float(j))
            matrix = numpy.array(matrix, Config().getIDataType()).reshape(cols, len(matrix) / cols)
            print "readItemsConfig" + str(matrix)
            items.append(CustomItem(name, matrix, allowSum))
        config.endGroup()
        return items

    def selectionChanged(self):
        print "selectionChanged()"
        if self.lbox.currentItem() == None:
            # XXX: Should need this if, fix it, in here for saveItem
            return
        matrix = self.lbox.currentItem().getMatrix(self.radius.value(), self.stddev.value())
        if matrix != None:
            n = len(matrix)
            m = len(matrix[0])
            p = max(m, n)
            if p > int(self.table.rowCount()):
                print "p=" + str(int(p / 2))
                self.radius.setValue(int(p / 2))
                return
            self.table.setMatrix(matrix)
        if self.lbox.currentItem().allowSTDDev() == True:
            self.stddev.show()
            self.stddevLabel.show()
        else:
            self.stddev.hide()
            self.stddevLabel.hide()
        # -2: Disabled Off
        # -1: Disabled On
        # 0: Enabled
        # 1: Enabled On
        # 2: Enabled Off
        print "allowSum()=" + str(self.lbox.currentItem().allowSum())
        if self.lbox.currentItem().allowSum() == -2:
            self.sumCheckBox.setChecked(False)
            self.sumCheckBox.hide()
        elif self.lbox.currentItem().allowSum() == -1:
            self.sumCheckBox.setChecked(True)
            self.sumCheckBox.hide()
        elif self.lbox.currentItem().allowSum() == 1:
            self.sumCheckBox.setChecked(True)
            self.sumCheckBox.show()
        elif self.lbox.currentItem().allowSum() == 2:
            self.sumCheckBox.setChecked(False)
            self.sumCheckBox.show()
        else:
            self.sumCheckBox.show()
        self.label.setText(self.lbox.currentItem().getName())

    def slotOk(self):
        self.accept()
        m = self.table.getMatrix()
        # Should be option to make sums at to 1
        if self.sumCheckBox.isChecked():
            m = m / m.sum()
        self.view.getCurrentDocument().replaceData(imageLib.convolve(self.view.getCurrentDocument().data, m),
                                                   "Convolve")
        self.view.getCurrentDocument().refresh(True)
