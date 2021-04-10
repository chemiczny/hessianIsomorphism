#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mar  6 11:51:48 2021

@author: michal
"""
from os.path import isdir, join, basename
from os import makedirs
from CppParser import CppParser

parsedDir = "mergedParsedForm"

if not isdir(parsedDir):
    makedirs(parsedDir)
    
fileA = "/home/michal/Projects/hessianIsomorphism/testData/mergingData/d_ne_dd_A0.ey.cpp"
fileB = "/home/michal/Projects/hessianIsomorphism/testData/mergingData/d_ne_dd_B0.ey.cpp"
    
resultFile = join( parsedDir, "fatality.cpp" )

cppParserA = CppParser( fileA )
cppParserA.parse()
cppParserA.function.markNodesOrigin()

cppParserB = CppParser( fileB )
cppParserB.parse()
cppParserB.function.markNodesOrigin()

cppParserA.function.mergeWithExternalGraph( cppParserB.function.graph, cppParserB.function.name )
#print(cppParserA.function.notCanonicalKey2Node.keys())
cppParserA.function.rebuildGraph()
cppParserA.function.findDeadEnds()
cppParserA.function.rebuildGraph()

cppParserA.function.analyseOrigin()

mergedCpp = open(join(parsedDir, "test.cpp"), 'w')
cppParserA.function.writeFunctionFromGraph("test", mergedCpp)
mergedCpp.close()
