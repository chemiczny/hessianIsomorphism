#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 20 10:50:32 2019

@author: michal
"""
from graphParser import GraphParser
from time import time
import networkx as nx
import matplotlib.pyplot as plt


class GraphOptimizer(GraphParser):
    def __init__(self , source = None, lastLine = None):
        GraphParser.__init__(self, source, lastLine)
    
    def findClusters(self):
        clusterFound = True
        
        searchingStart = time()
        maxClusterFound = 5000
        clusterIt = 0
        maxClusterSize = 0
        sortedNodes = list(reversed(list( nx.topological_sort(self.graph) )))
        lastNode = None
        
        while clusterFound:
            clusterFound = False
            
            for node in sortedNodes:
                if lastNode != None and node != lastNode:
                    continue
                else:
                    lastNode = None
                
                nodeType = self.graph.nodes[node]["kind"]
                if nodeType != "middle":
                    continue
                
                operator = self.graph.nodes[node]["operator"]
                
                if operator!= "+" and operator != "*":
                    continue
                
                newCluster = self.findMaximumCluster(node, operator, sortedNodes)
                
                if len(newCluster) > 1:
                    clusterFound = True
                    maxClusterSize = max(maxClusterSize, len(newCluster))
                    for node2remove in newCluster[1:]:
                        sortedNodes.remove(node2remove)
                    lastNode = newCluster[0]
                    
                    self.transformCluster(newCluster)
                    break
                
            if clusterFound:
#                print("znaleziony kluster: ",len(newCluster))
                clusterIt += 1
                if clusterIt % 500 == 0:
                    print(clusterIt)
                
            if clusterIt > maxClusterFound:
                break
                
        timeTaken = time() - searchingStart
        print("znaleziono: ", clusterIt, " klastrow")
        print("najwiekszy: ", maxClusterSize)
        print("czas: ", timeTaken)
                
    def transformCluster(self, clusterList):
        clusterList = clusterList[1:]
        clusterList.reverse()
        
        for node in clusterList:
            nodePredecessors = list(self.graph.predecessors( node))
            for pred in nodePredecessors:
                edgeFold = self.graph[pred][node]["fold"]
                
                nodeSuccesors = list(self.graph.successors(node))
                
                for succ in nodeSuccesors:
                    if succ in self.graph[pred]:
                        self.graph[pred][succ]["fold"] += edgeFold
                    else:
                        self.graph.add_edge(pred, succ, fold = edgeFold )
                    
            self.graph.remove_node(node)
        
                
    def findMaximumCluster(self, node, operator, sortedNodes):
        confirmedCluster = set([node])
        clusterList = [ node ]
        
        queue = set(self.graph.predecessors( node))
        
        while queue:
            element, queue = self.getNextElement(sortedNodes, queue)
            
            nodeType = self.graph.nodes[element]["kind"]
            
            if nodeType != "input":            
                elementOperator = self.graph.nodes[element]["operator"]
                if elementOperator != operator:
                    continue
            
            elementSuccesors = set( self.graph.successors( element) )
            notAcceptableSuccesors = elementSuccesors - confirmedCluster
#            print(len(notAcceptableSuccesors))
            if notAcceptableSuccesors:
#                print("odrzucam")
                continue
            
            previousLen = len(confirmedCluster)
            confirmedCluster.add(element)
            actualLen = len(confirmedCluster)
            
            if previousLen < actualLen:
                clusterList.append(element)
            
            queue |= set( self.graph.predecessors( element ) )
            
        return clusterList
    
    def getNextElement(self, sortedNodes, queue):
        for node in sortedNodes:
            if node in queue:
                queue.remove(node)
                return node, queue
            
    def histogramOfSuccessors(self):
        succesorsNoList = []
        
        for node in self.graph.nodes:
            succesorsNoList.append( len(list(self.graph.successors( node))))
            
        n, bins, patches = plt.hist(succesorsNoList, 50, density=True, facecolor='g', alpha=0.75)


        plt.xlabel('SuccesorsNo')
        plt.ylabel('Probability')
        plt.title('Histogram of succesors')
        plt.grid(True)
        plt.show()
        
    def histogramOfLevels(self):
        levelsList = []
        
        for node in self.graph.nodes:
            levelsList.append( self.graph.nodes[node]["level"])
            
        n, bins, patches = plt.hist(levelsList, 150, density=False, facecolor='g', alpha=0.75)


        plt.xlabel('Level')
        plt.ylabel('Probability')
        plt.title('Histogram of levels')
        plt.grid(True)
        plt.show()
            
    def simplifyBrackets(self):
        searchingStart = time()
        sortedNodes = list(reversed(list( nx.topological_sort(self.graph) )))
        possibilities = 0
        
        plusNodes = []
        perfectMatch = 0
        
        for node in sortedNodes:
            if not "operator" in self.graph.nodes[node]:
                continue
            
            operator = self.graph.nodes[node]["operator"]
            
            if operator == "+":
                plusNodes.append(node)
                
        for node in plusNodes:
            predecessors = list(self.graph.predecessors( node))
            possible2extract = None
            nodes2extract = 0
            
            for pred in predecessors:
                if not "operator" in self.graph.nodes[pred]:
                    continue
                
                predOperator = self.graph.nodes[pred]["operator"]
                
                if predOperator != "*":
                    continue
                
                succesNo = len(list(self.graph.successors( pred)))
                if succesNo != 1:
                    continue
                
                nodes2extract += 1
                if not possible2extract:
                    possible2extract = set( self.graph.predecessors( pred) )
                else:
                    possible2extract &= set( self.graph.predecessors( pred) )
            
            if possible2extract and nodes2extract > 1:
                possibilities += 1
                
            if nodes2extract == len(predecessors) and possible2extract and nodes2extract > 1:
                perfectMatch += 1
                
        timeTaken =time() - searchingStart
        print("time taken: ", timeTaken)
        print("possibilities: ", possibilities)
        print("perfection: ", perfectMatch)