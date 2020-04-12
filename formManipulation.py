#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mar 28 12:23:44 2020

@author: michal
"""
from collections import defaultdict

def primeFactorization(number, primesList):
    factors = defaultdict(int)
    
    temp = number
    primeIndex = 0
    while temp != 1:
        prime = primesList[primeIndex]
        
        while temp % prime == 0:
            factors[prime] += 1
            temp = temp//prime
            
        primeIndex += 1
    
    return factors

def generateSubKey2AtomDist(form, primesList,  atomDistribution = None):
    subformKey2atomDistribution = {}
    if atomDistribution:
        subformKey2atomDistribution = atomDistribution
    else:
        for subKey in form.subforms:
            subformKey2atomDistribution[subKey] = primeFactorization(subKey, primesList)
            
    return subformKey2atomDistribution

def CouchySchwarzTest(subforms1, subforms2, subforms1norm = -1 ):
    if subforms1norm < 0:
        subforms1norm = subformInnerProduct( subforms1, subforms1 )

    subforms2norm = subformInnerProduct(subforms2, subforms2)

    innerProd = subformInnerProduct(subforms1, subforms2)

    if innerProd*innerProd == subforms1norm*subforms2norm:
        return True

    return False

def subformInnerProduct(subforms1, subforms2):
    innerProd = 0
    keys = set(subforms1.keys()) & set(subforms2.keys())

    for key in keys:
        innerProd += subforms1[key] * subforms2[key]

    return innerProd 