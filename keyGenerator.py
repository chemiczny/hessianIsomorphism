#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 30 11:19:31 2019

@author: michal
"""

import networkx as nx
from copy import deepcopy
from graphParser import GraphParser
from canonical import CanonicalSubform, CanonicalForm

class AtomRepresentation:
    __slots__ = [ "name", "node", "maximumPower", "positiveOccurrence", "negativeOccurence" ]
    def __init__(self, atom, coeff = 1):
        self.name = atom.name
        self.node = atom.node
        self.maximumPower = atom.power
        self.positiveOccurrence = 0
        self.negativeOccurence = 0
        if coeff > 0:
            self.positiveOccurrence += coeff
        else:
            self.negativeOccurence += coeff
        
    def addAtom(self, atom, coeff = 1):
        if coeff > 0:
            self.positiveOccurrence += coeff
        else:
            self.negativeOccurence += coeff
            
        if atom.power > self.maximumPower:
            self.maximumPower = atom.power

class KeyGenerator:
    def __init__(self, graph, selectedNodes):
        self.graph = graph
        self.selectedNodes = selectedNodes
        self.subgraph = self.graph.subgraph(self.selectedNodes).copy()
        self.outputNodes = []
        self.inputNodes = []
        
    def writeFunction(self, functionName , file ):
        graphParser = GraphParser()
        graphParser.graph = self.subgraph
        print(self.subgraph.nodes)
        print(self.inputNodes)
        print(self.selectedNodes)
        arguments = [ "double " + self.subgraph.nodes[inp]["variable"] for inp in self.inputNodes  ]
        graphParser.arguments = graphParser.getArgsFromLine( " , ".join(arguments) )
#        graphParser.rebuildGraph()
        graphParser.writeFunctionFromGraph(functionName, file)
        
    def insertNode(self, node):
        originalSucc = list( self.graph.successors(node) )
        originalPred = list( self.graph.predecessors(node))
        
        newSucc = list( self.subgraph.successors(node))
        newPred = list( self.subgraph.predecessors(node))
        
        
        if len(originalPred) > len(newPred):
            newInputs = set(originalPred) - set(newPred)
            
            for newInp in newInputs:
                
                if not newInp in self.inputNodes:
                    self.inputNodes.append(newInp)
                    name = "i"+str(self.inpInd)
                    self.inpInd+=1
                    
                    newAtom = CanonicalAtom(name, 1, newInp)
                    
                    newSubform = CanonicalSubform()
                    newSubform.atoms[newAtom.name] = newAtom
                    
                    newForm = CanonicalForm()
                    newForm.subforms[ newSubform.getKey() ] = newSubform
                    
                    self.subgraph.add_node(newInp, form = newForm, kind = "input", variable = name)
                    
                newEdgeFold = self.graph[newInp][node]["fold"]
                
                if self.graph.nodes[node]["symmetric"]:
                    self.subgraph.add_edge(newInp, node, fold = newEdgeFold)
                else:
                    newEdgeOrder = self.graph[newInp][node]["order"]
                    self.subgraph.add_edge(newInp, node, fold = newEdgeFold, order = newEdgeOrder)
                    
                
        self.generateCanonicalFormForNode(node)
            
        
        if len(originalSucc) > len(newSucc):
            self.outputNodes.append(node)
            self.subgraph.nodes[node]["kind"] = "output"
            self.subgraph.nodes[node]["variable"] = "return"
            
    def updateOutputs(self):
        oldOutputs, self.outputNodes = self.outputNodes, []
        
        for node in oldOutputs:
            originalSucc = list( self.graph.successors(node) )
            
            newSucc = list( self.subgraph.successors(node))
            
            if len(originalSucc) > len(newSucc):
                self.outputNodes.append(node)
                
    def generateKeyIteration(self):
        atomRepresentations = {}
        for node in self.outputNodes:
            form =  self.subgraph.nodes[node]["form"] 
            for subformKey in form.subforms:
                subForm = form.subforms[subformKey]
                actualCoeff = subForm.coefficient
                for atomKey in subForm.atoms:
                    atom = subForm.atoms[atomKey]
                    atomName = atom.name
                    
                    if atomName in atomRepresentations:
                        atomRepresentations[atomName].addAtom(atom, actualCoeff)
                    else:
                        atomRepresentations[atomName] = AtomRepresentation(atom, actualCoeff)
                        
        atomReprList = list(atomRepresentations.values())
        atomReprList.sort( key = lambda x : ( -x.maximumPower , -x.positiveOccurrence, -x.negativeOccurence )  )
        
        atom2newName = {}
        atomInd = 0
        self.inputNodes = []
        for atom in atomReprList:
            atom2newName[atom.name] = "j" + str(atomInd)
            atomInd += 1
            self.inputNodes.append( atom.node )
        
        canonicalLabels = []
        for node in self.outputNodes:
            form =  self.subgraph.nodes[node]["form"] 
            for subformKey in form.subforms:
                subForm = form.subforms[subformKey]
                
                for atomKey in subForm.atoms:
                    atom = subForm.atoms[atomKey]
                    
                    oldname = atom.name
                    atom.name = atom2newName[oldname]
                    
            form.updateKeys()
            canonicalLabels.append( form.generateKey() )
        
        canonicalLabel = ",".join(sorted( canonicalLabels ))
        return canonicalLabel
        
    def generateKey(self ):
        sortedNodes = list(nx.topological_sort(self.subgraph))
        
        self.outputNodes = []
        
        self.inpInd = 0
        
        for node in sortedNodes:
            self.insertNode(node)
                
                
        return self.generateKeyIteration()
    
    def addNode(self, node):
        self.selectedNodes.append(node)
        self.subgraph = self.graph.subgraph(self.selectedNodes).copy()
        
    def copyOutputForms(self, isomorph):
#        self.inputNodes = deepcopy(isomorph.inputNodes)
        self.inpInd = isomorph.inpInd
        self.outputNodes = deepcopy(isomorph.outputNodes)
        
        
        for node in isomorph.outputNodes:
            
            if not node in isomorph.subgraph.nodes:
                print("nie ma w bazowym izomorfie")
                
            if not node in self.subgraph.nodes:
                print("nie ma w docelowym izomorfie")
            
            self.subgraph.nodes[node]["form"] = deepcopy( isomorph.subgraph.nodes[node]["form"] )
        
    def getSuccessors(self):
        graphSuccesors = set([])
        subgraphSuccesors = set([])
        
        for node in self.outputNodes:
            graphSuccesors |= set(self.graph.successors(node))
            subgraphSuccesors |= set(self.subgraph.successors(node))
            
        return graphSuccesors - subgraphSuccesors
    
    def generateCanonicalFormForNode(self, node):
        nodeOperator = self.subgraph.nodes[node]["operator"]
        predecessors = list(self.subgraph.predecessors(node))
        
        if nodeOperator == "+" :
            firstPredecessor = predecessors.pop(0)
            
            newForm = deepcopy( self.subgraph.nodes[firstPredecessor]["form"] )
            for pred in predecessors:
                fold = self.subgraph[pred][node]["fold"]
                
                for i in range(fold):
                    newForm.add( self.subgraph.nodes[pred]["form"] )
            
            self.subgraph.nodes[node]["form"] = newForm
            
        elif nodeOperator == "*":
            firstPredecessor = predecessors.pop(0)
            
            newForm = deepcopy( self.subgraph.nodes[firstPredecessor]["form"] )
            for pred in predecessors:
                fold = self.subgraph[pred][node]["fold"]
                
                for i in range(fold):
                    newForm.multiply( self.subgraph.nodes[pred]["form"] )
                    
            self.subgraph.nodes[node]["form"] = newForm            
        
        elif nodeOperator == "-":
            order2pred = {}
            
            if not self.subgraph.nodes[node]["symmetric"]:
                for pred in predecessors:
                    order2pred[ self.subgraph[pred][node]["order"] ] =  pred
                    
            else:
                if len(predecessors) > 1:
                    raise Exception("Symmetric - operator with more than one argument "+str(node))
                order2pred[0] = predecessors[0]
                
            sortedOrders = sorted(list(order2pred.keys()))
            
            if not self.subgraph.nodes[node]["symmetric"]:
                newForm = deepcopy( self.subgraph.nodes[ order2pred[ sortedOrders[0] ] ]["form"] )
                newForm.subtract( self.subgraph.nodes[ order2pred[ sortedOrders[1] ] ]["form"] )
            else:
                newForm = CanonicalForm()
                newForm.subtract( self.subgraph.nodes[ order2pred[ sortedOrders[0] ] ]["form"] )
                
            self.subgraph.nodes[node]["form"] = newForm
            
        else:
            raise Exception("Operator not supported! "+nodeOperator)














