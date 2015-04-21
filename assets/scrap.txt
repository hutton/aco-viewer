#!/usr/bin/python
# -*- coding: utf-8 -*-
# quick script no warranties whatsoever
import struct



class ColorSwatch():
    def __init__(self, fp):
        self.rawdata  = struct.unpack(">5H",fp.read(10))
        namelen, = struct.unpack(">I",fp.read(4))
        cp = fp.read(2*namelen)
        self.name = cp[0:-2].decode('utf-16-be')
        self.typename = self.colorTypeName()


    def colorTypeName(self):
        try:
            return {0:"RGB", 1:"HSB",
                    2:"CMYK",7:"Lab",
                    8:"Grayscale"}[self.rawdata[0]]
        except IndexError:
            print self.rawdata[0]

    def __strCMYK(self):
        rgb8bit = map(lambda a: (65535 - a)/655.35, self.rawdata[1:])
        return "{name} ({typename}): {0}% {1}% {2}% {3}%".format(*rgb8bit,**self.__dict__)

    def __strRGB(self):
        rgb8bit = map(lambda a: a/256,self.rawdata[1:4])
        return "{name} ({typename}): #{0:x}{1:x}{2:x}".format(*rgb8bit,**self.__dict__)

    def __strGrayscale(self):
        gray = self.rawdata[1]/100.
        return "{name} ({typename}): {0}%".format(gray,**self.__dict__)

    def __str__(self):
        return {0: self.__strRGB, 1:"HSB",
                2:self.__strCMYK,7:"Lab",
                8:self.__strGrayscale}[self.rawdata[0]]()

with open("test.aco", "rb") as acoFile:
    #skip ver 1 file
    head = acoFile.read(2)
    ver, = struct.unpack(">H",head)
    if (ver != 1):
        raise TypeError("Probably not a adobe aco file")
    count = acoFile.read(2)
    cnt, = struct.unpack(">H",count)
    acoFile.seek(cnt*10,1)

    #read ver2 file
    head = acoFile.read(2)
    ver, = struct.unpack(">H",head)
    if (ver != 2):
        raise TypeError("Probably not a adobe aco file")
    count = acoFile.read(2)
    count, = struct.unpack(">H",count)
    for _ in range(count):
        swatch = ColorSwatch(acoFile)
        print str(swatch)
