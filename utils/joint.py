"""
joint utils @ utils
Utilities to work with joints
"""

import maya.cmds as mc
import maya.OpenMaya as om

from . import name
from . import connect
from . import attribute
from . import transform
from . import vector
from . import apiwrap


def listHierarchy( topJoint, withEndJoints = True ):

    """
    List joint hierarchy starting with top joint
    :param topJoint: str, joint to get listed with its joint hierarchy
    :param withEndJoints: bool, list hierarchy including end joints
    :return: list( str ), listed joints starting with top joint
    """

    listedJoints = mc.listRelatives( topJoint, type = 'joint', ad = True )
    listedJoints.append( topJoint )
    listedJoints.reverse()

    completeJoints = listedJoints[:]

    if not withEndJoints:

        completeJoints = [ j for j in listedJoints if mc.listRelatives( j, c = 1, type = 'joint' ) ]

    return completeJoints

def createJntVtxPos(name = name, ctrl = False, popCon = False):

    sel = mc.ls(sl=True , fl=True)[0]

    #get vtx position , create jnt and copy vtx pos to jnt
    vtxPos = mc.xform(sel, ws=True, t=True, q=True)
    mc.select(cl=True)

    jntName = name + '_jnt'
    jnt = mc.joint(n=jntName)

    mc.xform(jnt, ws=True, t=(vtxPos[0],vtxPos[1], vtxPos[2] ))

    for i in ["root", "inf", "pos"]:

        grp = mc.group(n = "%s_%s_grp", em=True %  (i, name) )
        mc.delete(mc.parentConstraint(jnt, grp, mo=False))
        if i == "inf":
            mc.parent(i, "root_%s_grp" % name)
        elif i == "pos":
            mc.parent(i, "inf_%s_grp" % name)

def label(joints, optionalLeftPrefix = '', optionalRightPrefix = ''):
    
    """
    create labels for joints using the maya 'other' type to save the names
    very useful for accurate finding influences during copy and mirror skin weights
    
    :param: joints: list( str ), joints to have the label attribute named
    :param optionalLeftPrefix: str, additional prefix for detecting left side from object name start, example 'deform_l'
    :param optionalRightPrefix: str, additional prefix for detecting right side from object name start, example 'deform_r'
    :return None
    """
    
    for j in joints:
        
        # get needed strings
        
        side = name.getSide( j )
        base1 = name.removeSuffix( j )
        base = name.removeSide( base1 )
        
        # side prefix option
        
        optionalPrefix = ''
        
        if optionalLeftPrefix:
            
            if j.startswith( optionalLeftPrefix ):
                
                optionalPrefix = optionalLeftPrefix
                side = 'l'
        
        if optionalRightPrefix:
            
            if j.startswith( optionalRightPrefix ):
                
                optionalPrefix = optionalRightPrefix
                side = 'r'
        
        if optionalPrefix:
            
            base = name.removeSuffix( j )
            
        # set custom labels
        
        if side == '': mc.setAttr( j + '.side', 0 )
        if side == 'l': mc.setAttr( j + '.side', 1 )
        if side == 'r': mc.setAttr( j + '.side', 2 )
        
        mc.setAttr( j + '.type', 18 )
        mc.setAttr( j + '.otherType', base, typ = 'string' )

def listChainStartToEnd( topJoint, lowestJoint ):
    
    """
    return a list of joints from top joint to lowest joint
    NOTE: fuction is assuming that top joint is really a parent of lowest joint
    
    :param topJoint: str, top joint of the chain
    :param lowestJoint: str, lowest joint of the chain
    :return list ( str ), list of joints from topJoint to lowestJoint
    """
    
    lowestJointLong = mc.ls( lowestJoint, l = True )[0]
    lowestJointNameParts = lowestJointLong.split( '|' )
    
    jointsList = []
    
    topIdx = lowestJointNameParts.index( topJoint )
    
    for i in range( len( lowestJointNameParts ) ) [ topIdx: ] :
        
        jointsList.append( lowestJointNameParts[i] )
        
    return jointsList

def makeTwistRefJoint( baseJnt, endJnt, refObject, prefix = '', customTwistBaseObj = '', twistOffsetDriverPlug = None ):
    
    '''
    make twist reference joint
    NOTE: this is usualy part of twist joint setup, but it can be useful standalone
    NOTE: e.g. dual quaternion skinCluster from M2011 only needs this, not the inbetween twist joints
    
    :param baseJnt: str, name of base joint
    :param endJnt: str, name of end joint
    :param refObject: str, name of reference object to drive twist
    :param prefix: str, prefix to name new objects
    :param customTwistBaseObj: str, custom twist base object or joint for different base object behaviour (example: keep humanIk knee rotate one axis only)
    :param twistOffsetDriverPlug: str, optional, name of twist offset angle driver attribute in plug format <OBJECT.ATTRIBUTE>
    :return: dictionary: refjoint(str), ikHandle(str), ikjoint(str), mainGrp(str)
    
    NOTE: customTwistBaseObj is for rotation behaviour mainly, parent child information should be still retrieved from baseJnt
    '''
    
    if not prefix:
        
        prefix = name.removeSuffix( baseJnt )
    
    
    baseJntObj = baseJnt
    if customTwistBaseObj:
        
        baseJntObj = customTwistBaseObj
    
    # create main group and joints
    
    maingrp = mc.group( n = prefix + 'TwistRef_grp', em = 1, p = baseJntObj )
    
    
    refJoints = makeFromXforms( [ baseJntObj, endJnt ], prefix = prefix + 'TwistRefIk' )
    twistJoints = makeFromXforms( [ baseJntObj, endJnt ], prefix = prefix + 'TwistRef' )
    mc.parent( refJoints[0], maingrp )
    mc.parent( twistJoints[0], maingrp )
    mc.hide( refJoints[0] )
    
    if mc.nodeType( baseJnt ) == 'joint':
        
        baseJntRad = mc.getAttr( baseJnt + '.radi' )
        for j in refJoints: mc.setAttr( j + '.radi', baseJntRad * 2 )
        for j in twistJoints: mc.setAttr( j + '.radi', baseJntRad * 2 )
    
    # setup IK
    
    refIk = mc.ikHandle( n = prefix + 'TwistRef_ikh', sol = 'ikSCsolver', sj = refJoints[0], ee = refJoints[1] )[0]
    mc.hide( refIk )
    
    mc.parent( refIk, maingrp )
    mc.orientConstraint( refObject, refIk, mo = 1 )
    
    
    # add offset twist connection
    
    twistoffsetat = 'twistoffset'
    twistat = 'twist'
    
    mc.addAttr( maingrp, ln = twistoffsetat, at = 'float', k = 1 )
    mc.addAttr( maingrp, ln = twistat, at = 'float', k = 1 )
    
    offadd = mc.createNode( 'addDoubleLinear', n = prefix + 'TwistRef_adl' )
    
    mc.connectAttr( maingrp + '.' + twistoffsetat, offadd + '.i1' )
    mc.connectAttr( refJoints[0] + '.rx', offadd + '.i2' )
    mc.connectAttr( offadd + '.o', maingrp + '.' + twistat )
    mc.connectAttr( offadd + '.o', twistJoints[0] + '.rx' )
    
    # connect offset twist plug
    if twistOffsetDriverPlug:
        
        mc.connectAttr( twistOffsetDriverPlug, maingrp + '.rx' )
    
    
    return { 'refjoint':twistJoints[0], 'ikHandle':refIk, 'ikjoint':refJoints[0], 'mainGrp':maingrp }

def makeTwistJoints( baseJnt, refJnt, twistJointsNumber, prefix = '', customTwistBaseObj = '' ):
    
    
    '''
    NOTES: x axis is a primary axis for incrementing twist joints position
    
    :param baseJnt: str, name of base joint
    :param refJnt: str, name of reference joint to drive twist
    :param twistJointsNumber: int, number of twist joints to make
    :param prefix: str, optional, prefix to name new objects, if nothing passed it gets derived from base joint name
    :param customTwistBaseObj: str, custom twist base object or joint for different base object behaviour (example: keep humanIk knee rotate one axis only)
    :return: dictionary by part using makeTwistRefJoint() returned dictionary: refjoint(str), ikHandle(str), ikjoint(str), mainGrp(str), twistjoints(list)
    
    NOTE: customTwistBaseObj is for rotation behaviour mainly, parent child information should be still retrieved from baseJnt
    '''
    # define twist part prefix 
    twistPartPrefix = 'TwistPart'

    # get prefix in case is not passed
    if not prefix:
        prefix = name.removeSuffix( baseJnt )
    
    baseJntObj = baseJnt
    
    # make twist ref joint
    baseJntChild = mc.listRelatives( baseJnt, c = 1, typ = 'joint' )[0]
    twistRefJntData = makeTwistRefJoint( baseJnt = baseJnt, endJnt = baseJntChild, refObject = refJnt, prefix = prefix, customTwistBaseObj = customTwistBaseObj )
    
    # hide some objects
    mc.hide( twistRefJntData['refjoint'], twistRefJntData['ikjoint'], twistRefJntData['ikHandle'] )
    
    # make twist joints
    twistJnts = []
    twistJntRad = mc.getAttr( baseJnt + '.radi' ) * 3.0
    
    # create them and parent into base jnt 
    for i in range( twistJointsNumber ):
        
        j = mc.joint( n = '%s%s%d_jnt' % ( prefix, twistPartPrefix, ( i + 1 ) ) )
        mc.setAttr( j + '.radi', twistJntRad )
        mc.parent( j, baseJntObj, r = 1 )
        mc.setAttr( j + '.jo', 0, 0, 0 ) # this will orient the created joint same as base jnt 
        twistJnts.append( j )
    
    # make joints red
    for j in twistJnts:
        
        mc.color( j, ud = 8 )
        
    # get twist joint setup increment information
    jntLen = mc.getAttr( baseJntChild + '.tx' ) # total distance to divide number of  twist joints
    lengthIncrem = jntLen / ( twistJointsNumber - 1 ) # divide number of joints - 1 bcs first one doesn't move
    
    # do some test to get te right values
    twistRotPerc = 1.0 / ( twistJointsNumber - 1 ) * cmp( 0, jntLen )
    startTwistJntNegateVal = 1.0  * cmp( jntLen, 0 )
    
    # test base on hierarchy / for limbs like fore arm or foot twist
    baseJntParents = transform.getParentList( baseJnt )
    if not refJnt in baseJntParents:
        startTwistJntNegateVal = 0
        twistRotPerc = (1.0 / ( twistJointsNumber - 1 ) * cmp( 0, jntLen ) ) * -1.0
    
    # create the multiply divider to multiply the twist value along joints and negate the first one
    rotMultiNode = mc.createNode( 'multiplyDivide', n = prefix + 'TwistRot%d_mdv' % i )
    mc.connectAttr( twistRefJntData['mainGrp'] + '.twist', rotMultiNode + '.input1X' )
    mc.connectAttr( twistRefJntData['mainGrp'] + '.twist', rotMultiNode + '.input1Y' )
    
    mc.setAttr( rotMultiNode + '.input2X', twistRotPerc )
    mc.setAttr( rotMultiNode + '.input2Y', startTwistJntNegateVal )
    
    # place joints along the base joint to child and multiply by twist value
    for i in range( twistJointsNumber ):
        
        if i == 0:
            mc.connectAttr( rotMultiNode + '.outputY', twistJnts[i] + '.rx' )
        else:
            # parent and move twist joint along base and child joints
            mc.parent( twistJnts[i], twistJnts[i - 1] )
            mc.setAttr( twistJnts[i] + '.tx', lengthIncrem )
            
            # connect distributed rotation value
            mc.connectAttr( rotMultiNode + '.outputX', twistJnts[i] + '.rx' )
        
    twistRefJntData['twistjoints'] = twistJnts
    
    return twistRefJntData
    
def makeFromXforms( objects, prefix = 'jntFromXforms' ):
    
    '''
    create joint chain from Xforms (array of transforms)
    NOTE: each joint will be oriented by default
    
    :param objects:list( str ), list of reference objects to provide positions for joints
    :param prefix: str, prefix for naming new joints
    :return: list(str), joint chain list
    '''
    
    positionList = [ mc.xform( obj, q = 1, t = 1, ws = 1 ) for obj in objects ]    
    joints = makeFromPositions( positionList, prefix )
    
    return joints

def makeFromPositions( positionList, prefix = 'jntFromPositions', relativeSpaceObject = '' ):
    
    '''
    create joint chain from world positions (array of lists or tuples, e.g. [ (0,0,0), (1,0,0), (2,0,0)  ])
    NOTE: each joint will be oriented by default
    
    :param positionList: list(x,y,z), list of positions for making joints
    :param prefix: str, prefix for naming new joints
    :param relativeSpaceObject: str, optional, name of object reference for position values to be used locally
    :return: list(str), joint chain list
    '''
    
    joints = []
    
    if relativeSpaceObject:
          
          refGrp = mc.group( n = 'temp_grp', p = relativeSpaceObject, em = True )
    
    mc.select( cl = True )
    
    for i, pos in enumerate( positionList ):
      
      jointName = prefix + str( i + 1 ) + '_jnt'
      
      p = pos
      
      if relativeSpaceObject:
          
          mc.move( pos[0], pos[1], pos[2], refGrp, os = True, absolute = True )
          p = mc.xform( refGrp, q = True, t = True, ws = True )
      
      joint = mc.joint( p = p, n = jointName )
      
      
      if len( joints ) > 0:
        jointParent = joints[ -1 ]
        mc.joint( jointParent, e = 1, zso = 1, oj = 'xyz', sao = 'yup' )   
    
      joints.append( joint )
    
    
    mc.setAttr( joints[-1] + '.jo', 0, 0, 0 )
    
    if relativeSpaceObject:
        
        mc.delete( refGrp )
    
    
    return joints

def duplicateChain( jointlist, newjointnames = [], prefix = '', suffix = '', keepOrigName = False, inverseScale = True, removeUserAts = True ):
    
    '''
    Duplicate joints in list so that they form a chain
    Procedure goes from highest joint (first in list) down to find lowest joint (last in list)
    Duplicated top joint stays  where it was duplicated
    
    :param jointlist:list (str), joints of chain to be duplicated
    :param newjointnames: list (str), prefixes of new joints (without '_jnt'), which optionally can be provided
    :param prefix: optional, str, in case newjointnames were not provided, this will be used to rename new joints
    :param suffix: optional, str, suffix will be added after base name derived from first duplicated joint with '_jnt' at the end of name
    :param keepOrigName: bool, if True and newjointnames were not passed, keep original name and add chosen prefix or suffix to it
    :param inverseScale: bool, if True, connect scale of parent joint to inverseScale of child joint (Maya does it automaticly when using Joint Tool)
    :param removeUserAts: bool, remove user defined attributes from new joints
    :return: list (str), names of new joints
    '''
    
    # prepare joint names
    
    jointSuffix = '_jnt'
    
    if not prefix:
        
        prefEdit = name.removeSuffix( jointlist[0] )
        prefix = name.removeEndNumbers( prefEdit )
    
    if not newjointnames:
        
        if keepOrigName:
            
            newjointnames = [ '%s%s' % ( prefix, jointlist[i] ) for i in range( len( jointlist ) ) ]
        
        else:
            
            newjointnames = [ '%s%d' % ( prefix, ( i + 1 ) ) for i in range( len( jointlist ) ) ]        
        
        if suffix:
            
            newjointnames = [ n + suffix for n in newjointnames ]
        
        if keepOrigName:
            
            jointSuffix = ''
        
        newjointnames = [ n + jointSuffix for n in newjointnames ]
    
    else:
        
        editnames = [ n + jointSuffix for n in newjointnames ]
        newjointnames = editnames
    
    
    #===========================================================================
    # make joint chain
    #===========================================================================
    
    djointlist = []
    
    currentNs = mc.namespaceInfo( currentNamespace = 1 )
    tempNs = name.getAvailableNamespace( 'duplicateJointsTemp' )
    mc.namespace( add = tempNs )
    
    
    for i, inj in enumerate( jointlist ):
        
        # set namespace to protect new name
        mc.namespace( set = tempNs )
        
        # duplicate object will either keep its root namespace
        # or get protected temporary namespace
        j = mc.duplicate( inj, parentOnly = 1 )[0]
        
        # set namespace back to current
        mc.namespace( set = currentNs )
        
        j = mc.rename( j, newjointnames[i] )
        djointlist.append( j )
        
        # remove any set connections
        connect.removeFromAllSets( j )
        
        if i > 0:
            
            mc.parent( j, djointlist[ -2 ] )
            if inverseScale:
                
                try: mc.connectAttr( djointlist[i - 1] + '.scale', j + '.inverseScale', f = 1 )
                except: pass
    
    # remove temporary namespace
    mc.namespace( rm = tempNs )
    
    #===========================================================================
    # remove user defined attributes
    #===========================================================================
    
    removejlist = []
    if removeUserAts: removejlist = djointlist
    
    for j in removejlist:
        
        attribute.removeUserDefined( j )
        
    
    return djointlist

def makeFromCurveWithOptions( curve, prefix = 'newChain', doIK = 0, doStretchy = 0, numJoints = 5, numJointsFromLength = False, jointLength = 1.0, scalePlug = '', distributeByLength = True, upAxis = 'y', upAxisReverse = False ):
    
    '''
    make joint chain along a curve
    options for spline IK and stretching
    
    @param curve: str, name of curve
    @param prefix: str, prefix for naming new objects
    @param doIK: bool, build IK Spline solver on the joint chain
    @param doStretchy: bool, setup joints to be stretchy using curve to drive their length with optional scalePlug
    @param numJoints: int, number of joints to make
    @param numJointsFromLength: bool, generate number of joints based on jointLength parameter and length of curve
    @param jointLength: float, length of joint, this would be adjusted to fit joints evenly on curve
    @param scalePlug: str, scale plug to compensate joints length usualy by rig or module scale, plug is object.attribute
    @param distributeByLength: bool, distribute joints along curve using length, not parameter, which quarantees more even spacing
    @param upAxis: str, choose which world axis will be used as up axis reference, valid values are: 'x','y','z'
    @param upAxisReverse: bool, this will reverse world up axis if True
    
    @return: list( list(str), str ), 0 - list of joints, 1 - string name of IK spline handle
    '''
    
    joints = makeFromCurve( curve = curve, prefix = prefix, numJoints = numJoints, numJointsFromLength = numJointsFromLength, jointLength = jointLength, distributeByLength = distributeByLength, upAxis = upAxis, upAxisReverse = upAxisReverse )
    
    ik = ''
    if doIK:
        
        ik = mc.ikHandle( pcv = 0, ccv = 0, n = prefix + '_ikh', sj = joints[0] , ee = joints[-1], c = curve, sol = 'ikSplineSolver' )[0]
    
    if doStretchy:
        
        lengthPlug = ''
        stretchyJointChain( joints, curve, lengthPlug, scalePlug, prefix )
    
    
    jointData = [ joints, ik ]
    
    return jointData

def old_makeFromCurve( curve, prefix = 'newChain', numJoints = 5, numJointsFromLength = False, jointLength = 1.0, distributeByLength = True, upAxis = 'y', upAxisReverse = False ):
    
    '''
    make joint chain along a curve
    options for spline IK and stretching
    
    @param curve: str, name of curve
    @param prefix: str, prefix for naming new objects
    @param numJoints: int, number of joints to make
    @param numJointsFromLength: bool, generate number of joints based on jointLength parameter and length of curve
    @param jointLength: float, length of joint, this would be adjusted to fit joints evenly on curve
    @param distributeByLength: bool, distribute joints along curve using length, not parameter, which quarantees more even spacing
    @param upAxis: str, choose which world axis will be used as up axis reference, valid values are: 'x','y','z'
    @param upAxisReverse: bool, this will reverse world up axis if True
    @return: list(str), list of joint chain names
    '''
    
    mPath = mc.createNode( 'motionPath', n = 'joint_mpath' )
    mc.setAttr( mPath + '.fractionMode', distributeByLength )
    
    curveShape = mc.listRelatives( curve, s = 1, f = 1 )[0]
    mc.connectAttr( curveShape + '.worldSpace[0]', mPath + '.geometryPath' )
    mPathNull = mc.group( n = 'jointMotionPath_grp', em = 1 )
    mc.connectAttr( mPath + '.ro', mPathNull + '.ro' )
    mc.connectAttr( mPath + '.allCoordinates', mPathNull + '.t' )
    mc.connectAttr( mPath + '.r', mPathNull + '.r' )
    
    # calculate number of joints from curve length and jointLength parameter value
    if numJointsFromLength:
        
        numJoints = int( mc.arclen( curve ) / jointLength )
    
    par = 0.0
    parInc = 1 / float( numJoints - 1 )
    
    mc.select( cl = 1 )
    joints = []
    
    # set argument for world up axis
    
    upAxisDirectionString = 'up'
    
    if upAxisReverse:
        
        upAxisDirectionString = 'down'
    
    secondaryAxisOrient = upAxis + upAxisDirectionString
    
    # build joints
    
    for i in range( numJoints ):
      
      if i == numJoints - 1: par = 1.0
      
      mc.setAttr( mPath + '.uValue', par )
      pos = mc.getAttr( mPathNull + '.t' )[0]
      
      jointName = '%s%d_jnt' % ( prefix, ( i + 1 ) )
      joint = mc.joint( p = pos, n = jointName )
      
      if i > 0:
        
        lastJoint = joints[ -1 ]
        mc.joint( lastJoint, e = 1, zso = 1, oj = 'xyz', sao = secondaryAxisOrient )
      
      par = par + parInc
      joints.append( joint )
    
    mc.delete( [mPath, mPathNull] )  
    mc.setAttr( joints[-1] + '.jo', 0, 0, 0 )
    
    
    return joints

def makeFromCurve( curve, prefix = 'newChain', numJoints = 5, upAxis = 'y', upAxisReverse = False ):
        
    '''
    make joint chain along a curve
    
    :param curve: str, name of curve
    :param prefix: str, prefix for naming new objects
    :param numJoints: int, number of joints to make
    :param upAxis: str, choose which world axis will be used as up axis reference, valid values are: 'x','y','z'
    :param upAxisReverse: bool, this will reverse world up axis if True
    :return: list(str), list of joint chain names
    '''
    mc.select( cl = 1 )
    
    curveShape = mc.listRelatives( curve, s = 1, f = 1 )[0]
    crvFn = om.MFnNurbsCurve(apiwrap.getDagPath( curveShape ) )
    
    # set argument for world up axis
    
    upAxisDirectionString = 'up'
    
    if upAxisReverse:
        
        upAxisDirectionString = 'down'
    
    secondaryAxisOrient = upAxis + upAxisDirectionString
    
    
    jointsPosition = []
    joints = []
    
    for i in range(numJoints):
        parameter = crvFn.findParamFromLength(crvFn.length() * ( 1.0 / (numJoints - 1) ) * i)
        point = om.MPoint()
        crvFn.getPointAtParam(parameter, point)
        
        jointsPosition.append( [ point.x, point.y, point.z ] )
        
        jointName = '%s%d_jnt' % ( prefix, ( i + 1 ) )
        joint = mc.joint( p = ( point.x, point.y, point.z ), n = jointName )
        
        if i > 0:
            lastJoint = joints[ -1 ]
            mc.joint( lastJoint, e = 1, zso = 1, oj = 'xyz', sao = secondaryAxisOrient )
        
        joints.append( joint )
        
    mc.setAttr( joints[-1] + '.jo', 0, 0, 0 )
        
def stretchyJointChain( joints, curve = '', lengthPlug = '', scalePlug = '', prefix = 'unnamedStretchSetup', useJointScale = False, doIk = False, useCurve = True, stretchAmountPlug = None, stretchOffsetPlug = None ):
    
    '''
    drive joint translateX based on curve length
    - optionally give scale driver plug
    - scale is multiplying joint translateX
    - 3rd returned item is plug for controlling stretch amount, but if it was passed in arguments then it will be the same
    
    @param joints: list(str), joint chain to be stretchy
    @param curve: str, name of curve to drive joint chain length
    @param lengthPlug: str, optional, length plug to replace curve for measuring length
    @param scalePlug: str, scale plug to compensate rig scale, plug is object.attribute
    @param prefix: str, prefix to name new objects
    @param useJointScale: bool, use joint ScaleX attribute to stretch the chain instead of default TranslateX
    @param doIk: bool, setup splineIK solver on given joints
    @param useCurve: bool, switch parameter to enable using curve, otherwise lengthPlug needs to be provided
    @param stretchAmountPlug: str, name of stretch amount plug with range 0-1, with 0 having no stretch, this will be returned as 3rd item in any case
    @param stretchOffsetPlug: str, name of stretch offset plug to offset amount of stretch, this can be useful to make chain shorter or longer
    @return: list( str ), 0 - addDoubleLinear node driving stretch (translate) for all joints, 1 - optional, name of IK handle, 2 - stretch amount plug
    '''
    
    jointScaleAttribute = 'tx'
    
    if useJointScale:
        
        jointScaleAttribute = 'sx'
    
    if useCurve:
        
        curveInfo = mc.arclen( curve, ch = 1 )
        origLen = mc.getAttr( curveInfo + '.arcLength' )
        lengthPlug = curveInfo + '.arcLength'
    
    else:
        
        origLen = mc.getAttr( lengthPlug )
    
    
    
    lenStretch = mc.createNode( 'multiplyDivide', n = prefix + 'Length_md' )
    mc.setAttr( lenStretch + '.op', 2 )
    mc.connectAttr( lengthPlug, lenStretch + '.i1x' )
    mc.setAttr ( lenStretch + '.i2x', origLen )
    
    
    multiNodeOutPlug = lenStretch + '.ox'
    
    # scale compensate
    
    if mc.objExists( scalePlug ):
        
        scale_md = mc.createNode( 'multiplyDivide', n = prefix + 'ScaledMain_md' )
        mc.setAttr( scale_md + '.op', 2 )
        mc.connectAttr( lenStretch + '.ox', scale_md + '.i1x' )
        mc.connectAttr( scalePlug, scale_md + '.i2x' )
        multiNodeOutPlug = scale_md + '.ox'
    
    # add stretch amount node
    stretchAmountNode = mc.createNode( 'blendTwoAttr', n = prefix + 'StretchAmount_bta' )
    mc.setAttr( stretchAmountNode + '.attributesBlender', 1 )
    mc.setAttr( stretchAmountNode + '.input[0]', 1 )
    mc.connectAttr( multiNodeOutPlug, stretchAmountNode + '.input[1]' )
    
    # connect stretch amount plug
    if stretchAmountPlug:
        
        mc.connectAttr( stretchAmountPlug, stretchAmountNode + '.attributesBlender' )
    
    # add stretch offset
    stretchOffsetNode = mc.createNode( 'addDoubleLinear', n = prefix + 'StretchOffset_adl' )
    mc.connectAttr( stretchAmountNode + '.o', stretchOffsetNode + '.i1' )
    
    if stretchOffsetPlug:
        
        mc.connectAttr( stretchOffsetPlug, stretchOffsetNode + '.i2' )
    
    for j in joints:
      
        jBaseName = name.removeSuffix( j )
        
        perJointScalePlug = stretchOffsetNode + '.o'
        
        if not useJointScale:
            
            txMulti = mc.createNode( 'multiplyDivide', n = prefix + jBaseName + '_md' )
            mc.connectAttr( stretchOffsetNode + '.o', txMulti + '.i1x' )
            tx = mc.getAttr( j + '.tx' )
            mc.setAttr( txMulti + '.i2x', tx )
            perJointScalePlug = txMulti + '.ox'
        
        mc.connectAttr( perJointScalePlug, j + '.' + jointScaleAttribute )
    
    returnList = [stretchOffsetNode, None, None]
    
    if doIk:
        
        ik = mc.ikHandle( pcv = 0, ccv = 0, n = prefix + '_ikh', sj = joints[0] , ee = joints[-1], c = curve, sol = 'ikSplineSolver' )[0]
        returnList[1] = ik
    
    returnList[2] = stretchAmountNode + '.attributesBlender'
    
    return returnList

def makeSingleJoint( prefix = 'new', refObject = None, radius = 1.0, refJointRadiusMulti = 0.0, colorIdx = 1, parentObj = None, freezeRotation = True ):
    
    """
    make single joint with option to use reference object and parent
    
    @param prefix: str, prefix for naming new joint
    @param refObject: str, reference object for joint transform
    @param radius: float, radius for new joint
    @param refJointRadiusMulti: float, get radius from multiple of refObject radius if this is joint and multi value other then zero  
    @param colorIdx: int, color index for new joint based on Maya color command -userDefined range
    @param parentObj: str, optional, name of object for parenting new joint
    @param freezeRotation: bool, freeze rotation of new joint so it will be zeroed out and converted to joint orient
    @return: str, name of new joint
    """
    
    # make joint
    jnt = mc.createNode( 'joint', n = prefix + '_jnt' )
        
    # set joint attributes
    jntRadius = radius
    
    if mc.nodeType( refObject ) == 'joint' and not refJointRadiusMulti == 0:
        
        jntRadius = mc.getAttr( refObject + '.radius' ) * refJointRadiusMulti
    
    mc.setAttr( jnt + '.radius', jntRadius )
    mc.color( jnt, ud = colorIdx )
    
    # move joint
    if refObject:
        
        mc.delete( mc.parentConstraint( refObject, jnt ) )
    
    # parent joint
    if parentObj:
        
        jnt = mc.parent( jnt, parentObj )[0]
    
    # freeze rotation
    if freezeRotation:
        
        mc.makeIdentity( jnt, a = True, r = True )
    
    
    return jnt

def orient( jointsList, aimAxis = [1, 0, 0], upAxis = [0, 1, 0], upDir = [0, 1, 0], doAuto = False, verbose = False ):
    
    """
    Do automatic orientation for passed joints
    
    :param jointsList: list (str), joints to be oriented , starting from first item of list to last
    :param aimAxis: list [vector], aim axis for joint to be oriented
    :param upAxis: list [vector], up axis of the joint after orientation
    :param upDir: list[vector], world up vector ... this will be overwrite if doAuto
    :param doAuto: bool, guess the world up vector... this overwrites the upDir
    :return None
    """
    
    if aimAxis == upAxis:
        print '# The AIM and UP axis are the same! Orientation probably wont work!'
    
    prevUp = [0, 0, 0]
    i = 0
    jntListSize = len( jointsList )
    
    for i in range(jntListSize) :
        
        if verbose: print 'i:', i
        # First we need to unparent everything and then store that
        childs = mc.listRelatives( jointsList[i], c = True, type = 'joint' )
        
        if not childs:
            childs = []
        
        if len( childs ) > 0:
            # unparent and get NEW names in case they changed...
            childs = mc.parent( childs, w = True )
        
        # Find parent for later in case we need it.   
        parents =  mc.listRelatives( jointsList[i], p = True ) 
        
        if not parents:
            parent = ""
        else:
            parent = parents[0]
        
        # Now if we have a child joint...aim to that.
        aimTgt = ""
        for child in childs:
            if mc.nodeType( child ) == 'joint':
                aimTgt = child
                break
        if verbose:
            print "DEBUG: JNT = {}, PARENT = {}, AIMTGT = {}".format( jointsList[i], parent, aimTgt )
        
        if aimTgt != "":
            
            upVec = [0, 0, 0]
        
            if doAuto:
                # Now since the first joint we want to match the second orientation
                # we kind of hack the things passed in if it is the first joint
                # ie: If the joint doesn't have a parent...OR if the parent it has
                # has the "same" position as itself...then we use the "next" joints
                # as the up cross calculations                
        
                posJ = mc.xform( jointsList[i], q = True, ws = True, rp = True )
                posP = posJ
                
                if parent != "":
                    
                    posP = mc.xform( parent, q = True, ws = True, rp = True )
                
                tol = 0.0001   #How close to we consider "same"?
                
                if parent == "" or ( abs( posJ[0] - posP[0] ) <= tol and abs( posJ[1] - posP[1] ) <= tol and abs( posJ[2] - posP[2] ) <= tol ):
                    
                    aimChilds = mc.listRelatives( aimTgt, c = True )
                    aimChild = ""
                    
                    if not aimChilds:
                        
                        upVec = [0, 0, 0]
                        
                    else:
                        
                        for child in aimChilds:
                            if mc.nodeType( child ) == 'joint':
                                aimChild = child
                                break  
                    
                        vecA = vector.from2Objects( aimTgt, jointsList[i] )
                        vecB = vector.from2Objects( aimTgt, aimChild )
                        
                        upVec = vector.getCrossProduct( vecA, vecB )
                    
                else:
                                    
                    vecA = vector.from2Objects( jointsList[i], parent )
                    vecB = vector.from2Objects( jointsList[i], aimTgt )
                    
                    upVec = vector.getCrossProduct( vecA, vecB )
                
            if not doAuto or ( upVec[0] == 0 and upVec[1] == 0 and upVec[2] == 0):
                # or else use user set up Dir. if needed
                upVec = upDir
        
            aCons = mc.aimConstraint( aimTgt, 
                                      jointsList[i], 
                                      aim = ( aimAxis[0], aimAxis[1], aimAxis[2] ), 
                                      upVector = ( upAxis[0], upAxis[1], upAxis[2] ),
                                      worldUpVector = ( upVec[0], upVec[1], upVec[2] ),
                                      worldUpType = "vector",
                                      weight = 1.0
                                      )
            mc.delete( aCons )
                
            # Now compare the up we used to the prev one.
            curUp = vector.makeMVector( upVec )
            prevUp = vector.makeMVector( prevUp )
            
            dot = curUp * prevUp # dot product for angle betwen...
            prevUp = vector.makeMVector( upVec ) # store for later
            
            if i > 0 and dot <= 0.0:
                # Adjust the rotation axis 180 if it looks like we've flopped the wrong way!
                mc.xform( jointsList[i], r = True, os = True, ra = ( aimAxis[0] * 180.0, aimAxis[1] * 180.0, aimAxis[2] * 180.0 ) )
                prevUp *= -1
                
            # And now finish clearing out joint axis...
            mc.joint( jointsList[i], e = True, zso = True )
            mc.makeIdentity( jointsList[i], apply = True )
        
        elif parent != "":
            # Otherwise if there is no target, just dup orienation of parent...
            mc.delete( mc.orientConstraint( parent, jointsList[i] ) )
            
            # And now finish clearing out joint axis...
            mc.joint( jointsList[i], e = True, zso = True )
            mc.makeIdentity( jointsList[i], apply = True )
        
        if len( childs ) > 0:
            mc.parent( childs, jointsList[i] )         
        
        i += 1

    # mantain selection
    mc.select( jointsList )

def jointOrientKeyable( joints ):
    
    '''
    :param joints: list(str ), joints to have orientation keyable
    :return: None
    '''
    for j in joints:
        for ax in ['x', 'y', 'z']:
            mc.setAttr( '{}.jo{}'.format( j, ax ), k = 1 )