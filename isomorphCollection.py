#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep 12 11:30:58 2019

@author: michal
"""

from keyGenerator import KeyGenerator
from copy import deepcopy

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
            
            newKeyGenerator = KeyGenerator(self.graphParser.graph, [ node ])
            newLabel =  newKeyGenerator.generateKey()
            
            if newLabel in self.isomorphs:
                self.isomorphs[newLabel].append( newKeyGenerator )
            else:
                self.isomorphs[newLabel] = [ newKeyGenerator ]
                
                
        
#        print(len(list(self.isomorphs.keys())))
#        for key in self.isomorphs:
#            print(key)
            
            
    def createCanonicalLabel(self, nodes):
        newKeyGenerator = KeyGenerator(self.graphParser.graph, nodes)
        return newKeyGenerator.generateKey()
    
    def getOccurence(self):
        occurence = {}
        
        for key in self.isomorphs:
            occurence[key] = len(self.isomorphs[key])
            
#            allNodes = 0
#            uniqueNodes = set([])
#            
#            for isomorph in self.isomorphs[key]:
#                allNodes += len(isomorph.selectedNodes)
#                uniqueNodes |= set(isomorph.selectedNodes)
#                
#            print(key, len(uniqueNodes), "/", allNodes)
            
        return occurence
    
    def isomorphsGrowth(self):
        oldIsomorphs = deepcopy(self.isomorphs)
        self.isomorphs = {}
#        usedNodesSet = set()
        key2nodes = {}
        
        for key in oldIsomorphs:
            for isomorph in oldIsomorphs[key]:
                isomorphSuccessors = isomorph.getSuccessors()
                
                keysGeneratedFomIsomorph = set([])
                
                for node in isomorphSuccessors:
                    
                    if self.graphParser.graph.nodes[node]["kind"] != "middle":
                        continue
                    
                    if not self.graphParser.graph.nodes[node]["operator"] in [ "*" , "+" , "-" ] :
                        continue
                    
                    
#                    nodes = frozenset( isomorph.selectedNodes+ [node] )
#                    if nodes in usedNodesSet:
#                        continue
                    
#                    usedNodesSet.add(nodes)
                    
                    newIsomorph = KeyGenerator( self.graphParser.graph, isomorph.selectedNodes+ [node] )
                    newLabel = newIsomorph.generateKey()
                    
                    if key in key2nodes:
                        if set(newIsomorph.selectedNodes) & key2nodes[key]:
                            continue
                        
                        key2nodes[key] |= set(newIsomorph.selectedNodes) 
                    else:
                        key2nodes[key] = set(newIsomorph.selectedNodes) 
                    
                    if newLabel in keysGeneratedFomIsomorph:
                        continue
                    
                    keysGeneratedFomIsomorph.add(key)
                    
                    if newLabel in self.isomorphs:
                        self.isomorphs[newLabel].append( newIsomorph )
                    else:
                        self.isomorphs[newLabel] = [ newIsomorph ]
                
    def update(self, key2stay):
        actualKeys = set(self.isomorphs.keys())
        toDelete = actualKeys - key2stay
        
        for key in toDelete:
            del self.isomorphs[key]
            
            
            
            