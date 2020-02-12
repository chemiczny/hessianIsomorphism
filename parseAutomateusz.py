#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 12 15:50:23 2020

@author: michal
"""

from glob import glob
from os.path import isdir, join, basename
from os import makedirs
from CppParser import CppParser

automateuszFiles = glob("testData/automateusz_cpp_backup_low_level_optimized_ey/d2_ee*ey.cpp")
parsedDir = "automateuszParsedForm"

if not isdir(parsedDir):
    makedirs(parsedDir)
    
for automateuszFile in automateuszFiles:
    newFile = join( parsedDir, basename(automateuszFile)  )
    
    cppParser = CppParser( automateuszFile )
    cppParser.parse()
    cppParser.rewriteCppFile(newFile)
    