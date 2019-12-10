#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 29 11:01:07 2019

@author: michal
"""

import pickle

class CanonicalAtom:
#    __slots__ = [ "name", "power", "node" ]
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
#    __slots__ = [ "atoms", "coefficient", "key"]
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
#                self.atoms[atomKey] = deepcopy(subform.atoms[atomKey])
                self.atoms[atomKey] = pickle.loads(pickle.dumps(subform.atoms[atomKey], -1 ))
                
        self.key = ""
    
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
#                newForm = deepcopy( temp[s1key] )
                newForm = pickle.loads(pickle.dumps(temp[s1key] , -1))
                newForm.multiply( canonicalForm.subforms[s2key] )
                
                newKey = newForm.generateKey()
                
                if newKey in self.subforms:
                    self.subforms[newKey].coefficient += newForm.coefficient
                else:
                    self.subforms[newKey] = newForm
    
    def add(self, canonicalForm):
        for subFormKey in canonicalForm.subforms:
            if subFormKey in self.subforms:
                self.subforms[subFormKey].coefficient += canonicalForm.subforms[subFormKey].coefficient
            else:
#                self.subforms[subFormKey] = deepcopy(canonicalForm.subforms[subFormKey])
                self.subforms[subFormKey] = pickle.loads(pickle.dumps(canonicalForm.subforms[subFormKey], -1))
               
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
                self.subforms[subFormKey].coefficient -= canonicalForm.subforms[subFormKey].coefficient
            else:
#                self.subforms[subFormKey] = deepcopy(canonicalForm.subforms[subFormKey])
                self.subforms[subFormKey] = pickle.loads(pickle.dumps( canonicalForm.subforms[subFormKey], -1))
                self.subforms[subFormKey].coefficient *= -1
                
        self.removeZeroSubforms()
                
    def reverseSign(self):
        for subFormKey in self.subforms:
            self.subforms[subFormKey].coefficient *= -1