"""
rig.py

project: <type the project or client here>
assetName: <name of the asset to rig>
description: <short description of the rig to work with>

"""

#TODO: makeModuleRigSets() fuction in base.py
#TODO: clean rig scene

# import modules to work with
import os.path
import json

import maya.cmds as mc
import maya.mel as mm
import maya.OpenMaya as om

from pdb_rigLib.base import control
from pdb_rigLib.base import module
from pdb_rigLib.base import base

from pdb_rigLib.rig import spine
from pdb_rigLib.rig import neck
from pdb_rigLib.rig import ikChain
from pdb_rigLib.rig import leg
from pdb_rigLib.rig import arm
from pdb_rigLib.rig import hand
from pdb_rigLib.rig import head
from pdb_rigLib.rig import eyes
from pdb_rigLib.rig import eyebrow
from pdb_rigLib.rig import eyelids
from pdb_rigLib.rig import tongue
from pdb_rigLib.rig import mouth
from pdb_rigLib.rig import general
from pdb_rigLib.rig import tail

from pdb_rigLib.tools import saveSkinWeights
from pdb_rigLib.tools import saveCvPositions
from pdb_rigLib.tools import bSkinSaver
from pdb_rigLib.tools import transformWrapper

from pdb_rigLib.utils import joint
from pdb_rigLib.utils import name
from pdb_rigLib.utils import shape
from pdb_rigLib.utils import transform
from pdb_rigLib.utils import constraint
from pdb_rigLib.utils import vector
from pdb_rigLib.utils import anim
from pdb_rigLib.utils import attribute


# define the main asset folder of the asset after import the rig.py,  example: rig.mainAssetFolder = D:/TRABAJO/autoRig/assets/%s
global mainAssetFolder

# define components path
assetModelFilePath = '%smodel/%s_model.ma'
assetBuilderFilePath = '%sbuilder/%s_builder.ma'
skinWeightsFilePath = '%sweights/skinCluster/'
assetControlShapesPath = '%scontrolShapes/%s_controlShapes.xml'
skinBlendWeightsFilePath = '%sweights\\blendWeights\\'
gameJointsFilePath = '%sgameJointsInfo/'
gameSkinWeightsFilePath = '%sweights\\gameWeights\\'

# define scene scale
sceneScale = 1.0

# define main joints
rootJnt = 'root1_jnt'
headJnt = 'head1_jnt'
headEndJnt = 'head2_jnt'

bodyAssetGeo = 'body_geo'  # this should be the name of the main body geo
deformSetupGrp = 'deformSetup_grp'



def build ( assetName, loadControlShapes = True, loadSkinWeights = True, createGameJoints = False ):
    
    # check if main assset folder is define
    if not mainAssetFolder:
        raise Exception ('# please define a rig.mainAssetFolder for the asset %s with the project path') % assetName
    
    # start timer
    startTime = mc.timerX()
    print '# start build rig for asset %s' % assetName
    
    #===========================================================================
    # import files
    #===========================================================================
    assetFolder = mainAssetFolder % assetName
    
    # create a new scene    
    mc.file( new = True, f = True )
    
    # import model 
    mc.file(assetModelFilePath % (assetFolder, assetName), i = True)
    
    # import builder
    mc.file(assetBuilderFilePath % ( assetFolder, assetName ), i = True )
    
    #fit camera
    mc.viewFit()
    
    #==========================================================================
    # create baseRigData
    #==========================================================================
    baseRigData = base.build(
                        headJnt,
                        topHeadObj = headEndJnt,
                        assetName = assetName,
                        offsetAboveHeadY = sceneScale * 7,
                        scale = 1.0,
                        doCheckClashingNames = True
                        )
    
    # parent model under rig
    modelAssetGrp = '%s_grp' % assetName
    mc.parent( modelAssetGrp, baseRigData['modelGrp'] )
    
    # parent skeleton under rig
    mc.parent( rootJnt, baseRigData['jointsGrp'] )
    
    # make deform group
    deformSetupGroup = mc.group( n = deformSetupGrp, em = True, p = baseRigData['mainGrp'] )
    mc.hide( deformSetupGroup )
    
    
    moduleMainGrps = []
    
    #===========================================================================
    # setup control rig
    #===========================================================================
    
    controlRigData = setupControlRig( assetName, baseRigData )
    moduleMainGrps.extend( controlRigData[0] )
    
    # fix all the shapes names
    fixAllShapesNames()
    
    #===========================================================================
    # setup deform rig
    #===========================================================================
    
    deformRigData = setupDeformRig( assetName, baseRigData, loadSkinWeights, createGameJoints )
    moduleMainGrps.extend( deformRigData[0] )
    
    # fix all the shapes names
    fixAllShapesNames()    
    
    #===========================================================================
    # post build
    #===========================================================================
    
    # load rig settings
    adjustRigSettings( assetName )
    
    if loadControlShapes:
        
        loadRigControlShapes( assetName )
    
    # label joints
    joint.label( mc.ls( type = 'joint' ) )
    
    # clean builder grp
    mc.delete('build_objects_grp')
    
    # report time building setup    
    totalTime = mc.timerX( st = startTime )    
    print '# Total Time building %s rig: %f seconds' % ( assetName, totalTime )

def adjustRigSettings ( assetName ):
    
    visCtrl = 'vis_ctl'
    global1Ctrl = 'global1_ctl'
    global2Ctrl = 'global2_ctl'
    
    # add rig settings here

def setupControlRig( assetName, baseRigData ):
  
    '''
    build control rig
    '''
    
    # ========================================================
    # define scene object names
    # ========================================================

    buildSkeletonGrp = 'build_skeleton_grp'

    spineCrv = 'spine_crv'
    neckCrv = 'neck_crv'
    tailCrv = 'tail_crv'
    tongueCrv = 'tongue_crv'

    bodyPivotLoc = 'body_loc'
    chestPivotLoc = 'chest_loc'
    pelvisPivotLoc = 'pelvis_loc'

    lside = 'l_'
    rside = 'r_'
    fore = 'fore'
    hind = 'hind'

    rootJnt = 'root1_jnt'
    spineStartJnt = 'spine1_jnt'
    spineEndJnt = 'spine6_jnt'
    spineJoints = joint.listChainStartToEnd( spineStartJnt, spineEndJnt )
    
    chestJnt = 'spine5_jnt'
    pelvisJnt = 'pelvis1_jnt'
    headJnt = 'head1_jnt'
    headEndJnt = 'head2_jnt'
    jawJnt = 'jaw1_jnt'
    neckStartJnt = 'neck1_jnt'
    if mc.objExists( headJnt ):
        neckEndJnt = mc.listRelatives( headJnt, p = True, type = 'joint' )[0]
        neckJoints = joint.listChainStartToEnd( neckStartJnt, neckEndJnt )
    
    bellyJnt = 'belly1_jnt'
    lowerChestJnt = 'lowerChest1_jnt'
    lowerPelvisJnt = 'lowerPelvis1_jnt'
    
    eyeJnt = 'eye1_jnt'
    earJnt = 'ear1_jnt'
    clavicleJnt = 'clavicle1_jnt'
    shoulderJnt = 'shoulder1_jnt'
    elbowJnt = 'elbow1_jnt'
    handJnt = 'hand1_jnt'
    hand2Jnt = 'hand2_jnt'
    hand3Jnt = 'hand3_jnt'
    hipJnt = 'hip1_jnt'
    kneeJnt = 'knee1_jnt'
    footJnt = 'foot1_jnt'
    toeJnt = 'toes1_jnt'
    toe2Jnt = 'toes2_jnt'
    scapulaJnt = 'scapula1_jnt'
    scapulaEndJnt = 'scapula2_jnt'
    tailStartJnt = 'tail1_jnt'
    if mc.objExists( tailStartJnt ):
        tailEndJnt = mc.listRelatives( tailStartJnt, ad = True, type = 'joint' )[0]
        tailJoints = joint.listChainStartToEnd( tailStartJnt, tailEndJnt )
        
    armPvLoc = 'armPoleVec_loc'
    legPvLoc = 'legPoleVec_loc'
    handOrientRefLoc = 'handOrientRef_loc'
    handToeTipLoc = 'handToeTip_loc'
    footToeTipLoc = 'footToeTip_loc'
    handHeelLoc = 'handHeel_loc'
    footHeelLoc = 'footHeel_loc'
    handInLoc = 'handIn_loc'
    footInLoc = 'footIn_loc'
    handOutLoc = 'handOut_loc'
    footOutLoc = 'footOut_loc'
    handOrientRefLoc = 'handOrientRef_loc'
    footOrientRefLoc = 'footOrientRef_loc'

    muzzleJoints = ['muzzle1_jnt']
    
    topFingJnts = ['thumbFing1_jnt', 'indexFingBase1_jnt', 'middleFingBase1_jnt', 'ringFingBase1_jnt', 'pinkyFingBase1_jnt']
    #topFingJnts = ['thumbFing1_jnt', 'indexFing1_jnt', 'middleFing1_jnt', 'ringFing1_jnt', 'pinkyFing1_jnt']
    
    topToeJnts = ['toeA1_jnt', 'toeB1_jnt', 'toeC1_jnt']
    
    l_topFingJnts = [ lside + f for f in topFingJnts ]
    r_topFingJnts = [ rside + f for f in topFingJnts ]

    l_toeJnts = [ lside + toej for toej in topToeJnts ]
    r_toeJnts = [ rside + toej for toej in topToeJnts ]

    tongueStartJnt = 'tongue1_jnt'
    if mc.objExists( tongueStartJnt ):
        
        tongueEndJnt = mc.listRelatives( tongueStartJnt, ad = 1, type = 'joint' )[0]
        
    #===========================================================================
    # modules setup 
    #===========================================================================
    
    moduleMainGrps = []
    
    return [moduleMainGrps]

def setupDeformRig( assetName, baseRigData, loadSkinWeights, createGameJoints ):
    
    """
    setup deform rig
    """
    
    # define scene rig object names
    
    lside = 'l_'
    rside = 'r_'
    
    rootJnt = 'root1_jnt'
    headEndJnt = mc.listRelatives( headJnt, c = True, type = 'joint' )[0]
    chestJnt = 'spine5_jnt'
    pelvisjnt = 'pelvis1_jnt'
    tailStartJnt = 'tail1_jnt'
    # tailEndJnt = mc.listRelatives( tailStartJnt, ad = True, type = 'joint' )[0]
    neckStartJoint = 'neck1_jnt'
    neckEndJoint = mc.listRelatives( headJnt, p = True, type = 'joint' )
    clavicleJnt = 'clavicle1_jnt'
    shoulderjnt = 'shoulder1_jnt'
    elbowjnt = 'elbow1_jnt'
    handjnt = 'hand1_jnt'
    global1Ctrl = baseRigData['global1Ctrl']
    jawCtrl = 'jaw_ctl'
    stickyLipCrv = 'lips_line_crv'
    stickyLipOffsetCrv = 'lips_line_offset_crv'
    
    #===========================================================================
    # create game joints 
    #===========================================================================
    if createGameJoints:
        loadGameJointsSetup( assetName, baseRigData )
    
    #===========================================================================
    #  bind geometry
    #===========================================================================
    
    if loadSkinWeights:
        
        if createGameJoints:
            
            loadGameSkinClusterWeights( assetName )
        
        else:
            
            loadSkinClusterWeights( assetName )
            
            # load DQ skin weights
            assetFolder = mainAssetFolder % assetName
            weightsFolder = skinBlendWeightsFilePath % assetFolder
            
            try:
                for file in os.listdir( weightsFolder ):
                    print 'file:', file
                    if file.endswith( '.wts' ):
                        filePath = os.path.join( weightsFolder, file )
                        
                        # set skin to blend weights
                        # read from file
                        fileobj = open( filePath, mode = 'rb' )
                        fileobjStr = fileobj.read()
                        weightsDt = json.loads( fileobjStr )
                        fileobj.close()
                        
                        deformerNode = weightsDt['deformerName']
                        
                        mc.setAttr( '{}.skinningMethod'.format( deformerNode ), 2 )
                        mc.setAttr( '{}.deformUserNormals'.format( deformerNode ), 0 )
                        
                        saveSkinWeights.loadBlendWeights( filePath )
                        
            except:
                
                print '# no Dual Quaternion weights found... moving to next step'

    
    #===========================================================================
    #  modules setup
    #===========================================================================
    
    moduleMainGrps = []
     
    return [moduleMainGrps]
    
def fixAllShapesNames():
    
    """
    fix all the shapes names of transforms
    """
    
    allTransforms = mc.ls( type = 'transform' )
    
    for t in allTransforms:
        
        try:
            shape.fixShapesName( t )
            
        except:
            
            pass

def saveSkinClusterWeights( assetName, skinnedObjs = None ):
    
    """
    save skinCluster weights for the rig
    """
    
    if not skinnedObjs:
        
        return
    
    assetFolder = mainAssetFolder % assetName
    
    skinPath = skinWeightsFilePath % assetFolder
    
    for geo in skinnedObjs:
        
        mc.select(geo)
        
        fullSkinPath = skinPath + geo + '.skinwt'
        
        bSkinSaver.bSaveSkinValues(fullSkinPath)
        
        print "for: %s \n" % geo
    
    mc.select(cl = True)

def loadSkinClusterWeights( assetName ):
    
    """
    load skinCluster weights for the rig
    """
    
    assetFolder = mainAssetFolder % assetName
    skinPath = skinWeightsFilePath % assetFolder
    
    if skinPath.endswith( '/' ) == 0: skinPath = skinPath + '/'
    
    dirFiles = os.listdir( skinPath )
    weightFiles = [ skinPath + f for f in dirFiles if f.count( '.skinwt' ) ]

    for i, wtFile in enumerate( weightFiles ):
        try:
            loadedGeo = bSkinSaver.bLoadSkinValues(loadOnSelection = False, inputFile = wtFile)
            skinClusterName = mm.eval('findRelatedSkinCluster '+loadedGeo)
            
            mc.rename( skinClusterName, loadedGeo + '_skc' )
        except:
            '# not able to load {} ...skip'.format( wtFile )

def saveRigControlShapes( assetName ):

    '''
    save control shapes from prepared list
    '''
    
    saveControlShapesList = getSaveControlShapesNames( assetName )
    
    assetFolder = mainAssetFolder % assetName
    controlShapesFilepath = assetControlShapesPath % ( assetFolder, assetName )
    
    print '# saving controls shapes to %s, listed shapes: %s' % ( controlShapesFilepath, saveControlShapesList )
    saveCvPositions.save( controlShapesFilepath, saveControlShapesList )
    
def loadRigControlShapes( assetName ):

    '''
    load control shapes for control rig
    '''
    
    saveControlShapesList = getSaveControlShapesNames( assetName )
    
    assetFolder = mainAssetFolder % assetName
    controlShapesFilepath = assetControlShapesPath % ( assetFolder, assetName )
    
    if os.path.exists( controlShapesFilepath ):
        
        print '# loading controls shapes for %s' % saveControlShapesList
        saveCvPositions.load( path = controlShapesFilepath, objects = saveControlShapesList )
    
    else:
        
        print '# loading controls shapes skipped, file not found:%s' % controlShapesFilepath
        
def getSaveControlShapesNames( assetName ):
    
    """
    get save control shapes names
    """
    
    saveControlShapesList = mc.ls( '*_ctl', type = 'transform' )
    
    # use this for temporary skipping control shapes
    # by default it should always load everything in the file
    skipObjectsList = []
    
    templateCtrlObjects = ['headHeadTemplate_grp', 'spineChestTemplate_grp']
    
    for o in templateCtrlObjects:
        
        saveControlShapesList.append( o )
    
    for o in skipObjectsList:
        
        if o in saveControlShapesList:
            
            saveControlShapesList.remove( o )
    
    
    controlshapeListExisting = [ o for o in saveControlShapesList if mc.objExists( o ) ]
    
    
    return controlshapeListExisting

def saveDqWeights(dqObjects = [], assetName = ''):
    
    '''
    save dual quaternion weights
    '''
    
    assetFolder = mainAssetFolder % assetName
    dualQuaternionPath = skinBlendWeightsFilePath % assetFolder
    
    for object in dqObjects:
        
        skinClusterName = object + '_skc'
        
        objectNoSuffix = name.removeSuffix( object )
        dqSavePath = dualQuaternionPath + '/%sSkinBlend.wts' % objectNoSuffix
        
            
        saveSkinWeights.saveBlendWeights( dqSavePath, skinClusterName )
        
        print '# saving DQ weights for %s in %s' % (skinClusterName, dqSavePath)

def saveGameJointsSetup( assetName, gameJointsGroup = 'gameJoints_grp' ):
    
    '''
    function to save out as json file the game joints hierarchy 
    and their drivers through constraint parent to reconstruct when generate the game rig
    :param savePath: str, path to save out the json file, should be the asset path
    :param gameJointsGroup: str, name of the parent group which contains the game joints
    '''
    
    # define save path
    assetFolder = mainAssetFolder % assetName
    gameJointsSetupPath = gameJointsFilePath % ( assetFolder )
    jsonFilePath = '%s%s_gameJointsInfo.json' % ( gameJointsSetupPath, assetName )
    
    # check if folder already exists or create it if needed
    if not os.path.exists( gameJointsSetupPath ):
        os.mkdir( gameJointsSetupPath )
    
    gameJoints = mc.listRelatives( gameJointsGroup, ad = True, type = 'joint' )
    gameJointsData = {}
    
    for jnt in gameJoints:
        
        # get parent and constraint driver joint to populate the json dic
        consNode = mc.listConnections('{}.tx'.format( jnt ), type = 'constraint', s = True, d = False)[0]
        objs = mc.listConnections( consNode + '.target', s = 1, d = 0 ) 
        targets = [ obj for obj in objs if not obj == consNode ]
        jntDriver = list( set( targets ) )[0]
        jntParent = mc.listRelatives( jnt, p = True )[0]
        
        jntInfoDic = {
                    'name': jnt,
                    'parent': jntParent,
                    'driver': jntDriver
                    }
        gameJointsData[ jnt ] = jntInfoDic
    
    # save json file
    with open( jsonFilePath, 'w' ) as file_for_write:
        json.dump( gameJointsData, file_for_write, indent = 4 )
    
    print '# json file with game joints information saved successfully'
    
def loadGameJointsSetup( assetName, baseRigData = None, gameJointsGroup = 'gameJoints_grp' ):
    
    # define load path
    assetFolder = mainAssetFolder % assetName
    gameJointsSetupPath = gameJointsFilePath % ( assetFolder )
    jsonFilePath = '%s%s_gameJointsInfo.json' % ( gameJointsSetupPath, assetName )
    
    # load json info
    with open( jsonFilePath, 'r' ) as file_for_read:
        gameJointsData = json.load( file_for_read )
    
    # create game joints group
    parentGrp = gameJointsGroup
    if not mc.objExists( gameJointsGroup ):
        parentGrp = mc.group( em = True, n = gameJointsGroup, p = baseRigData['mainGrp'] )
    
    # connect game joints visibility
    visCtrl = baseRigData['visCtrl'].C
    jointVisAt = 'gameJointsVis'
    jointVisDisTypeAt = 'gameJointsDisType'
    
    attribute.addSection( visCtrl, 'GameJoints' )
    mc.addAttr( visCtrl, ln = jointVisAt, at = 'enum', en = 'off:on', k = True , dv = 0)
    mc.addAttr( visCtrl, ln = jointVisDisTypeAt, at = 'enum', enumName = 'normal:template:reference', k = 1, dv = 2 )

    mc.connectAttr( '{}.{}'.format( visCtrl, jointVisAt ), parentGrp + '.v' )
    mc.setAttr( parentGrp + '.ove', 1 )
    mc.connectAttr( '{}.{}'.format( visCtrl, jointVisDisTypeAt ), parentGrp + '.overrideDisplayType' )
    
    fullGameJoints = []
    
    # creat boneRoot joint
    boneRootJnt = mc.createNode( 'joint', n = 'game_boneRoot1_jnt', p = parentGrp )
    fullGameJoints.append( boneRootJnt )
    
    for jnt in gameJointsData.keys():
        
        # define some info from the json file
        jntName = gameJointsData[ jnt ]['name']
        jntParent = gameJointsData[ jnt ]['parent']
        jntDriver = gameJointsData[ jnt ]['driver']
        
        # duplicate joints
        gameJnt = mc.duplicate( jntDriver, n = jntName, po = True )[0]
        mc.parent( gameJnt, parentGrp )
        
        fullGameJoints.append( gameJnt )
    
    #  parent game joint in proper hierarchy and constraint from driver joint
    for gameJnt in gameJointsData.keys():
        
        jntParent = gameJointsData[ gameJnt ]['parent']
        jntDriver = gameJointsData[ gameJnt ]['driver']
        
        try:
            mc.parent( gameJnt, jntParent )
        except:
            mc.parent( gameJnt, boneRootJnt )
        
        mc.parentConstraint( jntDriver, gameJnt, mo = True )
        mc.scaleConstraint(jntDriver, gameJnt, mo = True )
    
    # clear selection
    mc.select( cl = True)
    
    # create game joints and geo set
    gameJointsSet = mc.sets( n = 'gameJoints_set' )
    mc.sets( fullGameJoints , add = gameJointsSet )
    
    gameGeoSet = mc.sets( n = 'gameGeometry_set' )
    mc.sets( baseRigData['modelGrp'] , add = gameGeoSet )
    
def saveGameSkinClusterWeights( assetName, skinnedObjs = None ):
    
    """
    save skinCluster weights for the rig
    """
    
    if not skinnedObjs:
        
        return
    
    assetFolder = mainAssetFolder % assetName
    
    skinPath = gameSkinWeightsFilePath % assetFolder
    
    # check if folder already exists or create it if needed
    if not os.path.exists( skinPath ):
        os.mkdir( skinPath )
    
    for geo in skinnedObjs:
        
        mc.select(geo)
        
        fullSkinPath = skinPath + geo + '.skinwt'
        
        bSkinSaver.bSaveSkinValues(fullSkinPath)
        
        print "for: %s \n" % geo
    
    mc.select(cl = True)    

def loadGameSkinClusterWeights( assetName ):
    
    """
    load skinCluster weights for the rig
    """
    
    assetFolder = mainAssetFolder % assetName
    skinPath = gameSkinWeightsFilePath % assetFolder
    
    if skinPath.endswith( '/' ) == 0: skinPath = skinPath + '/'
    
    dirFiles = os.listdir( skinPath )
    weightFiles = [ skinPath + f for f in dirFiles if f.count( '.skinwt' ) ]

    for i, wtFile in enumerate( weightFiles ):
        try:
            loadedGeo = bSkinSaver.bLoadSkinValues(loadOnSelection = False, inputFile = wtFile)
            skinClusterName = mm.eval('findRelatedSkinCluster '+loadedGeo)
            
            mc.rename( skinClusterName, loadedGeo + '_skc' )
        except:
            '# not able to load {} ...skip'.format( wtFile )
    