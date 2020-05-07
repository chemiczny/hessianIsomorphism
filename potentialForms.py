#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 24 13:07:18 2020

@author: michal
"""
import math
from functools import reduce
from canonical import CanonicalForm

class PotentialFormAdd:
    def __init__(self):
        self.node2subforms = {}
        self.monomials = set([])
        self.nodes = set([])
        self.monomialsCost = {}
        
    def getMaximumProfitForm(self, canonical2node, reduced2nodes, graph):
        reducedLocal2nodes, reducedLocal2form = self.clusterSubforms()
        
        maxProfit = 0
        for clusterKey in reducedLocal2nodes:
            maxProfit = max(self.calculateClusterProfit(clusterKey, reducedLocal2nodes, reducedLocal2form, canonical2node, reduced2nodes, graph ), maxProfit)
            
        return maxProfit
    
    def clusterSubforms(self):
        #zmienic na generacje kluczy zredukowanych form
        reducedKey2nodes = {}
        subKeyList = list( self.monomials )
        reducedKey2form = {}
        
        for node in self.node2subforms:
            coeffs = []
            for subKey in subKeyList:
                coeffs.append(self.node2subforms[node][subKey])
                
            gcd = reduce(math.gcd, coeffs)
            if gcd != 1:
                form = CanonicalForm()
                subforms = self.node2subforms[node]
                for subKey in subforms:
                    form.subforms[subKey] = subforms[subKey] // gcd
                    
                reducedKey = form.generateKey
            else:
                form = CanonicalForm()
                form.subforms = self.node2subforms[node]
                reducedKey = form.generateKey()
                
            if reducedKey in reducedKey2nodes:
                reducedKey2nodes[reducedKey].append(node)
            else:
                reducedKey2nodes[reducedKey] = [ node ]
                reducedKey2form[reducedKey] = form
#                
        return reducedKey2nodes, reducedKey2form
    
    def calculateClusterProfit(self, primitiveKey, reducedLocal2nodes, reducedLocal2form, canonical2node, reduced2nodesEx, graph):
        allMonomialCost = sum(self.monomialsCost.values())
        primitiveCost = 0
        primitiveSource = set([])
        currentCluster = set( reducedLocal2nodes[primitiveKey] )
        
        if primitiveKey in canonical2node:
            primitiveCost = 0
            primitiveSource.add( canonical2node[primitiveKey] )
        elif primitiveKey in reduced2nodesEx:
            primitiveCost += 1
            primitiveSource |= reduced2nodesEx[primitiveKey]
        else:
            primitiveCost += allMonomialCost
            primitiveSource |= currentCluster
            
        
        commonNodes = currentCluster & primitiveSource
        
        actualProfit = -primitiveCost
        if commonNodes:
            baseNode = commonNodes.pop()
        else:
            baseNode = primitiveSource.pop()
            
        actualProfit += len(currentCluster) * allMonomialCost
        analysedForm = reducedLocal2form[primitiveKey]
        
        highestProfit = 0
        for reducedKey in reducedLocal2form:
            if reducedKey == primitiveKey:
                continue
            
            ratio2monomials = {}
            
            for key in analysedForm.subforms:
                ratio = "{}:{}".format( analysedForm.subforms[key], reducedLocal2form[reducedKey].subforms[key] )
                
                if ratio in ratio2monomials:
                    ratio2monomials[ratio].append(key)
                else:
                    ratio2monomials[ratio] = [key]
                    
            
            highestSubProfit = 0
            for ratio in ratio2monomials:
                newProfit = 0
                for monomial in ratio2monomials[ratio]:
                    newProfit += self.monomialsCost[monomial]
                    
                if newProfit > highestSubProfit:
                    highestSubProfit = newProfit
                    
            highestProfit += highestSubProfit
            
        actualProfit += highestProfit
        
        return actualProfit
        
    
def mergePotentialFormAdd(form1, form2):
    commonMonomials = form1.monomials & form2.monomials
    
    if not commonMonomials:
        return None
    
    if form1.nodes <= form2.nodes:
        return form1
    elif form1.nodes >= form2.nodes:
        return form2
    
    newPotentialForm = PotentialFormAdd()
    newPotentialForm.monomials = commonMonomials
    
    newPotentialForm.nodes = form1.nodes | form2.nodes
    
    for m in commonMonomials:
        newPotentialForm.monomialsCost[m] = form1.monomialsCost[m]
        
    for node in form1.node2subforms:
        newPotentialForm.node2subforms[node] = {}
        for subKey in commonMonomials:
            newPotentialForm.node2subforms[node][subKey] = form1.node2subforms[node][subKey]
            
    uniqueForm2nodes = newPotentialForm.nodes - form1.nodes
    
    for node in uniqueForm2nodes:
        newPotentialForm.node2subforms[node] = {}
        for subKey in commonMonomials:
            newPotentialForm.node2subforms[node][subKey] = form2.node2subforms[node][subKey]
    
    return newPotentialForm
    
class PotentialFormMult:
    def __init__(self):
        self.usedNodes = set([])
        self.node2polynomialDecomposition = {}
        self.allReducedKeys = set([])