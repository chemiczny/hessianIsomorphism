#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 23 16:41:48 2020

@author: michal
"""
import matplotlib.pyplot as plt
import networkx as nx
from copy import deepcopy

class GraphAnalyser:
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
        
    def dumplOutputCanonicalForm(self, file2write):
        f2w = open(file2write, 'w')
        
        for key in self.key2uniqueOperatorNodes:
            node = self.key2uniqueOperatorNodes[key]
            kind = self.graph.nodes[node]["kind"]
            if kind == "output" and self.graph.nodes[node]["operator"] != "/":
#                f2w.write(self.graph.nodes[node]["variable"])
                f2w.write("\n")
                f2w.write(key)
                f2w.write("\n")
            elif kind != "input":
                for succ in self.graph.successors(node):
                    if self.graph.nodes[succ]["operator"] == "/":
                        f2w.write(key)
                        f2w.write("\n")
                        break
        
        f2w.close()
        
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
        
    def histogrameOfdevideInputs(self):
        levelsList = []
        uniqueDeviders= set([])
        devidesNo = 0
        for node in self.graph.nodes:
            if "operator" in self.graph.nodes[node]:
                if self.graph.nodes[node]["operator"] == "/":
                    devidesNo += 1
                    pred = list(self.graph.predecessors(node))
                    order1 = self.graph[pred[0]][node]["order"]
                    order2 = self.graph[pred[1]][node]["order"]
                    
                    divider = None
                    if order1 > order2:
                        divider = pred[0]
                    else:
                        divider = pred[1]
                    
                    uniqueDeviders.add(divider)
                    levelsList.append(  self.graph.nodes[divider]["level"]   )
            
        print("Devides no: ", devidesNo)
        print("Number of unique deviders: ", len(uniqueDeviders))
        plt.figure()
        n, bins, patches = plt.hist(levelsList, 150, density=False, facecolor='g', alpha=0.75)


        plt.xlabel('Level')
        plt.ylabel('Probability')
        plt.title('Histogram of levels for operator ')
        plt.grid(True)
        plt.show()
        
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