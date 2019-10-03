#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 30 11:19:31 2019

@author: michal
"""

import networkx as nx
from copy import deepcopy

class AtomRepresentation:
    def __init__(self, atom, coeff = 1):
        self.name = atom.name
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

class CanonicalAtom:
    def __init__(self, name, power, node):
        self.name = name
        self.power = 1
        self.node = node
        
    def getKey(self):
        key = self.name
        if self.power != 1:
            key += "^"+str(self.power)
            
        return key

class CanonicalSubform:
    def __init__(self):
        self.atoms = {}
        self.coefficient = 1
        self.key = ""
        
    def getKey(self):
        if self.key:
            return self.key
        
        self.generateKey()
        return self.key
    
    def updateKeys(self):
        self.atoms, oldAtoms = {} , self.atoms
        
        for atomKey in oldAtoms:
            atom = oldAtoms[atomKey]
            self.atoms[atom.name] = atom
        
    def generateKey(self):
        keyList = []
        for atomName in self.atoms:
            keyList.append( self.atoms[atomName].getKey() )
            
        keyList.sort()
        self.key = "*".join(keyList)
        return self.key
    
    
    def multiply(self, subform):
        self.coefficient *= subform.coefficient
        
        for atomKey in subform.atoms:
            if atomKey in self.atoms:
                self.atoms[atomKey].power += subform.atoms[atomKey].power
            else:
                self.atoms[atomKey] = deepcopy(subform.atoms[atomKey])
                
        self.key = ""
    
#    def divide(self):
#        pass
#    
#    def inverse(self):
#        pass

class CanonicalForm:
    def __init__(self):
        self.subforms = {}
#        self.subformsDown = []
    
    def generateKey(self):
        keyList = []
        
        for subKey in self.subforms:
            subform = self.subforms[subKey]
            newKey = subform.getKey()
            
            if subform.coefficient != 1:
                newKey += "*"+str(subform.coefficient)
            
            keyList.append( newKey )
            
            
        return "+".join(sorted( keyList ))
    
    def updateKeys(self):
        self.subforms, oldSubforms = {}, self.subforms
        
        for key in oldSubforms:
            subform = oldSubforms[key]
            subform.updateKeys()
            key = subform.generateKey()
            self.subforms[key] = subform
    
    def multiply(self, canonicalForm):
        temp, self.subforms = self.subforms , {}
        
        for s1key in temp:
            for s2key in canonicalForm.subforms:
                newForm = deepcopy( temp[s1key] )
                newForm.multiply( canonicalForm.subforms[s2key] )
                
                newKey = newForm.getKey()
                
                if newKey in self.subforms:
                    self.subforms[newKey].coefficient += newForm.coefficient
                else:
                    self.subforms[newKey] = newForm
    
    def add(self, canonicalForm):
        for subFormKey in canonicalForm.subforms:
            if subFormKey in self.subforms:
                self.subforms[subFormKey].coefficient += canonicalForm.subforms[subFormKey].coefficient
            else:
                self.subforms[subFormKey] = deepcopy(canonicalForm.subforms[subFormKey])
    
    def subtract(self, canonicalForm):
        for subFormKey in canonicalForm.subforms:
            if subFormKey in self.subforms:
                self.subforms[subFormKey].coefficient -= canonicalForm.subforms[subFormKey].coefficient
            else:
                self.subforms[subFormKey] = deepcopy(canonicalForm.subforms[subFormKey])
                self.subforms[subFormKey].coefficient *= -1

class KeyGenerator:
    def __init__(self, graph, selectedNodes):
        self.graph = graph
        self.selectedNodes = selectedNodes
        self.subgraph = self.graph.subgraph(self.selectedNodes).copy()
        
    def insertNode(self, node):
        originalSucc = list( self.graph.successors(node) )
        originalPred = list( self.graph.predecessors(node))
        
        newSucc = list( self.subgraph.successors(node))
        newPred = list( self.subgraph.predecessors(node))
        
        
        if len(originalPred) > len(newPred):
            newInputs = set(originalPred) - set(newPred)
            
            for newInp in newInputs:
                if not newInp in self.input2form:
                    name = "i"+str(self.inpInd)
                    self.inpInd+=1
                    
                    newAtom = CanonicalAtom(name, 1, newInp)
                    
                    newSubform = CanonicalSubform()
                    newSubform.atoms[newAtom.name] = newAtom
                    
                    newForm = CanonicalForm()
                    newForm.subforms[ newSubform.getKey() ] = newSubform
                    
                    self.subgraph.add_node(newInp, form = newForm)
                    
                newEdgeFold = self.graph[newInp][node]["fold"]
                
                if self.graph.nodes[node]["symmetric"]:
                    self.subgraph.add_edge(newInp, node, fold = newEdgeFold)
                else:
                    newEdgeOrder = self.graph[newInp][node]["order"]
                    self.subgraph.add_edge(newInp, node, fold = newEdgeFold, order = newEdgeOrder)
                    
                
        self.generateCanonicalFormForNode(node)
            
        
        if len(originalSucc) > len(newSucc):
            self.outputNodes.append(node)
            
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
        for atom in atomReprList:
            atom2newName[atom.name] = "j" + str(atomInd)
            atomInd += 1
        
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
        
        self.input2form = {}
        self.outputNodes = []
        
        self.inpInd = 0
        
        for node in sortedNodes:
            self.insertNode(node)
                
                
        return self.generateKeyIteration()
    
    def addNode(self, node):
        self.selectedNodes.append(node)
        self.subgraph = self.graph.subgraph(self.selectedNodes).copy()
        
    def copyOutputForms(self, isomorph):
        self.input2form = deepcopy(isomorph.input2form)
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














