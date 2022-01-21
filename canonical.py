#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 29 11:01:07 2019

@author: michal
"""
import pickle
import hashlib 

class CanonicalSubformFactory:
    def __init__(self):
        self.subformId2node = {}
        self.node2subformId = {}
        infile = open("primes.pickle",'rb')
        self.primes = pickle.load(infile)
        infile.close()
        self.currentPrime = 0
        
    def clean(self):
        self.subformId2node = {}
        self.node2subformId = {}
        self.currentPrime = 0
        
    def createSubform(self, node):
        key = self.primes[self.currentPrime]
        self.currentPrime += 1
        self.subformId2node[key] = node
        self.node2subformId[node] = key
                  
        return key
        

def multiplyForms(form1, form2):
    newForm = CanonicalForm()
    
    for s1key in form1.subforms:
        sub1Coeff = form1.subforms[s1key]
        for s2key in form2.subforms:
            sub2Coeff = form2.subforms[s2key]
            
            newKey = s1key*s2key
            
            if not newKey in newForm.subforms:
                newCoeff = sub1Coeff*sub2Coeff
                newForm.subforms[newKey] = newCoeff
            else:
                newCoeff = sub1Coeff*sub2Coeff  + newForm.subforms[newKey]
                newForm.subforms[newKey] = newCoeff
                
    return newForm

def addForms(form1, form2):
    newForm = CanonicalForm()
    
    newForm.subforms.update(form1.subforms)
    
    for subFormKey in form2.subforms:
        if subFormKey in newForm.subforms:
            newForm.subforms[subFormKey] += form2.subforms[subFormKey]
        else:
            newForm.subforms[subFormKey] = form2.subforms[subFormKey]
           
    removeZeroSubforms(newForm)
    return newForm
            
def removeZeroSubforms(form):
    for key in tuple(form.subforms.keys()):
        if form.subforms[key] == 0:
            del form.subforms[key]

def subtractForms(form1, form2):
    newForm = CanonicalForm()
    
    newForm.subforms.update(form1.subforms)
    
    for subFormKey in form2.subforms:
        if subFormKey in newForm.subforms:
            newForm.subforms[subFormKey] -= form2.subforms[subFormKey]
        else:
            newForm.subforms[subFormKey] = -1*form2.subforms[subFormKey]
            
            
    removeZeroSubforms(newForm)
    return newForm
            
def reverseFormSign(form):
    newForm = CanonicalForm()
    for subFormKey in form.subforms:
        newForm.subforms[subFormKey] = -1*form.subforms[subFormKey]
        
    return newForm
    
def subformMultAtomDict( atomDict1, atomDict2):
    atomDict = {}
    
    for atomKey in atomDict1:
        atomDict[atomKey] = atomDict1[atomKey]
        
    for atomKey in atomDict2:
        if atomKey in atomDict:
            atomDict[atomKey] += atomDict2[atomKey]
        else:
            atomDict[atomKey] = atomDict2[atomKey]
            
    return atomDict

def atomDict2subformKey(atomDict):
    atomKeys = []
    
    for atomKey in atomDict:
        power = atomDict[atomKey]
        
        if power == 1:
            atomKeys.append(atomKey)
        else:
            atomKeys.append(atomKey+"^"+str(power))
            
    return "*".join(sorted(atomKeys))
    

class CanonicalForm:
    def __init__(self):
        self.subforms = {}
    
    def generateKey(self):
#        return hash(frozenset(self.subforms.items()))
        return int(hashlib.md5(str(sorted(self.subforms.items())).encode()).hexdigest(), 16)
#        keyList = []
#        
#        for subKey in self.subforms:
#            coeff = self.subforms[subKey]
#            
#            newKey = str(subKey)
#            
#            if coeff != 1:
#                newKey += "*"+str(coeff)
#            
#            keyList.append( newKey )
#            
#        return int(hashlib.md5(("+".join(sorted( keyList ))).encode()).hexdigest(), 16)
    
    