#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 24 23:05:46 2020

@author: michal
"""
#import numpy as np
import math
from functools import reduce
from canonical import CanonicalForm, multiplyForms, addForms, subtractForms
#import networkx as nx
from formManipulation import reduceForm

class DivisiblePolynomial:
    def __init__(self, gcdMat, form, key2existingNodes, estimateProfit = True):
        self.gcdMatrix = gcdMat
        self.gcdMonomials = frozenset(self.gcdMatrix.keys())
        self.intermediateMonomials = frozenset([ ])
        self.resultsMonomials = set([])
        self.form = form
        self.key2node = key2existingNodes
        
        for gcdKey in self.gcdMatrix:
            self.intermediateMonomials |= set( self.gcdMatrix[gcdKey].keys() )
            self.resultsMonomials |= set(self.gcdMatrix[gcdKey].values())
        
        if estimateProfit:
            self.profit = self.calcProfit()
        else:
            self.profit = None
            
        self.reducedKeys = set([])
        
    """
    Zakladamy, ze wejsciowy wielomian sklada sie z wielomianow, z ktorych kazdy ma jakies dzielniki
    Koszt wejsciowego wielomianu to n-1 dodawan i n mnozen, gdzie n to liczba monomianow
    
    Analogicznie oblicza sie koszt reszty z dzielenia. W przypadku dzielnika i dzielnej 
    liczymy tylko koszt dodawania. Problematycznie jest gdy dana forma juz gdzies wystepuje - 
    wowczas obliczenia dokladnego zysku wymagaloby czasochlonnej faktoryzacji
    """
    def calcProfit(self, additionalCostFreeForms = []): 
        quotientForm, dividerForm, divisibleForm, restForm = findPolynomialCoeff(self.form, self, 1)
        restCost = 2*len(restForm.subforms)-1
        resultMonomialsCost = 2*len(divisibleForm.subforms)-1
        gcdCost = len(quotientForm.subforms)-1
        interCost = len( dividerForm.subforms )-1
        
        restFormKey = restForm.generateKey()
        if restFormKey in self.key2node or restFormKey in additionalCostFreeForms:
            restCost = 0
            
        quotientFormKey = quotientForm.generateKey()
        if quotientFormKey in self.key2node or quotientFormKey in additionalCostFreeForms:
            gcdCost = 0
            
        dividerFormKey = dividerForm.generateKey()
        if dividerFormKey in self.key2node or dividerFormKey in additionalCostFreeForms:
            interCost = 0
            
        divisibleFormKey = divisibleForm.generateKey()
        if divisibleFormKey in self.key2node or divisibleFormKey in additionalCostFreeForms:
            interCost = 0
            gcdCost = 0
        
        return resultMonomialsCost - gcdCost - interCost - restCost 
    
    def getForms(self):
        return findPolynomialCoeff(self.form, self, 1)
    
    def generateReducedKeys(self):
        self.reducedKeys = set([])
        quotientForm, dividerForm, divisibleForm, restForm = findPolynomialCoeff(self.form, self, 1)
        
        if len(quotientForm.subforms) > 1:
            quotientReduced = reduceForm(quotientForm)
            self.reducedKeys.add(quotientForm.generateKey())
            
        if len(dividerForm.subforms) > 1:
            dividerReduced = reduceForm(dividerForm)
            self.reducedKeys.add(dividerForm.generateKey())
            
        if len(divisibleForm.subforms) > 1:
            divisibleReduced = reduceForm(divisibleForm)
            self.reducedKeys.add(divisibleForm.generateKey())
        
        if len(restForm.subforms) > 1:
            restReduced = reduceForm(restForm)
            self.reducedKeys.add(restForm.generateKey())
        
    
def fuseDivisiblePolynomials(pol1, pol2):
    commonIntermediates = pol1.intermediateMonomials & pol2.intermediateMonomials
    
    if not commonIntermediates:
        return None
    
    newGcdMatrix = {}
    
    for gcd in pol1.gcdMatrix:
        for intermediate in pol1.gcdMatrix[gcd]:
            if intermediate in commonIntermediates:
                if not gcd in newGcdMatrix:
                    newGcdMatrix[gcd] = {}
                    
                newGcdMatrix[gcd][intermediate] = pol1.gcdMatrix[gcd][intermediate]
                
    for gcd in pol2.gcdMatrix:
        for intermediate in pol2.gcdMatrix[gcd]:
            if intermediate in commonIntermediates:
                if not gcd in newGcdMatrix:
                    newGcdMatrix[gcd] = {}
                    
                newGcdMatrix[gcd][intermediate] = pol2.gcdMatrix[gcd][intermediate]
                
    return DivisiblePolynomial(newGcdMatrix, pol1.form, pol1.key2node)
        
class OptimizationResult:
    def __init__(self):
        self.dividingWasPossible = False
        self.quotientForm = None
        self.deviderForm = None
        self.divisibleForm = None
        self.remainderForm = None
        self.relativelyPrimes = []
        self.gcdKeys = None

class NodeOptimizer:
    def __init__(self, nodeForm, logName, key2existingNode):
        self.form = nodeForm
        self.logName = logName
        self.key2existingNode = key2existingNode
        self.potentialSolutions = []
        
    def log(self, logText):
        lf = open(self.logName, 'a')
        lf.write(logText+"\n")
        lf.close()
        
    def generateReducedKeys(self):
        for sol in self.potentialSolutions:
            sol.generateReducedKeys()
        
    def findPotentialSolutions(self):
        self.log("Optimizing node: start")
        
        if len(self.form.subforms) == 1:
            self.optimizeMonomialNode()
            
#            deviderForm = 
        
        
#        gcdSubforms = reduce( math.gcd, list(self.form.subforms.keys()) )
        
#        if gcdSubforms != 1:
#            self.log("Common divider for all subforms! "+ str(gcdSubforms))
##            return
#        else:
#            self.log("There is no common divider for all subforms!")
        
        gcdSubformsPairs =set([])
        subformKeys = list(self.form.subforms.keys())
        
        for i , subKey1 in enumerate(subformKeys):
            for subKey2 in subformKeys[i+1:]:
                gcdSubformsPairs.add( math.gcd(subKey1, subKey2) )
                
        monoGCDdict = {}
        
        for subGcd in gcdSubformsPairs:
            newRow = {}
            newRow[subGcd] = {}
            for subKey in subformKeys:
                if subKey % subGcd == 0:
                    intermediate = subKey // subGcd
                    newRow[subGcd][intermediate] = subKey
                    
#                    if subKey*subGcd != 
                    
            monoGCDdict[subGcd] = DivisiblePolynomial(newRow, self.form, self.key2existingNode) 
            
        processedPolynomials = []
        usedIntermediates = set([])
        queue = list(monoGCDdict.values())
        self.gcdKeys = frozenset(monoGCDdict.keys())
        
        unitPolynomial = frozenset([1])
        
        while queue:
            newQueue = []
            for poly in queue:
                monomials2fuse = self.gcdKeys - poly.gcdMonomials
                
                if poly.intermediateMonomials != unitPolynomial and poly.gcdMonomials != unitPolynomial:
                    processedPolynomials.append(poly)
                
                for m in monomials2fuse:
                    newPoly = fuseDivisiblePolynomials(poly, monoGCDdict[m]  )
                    if newPoly != None:
                        if not newPoly.intermediateMonomials in usedIntermediates:
                            newQueue.append(newPoly)
                            usedIntermediates.add(newPoly.intermediateMonomials)
#                            usedIntermediates.add(newPoly.gcdMonomials)
            
            queue = newQueue
            
        self.potentialSolutions = processedPolynomials
        
    """
    return: polynomial was devided, quotient form, divider form, divisible form, remainder form
    """
    def optimize(self):
        self.findPotentialSolutions()
        
        unitPolynomial = frozenset([1])
        
        optimizationResult = OptimizationResult()
        
        if not self.potentialSolutions:
            optimizationResult.dividingWasPossible = False
#            print("nie znaleziono zadnych rozwiazan!")
#            print(self.form.subforms)
            if not optimizationResult.relativelyPrimes:
                for subKey in self.form.subforms:
                    newForm = CanonicalForm()
                    newForm.subforms[subKey] = self.form.subforms[subKey]
                    optimizationResult.relativelyPrimes.append(newForm)
                
            return optimizationResult
        
        if self.gcdKeys == unitPolynomial:
            optimizationResult.dividingWasPossible = False
            
            for subKey in self.form.subforms:
                newForm = CanonicalForm()
                newForm.subforms[subKey] = self.form.subforms[subKey]
                optimizationResult.relativelyPrimes.append(newForm)
                
            return optimizationResult
        
        bestPolynomial = max(self.potentialSolutions, key = lambda item: item.profit)
        gcdCoeff = reduce(math.gcd, list(self.form.subforms.values()) )
        
        quotientForm, dividerForm, divisibleForm, restForm = findPolynomialCoeff(self.form, bestPolynomial, gcdCoeff)
        
        optimizationResult.dividingWasPossible = True
        optimizationResult.quotientForm = quotientForm
        optimizationResult.deviderForm = dividerForm
        optimizationResult.divisibleForm = divisibleForm
        optimizationResult.remainderForm = restForm
#        if len( bestPolynomial.resultsMonomials ) < len(bestPolynomial.gcdMonomials)*len(bestPolynomial.intermediateMonomials):
#        print(15*"#")
#        print("Found best solution from ", len(processedPolynomials))
#        print("Highest profit: ", bestPolynomial.profit)
#        print("Full form len: ", len(self.form.subforms))
#        print("Best poly describes: ", len(bestPolynomial.resultsMonomials))
#        print("Using polynomials of size: ", len(bestPolynomial.gcdMonomials), " and ",len(bestPolynomial.intermediateMonomials))
        return optimizationResult
                    
    def optimizeMonomialNode(self):
        raise Exception("Not implemented!")
        
def findPolynomialCoeff(form, poly, gcdCoeff):
#        remainderForm = CanonicalForm()
    #inicjalizacja wartosci
    quotientForm = CanonicalForm()
    dividerForm = CanonicalForm()
    
#    if len(poly.intermediateMonomials) > len(poly.gcdMonomials):
#        reverseGcdMat = {}
#        
#        for gcdKey in poly.gcdMatrix:
#            for interKey in poly.gcdMatrix[gcdKey]:
#                resKey = poly.gcdMatrix[gcdKey][interKey]
#                
#                if not interKey in reverseGcdMat:
#                    reverseGcdMat[interKey] = {}
#                 
#                reverseGcdMat[interKey][gcdKey] = resKey
#                
#        poly = DivisiblePolynomial(reverseGcdMat, form)
                
    
    for subKey in poly.gcdMonomials:
        dividerForm.subforms[subKey] = None
        
    for subKey in poly.intermediateMonomials:
        quotientForm.subforms[subKey] = None
        
    #znalezienie wynikow zaleznych tylko i wylacznie od pojedynczych intermediatow
    intermediate2results = {}
    
    for dividerKey in poly.gcdMatrix:
        for interKey in poly.gcdMatrix[dividerKey]:
            if not interKey in intermediate2results:
                intermediate2results[interKey] = set([])
                
            intermediate2results[interKey].add(poly.gcdMatrix[dividerKey][interKey])
            
    intermediate2uniqueResults ={}
    
    for interKey in intermediate2results:
        uniqueInters = intermediate2results[interKey]
        otherInters = set(intermediate2results.keys())
        otherInters.remove(interKey)
        
        for otherInter in otherInters:
            uniqueInters -= intermediate2results[otherInter]
            
        intermediate2uniqueResults[interKey] = uniqueInters
        
    #okreslenie wartosci intermediatow
    
    for intermediate in intermediate2uniqueResults:
        uniqueResCoeffs = [ form.subforms[subKey] for subKey in intermediate2uniqueResults[intermediate] ]
#        print(uniqueResCoeffs)
        newCoeff = 1
        if uniqueResCoeffs:
            newCoeff = reduce(math.gcd, uniqueResCoeffs)
        quotientForm.subforms[intermediate] = newCoeff
        
    #okreslenie wartosci dzielnikow
    
    for gcdKey in poly.gcdMatrix:
        for interKey in poly.gcdMatrix[gcdKey]:
            resKey = poly.gcdMatrix[gcdKey][interKey]
            if resKey in intermediate2uniqueResults[interKey]:
                dividerForm.subforms[gcdKey] = form.subforms[resKey]//quotientForm.subforms[interKey]
        
    divisibleForm = multiplyForms(quotientForm, dividerForm)
    restForm = subtractForms(form, divisibleForm)
    
#    testForm = addForms(restForm, divisibleForm)
#    if form.generateKey() != testForm.generateKey():
#        raise Exception("Simplyfied form is not identical to source form!")
    #wiecej info
#        print(15*"#")
#        print("Full form len: ", len(self.form.subforms))
#        print("Divisible describes: ", len(divisibleForm.subforms))
#        print("By multipling: ", len(quotientForm.subforms), " and ", len(dividerForm.subforms))
#        print("Rest size: ", len(restForm.subforms))
        
    return quotientForm, dividerForm, divisibleForm, restForm