#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 11 15:58:16 2019

@author: michal
"""
from graphOptimizer import GraphOptimizer
#from isomorphCollection import IsomorphCollection
from itertools import combinations
import pickle
#import matplotlib.pyplot as plt
#from random import random

#import sys
    

class CppParser:
    def __init__(self, cppFile, variables2freeze = [], graphPickle = "test.pickle", frequentSubgraphPickle = "frequent.pickle"):
        self.cppFile = cppFile
        self.function = None
        self.graphPickle = graphPickle
        self.frequentSubgraphsPickle = frequentSubgraphPickle
        
        self.isomorphs = None
        self.variables2freeze = variables2freeze
        
    def parse(self ):        
        cppF = open(self.cppFile, 'r')
        
        line = cppF.readline()
        while not "void" in line:
            line = cppF.readline()
            
#            if "void" in line :
        newFunction = GraphOptimizer(cppF, line, self.variables2freeze)
        self.function = newFunction
        
        cppF.close()
#        newFunction.findClusterSubgraphs(acceptableOperators = [ "+", "-", "*", "/", None ], acceptableKinds = [ "middle"  ] )
#        newFunction.greedyScheme()
#        print("szukam klastrow ")
#        newFunction.findClusterSubgraphs(acceptableOperators = [ "*" ], acceptableKinds = [ "middle" ] )
#        newFunction.findClusterSubgraphs(acceptableOperators = [ "+" ], acceptableKinds = [ "middle" ] )
#        newFunction.findClusterSubgraphs(acceptableOperators = [ "+" , "*" ], acceptableKinds = [ "middle" ] )
#        newFunction.findClusterSubgraphs( )
#        newFunction.rebuildGraph()
#        newFunction.findClusters()
#        print("przebudowuje graf ", len(newFunction.graph.nodes))
#        newFunction.rebuildGraph()
#        print("Done ",len(newFunction.graph.nodes) )
#        newFunction.analysePools()
#        newFunction.findDeadEnds()
#        newFunction.rebuildGraph()
#        newFunction.greedySchemeSum()
#        newFunction.rebuildGraph()
#        newFunction.strongDivisionReduction = True
#        newFunction.findDeadEnds()
        
#        newFunction.rebuildGraph()
        
        #standard procedure start
        newFunction.rebuildGraph()
        newFunction.findDeadEnds()
        if len(newFunction.graph.nodes) < 300000:
            newFunction.strongDivisionReduction = True
            newFunction.rebuildGraph()
            newFunction.findDeadEnds()
#        newFunction.rebuildGraph()
        #standard procedure ends
        
        
#        newFunction.greedySchemeGlobal()
#        newFunction.greedySchemeSum()
#        newFunction.greedyScheme()

#        newFunction.dumpNodeFormData('+175op', "beforeRebuild.log")
#        newFunction.cleanForms()
        
#        newFunction.findDeadEnds()
#        newFunction.rebuildGraph()
#        newFunction.findAlternativePathProt()
#        newFunction.findClusterSubgraphs(acceptableOperators = [ "+", "-", "*", None ], acceptableKinds = [ "middle"  ] )
#        print("szukam slepych uliczek")
#        newFunction.findDeadEnds()
#        newFunction.rebuildGraph()
#        print("Analizuje nawiasy: ")
#        newFunction.simplifyBrackets()
#        newFunction.rebuildGraph()
#        newFunction.histogrameOfdevideInputs()
#        newFunction.dumplOutputCanonicalForm("canonicalOutputs.dat")
#        newFunction.findClusters()
#        newFunction.rebuildGraph()
#        newFunction.simplifyBrackets()
#        newFunction.rebuildGraph()
#        print("znowu szukam klastrów")
#        newFunction.findClusters()
#        newFunction.rebuildGraph()
#        newFunction.multiplyNodes()
#        newFunction.rebuildGraph()
#        newFunction.histogramOfSuccessors()
#        print("szukam klastrow ")
#        newFunction.findClusters()
#        print("przebudowuje graf ", len(newFunction.graph.nodes))
#        newFunction.rebuildGraph()
#        print("Done ",len(newFunction.graph.nodes) )
        
    def rewriteCppFile(self, destiny):
        if not self.function:
            return
        
        destinyFile = open(destiny, 'w')
        
        cppF = open(self.cppFile, 'r')
        
        line = cppF.readline()
        while not "void" in line:
            if '//#pragma GCC optimize ("O0")' in line:
                destinyFile.write('#pragma GCC optimize ("O0")\n')
            else:
                destinyFile.write(line)
                
            line = cppF.readline()
            
        cppF.close()
        
        function = self.function
        
        function.writeFunctionFromGraph( function.name , destinyFile)
        
        destinyFile.close()
        
    def writeTest(self, testFilename , variablesValues,  testCase = "prediction" ):
        if self.function == None:
            print("No function to test")
            return
        
        varNames = list(variablesValues.keys())
        for var1, var2 in combinations(varNames, 2):
            if var1 in var2 or var2 in var1:
                print("Variables overlapping!")
                print(var1, var2)
                return
        
        newFunction = self.function
        
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
            
        while not "}" in line:
            testFile.write(line)
            line = cppF.readline()
            
        testFile.write(line)
        cppF.close()
        
        newFunction.writeFunctionFromGraph( "dupa" , testFile )
#        newFunction.histogramOfLevels("+")
#        newFunction.histogramOfLevels("*")
#        newFunction.histogramOfLevels("/")
#        newFunction.histogramOfLevels("-")
#        newFunction.analyseSubGraphOverlaping()
#        arraysSize = str(newFunction.maxOutputSize+1)
#        print("najwiekszy wymiar tablicy wyjsciowej: ",newFunction.maxOutputSize+1)
        testFile.write("\n\nint main() { \n")
        
#        arraySize = "[27]"
        
        for varName in newFunction.inputs:
            if not varName in variablesValues:
                print("Missing variable!")
                print(varName)
            variableType = newFunction.inputs[varName].type
            if "double*" in variableType:
                testFile.write("\tdouble "+varName + "[] = "+str(variablesValues[varName]) + " ;\n"  )
            else:
                testFile.write("\t"+variableType+" "+varName + " = "+str(variablesValues[varName]) + " ;\n"  )

        testFile.write("\n")
        for varName in newFunction.outputs:
            maxIndex = 0
            for value in newFunction.outputIndexes[varName]:
                valueReplaced = value
                for varNam in variablesValues:
                    valueReplaced = valueReplaced.replace( varNam, str(variablesValues[varNam]) )
                integerValue = eval( valueReplaced)
                
                maxIndex = max(maxIndex, integerValue)
            arraySize =  str(maxIndex + 1)
            
            testFile.write("\tdouble " + varName + "_ref["+arraySize+"] = {0};\n" )
            testFile.write("\tdouble " + varName + "_2test["+arraySize+"] = {0};\n" )
            
        testFile.write("\n")
            
        referenceArgumentsList = []
        testArgumentsList = []
        
        for argument in newFunction.arguments:
            varName = argument.name
            if varName in newFunction.outputs:
                referenceArgumentsList.append( varName + "_ref" )
                testArgumentsList.append(varName + "_2test")
            else:
                referenceArgumentsList.append( varName )
                testArgumentsList.append(varName)
        
        if testCase == "prediction":
            
            testFile.write("\t"+newFunction.name+"("+" , ".join(referenceArgumentsList)+" );\n")
            testFile.write("\tdupa( "+ " , ".join(testArgumentsList) +" );\n\n")
            
            testFile.write("\tint testsFailed = 0;\n")
            testFile.write("\tint testsExecuted = 0;\n")
            testFile.write("\tint allValues = 0;\n")
            testFile.write("\tdouble diff;\n\n")
            for varName in newFunction.outputs:
                indexValues = []
                
                for value in newFunction.outputIndexes[varName]:
                    valueReplaced = value
                    for varNam in variablesValues:
                        valueReplaced = valueReplaced.replace( varNam, str(variablesValues[varNam]) )
                    
                    indexValues.append(str(eval( valueReplaced)))
                    
                testFile.write("\tint indexes_"+varName + "[] = {" + " , ".join(indexValues) + " };\n"  )
                testFile.write("\tallValues += "+str(len(indexValues))+";\n")
                testFile.write("\tfor ( int i = 0; i < "+str(len(indexValues))+"; i++) {\n")
                
                referenceVar = varName+"_ref[indexes_"+varName + "[i]]"
                testVar = varName+"_2test[indexes_"+varName + "[i]]"
                
                testFile.write("\t\tdiff = std::abs("+referenceVar + " - " + testVar + " );\n " )
                testFile.write("\t\tif ( std::abs("+referenceVar+") >  1e-8 ) {\n")
                testFile.write("\t\t\ttestsExecuted += 1;\n")
                testFile.write("\t\t\tif ( diff > 0.000001*std::abs("+referenceVar+")  ) { \n")
                testFile.write("\t\t\t\ttestsFailed += 1;\n")
                testFile.write('\t\t\t\tstd::cout<<"obtained vs reference"<<std::endl;\n')
                testFile.write('\t\t\t\tstd::cout<<'+testVar+'<<" "<<'+referenceVar+'<<std::endl;\n')
                testFile.write('\t\t\t\tstd::cout<<"'+varName+'"<<" "<<i<<std::endl;\n')
                testFile.write("\t\t}}\n")
                testFile.write("\t}\n\n")
                
            testFile.write("""
                std::cout<<"Values checked: "<<allValues<<" of: "<<allValues<<std::endl;
                std::cout<<"Tests failed: "<<testsFailed<<::std::endl;
                """)
        else:
            testFile.write("""
            const clock_t begin_old_time = clock();
            for( int i = 0; i < 1000000 ; i ++ )\n""")
            testFile.write("     "+newFunction.name+"("+" , ".join(referenceArgumentsList)+" );\n")
            testFile.write("""
            const clock_t old_time = clock() - begin_old_time;
            const clock_t begin_new_time = clock();
            for( int i = 0; i < 1000000 ; i ++ )\n""")
            testFile.write("     dupa( "+ " , ".join(testArgumentsList) +" );\n")
            testFile.write("""
            const clock_t new_time = clock() - begin_new_time;
            std::cout<<"stary czas: "<<old_time<<std::endl;
            std::cout<<"nowy  czas: "<<new_time<<std::endl;
            """)
        testFile.write("return 0;\n}\n")
        
        testFile.close()
        
    def saveGraphFunction(self):
        file2dump = open(self.graphPickle, 'wb')
        pickle.dump(self.function, file2dump)
        file2dump.close()
    
    def loadGraphFunction(self):
        infile = open(self.graphPickle,'rb')
        self.function = pickle.load(infile)
        infile.close()
        
#    def initSubgraphs(self, minSup):
#        self.isomorphs = IsomorphCollection(self.functions[0], minSup)
        
    def getOccurence(self):
        return self.isomorphs.getOccurence()
        
    def subgraphsGrowth(self):
        self.isomorphs.isomorphsGrowth()

    def replaceIsomorphWithFunction(self, isomorphKey, functionName):
        actualFunction = self.functions[0]
        for isomorph in self.isomorphs.isomorphs[isomorphKey]:
            allNodes = set(isomorph.selectedNodes)
            outputNodes = set(isomorph.outputNodes)
            inputNodes = set(isomorph.inputNodes)
            
            nodes2delete = allNodes - outputNodes
            nodes2delete -= inputNodes
            
            if len(outputNodes) > 1 :
                raise Exception("Inserting subgraph with more than one output is not yet implemented")
                
            actualFunction.graph.remove_nodes_from(nodes2delete)
            
            outputNode = isomorph.outputNodes[0]
            actualFunction.changeNodeOperator(outputNode, functionName, isomorph.inputNodes , "prefixBrackets" )
            
            
#        actualFunction.rebuildGraph()

if __name__ == "__main__":
#    testFile = "testData/short.cpp"
#    testFile = "testData/d2_ne_ss_AA.ey.cpp"
#    testFile = "testData/automateusz_cpp_backup_low_level_optimized_ey/d2_ee_pdpd_AB.ey.cpp"
    testFile = "testData/automateusz_cpp_backup_low_level_optimized_ey/d2_ee_psss_AC.ey.cpp"
#    testFile = "testData/overlapGradients/d_overlap10.ey.cpp"
#    testFile = "overlapGradientParsedForm/d_overlap10.ey.cpp"
#    testFile = "testData/d1_ee/d_ee_ddps_A4.ey.cpp"
#    testFile = "/home/michal/Projects/hessianIsomorphism/testData/gto_d1_kit/d_ee_dddd.ey.cpp"
#    testFile = "/home/michal/Projects/hessianIsomorphism/testData/vneGradients/d_ne_dd_A0.ey.cpp"
#    testFile = "/home/michal/Projects/niedoida/gto_d1_kit/src/d_ee_dddd_A3.ey.cpp"
#    testFile = "testData/d2_ee_ppps_AA.ey.cpp"
#    frozenVariables = set([ "xAB", "yAB", "zAB", "xCD", "yCD", "zCD" ])
#    frozenVariables = []
    frozenVariables = set([ "xAB", "yAB", "zAB", "xCD", "yCD", "zCD", "xP" , "yP", "zP", "xQ", "yQ", "zQ", "p", "q" ])
    cppParser = CppParser(testFile, variables2freeze=frozenVariables)
    cppParser.parse()
#    cppParser.saveGraphFunction()
#    cppParser.loadGraphFunction()
    varValues  = { "ae" : 1.1, "xA" : 1.1, "yA" : 3.3, "zA" : 1.6, "be" : 1.7,
                  "xB" : -0.9, "yB" : 0.3, "zB" : 0.6, "ce" : 1.3, "xC" : 1.4, 
                  "yC" : 1.8, "zC" : 1.2, "de" : 1.3, "xD" : -1.1, "yD" : 1.9, 
                  "zD" : 1.3, "bs" : "{ 0.7, 1.3, 1.5, 1.1, 0.8, 0.2, 0.15, 0.12, 0.1, 0.05}" }
    
#    varValues  = { "ae" : 1.1, "xAB" : 1.1, "yAB" : 3.3, "zAB" : 1.6, "be" : 1.7,
#                  "cc" : 1.3, "matrix_size" : 3, "Ai" : 0, "Bi" : 1}
    cppParser.writeTest("dupa.cpp", varValues, testCase="prediction")
#    cppParser.writeTest("dupa.cpp", testCase="performance")
    
    
    
#    test = Function()
#    test.arguments += test.getArgsFromLine(" const double* bs")
#    test.splitArguments()
#    print(test.inputs, test.inputs["bs"].type)
#    test.insertExpression2Graph( "1-3*2/Pi*(bs[0]+std::pow(5*(3+4)*3*3*3*4, 2))")
#    test.insertExpression2Graph( "1+3*2+std::sqrt(Pi)*((2+3)*3*9)")
#    test.insertExpression2Graph( "2*3*4*5+1")
#    print(test.getNextNode(["(", "2", ")"]))
#    test.plotGraph()