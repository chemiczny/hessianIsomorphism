#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 11 15:58:16 2019

@author: michal
"""
import networkx as nx
import shlex
import matplotlib.pyplot as plt
#import sys

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
        self.graph.add_node("Pi",  variable = "Pi", kind = "input")
        self.constants = [ "Pi" ]
        
        self.inputs = {}
        self.outputs = {}
        
        self.variables2nodes = {}
        self.outputs2nodes = {}
        
        self.key2uniqueOperatorNodes = {}
        
        self.operators = { }
        
        if source and lastLine:
            self.read(source, lastLine)
            
    def plotGraph(self):
        plt.figure()
        layout = nx.spring_layout(self.graph)
        nx.draw_networkx(self.graph, layout)
        
    def read(self, source, lastLine):
        name = lastLine.replace("void" , "")
        name = name.replace("(", "")
        name = name.strip()
        self.name = name
        
        self.readArguments(source)
        self.readBody(source)
        
    def readArguments(self, source):
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
            else:
                self.inputs[arg.name] = arg
#                self.graph.add_node( arg.name)
                
    def readBody(self, source):
        line = source.readline()
        
        if not "{" in line:
            print("cannot find body begin")
        
        line = source.readline()
            
        while not "}" in line or "//" in line :
            if not "//" in line and "=" in line and "double" in line:
#                print(line)
                lineS = line.split("=")
                expr = lineS[1]
                expr = expr.replace(";", "")
                newVar = lineS[0]
                newVar = newVar.split()[-1]
                
                try:            
                    bottomNode = self.insertExpression2Graph(expr)
                    self.graph.nodes[bottomNode]["variable"] = newVar
                except:
                    print(line)
                    print(newVar)
                    print(bottomNode)
                    print("kurwa")
                    print(self.lastBrackets)
                    print(self.lastTokenStack)
                    return
                self.variables2nodes[newVar] = bottomNode
                
                if "[" in newVar and "]" in newVar:
                    self.outputs2nodes[newVar] = bottomNode
                    self.graph.nodes[bottomNode]["kind"] = "output"
            elif "+=" in line:
                lineS = line.split("+=")
                expr = lineS[1]
                expr = expr.replace(";", "")
                newVar = lineS[0]
                
                try:            
                    bottomNode = self.insertExpression2Graph(expr)
                    self.graph.nodes[bottomNode]["variable"] = newVar
                except:
                    print(line)
                    print(newVar)
                    print(bottomNode)
                    print("kurwa")
                    print(self.lastBrackets)
                    print(self.lastTokenStack)
                    return
                self.variables2nodes[newVar] = bottomNode
                
                self.outputs2nodes[newVar] = bottomNode
                self.graph.nodes[bottomNode]["kind"] = "output"
            elif "[" in line:
                newVariable = line.split()[1]
                newVariable = newVariable.split("[")[0]
                
                self.inputs[newVariable] = Variable(newVariable, "double *")
                
            line = source.readline()
            
#        self.plotGraph()
#        print("zczytywanie skonczone")
#        self.writeFunctionFromGraph("dupa", "dupa")
#        print("sortowanie skonczone")
            
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
        
        
    def insertNewOperator(self, operatorName, inputs, fix ):
#        print("Dodaje wierzcholek: ", operatorName, "wejscia", inputs)
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
        self.graph.add_node(nodeName, variable = None, kind = "middle", operator = operatorName, fix = fix, symmetric = True)
        
        for inp in inp2fold:
            self.graph.add_edge(inp, nodeName, fold = inp2fold[inp] )
            
        return nodeName
    
    def insertNewAssimetricOperator(self, operatorName, inputs, fix):
#        print("Dodaje wierzcholek: ", operatorName, "wejscia", inputs)
        if not operatorName in self.operators:
            self.operators[operatorName] = -1
            
        
        self.operators[operatorName] += 1
        
        nodeName = operatorName + str( self.operators[operatorName] )
        self.graph.add_node(nodeName, variable = None, kind = "middle", operator = operatorName, fix = fix, symmetric = False)
        
        onlyUnique = 0 == len(set(inputs))-len(inputs)
        
        if onlyUnique:
            for index, inp in enumerate(inputs):
                self.graph.add_edge(inp, nodeName, fold = 1, order = index )
        
        else:
            self.graph.add_edge(inputs[0], nodeName, fold = 2, order = 0 )
        
        return nodeName
        
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
                    self.graph.add_node(token, variable = token, kind = "input")
                    
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
                    self.graph.add_node(token, variable = token, kind = "input")
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
        
        constantIndex = 0
        for node in nodes:
            if not "kind" in self.graph.nodes[node]:
                print("nie ma rodzaju!", node)
                print(self.graph.nodes[node])
            
            if self.graph.nodes[node]["kind"] == "input":
                print("wejsciowy", node, self.graph.nodes[node])
                continue
            
            else:
                predecessors = list(self.graph.predecessors( node))
                
                order2predecessor = {}
                
                if not self.graph.nodes[node]["symmetric"]:
                    for pred in predecessors:
                            order2predecessor[ self.graph[pred][node]["order"] ] = pred
                            
                predecessor2fold = {}
                for pred in predecessors:
                    predecessor2fold[ pred ] =  self.graph[pred][node]["fold"]
                
                inputList = []
                
                if order2predecessor:
                    for order in sorted(list(order2predecessor.keys())):
                        pred = order2predecessor[order]
                        inputList += predecessor2fold[pred] * [ self.graph.nodes[pred]["variable"] ]
                        
                else:
                    for pred in predecessor2fold:
                        inputList += predecessor2fold[pred] * [ self.graph.nodes[pred]["variable"]  ]
                        
                fixType = self.graph.nodes[node]["fix"]
                
                if fixType == "prefix" and len(inputList) > 1:
                    raise Exception("One argument prefix operator with more arguments!")
                    
                if not self.graph.nodes[node]["variable"]:
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
                
                
        
        file.write("}\n")

class CppParser:
    def __init__(self, cppFile):
        self.cppFile = cppFile
        self.functions = []
        
    def parse(self, testFilename = "" ):
        
#        if testFilename:
        testFile = open(testFilename ,'w')
        
        testFile.write("#include <cmath>\n")
        testFile.write("#include <iostream>\n")
        testFile.write("#include <cstdlib>\n")
        testFile.write("namespace {\n")
        testFile.write("   const double Pi = M_PI;\n")
        testFile.write("} \n\n")
        
        cppF = open(self.cppFile, 'r')
        
        line = cppF.readline()
        while not "void" in line:
            line = cppF.readline()
            
#            if "void" in line :
        newFunction = Function(cppF, line)
        self.functions.append(newFunction)
        
        cppF.close()
        
        cppF = open(self.cppFile, 'r')
        
        line = cppF.readline()
        while not "void" in line:
            line = cppF.readline()
            
        while not "}" in line:
            testFile.write(line)
            line = cppF.readline()
            
        testFile.write(line)
        cppF.close()
        
        newFunction.writeFunctionFromGraph( "dupa" , testFile )
        
        testFile.write("\n\nint main() { \n")
        
#        arraySize = "[27]"
        testFile.write( '\tdouble ae = 1.1; \n')
        testFile.write( '\tdouble xA = 1.1;\n')
        testFile.write( '\tdouble yA = 2.3;\n')
        testFile.write( '\tdouble zA = 1.6;\n')
        testFile.write( '\tdouble be = 1.7;\n')
        testFile.write( '\tdouble xB = 0.1;\n')
        testFile.write( '\tdouble yB = 0.3;\n')
        testFile.write( '\tdouble zB = 0.6;\n')
        testFile.write( '\tdouble ce = 1.3;\n')
        testFile.write( '\tdouble xC = 1.4;\n')
        testFile.write( '\tdouble yC = 2.7;\n')
        testFile.write( '\tdouble zC = 1.2;\n')
        testFile.write( '\tdouble de = 1.5;\n')
        testFile.write( '\tdouble xD = 0.9;\n')
        testFile.write( '\tdouble yD = 2.2;\n')
        testFile.write( '\tdouble zD = 1.3;\n')
        testFile.write( '\tdouble bs[] = { 0.7, 1.3, 1.5, 1.1, 0.8, 0.2, 0.15, 0.12, 0.1, 0.05};\n')
        testFile.write( '\tdouble hxx[27] = {0};\n')
        testFile.write( '\tdouble hxy[27] = {0};\n')
        testFile.write( '\tdouble hxz[27] = {0};\n')
        testFile.write( '\tdouble hyx[27] = {0};\n')
        testFile.write( '\tdouble hyy[27] = {0};\n')
        testFile.write( '\tdouble hyz[27] = {0};\n')
        testFile.write( '\tdouble hzx[27] = {0};\n')
        testFile.write( '\tdouble hzy[27] = {0};\n')
        testFile.write( '\tdouble hzz[27] = {0};\n')
        
        testFile.write( '\tdouble hTestxx[27] = {0};\n')
        testFile.write( '\tdouble hTestxy[27] = {0};\n')
        testFile.write( '\tdouble hTestxz[27] = {0};\n')
        testFile.write( '\tdouble hTestyx[27] = {0};\n')
        testFile.write( '\tdouble hTestyy[27] = {0};\n')
        testFile.write( '\tdouble hTestyz[27] = {0};\n')
        testFile.write( '\tdouble hTestzx[27] = {0};\n')
        testFile.write( '\tdouble hTestzy[27] = {0};\n')
        testFile.write( '\tdouble hTestzz[27] = {0};\n')
        
        testFile.write(newFunction.name+"( ae, xA, yA, zA,be,  xB, yB, zB, ce, xC, yC, zC, de, xD, yD, zD, bs, hxx, hxy, hxz, hyx, hyy,hyz, hzx, hzy, hzz );\n")
        testFile.write("dupa( ae, xA, yA, zA,be,  xB, yB, zB, ce, xC, yC, zC, de, xD, yD, zD, bs, hTestxx, hTestxy, hTestxz, hTestyx, hTestyy,hTestyz, hTestzx, hTestzy, hTestzz );\n")
        
        testFile.write("""
        for ( int i = 0; i < 27; i++) {
          double diffxx = std::abs(hxx[i] - hTestxx[i]);
          double diffxy = std::abs(hxy[i] - hTestxy[i]);
          double diffxz = std::abs(hxz[i] - hTestxz[i]);
          
          double diffyx = std::abs(hyx[i] - hTestyx[i]);
          double diffyy = std::abs(hyy[i] - hTestyy[i]);
          double diffyz = std::abs(hyz[i] - hTestyz[i]);
          
          double diffzx = std::abs(hzx[i] - hTestzx[i]);
          double diffzy = std::abs(hzy[i] - hTestzy[i]);
          double diffzz = std::abs(hzz[i] - hTestzz[i]);
          
          if ( diffxx > 0.0001 )
            std::cout<<"ERROR XX !!! "<<hxx[i]<<" "<<hTestxx[i]<<std::endl;
          if ( diffxy > 0.0001 )
            std::cout<<"ERROR XY !!! "<<hxy[i]<<" "<<hTestxy[i]<<std::endl;
          if ( diffxz > 0.0001 )
            std::cout<<"ERROR XZ !!! "<<hxz[i]<<" "<<hTestxz[i]<<std::endl;
            
          if ( diffyx > 0.0001 )
            std::cout<<"ERROR YX !!! "<<hyz[i]<<" "<<hTestyx[i]<<std::endl;
          if ( diffyy > 0.0001 )
            std::cout<<"ERROR YY !!! "<<hyy[i]<<" "<<hTestyy[i]<<std::endl;
          if ( diffyz > 0.0001 )
            std::cout<<"ERROR YZ !!! "<<hyz[i]<<" "<<hTestyz[i]<<std::endl;
            
          if ( diffzx > 0.0001 )
            std::cout<<"ERROR ZX !!! "<<hzx[i]<<" "<<hTestzx[i]<<std::endl;
          if ( diffzy > 0.0001 )
            std::cout<<"ERROR ZY !!! "<<hzy[i]<<" "<<hTestzy[i]<<std::endl;
          if ( diffzz > 0.0001 )
            std::cout<<"ERROR ZZ !!! "<<hzz[i]<<" "<<hTestzz[i]<<std::endl;
          }                       
                       """)
        
        testFile.write("return 0;\n}\n")
        
        testFile.close()


if __name__ == "__main__":
#    testFile = "testData/short.cpp"
#    testFile = "testData/d2_ne_ss_AA.ey.cpp"
    testFile = "testData/d2_ee_ppps_AA.ey.cpp"
    
    cppParser = CppParser(testFile)
    cppParser.parse("dupa.cpp")
    
    
    
#    test = Function()
#    test.arguments += test.getArgsFromLine(" const double* bs")
#    test.splitArguments()
#    print(test.inputs, test.inputs["bs"].type)
#    test.insertExpression2Graph( "1-3*2/Pi*(bs[0]+std::pow(5*(3+4)*3*3*3*4, 2))")
#    test.insertExpression2Graph( "1+3*2+std::sqrt(Pi)*((2+3)*3*9)")
#    test.insertExpression2Graph( "2*3*4*5+1")
#    print(test.getNextNode(["(", "2", ")"]))
#    test.plotGraph()