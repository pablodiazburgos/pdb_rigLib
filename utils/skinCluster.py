"""
module to work with skin clusters
@category rigging @subcategory utils
@tags skinClusters weights utils
"""

import os
from string import atoi
from string import atof

import maya.cmds as mc
import maya.mel as mm

from . import name
from . import shape

def getRelated( shapeObj ):
    
    '''
    find related skinCluster if object is skinned
    
    @param shapeObj: str or list(str), shape or transform with shape or list with shapes from the same object
    @return: (str) skinCluster, if not found return None
    '''
    
    # get object shapes in case there was transform
    objShapes = shape.getShape( shapeObj, useLongName = True, noIntermediate = True )
    
    historyRes = mc.listHistory( objShapes, pruneDagObjects = True )
    sClusters = mc.ls( historyRes, type = 'skinCluster' )
        
    if sClusters:
        
        return sClusters[0]
    

def makeSkinClusterAddInfluences( shapeObj, influences, verbose = False, useCompInfluences = True ):
    
    '''
    make skinCluster if needed and add multiple influences supporting both transform and component types
    
    @param shapeObj: shape object to be skinned
    @type shapeObj: str
    @param influences: list of influences to be added to skinCluster
    @type influences: str
    @param verbose: if True then function will print information about its progress
    @type verbose: bool
    @param useCompInfluences: use component influences, otherwise treat all influences like transform
    @type useCompInfluences: bool
    @return: list( str, list, bool ), 0- name of skinCluster deformer node, 1- list with all influences in skinCluster, 2- created skinCluster
    '''
    
    # detect if there is a skinCluster on shape object
    
    skincldef = getRelated( shapeObj )
    createdSkinCluster = False
    
    if not skincldef or not mc.objExists( skincldef ):
        
        createdSkinCluster = True
    
    # create skinCluster using initial joint found in influences list
    
    if createdSkinCluster:
        
        jointInf = [ f for f in influences if mc.nodeType( f ) == 'joint' ][0]
        
        # make skinCluster name and remove namespaces (invalid Maya name)
        scName = name.removeNamespace( shapeObj ) + '_skc'
        
        skincldef = mc.skinCluster( jointInf, shapeObj, tsb = 1, n = scName, weightDistribution = 1 )[0]
        
        # make sure skinCluster will not have few maximum influences and maintain will be turned off
        mc.setAttr( skincldef + '.maintainMaxInfluences', 0, l = 1 )
    
    # turn off skinCluster envelope before adding influences
    # to minimize evaluations
    
    try: mc.setAttr( skincldef + '.en', 0 )
    except: pass
    
    # add skin cluster influences if skinCluster had to be created
    
    if createdSkinCluster:
    
        addInfs = influences[:]
        addInfs.remove( jointInf )
        
        addInfluences( skincldef, addInfs, verbose = verbose, useCompInfluences = useCompInfluences )
    
    # get list of influences
    
    scInfluences = mc.listConnections( skincldef + '.matrix' )
    
    # add missing influences if skinCluster existed
    
    missingInfluenceList = [ inf for inf in influences if inf not in scInfluences ]
    
    if len( missingInfluenceList ):
        
        addInfluences( skincldef, missingInfluenceList, verbose = verbose, useCompInfluences = useCompInfluences )
        
        # update list of influences
        scInfluences = mc.listConnections( skincldef + '.matrix' )
    
    # turn skinCluster node back on
    
    try: mc.setAttr( skincldef + '.en', 1 )
    except: pass
    
    
    return [ skincldef, scInfluences, createdSkinCluster ]

