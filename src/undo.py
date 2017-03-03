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

import misc
import os


class Undo:
    def __init__(self):
        self.redoList = []
        self.undoList = []

    def cleanup(self):
        for f in self.redoList:
            f.close()
        for f in self.undoList:
            f.close()
        self.redoList = []
        self.undoList = []

    def setUndo(self, doc, replaceBrightRange=None, replaceData=None, isRedo=False):
        undoEvent = [doc.getBrightRange()]
        if replaceData != None:
            undoEvent.append(doc.data)
        else:
            undoEvent.append(None)
        if isRedo == False:
            self.clearRedos()
        self.undoList.append(misc.pickle(undoEvent))

    def clearRedos(self):
        for f in self.redoList:
            f.close()
        self.redoList = []

    def redo(self, doc):
        print "Undo.redo()"
        if len(self.redoList) > 0:
            redoEvent = misc.unpickle(self.redoList[-1])
            self.setUndo(doc, redoEvent[0], redoEvent[1], True)
            doc.setBrightRange(redoEvent[0])
            if redoEvent[1] != None:
                doc.data = redoEvent[1]
            self.redoList[-1].close()
            self.redoList = self.redoList[0:-1]

    def undo(self, doc):
        print "Undo.undo()"
        if len(self.undoList) > 0:
            redoEvent = [doc.getBrightRange()]
            undoEvent = misc.unpickle(self.undoList[-1])
            doc.setBrightRange(undoEvent[0])
            if undoEvent[1] != None:
                redoEvent.append(doc.data)
                doc.data = undoEvent[1]
            else:
                redoEvent.append(None)
            self.undoList[-1].close()
            self.undoList = self.undoList[0:-1]
            self.redoList.append(misc.pickle(redoEvent))


class UndoRGB:
    def __init__(self):
        self.redoList = []
        self.undoList = []

    def cleanup(self):
        print "UndoRGB.cleanup()"
        for f in self.redoList:
            f.close()
        for f in self.undoList:
            f.close()
        self.redoList = []
        self.undoList = []

    def setUndo(self, doc, replaceBrightRange=None, replaceDatas=None, isRedo=False):
        undoEvent = [doc.getBrightRange()]
        for i in range(len(replaceDatas)):
            if replaceDatas[i] != None:
                undoEvent.append(doc.rgb[i].data)
            else:
                undoEvent.append(None)
        if isRedo == False:
            self.clearRedos()
        self.undoList.append(misc.pickle(undoEvent))

    def clearRedos(self):
        for f in self.redoList:
            f.close()
        self.redoList = []

    def redo(self, doc):
        print "UndoRGB.redo()"
        if len(self.redoList) > 0:
            redoEvent = misc.unpickle(self.redoList[-1])
            self.setUndo(doc, redoEvent[0], redoEvent[1:], True)
            doc.setBrightRange(redoEvent[0])
            for i in range(1, len(redoEvent)):
                if redoEvent[i] != None:
                    doc.rgb[i - 1].data = redoEvent[i]
            self.redoList[-1].close()
            self.redoList = self.redoList[0:-1]

    def undo(self, doc):
        print "UndoRGB.undo()"
        if len(self.undoList) > 0:
            redoEvent = [doc.getBrightRange()]
            undoEvent = misc.unpickle(self.undoList[-1])
            doc.setBrightRange(undoEvent[0])
            for i in range(1, len(undoEvent)):
                if undoEvent[i] != None:
                    redoEvent.append(doc.rgb[i - 1].data)
                    doc.rgb[i - 1].data = undoEvent[i]
                else:
                    redoEvent.append(None)
            self.undoList[-1].close()
            self.undoList = self.undoList[0:-1]
            self.redoList.append(misc.pickle(redoEvent))
