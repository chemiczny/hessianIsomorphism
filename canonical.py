#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 29 11:01:07 2019

@author: michal
"""

import hashlib 
#from copy import copy
#import pickle

#class CanonicalAtomFactory:
#    def __init__(self):
#        self.key2atom = {}
#        
#    def clean(self):
#        self.key2atom = {}
#        
#    def createAtom(self, name, power):
#        if power != 1:
#            key = "{name}^power".format(name = name, power = power)
#        else:
#            key = name
#        
#        if not key in self.key2atom:
#            self.key2atom[key] = CanonicalAtom(name, power)
#            
#        return self.key2atom[key]
#
#__AtomFactory__ = CanonicalAtomFactory()

class CanonicalSubformFactory:
    def __init__(self):
        self.key2subform = {}
        
    def clean(self):
        self.key2subform = {}
        
    def createSubform(self, atomDict, coeff, key = ""):
        if not key:
            key = atomDict2subformKey(atomDict)+"*"+str(coeff)
#        global __AtomFactory__
        
        if not key in self.key2subform:
            newSubform = CanonicalSubform()
            newSubform.coefficient = coeff
            newSubform.atoms = atomDict
            
#            for atomName in atomDict:
#                power = atomDict[atomName]
#                newSubform.atoms[atomName] = __AtomFactory__.createAtom(atomName, power)
                
            self.key2subform[key] = newSubform
        
        return self.key2subform[key]
        
__SubformFactory__ = CanonicalSubformFactory()

#class CanonicalAtom:
##    __slots__ = [ "name", "power" ]
#    def __init__(self, name, power):
#        self.name = name
#        self.power = power
#        
#    def getKey(self):
#        key = self.name
#        if self.power != 1:
#            key += "^"+str(self.power)
#            
#        return key

def atomKey(name, power):
    key = name
    if power != 1:
        key += "^"+str(power)
        
    return key

class CanonicalSubform:
#    __slots__ = [ "atoms", "coefficient", "key"]
    def __init__(self):
        self.atoms = {}
        self.coefficient = 1
        self.key = ""
        
    def getKey(self):
        if self.key:
            return self.key
        
        return self.generateKey()
#        return self.key
    
    def updateKeys(self):
        self.atoms, oldAtoms = {} , self.atoms
        
        for atomKey in oldAtoms:
            atom = oldAtoms[atomKey]
            self.atoms[atom.name] = atom
        
    def generateKey(self):
        keyList = []
        for atomName in self.atoms:
            keyList.append( atomKey( atomName, self.atoms[atomName] ) )
            
        keyList.sort()
        self.key = "*".join(keyList)
        return self.key
    
    
    def multiply(self, subform):
        self.coefficient *= subform.coefficient
        
        for atomKey in subform.atoms:
            if atomKey in self.atoms:
#                self.atoms[atomKey].power += subform.atoms[atomKey].power
                self.atoms[atomKey] =  self.atoms[atomKey].power +  subform.atoms[atomKey].power 
            else:
                #WTF?
                self.atoms[atomKey] = subform.atoms[atomKey]
#                self.atoms[atomKey] = deepcopy(subform.atoms[atomKey])
#                self.atoms[atomKey] = pickle.loads(pickle.dumps(subform.atoms[atomKey], -1 ))
#                self.atoms[atomKey] = copy(subform.atoms[atomKey])
                
        self.key = ""
        

def multiplyForms(form1, form2):
    newForm = CanonicalForm()
    
    for s1key in form1.subforms:
        for s2key in form2.subforms:
#                newForm = deepcopy( temp[s1key] )
            sub1 = form1.subforms[s1key]
            sub2 = form2.subforms[s2key]
            
            atomDict = subformMultAtomDict( sub1 , sub2 )
            newKey = atomDict2subformKey(atomDict)
            
            if not newKey in newForm.subforms:
                newCoeff = sub1.coefficient*sub2.coefficient
                fullKey = newKey+"*"+str(newCoeff)
                newForm.subforms[newKey] = __SubformFactory__.createSubform( atomDict, newCoeff, fullKey )
            else:
                newCoeff = sub1.coefficient*sub2.coefficient  + newForm.subforms[newKey].coefficient
                fullKey = newKey+"*"+str(newCoeff)
                newForm.subforms[newKey] = __SubformFactory__.createSubform( atomDict, newCoeff, fullKey )
                
    return newForm

def addForms(form1, form2):
    newForm = CanonicalForm()
    
    for subFormKey in form1.subforms:
        newForm.subforms[subFormKey] = form1.subforms[subFormKey]
    
    for subFormKey in form2.subforms:
        if subFormKey in newForm.subforms:
            atomDict = form2.subforms[subFormKey].atoms
            newForm.subforms[subFormKey] = __SubformFactory__.createSubform(atomDict , form2.subforms[subFormKey].coefficient + newForm.subforms[subFormKey].coefficient)
        else:
#                self.subforms[subFormKey] = deepcopy(canonicalForm.subforms[subFormKey])
            newForm.subforms[subFormKey] = form2.subforms[subFormKey]
           
#    return newForm
    return removeZeroSubforms(newForm)
            
def removeZeroSubforms(form):
    newForm = CanonicalForm()
    key2delete = []
    
    for key in form.subforms:
        if form.subforms[key].coefficient == 0:
            key2delete.append(key)
        else:
            atomDict = form.subforms[key].atoms
            newForm.subforms[key] = __SubformFactory__.createSubform(atomDict , form.subforms[key].coefficient )
            
    return newForm

def subtractForms(form1, form2):
    newForm = CanonicalForm()
    
    for subFormKey in form1.subforms:
        newForm.subforms[subFormKey] = form1.subforms[subFormKey]
    
    for subFormKey in form2.subforms:
        if subFormKey in newForm.subforms:
            atomDict = newForm.subforms[subFormKey].atoms
            newForm.subforms[subFormKey] = __SubformFactory__.createSubform(atomDict, newForm.subforms[subFormKey].coefficient - form2.subforms[subFormKey].coefficient )
        else:
#                self.subforms[subFormKey] = deepcopy(canonicalForm.subforms[subFormKey])
            atomDict = form2.subforms[subFormKey].atoms
            newForm.subforms[subFormKey] = __SubformFactory__.createSubform(atomDict, form2.subforms[subFormKey].coefficient*-1)
            
    return removeZeroSubforms(newForm)
            
def reverseFormSign(form):
    newForm = CanonicalForm()
    for subFormKey in form.subforms:
        atomDict = form.subforms[subFormKey].atoms
        newForm.subforms[subFormKey] = __SubformFactory__.createSubform(atomDict, form.subforms[subFormKey].coefficient*-1)
        
    return newForm
        
#def subform2AtomDict(subform):
#    atomDict = {}
#    
#    for atomKey in subform.atoms:
#        atom = subform.atoms[atomKey]
#        atomDict[atom.name] = atom.power
#        
#    return atomDict
    
def subformMultAtomDict( subform1, subform2):
    atomDict = {}
    
    for atomKey in subform1.atoms:
        atomDict[atomKey] = subform1.atoms[atomKey]
        
    for atomKey in subform2.atoms:
        if atomKey in atomDict:
            atomDict[atomKey] += subform2.atoms[atomKey]
        else:
            atomDict[atomKey] = subform2.atoms[atomKey]
            
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
            subform = self.subforms[subKey]
            newKey = subform.getKey()
            
            if subform.coefficient != 1:
                newKey += "*"+str(subform.coefficient)
            
            keyList.append( newKey )
            
            
        return str(hashlib.md5(("+".join(sorted( keyList ))).encode()).digest())
#        return "+".join(sorted( keyList ))
    
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
#                newForm = deepcopy( temp[s1key] )
                sub1 = temp[s1key]
                sub2 = canonicalForm.subforms[s2key]
                
                atomDict = subformMultAtomDict( sub1 , sub2 )
                newKey = atomDict2subformKey(atomDict)
                
                if not newKey in self.subforms:
                    self.subforms[newKey] = __SubformFactory__.createSubform( atomDict, sub1.coefficient*sub2.coefficient )
                else:
                    self.subforms[newKey] = __SubformFactory__.createSubform( atomDict, sub1.coefficient*sub2.coefficient  + self.subforms[newKey].coefficient )
    
    def add(self, canonicalForm):
        for subFormKey in canonicalForm.subforms:
            if subFormKey in self.subforms:
                atomDict = self.subforms[subFormKey].atoms
                self.subforms[subFormKey] = __SubformFactory__.createSubform(atomDict , self.subforms[subFormKey].coefficient + canonicalForm.subforms[subFormKey].coefficient)
            else:
#                self.subforms[subFormKey] = deepcopy(canonicalForm.subforms[subFormKey])
                self.subforms[subFormKey] = canonicalForm.subforms[subFormKey]
               
        self.removeZeroSubforms()
                
    def removeZeroSubforms(self):
        key2delete = []
        for key in self.subforms:
            if self.subforms[key].coefficient == 0:
                key2delete.append(key)
                
        for key in key2delete:
            del self.subforms[key]
    
    def subtract(self, canonicalForm):
        for subFormKey in canonicalForm.subforms:
            if subFormKey in self.subforms:
                atomDict = self.subforms[subFormKey].atoms
                self.subforms[subFormKey] = __SubformFactory__.createSubform(atomDict, self.subforms[subFormKey].coefficient - canonicalForm.subforms[subFormKey].coefficient )
            else:
#                self.subforms[subFormKey] = deepcopy(canonicalForm.subforms[subFormKey])
                atomDict = canonicalForm.subforms[subFormKey].atoms
                self.subforms[subFormKey] = __SubformFactory__.createSubform(atomDict, canonicalForm.subforms[subFormKey].coefficient*-1)
                
        self.removeZeroSubforms()
                
    def reverseSign(self):
        for subFormKey in self.subforms:
            atomDict = self.subforms[subFormKey].atoms
            self.subforms[subFormKey] = __SubformFactory__.createSubform(atomDict, self.subforms[subFormKey].coefficient*-1)