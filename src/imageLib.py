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

import math
from math import *
import numpy
import time

from scipy import weave, ndimage
from PyQt4 import QtCore, QtGui

from config import Config


def transform(data, xtranslate, ytranslate, xcenter, ycenter, angle=0, scalex=1, scaley=1, canvas=False):
    """
    @return: transformed numpy image data. This is the main work horse of this library, this is requires scipy because of the inline C. The pure python version transform2 for a simple rotate is about 110 times slower compared to this one."""
    startTime = time.time()

    xtranslate = float(xtranslate)
    ytranslate = float(ytranslate)
    xcenter = float(xcenter)
    ycenter = float(ycenter)
    angle = float(angle)
    scalex = float(scalex)
    scaley = float(scaley)

    rcos = cos(angle)
    rsin = sin(angle)
    print "xtranslate=" + str(xtranslate) + ", ytranslate=" + str(ytranslate) + ", xcenter=" + str(
        xcenter) + ", ycenter=" + str(ycenter) + ", angle=" + str(angle) + ", scalex=" + str(
        scalex) + ", scaley=" + str(scaley) + ", rcos=" + str(rcos) + ", rsin=" + str(rsin) + ", canvas=" + str(
        canvas) + "\n"
    maxx = 0
    maxy = 0
    if canvas:
        print "Going to fit canvas\n"
        if xtranslate != 0 and ytranslate != 0:
            print "WARNING: Fit canvas with translate"
            xtranslate = 0
            ytranslate = 0
        maxx = data.shape[1] * scalex
        maxy = data.shape[0] * scaley
        x1 = xcenter + ((-xcenter) * rcos - (-ycenter) * rsin) * scalex
        y1 = ycenter + ((-xcenter) * rsin + (-ycenter) * rcos) * scaley
        x2 = xcenter + ((float(data.shape[1]) - xcenter) * rcos - (-ycenter) * rsin) * scalex
        y2 = ycenter + ((float(data.shape[1]) - xcenter) * rsin + (-ycenter) * rcos) * scaley
        x3 = xcenter + ((-xcenter) * rcos - (float(data.shape[0]) - ycenter) * rsin) * scalex
        y3 = ycenter + ((-xcenter) * rsin + (float(data.shape[0]) - ycenter) * rcos) * scaley
        x4 = xcenter + ((float(data.shape[1]) - xcenter) * rcos - (float(data.shape[0]) - ycenter) * rsin) * scalex
        y4 = ycenter + ((float(data.shape[1]) - xcenter) * rsin + (float(data.shape[0]) - ycenter) * rcos) * scaley
        maxx = max([x1, x2, x3, x4])
        minx = min([x1, x2, x3, x4])
        maxy = max([y1, y2, y3, y4])
        miny = min([y1, y2, y3, y4])
        if (miny < 0):
            maxy = maxy - miny
            ytranslate = -miny
        if (minx < 0):
            maxx = maxx - minx
            xtranslate = -minx
    else:
        maxx = data.shape[1]
        maxy = data.shape[0]
    print "maxx=" + str(maxx) + ", maxy=" + str(maxy) + "\n"
    newdata = numpy.empty((maxy, maxx), data.dtype.char)
    newdata.fill(data.mean())
    ny = newdata.shape[0]
    nx = newdata.shape[1]
    oy = data.shape[0]
    ox = data.shape[1]

    code = """
           double rx=0;
           double ry=0;
           double f_1, f_2;
           double a, b, c, d;
           for(int y=0; y<ny; y++){
            for(int x=0; x<nx; x++){
                rx=xcenter+((((double)x)-xcenter-xtranslate)*rcos - (((double)y)-ycenter-ytranslate)*rsin)/scalex;
                ry=ycenter+((((double)x)-xcenter-xtranslate)*rsin + (((double)y)-ycenter-ytranslate)*rcos)/scaley;
                if( (rx >= 0 && (rx+1) < ox) && (ry>=0 && (ry+1) < oy)){
                    //Bi-linear Interpolation
                    a=data[(int)ry * ox+(int)rx];
                    b=data[(int)ry * ox+ (int)rx+1];
                    c=data[((int)ry+1) *ox + (int)rx];
                    d=data[((int)ry+1)*ox+ (int)rx+1];
                    f_1=((int)rx+1-rx)*a+(rx-(int)rx)*b;
                    f_2=((int)rx+1-rx)*c+(rx-(int)rx)*d;
                    newdata[y*nx+x]=((int)ry+1-ry)*f_1+(ry-(int)ry)*f_2;
                }
            }
           }
           """
    data = numpy.cast[Config().getIDataType()](data)
    newdata = numpy.cast[Config().getIDataType()](newdata)
    weave.inline(code,
                 ['data', 'newdata', 'nx', 'ny', 'ox', 'oy', 'xcenter', 'ycenter', 'xtranslate', 'ytranslate', 'rsin',
                  'rcos', 'scalex', 'scaley'], compiler='gcc')

    print "TIME: imageLib.transform() " + str(time.time() - startTime) + " s"
    return newdata


def transform2(data, xtranslate, ytranslate, xcenter, ycenter, angle=0, scalex=1, scaley=1, canvas=False):
    """Like transform() but all in python"""

    startTime = time.time()
    xtranslate = float(xtranslate)
    ytranslate = float(ytranslate)
    xcenter = float(xcenter)
    ycenter = float(ycenter)
    angle = float(angle)
    scalex = float(scalex)
    scaley = float(scaley)

    rcos = cos(angle)
    rsin = sin(angle)
    print "xtranslate=" + str(xtranslate) + ", ytranslate=" + str(ytranslate) + ", xcenter=" + str(
        xcenter) + ", ycenter=" + str(ycenter) + ", angle=" + str(angle) + ", scalex=" + str(
        scalex) + ", scaley=" + str(scaley) + ", rcos=" + str(rcos) + ", rsin=" + str(rsin) + ", canvas=" + str(
        canvas) + "\n"
    maxx = 0
    maxy = 0
    if (canvas):
        print "Going to fit canvas\n"
        if (xtranslate != 0 and ytranslate != 0):
            print "WARNING: Fit canvas with translate"
            xtranslate = 0
            ytranslate = 0
        maxx = data.shape[1] * scalex
        maxy = data.shape[0] * scaley
        x1 = xcenter + ((-xcenter) * rcos - (-ycenter) * rsin) * scalex
        y1 = ycenter + ((-xcenter) * rsin + (-ycenter) * rcos) * scaley
        x2 = xcenter + ((float(data.shape[1]) - xcenter) * rcos - (-ycenter) * rsin) * scalex
        y2 = ycenter + ((float(data.shape[1]) - xcenter) * rsin + (-ycenter) * rcos) * scaley
        x3 = xcenter + ((-xcenter) * rcos - (float(data.shape[0]) - ycenter) * rsin) * scalex
        y3 = ycenter + ((-xcenter) * rsin + (float(data.shape[0]) - ycenter) * rcos) * scaley
        x4 = xcenter + ((float(data.shape[1]) - xcenter) * rcos - (float(data.shape[0]) - ycenter) * rsin) * scalex
        y4 = ycenter + ((float(data.shape[1]) - xcenter) * rsin + (float(data.shape[0]) - ycenter) * rcos) * scaley
        maxx = max([x1, x2, x3, x4])
        minx = min([x1, x2, x3, x4])
        maxy = max([y1, y2, y3, y4])
        miny = min([y1, y2, y3, y4])
        if (miny < 0):
            maxy = maxy - miny
            ytranslate = -miny
        if (minx < 0):
            maxx = maxx - minx
            xtranslate = -minx
    else:
        maxx = data.shape[1]
        maxy = data.shape[0]
    print "maxx=" + str(maxx) + ", maxy=" + str(maxy) + "\n"
    newdata = numpy.empty((maxy, maxx), data.dtype.char)
    newdata.fill(data.mean())
    for y in range(0, newdata.shape[0]):
        for x in range(0, newdata.shape[1]):
            rx = xcenter + (
                           (float(x) - xcenter - xtranslate) * rcos - (float(y) - ycenter - ytranslate) * rsin) / scalex
            ry = ycenter + (
                           (float(x) - xcenter - xtranslate) * rsin + (float(y) - ycenter - ytranslate) * rcos) / scaley
            if (rx >= 0 and (rx + 1) < data.shape[1]) and (ry >= 0 and (ry + 1) < data.shape[0]):
                # Bi-linear Interpolation
                a = data[int(ry), int(rx)]
                b = data[int(ry), int(rx) + 1]
                c = data[int(ry) + 1, int(rx)]
                d = data[int(ry) + 1, int(rx) + 1]
                f_1 = (int(rx) + 1 - rx) * a + (rx - int(rx)) * b
                f_2 = (int(rx) + 1 - rx) * c + (rx - int(rx)) * d
                newdata[y][x] = (int(ry) + 1 - ry) * f_1 + (ry - int(ry)) * f_2

    print "TIME: imageLib.transform2() " + str(time.time() - startTime) + " s"
    return newdata


def rotate(data, angle, fitCanvas):
    """
    Rotate image
    @param angle: Angle to rotate the image in radians.
    @type angle: number
    @param fitCanvas:  if True will enlarge size of image to fit rotation.
    """
    return transform(data, 0, 0, data.shape[1] / 2., data.shape[0] / 2., angle, 1, 1, fitCanvas)


def power(data, power):
    return data ** power


#
# x11, y11 - point 1 aligner
# x12, y12 - point 1 alignee
# x21, y21 - point 2 aligner
# x22, y22 - point 2 alignee
def align(data, x11, y11, x12, y12, x21, y21, x22, y22):
    """Aligns data based on given points, x12, y12 and x22, y22 should be the points on data that you want to mach up with x11, y11, x21, y21"""
    print str(x11) + "," + str(y11) + "," + str(x12) + "," + str(y12) + "," + str(x21) + "," + str(y21) + "," + str(
        x22) + "," + str(y22)
    theta = atan2(y21 - y11, x21 - x11)
    alpha = atan2(y22 - y12, x22 - x12)
    phi = alpha - theta
    rsin = sin(phi)
    rcos = cos(phi)
    x4 = abs((x12 - x22) * rcos - (-y12 + y22) * rsin)
    y4 = abs((x12 - x22) * rsin + (-y12 + y22) * rcos)
    # print "=="+str(x4)+" "+str(y4)
    # print "+="+str(x21-x11)+" "+str(y21-y11)
    scalex = abs(x21 - x11) / x4
    scaley = abs(y21 - y11) / y4
    xtranslate = x21 - x22
    ytranslate = y21 - y22
    return transform(data, xtranslate, ytranslate, x22, y22, phi, scalex, scaley)


def center(data, x, y):
    """
    Moves image to make points x, y be center.
    """
    center = numpy.array(data.shape) / 2.0
    xtranslate = center[1] - x
    ytranslate = center[0] - y
    return shift(data, xtranslate, ytranslate)


def scale(data, xscale, yscale, fitCanvas):
    """enlarges or shrinks image"""
    return transform(data, 0, 0, 0, 0, 0, xscale, yscale, fitCanvas)


def shift(data, xshift, yshift):
    """Moves image over up, down, and left and right by certain many pixels."""
    return transform(data, xshift, yshift, 0, 0)


def sum(data, data1):
    """@return: sum of data and data1"""
    return data + data1


def quadsum(data, indexes, documents):
    n = len(indexes) + 1
    d = data ** 2.
    for i in indexes:
        d += documents[i].data ** 2
    return d ** (1. / 2.)


# XXX: Replace d.max() with dtype max
def subtract(data, data1):
    """Subtract data1 from data"""
    d = data - data1
    return numpy.clip(d, 0, d.max())


def average(data, indexes, documents):
    """Averages images, documents is a list of documents and indexes is what other images to average with data."""
    n = len(indexes) + 1
    d = data / n
    for i in indexes:
        d = d + documents[i].data / n
    return d


# XXX: Mess with data types correctly
def divide(data, data1, meanRatio=False):
    """Divides one image from other, meanRation uses a 60% ratio method on data1 before dividing"""
    # TODO: Probably shouldn't clip at 1
    if (meanRatio == False):
        d = data / numpy.clip(data1, 1, data1.max())
        # return numpy.cast[numpy.uint32](d)
        return d
    else:
        x = data1.shape[1]
        y = data1.shape[0]
        mean = data1[int(0.2 * y):int(0.8 * y), int(0.2 * x):int(0.8 * x)].mean()
        mdata1 = mean / numpy.clip(data1, 1, data1.max())
        print "divide mean: " + str(mean)
        return mdata1 * data


def multiply(data, data1):
    return data * data1


def centroidC(data, xc, yc, radius=5, background=0, rcount=0):
    """Centroid tries to find the exact center of a star based on initial guess points xc, yc."""
    print "xc, yc = " + str(xc) + ", " + str(yc)
    print "background = " + str(background)
    code = """
    int xci=(int)xc-radius;
    int xcf=(int)xc+radius;
    int yci=(int)yc-radius;
    int ycf=(int)yc+radius;
    double centerx=0.0;
    double centery=0.0;
    for(int x=xci; x<=xcf; x++){
        for(int y=yci; y<=ycf; y++){
            if(x >= 0 && x < nx && y >=0 && y < ny){
                t+=data[y*nx+x]-background;
                centerx+=x*(data[y*nx+x]-background);
                centery+=y*(data[y*nx+x]-background);
            }
        }
    }
    center[0]=centerx/t;
    center[1]=centery/t;
    """
    center = numpy.array([0.0, 0.0], Config().getIDataType())
    t = float(0.0)
    xc = float(xc)
    yc = float(yc)
    background = float(background)
    nx = data.shape[1]
    ny = data.shape[0]
    weave.inline(code, ['data', 'center', 'radius', 'background', 't', 'nx', 'ny', 'xc', 'yc'], compiler='gcc')
    if (abs(center[0] - xc) > 0.01 or abs(center[1] - yc) > 0.01) and rcount < 20:
        return centroidC(data, center[0], center[1], radius, background, rcount + 1)
    else:
        if (rcount == 20):
            print "WARNING: Centroid recursion limit hit."
        return [center[0], center[1]]


# XXX: This needs improvement
def centroid(data, xc, yc, radius=5, background=0, rcount=0):
    """Centroid tries to find the exact center of a star based on initial guess points xc, yc."""
    print "xc, yc = " + str(xc) + ", " + str(yc)
    print "background = " + str(background)
    t = 0
    centerx = 0
    centery = 0
    nx = data.shape[1]
    ny = data.shape[0]
    for x in range(int(xc) - radius, int(xc) + radius + 1):
        for y in range(int(yc) - radius, int(yc) + radius + 1):
            if x >= 0 and x < nx and y > 0 and y < ny:
                t += data[y][x] - background
                centerx += x * (data[y][x] - background)
                centery += y * (data[y][x] - background)
    centerx = centerx / t
    centery = centery / t
    if (abs(centerx - xc) > 0.01 or abs(centery - yc) > 0.01) and rcount < 50:
        return centroid(data, centerx, centery, radius, background, rcount + 1)
    else:
        if (rcount == 50):
            print "WARNING: Centroid recursion limit hit."
        return [centerx, centery]


# Return matrix meant for looking at with values 0-255
def reduceToVisual(data, brightRange):
    """
    Reduce data to 8bit using back, range as what data should be used.
    @param brightRange: [background, range]
    """
    startTime = time.time()
    ratio = 0
    if (brightRange[1] - brightRange[0]) > 0:
        ratio = 255.0 / float(brightRange[1] - brightRange[0])
    tmpData = numpy.subtract(data, brightRange[0])
    tmpData = numpy.multiply(numpy.cast[Config().getIDataType()](tmpData), ratio)
    tmpData = numpy.add(tmpData, 0.5)
    tmpData = numpy.clip(tmpData, 0, 255)
    print "TIME: reduceToVisual() " + str(time.time() - startTime) + " s"
    return numpy.cast[numpy.uint8](tmpData)


def reducedRGBtoBufferQImage(rgb):
    """Takes 0-255 [r, g, b] returns [buffer, image]"""
    tmpData = numpy.zeros((rgb[0].shape[0], rgb[0].shape[1]), numpy.uint32)
    m16 = 16 * numpy.ones((rgb[0].shape[0], rgb[0].shape[1]), numpy.uint32)
    m8 = 8 * numpy.ones((rgb[0].shape[0], rgb[0].shape[1]), numpy.uint32)
    tmpData = tmpData.__or__(rgb[0].__lshift__(m16))
    tmpData = tmpData.__or__(rgb[1].__lshift__(m8))
    tmpData = (tmpData.__or__(rgb[2])).astype(numpy.uint32)
    buffer = tmpData.tostring()
    image = QtGui.QImage(buffer, rgb[0].shape[1], rgb[0].shape[0], QtGui.QImage.Format_RGB32)
    return [buffer, image]


def toHSL(r, g, b):
    """
    Takes 0-1 rgb space values and converts to 0-1 hsl space values
    @return: [h, s, l]
    """

    startTime = time.time()
    h = numpy.zeros(r.shape, Config().getIDataType())
    s = numpy.zeros(r.shape, Config().getIDataType())
    l = numpy.zeros(r.shape, Config().getIDataType())
    code = """
        double r1;
        double g1;
        double b1;
        double min;
        double max;
        for(int y=0; y<ny; y++){
            for(int x=0; x<nx; x++){
                r1=r[y*nx+x];
                g1=g[y*nx+x];
                b1=b[y*nx+x];
                if(r1 < g1){
                    min=r1;
                } else {
                    min=g1;
                }
                if(b1 < min){
                    min=b1;
                }
                if(r1 > g1 && r1 > b1){
                    max=r1;
                    if(g1 >= b1){
                        h[y*nx+x]=(1./6.)*(g1-b1)/(r1-min);
                    } else {
                        h[y*nx+x]=(1./6.)*(g1-b1)/(r1-min) + 1.;
                    }
                } else if (g1 > r1 && g1 > b1){
                    max=g1;
                    h[y*nx+x]=(1./6.)*(b1-r1)/(g1-min) + (1./3.);
                } else if (b1 > r1 && b1 > g1){
                    max=b1;
                    h[y*nx+x]=(1./6.)*(r1-g1)/(b1-min) + (2./3.);
                } else {
                    max=r1;
                }
                l[y*nx+x]=(max+min)*0.5;
                if(max-min == 0){
                    s[y*nx+x]=0;
                } else if(l[y*nx+x] <= 0.5 && l[y*nx+x] != 0){
                    s[y*nx+x]=(max-min)/(max+min);
                } else {
                    s[y*nx+x]=(max-min)/(2.-max-min);
                }
            }
        }
    """
    ny = r.shape[0]
    nx = r.shape[1]
    weave.inline(code, ['r', 'g', 'b', 'h', 's', 'l', 'nx', 'ny'], compiler='gcc')
    print "TIME: toHSL() " + str(time.time() - startTime) + " s"
    return [h, s, l]


def toHSL2(r, g, b):
    """Like toHSL() but in python"""
    startTime = time.time()
    rmin = (r < g) & (r < b)
    rmax = (r > g) & (r > b)
    rmax1 = rmax & (g >= b)
    rmax2 = rmax & (g < b)

    gmax = (g > r) & (g > b)
    gmin = (g < r) & (g < b)

    bmax = (b > r) & (b > g)
    bmin = (b < r) & (b < g)

    min = numpy.zeros(r.shape, Config().getIDataType())
    min[rmin] = r[rmin]
    min[gmin] = g[gmin]
    min[bmin] = b[bmin]

    del rmin
    del gmin
    del bmin

    equals = (r == g) & (r == b)
    max = numpy.zeros(r.shape, Config().getIDataType())
    max[rmax] = r[rmax]
    max[gmax] = g[gmax]
    max[bmax] = b[bmax]
    max[equals] = r[equals]

    del rmax

    h = numpy.zeros(r.shape, Config().getIDataType())
    h[rmax1] = (1. / 6.) * (g[rmax1] - b[rmax1]) / (r[rmax1] - min[rmax1])
    h[rmax2] = (1. / 6.) * (g[rmax2] - b[rmax2]) / (r[rmax2] - min[rmax2]) + 1.
    h[gmax] = (1. / 6.) * (b[gmax] - r[gmax]) / (g[gmax] - min[gmax]) + (1. / 3.)
    h[bmax] = (1. / 6.) * (r[bmax] - g[bmax]) / (b[bmax] - min[bmax]) + (2. / 3.)

    del rmax1
    del rmax2
    del gmax
    del bmax

    l = (max + min) * .5
    lhalf1 = (l <= 0.5) & (l != 0.)
    lhalf2 = (l > 0.5)
    s = numpy.zeros(r.shape, Config().getIDataType())
    # if max == min
    s[lhalf1] = (max[lhalf1] - min[lhalf1]) / (max[lhalf1] + min[lhalf1])
    s[lhalf2] = (max[lhalf2] - min[lhalf2]) / (2. - max[lhalf2] - min[lhalf2])

    print "TIME: toHSL2() " + str(time.time() - startTime) + " s"
    return [h, s, l]


def toRGB(h, s, l):
    """Takes 0-1 hsl space values returns 0-1 rgb space values [r, g, b]"""
    startTime = time.time()
    r = numpy.zeros(h.shape, Config().getIDataType())
    g = numpy.zeros(h.shape, Config().getIDataType())
    b = numpy.zeros(h.shape, Config().getIDataType())
    ny = h.shape[0]
    nx = h.shape[1]
    code = """
        double temp2;
        double temp1;
        double temp3_r;
        double temp3_g;
        double temp3_b;
        for(int y=0; y<ny; y++){
            for(int x=0; x<nx; x++){
                if(l[y*nx+x] < 0.5){
                    temp2=l[y*nx+x]*(1.+s[y*nx+x]);
                } else {
                    temp2=l[y*nx+x]+s[y*nx+x]-(l[y*nx+x]*s[y*nx+x]);
                }
                temp1=2.*l[y*nx+x]-temp2;
                temp3_r=h[y*nx+x]+(1./3.);
                temp3_g=h[y*nx+x];
                temp3_b=h[y*nx+x]-(1./3.);
                if(temp3_r < 0.) temp3_r = temp3_r+1.;
                if(temp3_g < 0.) temp3_g = temp3_g+1.;
                if(temp3_b < 0.) temp3_b = temp3_b+1.;
                if(temp3_r > 1.) temp3_r = temp3_r-1.;
                if(temp3_g > 1.) temp3_g = temp3_g-1.;
                if(temp3_b > 1.) temp3_b = temp3_b-1.;
                if(temp3_r < (1./6.)){
                    r[y*nx+x]=temp1+(temp2-temp1)*6.*temp3_r;
                } else if(temp3_r >= (1./6.) && temp3_r < 0.5){
                    r[y*nx+x]=temp2;
                } else if(temp3_r >= 0.5 && temp3_r < (2./3.)){
                    r[y*nx+x]=temp1+(temp2-temp1)*((2./3.)-temp3_r)*6.;
                } else {
                    r[y*nx+x]=temp1;
                }
                if(temp3_g < (1./6.)){
                    g[y*nx+x]=temp1+(temp2-temp1)*6.*temp3_g;
                } else if(temp3_g >= (1./6.) && temp3_g < 0.5){
                    g[y*nx+x]=temp2;
                } else if(temp3_g >= 0.5 && temp3_g < (2./3.)){
                    g[y*nx+x]=temp1+(temp2-temp1)*((2./3.)-temp3_g)*6.;
                } else {
                    g[y*nx+x]=temp1;
                }
                if(temp3_b < (1./6.)){
                    b[y*nx+x]=temp1+(temp2-temp1)*6.*temp3_b;
                } else if(temp3_b >= (1./6.) && temp3_b < 0.5){
                    b[y*nx+x]=temp2;
                } else if(temp3_b >= 0.5 && temp3_b < (2./3.)){
                    b[y*nx+x]=temp1+(temp2-temp1)*((2./3.)-temp3_b)*6.;
                } else {
                    b[y*nx+x]=temp1;
                }

            }
        }
    """
    print "TIME: toRGB() " + str(time.time() - startTime) + " s"
    weave.inline(code, ['r', 'g', 'b', 'h', 's', 'l', 'nx', 'ny'], compiler='gcc')
    return [r, g, b]


# XXX: This needs to be faster
def toRGB2(h, s, l):
    """like toRGB by all in python"""
    startTime = time.time()

    temp2 = numpy.zeros(h.shape, Config().getIDataType())
    t = (l < 0.5)
    temp2[t] = l[t] * (1. + s[t])
    t = (l >= 0.5)
    temp2[t] = l[t] + s[t] - (l[t] * s[t])
    temp1 = 2. * l - temp2

    h1 = numpy.array(h)
    temp3 = [(h1 + (1. / 3.)), h1, (h1 - (1. / 3.))]

    colors = [numpy.zeros(h.shape, Config().getIDataType()), numpy.zeros(h.shape, Config().getIDataType()),
              numpy.zeros(h.shape, Config().getIDataType())]
    i = 0
    for color in temp3:
        t = (color < 0.)
        color[t] = color[t] + 1.
        t = (color > 1.)
        color[t] = color[t] - 1.
        t = (color < (1. / 6.))
        colors[i][t] = temp1[t] + (temp2[t] - temp1[t]) * 6. * color[t]
        t = (color >= (1. / 6.)) & (color < (0.5))
        colors[i][t] = temp2[t]
        t = (color >= 0.5) & (color < (2. / 3.))
        colors[i][t] = temp1[t] + (temp2[t] - temp1[t]) * ((2. / 3.) - color[t]) * 6.
        t = (color >= (2. / 3.))
        colors[i][t] = temp1[t]
        i = i + 1

    print "TIME: toRGB2() " + str(time.time() - startTime) + " s"
    return colors


def autoContrast(histogram, height, width):
    """Tries to calculate a good starting point for background and range.
       returns [min, max]
    """
    csum = numpy.cumsum(histogram)
    cmax = width * height
    crange = cmax * .01
    searchParam = [crange, cmax - crange]
    print "autoContrast, searchParam - " + str(searchParam)
    search = csum.searchsorted(searchParam)
    print "autoContrast, search - " + str(search)
    rmin = search[0]
    rmax = search[1]
    return [rmin, rmax]


def lesser(data, data1):
    """@return: a matrix where every entry less of the two datasets entries"""
    sdata = data.copy()
    sdata1 = data1.copy()
    sdata[data > data1] = 0
    sdata1[data1 > data] = 0
    return sdata + sdata1


def convolve(data, matrix):
    d = ndimage.convolve(data, matrix)
    max = d.max()
    if max < 0:
        max = 0
    return numpy.clip(d, 0, max)


def extractBrightRange(header):
    """
    Tries to get background and range data from header.
    @return: [min, max] - if found, None - if it can't find it.
    """
    try:
        a = header["BACKGRD"]
        b = header["RANGE"]
        return [a[0], b[0]]
    except KeyError:
        return None
    except:
        raise


def DDP(data, a, b, edgeEmphasis=False, radius=1., stddev=1.):
    """
    Applies DDP to image (See: http://www.asahi-net.or.jp/~rt6k-okn/its98/ddp1.htm)
    @param data: The working data
    @param edgeEmphasis: If edge emphasis should be done
    @param radius: The radius of the Gaussian blur convolution.
    @param stddev: The stddev used to make the convolution matrix.
    @returns image having been throught he processing.
    """
    if edgeEmphasis:
        # Gaussian blur
        t = numpy.arange(-radius, radius + 1)
        t = (1. / (stddev * (2. * math.pi) ** (1. / 2.))) * math.e ** -(t ** 2. / (2. * stddev ** 2.))
        t = numpy.array(numpy.outer(t, t), Config().getIDataType())
        t = t / t.sum()
        d = convolve(data, t)
    else:
        d = numpy.array(data)
    # DDP
    k = d.mean()
    newData = k * (data / (d + a)) + b
    return newData


def resizeCanvas(data, x, y, center):
    newData = numpy.zeros([y, x], Config().getIDataType())
    if data.shape[0] < y:
        if center:
            yn1 = int((y - data.shape[0]) / 2)
            yn2 = yn1 + data.shape[0]
            yo1 = 0
            yo2 = data.shape[0]
        else:
            yn1 = 0
            yn2 = data.shape[0]
            yo1 = 0
            yo2 = yn2
    else:
        if center:
            yn1 = 0
            yn2 = y
            yo1 = int((data.shape[0] - y) / 2)
            yo2 = yo1 + y
        else:
            yn1 = 0
            yn2 = y
            yo1 = 0
            yo2 = y
    if data.shape[1] < x:
        if center:
            xn1 = int((x - data.shape[1]) / 2)
            xn2 = xn1 + data.shape[1]
            xo1 = 0
            xo2 = data.shape[1]
        else:
            xn1 = 0
            xn2 = data.shape[0]
            xo1 = 0
            xo2 = xn2
    else:
        if center:
            xn1 = 0
            xn2 = x
            xo1 = int((data.shape[1] - x) / 2)
            xo2 = xo1 + x
        else:
            xn1 = 0
            xn2 = x
            xo1 = 0
            xo2 = x

    newData[yn1:yn2, xn1:xn2] = data[yo1:yo2, xo1:xo2]
    return newData


def bin(data, numpixels):
    newdata = numpy.zeros((int(data.shape[0] / numpixels), int(data.shape[1] / numpixels)), Config().getIDataType())
    nx = newdata.shape[1]
    ny = newdata.shape[0]
    ox = data.shape[1]
    oy = data.shape[0]

    code = """
        for (int x = 0; x < nx; x++){
            for (int y = 0; y < ny; y++){
                for(int x1=x*numpixels; x1 < x*numpixels+numpixels; x1++){
                    for(int y1=y*numpixels; y1 < y*numpixels+numpixels; y1++){
                        newdata[y*nx+x]+=data[y1*ox+x1];
                    }
                }
            }
        }
        """
    weave.inline(code, ['data', 'newdata', 'nx', 'ny', 'ox', 'oy', 'numpixels'], compiler='gcc')
    return newdata
