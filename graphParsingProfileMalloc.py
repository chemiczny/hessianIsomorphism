#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 17 15:49:21 2019

@author: michal
"""

from CppParser import CppParser
import tracemalloc

tracemalloc.start()

testFile = "testData/automateusz_cpp_backup_low_level_optimized_ey/d2_ee_pppp_AA.ey.cpp"
    
cppParser = CppParser(testFile)
cppParser.parse()
cppParser.writeTest("dupa.cpp", testCase="prediction", reuseVariables=True, printingMode= False)


snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')

print("[ Top 10 ]")
for stat in top_stats[:10]:
    print(stat)
