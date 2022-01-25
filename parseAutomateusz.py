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
import logging

automateuszFiles = glob("testData/automateusz_cpp_backup_low_level_optimized_ey/d2_ee*ey.cpp")
parsedDir = "automateuszParsedForm"
pickleDir = "pickled"

if not isdir(parsedDir):
    makedirs(parsedDir)
    
if not isdir(pickleDir):
    makedirs(pickleDir)
    
logging.basicConfig(filename='divisionReductionStatus.log', level=logging.INFO)
for automateuszFile in automateuszFiles:
    pickleFile = join(pickleDir, basename(automateuszFile.replace("ey.cpp", "pickle") ) )
    newFile = join( parsedDir, basename(automateuszFile) , pickleFile )
    
    cppParser = CppParser( automateuszFile )
    cppParser.parse()
    cppParser.rewriteCppFile(newFile)
    cppParser.saveGraphFunction()
    
    logging.info( "{name} {status}".format( name = basename(automateuszFile ), status = cppParser.function.strongDivisionReduction ))