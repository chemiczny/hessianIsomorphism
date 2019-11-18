#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 11 15:58:16 2019

@author: michal
"""
from graphOptimizer import GraphOptimizer
from isomorphCollection import IsomorphCollection

import pickle
#import matplotlib.pyplot as plt
#from random import random

#import sys
    

class CppParser:
    def __init__(self, cppFile, graphPickle = "test.pickle", frequentSubgraphPickle = "frequent.pickle"):
        self.cppFile = cppFile
        self.functions = []
        self.graphPickle = graphPickle
        self.frequentSubgraphsPickle = frequentSubgraphPickle
        
        self.isomorphs = None
        
    def parse(self ):        
        cppF = open(self.cppFile, 'r')
        
        line = cppF.readline()
        while not "void" in line:
            line = cppF.readline()
            
#            if "void" in line :
        newFunction = GraphOptimizer(cppF, line)
        self.functions.append(newFunction)
        
        cppF.close()
        
        print("szukam klastrow ")
        newFunction.findClusters()
        print("przebudowuje graf ", len(newFunction.graph.nodes))
        newFunction.rebuildGraph()
        print("Done ",len(newFunction.graph.nodes) )
#        newFunction.analysePools()
        
#        print("szukam slepych uliczek")
#        newFunction.findDeadEnds()
        
#        print("Analizuje nawiasy: ")
#        newFunction.simplifyBrackets()
#        newFunction.rebuildGraph()
#        newFunction.multiplyNodes()
#        newFunction.rebuildGraph()
#        newFunction.histogramOfSuccessors()
#        print("szukam klastrow ")
#        newFunction.findClusters()
#        print("przebudowuje graf ", len(newFunction.graph.nodes))
#        newFunction.rebuildGraph()
#        print("Done ",len(newFunction.graph.nodes) )
        
#        newFunction.printingMode = True
        
    def writeTest(self, testFilename , testCase = "prediction", reuseVariables = False ):
        if not self.functions:
            return
        
        newFunction = self.functions[0]
                
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
        
        if reuseVariables:
            newFunction.writeFunctionFromGraphVariableReuse("dupa", testFile)
        else:
            newFunction.writeFunctionFromGraph( "dupa" , testFile )
#        newFunction.histogramOfLevels("+")
#        newFunction.histogramOfLevels("*")
#        newFunction.histogramOfLevels("/")
#        newFunction.histogramOfLevels("-")
#        newFunction.analyseSubGraphOverlaping()
        arraysSize = str(newFunction.maxOutputSize+1)
        print("najwiekszy wymiar tablicy wyjsciowej: ",newFunction.maxOutputSize)
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
        testFile.write( '\tdouble hxx['+arraysSize+'] = {0};\n')
        testFile.write( '\tdouble hxy['+arraysSize+'] = {0};\n')
        testFile.write( '\tdouble hxz['+arraysSize+'] = {0};\n')
        testFile.write( '\tdouble hyx['+arraysSize+'] = {0};\n')
        testFile.write( '\tdouble hyy['+arraysSize+'] = {0};\n')
        testFile.write( '\tdouble hyz['+arraysSize+'] = {0};\n')
        testFile.write( '\tdouble hzx['+arraysSize+'] = {0};\n')
        testFile.write( '\tdouble hzy['+arraysSize+'] = {0};\n')
        testFile.write( '\tdouble hzz['+arraysSize+'] = {0};\n')
        
        testFile.write( '\tdouble hTestxx['+arraysSize+'] = {0};\n')
        testFile.write( '\tdouble hTestxy['+arraysSize+'] = {0};\n')
        testFile.write( '\tdouble hTestxz['+arraysSize+'] = {0};\n')
        testFile.write( '\tdouble hTestyx['+arraysSize+'] = {0};\n')
        testFile.write( '\tdouble hTestyy['+arraysSize+'] = {0};\n')
        testFile.write( '\tdouble hTestyz['+arraysSize+'] = {0};\n')
        testFile.write( '\tdouble hTestzx['+arraysSize+'] = {0};\n')
        testFile.write( '\tdouble hTestzy['+arraysSize+'] = {0};\n')
        testFile.write( '\tdouble hTestzz['+arraysSize+'] = {0};\n')
        
        if testCase == "prediction":
        
            testFile.write(newFunction.name+"( ae, xA, yA, zA,be,  xB, yB, zB, ce, xC, yC, zC, de, xD, yD, zD, bs, hxx, hxy, hxz, hyx, hyy,hyz, hzx, hzy, hzz );\n")
            testFile.write("dupa( ae, xA, yA, zA,be,  xB, yB, zB, ce, xC, yC, zC, de, xD, yD, zD, bs, hTestxx, hTestxy, hTestxz, hTestyx, hTestyy,hTestyz, hTestzx, hTestzy, hTestzz );\n")
            
            testFile.write("for ( int i = 0; i < "+arraysSize+"; i++) {\n")
            testFile.write("""
              double diffxx = std::abs(hxx[i] - hTestxx[i]);
              double diffxy = std::abs(hxy[i] - hTestxy[i]);
              double diffxz = std::abs(hxz[i] - hTestxz[i]);
              
              double diffyx = std::abs(hyx[i] - hTestyx[i]);
              double diffyy = std::abs(hyy[i] - hTestyy[i]);
              double diffyz = std::abs(hyz[i] - hTestyz[i]);
              
              double diffzx = std::abs(hzx[i] - hTestzx[i]);
              double diffzy = std::abs(hzy[i] - hTestzy[i]);
              double diffzz = std::abs(hzz[i] - hTestzz[i]);
              
              if ( diffxx > 0.00000001 )
                std::cout<<"ERROR XX !!! "<<hxx[i]<<" "<<hTestxx[i]<<std::endl;
              if ( diffxy > 0.00000001 )
                std::cout<<"ERROR XY !!! "<<hxy[i]<<" "<<hTestxy[i]<<std::endl;
              if ( diffxz > 0.00000001 )
                std::cout<<"ERROR XZ !!! "<<hxz[i]<<" "<<hTestxz[i]<<std::endl;
                
              if ( diffyx > 0.00000001 )
                std::cout<<"ERROR YX !!! "<<hyz[i]<<" "<<hTestyx[i]<<std::endl;
              if ( diffyy > 0.00000001 )
                std::cout<<"ERROR YY !!! "<<hyy[i]<<" "<<hTestyy[i]<<std::endl;
              if ( diffyz > 0.00000001 )
                std::cout<<"ERROR YZ !!! "<<hyz[i]<<" "<<hTestyz[i]<<std::endl;
                
              if ( diffzx > 0.00000001 )
                std::cout<<"ERROR ZX !!! "<<hzx[i]<<" "<<hTestzx[i]<<std::endl;
              if ( diffzy > 0.00000001 )
                std::cout<<"ERROR ZY !!! "<<hzy[i]<<" "<<hTestzy[i]<<std::endl;
              if ( diffzz > 0.00000001 )
                std::cout<<"ERROR ZZ !!! "<<hzz[i]<<" "<<hTestzz[i]<<std::endl;
              }                       
                           """)
        else:
            testFile.write("""
            const clock_t begin_old_time = clock();
            for( int i = 0; i < 10000 ; i ++ )\n""")
            testFile.write("     "+newFunction.name+"( ae, xA, yA, zA,be,  xB, yB, zB, ce, xC, yC, zC, de, xD, yD, zD, bs, hxx, hxy, hxz, hyx, hyy,hyz, hzx, hzy, hzz );\n")
            testFile.write("""
            const clock_t old_time = clock() - begin_old_time;
            const clock_t begin_new_time = clock();
            for( int i = 0; i < 10000 ; i ++ )\n""")
            testFile.write("     dupa( ae, xA, yA, zA,be,  xB, yB, zB, ce, xC, yC, zC, de, xD, yD, zD, bs, hTestxx, hTestxy, hTestxz, hTestyx, hTestyy,hTestyz, hTestzx, hTestzy, hTestzz );\n")
            testFile.write("""
            const clock_t new_time = clock() - begin_new_time;
            std::cout<<old_time<<" "<<new_time<<std::endl;
            """)
        testFile.write("return 0;\n}\n")
        
        testFile.close()
        
    def saveGraphFunction(self):
        file2dump = open(self.graphPickle, 'wb')
        pickle.dump(self.functions, file2dump)
        file2dump.close()
    
    def loadGraphFunction(self):
        infile = open(self.graphPickle,'rb')
        self.functions = pickle.load(infile)
        infile.close()
        
    def initSubgraphs(self, minSup):
        self.isomorphs = IsomorphCollection(self.functions[0], minSup)
        
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
    testFile = "testData/automateusz_cpp_backup_low_level_optimized_ey/d2_ee_ppps_AA.ey.cpp"
#    testFile = "testData/d2_ee_ppps_AA.ey.cpp"
    
    cppParser = CppParser(testFile)
    cppParser.parse()
#    cppParser.saveGraphFunction("test.pickle")
#    cppParser.loadGraphFunction()
    cppParser.writeTest("dupa.cpp", testCase="performance", reuseVariables=False)
    
    
    
#    test = Function()
#    test.arguments += test.getArgsFromLine(" const double* bs")
#    test.splitArguments()
#    print(test.inputs, test.inputs["bs"].type)
#    test.insertExpression2Graph( "1-3*2/Pi*(bs[0]+std::pow(5*(3+4)*3*3*3*4, 2))")
#    test.insertExpression2Graph( "1+3*2+std::sqrt(Pi)*((2+3)*3*9)")
#    test.insertExpression2Graph( "2*3*4*5+1")
#    print(test.getNextNode(["(", "2", ")"]))
#    test.plotGraph()