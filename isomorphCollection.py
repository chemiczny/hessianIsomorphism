#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep 12 11:30:58 2019

@author: michal
"""

from isomorph import Isomorph
from keyGenerator import KeyGenerator

class IsomorphCollection:
    def __init__(self, graphParser, minSup):
        self.graphParser = graphParser
        self.minSup = minSup
        
        self.isomorphs = {}
        
        self.buildSeeds()
        
    def buildSeeds(self):
        self.isomorphs = {}
        
        for node in self.graphParser.graph.nodes:
            if self.graphParser.graph.nodes[node]["kind"] != "middle":
                continue
            
            if not self.graphParser.graph.nodes[node]["operator"] in [ "*" , "+" , "-" ] :
                continue
            
            newLabel = self.createCanonicalLabel( [node] )
            
            if newLabel in self.isomorphs:
                self.isomorphs[newLabel].update( [node] )
            else:
                self.isomorphs[newLabel] = Isomorph( [node] )
                
                
        print( list(self.isomorphs.keys()))
            
            
    def createCanonicalLabel(self, nodes):
        newKeyGenerator = KeyGenerator(self.graphParser.graph, nodes)
        return newKeyGenerator.generateKey()