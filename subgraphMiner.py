#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep 11 11:44:27 2019

@author: michal
"""

from glob import glob
from os import path
from os import mkdir

from CppParser import CppParser

class SubgraphMiner:
    def __init__(self, minSup, sourceDir, graphDir, frequentSubgraphDir):
        self.minSup = minSup
        self.sourceDir = sourceDir
        self.graphDir = graphDir
        
        if not path.isdir(self.graphDir):
            mkdir(self.graphDir)
            
        self.frequentSubgraphDir = frequentSubgraphDir
            
        if not path.isdir(self.frequentSubgraphDir):
            mkdir(self.frequentSubgraphDir)
        
        self.sourceList = glob( path.join( self.sourceDir, "*ey.cpp"  ) )
        self.graphs = []
        
    def buildGraphSet(self, load = False):
        for cpp in self.sourceList:
            
            graphBackup = path.join( self.graphDir, path.basename(cpp).replace(".cpp", ".pickle"))
            miningBackup = path.join( self.frequentSubgraphDir, path.basename(cpp).replace(".cpp", ".pickle"))
            newGraphParser = CppParser(cpp, graphBackup, miningBackup)
            
            if load:
                print("loading graph for: ", cpp)
                newGraphParser.loadGraphFunction()
            else:
                print("building graph for: ", cpp)
                newGraphParser.parse()
                newGraphParser.saveGraphFunction()
            
            self.graphs.append(newGraphParser)
            
    def mining(self):
        self.initSubgraphs()
    
    def initSubgraphs(self):
        for graph in self.graphs:
            graph.initSubgraphs(self.minSup)
            
        
if __name__ == "__main__":
    sm = SubgraphMiner(10, "testData", "graphDir", "fsDir" )
    sm.buildGraphSet(True)
    sm.initSubgraphs()