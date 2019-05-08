#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 11 15:58:16 2019

@author: michal
"""
import networkx as nx
import shlex
import matplotlib.pyplot as plt


def isfloat(value):
  try:
    float(value)
    return True
  except ValueError:
    return False

class Variable:
    def __init__(self, name, varType):
        self.name = name
        self.type = varType

class Function:
    def __init__(self, source = None, lastLine = None):
        self.name = None
        self.arguments = []
        
        self.graph = nx.DiGraph()
        self.graph.add_node("Pi", nodeType = "input", variableName = "Pi")
        self.constants = [ "Pi" ]
        
        self.inputs = {}
        self.outputs = {}
        
        self.variables2nodes = {}
        
        self.operators = { }
        
        if source and lastLine:
            self.read(source, lastLine)
            
    def plotGraph(self):
        plt.figure()
        layout = nx.spring_layout(self.graph)
        nx.draw_networkx(self.graph, layout)
        
    def read(self, source, lastLine):
        name = lastLine.replace("void" , "")
        name = lastLine.replace("(", "")
        name = name.strip()
        self.name = name
        
        self.readArguments(source)
        self.readBody(source)
        
    def readArguments(self, source):
        line = source.readline()
        
        while not ")" in line:
            self.arguments += self.getArgsFromLine(line)
            
            line = source.readline()
            
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
            
            arguments.append( Variable(name, varType) )
            
        return arguments
    
    def splitArguments(self):
        for arg in self.arguments:
            if arg.type == "double* const":
                self.outputs[arg.name] = arg
            else:
                self.inputs[arg.name] = arg
#                self.graph.add_node( arg.name)
                
    def readBody(self, source):
        line = source.readline()
        
        if not "{" in line:
            print("cannot find body begin")
        
        line = source.readline()
            
        while not "}" in line or "//" in line:
            if not "//" in line:
#                print(line)
                lineS = line.split("=")
                expr = lineS[1]
                expr = expr.replace(";", "")
                newVar = lineS[0]
                
                bottomNode = self.insertExpression2Graph(expr)
                
            line = source.readline()
            
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
        print("Po dodaniu nawiasow")
        print(finalExpr)
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
            
            tokenIndex += 1
            fixedExprList.append(token)
        
        self.parseExpression(fixedExprList)
        
        
    def insertNewOperator(self, operatorName, inputs):
        print("Dodaje wierzcholek: ", operatorName, "wejscia", inputs)
        if not operatorName in self.operators:
            self.operators[operatorName] = -1
            
            
        inp2fold = {}
        
        for inp in inputs:
            if inp in inp2fold:
                inp2fold[inp] += 1
            else:
                inp2fold[inp] = 1
        
        self.operators[operatorName] += 1
        
        nodeName = operatorName + str( self.operators[operatorName] )
        
        for inp in inp2fold:
            self.graph.add_edge(inp, nodeName, fold = inp2fold[inp] )
            
        return nodeName
    
    def insertNewAssimetricOperator(self, operatorName, inputs):
        print("Dodaje wierzcholek: ", operatorName, "wejscia", inputs)
        if not operatorName in self.operators:
            self.operators[operatorName] = -1
            
        
        self.operators[operatorName] += 1
        
        nodeName = operatorName + str( self.operators[operatorName] )
        
        onlyUnique = 0 == len(set(inputs))-len(inputs)
        
        if onlyUnique:
            for index, inp in enumerate(inputs):
                self.graph.add_edge(inp, nodeName, fold = 1, order = index )
        
        else:
            self.graph.add_edge(inputs[0], nodeName, fold = 2, order = 0 )
        
            
        return nodeName
        
    def parseExpression(self, exprSplit):
        print("Parsuje wyrazenie: ","".join(exprSplit))
        tokenIndex = 0
        tokenLimit = len(exprSplit)
        currentNode = None
        
        while tokenIndex < tokenLimit:
            token = exprSplit[tokenIndex]
            
            if token == "-" and not currentNode:
                subExpr = self.getNextNode( exprSplit[tokenIndex+1:] )
                tokenIndex += len(subExpr)
                
                if not self.isAtom( subExpr ):
                    node = self.parseExpression( subExpr )
                else:
                    node = subExpr[0]
                    
                currentNode = self.insertNewOperator( token, [node] )
                
            elif token in [ "std::exp", "std::sqrt" ]:
                subExpr = self.getNextNode( exprSplit[tokenIndex+1:] )
                tokenIndex += len(subExpr)
                
                if not self.isAtom( subExpr ):
                    node = self.parseExpression( subExpr )
                else:
                    node = subExpr[0]
                    
                currentNode = self.insertNewOperator( token, [node] )
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
                        
                if not self.isAtom( part1 ):
                    node1 = self.parseExpression( part1 )
                else:
                    node1 = part1[0]
                    
                if not self.isAtom( part2 ):
                    node2 = self.parseExpression( part2 )
                else:
                    node2 = part2[0]
                    
                currentNode = self.insertNewAssimetricOperator(token, [ node1, node2 ])
                
            elif token in [  "+" , "*" ]:
                if not currentNode:
                    raise Exception("Two argument operator with only one argument! "+str(exprSplit))
                    
#                print("kurwa ", )
                subExpr = self.getNextNode( exprSplit[tokenIndex+1:] )
                tokenIndex += len(subExpr)
                
                if not self.isAtom( subExpr ):
                    node = self.parseExpression( subExpr )
                else:
                    node = subExpr[0]
                    
                currentNode = self.insertNewOperator( token, [ currentNode, node] )
                
                
            elif token in [ "-" , "/"]:
                if not currentNode:
                    raise Exception("Two argument operator with only one argument! "+str(exprSplit))
                    
                subExpr = self.getNextNode( exprSplit[tokenIndex+1:] )
                tokenIndex += len(subExpr)
                
                if not self.isAtom( subExpr ):
                    node = self.parseExpression( subExpr )
                else:
                    node = subExpr[0]
                    
                currentNode = self.insertNewAssimetricOperator(token, [ currentNode, node ])
                    
            elif token in self.inputs:
                inputType = self.inputs[token].type
                
                if "*" in inputType:
                    for i in range(3):
                        tokenIndex += 1
                        token += exprSplit[tokenIndex]
                currentNode = token
                
            elif token in self.constants:
                currentNode = token
            elif token in self.variables2nodes:
                currentNode = self.variables2nodes[token]
            elif token == "(":
                subExpr = self.getNextNode( exprSplit[tokenIndex:] )
                tokenIndex += len(subExpr)-1
                subExpr = subExpr[1:-1]
                
                if not self.isAtom( subExpr ):
                    node = self.parseExpression( subExpr )
                else:
                    node = subExpr[0]
                    
                if not currentNode:
                    currentNode = node
                else:
                    raise Exception("No operator found! "+str(exprSplit))
                    
            elif isfloat(token):
                currentNode = token
            else:
                raise Exception("Unknown token! "+token + " in " + str(exprSplit))
                
            tokenIndex += 1
            
        return currentNode
            
    def getNextNode(self, exprList):
        print("szukam kolejnego podwyrazenia: ", "".join(exprList))
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
            
        print("Znalezione podwyrazenie: ", "".join(internalExpression))
        return internalExpression
    
    def getNextOperatorAndNode(self, exprList):
        internalExpression = []
        nextToken = exprList[0]
        
        if not nextToken in [ "+", "*" , "-", "/" ]:
            raise Exception("No operator after variable")
            
        internalExpression.append(nextToken)
        return internalExpression +  self.getNextNode( exprList[1:] )
    
    def isAtom(self, exprList):
        return len(exprList) == 1
        

class CppParser:
    def __init__(self, cppFile):
        self.cppFile = cppFile
        self.functions = []
        
    def parse(self):
        cppF = open(self.cppFile, 'r')
        
        line = cppF.readline()
        while line:
            
            if "void" in line :
                newFunction = Function(cppF, line)
                self.functions.append(newFunction)
            
            line = cppF.readline()
        
        cppF.close()


if __name__ == "__main__":
    testFile = "testData/d2_ne_ss_AA.ey.cpp"
    
#    cppParser = CppParser(testFile)
#    cppParser.parse()
    
    test = Function()
    test.arguments += test.getArgsFromLine(" const double* bs")
    test.splitArguments()
    print(test.inputs, test.inputs["bs"].type)
    test.insertExpression2Graph( "1-3*2/Pi*(bs[0]+std::pow(5*(3+4)*3*3*3*4, 2))")
#    test.insertExpression2Graph( "1+3*2+std::sqrt(Pi)*((2+3)*3*9)")
#    test.insertExpression2Graph( "2*3*4*5+1")
#    print(test.getNextNode(["(", "2", ")"]))
    test.plotGraph()