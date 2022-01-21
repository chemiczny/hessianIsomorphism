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
from canonical import addForms, multiplyForms, subtractForms
from itertools import combinations
from collections import defaultdict
from formManipulation import primeFactorization, generateSubKey2AtomDist, CouchySchwarzTest
from potentialForms import PotentialFormAdd, PotentialFormMult, mergePotentialFormAdd

def mergeNodeOptimizers(nodeOptimizer1, node1, nodeOptimizer2, node2):
    potentialForms = []
    
    for sol1 in nodeOptimizer1.potentialSolutions:
        for sol2 in nodeOptimizer2.potentialSolutions:
            commonReducedKeys = sol1.reducedKeys & sol2.reducedKeys
            
            if not commonReducedKeys:
                continue
            
            newPotentialForm = PotentialFormMult()
            newPotentialForm.usedNodes.add(node1)
            newPotentialForm.usedNodes.add(node2)
            
            newPotentialForm.node2polynomialDecomposition[node1] = sol1
            newPotentialForm.node2polynomialDecomposition[node2] = sol2
            
            newPotentialForm.allReducedKeys = sol1.reducedKeys | sol2.reducedKeys
            
            potentialForms.append(newPotentialForm)
        
    return potentialForms

def mergeNodeOptimizerWithPotentialFormMult(nodeOptimizer, node, potentialFormMult):
    if node in potentialFormMult.usedNodes:
        return
    
    potentialForms= []
    
    for sol in nodeOptimizer.potentialSolutions:
        commonReducedKeys = sol.reducedKeys & potentialFormMult.allReducedKeys
        
        if not commonReducedKeys:
            continue
        
        newPotentialForm = PotentialFormMult()
        
        newPotentialForm.usedNodes = potentialFormMult.usedNodes | set([node])
        newPotentialForm.allReducedKeys = sol.reducedKeys | potentialFormMult.allReducedKeys
        
        newPotentialForm.node2polynomialDecomposition[node] = sol
        for node in potentialFormMult.node2polynomialDecomposition:
            newPotentialForm.node2polynomialDecomposition[node] = potentialFormMult.node2polynomialDecomposition[node]
            
            
        potentialForms.append(newPotentialForm)
        
    return potentialForms

def mergePotentialFormMultWithDivisiblePolynomial( potentialFormMult, divisiblePolynomial, node ):
    commonReducedKeys = divisiblePolynomial.reducedKeys & potentialFormMult.allReducedKeys
        
    if not commonReducedKeys and len(potentialFormMult.allReducedKeys) > 0:
        raise Exception("No common monomials!")
    
    newPotentialForm = PotentialFormMult()
    
    newPotentialForm.usedNodes = potentialFormMult.usedNodes | set([node])
    newPotentialForm.allReducedKeys = divisiblePolynomial.reducedKeys | potentialFormMult.allReducedKeys
    
    newPotentialForm.node2polynomialDecomposition[node] = divisiblePolynomial
    for node in potentialFormMult.node2polynomialDecomposition:
        newPotentialForm.node2polynomialDecomposition[node] = potentialFormMult.node2polynomialDecomposition[node]
        
    return newPotentialForm

class GraphOptimizer(GraphParser, GraphAnalyser):
    def __init__(self, source = None, lastLine = None, variables2freeze = []):
        GraphParser.__init__(self, source, lastLine, variables2freeze)
        
        self.nodes2expand = []
        self.monomialKey2node = {}
        
        self.existingForms = {}
        self.potentialFormsAdd = {}
        self.node2potentialFormAdd = {}
        self.potentialFormsMult = {}
        self.monomialCost = {}
    
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
        
    def initPotentialFormsAdd(self):
        self.potentialFormsAdd = {}
        self.node2potentialFormAdd = {}
        
        node2primitivePotentialForm = {}
        queue = []
        allMonomials = set()
        monomialsNo = 0
        for node in self.nodes2expand:
            newPotentialForm = PotentialFormAdd()
            newPotentialForm.node2subforms[node] = self.graph.nodes[node]["form"].subforms
            newMonomials = set(self.graph.nodes[node]["form"].subforms.keys())
            newPotentialForm.monomials = newMonomials
            newPotentialForm.nodes.add(node)
            
            monomialsNo += len(newMonomials)
            node2primitivePotentialForm[node] = newPotentialForm
            allMonomials |= newMonomials
            self.node2potentialFormAdd[node] = []
            
        print("Found ", monomialsNo, " monomials")
        print("unique ones: ", len(allMonomials))
        self.monomialCost = self.calcCostOfMonomialsSet(allMonomials)
        
        for n in node2primitivePotentialForm:
            potentialForm = node2primitivePotentialForm[n]
            for m in potentialForm.monomials:
                potentialForm.monomialsCost[m] = self.monomialCost[m]
                
            queue.append(potentialForm)
            
        while queue:
            newQueue = []
            
            for potentialForm in queue:
                otherNodes = self.nodes2expand - potentialForm.nodes
                for otherNode in otherNodes:
                    newPotentialForm = mergePotentialFormAdd( potentialForm, node2primitivePotentialForm[otherNode] )
                    
                    if newPotentialForm != None:
                        newQueue.append(newPotentialForm)
                #a moze frozenset juz w tworzenia?
                potentialFormKey = frozenset(potentialForm.monomials)
                if potentialFormKey in self.potentialFormsAdd:
                    self.potentialFormsAdd[potentialFormKey] = mergePotentialFormAdd( potentialForm, self.potentialFormsAdd[potentialFormKey] )
                else:
                    self.potentialFormsAdd[potentialFormKey] = potentialForm
                        
            queue = newQueue
                    
    def calcCostOfMonomialsSet(self, monomials):
        monomial2cost = {}
        for m in monomials:
            factors = primeFactorization(m, self.subformFactory.primes)
            cost = 0
            for f in factors:
                cost += factors[f]
                
            monomial2cost[m] = cost - 1
            
        return monomial2cost
    
    def updatePotentialFormsAdd(self):
        pass
    
    def initPotentialFormsMult(self):
        self.potentialFormsMult = []
#        node2potentialForms = {}
#        monomialNodes2optimize = []
        nodeMultOptimizers = {}
        reducedKey2node2poly = {}
        #rozklad na czynniki kazdego z wielomianow + grupowanie
        for node in self.nodes2expand:
            form = self.graph.nodes[node]["form"]
            if len(form.subforms) > 1:
                nodeMultOptimizer = NodeOptimizer( form, self.scrLog, self.key2uniqueOperatorNodes )
                nodeMultOptimizer.findPotentialSolutions()
                nodeMultOptimizer.generateReducedKeys()
                if len(nodeMultOptimizer.potentialSolutions) > 0:
                    nodeMultOptimizers[node] = {}
                
                for polyId, poly in enumerate(nodeMultOptimizer.potentialSolutions):
                    nodeMultOptimizers[node][polyId] = poly
                    for key in poly.reducedKeys:
                        if not key in reducedKey2node2poly:
                            reducedKey2node2poly[key] = {}
                            
                        if not node in reducedKey2node2poly[key]:
                            reducedKey2node2poly[key][node] = set([])
                        
                        reducedKey2node2poly[key][node].add(polyId)
                        
#            else:
#                pass
                
        availableNodes = set( nodeMultOptimizers.keys() )
        actualCluster = None
#        stats = defaultdict(int)
#        print("saldsal")
#        for key in reducedKey2node2poly:
#            stats[ len(reducedKey2node2poly[key]  ) ] += 1
#            if len(reducedKey2node2poly[key]) > 10:
#                print(key)
            
#        print("lo kurwa")
#        print(stats)
        
        queue = []
#        print("Do ogarniecia:")
#        print(len(reducedKey2node2poly))
        while reducedKey2node2poly:
            
            if actualCluster == None:
#                print("zaczynam nowy klaster")
                selectedNode = list(nodeMultOptimizers.keys())[0]
                selectedPoly = list(nodeMultOptimizers[selectedNode].keys())[0]
                
                actualCluster = PotentialFormMult()
                seed = nodeMultOptimizers[selectedNode][selectedPoly]
                queue = [ ( selectedNode, seed) ]
                
                del nodeMultOptimizers[selectedNode][selectedPoly]
                if not nodeMultOptimizers[selectedNode]:
                    del nodeMultOptimizers[selectedNode]
                    
                for key in seed.reducedKeys:
#                    print(key, selectedNode, selectedPoly)
                    reducedKey2node2poly[key][selectedNode].remove(selectedPoly)
                    
                    if  not reducedKey2node2poly[key][selectedNode]:
                        del reducedKey2node2poly[key][selectedNode]
                        
                    if not reducedKey2node2poly[key]:
                        del reducedKey2node2poly[key]
                
            usedNodes = set([])
            
            while queue:
                node, newSeed = queue.pop()
                usedNodes.add(node)
                keys2investigate = actualCluster.allReducedKeys | newSeed.reducedKeys
                actualCluster = mergePotentialFormMultWithDivisiblePolynomial(actualCluster, newSeed, node)
                
                
                for key in keys2investigate:
                    if key in reducedKey2node2poly:
                        nodes2intesigate = list(reducedKey2node2poly[key].keys())
                    else:
                        continue
                        
                    for newNode in nodes2intesigate:
                        if newNode in usedNodes:
                            continue
                        
                        selectedPolyId = reducedKey2node2poly[key][newNode].pop()
                            
#                        print(newNode, selectedPolyId)
                        selectedPoly = nodeMultOptimizers[newNode][selectedPolyId]
                        del nodeMultOptimizers[newNode][selectedPolyId]
                        if not nodeMultOptimizers[newNode]:
                            del nodeMultOptimizers[newNode]
                            
                        for key2delete in selectedPoly.reducedKeys:
                            reducedKey2node2poly[key2delete][newNode].discard(selectedPolyId)
                            
                            if not reducedKey2node2poly[key2delete][newNode]:
                                del reducedKey2node2poly[key2delete][newNode]
                                
                            if not reducedKey2node2poly[key2delete]:
                                del reducedKey2node2poly[key2delete]
                            
                        queue.append( (newNode, selectedPoly) )
#                        usedNodes.add(newNode)
                
            self.potentialFormsMult.append(actualCluster)
            actualCluster = None
#                print("queue sieze: ", len(queue))
            
        print("After clustering: ", len(self.potentialFormsMult))
                
        
    def calculateReducedForms(self):
        pass
    
    def updatePotentialFormsMult(self):
        pass
        
    def greedySchemeGlobal(self):
        self.log("Greedy scheme atom sum: start")
        self.nodes2expand = self.prepareToExpandOutputNodes()
        #od razu ogarnac monomiany?
        
#        while True:
        for i in range(20):
            if len(self.nodes2expand) == 0:
                print("wierzcholki do ekspancji wyczerpane")
                break
            
            self.initPotentialFormsAdd()
            self.initPotentialFormsMult()
            
            maxAddProfit = 0
            bestAddForm = None
            addClusterKey = None
            rl2form = None
            rl2nodes = None
            
            for key in self.potentialFormsAdd:
                maxProfit, bestKey, reducedLocal2form, reducedLocal2nodes = self.potentialFormsAdd[key].getMaximumProfitForm(self.key2uniqueOperatorNodes, {}, self.graph)
    
                if maxProfit > maxAddProfit:
#                    print("zysk")
                    maxAddProfit = maxProfit
                    bestAddForm = key
                    addClusterKey = bestKey
                    rl2form = reducedLocal2form
                    rl2nodes = reducedLocal2nodes
                    
                    
            maxMultProfit = 0
            bestPotForm = None
            stats = defaultdict(int)
            for potForm in self.potentialFormsMult:
                newMultProfit = potForm.calcProfit()
#                newMultProfit = len(potForm.usedNodes)
                stats[ len(potForm.usedNodes) ] += 1
                if newMultProfit > maxMultProfit:
                    maxMultProfit = newMultProfit
                    bestPotForm = potForm
                    
            print("STATSY!")
            print(stats)
            if maxAddProfit == 0 and maxMultProfit == 0:
                print("brak profitu!")
                break
            
#            if False in self.nodes2expand:
#                print("dziwne rzeczy przed usem")
                
            print("add vs mult ", maxAddProfit, maxMultProfit)
            if maxAddProfit > maxMultProfit and False:
                self.usePotentialFormAdd(bestAddForm,addClusterKey, rl2form, rl2nodes )
            else:
                print("len formy mult")
                print(len(bestPotForm.usedNodes))
                self.usePotentialFormMult( bestPotForm )
            
#            if False in self.nodes2expand:
#                print("dziwne rzeczy po usie")
            
#        self.checkForCycles("przed greedy expandem")
        for node in self.nodes2expand:
            self.greedyExpandSum(node)
            
#        self.checkForCycles("lol")
        
        
    def usePotentialFormAdd(self, potentialFormKey, clusterKey, rl2form, rl2nodes):
        print("wykorzystuje znaleziony klaster sumy")
#        self.checkForCycles("usePotentialFormAdd: start")
        selectedPotentialForm = self.potentialFormsAdd[potentialFormKey]
        #znalezienie dobrego wierzcholka zrodloego
        print("Znaleziona forma do wyciagniecia: ")
        print( rl2form[clusterKey].subforms )
        print("wielkosc klastera: ")
        
        sourceNode = None
        need2generateSource = True
        scale = 1
        nodes2transform = rl2nodes[clusterKey]
        print(len(nodes2transform))
        
        if clusterKey in self.key2uniqueOperatorNodes:
            sourceNode = self.key2uniqueOperatorNodes[clusterKey]
            need2generateSource = False
            print("wierzcholek do uzycia")
            
            if sourceNode in nodes2transform:
                print("wierzcholek zrodlowy wsrod transformowanych!")
                nodes2transform.remove(sourceNode)
            
        elif clusterKey in rl2nodes:
            sources = rl2nodes[clusterKey]
            
            #zrodlo bez skalowania
            for s in sources:
                form = CanonicalForm()
                form.subforms = selectedPotentialForm.node2subforms[s]
                
                if form.generateKey() == clusterKey:
                    print("jest git")
                    sourceNode = s
                    sources.remove(s)
                    break
            else:    
                s = sources.pop()
                form = CanonicalForm()
                form.subforms = selectedPotentialForm.node2subforms[s]
                
                subKey = list(form.subforms.keys()).pop()
                
                scale = form.subforms[subKey] // rl2form[clusterKey].subforms[subKey] 
                if scale < 1:
                    raise Exception("Scaling node less than 1!")
                sourceNode = s
                print("Wierzcholek ze skalowaniem")
                print(form.subforms[subKey] , rl2form[clusterKey].subforms[subKey] )
                print(scale)
#                if form.generateKey() != potentialFormKey:
#                    raise Exception("Error while generating source node")
                
        print("generacje zrodla: ", need2generateSource)
        print("skalowanie", scale)
        if need2generateSource:
            if scale == 1:
                self.nodes2expand.remove( sourceNode )
                self.graph.nodes[sourceNode]["operator"] = "+"
                self.graph.nodes[sourceNode]["fix"] = "infix"
                newCanonicalForm = subtractForms( self.graph.nodes[sourceNode]["form"], rl2form[clusterKey] )
                newNode, alreadyExisting = self.insertNewOperatorBottomUp( "unk", sourceNode, newCanonicalForm )
                
                if not alreadyExisting:
                    self.nodes2expand.add(newNode)
                
                sourceNode, rfAlreadyExisting = self.insertNewOperatorBottomUp( "unk", sourceNode, rl2form[clusterKey] )
                if rfAlreadyExisting:
                    raise Exception("This node should not exists until now!")
                else:
                    self.nodes2expand.add(sourceNode)
            else:
                reducedForm = rl2form[clusterKey]
                fullForm = CanonicalForm()
                
                for key in reducedForm.subforms:
                    fullForm.subforms[key] = scale * reducedForm.subforms[key]
                
                self.nodes2expand.remove( sourceNode )
                self.graph.nodes[sourceNode]["operator"] = "+"
                self.graph.nodes[sourceNode]["fix"] = "infix"
                newCanonicalForm = subtractForms( self.graph.nodes[sourceNode]["form"], fullForm )
                newNode, alreadyExisting = self.insertNewOperatorBottomUp( "unk", sourceNode, newCanonicalForm )
                
                if not alreadyExisting:
                    self.nodes2expand.add(newNode)
                
                fullFormNode, fullAlreadyExisting = self.insertNewOperatorBottomUp( "*", sourceNode, fullForm )
                
                if fullAlreadyExisting:
                    raise Exception("Full form exists: correct behauvior not implemented")
                    
                scaleForm = self.createIntegerCanonical(scale)
                scaleNode = self.nodeFromCanonical(scaleForm)
                
                if scaleNode == None:
                    self.createIntegerForm(str(scale), scale)
                    scaleNode = str(scale)
                    
#                self.graph.add_edge( scaleNode, fullFormNode, fold = 1)
                self.addEdgeOrIncreaseFold(scaleNode, fullFormNode)
                
                sourceNode, rfAlreadyExisting = self.insertNewOperatorBottomUp( "unk", fullFormNode, rl2form[clusterKey] )
                
                if not rfAlreadyExisting:
                    self.nodes2expand.add(sourceNode)
            
#        self.checkForCycles("usePotentialFormAdd: po generacji zrodla "+str(need2generateSource))
        
        
        form2insert = rl2form[clusterKey]
        selectedKey = list(form2insert.subforms.keys())[0]
        for n in nodes2transform:
            self.nodes2expand.remove(n)
            
            scale = selectedPotentialForm.node2subforms[n][selectedKey] // form2insert.subforms[selectedKey]
            self.graph.nodes[n]["operator"] = "+"
            self.graph.nodes[n]["fix"] = "infix"
                
            if scale == 1:
                newForm = subtractForms(self.graph.nodes[n]["form"], form2insert)
                
                restNode, restExisting = self.insertNewOperatorBottomUp( "unk", n, newForm )
                if not restExisting:
                    self.nodes2expand.add(restNode)
                    
                self.addEdgeOrIncreaseFold(sourceNode, n)
                
                
            else:
                fullForm = CanonicalForm()
                
                for key in form2insert.subforms:
                    fullForm.subforms[key] = scale * form2insert.subforms[key]
                    
                restForm =subtractForms(self.graph.nodes[n]["form"], fullForm)
                
                restNode, restExisting = self.insertNewOperatorBottomUp( "unk", n, restForm )
                if not restExisting:
                    self.nodes2expand.add(restNode)  
                    
                scaledNode, scaledExists = self.insertNewOperatorBottomUp( "*", n, fullForm )
                
                if scaledExists:
                    continue
                
                scaleForm = self.createIntegerCanonical(scale)
                scaleNode = self.nodeFromCanonical(scaleForm)
                
                if scaleNode == None:
                    self.createIntegerForm(str(scale), scale)
                    scaleNode = str(scale)
                    
                self.addEdgeOrIncreaseFold(scaleNode, scaledNode)
                self.addEdgeOrIncreaseFold(sourceNode, scaledNode)
                
#        self.checkForCycles("usePotentialFormAdd: finish ")
        
    def greedyGlobalIteration(self):
        pass

                
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
                    
#                if coeff == 1:
#                    return
                
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
            #tu jest blad!
            newNode, presentInGraph = self.insertNewOperatorBottomUp("unkNoRest", node, devidedForm)
            if devidedForm.subforms == { 5 : 1 } and not presentInGraph:
                print("nie rozpoznaje form atomowych")

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
        
        nodeOptimizer = NodeOptimizer(form, self.scrLog, self.key2uniqueOperatorNodes)
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
                
    def usePotentialFormMult(self, potentialForm):
        for node in potentialForm.node2polynomialDecomposition:
            quotientForm, dividerForm, divisibleForm, restForm = potentialForm.node2polynomialDecomposition[node].getForms()
            self.expandMult( node, quotientForm, dividerForm, divisibleForm, restForm )
            
    def expandMult(self, node, quotientForm, dividerForm, divisibleForm, restForm ):
        
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
        
        self.nodes2expand.remove(node)
        if restForm.subforms:
            self.graph.nodes[node]["operator"] = "+"
            restNode, presentInGraph = self.insertNewOperatorBottomUp("unkRest", node, restForm)
#            self.checkForCycles("dodanie reszty")
            if not presentInGraph:
                self.nodes2expand.add(restNode)
                
            divisibleNode, presentInGraph = self.insertNewOperatorBottomUp("*", node, divisibleForm )
#            self.checkForCycles("dodanie podzielnego wielomianu")
            if not presentInGraph:
                quotientNode, quotientPresentInGraph = self.insertNewOperatorBottomUp("unkRest", divisibleNode, quotientForm )
#                self.checkForCycles("kurwa 1")
                
                if not quotientPresentInGraph:
                    self.nodes2expand.add( quotientNode )
                    
                dividerNode, dividerPresentInGraph = self.insertNewOperatorBottomUp("unkRest", divisibleNode, dividerForm )
#                self.checkForCycles("kurwa 2")
                if not dividerPresentInGraph:
                    self.nodes2expand.add( dividerNode )
                
        else:
            self.graph.nodes[node]["operator"] = "*"
            
            quotientNode, quotientPresentInGraph = self.insertNewOperatorBottomUp("unkNoRest", node, quotientForm)
#            self.checkForCycles("kurwa 3")
            if not quotientPresentInGraph:
                self.nodes2expand.add(quotientNode)
#                self.greedyExpandSum(quotientNode)
                
            dividerNode, dividerPresentInGraph = self.insertNewOperatorBottomUp("unkNoRest", node, dividerForm )
#            self.checkForCycles("kurwa 4", dividerForm)
            
            if not dividerPresentInGraph:
                self.nodes2expand.add(dividerNode)
#                self.greedyExpandSum(dividerNode)
    
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
            key = self.graph.nodes[node]["canonicalKey"]
            self.graph.remove_node(node)
            del self.key2uniqueOperatorNodes[key]
            
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
            
            
    
