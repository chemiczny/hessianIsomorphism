#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 20 10:50:32 2019

@author: michal
"""
from graphParser import GraphParser
from time import time
import networkx as nx
from copy import deepcopy
import matplotlib.pyplot as plt
#from math import ceil, sqrt
from collections import defaultdict
from canonical import CanonicalForm
from graphAnalyser import GraphAnalyser
from nodeOptimizer import NodeOptimizer

from formManipulation import primeFactorization, generateSubKey2AtomDist, CouchySchwarzTest

class GraphOptimizer(GraphParser, GraphAnalyser):
    def __init__(self, source = None, lastLine = None):
        GraphParser.__init__(self, source, lastLine)
    
    def findClusterSubgraphs(self, acceptableOperators = [ "+", "-", "*", None ], acceptableKinds = [ "middle" , "integer" ], minimumSize = 2, minimumCost = 0 ):
        sortedNodes = list(reversed(list( nx.topological_sort(self.graph) )))
        
        verifiedNodes = set([])
        clusters = []
        clusterSizes = []
        nodesInClusters = 0
        maxSize = 0
        
        for node in sortedNodes:
            
            nodeKind = self.graph.nodes[node]["kind"]
            nodeOperator = None
            
            if not nodeKind in [ "input", "integer" ]:
                nodeOperator = self.graph.nodes[node]["operator"]
                
            if not nodeOperator in acceptableOperators:
                continue
            
            if not nodeKind in acceptableKinds:
                continue
            
            if node in verifiedNodes:
                continue
            
            newCluster = [ node ]
            newClusterSet = set(newCluster)
            
            queue = list(self.graph.predecessors(node))
            clusterCost = len(queue) -1
            
            while queue:
                clusterCandidate = queue.pop(0)
                
                candidateKind = self.graph.nodes[clusterCandidate]["kind"]
                candidateOperator = None
                
                if not candidateKind in [ "input", "integer"]:
                    candidateOperator = self.graph.nodes[clusterCandidate]["operator"]
                
                if not candidateKind in acceptableKinds:
                    continue
                
                if not candidateOperator in acceptableOperators:
                    continue
                
                candidateSuccessors = set( self.graph.successors(clusterCandidate) )
                candidatePredecessors = list(self.graph.predecessors(clusterCandidate))
                
                if len(candidateSuccessors - newClusterSet) > 0:
                    continue
                
                if not clusterCandidate in newClusterSet:
                    newCluster.append(clusterCandidate)
                    newClusterSet.add(clusterCandidate)
                    clusterCost += len(candidatePredecessors) - 1
                
                for p in candidatePredecessors:
                    queue.append(p)
                
            if len(newCluster) >= minimumSize and clusterCost >= minimumCost:
                clusters.append(newCluster)
                clusterSizes.append(len(newCluster))
                verifiedNodes |= newClusterSet
                nodesInClusters += len(newCluster)
                maxSize = max(maxSize, len(newCluster))
                
        print("Found ", len(clusters), " clusters")
        print("Nodes in cluster: ", nodesInClusters)
        print("Max size: ", maxSize)
        return clusters
#        plt.figure()
#        n, bins, patches = plt.hist(clusterSizes, 150, density=False, facecolor='g', alpha=0.75)
#
#
#        plt.xlabel('Cluster size')
#        plt.ylabel('Number of occurences')
#        plt.title('Acceptable operators: '+str(acceptableOperators))
#        plt.grid(True)
#        plt.show()
        
    def findAlternativePath(self):
        print("Searching for alterntives paths...")
        clusters = self.findClusterSubgraphs(acceptableOperators = [ "+", "-", "*" ], acceptableKinds = [ "middle"  ], minimumSize = 1, minimumCost = 4 )
#        allClusterNodes = set([])

        
#        for c in clusters:
#            allClusterNodes |= set(c[1:])
            
        basesFound = 0
        fullVectorsFound = 0
        
        for c in clusters:
            root = c[0]
        
            rootSubformSet = set(self.graph.nodes[root]["form"].subforms.keys())
            forbiddenNodes = set(c) | self.getAllSuccessors(root)
            
            fullVectors, potentialBase = self.findSubsetForms(rootSubformSet, forbiddenNodes )
            
            if potentialBase or fullVectors:
                basesFound += 1
                
            if fullVectors:
                fullVectorsFound += 1
                
        print("Found potential bases for ", basesFound , " of ", len(clusters))
        print("Found full vectors bases for ", fullVectorsFound , " of ", len(clusters)) 
        
    def findAlternativePathProt(self):
        self.log("Searching for alterntives paths...")
            
        basesFound = 0
        fullVectorsFound = 0
        chances = 0
        linearDependency = 0
        integerNodes = self.getAllIntegerNodes()
        self.log("All nodes: "+str( len(self.graph.nodes()) ) )
        
        nodes2dependentVectors = {}
        primeKey2possibleNodes = {}
        
        for i, n in enumerate(self.graph.nodes):
            if i % 200 == 0:
                self.log(str(i))
                
            
            if not "operator" in self.graph.nodes[n]:
                continue
        
            operator = self.graph.nodes[n]["operator"]
            
            if not operator in [ "+", "-", "*" ]:
                continue
        
            chances += 1
            rootSubform = self.graph.nodes[n]["form"].subforms
            forbiddenNodes = set( self.graph.predecessors(n) ) | self.getAllSuccessors(n)
            forbiddenNodes.add(n)
            
            primePredecessors, primeKey = self.getPrimePredecessors(n)
            
            if primeKey in primeKey2possibleNodes:
                possibleNodes = primeKey2possibleNodes[primeKey]
            else:
                primePredecessors |= integerNodes
                possibleNodes = self.getAllPureSuccessors(primePredecessors)
                primeKey2possibleNodes[primeKey ] = possibleNodes
            
            fullVectors, potentialBase, linearDependent = self.findSubsetForms(rootSubform, forbiddenNodes, possibleNodes )
            
            if potentialBase or fullVectors:
                basesFound += 1
                
            if fullVectors:
                fullVectorsFound += 1
                
            if linearDependent:
                nodes2dependentVectors[n] = linearDependent
                linearDependency += 1
                # break
            
                
        self.log("Found potential bases for "+ str(basesFound) + " of " + str(chances))
        self.log("Found full vectors bases for " + str(fullVectorsFound) + " of " + str(chances)) 
        self.log("Linear dependency for " + str(linearDependency) + " of " + str(chances))
        nodes2dependentVectors = self.useLinearDependency( nodes2dependentVectors, onlyIntegers = True )
        self.useLinearDependency( nodes2dependentVectors, onlyIntegers = False )

    def useLinearDependency( self, node2linearDependent, onlyIntegers = False ):
        node2delete = []
        for node in node2linearDependent:
            replacements = node2linearDependent[node]

            replacement, coefficient, isInteger = self.findBestReplacement(node, replacements)

            if not replacement:
                continue

            if isInteger:
                multNodeName = str(coefficient)
                if not multNodeName in self.graph.nodes:
                    self.graph.add_node(multNodeName, variable = multNodeName, kind = "integer", level = 0)
                    self.createIntegerForm(multNodeName, coefficient)

            else:
                if onlyIntegers:
                    continue

                multNodeName = coefficient
                if not multNodeName in self.graph.nodes:
                    self.graph.add_node(multNodeName, variable = multNodeName, kind = "input", level = 0)
                    self.createPrimeForm(multNodeName)

            newNode = self.insertNewOperator( "*", [ replacement, multNodeName ] , "infix",forceNewNode = True )
            self.replaceNode( node, newNode )
            node2delete.append(node)

        for n in node2delete:
            del node2linearDependent[n]

        return node2linearDependent

    def getAllIntegerNodes(self):
        integerNodes = set([])
        
        for node in self.graph.nodes:
            if self.graph.nodes[node]["kind"] == "integer":
                integerNodes.add(node)
                
        return integerNodes

    def findBestReplacement(self, node, replacements):
        isInteger = False

        subKey = list(self.graph.nodes[node]["form"].subforms.keys())[0]
        subCoeff = self.graph.nodes[node]["form"].subforms[subKey]
        bestRepl = None
        coeff = None

        for rep in replacements:
            if not rep in self.graph.nodes:
                continue

            candidateCoeff = self.graph.nodes[rep]["form"].subforms[subKey]

            if subCoeff % candidateCoeff == 0:
                isInteger = True
                bestRepl = rep
                coeff = subCoeff // candidateCoeff
                break

            bestRepl = rep
            coeff = str(subCoeff)+"./"+str(candidateCoeff) + "."

        return bestRepl, coeff, isInteger
            
    def getAllSuccessors(self, node):
        queue = set(self.graph.successors(node))
        allSuccessors = deepcopy(queue)
        
        while queue:
            newNode = queue.pop()
            
            newSuccessors = set(self.graph.successors(newNode))
            allSuccessors |= newSuccessors
            queue |= newSuccessors
            
        return allSuccessors
    
    def getAllSuccessorsIt(self, nodes):
        queue = set(nodes)
        for node in nodes:
            queue |= set(self.graph.successors(node))
        allSuccessors = deepcopy(queue)
        
        while queue:
            newNode = queue.pop()
            
            newSuccessors = set(self.graph.successors(newNode))
            allSuccessors |= newSuccessors
            queue |= newSuccessors
            
        return allSuccessors
    
    def getAllPureSuccessors(self, nodes):
        queue = set(nodes)
        
        allSuccessors = set([])
        
        while queue:
            newNode = queue.pop()
            allSuccessors.add(newNode)
            
            newSuccessors = set(self.graph.successors(newNode))
            for s in newSuccessors:
                sPred = set(self.graph.predecessors(s))
                
                if allSuccessors >= sPred:
                    queue.add(s)
            
        return allSuccessors
    
    def getPrimePredecessors(self, node):
        form = self.graph.nodes[node]["form"]
        allPrimes = set({})
        for subKey in form.subforms:
            allPrimes |= set(primeFactorization(subKey, self.subformFactory.primes ).keys())
            
        primeNodes = set([])
        primeKey = 1
        for p in allPrimes:
            primeNodes.add( self.subformFactory.subformId2node[p] )
            primeKey *= p
            
        return primeNodes, primeKey
        
    def findSubsetForms(self, subform2search, notAcceptableNodes, possibleNodes = None ):
        perfectMatch = []
        similarNodes = []
        perfectMatch = False
        allCoords = set([])
        subform2searchNorm = self.subformInnerProduct(subform2search, subform2search)
        subformSet2search = set( subform2search.keys() )
        linerDependentVectors = []

        if possibleNodes == None:
            possibleNodes = set(self.graph.nodes)

        acceptableNodes = possibleNodes - notAcceptableNodes
        for node in acceptableNodes:
            
            subform = self.graph.nodes[node]["form"].subforms
            subformSet = set(subform.keys())
            
            if subformSet2search >= subformSet :
                allCoords |= subformSet
                similarNodes.append(node)
            else:
                continue

            if CouchySchwarzTest( subform2search, subform,  subform2searchNorm):
                perfectMatch = True
                linerDependentVectors.append(node)
                # break
        
            if len(subformSet2search) == len(allCoords):
                perfectMatch = True
                # break
        
        return perfectMatch, similarNodes, linerDependentVectors
    
    def prepareToExpandOutputNodes(self):
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
                
        self.log("to remove: " + str( len(nodes2remove)) )
        self.log("to expand: " + str( len(nodes2optimize)) )
        self.log("to stay: "+ str(toStay))
        
        for node in nodes2remove:
            canonicalKey = self.graph.nodes[node]["canonicalKey"]
            del self.key2uniqueOperatorNodes[canonicalKey]
            
        self.graph.remove_nodes_from(nodes2remove)
        
        for n in nodes2optimize:
            predecessors = list(self.graph.predecessors(n))
            
            for p in predecessors:
                self.graph.remove_edge(p, n)
                
        return nodes2optimize
    
    def greedyScheme(self):
        self.log("Greedy scheme: start")
        nodes2optimize = self.prepareToExpandOutputNodes()
        
        expandNo = len(nodes2optimize)
        progressStep = int(0.05 * expandNo)
        nextLog = 0
        for i,n in enumerate(nodes2optimize):
            if self.debug:
                print(40*"#")
                print("GREEDY EXPAND FOR NODE: ", n, self.graph.nodes[n]["variable"])
                
            if i >= nextLog:
                self.log(str(i) + " of " + str(expandNo))
                nextLog += progressStep

            self.greedyExpand(n)

        self.log("Greedy scheme: stop")
        
    def greedySchemeSum(self):
        self.log("Greedy scheme atom sum: start")
        nodes2optimize = self.prepareToExpandOutputNodes()
        
        expandNo = len(nodes2optimize)
        progressStep = int(0.05 * expandNo)
        nextLog = 0
        for i,n in enumerate(nodes2optimize):
            if self.debug:
                print(40*"#")
                print("GREEDY EXPAND FOR NODE: ", n, self.graph.nodes[n]["variable"])
                
            if i >= nextLog:
                self.log(str(i) + " of " + str(expandNo))
                nextLog += progressStep

            self.greedyExpandSum(n)

        self.log("Greedy scheme atom sum: stop")
        

                
    def getMostCommonAtom(self, node, form, subformKey2atomDistribution,  atomDistribution = None):
        atomsOccurence = defaultdict(int)
        
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
            return None
            
        return sorted(atomsOccurence.items(), key=lambda item: item[1])[-1][0]
        
    def devideFormByAtom(self, node, form, mostCommonAtom, subformKey2atomDistribution):
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
        
        
        
        quotientForm = CanonicalForm()
        quotientForm.subforms = quotientSubforms
        
        return devidedForm, devidedAtomDistribution, quotientForm, quotientAtomDistribution, restSubforms, restAtomDistribution
    
    def greedyExpand(self, node, atomDistribution = None):    
        if self.debug:
            print("######################")
                  
        form = self.graph.nodes[node]["form"]
        subformKey2atomDistribution = generateSubKey2AtomDist(form, self.subformFactory.primes, atomDistribution)
        mostCommonAtom = self.getMostCommonAtom(node, form, subformKey2atomDistribution, atomDistribution)
        
        if mostCommonAtom == None:
            return
        
#        if self.debug:
#            print("ilosc cubow: ",len(form.subforms))
#            print("postac cubow: ",form.subforms)
#            print("wystepowanie atomow",atomsOccurence)
#            print("wybrany dzielnik", mostCommonAtom)
        
        dividerAtomNode = self.subformFactory.subformId2node[mostCommonAtom]
        devidedForm, devidedAtomDistribution, quotientForm, quotientAtomDistribution, restSubforms, restAtomDistribution = self.devideFormByAtom( node, form, mostCommonAtom, subformKey2atomDistribution)

        
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

            quotientNode, presentInGraph = self.insertNewOperatorBottomUp("*", node, quotientForm )
            if not presentInGraph:
                self.greedyExpand( quotientNode, quotientAtomDistribution )
            
    
    def checkForCycles(self, message, form2print = None):
        cyclesList = list(nx.simple_cycles(self.graph))
        
        if cyclesList:
            print("Cykl pojawił sie po")
            print(message)
            if form2print:
                print("po dodaniu wierzcholka dla formy:")
                print(form2print.subforms)
            plt.figure()
            graph = nx.subgraph(self.graph, cyclesList[0])
            layout = nx.spring_layout(graph)
            nx.draw_networkx(graph, layout)
            raise Exception("cykl kurwa")
        
    
    def greedyExpandSum(self, node):
        form = self.graph.nodes[node]["form"]
        
        if len(form.subforms) == 1:
            self.greedyExpand(node)
#            self.checkForCycles("stary greedy expand")
            return
        
        nodeOptimizer = NodeOptimizer(form, self.scrLog)
#        quotientForm, dividerForm, divisibleForm, restForm  = nodeOptimizer.optimize()
        optimizationResult = nodeOptimizer.optimize()
        self.graph.nodes[node]["symmetric"] = True
        self.graph.nodes[node]["fix"] = "infix"
        
        if not optimizationResult.dividingWasPossible:
            self.graph.nodes[node]["operator"] = "+"
            for relPrime in optimizationResult.relativelyPrimes:
                newNode, presentInGraph = self.insertNewOperatorBottomUp("unkRest", node, relPrime)
                if not presentInGraph:
                    self.greedyExpand(newNode)
                
            return
        
        quotientForm = optimizationResult.quotientForm
        dividerForm = optimizationResult.deviderForm
        divisibleForm = optimizationResult.divisibleForm
        restForm = optimizationResult.remainderForm
        
#        for form in [ quotientForm, dividerForm, divisibleForm, restForm  ]:
#            algebraicOne = True
#            for subKey in form.subforms:
#                if subKey != 1:
#                    algebraicOne = False
#                    break
#                
#                if form.subforms[subKey] != 1:
#                    algebraicOne = False
#                    break
#                
#            if algebraicOne:
#                raise Exception("Algebraic one detected!")
        
        if restForm.subforms:
            self.graph.nodes[node]["operator"] = "+"
            restNode, presentInGraph = self.insertNewOperatorBottomUp("unkRest", node, restForm)
#            self.checkForCycles("dodanie reszty")
            if not presentInGraph:
                self.greedyExpandSum(restNode)
                
            divisibleNode, presentInGraph = self.insertNewOperatorBottomUp("*", node, divisibleForm )
#            self.checkForCycles("dodanie podzielnego wielomianu")
            if not presentInGraph:
                quotientNode, quotientPresentInGraph = self.insertNewOperatorBottomUp("unkRest", divisibleNode, quotientForm )
#                self.checkForCycles("kurwa 1")
                
                if not quotientPresentInGraph:
                    self.greedyExpandSum(quotientNode)
                    
                dividerNode, dividerPresentInGraph = self.insertNewOperatorBottomUp("unkRest", divisibleNode, dividerForm )
#                self.checkForCycles("kurwa 2")
                if not dividerPresentInGraph:
                    self.greedyExpandSum(dividerNode)
                
        else:
            self.graph.nodes[node]["operator"] = "*"
            
            quotientNode, quotientPresentInGraph = self.insertNewOperatorBottomUp("unkNoRest", node, quotientForm)
#            self.checkForCycles("kurwa 3")
            if not quotientPresentInGraph:
                self.greedyExpandSum(quotientNode)
                
            dividerNode, dividerPresentInGraph = self.insertNewOperatorBottomUp("unkNoRest", node, dividerForm )
#            self.checkForCycles("kurwa 4", dividerForm)
            
            if not dividerPresentInGraph:
                self.greedyExpandSum(dividerNode)
    
    def findClusters(self):
        self.log("Searching for cluster start...")
        
        totalNodes = 0
        searchingStart = time()
        maxClusterSize = 0
        
        multClusters = self.findClusterSubgraphs(acceptableOperators = [ "*" ], acceptableKinds = [ "middle" ] )
        plusClusters = self.findClusterSubgraphs(acceptableOperators = [ "+" ], acceptableKinds = [ "middle" ] )
        
        allClusters = multClusters + plusClusters
        
        for cluster in allClusters:
            clusterSize = len(cluster)
            totalNodes += clusterSize

            maxClusterSize = max(clusterSize, maxClusterSize)
                
            self.transformCluster(cluster)
                
        timeTaken = time() - searchingStart
        print("znaleziono: ", len(allClusters), " klastrow")
        print("nodes: ",totalNodes)
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
        
    def replaceNode(self, node2remove, nodeReplacement):

        for succ in self.graph.successors(node2remove):
            edgeFold = self.graph[node2remove][succ]["fold"]

            if succ in self.graph[nodeReplacement]:
                self.graph[nodeReplacement][succ]["fold"] += edgeFold

            else:
                self.graph.add_edge(nodeReplacement, succ, fold = edgeFold)
                
            if "order" in self.graph[node2remove][succ]:
                self.graph[nodeReplacement][succ]["order"] = self.graph[node2remove][succ]["order"]


        self.graph.remove_node(node2remove)
            
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
#                if "form" in self.graph.nodes[node2change]:
#                    del self.graph.nodes[node2change]["form"] 
                    
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
        

        
    def findDeadEnds(self):
        self.log("Searching for dead ends...")
        deletedAtoms = 0
        seeds = []
        for node in self.graph.nodes:
            successorsNo = len(list(self.graph.successors(node)))
            
            if successorsNo == 0 and self.graph.nodes[node]["kind"] != "output":
                seeds.append(node)
                
                
        while seeds:
            node = seeds.pop()
            
            predecessors = list(self.graph.predecessors(node))
            self.graph.remove_node(node)
            deletedAtoms += 1
            
            for p in predecessors:
                successorsNo = len(list(self.graph.successors(p)))
                if successorsNo == 0 and self.graph.nodes[p]["kind"] != "output":
                    seeds.append(p)
                    
        self.log("Deleted: "+ str(deletedAtoms))
        
            
    def getSubNodes(self, node):
        subNodes = set([])
        
        queue = [ node ]
        
        while queue:
            element = queue.pop()
            subNodes.add( element )
            queue += list(self.graph.predecessors(element) )
            
        return subNodes
            
            
    
