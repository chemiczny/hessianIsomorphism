#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 22 16:03:03 2019

@author: michal
"""
from collections import defaultdict

functions2operations = {}

cppF = open("dupa.cpp", 'r')

line = cppF.readline()

while line and not "void" in line:
    line = cppF.readline()

key = line.strip()

operators = defaultdict(int)

line = cppF.readline()
lineNo = 0
while line and not "void" in line:
    line = cppF.readline()
    
    plusNo = line.count("+")
    minusNo = line.count("-")
    multNo = line.count("*")
    devNo = line.count("/")
    
    operators["+"] += plusNo
    operators["-"] += minusNo
    operators["*"] += multNo
    operators["/"] += devNo
    operators["sqrt"] += line.count("sqrt")
    operators["pow"] += line.count("pow")
    operators["exp"] += line.count("exp")
#    operators["double"] +=  line.count("double")
    lineNo += 1
    
print(key, lineNo)

functions2operations[key] = operators

key = line.strip()

operators = defaultdict(int)

line = cppF.readline()
lineNo = 0
while line:
    line = cppF.readline()
    
    plusNo = line.count("+")
    minusNo = line.count("-")
    multNo = line.count("*")
    devNo = line.count("/")
    
    operators["+"] += plusNo
    operators["-"] += minusNo
    operators["*"] += multNo
    operators["/"] += devNo
    operators["sqrt"] += line.count("sqrt")
    operators["pow"] += line.count("pow")
    operators["exp"] += line.count("exp")
#    operators["double"] +=  line.count("double")
    lineNo += 1
print(key, lineNo)

functions2operations[key] = operators
cppF.close()

for func in functions2operations:
    print(func)
    print(functions2operations[func])
    total = 0
    for key in functions2operations[func]:
        total += functions2operations[func][key]
        
    print("total: ", total)
