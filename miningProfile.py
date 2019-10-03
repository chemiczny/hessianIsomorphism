#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct  3 09:56:52 2019

@author: michal
"""

from subgraphMiner import SubgraphMiner

import cProfile, pstats, io
pr = cProfile.Profile()
pr.enable()

sm = SubgraphMiner(200, "testData", "graphDir", "fsDir", "mining.log" )
sm.buildGraphSet(True)
sm.initSubgraphs()
for i in range(1):
    sm.miningIteration()


pr.disable()
s = io.StringIO()
sortby = 'cumulative'
ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
ps.print_stats()

logFile = open("mining.profile", 'w')
logFile.write(s.getvalue())
logFile.close()