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

from widgets import ChooseDocScrollView
from simpleDialogs import SizeDialog, DialogBase
import imageLib


class AlignDialog1(DialogBase):
    """AlignDialog1(view) one of two dialogs that prompts you for image alignment. You choose which images to align."""

    def __init__(self, view):
        DialogBase.__init__(self, "Align Image (1)", cancel=True, user1=True, modal=True, parent=view)

        self.view = view

        self.setUser1ButtonText("Next")

        w = QtGui.QWidget()
        layout = QtGui.QVBoxLayout()
        w.setLayout(layout)
        infoLabel = QtGui.QLabel("Select an image to align against.")
        layout.addWidget(infoLabel)

        self.scrollView = ChooseDocScrollView(view, [view.getCurrentDocIndex()])
        layout.addWidget(self.scrollView)
        self.addWidget(w)

    def slotUser1(self):
        i = self.scrollView.getSelectedIndex()
        if self.view.getCurrentDocument().data.shape != self.view.documents[i].data.shape:
            sizeD = SizeDialog(self)
            sizeD.show()
            return
        self.accept()
        d = AlignDialog2(self.view, self.view.getCurrentDocIndex(), i)
        d.show()

    def finished(self):
        pass


class AlignDialog2(DialogBase):
    """AlignDialog2(view) second of two dialogs that prompts you for image alignment. Select the stars used for alignment."""

    def __init__(self, view, currentIndex, otherIndex):
        DialogBase.__init__(self, "Align Image(2)", parent=view, cancel=True, user2=True, user1=True, modal=True)

        self.view = view
        self.step = 0
        self.currentIndex = currentIndex
        self.otherIndex = otherIndex
        print "AlignDialog2 docindex=" + str(otherIndex)

        self.setUser1ButtonText("Next")
        self.setUser2ButtonText("Back")
        self.enableUser1Button(False)

        w = QtGui.QWidget()
        layout = QtGui.QVBoxLayout()
        w.setLayout(layout)
        self.instructions = QtGui.QLabel("Select the first star from each image.")
        layout.addWidget(self.instructions)

        hlayout = QtGui.QHBoxLayout()
        layout.addLayout(hlayout)
        self.scrollArea1 = QtGui.QScrollArea(self)
        self.scrollView1 = AlignScrollWidget(w, self.view, currentIndex)
        self.scrollArea1.setWidget(self.scrollView1)
        hlayout.addWidget(self.scrollArea1)

        self.scrollArea2 = QtGui.QScrollArea(self)
        self.scrollView2 = AlignScrollWidget(w, self.view, otherIndex)
        self.scrollArea2.setWidget(self.scrollView2)
        hlayout.addWidget(self.scrollArea2)
        self.scrollView1.mouseRelease.connect(self.release1)
        self.scrollView2.mouseRelease.connect(self.release2)

        hlayout = QtGui.QHBoxLayout()
        layout.addLayout(hlayout)
        hlayout.setSpacing(3)
        radiusLabel = QtGui.QLabel("Radius:")
        hlayout.addWidget(radiusLabel)
        self.radiusBox = QtGui.QSpinBox()
        self.radiusBox.setMinimum(1)
        self.radiusBox.setMaximum(100)
        self.radiusBox.setValue(3)
        hlayout.addWidget(self.radiusBox)
        self.addWidget(w)

    def release1(self, x, y):
        print "1 - " + str(x) + ", " + str(y)
        center = imageLib.centroidC(self.view.documents[self.currentIndex].data, x, y, self.radiusBox.value(),
                                    self.view.documents[self.currentIndex].background)
        print str(center)
        self.scrollView1.setCircle(self.step, center[0], center[1], self.radiusBox.value())
        self.scrollView1.update()
        if (self.scrollView1.circle1 != None and self.scrollView2.circle1 != None) and (
                        self.scrollView1.circle2 == None and self.scrollView2.circle2 == None):
            self.enableUser1Button(True)
        elif (self.scrollView1.circle1 != None and self.scrollView2.circle1 != None) and (
                        self.scrollView1.circle2 != None and self.scrollView2.circle2 != None):
            self.enableUser1Button(True)

    def release2(self, x, y):
        print "2 - " + str(x) + ", " + str(y)
        center = imageLib.centroidC(self.view.documents[self.otherIndex].data, x, y, self.radiusBox.value(),
                                    self.view.documents[self.otherIndex].background)
        print str(center)
        self.scrollView2.setCircle(self.step, center[0], center[1], self.radiusBox.value())
        self.scrollView2.update()
        if (self.scrollView1.circle1 != None and self.scrollView2.circle1 != None) and (
                        self.scrollView1.circle2 == None and self.scrollView2.circle2 == None):
            self.enableUser1Button(True)
        elif (self.scrollView1.circle1 != None and self.scrollView2.circle1 != None) and (
                        self.scrollView1.circle2 != None and self.scrollView2.circle2 != None):
            self.enableUser1Button(True)

    def slotUser1(self):
        if self.scrollView1.circle2 != None and self.scrollView2.circle2 != None:
            p11 = self.scrollView2.circle1
            p12 = self.scrollView1.circle1
            p21 = self.scrollView2.circle2
            p22 = self.scrollView1.circle2
            self.accept()
            self.view.getCurrentDocument().replaceData(
                imageLib.align(self.view.documents[self.currentIndex].data, p11[0], p11[1], p12[0], p12[1], p21[0],
                               p21[1], p22[0], p22[1]), "Align")
            self.view.getCurrentDocument().refresh(True)
            return
        if self.scrollView1.circle1 != None and self.scrollView2.circle1 != None:
            self.instructions.setText("Select the second star from each image.")
            self.setUser1ButtonText("Align")
            self.enableUser1Button(False)
            self.step = 1

    def slotUser2(self):
        if self.step == 1:
            self.step = 0
            self.scrollView1.resetCircles()
            self.scrollView2.resetCircles()
            self.instructions.setText("Select the first star from each image.")
            self.setUser1ButtonText("Next")
            self.enableUser1Button(False)
            self.scrollView1.update()
            self.scrollView2.update()
            return
        self.accept()
        d = AlignDialog1(self.view)
        d.show()

    def finished(self):
        pass


class MakeCenterDialog(DialogBase):
    """Center dialog"""

    def __init__(self, view):
        DialogBase.__init__(self, "Align Image (2) - Make Center", cancel=True, user1=True, modal=True, parent=view)

        self.view = view
        self.step = 0
        self.currentIndex = self.view.getCurrentDocIndex()

        self.setUser1ButtonText("Center")
        self.enableUser1Button(False)

        w = QtGui.QWidget()
        layout = QtGui.QVBoxLayout()
        w.setLayout(layout)
        self.instructions = QtGui.QLabel("Select an object to center.")
        layout.addWidget(self.instructions)

        hlayout = QtGui.QHBoxLayout()
        layout.addLayout(hlayout)
        self.scrollView1 = AlignScrollWidget(w, self.view, self.currentIndex)
        self.scrollArea1 = QtGui.QScrollArea(self)
        self.scrollArea1.setWidget(self.scrollView1)
        hlayout.addWidget(self.scrollArea1)
        self.scrollView1.mouseRelease.connect(self.release1)

        hlayout = QtGui.QHBoxLayout()
        layout.addLayout(hlayout)
        hlayout.setSpacing(3)
        hlayout.addWidget(QtGui.QLabel("Radius:"))
        self.radiusBox = QtGui.QSpinBox()
        self.radiusBox.setMinimum(1)
        self.radiusBox.setMaximum(100)
        self.radiusBox.setValue(3)
        hlayout.addWidget(self.radiusBox)
        self.addWidget(w)

    def release1(self, x, y):
        print "1 - " + str(x) + ", " + str(y)
        center = imageLib.centroidC(self.view.documents[self.currentIndex].data, x, y, self.radiusBox.value(),
                                    self.view.documents[self.currentIndex].background)
        print str(center)
        self.scrollView1.setCircle(self.step, center[0], center[1], self.radiusBox.value())
        self.scrollView1.update()
        self.enableUser1Button(True)

    def slotUser1(self):
        p = self.scrollView1.circle1
        self.accept()
        self.view.getCurrentDocument().replaceData(imageLib.center(self.view.getCurrentDocument().data, p[0], p[1]),
                                                   "Make Center")
        self.view.getCurrentDocument().refresh(True)
        return

    def finished(self):
        pass


class AlignScrollWidget(QtGui.QWidget):
    mouseRelease = QtCore.pyqtSignal(int, int)

    def __init__(self, parent, view, docIndex):
        QtGui.QWidget.__init__(self)
        self.setMouseTracking(1)
        self.setSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Maximum)
        self.view = view
        self.docIndex = docIndex

        self.pixmap = self.view.documents[self.docIndex].makePixmap(0, 1)
        self.setMouseTracking(1)
        self.resize(self.pixmap.width(), self.pixmap.height())
        self.mouseX = 0
        self.mouseY = 0
        self.circle1 = None
        self.circle2 = None

    def setCircle(self, number, x, y, radius):
        if number == 0:
            self.circle1 = [x, y, radius]
        else:
            self.circle2 = [x, y, radius]

    def resetCircles(self):
        self.circle1 = None
        self.circle2 = None

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.drawPixmap(0, 0, self.pixmap)
        if self.circle1 != None:
            painter.setPen(QtGui.QColor("hotpink"))
            painter.drawEllipse(self.circle1[0] - self.circle1[2], self.circle1[1] - self.circle1[2],
                                2 * self.circle1[2], 2 * self.circle1[2])
        if self.circle2 != None:
            painter.setPen(QtGui.QColor("lightgreen"))
            painter.drawEllipse(self.circle2[0] - self.circle2[2], self.circle2[1] - self.circle2[2],
                                2 * self.circle2[2], 2 * self.circle2[2])

    def mouseReleaseEvent(self, event):
        # if event.x() < self.pixmap.width() and event.y() < self.pixmap.height() and event.x() >= 0 and event.y() >= 0:
        self.mouseRelease.emit(event.x(), event.y())
