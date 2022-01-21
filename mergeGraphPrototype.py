#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mar  6 11:51:48 2021

@author: michal
"""
from os.path import isdir, join, basename
from os import makedirs
from CppParser import CppParser
from collections import defaultdict

def getCanonicalKeysFromParser(parser):
    keys = set([])
    totalFormNo = 0
    for node in parser.function.graph.nodes:
        if "form" in parser.function.graph.nodes[node]:
            keys.add( parser.function.graph.nodes[node]["form"].generateKey() )
            totalFormNo += 1
            
    return keys, totalFormNo

parsedDir = "mergedParsedForm"

if not isdir(parsedDir):
    makedirs(parsedDir)
    
#fileA = "/home/michal/Projects/hessianIsomorphism/testData/mergingData/d_ne_dd_A0.ey.cpp"
#fileB = "/home/michal/Projects/hessianIsomorphism/testData/mergingData/d_ne_dd_B0.ey.cpp"
    
fileA = "testData/automateusz_cpp_backup_low_level_optimized_ey/d2_ee_psss_AC.ey.cpp"
#fileB = "testData/automateusz_cpp_backup_low_level_optimized_ey/d2_ee_ppss_AA.ey.cpp"
fileB = "testData/automateusz_cpp_backup_low_level_optimized_ey/d2_ee_psss_ACrenamed.ey.cpp"

resultFile = join( parsedDir, "fatality.cpp" )

cppParserA = CppParser( fileA )
cppParserA.parse()
origName = cppParserA.function.name 
cppParserA.function.name = "A"
cppParserA.function.markNodesOrigin()

cppParserB = CppParser( fileB )
cppParserB.parse()
cppParserB.function.name = "B"
cppParserB.function.markNodesOrigin()

cppParserB.function.analyseOrigin()
cppParserA.function.analyseOrigin()

keysA, formNoA = getCanonicalKeysFromParser(cppParserA)
keysB, formNoB = getCanonicalKeysFromParser(cppParserB)

cppParserA.function.mergeWithExternalGraph( cppParserB.function.graph, cppParserB.function.name )
#print(cppParserA.function.notCanonicalKey2Node.keys())
keysMerge, formNoMerge = getCanonicalKeysFromParser(cppParserA)
cppParserA.function.analyseOrigin()

cppParserA.function.rebuildGraph()
#cppParserA.function.findDeadEnds()
keysMerge2, formNoMerge2 = getCanonicalKeysFromParser(cppParserA)
nodesNo = len(cppParserA.function.graph.nodes)
iters = 0
while True:
    cppParserA.function.rebuildGraph()
    iters += 1
    newNodesNo = len(cppParserA.function.graph.nodes)
    if newNodesNo >= nodesNo:
        break
    else:
        nodesNo = newNodesNo

print("uzbiezniono po ", iters)
cppParserA.function.analyseOrigin()

#mergedCpp = open(join(parsedDir, "test.cpp"), 'w')
#mergedCpp = open("dupa.cpp", 'w')
#cppParserA.function.writeFunctionFromGraph("test", mergedCpp)
#mergedCpp.close()
varValues  = { "ae" : 1.1, "xA" : 1.1, "yA" : 3.3, "zA" : 1.6, "be" : 1.7,
                  "xB" : -0.9, "yB" : 0.3, "zB" : 0.6, "ce" : 1.3, "xC" : 1.4, 
                  "yC" : 1.8, "zC" : 1.2, "de" : 1.3, "xD" : -1.1, "yD" : 1.9, 
                  "zD" : 1.3, "bs" : "{ 0.7, 1.3, 1.5, 1.1, 0.8, 0.2, 0.15, 0.12, 0.1, 0.05}" }
cppParserA.function.name  = origName
cppParserA.writeTest("dupa.cpp", varValues, testCase="prediction")

print("klucze A", len(keysA), formNoA)
print("klucze B", len(keysB), formNoB)
print("A i B", len(keysA & keysB))
print(len(keysA-keysB))
print(len(keysB - keysA))

print("zaraz po mergu ", len(keysMerge), formNoMerge)
print("zaraz po mergu ", len(keysMerge2), formNoMerge2)