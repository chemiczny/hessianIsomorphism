#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 10 10:23:13 2019

@author: michal
"""

from CppParser import CppParser
import cProfile, pstats, io

pr = cProfile.Profile()
pr.enable()

testFile = "testData/d1_ee/d_ee_ppps_A4.ey.cpp"
#testFile = "testData/automateusz_cpp_backup_low_level_optimized_ey/d2_ee_ppss_AA.ey.cpp"
varValues  = { "ae" : 1.1, "xA" : 1.1, "yA" : 3.3, "zA" : 1.6, "be" : 1.7,
              "xB" : -0.9, "yB" : 0.3, "zB" : 0.6, "ce" : 1.3, "xC" : 1.4, 
              "yC" : 1.8, "zC" : 1.2, "de" : 1.3, "xD" : -1.1, "yD" : 1.9, 
              "zD" : 1.3, "bs" : "{ 0.7, 1.3, 1.5, 1.1, 0.8, 0.2, 0.15, 0.12, 0.1, 0.05}" }
    
frozenVariables = set([ "xAB", "yAB", "zAB", "xCD", "yCD", "zCD" ])
cppParser = CppParser(testFile, variables2freeze=frozenVariables)
cppParser.parse()
cppParser.writeTest("dupa.cpp", varValues, testCase="prediction")

pr.disable()
s = io.StringIO()
sortby = 'cumulative'
ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
ps.print_stats()

logFile = open("parsing.profile", 'w')
logFile.write(s.getvalue())
logFile.close()
