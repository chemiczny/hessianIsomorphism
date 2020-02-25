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
#from math import ceil, sqrt
from collections import defaultdict
from canonical import CanonicalForm

class GraphOptimizer(GraphParser):
    def __init__(self , source = None, lastLine = None):
        GraphParser.__init__(self, source, lastLine)
    
    def primeFactorization(self, number):
        factors = defaultdict(int)
        
        temp = number
        primeIndex = 0
        while temp != 1:
            prime = self.subformFactory.primes[primeIndex]
            
            while temp % prime == 0:
                factors[prime] += 1
                temp = temp//prime
                
            primeIndex += 1
        
        return factors
    
    def greedyScheme(self):
        self.actualCycles = 0
        nodes2optimize = set([])
        nodes2remove = set([])
        operatorsOptim = set( [ "+", "-", "*" ] )
        toStay = 0
        
        for node in self.graph.nodes:
            
            if self.graph.nodes[node]["kind"] in  [ "input", "integer" ]:
                toStay+=1
                continue
            
            if not self.graph.nodes[node]["operator"] in operatorsOptim:
                toStay+=1
                continue
            
            if self.graph.nodes[node]["kind"] == "output" :
                nodes2optimize.add(node)
                continue
            
            if node in self.subformFactory.node2subformId:
                toStay += 1
                continue
                
            successors = list(self.graph.successors(node))
            
            if all( [  self.graph.nodes[s]["operator"] in operatorsOptim for s in successors    ] ):
                nodes2remove.add(node)
            else:
                nodes2optimize.add(node)
                
                
                
        print("to remove: ", len(nodes2remove))
        print("to expand: ", len(nodes2optimize))
        print("to stay: ", toStay)
        
        for node in nodes2remove:
            canonicalKey = self.graph.nodes[node]["canonicalKey"]
            del self.key2uniqueOperatorNodes[canonicalKey]
            
        self.graph.remove_nodes_from(nodes2remove)
        
        for n in nodes2optimize:
            predecessors = list(self.graph.predecessors(n))
            
            for p in predecessors:
                self.graph.remove_edge(p, n)
        
        for n in nodes2optimize:
            if self.debug:
                print(40*"#")
                print("GREEDY EXPAND FOR NODE: ", n, self.graph.nodes[n]["variable"])
                
            self.greedyExpand(n)
        
    def greedyExpand(self, node, atomDistribution = None):    
        if self.debug:
            print("######################")
                  
        form = self.graph.nodes[node]["form"]
        subformKey2atomDistribution = {}
        atomsOccurence = defaultdict(int)
        
        if atomDistribution:
            subformKey2atomDistribution = atomDistribution
        else:
            for subKey in form.subforms:
                subformKey2atomDistribution[subKey] = self.primeFactorization(subKey)
        
        for subKey in form.subforms:
            for atom in subformKey2atomDistribution[subKey]:
                atomsOccurence[atom] += 1
                
        if len(atomsOccurence) == 0 and len(form.subforms) == 1:
            subformKey = list( form.subforms.keys() )[0]
            coeff = form.subforms[subformKey]
            self.createIntegerForm(node, coeff)
            self.graph.nodes[node]["kind"] = "integer"
            self.graph.nodes[node]["variable"] = str(coeff)
            return
                
        if len(atomsOccurence) == 1 and len(form.subforms) == 1:
            
            subformKey = list( form.subforms.keys() )[0]
            primeKey =  list( atomsOccurence.keys() )[0] 
            
            atomPower = subformKey2atomDistribution[subformKey][primeKey]
            primeNode = self.subformFactory.subformId2node[ primeKey ]
            if atomPower == 1:
                coeff = form.subforms[subformKey]
                if self.debug:
                    print("znaleziono forma skladajaca sie z dokladnie jednego atomu")
                    print(primeKey)
                    print("z wspolczynnikiem: ", coeff)
                
                if primeKey == 1:
                    raise Exception("Node with subform key equal to one!")
#                    self.createIntegerForm(node, coeff)
#                    self.graph.nodes[node]["kind"] = "integer"
                    
                
                nodeName = str(coeff)
                if not nodeName in self.graph.nodes:
                    self.graph.add_node(nodeName, variable = nodeName, kind = "integer", level = 0)
                    self.createIntegerForm(nodeName, coeff)
                    
                self.graph.nodes[node]["operator"] = "*"
                self.graph.nodes[node]["fix"] = "infix"
                self.graph.nodes[node]["symmetric"] = True

                self.addEdgeOrIncreaseFold(nodeName, node)
                
                if not primeNode in self.graph.nodes:
                    print("nie znaleziono formy pierwszej w grafie! ", primeKey)
                    raise Exception("nie znaleziono formy pierwszej w grafie! ")
                    
                
                
                self.addEdgeOrIncreaseFold(primeNode, node)
                return

        if not atomsOccurence:
            return
            
        mostCommonAtom =  sorted(atomsOccurence.items(), key=lambda item: item[1])[-1][0]
        if self.debug:
            print("ilosc cubow: ",len(form.subforms))
            print("postac cubow: ",form.subforms)
            print("wystepowanie atomow",atomsOccurence)
            print("wybrany dzielnik", mostCommonAtom)
        
        
        devidedSubforms = {}
        devidedAtomDistribution = {}
        restSubforms = {}
        restAtomDistribution = {}
        quotientSubforms = {}
        quotientAtomDistribution = {}
        
        for subKey in subformKey2atomDistribution:
            atomDistribution = subformKey2atomDistribution[subKey]
            if mostCommonAtom in atomDistribution:
                quotientAtomDistribution[ subKey ] = deepcopy(atomDistribution)
                atomDistribution[mostCommonAtom] -= 1
                newKey = subKey//mostCommonAtom
                if atomDistribution[mostCommonAtom] == 0:
                    del atomDistribution[mostCommonAtom]
                    
                if newKey in devidedAtomDistribution:
                    devidedSubforms[newKey] += form.subforms[subKey]
                else:
                    devidedAtomDistribution[newKey] = atomDistribution
                    devidedSubforms[newKey] = form.subforms[subKey]
                    
                if subKey in quotientSubforms:
                    raise Exception("Subform already exists in quotient!")
                    
                quotientSubforms[subKey] = form.subforms[subKey]
            else:
                if subKey in restAtomDistribution:
                    raise Exception("Subform already exists in rest!")
                
                restAtomDistribution[subKey] = atomDistribution
                restSubforms[subKey] = form.subforms[subKey]
                
        self.graph.nodes[node]["symmetric"] = True
        self.graph.nodes[node]["fix"] = "infix"
        
        devidedForm = CanonicalForm()
        devidedForm.subforms = devidedSubforms
        dividerAtomNode = self.subformFactory.subformId2node[mostCommonAtom]
        
        if not "kind" in self.graph.nodes[dividerAtomNode]:
            raise Exception( "Devider atom not found in graph!!!" )
        
        if not restSubforms:            
            if self.debug:
                print("nie ma reszty z dzielenia")
                print( "Wprowadzam nowa krawedz od:" )
                print( dividerAtomNode )
                print( self.graph.nodes[dividerAtomNode]["form"].subforms )            
                print("Wprowadzam nowy wierzcholek dla formy")
                print(devidedForm.subforms)
            self.graph.nodes[node]["operator"] = "*"
            self.addEdgeOrIncreaseFold(dividerAtomNode, node)
            newNode, presentInGraph = self.insertNewOperatorBottomUp("unkNoRest", node, devidedForm)

            if not presentInGraph:
                if self.debug:
                    print("Greedy expand dla nowego wierzcholka")
                self.greedyExpand(newNode, devidedAtomDistribution)
        else:
            if self.debug:
                print("jest reszta z dzielenia")
            self.graph.nodes[node]["operator"] = "+"
            restForm = CanonicalForm()
            restForm.subforms = restSubforms
            restNode, presentInGraph = self.insertNewOperatorBottomUp("unkRest", node, restForm)
            if not presentInGraph:
                self.greedyExpand(restNode, restAtomDistribution)
            
            quotientForm = CanonicalForm()
            quotientForm.subforms = quotientSubforms

            quotientNode, presentInGraph = self.insertNewOperatorBottomUp("*", node, quotientForm )
            if not presentInGraph:
                self.greedyExpand( quotientNode, quotientAtomDistribution )
            
    
    def findClusters(self):
        self.log("Searching for cluster start...")
        clusterFound = True
        
        searchingStart = time()
#        maxClusterFound = 5000
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
                
#            if clusterIt > maxClusterFound:
#                break
                
        timeTaken = time() - searchingStart
        print("znaleziono: ", clusterIt, " klastrow")
        print("najwiekszy: ", maxClusterSize)
        print("czas: ", timeTaken)
        self.log("Searching for cluster finished.")
                
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
            
            if not nodeType in [ "input" , "integer" ]:            
                elementOperator = self.graph.nodes[element]["operator"]
                if elementOperator != operator:
                    continue
            else:
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
        self.log("Simplifying brackets start...")
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
                
            nodes2deleteForm = []
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
                nodes2deleteForm.append(node2change)
                if "form" in self.graph.nodes[node2change]:
                    del self.graph.nodes[node2change]["form"] 
                    
                newInputs += nodeFold * [ node2change ]
                
            newOperatorNode1 = self.insertNewOperator( "+" , newInputs, "infix", True )
            newOperatorNode2 = self.insertNewOperator( "*", [ newOperatorNode1 ] + nodes2extract , "infix" , True)
            self.graph.add_edge(newOperatorNode2, node, fold = 1 )
            nodes2deleteForm.append(node)
            nodes2deleteForm.append(newOperatorNode1)
            nodes2deleteForm.append(newOperatorNode2)
            
            nodes2checkForIdentity =  nodes2change + [ node ]
            self.checkForIdentity(nodes2checkForIdentity)
            
            for n2df in nodes2deleteForm:
                if n2df in self.graph.nodes:
                    if "form" in self.graph.nodes[n2df]:
                        del self.graph.nodes[n2df]["form"]
                
            
                
        timeTaken =time() - searchingStart
        print("time taken: ", timeTaken)
        print("possibilities: ", possibilities)
        print("perfection: ", perfectMatch)
        self.log("Simplifying brackets finished")
        
#        cycles = list(nx.simple_cycles(self.graph))
#        print("szukam cykli")
#        print(cycles)
#        print("i jak?")
        
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
            
            
    