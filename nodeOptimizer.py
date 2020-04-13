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

class DivisiblePolynomial:
    def __init__(self, gcdMat):
        self.gcdMatrix = gcdMat
        self.gcdMonomials = frozenset(self.gcdMatrix.keys())
        self.intermediateMonomials = frozenset([ ])
        self.resultsMonomials = set([])
        
        for gcdKey in self.gcdMatrix:
            self.intermediateMonomials |= set( self.gcdMatrix[gcdKey].keys() )
            self.resultsMonomials |= set(self.gcdMatrix[gcdKey].values())
        
        self.profit = self.calcProfit()
        
    def calcProfit(self):
        resultMonomialsNo = len(self.resultsMonomials)
        gcdLen = len(self.gcdMatrix)
        interLen = len(self.intermediateMonomials)
        
        return 2*resultMonomialsNo - gcdLen - interLen 
    
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
                
    return DivisiblePolynomial(newGcdMatrix)
        
class OptimizationResult:
    def __init__(self):
        self.dividingWasPossible = False
        self.quotientForm = None
        self.deviderForm = None
        self.divisibleForm = None
        self.remainderForm = None
        self.relativelyPrimes = []

class NodeOptimizer:
    def __init__(self, nodeForm, logName):
        self.form = nodeForm
        self.logName = logName
        
    def log(self, logText):
        lf = open(self.logName, 'a')
        lf.write(logText+"\n")
        lf.close()
        
    """
    return: polynomial was devided, quotient form, divider form, divisible form, remainder form
    """
    def optimize(self):
        self.log("Optimizing node: start")
        
        if len(self.form.subforms) == 1:
            return self.optimizeMonomialNode()
            
#            deviderForm = 
        
        gcdCoeff = reduce(math.gcd, list(self.form.subforms.values()) )
        gcdSubforms = reduce( math.gcd, list(self.form.subforms.keys()) )
        
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
                    
            monoGCDdict[subGcd] = DivisiblePolynomial(newRow) 
            
        processedPolynomials = []
        usedIntermediates = set([])
        queue = list(monoGCDdict.values())
        gcdKeys = frozenset(monoGCDdict.keys())
        
        unitPolynomial = frozenset([1])
        
        optimizationResult = OptimizationResult()
        
        if gcdKeys == unitPolynomial:
            optimizationResult.dividingWasPossible = False
            
            for subKey in self.form.subforms:
                newForm = CanonicalForm()
                newForm.subforms[subKey] = self.form.subforms[subKey]
                optimizationResult.relativelyPrimes.append(newForm)
                
            return optimizationResult
        
        while queue:
            newQueue = []
            for poly in queue:
                monomials2fuse = gcdKeys - poly.gcdMonomials
                
                if poly.intermediateMonomials != unitPolynomial and poly.gcdMonomials != unitPolynomial:
                    processedPolynomials.append(poly)
                
                for m in monomials2fuse:
                    newPoly = fuseDivisiblePolynomials(poly, monoGCDdict[m]  )
                    if newPoly != None:
                        if not newPoly.intermediateMonomials in usedIntermediates:
                            newQueue.append(newPoly)
                            usedIntermediates.add(newPoly.intermediateMonomials)
                            usedIntermediates.add(newPoly.gcdMonomials)
            
            queue = newQueue
            
        bestPolynomial = max(processedPolynomials, key = lambda item: item.profit)
        
        quotientForm, dividerForm, divisibleForm, restForm = self.findPolynomialCoeff(bestPolynomial, gcdCoeff)
        
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

        
    def findPolynomialCoeff(self, poly, gcdCoeff):
#        remainderForm = CanonicalForm()
        #inicjalizacja wartosci
        quotientForm = CanonicalForm()
        dividerForm = CanonicalForm()
        
        if len(poly.intermediateMonomials) > len(poly.gcdMonomials):
            reverseGcdMat = {}
            
            for gcdKey in poly.gcdMatrix:
                for interKey in poly.gcdMatrix[gcdKey]:
                    resKey = poly.gcdMatrix[gcdKey][interKey]
                    
                    if not interKey in reverseGcdMat:
                        reverseGcdMat[interKey] = {}
                     
                    reverseGcdMat[interKey][gcdKey] = resKey
                    
            poly = DivisiblePolynomial(reverseGcdMat)
                    
        
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
            uniqueResCoeffs = [ self.form.subforms[subKey] for subKey in intermediate2uniqueResults[intermediate] ]
            newCoeff = reduce(math.gcd, uniqueResCoeffs)
            quotientForm.subforms[intermediate] = newCoeff
            
        #okreslenie wartosci dzielnikow
        
        for gcdKey in poly.gcdMatrix:
            for interKey in poly.gcdMatrix[gcdKey]:
                resKey = poly.gcdMatrix[gcdKey][interKey]
                if resKey in intermediate2uniqueResults[interKey]:
                    dividerForm.subforms[gcdKey] = self.form.subforms[resKey]//quotientForm.subforms[interKey]
            
        divisibleForm = multiplyForms(quotientForm, dividerForm)
        restForm = subtractForms(self.form, divisibleForm)
        
        testForm = addForms(restForm, divisibleForm)
        if self.form.generateKey() != testForm.generateKey():
            raise Exception("Simplyfied form is not identical to source form!")
        
#        print(15*"#")
#        print("Full form len: ", len(self.form.subforms))
#        print("Divisible describes: ", len(divisibleForm.subforms))
#        print("By multipling: ", len(quotientForm.subforms), " and ", len(dividerForm.subforms))
#        print("Rest size: ", len(restForm.subforms))
            
        return quotientForm, dividerForm, divisibleForm, restForm
                    
    def optimizeMonomialNode(self):
        raise Exception("Not implemented!")