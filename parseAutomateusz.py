#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 12 15:50:23 2020

@author: michal
"""

from glob import glob
from os.path import isdir, join, basename, isfile
from os import makedirs, remove
from CppParser import CppParser

automateuszFiles = glob("testData/automateusz_cpp_backup_low_level_optimized_ey/d2_ee*ey.cpp")
parsedDir = "automateuszParsedForm"
pickleDir = "pickled"

if not isdir(parsedDir):
    makedirs(parsedDir)
    
if not isdir(pickleDir):
    makedirs(pickleDir)
    
if isfile('divisionReductionStatus.log'):
    remove('divisionReductionStatus.log')
    
for automateuszFile in sorted(automateuszFiles, reverse = True):
    pickleFile = join(pickleDir, basename(automateuszFile).replace("ey.cpp", "pickle")  )
    newFile = join( parsedDir, basename(automateuszFile) )
    frozenVariables = set([ "xAB", "yAB", "zAB", "xCD", "yCD", "zCD", "xP" , "yP", "zP", "xQ", "yQ", "zQ", "p", "q" ])
    cppParser = CppParser( automateuszFile, frozenVariables, pickleFile  )
    cppParser.parse()
    cppParser.rewriteCppFile(newFile)
    cppParser.saveGraphFunction()
    
    logName = open('divisionReductionStatus.log', "a+")
    logName.write( "{name} {status}\n".format( name = pickleFile, status = cppParser.function.strongDivisionReduction ))
    logName.close()