"""
Module with some functions for iclone rig creation
"""

import maya.cmds as mc
import maya.OpenMaya as om

from ..utils import shape
from ..utils import skinCluster
from ..utils import joint
from ..utils import vector

from pdb_rigLib.tools import saveSkinWeights
from pdb_rigLib.tools import bSkinSaver
from pdb_rigLib.tools import poleVector
from pdb_rigLib.tools import footRigLocators
from __builtin__ import True

# define components path
assetModelFilePath = '%smodel/%s_model.ma'
assetBuilderFilePath = '%sbuilder/%s_builder.ma'
skinWeightsFilePath = '%sweights/skinCluster/'
assetControlShapesPath = '%scontrolShapes/%s_controlShapes.xml'


# define scene scale
sceneScale = 1.0

# define main joints
rootJnt = 'root1_jnt'
headJnt = 'head1_jnt'

boneRootJntName = 'boneRoot1_jnt'

bodyAssetGeo = 'C_head_00__MSH'  # this should be the name of the main body geo

# ========================================================
# define scene object names
# ========================================================
    
deformSetupGrp = 'deformSetup_grp'
buildObjectsGrp = 'build_objects_grp'
buildSkeletonGrp = 'build_skeleton_grp'

hipJnt = 'hip1_jnt'
kneeJnt = 'knee1_jnt'
ankleJnt = 'foot1_jnt'
toeJnt = 'toes1_jnt'
endToeJnt = 'toes2_jnt'

pelvisJnt = 'pelvis1_jnt'
pelvisEndJnt = 'pelvis2_jnt'

spineStartJnt = 'spine1_jnt'
spineEndJnt = 'spine4_jnt'

neckJnt = 'neck1_jnt'
headJnt = 'head1_jnt'
headEndJnt = 'head2_jnt'

clavicleJnt = 'clavicle1_jnt'
shldrJnt = 'shoulder1_jnt'
elbowJnt = 'elbow1_jnt'
handJnt = 'hand1_jnt'
middleFingJnt = 'middleFing1_jnt'

def prepareModel( assetName, assetFolder, modelSource = 'CC', verbose = False ):
    '''
    fuction to rename joints and export weights and model/blendshapes to corresponding folders and delete model/blendshapes from current scene 
    :param assetName: str, name of the asset we are working on
    :param assetFolder: str, asset folder directory to save multiple stuffs
    :param modelSource: str, source file to be rigged... current only work for 'CC'(character creator) and 'RP6'(iclone resource pack 6)
    :param verbose: bool, print different items while is creating the rig( usually good for debug )
    :return None
    '''
    
    # fix joint names in order to export weights is proper names
    # check supported modelSource
    supportTypes = { 'CC': _CCFixJointNames, 'RP6': _RP6FixJointNames }
    
    if not modelSource in supportTypes.keys():
        om.MGlobal_displayError(" '{}' is not a valid model source type ". format( modelSource ) )
        return
    # run fix name based of modelSource
    supportTypes[modelSource](verbose = verbose)
    
    # fix clashing names on all tope nodes
    topTransformNodes = mc.ls('|*', type = 'transform')
    
    for topNode in topTransformNodes:
        try:
            shape.fixShapesName(topNode)
        except:
            pass
    
    shapesNodes = [ mc.listRelatives( geo, s = True )[0] for geo in topTransformNodes if mc.listRelatives( geo, s = True ) ]
    allTopMesh = [ mc.listRelatives(shp, p = True)[0] for shp in shapesNodes if 'mesh' in mc.nodeType( shp ) ]
    
    # save skin clusters
    for mesh in allTopMesh:
        skinNode = skinCluster.getRelated( mesh )
        if skinNode:
            mc.setAttr( '{}.skinningMethod'.format( skinNode ), 0 )
            saveSkinClusterWeights( assetName, assetFolder, [mesh] )
    
    # delete history and group in in blendshape or asset model groups based on visibility   
    
    blendshapeGeo = [ geo for geo in allTopMesh if not mc.getAttr( '{}.v'.format(geo) ) ]
    skinnedGeo = [ geo for geo in allTopMesh if mc.getAttr( '{}.v'.format(geo) ) ]
    
    for geo in allTopMesh:
        mc.delete( geo, ch = True )
    
    print '# all top node geo history was deleted!'
    
    assetGeoGrp = mc.group( em = True, n = '{}_grp'.format( assetName ) )
    blsGrp = mc.group(em = True, p = assetGeoGrp, n = 'blendshapes_grp')
    
    # if there is some blendshapes group it an parent it
    if len( blendshapeGeo ) > 0: 
        mc.parent( blendshapeGeo, blsGrp )
        
        #mc.setAttr( '{}.rx'.format( blsGrp ), -90 )
        #mc.makeIdentity(blsGrp, apply = True, r = True, pn = True )
        
    mc.parent( skinnedGeo, assetGeoGrp )
    
    # delete all the scene keys
    allTransformNodes = mc.ls(tr = True, type = 'joint')
    for trans in allTransformNodes:
        mc.cutKey(trans)
        
    # delete selection sets
    setsList = mc.ls(et = 'objectSet')
    setsList.remove('defaultLightSet')
    setsList.remove('defaultObjectSet')
    for set in setsList:
        mc.delete( set )
    
    # export asset grp to model folder and delete it from current scene 
    exportModelPath = assetModelFilePath % ( assetFolder, assetName )
    
    mc.select( assetGeoGrp )
    mc.file( exportModelPath, f = True, type = 'mayaAscii', es = True )
    
    print '# "{}_grp" exported to {}'.format( assetName, exportModelPath )
    
    mc.delete( assetGeoGrp )
    
def saveSkinClusterWeights( assetName, assetFolder, skinnedObjs = None ):
    
    """
    save skinCluster weights for the rig
    """
    
    if not skinnedObjs:
        
        return
    
    skinPath = skinWeightsFilePath % assetFolder
    
    for geo in skinnedObjs:
        
        mc.select(geo)
        
        fullSkinPath = skinPath + geo + '.skinwt'
        
        bSkinSaver.bSaveSkinValues(fullSkinPath)
        
        print "for: %s \n" % geo
    
    mc.select(cl = True)
    
def _RP6FixJointNames( verbose ):
    '''
    :param verbose: bool, print some object for debug 
    :return None
    '''
    
    # there is a clashing with "Hair"... rename joint to avoid this
    
    if len( mc.ls( 'Hair' ) ) > 1:
        hairJnt = mc.ls( 'Hair', type = 'joint' )[0]
        if hairJnt:
            mc.rename( hairJnt, 'hair1_jnt' )
        
    
    topJnt = 'BoneRoot'
    
    allJntsList = mc.listRelatives( topJnt, ad = True )
    
    for j in allJntsList:
        
        # remove 'G6Beta prefix and lower the names'
        
        if j.startswith( 'G6Beta_' ):
            
            newName = j.replace( 'G6Beta_', '' )
            newNameLower = newName.lower()
            newJnt = mc.rename( j, newNameLower )
    # fix l_middle03nub no match name convention
    mc.rename( 'l_middle03nub', 'l_middlenub' )
    
    # rename dictionary
    fixedNamesDic = {
                    'hips': 'root1_jnt',
                    'pelvis': 'pelvis1_jnt',
                    'spine01': 'spine2_jnt',
                    'spine02': 'spine3_jnt',
                    'spine03': 'spine4_jnt',
                    'neck': 'neck1_jnt',
                    'head': 'head1_jnt',
                    'headnub': 'head2_jnt',
                    'facejawroot': 'jaw1_jnt',
                    'l_pinky01': 'l_pinkyFing1_jnt',
                    'l_pinky02': 'l_pinkyFing2_jnt',
                    'l_pinky03': 'l_pinkyFing3_jnt',
                    'l_pinkynub': 'l_pinkyFing4_jnt',
                    'rpinky01': 'r_pinkyFing1_jnt',
                    'rpinky02': 'r_pinkyFing2_jnt',
                    'rpinky03': 'r_pinkyFing3_jnt',
                    'rpinkynub': 'r_pinkyFindg4_jnt'
                    }
       
    # add side items to fixedNamesDic
    for side in ['l_', 'r_']:
        
        # legs
        fixedNamesDic['{}thigh'.format( side )] = '{}hip1_jnt'.format( side )
        fixedNamesDic['{}calf'.format( side )] = '{}knee1_jnt'.format( side )
        fixedNamesDic['{}foot'.format( side )] = '{}foot1_jnt'.format( side )
        fixedNamesDic['{}toe'.format( side )] = '{}toes1_jnt'.format( side )
        fixedNamesDic['{}toe0nub'.format( side )] = '{}toes2_jnt'.format( side )
        
        # arms
        fixedNamesDic['{}clavicle'.format( side )] = '{}clavicle1_jnt'.format( side )
        fixedNamesDic['{}upperarm'.format( side )] = '{}shoulder1_jnt'.format( side )
        fixedNamesDic['{}forearm'.format( side )] = '{}elbow1_jnt'.format( side )
        fixedNamesDic['{}hand'.format( side )] = '{}hand1_jnt'.format( side )
        
        # fingers
        fixedNamesDic['{}thumb01'.format( side )] = '{}thumbFing1_jnt'.format( side )
        fixedNamesDic['{}thumb02'.format( side )] = '{}thumbFing2_jnt'.format( side )
        fixedNamesDic['{}thumb03'.format( side )] = '{}thumbFing3_jnt'.format( side )
        fixedNamesDic['{}thumbnub'.format( side )] = '{}thumbFing4_jnt'.format( side )
        
        fixedNamesDic['{}inde01'.format( side )] = '{}indexFing1_jnt'.format( side )
        fixedNamesDic['{}inde02'.format( side )] = '{}indexFing2_jnt'.format( side )
        fixedNamesDic['{}inde03'.format( side )] = '{}indexFing3_jnt'.format( side )
        fixedNamesDic['{}indenub'.format( side )] = '{}indexFing4_jnt'.format( side )

        fixedNamesDic['{}middle01'.format( side )] = '{}middleFing1_jnt'.format( side )
        fixedNamesDic['{}middle02'.format( side )] = '{}middleFing2_jnt'.format( side )
        fixedNamesDic['{}middle03'.format( side )] = '{}middleFing3_jnt'.format( side )
        fixedNamesDic['{}middlenub'.format( side )] = '{}middleFing4_jnt'.format( side )        
        
        fixedNamesDic['{}ring01'.format( side )] = '{}ringFing1_jnt'.format( side )
        fixedNamesDic['{}ring02'.format( side )] = '{}ringFing2_jnt'.format( side )
        fixedNamesDic['{}ring03'.format( side )] = '{}ringFing3_jnt'.format( side )
        fixedNamesDic['{}ringnub'.format( side )] = '{}ringFing4_jnt'.format( side )
        
    # rename based on dictionary
    for k, v in fixedNamesDic.items():
        if verbose:
            print 'k:', k
            print 'v:', v
        mc.rename( k, v )

def _CCFixJointNames( verbose ):
    '''
    :param verbose: bool, print some object for debug 
    :return None
    '''
    topJnt = 'CC_Base_BoneRoot'
    
    allJntsList = mc.listRelatives( topJnt, ad = True )
    
    #rename top bone
    mc.rename( topJnt, boneRootJntName )
    
    for j in allJntsList:
        
        # remove 'CC_Base prefix and lower the names'
        
        if j.startswith( 'CC_Base_' ):
            
            newName = j.replace( 'CC_Base_', '' )
            newNameLower = newName.lower()
            newJnt = mc.rename( j, newNameLower )
    
    # rename dictionary
    fixedNamesDic = {
                    'hip': 'root1_jnt',
                    'pelvis': 'pelvis1_jnt',
                    'waist': 'spine2_jnt',
                    'spine01': 'spine3_jnt',
                    'spine02': 'spine4_jnt',
                    'necktwist01': 'neck1_jnt',
                    'necktwist02': 'neck2_jnt', 
                    'head': 'head1_jnt',
                    'jawroot': 'jaw1_jnt',
                    }
       
    # add side items to fixedNamesDic
    for side in ['l_', 'r_']:
        
        # legs
        fixedNamesDic['{}thigh'.format( side )] = '{}hip1_jnt'.format( side )
        fixedNamesDic['{}thightwist01'.format( side )] = '{}hipTwist1_jnt'.format( side )
        fixedNamesDic['{}thightwist02'.format( side )] = '{}hipTwist2_jnt'.format( side )
        fixedNamesDic['{}calf'.format( side )] = '{}knee1_jnt'.format( side )
        fixedNamesDic['{}kneesharebone'.format( side )] = '{}knee2_jnt'.format( side )
        fixedNamesDic['{}calftwist01'.format( side )] = '{}footTwist1_jnt'.format( side )
        fixedNamesDic['{}calftwist02'.format( side )] = '{}footTwist2_jnt'.format( side )
        fixedNamesDic['{}foot'.format( side )] = '{}foot1_jnt'.format( side )
        fixedNamesDic['{}toebase'.format( side )] = '{}toes1_jnt'.format( side )
        #fixedNamesDic['{}toe0nub'.format( side )] = '{}toes2_jnt'.format( side )
        
        # arms
        fixedNamesDic['{}clavicle'.format( side )] = '{}clavicle1_jnt'.format( side )
        fixedNamesDic['{}upperarm'.format( side )] = '{}shoulder1_jnt'.format( side )
        fixedNamesDic['{}upperarmtwist01'.format( side )] = '{}shoulderTwist1_jnt'.format( side )
        fixedNamesDic['{}upperarmtwist02'.format( side )] = '{}shoulderTwist2_jnt'.format( side )
        fixedNamesDic['{}forearm'.format( side )] = '{}elbow1_jnt'.format( side )
        fixedNamesDic['{}elbowsharebone'.format( side )] = '{}elbow2_jnt'.format( side )
        fixedNamesDic['{}forearmtwist01'.format( side )] = '{}handTwist1_jnt'.format( side )  
        fixedNamesDic['{}forearmtwist02'.format( side )] = '{}handTwist2_jnt'.format( side )    
        fixedNamesDic['{}hand'.format( side )] = '{}hand1_jnt'.format( side )
        
        # fingers
        fixedNamesDic['{}thumb1'.format( side )] = '{}thumbFing1_jnt'.format( side )
        fixedNamesDic['{}thumb2'.format( side )] = '{}thumbFing2_jnt'.format( side )
        fixedNamesDic['{}thumb3'.format( side )] = '{}thumbFing3_jnt'.format( side )
        
        fixedNamesDic['{}index1'.format( side )] = '{}indexFing1_jnt'.format( side )
        fixedNamesDic['{}index2'.format( side )] = '{}indexFing2_jnt'.format( side )
        fixedNamesDic['{}index3'.format( side )] = '{}indexFing3_jnt'.format( side )

        fixedNamesDic['{}mid1'.format( side )] = '{}middleFing1_jnt'.format( side )
        fixedNamesDic['{}mid2'.format( side )] = '{}middleFing2_jnt'.format( side )
        fixedNamesDic['{}mid3'.format( side )] = '{}middleFing3_jnt'.format( side )
        
        fixedNamesDic['{}ring1'.format( side )] = '{}ringFing1_jnt'.format( side )
        fixedNamesDic['{}ring2'.format( side )] = '{}ringFing2_jnt'.format( side )
        fixedNamesDic['{}ring3'.format( side )] = '{}ringFing3_jnt'.format( side )
        
        fixedNamesDic['{}pinky1'.format( side )] = '{}pinkyFing1_jnt'.format( side )
        fixedNamesDic['{}pinky2'.format( side )] = '{}pinkyFing2_jnt'.format( side )
        fixedNamesDic['{}pinky3'.format( side )] = '{}pinkyFing3_jnt'.format( side )
    
    # rename based on dictionary

    for k, v in fixedNamesDic.items():
        if verbose:
            print 'k:', k
            print 'v:', v
        mc.rename( k, v )
    
def fixJointHierarchy(pelvis2YSubs = 14, toeExtendFactor = 2.0, headExtendFactor = 1.165):
    '''
    :param toeExtendFactor: float, factor to extend the ankle -> toe vector
    :return None
    '''
    
    
    # create joints builder group and top builder group in case they dont exists
    if not mc.objExists( buildObjectsGrp ):
        mc.group( em = True, w = True, n = buildObjectsGrp )
    
    if not mc.objExists( buildSkeletonGrp ):
        mc.group ( em = True, p = buildObjectsGrp, n = buildSkeletonGrp ) 
        
    # set root joint radius
    rootRadVal = mc.getAttr( '{}.radius'.format( rootJnt ) ) 
    mc.setAttr( '{}.radius'.format( rootJnt ), rootRadVal * 2)
    
    # freeze top hierarchy joint so will be possible to reparent items without creating transforms groups
    boneRoot = 'BoneRoot'
    mc.makeIdentity( boneRoot, apply = True )
    mc.parent( boneRoot, buildSkeletonGrp )
    
    extraBoneRoot = 'RL_ExtendedRoot'
    # if extra bone root joint exists parent it in build skeleton ... usually exists in RP6 type rigs
    if mc.objExists( extraBoneRoot ):
        mc.parent( extraBoneRoot, buildSkeletonGrp )
    
    # create extra pelvis joint
    pelvisJnt = 'pelvis1_jnt'
    pelvis2YSubs = pelvis2YSubs
    
    pelvisPos = mc.xform( pelvisJnt, q = True, t = True, ws = True )
    pelvisRad = mc.getAttr( pelvisJnt + '.radius' )
    
    pelvisExtraJnt = mc.createNode( 'joint', n = 'pelvis2_jnt' )
    mc.setAttr( pelvisExtraJnt + '.radius', pelvisRad )
    mc.xform( pelvisExtraJnt, ws = True, t = ( pelvisPos[0], pelvisPos[1] - pelvis2YSubs, pelvisPos[2] ) )
    
    mc.parent( pelvisExtraJnt, pelvisJnt )
    mc.reorder( pelvisExtraJnt, r = 1 )
    
    # create spine1_jnt
    spine1Jnt = mc.createNode( 'joint', n = 'spine1_jnt' )
    mc.xform( spine1Jnt, ws = True, t = ( pelvisPos[0], pelvisPos[1], pelvisPos[2] ) )
    mc.setAttr( spine1Jnt + '.radius', mc.getAttr( 'spine2_jnt.radius' ) )
    
    mc.parent( spine1Jnt, rootJnt )
    mc.parent( 'spine2_jnt', spine1Jnt )
    
    # create head tip joint if it doesn't exists
    headEndJnt = 'head2_jnt'
    if not mc.objExists( headEndJnt ):
        headEndJnt = mc.createNode('joint', n = headEndJnt)
        
        # get head position and apply it to head end adding some offset in y
        headPos = mc.xform( headJnt, ws = True, q = True, t = True )
        mc.xform( headEndJnt, ws = True, t = ( headPos[0], headPos[1] * headExtendFactor, headPos[2] ) )
        
        # set radius
        headJntRadVal = mc.getAttr( headJnt + '.radius' )
        mc.setAttr( headEndJnt + '.radius', headJntRadVal )
        
        mc.parent( headEndJnt, headJnt )
    
    # create toe end joints if they don't exists 
    for side in ['l_', 'r_']:
        
        # defide joints per side
        toeEndJnt = side + endToeJnt
        
        if not mc.objExists( toeEndJnt ):
            # create joint 
            toeEndJnt = mc.createNode( 'joint', n = toeEndJnt )
            mc.parent( toeEndJnt, side + toeJnt )
            
            # set radius
            radiusVal = mc.getAttr( side + toeJnt + '.radius' )
            mc.setAttr( toeEndJnt + '.radius', radiusVal )
            
            toeEndV = _findToeEndPos( side + ankleJnt, side + toeJnt, extendFactor = toeExtendFactor  )
            
            mc.xform( toeEndJnt, ws = True, t = ( toeEndV.x, toeEndV.y, toeEndV.z ) )
    
def fixRP6JointsOrient():
    
    # fix pelvis orient
    pelvisJntsList = [pelvisJnt, pelvisEndJnt]
    
    joint.orient( jointsList = pelvisJntsList, 
                  aimAxis = [1, 0, 0], 
                  upAxis = [0, -1, 0], 
                  upDir = [0, 0, 1] )
    
    # fix legs orient
    aimAxis = [1, 0, 0]
    
    for side in ['l_', 'r_']:
        
        legJointsList = joint.listChainStartToEnd( side + hipJnt, side + endToeJnt )
        
        joint.orient( jointsList = legJointsList, 
                  aimAxis = aimAxis, 
                  upAxis = [0, 1, 0], 
                  upDir = [0, 0, 1] )
        
        aimAxis = [-1, 0, 0]
    
    # fix spine and head orient
    spineToHeadList = joint.listChainStartToEnd( spineStartJnt, headEndJnt )
    
    joint.orient( jointsList = spineToHeadList, 
                  aimAxis = [1, 0, 0], 
                  upAxis = [0, -1, 0], 
                  upDir = [0, 0, 1] )    
    
    # fix arms orient
    aimAxis = [1, 0, 0]
    upAxis = [0, 0, 1]
    
    for side in ['l_', 'r_']:
        
        # reorder middle finger to improve hand orient
        mc.reorder( side + middleFingJnt, r = -3 )
        armJointsList = joint.listChainStartToEnd( side + clavicleJnt, side + handJnt )
        
        joint.orient( jointsList = armJointsList, 
                  aimAxis = aimAxis, 
                  upAxis = upAxis, 
                  upDir = [0, 1, 0] )
        
        aimAxis = [-1, 0, 0]    
        upAxis = [0, 0, -1]

    # orient fingers
    aimAxis = [1, 0, 0]
    upAxis = [0, 1, 0]     

    for side in ['l_', 'r_']:
        topFingers = mc.listRelatives( side + handJnt, c = True )[:5]
   
        for topFing in topFingers:
            
            fingerJointList = joint.listHierarchy( topFing )
            
            joint.orient( jointsList = fingerJointList, 
            aimAxis = aimAxis, 
            upAxis = upAxis, 
            upDir = [0, 1, 0] )
            
        aimAxis = [-1, 0, 0]    
        upAxis = [0, -1, 0] 

def fixCCJointsOrient():
    
    # fix pelvis orient
    pelvisJntsList = [pelvisJnt, pelvisEndJnt]
    
    joint.orient( jointsList = pelvisJntsList, 
                  aimAxis = [1, 0, 0], 
                  upAxis = [0, -1, 0], 
                  upDir = [0, 0, 1] )
    
    # fix legs orient
    aimAxis = [1, 0, 0]
    upAxis = [0, 0, 1]
    hipUpAxis = [0, 1, 0]
    TupAxis = [0, 1, 0]
    
    # fix right hip childs orientation to match the left one
    mc.reorder( 'r_knee1_jnt', r = -1 )
    
    for side in ['l_', 'r_']:
        
        legJointsList = joint.listChainStartToEnd( side + kneeJnt, side + endToeJnt )
        
        upperLegTwist = joint.listHierarchy( side + 'hipTwist1_jnt', withEndJoints = True )
        lowerLegTwist = joint.listHierarchy( side + 'footTwist1_jnt', withEndJoints = True )
        
        # orient hip joint ... this must be alone since it orientation is different than the other ones
        joint.orient( jointsList = [ side + hipJnt ], 
          aimAxis = aimAxis,
          upAxis = hipUpAxis, 
          upDir = [0, 0, 1],
          doAuto = False,
          verbose = False )
            
        # reorder middle finger to improve foot orient
        mc.reorder( side + endToeJnt, r = -5 )
        
        joint.orient( jointsList = legJointsList, 
                  aimAxis = aimAxis,
                  upAxis = upAxis, 
                  upDir = [0, 0, 1],
                  doAuto = True,
                  verbose = False )
        
        
        # orient twist for leg
        for jointList in [upperLegTwist, lowerLegTwist]:
        
            joint.orient( jointsList = jointList, 
              aimAxis = aimAxis,
              upAxis = TupAxis, 
              upDir = [0, 0, 1],
              doAuto = True,
              verbose = False )
                
        
        mc.delete(mc.parentConstraint( side + kneeJnt, lowerLegTwist[0] ) )
        mc.delete(mc.parentConstraint( side + kneeJnt, side + 'knee2_jnt' ) )
            
        TupAxis = [0, -1, 0]
        aimAxis = [-1, 0, 0]
        upAxis = [0, 0, 1]
        hipUpAxis = [0, -1, 0]
        
    
    # fix spine and head orient
    spineToHeadList = joint.listChainStartToEnd( spineStartJnt, headEndJnt )
    
    # reorder headEnd joint to be the aimTgt for head
    mc.reorder( headEndJnt, r = -1 )
    
    joint.orient( jointsList = spineToHeadList, 
                  aimAxis = [1, 0, 0], 
                  upAxis = [0, -1, 0], 
                  upDir = [0, 0, 1] )    
    
    # fix arms orient
    aimAxis = [1, 0, 0]
    upAxis = [0, 0, 1]
    TupAxis = [0, -1, 0]
    
    # reorder right elbow to match left one
    mc.reorder('r_elbow1_jnt', r = -1)
    
    for side in ['l_', 'r_']:
        
        # reorder hand joint to improve elbow orientation
        mc.reorder( side + handJnt, r = -2 )
        
        armJointsList = joint.listChainStartToEnd( side + clavicleJnt, side + handJnt )
        upperArmTwist = joint.listHierarchy( side + 'shoulderTwist1_jnt', withEndJoints = True )
        lowerArmTwist = joint.listHierarchy( side + 'handTwist1_jnt', withEndJoints = True )
        
        joint.orient( jointsList = armJointsList, 
                  aimAxis = aimAxis, 
                  upAxis = upAxis, 
                  upDir = [0, 1, 0] )
        
        # orient twist for arms
        for jointList in [upperArmTwist, lowerArmTwist]:
        
            joint.orient( jointsList = jointList, 
              aimAxis = aimAxis,
              upAxis = TupAxis, 
              upDir = [0, 0, 1],
              doAuto = True,
              verbose = False )
            
        mc.delete(mc.parentConstraint( side + elbowJnt, side + 'elbow2_jnt' ) )
            
        TupAxis = [0, 1, 0]
        aimAxis = [-1, 0, 0]    
        upAxis = [0, 0, -1]
    
    
    
    # orient fingers
    aimAxis = [1, 0, 0]
    upAxis = [0, 1, 0]     

    for side in ['l_', 'r_']:
        topFingers = mc.listRelatives( side + handJnt, c = True )[:5]
   
        for topFing in topFingers:
            
            fingerJointList = joint.listHierarchy( topFing )
            
            joint.orient( jointsList = fingerJointList, 
            aimAxis = aimAxis, 
            upAxis = upAxis, 
            upDir = [0, 1, 0] )
            
            if topFing == '{}thumbFing1_jnt'.format( side ):
                joint.orient( jointsList = fingerJointList, aimAxis = [1, 0, 0], upAxis = [0, 0, -1], upDir = [0, 1, 0], doAuto = False, verbose = False )
            
        aimAxis = [-1, 0, 0]    
        upAxis = [0, -1, 0]
        
def createReferenceLocators():
    
    
    for side in ['l_', 'r_']:
        buildLocGrp = side + 'build_loc_grp'
        if not mc.objExists( buildLocGrp ):
            mc.group( em = True, n = buildLocGrp, p = buildObjectsGrp )
        
        # create pole vector for elbow
        sideShldrJnt = side + shldrJnt
        sideElbowJnt = side + elbowJnt
        sideHandJnt = side + handJnt
        
        elbowPvPos = poleVector.findPoleVectorPosition( sideShldrJnt, sideElbowJnt, sideHandJnt, posOffset = 2 )
        
        armPv = mc.spaceLocator(n = side + 'armPoleVec_loc')[0]
        for axis in ['X', 'Y', 'Z']:
            mc.setAttr( '{}Shape.localScale{}'.format( armPv, axis ), 5 )
        mc.parent( armPv, buildLocGrp )
    
        mc.xform( armPv, ws = True, t = ( elbowPvPos['position'][0],
                                        elbowPvPos['position'][1],
                                        elbowPvPos['position'][2]),
                                        rotation = ( elbowPvPos['rotation'][0],
                                        elbowPvPos['rotation'][1],
                                        elbowPvPos['rotation'][2])
                                        )
        
        # create pole vector for knee
        sideHipJnt = side + hipJnt
        sideKneeJnt = side + kneeJnt
        sideFootJnt = side + ankleJnt           
    
        kneePvPos = poleVector.findPoleVectorPosition( sideHipJnt, sideKneeJnt, sideFootJnt, posOffset = 5 )
        
        legPv = mc.spaceLocator(n = side + 'legPoleVec_loc')[0]
        for axis in ['X', 'Y', 'Z']:
            mc.setAttr( '{}Shape.localScale{}'.format( legPv, axis ), 5 )
        mc.parent( legPv, buildLocGrp )
    
        mc.xform( legPv, ws = True, t = ( kneePvPos['position'][0],
                                        kneePvPos['position'][1],
                                        kneePvPos['position'][2]),
                                        rotation = ( kneePvPos['rotation'][0],
                                        kneePvPos['rotation'][1],
                                        kneePvPos['rotation'][2])
                                        )    
    
        # create foot locators
        footLocs = footRigLocators.build( side + ankleJnt, side + toeJnt, side + endToeJnt )
        mc.parent( footLocs, buildLocGrp )
        
def _findToeEndPos( ankleJnt, toeJnt, extendFactor  ):
    
    '''
    fuction to find a position for end toe joint
    :param ankleJnt: str, foot joint
    :param toeJnt: str, toe joint 
    :param extendFactor: float, factor to extend the ankle -> toe vector
    :return vector: new position for toe end joint
    '''
    ankleV = vector.makeMVector( mc.xform( ankleJnt, q = True, ws = True, t = True ) )
    toeV = vector.makeMVector( mc.xform( toeJnt, q = True, ws = True, t = True ) )
    
    # fix ankle 'y' position to be align with toe
    ankleV.y = toeV.y
    
    # make new vector and extend it 
    ankleToToeV = toeV - ankleV
    
    ankleToToeV = ankleToToeV * extendFactor
    
    toeEndV = toeV + ankleToToeV
    
    return toeEndV
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    