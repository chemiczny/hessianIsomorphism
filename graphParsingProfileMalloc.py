#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 17 15:49:21 2019

@author: michal
"""

from CppParser import CppParser
import tracemalloc

tracemalloc.start()

#testFile = "testData/automateusz_cpp_backup_low_level_optimized_ey/d2_ee_pppp_AA.ey.cpp"
testFile = "testData/d1_ee/d_ee_ppps_A4.ey.cpp"
   
varValues  = { "ae" : 1.1, "xA" : 1.1, "yA" : 3.3, "zA" : 1.6, "be" : 1.7,
              "xB" : -0.9, "yB" : 0.3, "zB" : 0.6, "ce" : 1.3, "xC" : 1.4, 
              "yC" : 1.8, "zC" : 1.2, "de" : 1.3, "xD" : -1.1, "yD" : 1.9, 
              "zD" : 1.3, "bs" : "{ 0.7, 1.3, 1.5, 1.1, 0.8, 0.2, 0.15, 0.12, 0.1, 0.05}" }

frozenVariables = set([ "xAB", "yAB", "zAB", "xCD", "yCD", "zCD" ])
#frozenVariables = []
cppParser = CppParser(testFile, variables2freeze=frozenVariables)
cppParser.parse()
cppParser.writeTest("dupa.cpp", varValues, testCase="prediction")


snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')

print("[ Top 10 ]")
for stat in top_stats[:10]:
    print(stat)
