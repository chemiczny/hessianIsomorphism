#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 29 11:01:07 2019

@author: michal
"""

import hashlib 

class CanonicalSubformFactory:
    def __init__(self):
        self.subformKey2atomDict = {}
        
    def clean(self):
        self.subformKey2atomDict = {}
        
    def createSubform(self, atomDict, key = ""):
        if not key:
            key = atomDict2subformKey(atomDict)
        
        if not key in self.subformKey2atomDict:
            self.subformKey2atomDict[key] = atomDict
            
#        print("Aktualny stan fabryki: ", list(self.subformKey2atomDict.keys()))
        
        return key
        
__SubformFactory__ = CanonicalSubformFactory()

def atomKey(name, power):
    key = name
    if power != 1:
        key += "^"+str(power)
        
    return key

#class CanonicalSubform:
##    __slots__ = [ "atoms", "coefficient", "key"]
#    def __init__(self):
#        self.atoms = {}
#        self.coefficient = 1
#        self.key = ""
#        
#    def getKey(self):
#        if self.key:
#            return self.key
#        
#        return self.generateKey()
##        return self.key
#    
#    def updateKeys(self):
#        self.atoms, oldAtoms = {} , self.atoms
#        
#        for atomKey in oldAtoms:
#            atom = oldAtoms[atomKey]
#            self.atoms[atom.name] = atom
#        
#    def generateKey(self):
#        keyList = []
#        for atomName in self.atoms:
#            keyList.append( atomKey( atomName, self.atoms[atomName] ) )
#            
#        keyList.sort()
#        self.key = "*".join(keyList)
#        return self.key
#    
#    
#    def multiply(self, subform):
#        self.coefficient *= subform.coefficient
#        
#        for atomKey in subform.atoms:
#            if atomKey in self.atoms:
##                self.atoms[atomKey].power += subform.atoms[atomKey].power
#                self.atoms[atomKey] =  self.atoms[atomKey].power +  subform.atoms[atomKey].power 
#            else:
#                #WTF?
#                self.atoms[atomKey] = subform.atoms[atomKey]
##                self.atoms[atomKey] = deepcopy(subform.atoms[atomKey])
##                self.atoms[atomKey] = pickle.loads(pickle.dumps(subform.atoms[atomKey], -1 ))
##                self.atoms[atomKey] = copy(subform.atoms[atomKey])
#                
#        self.key = ""
        

def multiplyForms(form1, form2):
    global __SubformFactory__
    newForm = CanonicalForm()
    
    for s1key in form1.subforms:
        for s2key in form2.subforms:
#                newForm = deepcopy( temp[s1key] )
            sub1Coeff = form1.subforms[s1key]
            sub2Coeff = form2.subforms[s2key]
            
            sub1 = __SubformFactory__.subformKey2atomDict[s1key]
            sub2 = __SubformFactory__.subformKey2atomDict[s2key]
            
            atomDict = subformMultAtomDict( sub1 , sub2 )
            newKey = atomDict2subformKey(atomDict)
            
            if not newKey in newForm.subforms:
                newCoeff = sub1Coeff*sub2Coeff
                newForm.subforms[newKey] = newCoeff
                __SubformFactory__.createSubform( atomDict, newKey )
            else:
                newCoeff = sub1Coeff*sub2Coeff  + newForm.subforms[newKey]
                newForm.subforms[newKey] = newCoeff
                
    return newForm

def addForms(form1, form2):
    newForm = CanonicalForm()
    
    for subFormKey in form1.subforms:
        newForm.subforms[subFormKey] = form1.subforms[subFormKey]
    
    for subFormKey in form2.subforms:
        if subFormKey in newForm.subforms:
            newForm.subforms[subFormKey] += form2.subforms[subFormKey]
        else:
            newForm.subforms[subFormKey] = form2.subforms[subFormKey]
           
    return removeZeroSubforms(newForm)
            
def removeZeroSubforms(form):
    newForm = CanonicalForm()
    
    for key in form.subforms:
        if form.subforms[key] != 0:
            newForm.subforms[key] = form.subforms[key] 
            
    return newForm

def subtractForms(form1, form2):
    newForm = CanonicalForm()
    
    for subFormKey in form1.subforms:
        newForm.subforms[subFormKey] = form1.subforms[subFormKey]
    
    for subFormKey in form2.subforms:
        if subFormKey in newForm.subforms:
            newForm.subforms[subFormKey] -= form2.subforms[subFormKey]
        else:
            newForm.subforms[subFormKey] = -1*form2.subforms[subFormKey]
            
    return removeZeroSubforms(newForm)
            
def reverseFormSign(form):
    newForm = CanonicalForm()
    for subFormKey in form.subforms:
        newForm.subforms[subFormKey] = -1*form.subforms[subFormKey]
        
    return newForm
        
#def subform2AtomDict(subform):
#    atomDict = {}
#    
#    for atomKey in subform.atoms:
#        atom = subform.atoms[atomKey]
#        atomDict[atom.name] = atom.power
#        
#    return atomDict
    
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
    

#    def divide(self):
#        pass
#    
#    def inverse(self):
#        pass

class CanonicalForm:
#    __slots__ = "subforms"
    def __init__(self):
        self.subforms = {}
#        self.subformsDown = []
    
    def generateKey(self):
        keyList = []
        
        for subKey in self.subforms:
#            print("klucz: ", subKey)
            coeff = self.subforms[subKey]
            
            newKey = subKey
            
            if coeff != 1:
                newKey += "*"+str(coeff)
            
            keyList.append( newKey )
            
#        print(keyList)
        return int(hashlib.md5(("+".join(sorted( keyList ))).encode()).hexdigest(), 16)
#        return "+".join(sorted( keyList ))
    
#    def updateKeys(self):
#        self.subforms, oldSubforms = {}, self.subforms
#        
#        for key in oldSubforms:
#            subform = oldSubforms[key]
#            subform.updateKeys()
#            key = subform.generateKey()
#            self.subforms[key] = subform
    