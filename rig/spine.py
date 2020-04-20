"""
spine @ rig
"""

import string
from itertools import count

import maya.cmds as mc
import maya.OpenMaya as om

from ..base import module
from ..base import control

from . import general

from ..utils import joint
from ..utils import name
from ..utils import attribute
from ..utils import apiwrap

def buildSimpleFk(
        rootJnt,
        spineJoints = None,
        pelvisJnt = None,
        bodyPivotRef = None,
        pelvisPivotRef = None,
        prefix = 'spine',
        ctrlScale = 1.0,
        baseRigData = None,
        useRefPivotsOrientation = True,
        skipLastSpineJoint = True
        ):

    """
    build function to create simple fk spine rig setup
    :param rootJnt: str, parent joint of spine start joint and hips joint
    :param spineJoints: list( str ), names of spine joints starting from top joint
    :param pelvisJnt: str,joint to skin hips area, useful for local FK rotation, often child of root joint
    :param bodyPivotRef: str, this overrides hipJoints, reference object to be used body pivot, if None then startJnt is used
    :param pelvisPivotRef: str, reference object to be used pelvis pivot, if None then startJnt is used
    :param prefix: str, prefix for naming new objects
    :param ctrlScale: float, scale of controls
    :param baseRigData: base rig data returned from rigbase.base build(), top rig object for automatic connecting and parenting of this module
    :param useRefPivotsOrientation: bool, use orientation of reference pivot joints, otherwise only position is used
    :param skipLastSpineJoint: bool, for cases where last spine joint is also end of chain control will not be made for last joint
    :return: dictionary with rig objects
    """


    # module setup
    rigmodule = module.Module( prefix )
    rigmodule.connect( baseRigData )
    rigmodule.parent( baseRigData )
    
    #===========================================================================
    # get control pivots
    #===========================================================================
    
    # get body pivot  object
    
    bodyPivotTrans = rootJnt
    bodyRotateRef = None
    
    if bodyPivotRef:
        
        bodyPivotTrans = bodyPivotRef
        
        if useRefPivotsOrientation:
            
            bodyRotateRef = bodyPivotRef
    
    bodyRotateToObj = None
    
    if useRefPivotsOrientation and bodyPivotRef:
        
        bodyRotateToObj = bodyPivotRef
    
    # get pelvis pivot  object
    
    pelvisPivotTrans = None
    pelvisRotateRef = None
    
    if pelvisJnt:
        
        pelvisPivotTrans = pelvisJnt
        
        if pelvisPivotRef:
            
            pelvisPivotTrans = pelvisPivotRef
            
            if useRefPivotsOrientation:
                
                pelvisRotateRef = pelvisPivotRef
    
    #===========================================================================
    # make controls
    #===========================================================================
    
    body1Ctrl = control.Control( prefix = prefix + 'Body1', translateTo = bodyPivotTrans, rotateTo = bodyRotateToObj, scale = 13 * ctrlScale, shape = 'squareY', ctrlParent = rigmodule.Controls, colorName = 'primary' )
    body2Ctrl = control.Control( prefix = prefix + 'Body2', translateTo = bodyPivotTrans, rotateTo = bodyRotateToObj, scale = 12 * ctrlScale, shape = 'inverseCrown', colorName = 'secondary', ctrlParent = body1Ctrl.C )
    
    mc.parentConstraint( body2Ctrl.C, rootJnt, mo = True )
    
    spineControls = None
    hips1Ctrl = None
    
    if spineJoints:
        
        if skipLastSpineJoint:
            
            spineJntChain = spineJoints[:-1]
        
        else:
            
            spineJntChain = spineJoints[:]
        
        spineControls = general.makeFkControlChain( spineJntChain, prefix = prefix, scale = ctrlScale * 4, connectR = True, connectT = True, prefixSeq = [], ctrlshape = 'circle' )
        mc.parent( spineControls[0].Off, rigmodule.Controls )
        mc.parentConstraint( body2Ctrl.C, spineControls[0].Off, mo = True )
    
    if pelvisJnt:
        
        hips1Ctrl = control.Control( prefix = prefix + 'Hips1', translateTo = pelvisPivotTrans, rotateTo = bodyRotateToObj, scale = 5 * ctrlScale, shape = 'cross', ctrlParent = rigmodule.Controls, colorName = 'midGreen' )
        mc.parentConstraint( body2Ctrl.C, hips1Ctrl.Off, mo = True )
        mc.parentConstraint( hips1Ctrl.C, pelvisJnt, mo = True )
    
    
    return {
            'module':rigmodule,
            'mainGrp':rigmodule.Main,
            'body1Ctrl':body1Ctrl,
            'body2Ctrl':body2Ctrl,
            'spineControls':spineControls,
            'pelvisCtrl':hips1Ctrl,
            'globalSpaceGrp':rigmodule.GlobalSpace,
            'bodySpaceGrp':rigmodule.BodySpace,
            'localSpaceGrp':rigmodule.LocalSpace,
            'toggleGrp':rigmodule.Toggle,
            'settingsGrp':rigmodule.Settings
            }

def buildHybrid(
        rootJnt,
        ikCurve,
        spineJoints = None,
        pelvisJnt = None,
        bodyPivotRef = None,
        pelvisPivotRef = None,
        prefix = 'spine',
        ctrlScale = 1.0,
        baseRigData = None,
        useRefPivotsOrientation = True,
        skipLastSpineJoint = True,
        doSquashStretch = True
        ):
    """
    NOTE: Currently only work with 7 cvs curve
    build function to create simple fk spine rig setup 
    spine must be oriented to X axis as primary axis
    :param rootJnt: str, parent joint of spine start joint and hips joint
    :param ikCurve, str, curve to drive the joints through a ik spline 
    :param spineJoints: list( str ), names of spine joints starting from top joint
    :param pelvisJnt: str,joint to skin hips area, useful for local FK rotation, often child of root joint
    :param bodyPivotRef: str, this overrides hipJoints, reference object to be used body pivot, if None then startJnt is used
    :param pelvisPivotRef: str, reference object to be used pelvis pivot, if None then startJnt is used
    :param prefix: str, prefix for naming new objects
    :param ctrlScale: float, scale of controls
    :param baseRigData: base rig data returned from rigbase.base build(), top rig object for automatic connecting and parenting of this module
    :param useRefPivotsOrientation: bool, use orientation of reference pivot joints, otherwise only position is used
    :param skipLastSpineJoint: bool, for cases where last spine joint is also end of chain control will not be made for last joint
    :return: dictionary with rig objects
    """
    
    # module setup
    rigmodule = module.Module( prefix )
    rigmodule.connect( baseRigData )
    rigmodule.parent( baseRigData )
    
    #===========================================================================
    # get control pivots
    #===========================================================================
    
    # get body pivot  object
    
    bodyPivotTrans = rootJnt
    bodyRotateRef = None
    
    if bodyPivotRef:
        
        bodyPivotTrans = bodyPivotRef
        
        if useRefPivotsOrientation:
            
            bodyRotateRef = bodyPivotRef
    
    bodyRotateToObj = None
    
    if useRefPivotsOrientation and bodyPivotRef:
        
        bodyRotateToObj = bodyPivotRef
    
    # get pelvis pivot  object
    
    pelvisPivotTrans = None
    pelvisRotateRef = None
    
    if pelvisJnt:
        
        pelvisPivotTrans = pelvisJnt
        
        if pelvisPivotRef:
            
            pelvisPivotTrans = pelvisPivotRef
            
            if useRefPivotsOrientation:
                
                pelvisRotateRef = pelvisPivotRef
    
    #===========================================================================
    # make main controls 
    #===========================================================================
    
    body1Ctrl = control.Control( prefix = prefix + 'Body1', translateTo = bodyPivotTrans, rotateTo = bodyRotateToObj, scale = 18 * ctrlScale, shape = 'squareY', ctrlParent = rigmodule.Controls, colorName = 'primary' )
    body2Ctrl = control.Control( prefix = prefix + 'Body2', translateTo = bodyPivotTrans, rotateTo = bodyRotateToObj, scale = 1.0 * ctrlScale, shape = 'inverseCrown', colorName = 'secondary', ctrlParent = body1Ctrl.C )
    
    mc.parentConstraint( body2Ctrl.C, rootJnt, mo = True )
    
    hips1Ctrl = None
    if pelvisJnt:
        
        hips1Ctrl = control.Control( prefix = prefix + 'Hips1', translateTo = pelvisPivotTrans, rotateTo = pelvisRotateRef, scale = 1.2 * ctrlScale, shape = 'cross', ctrlParent = rigmodule.Controls, colorName = 'midGreen' )
        mc.parentConstraint( body2Ctrl.C, hips1Ctrl.Off, mo = True )
        mc.parentConstraint( hips1Ctrl.C, pelvisJnt, mo = True )
    
    #===========================================================================
    #  create IK setup
    #===========================================================================
    # create joints to skin the ik curve
    if spineJoints:
        if skipLastSpineJoint:
            spineJntsChain = spineJoints[:-1]
        else:
            spineJntsChain = spineJoints[:]
    
    startIkDrvJnt, endIkDrvJnt = _createIkDriverJoints( rigmodule, spineJntsChain, prefix )
    
    # create Ik controls
    startIkCtrl = control.Control( prefix = prefix + 'StartIk1', translateTo = spineJntsChain[0], rotateTo = spineJntsChain[0], scale = 5 * ctrlScale, shape = 'circle', ctrlParent = rigmodule.Controls, colorName = 'green' )
    endIkCtrl = control.Control( prefix = prefix + 'EndIk1', translateTo = spineJntsChain[-1], rotateTo = spineJntsChain[-1], scale = 5 * ctrlScale, shape = 'circle', ctrlParent = rigmodule.Controls, colorName = 'green' )
    chestCtrl = control.Control( prefix = prefix + 'Chest1', translateTo = spineJntsChain[-1], rotateTo = spineJntsChain[-1], scale = 5 * ctrlScale, shape = 'triangle', ctrlParent = rigmodule.Controls, colorName = 'green' )
    
    mc.parent( chestCtrl.Off, endIkCtrl.C )
    
    mc.parentConstraint( startIkCtrl.C, startIkDrvJnt, mo = True )
    mc.parentConstraint( endIkCtrl.C, endIkDrvJnt, mo = True )
    
    mc.orientConstraint( chestCtrl.C, spineJntsChain[-1], mo = True )
    
    # create skin from driver joints
    mc.parent( ikCurve, rigmodule.PartsNt )
    ikCurveSkinCluster = mc.skinCluster( [startIkDrvJnt, endIkDrvJnt], ikCurve, n = prefix + 'IkCurve_skc' )[0]
    _setIkCurveSkinWeights( ikCurveSkinCluster, startIkDrvJnt, endIkDrvJnt, ikCurve )
    
    # create ik spline solver
    ikStartJnt = spineJntsChain[0]
    ikEndJnt = spineJntsChain[-1]
    spineIk = mc.ikHandle( n = prefix + '_ikh', sol = 'ikSplineSolver', sj = ikStartJnt, ee = ikEndJnt, c = ikCurve, ccv = 0, parentCurve = 0 )[0]
    mc.parent( spineIk, rigmodule.PartsNt )  
    
    # set advanced twist
    _setAdvancedTwist( spineIk, startIkCtrl, endIkCtrl )
    
    # set squash and stretch setup
    if doSquashStretch:
        _setSquashStretch( spineIk, ikCurve, body1Ctrl, spineJntsChain, prefix, baseRigData )
    
    #===========================================================================
    # create FK setup
    #===========================================================================
    # get middle control position and rotation
    curveShape = mc.listRelatives( ikCurve, s = 1, f = 1 )[0]
    crvFn = om.MFnNurbsCurve(apiwrap.getDagPath( curveShape ) )
    parameter = crvFn.findParamFromLength(crvFn.length() * 0.5)
    point = om.MPoint()
    crvFn.getPointAtParam(parameter, point)
    midPos = [point.x, point.y, point.z]
    
    # create 3 fk controls
    startFkCtrl = control.Control( prefix = prefix + 'Fk1', translateTo = spineJntsChain[0], rotateTo = spineJntsChain[0], scale = 2 * ctrlScale, shape = 'cube', ctrlParent = rigmodule.Controls, colorName = 'primary', lockHideChannels = ['t'] )
    endFkCtrl = control.Control( prefix = prefix + 'Fk3', translateTo = spineJntsChain[-1], rotateTo = spineJntsChain[-1], scale = 2 * ctrlScale, shape = 'cube', ctrlParent = rigmodule.Controls, colorName = 'primary', lockHideChannels = ['t'] )
    midFkCtrl = control.Control( prefix = prefix + 'Fk2', translateTo = spineJntsChain[0], rotateTo = spineJntsChain[0], scale = 2 * ctrlScale, shape = 'cube', ctrlParent = rigmodule.Controls, colorName = 'primary', lockHideChannels = ['t'])
    
    # fix position for mid fk control
    mc.xform( midFkCtrl.Off, ws = True, t = [midPos[0], midPos[1], midPos[2]] )
    
    # make constraints
    mc.parentConstraint( body2Ctrl.C, startFkCtrl.Off, mo = True )
    
    mc.parentConstraint( startFkCtrl.C, startIkCtrl.Off, mo = True )
    mc.parentConstraint( startFkCtrl.C, midFkCtrl.Off, mo = True )
    
    mc.parentConstraint( midFkCtrl.C, endFkCtrl.Off, mo = True )
    
    mc.parentConstraint( midFkCtrl.C, endFkCtrl.Off, mo = True )
    mc.parentConstraint( endFkCtrl.C, endIkCtrl.Off, mo = True )

    return {
            'module':rigmodule,
            'mainGrp':rigmodule.Main,
            'body1Ctrl':body1Ctrl,
            'body2Ctrl':body2Ctrl,
            'ikCtrls':[startIkCtrl, endIkCtrl],
            'fkCtrls':[ startFkCtrl, midFkCtrl, endFkCtrl ],
            'pelvisCtrl':hips1Ctrl,
            'globalSpaceGrp':rigmodule.GlobalSpace,
            'bodySpaceGrp':rigmodule.BodySpace,
            'localSpaceGrp':rigmodule.LocalSpace,
            'toggleGrp':rigmodule.Toggle,
            'settingsGrp':rigmodule.Settings
            }

def _createIkDriverJoints( rigModule, spineJntsChain, prefix ):
    '''
    Creates drivers joints at start and end positions of the spine chain,
    driver joints will be skinned to the ik spline driver curve
    '''
    radiusVal = mc.getAttr( '{}.radius'.format( spineJntsChain[0] ) )
    
    #===========================================================================
    # create start driver joint
    #===========================================================================
    
    startDriverJnt = mc.createNode( 'joint', n = prefix + 'StartIkDriver1_jnt' )
    
    mc.delete( mc.pointConstraint( spineJntsChain[0], startDriverJnt ) )
    mc.parent( startDriverJnt, rigModule.Parts )
    mc.setAttr( '{}.radius'.format( startDriverJnt ), radiusVal * 2.5 )
   
    #===========================================================================
    # create end driver joint
    #===========================================================================
    
    prefix = name.getBase( spineJntsChain[-1] ) 
    endDriverJnt = mc.createNode( 'joint', n = prefix + 'EndIkDriver1_jnt' )
    
    mc.delete( mc.pointConstraint( spineJntsChain[-1], endDriverJnt ) )
    mc.parent( endDriverJnt, rigModule.Parts )
    mc.setAttr( '{}.radius'.format( endDriverJnt ), radiusVal * 2.5 )
    
    return startDriverJnt, endDriverJnt

def _setIkCurveSkinWeights( ikCurveSkinCluster, startIkDrvJnt, endIkDrvJnt, ikCurve ):
    
    '''
    Set the skin cluster weights per vertex in ik curve, 
    Currently only works for 7 cvs curve 
    '''
    '''
    weightsList =[
                1.0,
                0.917,
                0.750,
                0.5,
                0.250,
                0.083,
                0.0
                ]
    '''
    weightsList =[
                1.0,
                1.0,
                0.9,
                0.5,
                0.1,
                0.0,
                0.0
                ]
    
    ikCurveCvs = mc.ls('{}.cv[*]'.format( ikCurve ), fl = True)
    
    if len( ikCurveCvs ) != 7:
        om.MGlobal_displayError( '# {} must have 7 cvs'.format( ikCurve ) )
    
    for i,ikCv in enumerate( ikCurveCvs):
        mc.skinPercent( ikCurveSkinCluster, ikCv, transformValue=[ (startIkDrvJnt, weightsList[i]) ] ) 

def _setAdvancedTwist( spineIk, startIkCtrl, endIkCtrl,  ):
    
    '''
    setup advanced twist setup for ik spline solver
    '''    
    
    mc.setAttr( "{}.dTwistControlEnable".format( spineIk ), 1 )
    mc.setAttr( "{}.dWorldUpType".format( spineIk ), 4 ) # object rotation up start/end
    mc.setAttr( "{}.dForwardAxis".format( spineIk ), 0 ) # positive X
    mc.setAttr( "{}.dWorldUpAxis".format( spineIk ), 0 ) # positive Y
    mc.setAttr( "{}.dWorldUpVectorY".format( spineIk ), 1 )
    mc.setAttr( "{}.dWorldUpVectorEndY".format( spineIk ), 1 )
    mc.connectAttr( "{}.worldMatrix[0]".format( startIkCtrl.C ), "{}.dWorldUpMatrix".format( spineIk ) )
    mc.connectAttr( "{}.worldMatrix[0]".format( endIkCtrl.C ), "{}.dWorldUpMatrixEnd".format( spineIk ) )
    
def _setSquashStretch( spineIk, ikCurve, body1Ctrl, spineJntsChain, prefix, baseRigData ):
    
    '''
    create squash and stretch setup with multiplier option 
    '''
    # add control attributes
    spineAttrsCtrl = body1Ctrl.C
    stretchAt = 'stretch'
    stretchFactorAt = 'stretchFactor'
    
    attribute.addSection( spineAttrsCtrl, sectionName = 'spineAttrs' )
    mc.addAttr( spineAttrsCtrl, at = 'float', ln = stretchAt, min = 0.0, max = 1.0, dv = 1.0, k = True )
    mc.addAttr( spineAttrsCtrl, at = 'float', ln = stretchFactorAt, k = True )
    
    # create curve info and connect curve to get curve length
    crvInfo = mc.createNode( 'curveInfo', n =  prefix + "SquashStretch_cin")
    ikCurveShp = mc.listRelatives( ikCurve, s = True )[0]
    mc.connectAttr( "{}.worldSpace[0]".format( ikCurveShp ), "{}.inputCurve".format( crvInfo ) )
    crvLenVal = mc.getAttr( '{}.arcLength'.format( crvInfo ) )
    
    #===========================================================================
    # stretch
    #===========================================================================
    
    # create multiple divide to fix stretch global scale 
    stretchScaleFixMdv = mc.createNode( 'multiplyDivide', n = prefix + "StretchScaleFix_mdv" )
    mc.setAttr( "{}.operation".format( stretchScaleFixMdv ), 2  ) # divide operation
    mc.connectAttr(  "{}.arcLength".format( crvInfo ), "{}.input1X".format( stretchScaleFixMdv ) )
    mc.setAttr( "{}.input2X".format( stretchScaleFixMdv ), 1 )
    
    if baseRigData:    
        mc.connectAttr( "{}.scaleX".format( baseRigData['global1Ctrl'].C ),  "{}.input2X".format( stretchScaleFixMdv ) )
    
    # create stretch multiply divide
    stretchMdv = mc.createNode( 'multiplyDivide', n = prefix + "Stretch_mdv" )
    mc.setAttr( "{}.operation".format( stretchMdv ), 2 ) # divide operation
    mc.connectAttr( "{}.outputX".format( stretchScaleFixMdv ), "{}.input1X".format( stretchMdv ) )
    mc.setAttr( "{}.input2X".format( stretchMdv ), crvLenVal )
    
    # create blend colors node for stretch on/off switch
    stretchSwitch = mc.createNode( 'blendColors', n = prefix + "Stretch_bcl" )
    mc.connectAttr( "{}.{}".format( spineAttrsCtrl, stretchAt ), "{}.blender".format( stretchSwitch ) )
    mc.connectAttr( "{}.outputX".format( stretchMdv ), "{}.color1R".format( stretchSwitch ) )
    mc.setAttr( "{}.color2R".format( stretchSwitch ), 1 )
    
    mc.connectAttr( "{}.outputR".format( stretchSwitch ), "{}.{}".format( spineAttrsCtrl, stretchFactorAt ) )
    mc.setAttr( "{}.{}".format( spineAttrsCtrl, stretchFactorAt ), l = True )
    
    #===========================================================================
    # squash
    #===========================================================================
    
    # create multiple divide to fix squash global scale 
    squashScaleFixMdv = mc.createNode( 'multiplyDivide', n = prefix + "SquashScaleFix_mdv" )
    mc.setAttr( "{}.operation".format( squashScaleFixMdv ), 2  ) # divide operation
    mc.connectAttr(  "{}.arcLength".format( crvInfo ), "{}.input1X".format( squashScaleFixMdv ) )
    mc.setAttr( "{}.input2X".format( squashScaleFixMdv ), 1 )
    
    if baseRigData:    
        mc.connectAttr( "{}.scaleX".format( baseRigData['global1Ctrl'].C ),  "{}.input2X".format( squashScaleFixMdv ) )
    
    # create squash multiply divide
    squashMdv = mc.createNode( 'multiplyDivide', n = prefix + "squash_mdv" )
    mc.setAttr( "{}.operation".format( squashMdv ), 2 ) # divide operation
    mc.setAttr( "{}.input1X".format( squashMdv ), crvLenVal )
    mc.connectAttr( "{}.outputX".format( squashScaleFixMdv ), "{}.input2X".format( squashMdv ) )
    
    # create blend colors node for squash on/off switch
    squashSwitch = mc.createNode( 'blendColors', n = prefix + "squash_bcl" )
    mc.connectAttr( "{}.{}".format( spineAttrsCtrl, stretchAt ), "{}.blender".format( squashSwitch ) )
    mc.connectAttr( "{}.outputX".format( squashMdv ), "{}.color1R".format( squashSwitch ) )
    mc.setAttr( "{}.color2R".format( squashSwitch ), 1 )
    
    #===========================================================================
    # connect to joints
    #===========================================================================
    
    # connect squash - stretch output to spine joints
    # stretch
    for i, jnt in enumerate( spineJntsChain[:-1] ):
        mc.connectAttr( "{}.outputR".format( stretchSwitch ), "{}.scaleX".format( jnt ) )
    
    #squash     
    # create exponent attribute for squash values and connect it
    
    alphabetList = list(string.ascii_uppercase )
    
    # get squash able joints without start joint since start joint should have exponent 0.0 by default
    squashableJnts = spineJntsChain[1:-1]
    squashableJntsLen = len( squashableJnts )
    n = int(squashableJntsLen / 3)
    
    # make 3 chunks of joints to assign default exponent values
    finalList = [ squashableJnts [i * n:(i + 1) * n] for i in range((len(squashableJnts) + n - 1) // n ) ] 
    
    # final 4 length list with spine1_jnt as first index
    finalList.insert(0, [ spineJntsChain[0] ] )
    exponentValues = [ 0.0, 1.25, 1.5, 1.25 ]
    
    # create and connect the exponent for squash joints
    for jnt, exp in zip( finalList, exponentValues ):
        
        for j in jnt:
            
            # add exponent attr
            prefix = name.removeSuffix(j)
            exponentAt = "squashExp_{}".format( prefix )
            mc.addAttr( spineAttrsCtrl, at = 'float', ln = exponentAt, dv = exp, k = True )
            
            # create and connect exponent multiply divide
            squashExpMdv = mc.createNode( 'multiplyDivide', n = prefix + "SquashExp_mdv" )
            mc.setAttr( "{}.operation".format( squashExpMdv ), 3 ) # power operation
            mc.connectAttr( "{}.outputR".format( squashSwitch ),  "{}.input1X".format( squashExpMdv ) )
            mc.connectAttr( "{}.{}".format( spineAttrsCtrl, exponentAt ), "{}.input2X".format( squashExpMdv ) )
            mc.connectAttr( "{}.outputX".format( squashExpMdv ), "{}.scaleY".format( j ) )
            mc.connectAttr( "{}.outputX".format( squashExpMdv ), "{}.scaleZ".format( j ) )
        
    
        

        






