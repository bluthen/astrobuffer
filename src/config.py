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

from PyQt4 import QtCore
import numpy


class Config:
    """ Astrobuffer config singleton """

    class __impl:
        """ Implementation of the singleton interface """

        def __init__(self):
            self.con = QtCore.QSettings("ColdstoneLabs", "AstroBuffer")
            self.con.beginGroup("General Options")
            prec = self.con.value("Precision").toInt()[0]
            self.con.endGroup()
            if (prec == 64):
                self.imageDType = numpy.float64
                self.precision = 64
            else:
                self.imageDType = numpy.float32
                self.precision = 32

        def getGeometry(self):
            self.con.beginGroup("General Options")
            s = self.con.value("Geometry").toSize()
            self.con.endGroup()
            return s

        def setGeometry(self, size):
            self.con.beginGroup("General Options")
            self.con.setValue("Geometry", QtCore.QVariant(size))
            self.con.endGroup()
            self.con.sync()

        def getSaveDir(self):
            self.con.beginGroup("General Options")
            s = self.con.value("SaveDir").toString()
            self.con.endGroup()
            return s

        def setSaveDir(self, dir):
            self.con.beginGroup("General Options")
            self.con.setValue("SaveDir", QtCore.QVariant(dir))
            self.con.endGroup()
            self.con.sync()

        def getIDataType(self):
            return self.imageDType

        def getPrecision(self):
            return self.precision

        def setPrecision(self, precision):
            self.con.beginGroup("General Options")
            if (precision == 64):
                self.con.setValue("Precision", QtCore.QVariant(64))
                self.imageDType = numpy.float64
                self.precision = 64
            else:
                self.con.setValue("Precision", QtCore.QVariant(32))
                self.imageDType = numpy.float32
                self.precision = 32
            self.con.endGroup()
            self.con.sync()

        def getSettingsObj(self):
            return self.con

    # storage for the instance reference
    __instance = None

    def __init__(self):
        """ Create singleton instance """
        # Check whether we already have an instance
        if Config.__instance is None:
            # Create and remember instance
            Config.__instance = Config.__impl()

        # Store instance reference as the only member in the handle
        self.__dict__['_Config__instance'] = Config.__instance

    def __getattr__(self, attr):
        """ Delegate access to implementation """
        return getattr(self.__instance, attr)

    def __setattr__(self, attr, value):
        """ Delegate access to implementation """
        return setattr(self.__instance, attr, value)
