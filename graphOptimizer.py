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
from copy import deepcopy


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
        
    def histogramOfLevels(self, operator):
        levelsList = []
#        outputLevelsFile = open("outputLevels.log", 'w')
        
        for node in self.graph.nodes:
            if "operator" in self.graph.nodes[node]:
                if self.graph.nodes[node]["operator"] == operator:
                    levelsList.append( self.graph.nodes[node]["level"])
            
#            if self.graph.nodes[node]["kind"] == "output":
#                outputLevelsFile.write(  self.graph.nodes[node]["variable"] + " ; " +str( self.graph.nodes[node]["level"] )+"\n" )
            
            
#        outputLevelsFile.close()
        plt.figure()
        n, bins, patches = plt.hist(levelsList, 150, density=False, facecolor='g', alpha=0.75)


        plt.xlabel('Level')
        plt.ylabel('Probability')
        plt.title('Histogram of levels for operator '+operator)
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
            
            pred2occur = {}
            pred2succ = {}
            
            for pred in predecessors:
                if not "operator" in self.graph.nodes[pred]:
                    continue
                
                predOperator = self.graph.nodes[pred]["operator"]
                
                if predOperator != "*":
                    continue
                
                succesNo = len(list(self.graph.successors( pred)))
                if succesNo != 1:
                    continue
                
                predPred = set( self.graph.predecessors( pred) )
                
                for nodePred in predPred:
                    if not nodePred in pred2occur:
                        pred2occur[nodePred] = 1
                        pred2succ[nodePred] = [ pred ]
                    else:
                        pred2occur[nodePred] += 1
                        pred2succ[nodePred].append(pred)
                        
            
            bestNode2extract = None
            maximumEdges2delete = 0
            
            for pred in pred2occur:
                if pred2occur[pred] > maximumEdges2delete:
                    maximumEdges2delete = pred2occur[pred]
                    bestNode2extract = pred
                    
            if maximumEdges2delete > 1:
                possibilities += 1
            else:
                continue
                
            nodes2extract = [ bestNode2extract ]
            
            for pred in pred2succ:
                if pred == bestNode2extract:
                    continue
                
                if len(pred2succ[pred]) != len(pred2succ[bestNode2extract]):
                    continue
                
                if len( set(pred2succ[pred]) & set(pred2succ[bestNode2extract]) ) != len(pred2succ[bestNode2extract]):
                    continue
                
                nodes2extract.append(pred)
                
            nodes2change = pred2succ[bestNode2extract]
            
            if maximumEdges2delete == len(predecessors):
                perfectMatch+= 1
                
            newInputs = []
            for node2change in nodes2change:
                for node2extract in nodes2extract:
                    fold =  self.graph[node2extract][node2change]["fold"]
                    if fold > 1:
                        self.graph[node2extract][node2change]["fold"] -= 1
                    else:
                        self.graph.remove_edge(node2extract, node2change)
                        
                nodeFold = self.graph[node2change][node]["fold"]
                self.graph.remove_edge(node2change, node)
                newInputs += nodeFold * [ node2change ]
                
            newOperatorNode1 = self.insertNewOperator( "+" , newInputs, "infix", True )
            newOperatorNode2 = self.insertNewOperator( "*", [ newOperatorNode1 ] + nodes2extract , "infix" , True)
            self.graph.add_edge(newOperatorNode2, node, fold = 1 )
            nodes2checkForIdentity =  nodes2change + [ node ]
            self.checkForIdentity(nodes2checkForIdentity)
            
                
        timeTaken =time() - searchingStart
        print("time taken: ", timeTaken)
        print("possibilities: ", possibilities)
        print("perfection: ", perfectMatch)
        
        cycles = list(nx.simple_cycles(self.graph))
        print("szukam cykli")
        print(cycles)
        print("i jak?")
        
    def checkForIdentity(self, nodesList):
        for node in nodesList:
            operator = self.graph.nodes[node]["operator"]
            
            if operator == "-":
                continue
            
            prececessors = list(self.graph.predecessors(node))
            succesors = list(self.graph.successors(node))
            
            if len(prececessors) > 1 or len(succesors) > 1:
                continue
            
            predecessor = prececessors[0]
            succesor = succesors[0]
            
            if self.graph[predecessor][node]["fold"]  != 1:
                continue
            
            if self.graph[node][succesor]["fold"]  != 1:
                continue
            
            if "order" in self.graph[node][succesor]:
                self.graph.add_edge( predecessor, succesor, fold = 1 , order = self.graph[node][succesor]["order"])
            else:
                self.graph.add_edge( predecessor, succesor, fold = 1 )
            self.graph.remove_node(node)
    
    def multiplyNodes(self):
        sortedNodes = list( nx.topological_sort(self.graph) )
        
        multNodes = []
        
        fuckedBySuccessors = 0
        fuckedByOperator = 0
        totalWTF = 0
        
        for node in sortedNodes:
            if not "operator" in self.graph.nodes[node]:
                continue
            
            operator = self.graph.nodes[node]["operator"]
            
            if operator == "*":
                multNodes.append(node)
                
        for node in multNodes:
            predecessors = list(self.graph.predecessors( node))
            
            multiStack = []
            
            for pred in predecessors:
                if not "operator" in self.graph.nodes[pred]:
                    continue
                
                predOperator = self.graph.nodes[pred]["operator"]
                #TODO uwzglednic tez odejmowanie
                
                if predOperator == "*":
                    totalWTF += 1
                
                if predOperator != "+":
                    fuckedByOperator +=1
                    continue
                
                succesNo = len(list(self.graph.successors( pred)))
                if succesNo != 1:
                    fuckedBySuccessors += 1
                    continue
                
                
                predPred = list( self.graph.predecessors( pred) )
                mainFold = self.graph[pred][node]["fold"]
                
                newStackElement = []
                
                for nodePred in predPred:
                    newStackElement.append( { "node" : nodePred , "fold" : self.graph[nodePred][pred]["fold"] } )
                    
                for i in range(mainFold):
                    multiStack.append(newStackElement)
                    
                
            if  len(multiStack) < 2:
                continue
            print("no kurwa")
            for pred in predecessors:
                self.graph.remove_node(pred)
            
            queue = [ [] ]
            print("Stos wierzcholkow: ", multiStack)
            for layer in multiStack:
                newQueue = []
                for component in layer:
                    for element in queue:
                        newQueue.append(  element + [component] )
                        
                queue = newQueue
                
            print("Kolejka: ", queue)
            mainInputList = []
            for nodeSet in queue:
                inputList = []
                for singleNode in nodeSet:
                    inputList += [ singleNode["node"] ] * singleNode["fold"]
                    
                mainInputList.append( self.insertNewOperator( "*" ,  inputList, "infix" ) )
                
            newNode = self.insertNewOperator( "+", mainInputList, "infix" )
            self.graph.add_edge(newNode, node, fold = 1)
#            self.checkForIdentity([node])
            
            print("zrobiene!")
            break
#                        
#            
        print("Zjebne orzez operatory: ", fuckedByOperator)
        print("Zjebane przez nastepcw: ", fuckedBySuccessors)
        print("Total wtf: ", totalWTF)
        
    def findDeadEnds(self):
        seeds = []
        for node in self.graph.nodes:
            successorsNo = len(list(self.graph.successors(node)))
            
            if successorsNo == 0 and self.graph.nodes[node]["kind"] != "output":
                seeds.append(node)
                
                
        while seeds:
            node = seeds.pop()
            
            predecessors = list(self.graph.predecessors(node))
            self.graph.remove_node(node)
            
            for p in predecessors:
                successorsNo = len(list(self.graph.successors(p)))
                if successorsNo == 0 and self.graph.nodes[p]["kind"] != "output":
                    seeds.append(p)

    def analyseSubGraphOverlaping(self):
        totalNodesNo = len( list( self.graph.nodes ) )
        
        report = open("subgraphReport.dat", 'w')
        output2nodeSet = {}
        
        for outputName in self.outputs2nodes:
            outputNode = self.outputs2nodes[outputName]
            
            output2nodeSet[outputName] = self.getSubNodes(outputNode) 
            subNodesNo = len( output2nodeSet[outputName] )
            percentage = float(subNodesNo)*100/totalNodesNo
            
            report.write( outputName +";"+  str(subNodesNo) + ";" + str(totalNodesNo) + ";" + str( percentage )+"\n"  )
            
            
        report.close()
        
        report = open("subgraphOverlapping.dat", 'w')
        
        outputNames = list(output2nodeSet.keys())
        
        for index, key1 in enumerate(outputNames):
            for key2 in outputNames[index+1:]:
                overlapping = output2nodeSet[key1] & output2nodeSet[key2]
                
                percentage1 = float(len(overlapping))*100/len(output2nodeSet[key1] )
                percentage2 = float(len(overlapping))*100/len(output2nodeSet[key2] )
                
                report.write( key1 +" ; "+ str(len(output2nodeSet[key1] )) + " ; "+
                             str(percentage1) + " ; " + key2 +" ; "+ str(len(output2nodeSet[key2] )) + 
                             " ; "+  str(percentage2) + " ; "+ str(max(percentage1, percentage2)) + "\n")
                
        
        report.close()
        
        report = open("subgraphOperators.dat", 'w')
        report.write("out name ; + ; * ; - ; / \n")
        
        for key in output2nodeSet:
            nodeSet = output2nodeSet[key]
            
            plusNo = 0
            multNo = 0
            subNo = 0
            devNo = 0
            
            for node in nodeSet:
                if not "operator" in self.graph.nodes[node]:
                    continue
                
                operator = self.graph.nodes[node]["operator"]
                
                if operator == "+":
                    plusNo += 1
                elif operator == "*":
                    multNo += 1
                elif operator == "-":
                    subNo += 1
                elif operator == "/":
                    devNo += 1
                    
            report.write( key + " ; " + str(plusNo) + " ; " + str(multNo) + " ; " + str(subNo) + " ; " + str(devNo) + "\n" )
        
        
        report.close()
        
    def analysePools(self):
        graphTemp = deepcopy(self.graph)
        
        nodes2remove = []
        for node in graphTemp.nodes:
            if not "operator" in graphTemp.nodes[node]:
                continue
            
            if graphTemp.nodes[node]["operator"] == "/":
                nodes2remove.append(node)
                
        graphTemp.remove_nodes_from(nodes2remove)
        
        print("Niezalezne komponenty po usunieciu dzielenia:")
        i = 0
        for component in nx.weakly_connected_components(graphTemp):
            print(len(component))
            i += 1
        
        print("Liczba wszystkich niezależnych komponentow: ", i)
        
            
    def getSubNodes(self, node):
        subNodes = set([])
        
        queue = [ node ]
        
        while queue:
            element = queue.pop()
            subNodes.add( element )
            queue += list(self.graph.predecessors(element) )
            
        return subNodes
            
            
    