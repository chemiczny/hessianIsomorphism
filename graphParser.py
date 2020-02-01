#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 20 10:34:48 2019

@author: michal
"""
import networkx as nx
import shlex
import matplotlib.pyplot as plt

from canonical import CanonicalSubformFactory, CanonicalForm
from canonical import addForms, multiplyForms, subtractForms, reverseFormSign

from variable import Variable
from parsingUtilities import isfloat

#import pickle

class GraphParser:
    def __init__(self, source = None, lastLine = None):
        self.name = None
        self.arguments = []
        
        self.scrLog = "graphParser.log"
        self.cleanLog()
        
        self.graph = nx.DiGraph()
        self.graph.add_node("Pi",  variable = "Pi", kind = "input", level = 0)
        self.constants = [ "Pi" ]
        
        self.inputs = {}
        self.outputs = {}
        
        self.variables2nodes = {}
        self.outputs2nodes = {}
        
        self.key2uniqueOperatorNodes = {}
        self.fastKey2canonicalKey = {}
        
        self.operators = { }
        
        self.maxOutputSize = -1
        self.generatedCanonicalLabels = 0
        
        self.printingMode = False
        self.nodeKeyByCanonicalForm = True
        self.deleteFormAfterUse = False
        
        self.subformFactory = CanonicalSubformFactory()
        
        if source and lastLine:
            self.read(source, lastLine)
            
    def cleanLog(self):
        logF = open(self.scrLog, 'w')
        logF.close()
        
    def log(self, data):
        logF = open(self.scrLog, 'a')
        logF.write(data+ "\n")        
        logF.close()
            
    def plotGraph(self):
        plt.figure()
        layout = nx.spring_layout(self.graph)
        nx.draw_networkx(self.graph, layout)
        
    def read(self, source, lastLine):
        lineS = lastLine.split("(")
        namePart = lineS[0]
        name = namePart.replace("void" , "")
        name = name.strip()
        self.name = name
        
        self.readArguments(source, lineS[1])
        self.readBody(source)
        
    def readArguments(self, source, additional= ""):
        if additional.strip():
            self.arguments += self.getArgsFromLine(additional)
        
        line = source.readline()
        
        while not ")" in line:
            self.arguments += self.getArgsFromLine(line)
            
            line = source.readline()
            
        self.arguments += self.getArgsFromLine(line)
        self.splitArguments()
            
    def getArgsFromLine(self, line):
        arguments = []
        
        for potArg in line.split(","):
            if not potArg.strip():
                continue
            
            potArg = potArg.replace(")","")
            
            potArgSplitted = potArg.split()
            name = potArgSplitted[-1]
            varType = " ".join( potArgSplitted[:-1] )
            print("nowy argument ", varType, name)
            arguments.append( Variable(name, varType) )
            
        return arguments
    
    def splitArguments(self):
        for arg in self.arguments:
            if arg.type == "double* const":
                self.outputs[arg.name] = arg
                print("Wykryto output: ", arg.name)
            else:
                self.inputs[arg.name] = arg
#                self.graph.add_node( arg.name)
                
    def outputInLine(self, line):
        if not line:
            return False
        
        temp = line.split("[")[0]
        varName = temp.strip()
            
        return varName in self.outputs
                
    def readBody(self, source):
        self.log("Reading function body start...")
        line = source.readline()
        
        expressionParsed = 0
        
        if not "{" in line:
            print("cannot find body begin")
        
        line = source.readline()
            
        while not "}" in line or "//" in line :
            beforeEq = ""
            afterEq = ""
            eq = ""
            
            if "+=" in line:
                lineS = line.split("+=")
                eq = "+="
            elif "=" in line:
                lineS = line.split("=")
                eq = "="
                
            beforeEq = lineS[0].strip()
            afterEq = lineS[1].strip()
        
            
            outputInLine = self.outputInLine(beforeEq)
            
            if not "//" in line and eq != "" and "double" in line and not outputInLine:

                expr = afterEq
                maxLines = 10
                lineId = 0
                while not ";" in expr and lineId < maxLines:
                    expr += source.readline()
                    lineId += 1
                    
                if not ";" in expr:
                    raise Exception("Invalid expression!")
                    
                expr = expr.replace(";", "")
                newVar = lineS[0]
                newVar = newVar.split()[-1]
                
                bottomNode = self.insertExpression2Graph(expr)
                if not bottomNode:
                    print(line)
                self.graph.nodes[bottomNode]["variable"] = newVar
                
                self.variables2nodes[newVar] = bottomNode
                
            elif outputInLine:
                expr = afterEq
                expr = expr.replace(";", "")
                newVar = beforeEq
                
                argNumber = int( newVar.split("[")[1].replace("]","") )
                self.maxOutputSize = max(self.maxOutputSize, argNumber)
                
                bottomNode = self.insertExpression2Graph(expr)
                if "variables" in self.graph.nodes[bottomNode]:
                    self.graph.nodes[bottomNode]["variables"].append(newVar)
                else:
                    self.graph.nodes[bottomNode]["variables"] = [ newVar ]
                    
                    
                self.graph.nodes[bottomNode]["eq"] = eq
                self.variables2nodes[newVar] = bottomNode
                
                self.outputs2nodes[newVar] = bottomNode
#                if "kind" in self.graph.nodes[bottomNode]:
#                    if self.graph.nodes[bottomNode]["kind"] == "output":
#                        print("o kurwa, ja pierdole")
                    
                    
                self.graph.nodes[bottomNode]["kind"] = "output"
            elif "[" in line:
                newVariable = line.split()[1]
                newVariable = newVariable.split("[")[0]
                
                self.inputs[newVariable] = Variable(newVariable, "double *")
                
            line = source.readline()
            expressionParsed += 1
            
            if expressionParsed % 500 == 0:
                self.log("Parsed "+str(expressionParsed)+ " expresions")
            
#        self.plotGraph()
#        print("zczytywanie skonczone")
#        self.writeFunctionFromGraph("dupa", "dupa")
#        print("sortowanie skonczone")
            
        print("stan operatorow: ")
        print(self.operators)
        self.log("Reading function body finished")
            
    def insertExpression2Graph(self, expr):
        exprSplit = list(shlex.shlex(expr))
        
        fixedExprList = []
        
        tokenIndex = 0
        tokenIndexLimit = len(exprSplit)
        
        tokenStack = [ [] ]
        statusStack = [ "low" ]
        tokenStackIndex = 0
        
        highOrderOperators = [ "*" , "/" ]
        lowOrderOperators = [ "+" , "-" ]
        
        while tokenIndex < tokenIndexLimit:
            token = exprSplit[tokenIndex]
            actualStatus = statusStack[ tokenStackIndex ]
            
            
            if token == "std":
                for i in range(4):
                    tokenIndex += 1
                    token += exprSplit[tokenIndex]
                    
                tokenStackIndex += 1
                statusStack.append("low")
                tokenStack.append([])
                
            elif token in self.inputs:
                inputType = self.inputs[token].type
                
                if "*" in inputType:
                    for i in range(3):
                        tokenIndex += 1
                        token += exprSplit[tokenIndex]
                        
            elif token == ".":                
                nextToken = exprSplit[tokenIndex+1]
                if isfloat(nextToken):
                    tokenIndex += 1
                    token += exprSplit[tokenIndex]
                    
                tokenStack[tokenStackIndex][-1] += token
                tokenIndex += 1
                continue
                    
            if token == "(":
                tokenStackIndex += 1
                statusStack.append("low")
                tokenStack.append([])
            elif token == ")":
                tokenStackIndex -= 1
                statusStack.pop()
                highLayer = tokenStack.pop()
                highLayer.append(token)
                
                if actualStatus == "high":
                    highLayer.append(")")
                
                highLayer = "".join(highLayer)
                
                tokenStack[tokenStackIndex].append( highLayer )
                tokenIndex += 1
                
#                print("kurwa ",tokenStack[tokenStackIndex] )
                continue
            
            elif token == ",":
                if actualStatus == "high":
                    tokenStack[tokenStackIndex].append(")")
                statusStack[tokenStackIndex] = "low"
                
                
            elif token in highOrderOperators:
                statusStack[tokenStackIndex] = "high"
                
                if actualStatus == "low":
                    lastVariable = tokenStack[tokenStackIndex].pop()
                    
                    tokenStack[tokenStackIndex].append("(")
                    tokenStack[tokenStackIndex].append(lastVariable)
                    
                
            elif token in lowOrderOperators:
                statusStack[tokenStackIndex] = "low"
                
                if actualStatus == "high":
                    tokenStack[tokenStackIndex].append(")")
            
                    
            tokenStack[tokenStackIndex].append(token)
            tokenIndex += 1
        
        fixedExprList = tokenStack[0]
        if statusStack[0] == "high":
            fixedExprList.append(")")
        finalExpr = "".join(fixedExprList)
#        print("Po dodaniu nawiasow")
        self.lastBrackets = finalExpr
        self.lastTokenStack = tokenStack
        exprSplit = list(shlex.shlex(finalExpr))
        
        fixedExprList = []
        
        tokenIndex = 0
        tokenIndexLimit = len(exprSplit)
        
#        print(fixedExprList)
        
        while tokenIndex < tokenIndexLimit:
            token = exprSplit[tokenIndex]
            actualStatus = statusStack[ tokenStackIndex ]
            
            
            if token == "std":
                for i in range(3):
                    tokenIndex += 1
                    token += exprSplit[tokenIndex]
                    
            elif token == ".":
                nextToken = exprSplit[tokenIndex+1]
                if isfloat(nextToken):
                    tokenIndex += 1
                    token += exprSplit[tokenIndex]
                    
                fixedExprList[-1] += token
                tokenIndex += 1
                continue
            
            tokenIndex += 1
            fixedExprList.append(token)
        
        return self.parseExpression(fixedExprList)
        
    def generateCanonicalForm(self, operator, inputs ):
        inputSet = set(inputs)
        
        for inp in inputSet:
            self.graph.nodes[inp]["generatedChildren"] += 1

        newCanonicalForm = self.graph.nodes[inputs[0]]["form"]
        if operator == "+":
            for inp in inputs[1:]:
#                newCanonicalForm.add( self.graph.nodes[inp]["form"] )
                newCanonicalForm = addForms( newCanonicalForm, self.graph.nodes[inp]["form"] )
        elif operator == "*":
            for inp in inputs[1:]:
#                newCanonicalForm.multiply( self.graph.nodes[inp]["form"] )
                newCanonicalForm = multiplyForms(newCanonicalForm, self.graph.nodes[inp]["form"] )
        elif operator == "-":
            if len(inputs) == 1:
#                newCanonicalForm.reverseSign()
                newCanonicalForm = reverseFormSign(newCanonicalForm)
            elif len(inputs) == 2:
#                newCanonicalForm.subtract(self.graph.nodes[inputs[1]]["form"])
                newCanonicalForm = subtractForms( newCanonicalForm, self.graph.nodes[inputs[1]]["form"])
            else:
                raise Exception("Substract operator with wrong number of arguments")
        else:
            raise Exception("Not supported operator for canonical labeling!")
            
        if self.deleteFormAfterUse:
            for inp in inputSet:
                childrenLen = len(list( self.graph.successors(inp) ))
                if childrenLen == 0:
                    continue
                
                childrenGenerated = self.graph.nodes[inp]["generatedChildren"]
                
                if childrenLen == childrenGenerated:
                    del self.graph.nodes[inp]["form"] 
                elif  childrenGenerated > childrenLen:
                    raise Exception("Generated more children than possible "+str(childrenGenerated) + " "+str(childrenLen))
        
        return newCanonicalForm
    
    def generateInpForms(self, operatorName, inputs):
        inputSet = set(inputs)
        
        for inp in inputSet:
            if "form" in self.graph.nodes[inp]:
                continue
            
            atomName = inp        
            newSubformKey = self.subformFactory.createSubform( atomName )
#            newSubform.atoms[newAtom.name] = newAtom
#            print("created subform: ", newSubformKey)
            newForm = CanonicalForm()
            newForm.subforms[ newSubformKey ] = 1
            
            self.graph.nodes[inp]["form"] = newForm
            self.graph.nodes[inp]["generatedChildren"] = 0
            self.graph.nodes[inp]["canonicalKey"] = newForm.generateKey()
            
#        keyList = [ "("+ self.graph.nodes[inp]["canonicalKey"] + ")" for inp in inputs ]
#        
#        if symmetric:
#            keyList.sort()
#            
#        return "_".join(keyList)+"_"+operatorName
        
    def insertNewOperator(self, operatorName, inputs, fix , forceNewNode = False, oldCanonicalForm = None):
#        print("Dodaje wierzcholek: ", operatorName, "wejscia", inputs)
        if not operatorName in self.operators:
            self.operators[operatorName] = -1           
            
        canonicalForm = None
        if self.nodeKeyByCanonicalForm and operatorName in [ "+", "*", "-" ] :
            self.generateInpForms(operatorName, inputs)
            if oldCanonicalForm:
                canonicalForm = oldCanonicalForm
                key = canonicalForm.generateKey()
#            elif not fastKey in self.fastKey2canonicalKey:
            else:
                canonicalForm = self.generateCanonicalForm(operatorName, inputs)
                key = canonicalForm.generateKey()
#            else:
#                key = self.fastKey2canonicalKey[fastKey]
        else:
            key = "_".join(sorted(inputs)) + "_"+operatorName
            
        if key in self.key2uniqueOperatorNodes and not forceNewNode:
            return self.key2uniqueOperatorNodes[key]
            
        inp2fold = {}
        level = 0
        
        for inp in inputs:
            level = max(level, self.graph.nodes[inp]["level"])
            if inp in inp2fold:
                inp2fold[inp] += 1
            else:
                inp2fold[inp] = 1
        
        level += 1
        self.operators[operatorName] += 1
        
        nodeName = operatorName + str( self.operators[operatorName] )
        self.key2uniqueOperatorNodes[key] = nodeName
        self.graph.add_node(nodeName, variable = None, kind = "middle", operator = operatorName, fix = fix, symmetric = True, level = level)
        
        if canonicalForm:
            self.graph.nodes[nodeName]["form"] = canonicalForm
            self.graph.nodes[nodeName]["canonicalKey"] = key
            self.graph.nodes[nodeName]["generatedChildren"] = 0
            self.generatedCanonicalLabels += 1
#            self.fastKey2canonicalKey[fastKey] = key
        
        for inp in inp2fold:
            if not inp in self.graph.nodes:
                raise Exception("No node in graph! "+str(inp))
            self.graph.add_edge(inp, nodeName, fold = inp2fold[inp] )
            
        return nodeName
    
    def insertNewAssimetricOperator(self, operatorName, inputs, fix, forceNewNode = False, oldCanonicalForm = None):
#        print("Dodaje wierzcholek: ", operatorName, "wejscia", inputs)
        if not operatorName in self.operators:
            self.operators[operatorName] = -1
            
        canonicalForm = None
        if self.nodeKeyByCanonicalForm and operatorName in [ "-" ] :
            self.generateInpForms(operatorName, inputs)
            if oldCanonicalForm:
                canonicalForm = oldCanonicalForm
                key = canonicalForm.generateKey()
#            elif not fastKey in self.fastKey2canonicalKey:
            else:
                canonicalForm = self.generateCanonicalForm(operatorName, inputs)
                key = canonicalForm.generateKey()
#            else:
#                key = self.fastKey2canonicalKey[fastKey]
        else:
            key = "_".join(sorted(inputs)) + "_"+operatorName
            
        if key in self.key2uniqueOperatorNodes and not forceNewNode:
            return self.key2uniqueOperatorNodes[key]
        
        level = 0
        
        for inp in inputs:
            level = max(level, self.graph.nodes[inp]["level"])
            
        level += 1
        self.operators[operatorName] += 1
        
        nodeName = operatorName + str( self.operators[operatorName] )
        self.key2uniqueOperatorNodes[key] = nodeName
        self.graph.add_node(nodeName, variable = None, kind = "middle", operator = operatorName, fix = fix, symmetric = False, level = level)
        
        if canonicalForm:
            self.graph.nodes[nodeName]["form"] = canonicalForm
            self.graph.nodes[nodeName]["canonicalKey"] = key
            self.graph.nodes[nodeName]["generatedChildren"] = 0
            self.generatedCanonicalLabels += 1
#            self.fastKey2canonicalKey[fastKey] = key
        
        onlyUnique = 0 == len(set(inputs))-len(inputs)
        
        if onlyUnique:
            for index, inp in enumerate(inputs):
                self.graph.add_edge(inp, nodeName, fold = 1, order = index )
        else:
            self.graph.add_edge(inputs[0], nodeName, fold = 2, order = 0 )
        
        return nodeName
    
    
    def changeNodeOperator(self, nodeName, newOperator, inputs, fix):
        self.graph.nodes[nodeName]["symmetric"] = False
        self.graph.nodes[nodeName]["operator"] = newOperator
        self.graph.nodes[nodeName]["fix"] = fix
        
        onlyUnique = 0 == len(set(inputs))-len(inputs)
        
        if onlyUnique:
            for index, inp in enumerate(inputs):
                self.graph.add_edge(inp, nodeName, fold = 1, order = index )
        else:
            self.graph.add_edge(inputs[0], nodeName, fold = 2, order = 0 )
        
    def parseExpression(self, exprSplit):
#        print("Parsuje wyrazenie: ","".join(exprSplit))
        tokenIndex = 0
        tokenLimit = len(exprSplit)
        currentNode = None
        
        while tokenIndex < tokenLimit:
            token = exprSplit[tokenIndex]
                
            if token == "-" and not currentNode:
                subExpr = self.getNextNode( exprSplit[tokenIndex+1:] )
                tokenIndex += len(subExpr)
                
                node = self.parseExpression( subExpr )
                    
                currentNode = self.insertNewOperator( token, [node] , "prefix" )
                
            elif token in [ "std::exp", "std::sqrt" ]:
                subExpr = self.getNextNode( exprSplit[tokenIndex+1:] )
                tokenIndex += len(subExpr)
                
                node = self.parseExpression( subExpr )
                    
                currentNode = self.insertNewOperator( token, [node] , "prefixBrackets" )
            elif token in ["std::pow"]:
                subExpr = self.getNextNode( exprSplit[tokenIndex+1:] )
                tokenIndex += len(subExpr)
                subExpr = subExpr[1:-1]
                
                part1, part2 = [], []
                comma = False
                
                for element in subExpr:
                    if element == ",":
                        comma = True
                    elif not comma:
                        part1.append(element)
                    else:
                        part2.append(element)
                        
                node1 = self.parseExpression( part1 )
                node2 = self.parseExpression( part2 )
                    
                currentNode = self.insertNewAssimetricOperator(token, [ node1, node2 ], "prefixBrackets")
                
            elif token in [  "+" , "*" ]:
                if not currentNode:
                    print("Two argument operator with only one argument! "+str(exprSplit))
                    raise Exception("Two argument operator with only one argument! "+str(exprSplit))
                    
                subExpr = self.getNextNode( exprSplit[tokenIndex+1:] )
                tokenIndex += len(subExpr)
                
                node = self.parseExpression( subExpr )
                    
                currentNode = self.insertNewOperator( token, [ currentNode, node] , "infix" )
                
                
            elif token in [ "-" , "/"]:
                if not currentNode:
                    print("Two argument operator with only one argument! "+str(exprSplit))
                    raise Exception("Two argument operator with only one argument! "+str(exprSplit))
                    
                subExpr = self.getNextNode( exprSplit[tokenIndex+1:] )
                tokenIndex += len(subExpr)
                
                node = self.parseExpression( subExpr )
                    
                currentNode = self.insertNewAssimetricOperator(token, [ currentNode, node ], "infix")
                    
            elif token in self.inputs:
                inputType = self.inputs[token].type
#                print(token)
                operator = ""
                if "*" in inputType:
                    for i in range(3):
                        tokenIndex += 1
                        operator += exprSplit[tokenIndex]
                        
                if not token in self.graph.nodes:
                    self.graph.add_node(token, variable = token, kind = "input", level = 0)
                    
                if operator:
                    currentNode = self.insertNewOperator( operator, [token] , "postfix" )
                else:
                    currentNode = token
                
            elif token in self.constants:
                currentNode = token
            elif token in self.variables2nodes:
                currentNode = self.variables2nodes[token]
            elif token == "(":
                subExpr = self.getNextNode( exprSplit[tokenIndex:] )
                tokenIndex += len(subExpr)-1
                subExpr = subExpr[1:-1]
                
                node = self.parseExpression( subExpr )
                    
                if not currentNode:
                    currentNode = node
                else:
                    print("No operator found! "+str(exprSplit))
                    raise Exception("No operator found! "+str(exprSplit))
                    
                    
            elif isfloat(token):
                currentNode = token
                if not token in self.graph.nodes:
                    self.graph.add_node(token, variable = token, kind = "input", level = 0)
            else:
                print("Unknown token! "+token + " in " + str(exprSplit))
                raise Exception("Unknown token! "+token + " in " + str(exprSplit))
                
            tokenIndex += 1
            
        return currentNode
            
    def getNextNode(self, exprList):
#        print("szukam kolejnego podwyrazenia: ", "".join(exprList))
        tokenIndex = 0
        tokenLimit = len(exprList)
        
        internalExpression = []
        bracketStack = []
        
        while tokenIndex < tokenLimit:
            token = exprList[tokenIndex]
            internalExpression.append(token)
            
#            tokenRecognized = False
            
            if token == "(":
                bracketStack.append("(")
            elif token == ")":
                if bracketStack[-1] == "(":
                    bracketStack.pop()
                else:
                    print("Brackets error!")
                    raise Exception("Brackets error!")
                
#            elif token in self.inputNames:
#                tokenRecognized = True
#            elif token in self.constants:
#                tokenRecognized = True
#            elif token in self.variables2nodes:
#                tokenRecognized = True
#            elif isfloat(token):
#                tokenRecognized = True
            elif token in [ "std::exp", "std::sqrt" , "std::pow", "-" ]:
                tokenIndex += 1
                continue
#            else:
#                raise Exception("Unknown token! "+token)
            elif token in self.inputs:
                inputType = self.inputs[token].type
#                print("input!!! ", inputType)
                if "*" in inputType:
#                    print("ogarniam")
                    for i in range(3):
                        tokenIndex += 1
                        token = exprList[tokenIndex]
                        internalExpression.append(token)
                
            if not bracketStack:
                break
            
            tokenIndex += 1
            
#        print("Znalezione podwyrazenie: ", "".join(internalExpression))
        return internalExpression
    
    def getNextOperatorAndNode(self, exprList):
        internalExpression = []
        nextToken = exprList[0]
        
        if not nextToken in [ "+", "*" , "-", "/" ]:
            print("No operator after variable")
            raise Exception("No operator after variable")
            
        internalExpression.append(nextToken)
        return internalExpression +  self.getNextNode( exprList[1:] )
    
    def writeFunctionFromGraph(self, functionName, file):
        nodes = nx.topological_sort(self.graph)
        
        file.write("void "+functionName+"(\n")
        
        for arg in self.arguments[:-1]:
            file.write( arg.type+" "+arg.name+" , \n" )
            
        lastArgument = self.arguments[-1]
        file.write(lastArgument.type +" "+ lastArgument.name+" ) \n")
        file.write("{\n")
        
        maxPrint = 100
        printed = 0
        constantIndex = 0
        for node in nodes:
            if not "kind" in self.graph.nodes[node]:
                print("nie ma rodzaju!", node)
                print(self.graph.nodes[node])
            
            if self.graph.nodes[node]["kind"] == "input":
                print("wejsciowy", node, self.graph.nodes[node])
                continue
            
            else:
                inputList = self.prepareInputList(self.graph, node)
                        
                fixType = self.graph.nodes[node]["fix"]
                
                if fixType == "prefix" and len(inputList) > 1:
                    raise Exception("One argument prefix operator with more arguments!")
                    
                nodeVariable = self.graph.nodes[node]["variable"]
                if not nodeVariable or "dupa" in str(nodeVariable):
                    self.graph.nodes[node]["variable"] = "dupa"+str(constantIndex)
                    constantIndex += 1
                    
                if self.graph.nodes[node]["kind"] == "middle":
                    file.write("    const double "+self.graph.nodes[node]["variable"]+" = ")
                elif self.graph.nodes[node]["kind"] == "output":
                    file.write("    "+self.graph.nodes[node]["variable"]+" += ")
                else:
                    raise Exception("Unknown kind of node!")
                
                operator = self.graph.nodes[node]["operator"]
                if fixType == "prefix":
                    file.write(operator+inputList[0])
                elif fixType == "prefixBrackets":
                    inputStr = " , ".join(inputList)
                    file.write(operator + "("+inputStr+")")
                elif fixType == "infix":
                    file.write(  operator.join( inputList ) )
                elif fixType == "postfix":
                    file.write(inputList[0]+operator)
                else:
                    raise Exception("Uknown operator type")
                    
                file.write(";\n")
                
                if self.printingMode and printed < maxPrint:
                    file.write('std::cout<<"'+self.graph.nodes[node]["variable"]+'"<<" "<<'+self.graph.nodes[node]["variable"]+"<<std::endl;\n")
                    printed+=1
                
                
        
        file.write("}\n")
            
    def rebuildVariableNames(self, sortedNodes):
        
        constantIndex = 0
        variables2reuse = []
        
        for node in sortedNodes:            
            if self.graph.nodes[node]["kind"] != "middle":
                continue
            
            nodeVariable = self.graph.nodes[node]["variable"]
            predecessorsNo = len(list(self.graph.predecessors( node)))
            
            if not variables2reuse or predecessorsNo == 1:
                self.graph.nodes[node]["newDefinition"] = True
                if not nodeVariable or "dupa" in str(nodeVariable):
                    self.graph.nodes[node]["variable"] = "dupa"+str(constantIndex)
                    constantIndex += 1
                    
            else:
                self.graph.nodes[node]["variable"] = variables2reuse.pop()
                self.graph.nodes[node]["newDefinition"] = False
                
            self.graph.nodes[node]["generatedChildren"] = 0
            
            parents = list(self.graph.predecessors( node))
            continue
        
            for parent in parents:
                if self.graph.nodes[parent]["kind"] != "middle":
                    continue
                
                parentChildren = list( self.graph.successors(parent ) )
                parentChildrenNo = len( parentChildren )
                firstFold = 0
                if parentChildren:
                    firstFold = self.graph[parent][parentChildren[0]]["fold"]
                
                if parentChildrenNo == 1 and firstFold == 1:
                    continue
                
                self.graph.nodes[parent]["generatedChildren"] += 1
               
                
                if parentChildrenNo == self.graph.nodes[parent]["generatedChildren"]:
                    variables2reuse.append( self.graph.nodes[parent]["variable"] )
            
            
            
            
    def writeFunctionFromGraphVariableReuse(self, functionName, file):
        nodes = list(nx.topological_sort(self.graph))
        
        self.rebuildVariableNames(nodes)
        
        file.write("void "+functionName+"(\n")
        
        for arg in self.arguments[:-1]:
            file.write( arg.type+" "+arg.name+" , \n" )
            
        lastArgument = self.arguments[-1]
        file.write(lastArgument.type +" "+ lastArgument.name+" ) \n")
        file.write("{\n")
        
        maxPrint = 100
        printed = 0
        constantResIndex = 0
        for node in nodes:
            if not "kind" in self.graph.nodes[node]:
                print("nie ma rodzaju!", node)
                print(self.graph.nodes[node])
            
            if self.graph.nodes[node]["kind"] == "input":
                print("wejsciowy", node, self.graph.nodes[node])
                continue
            
            else:
                inputList = self.prepareInputList(self.graph, node)
                        
                succesors = list(self.graph.successors( node))
                succesorsNo = len(succesors)
                firstFold = 0
                if succesors:
                    firstFold = self.graph[node][succesors[0]]["fold"]
                
                fixType = self.graph.nodes[node]["fix"]
                
                if fixType == "prefix" and len(inputList) > 1:
                    raise Exception("One argument prefix operator with more arguments!")
                    
                operator = self.graph.nodes[node]["operator"]
                command = ""
                if fixType == "prefix":
                    command = operator+inputList[0]
                elif fixType == "prefixBrackets":
                    inputStr = " , ".join(inputList)
                    command = operator + "("+inputStr+")"
                elif fixType == "infix":
                    command =  operator.join( inputList ) 
                elif fixType == "postfix":
                    command = inputList[0]+operator
                else:
                    raise Exception("Uknown operator type")
                    
                if succesorsNo != 1 or len(command) > 80 or firstFold != 1 or self.graph.nodes[node]["kind"] == "output":
                    if self.graph.nodes[node]["kind"] == "middle":
                        if self.graph.nodes[node]["newDefinition"]:
                            file.write("    double "+self.graph.nodes[node]["variable"]+" = "+ command + ";\n")
                        else:
                            file.write("    "+self.graph.nodes[node]["variable"]+" = " + command + ";\n")
                    elif self.graph.nodes[node]["kind"] == "output":
                        eqOp = self.graph.nodes[node]["eq"]
                        if len( self.graph.nodes[node]["variables"] ) == 1 and not "variable" in self.graph.nodes[node] :
                            file.write("    "+self.graph.nodes[node]["variables"][0]+" "+eqOp+" ")
                        else:
                            if not  self.graph.nodes[node]["variable"]:
                                newConstant = "res"+str(constantResIndex)
                            else:
                                newConstant =self.graph.nodes[node]["variable"]
                                
                            file.write("    const double "+newConstant+" = "+ command+";\n")
                            constantResIndex += 1
                            
                            for outputVar in self.graph.nodes[node]["variables"] :
                                file.write("    "+outputVar+" "+eqOp+" "+newConstant+";\n")
                    else:
                        raise Exception("Unknown kind of node!")  
                
#                    file.write(command)
#                    file.write(";\n")
                else:
                    self.graph.nodes[node]["variable"] = " ( " + command + " ) "
                
                if self.printingMode and printed < maxPrint and "C" in self.graph.nodes[node]["variable"]:
                    file.write('std::cout<<"'+self.graph.nodes[node]["variable"]+'"<<" "<<'+self.graph.nodes[node]["variable"]+"<<std::endl;\n")
                    printed+=1
                
                
        
        file.write("}\n")
    def rebuildGraph(self):
        self.log("Rebuild graph start...")
        oldGraph, self.graph = self.graph, nx.DiGraph()
#        oldVariables2nodes = deepcopy(self.variables2nodes)
        
        self.variables2nodes = {}
        self.key2uniqueOperatorNodes = {}
        self.operators = { }
        self.fastKey2canonicalKey = {}
        self.generatedCanonicalLabels = 0
        self.subformFactory.clean()
        
        nodes = list(nx.topological_sort(oldGraph))
        usedOldForms = 0
        for node in nodes:
            kind = oldGraph.nodes[node]["kind"]
            
            if kind == "input":
                self.graph.add_node(node, variable = oldGraph.nodes[node]["variable"] , kind = "input",  level = 0 )
            else:
                symmetry = oldGraph.nodes[node]["symmetric"]
                inputsList = self.prepareInputList(oldGraph, node)
                
                if "form" in oldGraph.nodes[node]:
                    usedOldForms += 1
                    if symmetry:
                        newNode = self.insertNewOperator( oldGraph.nodes[node]["operator"], 
                                                         inputsList , oldGraph.nodes[node]["fix"], False, oldGraph.nodes[node]["form"] )
                    else:
                        newNode = self.insertNewAssimetricOperator(oldGraph.nodes[node]["operator"], 
                                                                   inputsList, oldGraph.nodes[node]["fix"], False, oldGraph.nodes[node]["form"] )
                else:
                    if symmetry:
                        newNode = self.insertNewOperator( oldGraph.nodes[node]["operator"], 
                                                         inputsList , oldGraph.nodes[node]["fix"] )
                    else:
                        newNode = self.insertNewAssimetricOperator(oldGraph.nodes[node]["operator"], 
                                                                   inputsList, oldGraph.nodes[node]["fix"] )
                
                self.graph.nodes[newNode]["variable"] = oldGraph.nodes[node]["variable"]
                self.graph.nodes[newNode]["kind"] = oldGraph.nodes[node]["kind"]
                if "variables" in oldGraph.nodes[node]:
                    self.graph.nodes[newNode]["variables"] = oldGraph.nodes[node]["variables"]
                    
                if "eq" in oldGraph.nodes[node]:
                    self.graph.nodes[newNode]["eq"] = oldGraph.nodes[node]["eq"]
                    
                oldGraph.nodes[node]["variable"] = newNode
                
                if "form" in oldGraph.nodes[node]:
                    del oldGraph.nodes[node]["form"]
                
        print("Wykorzystano dotychczas wygenerowane formy: ", usedOldForms)
        print("stan operatorow: ")
        print(self.operators)
        self.log("Rebuild graph finished")
        
    def prepareInputList(self, graph, node):
        predecessors = list(graph.predecessors( node))
                
        order2predecessor = {}
        
        if not graph.nodes[node]["symmetric"]:
            for pred in predecessors:
                order2predecessor[ graph[pred][node]["order"] ] = pred
                    
        predecessor2fold = {}
        for pred in predecessors:
            predecessor2fold[ pred ] =  graph[pred][node]["fold"]
        
        inputList = []
        
        if order2predecessor:
            for order in sorted(list(order2predecessor.keys())):
                pred = order2predecessor[order]
                inputList += predecessor2fold[pred] * [ graph.nodes[pred]["variable"] ]
                
        else:
            for pred in predecessor2fold:
                inputList += predecessor2fold[pred] * [ graph.nodes[pred]["variable"]  ]
 
                
        return inputList