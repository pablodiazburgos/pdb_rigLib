"""
module to work with skin clusters
@category rigging @subcategory utils
@tags skinClusters weights utils
"""

import os
from string import atoi
from string import atof

import logging
_logger = logging.getLogger( __name__ )

import maya.cmds as mc
import maya.mel as mm
import pymel.core as pm

from . import name
from . import shape

def getRelated( shapeObj ):
    
    '''
    find related skinCluster if object is skinned
    
    :param shapeObj: str or list(str), shape or transform with shape or list with shapes from the same object
    :return: (str) skinCluster, if not found return None
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

def makeBipedStandardBindSet():
    
    """
    Creates a quick select set with the standard biped body bind joints
    """
    bodyBindJointsSelection = [
                        u'l_elbow1TwistPart1_jnt',
                        u'l_elbow1TwistPart2_jnt',
                        u'l_elbow1TwistPart3_jnt',
                        u'l_elbow1TwistPart4_jnt',
                        u'l_elbow1TwistPart5_jnt',
                        u'l_hip1TwistPart1_jnt',
                        u'l_hip1TwistPart2_jnt',
                        u'l_hip1TwistPart3_jnt',
                        u'l_hip1TwistPart4_jnt',
                        u'l_hip1TwistPart5_jnt',
                        u'l_knee1TwistPart1_jnt',
                        u'l_knee1TwistPart2_jnt',
                        u'l_knee1TwistPart3_jnt',
                        u'l_knee1TwistPart4_jnt',
                        u'l_knee1TwistPart5_jnt',
                        u'l_shoulder1TwistPart1_jnt',
                        u'l_shoulder1TwistPart2_jnt',
                        u'l_shoulder1TwistPart3_jnt',
                        u'l_shoulder1TwistPart4_jnt',
                        u'l_shoulder1TwistPart5_jnt',
                        u'r_elbow1TwistPart1_jnt',
                        u'r_elbow1TwistPart2_jnt',
                        u'r_elbow1TwistPart3_jnt',
                        u'r_elbow1TwistPart4_jnt',
                        u'r_elbow1TwistPart5_jnt',
                        u'r_hip1TwistPart1_jnt',
                        u'r_hip1TwistPart2_jnt',
                        u'r_hip1TwistPart3_jnt',
                        u'r_hip1TwistPart4_jnt',
                        u'r_hip1TwistPart5_jnt',
                        u'r_knee1TwistPart1_jnt',
                        u'r_knee1TwistPart2_jnt',
                        u'r_knee1TwistPart3_jnt',
                        u'r_knee1TwistPart4_jnt',
                        u'r_knee1TwistPart5_jnt',
                        u'r_shoulder1TwistPart1_jnt',
                        u'r_shoulder1TwistPart2_jnt',
                        u'r_shoulder1TwistPart3_jnt',
                        u'r_shoulder1TwistPart4_jnt',
                        u'r_shoulder1TwistPart5_jnt',
                        u'l_toes1_jnt',
                        u'l_foot1_jnt',
                        u'r_toes1_jnt',
                        u'r_foot1_jnt',
                        u'pelvis1_jnt',
                        u'head1_jnt',
                        u'jaw1_jnt',
                        u'neck3_jnt',
                        u'neck2_jnt',
                        u'neck1_jnt',
                        u'l_thumbFing3_jnt',
                        u'l_thumbFing2_jnt',
                        u'l_thumbFing1_jnt',
                        u'l_indexFing3_jnt',
                        u'l_indexFing2_jnt',
                        u'l_indexFing1_jnt',
                        u'l_indexFingBase1_jnt',
                        u'l_middleFing3_jnt',
                        u'l_middleFing2_jnt',
                        u'l_middleFing1_jnt',
                        u'l_ringFing3_jnt',
                        u'l_ringFing2_jnt',
                        u'l_ringFing1_jnt',
                        u'l_pinkyFing3_jnt',
                        u'l_pinkyFing2_jnt',
                        u'l_pinkyFing1_jnt',
                        u'l_middleFingBase1_jnt',
                        u'l_ringFingBase1_jnt',
                        u'l_pinkyFingBase1_jnt',
                        u'l_hand1_jnt',
                        u'r_thumbFing3_jnt',
                        u'r_thumbFing2_jnt',
                        u'r_thumbFing1_jnt',
                        u'r_indexFing3_jnt',
                        u'r_indexFing2_jnt',
                        u'r_indexFing1_jnt',
                        u'r_middleFing3_jnt',
                        u'r_middleFing2_jnt',
                        u'r_middleFing1_jnt',
                        u'r_ringFing3_jnt',
                        u'r_ringFing2_jnt',
                        u'r_ringFing1_jnt',
                        u'r_pinkyFing3_jnt',
                        u'r_pinkyFing2_jnt',
                        u'r_pinkyFing1_jnt',
                        u'r_pinkyFingBase1_jnt',
                        u'r_ringFingBase1_jnt',
                        u'r_indexFingBase1_jnt',
                        u'r_middleFingBase1_jnt',
                        u'r_hand1_jnt',
                        u'l_clavicle1_jnt',
                        u'r_clavicle1_jnt',
                        u'spine5_jnt',
                        u'spine4_jnt',
                        u'spine3_jnt',
                        u'spine2_jnt',
                        u'spine1_jnt'
                        ]
    
    # check if all the joints exists
    nonExistingJoints = [ jnt for jnt in bodyBindJointsSelection if not mc.objExists(jnt) ]
    
    if not nonExistingJoints:
        for jnt in nonExistingJoints:
            bodyBindJointsSelection.remove( jnt )
        
        print ( "# Non existing joints in the standard body bind joints:" )
        print ( '\n'.join( map( str, nonExistingJoints ) ) )
        
    # create bind select set
    mc.sets( bodyBindJointsSelection, n = 'bodyBindJoints_set' )
    print "# body bind joints set created successfully!"

def getMultipleRelated( tfmObj ):
    
    '''
    return skin clusters attached to given transform, if nothing found return None
    if more than one skin cluster found this will return the skin clusters in the 
    right order from top to bottom in the channel box
    '''
    
    tfmHistory = tfmObj.getShapes(noIntermediate = True)[0].listHistory(pruneDagObjects = True)
    skinClusters = [skc for skc in tfmHistory if skc.nodeType() == 'skinCluster']
    
    if not skinClusters:
        return None
    
    return skinClusters

def createParallelSkinCluster( tfmObj, skinClusterName, infJoints  ):
    
    '''
    Creates a skin cluster in parallel to given object switching the intermediate shape and once is created delete
    the non-needed shape keeping only one shapeOrig
    :param  tfmObj: PyNode, transform object to attach skin to
    :param skinClusterName: str, name of the skin clusters that is going to be created, if nothing passed create one by default
    :param infJoints: list( str ), influence joints of the skin cluster
    '''
    
    # create skin cluster name
    if not skinClusterName:
        skinClusterName = tfmObj.name() + '_skc'
        
    # create skin cluster, if already has one switch between intermediate object to create a new one
    skinClusters = getMultipleRelated( tfmObj )
    _logger.debug( 'related skin clusters: {}'.format( skinClusters ) )
    
    
    if not skinClusters:
        pm.skinCluster( tfmObj, infJoints, n = skinClusterName )
        return
   
    # switch intermediate shapes
    _logger.debug( 'Transform shapes: {}'.format( tfmObj.getShapes() ) )
    objShape = tfmObj.getShapes(noIntermediate = True)[0]
    objInter = tfmObj.getShapes(noIntermediate = False)[1]
    
    objInterName = objInter.name()
    
    objShape.intermediateObject.set(1)
    objInter.intermediateObject.set(0)
    
    # create parallel skc
    newSkc = pm.skinCluster( tfmObj, infJoints, n = skinClusterName )
    _logger.debug( 'created skin cluster: {}'.format( newSkc ) )
    
    # delete old shapeOri and switch back original shapes        
    objShape.intermediateObject.set(0)
    objInter.intermediateObject.set(1)
    
    _logger.debug( 'pre delete obj intermadiate: {}'.format( objInter ) )

    pm.delete( objInter )
    
    # rename new oriShape
    objInter = tfmObj.getShapes()[1] # intermediate shape
    objInter.rename( objInterName )
    
    # return the last created skin as first in deformation order
    for i in range( len( skinClusters ) ):
        pm.reorderDeformers( newSkc.name(), skinClusters[i].name(), objShape.name() )

def getJointMatrixIndex(skinnedJoint, skinClusterTarget):
    '''
    get the matrix input index in the skin cluster for passed joint
    :param skinnedJoint: PyNode('joint'), joint connected to the skin cluster
    :param skinClusterTarget: PyNode('skinCluster'), skin cluster node to look the input matrix connection
    :return index for the skin cluster matrix connection
    '''
    
    plugAttr = [ skinnedJoint.worldMatrix[0].outputs(plugs = True)[0] for output in skinnedJoint.worldMatrix[0].outputs() if output == skinClusterTarget ][0]
    
    if not plugAttr:
        return
    
    wmPlugIdx = plugAttr.split('[')[-1]
    wmPlugIdx = wmPlugIdx.split(']')[0]
    
    return int(wmPlugIdx)