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


testFile = "testData/automateusz_cpp_backup_low_level_optimized_ey/d2_ee_dppp_AA.ey.cpp"
    
cppParser = CppParser(testFile)
cppParser.parse()
cppParser.writeTest("dupa.cpp", testCase="prediction", reuseVariables=True, printingMode= False)

pr.disable()
s = io.StringIO()
sortby = 'cumulative'
ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
ps.print_stats()

logFile = open("parsing.profile", 'w')
logFile.write(s.getvalue())
logFile.close()
