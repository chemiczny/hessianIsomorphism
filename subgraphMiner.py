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
    def __init__(self, minSup, sourceDir, graphDir, frequentSubgraphDir, logFile):
        self.minSup = minSup
        self.sourceDir = sourceDir
        self.graphDir = graphDir
        self.logFile = logFile
        
        lf = open(logFile, 'w')
        lf.close()
        
        if not path.isdir(self.graphDir):
            mkdir(self.graphDir)
            
        self.frequentSubgraphDir = frequentSubgraphDir
            
        if not path.isdir(self.frequentSubgraphDir):
            mkdir(self.frequentSubgraphDir)
        
        self.sourceList = glob( path.join( self.sourceDir, "*ey.cpp"  ) )
        self.graphs = []
        
    def buildGraphSet(self, load = False):
        for cpp in self.sourceList:
            self.append2logFile("Creating seed for "+cpp)
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
            
    def append2logFile(self, message):
        lf = open(self.logFile, 'a')
        lf.write(message+"\n")
        lf.close()
            
    def mining(self):
        self.initSubgraphs()
        self.joinIsomorphs()
        
        initialSize = 1
        maxSize = 3
        
        for i in range(initialSize, maxSize):
            self.miningIteration()
        
    
    def initSubgraphs(self):
        for graph in self.graphs:
            graph.initSubgraphs(self.minSup)
            
        self.joinIsomorphs()
            
    def miningIteration(self):
        for graph in self.graphs:
            graph.subgraphsGrowth()
            
        self.joinIsomorphs()
    
    def joinIsomorphs(self):
        lf = open(self.logFile, "a")
        lf.write("###############MINING STATUS##################\n")
        
        self.isomorphKey2occurence = {}
        allExpr = 0
        
        
        for graph in self.graphs:
            update = graph.getOccurence()
            for key in update:
                allExpr += update[key]
                if key in self.isomorphKey2occurence:
                    self.isomorphKey2occurence[key] += update[key]
                else:
                    self.isomorphKey2occurence[key] = update[key]
                    
        lf.write("unikalne klucze: "+str(len(self.isomorphKey2occurence))+"\n")
        lf.write("liczba wyrazen: "+str( allExpr)+"\n")
        
        key2save = set([])
        
        for key in self.isomorphKey2occurence:
#            print(isomorphKey2occurence[key], key)
            if self.isomorphKey2occurence[key] > self.minSup:
                key2save.add(key)
                
        for graph in self.graphs:
            graph.isomorphs.update(key2save)
            
        lf.write("Po updejcie: \n")
        
        self.isomorphKey2occurence = {}
        allExpr = 0
        
        
        for graph in self.graphs:
            update = graph.getOccurence()
            for key in update:
                allExpr += update[key]
                if key in self.isomorphKey2occurence:
                    self.isomorphKey2occurence[key] += update[key]
                else:
                    self.isomorphKey2occurence[key] = update[key]
                    
        lf.write("unikalne klucze: "+str( len(self.isomorphKey2occurence))+"\n")
        lf.write("liczba wyrazen: " + str( allExpr )+"\n")
        
        for key in self.isomorphKey2occurence:
            lf.write(str(self.isomorphKey2occurence[key])+" "+ key+"\n")
            
        lf.close()
        
        
        
if __name__ == "__main__":
    sm = SubgraphMiner(200, "testData", "graphDir", "fsDir", "mining.log" )
    sm.buildGraphSet(True)
    sm.initSubgraphs()
    for i in range(1):
        sm.miningIteration()
        
    for key in sm.isomorphKey2occurence:
        if not "," in key:
            selected = key
            
    print(selected)
    sm.graphs[0].writeTest("brutality.cpp", "perf")
    sm.graphs[0].replaceIsomorphWithFunction(selected, "testIso")
    sm.graphs[0].writeTest("fatality.cpp", "perf")
    
    lol = open("iso.cpp",'w')
    sm.graphs[0].isomorphs.isomorphs[selected][0].writeFunction( "testIso", lol)
    lol.close()