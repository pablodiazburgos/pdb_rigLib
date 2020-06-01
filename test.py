import maya.cmds as mc
from maya import OpenMaya as om

import pymel.core as pm


def mouthInicialPosition():
    
    # create a curve from edge selection to move the mouth surface
    guideCrv = mc.polyToCurve(n = 'tempMouth_crv')[0]
    mc.delete(guideCrv, ch = True)
    guideCrvShape = mc.listRelatives( guideCrv, s = True )[0]

    # define a list of 2 index which are left and right, top, bottom index of vertex ex: mouth_srf.cv[0:3][4]
    Acv = [ 3, 5 ]
    Bcv = [ 2, 6 ]
    Ccv = [ 1, 7 ]
    Dcv = [ 0, 8 ]
    Ecv = [ 11, 9 ]
    SECvs = [4, 10]
    surfaceName = 'mouth_srf'
    
    allCvs = [Acv, Bcv, Ccv, Dcv, Ecv, SECvs]
    
    # create a cluster per span of the surface and keep it in a list in the same order
    clsList = []
    for cvs in allCvs:
        
        tempClsList = []
        cvsA = cvs[0]
        cvsB = cvs[1]
        
        cls1 = mc.cluster( '{}.cv[0:3][{}]'.format(surfaceName, cvsA), n = 'cls{}'.format(cvsA) )[1]
        cls2 = mc.cluster( '{}.cv[0:3][{}]'.format(surfaceName, cvsB), n = 'cls{}'.format(cvsB) )[1]
        
        tempClsList.append(cls1)
        tempClsList.append(cls2)
        
        clsList.append(tempClsList)
   
    crvFn = om.MFnNurbsCurve(getDagPath( guideCrvShape ) )
    numJoints = 7
    
    for i in range(numJoints):
        parameter = crvFn.findParamFromLength(crvFn.length() * ( 1.0 / (numJoints - 1) ) * i)
        point = om.MPoint()
        crvFn.getPointAtParam(parameter, point)
       
        if i == 0 :
            jnt = mc.createNode("joint")
            mc.xform(jnt,t=[point.x,point.y,point.z])
            mc.delete( mc.parentConstraint( jnt, clsList[-1][0] ) )
            mc.delete(jnt)
            
        elif i == 6:
            jnt = mc.createNode("joint")
            mc.xform(jnt,t=[point.x,point.y,point.z])
            mc.delete( mc.parentConstraint( jnt, clsList[-1][1] ) )
            mc.delete(jnt)
            
        else:
            jnt = mc.createNode("joint")
            mc.xform(jnt,t=[point.x,point.y,point.z])
            
            jnt2 = mc.createNode("joint")
            mc.xform(jnt2,t=[point.x * -1,point.y,point.z])

            mc.delete( mc.parentConstraint( jnt, clsList[i - 1][0] ) )
            mc.delete( mc.parentConstraint( jnt2, clsList[i - 1][1] ) )
            
            mc.delete(jnt, jnt2)
        
    mc.delete(surfaceName, ch = True)    
    mc.delete(guideCrv)
        
def getDagPath(node=None):
    sel = om.MSelectionList()
    sel.add(node)
    d = om.MDagPath()
    sel.getDagPath(0, d)
    return d

def buildSimpleIk(
                  chainJoints,
                  chainCurve,
                  prefix = 'tail',
                  ctrlScale = 1.0,
                  colorName = 'primary',
                  fkParenting = True,
                  baseRigData = None,
                  controlsWorldOrient = False,
                  advancedTwist = False,
                  worldUpVector = 'posY',
                  stretch = True
                  ):
    """
    Note: currently setup only works with 7 cvs 3 degree curve and create 5 controls
    later should be improve to work with n numbers of cvs and be able to create n number of controls
    
    :param chainJoints: list( str ), list of chain joints
    :param chainCurve: str, name of chain cubic curve
    :param prefix: str, prefix to name new objects
    :param rigScale: float, scale factor for size of controls
    :param fkParenting: bool, parent each control to previous one to make FK chain
    :param baseRigData: instance of base.module.Base class
    :param controlsWorldOrient: keep orientation of controls to world
    :param worldUpVector: world up vector for local control orient
    :return: dictionary with rig module objects
    """
    
    #===========================================================================
    # module
    #===========================================================================    
    
    rigmodule = module.Module( prefix )
    rigmodule.parent( baseRigData = baseRigData )
    rigmodule.connect( baseRigData = baseRigData )
    
    # make world up vector directory for later use in orient controls
    worldUpVec = { 'posY':(0, 1, 0), 'negY':(0, -1, 0), 'posZ':(0, 0, 1), 'negZ':(0, 0, -1) }
    
    # make IK handle
    
    chainIk = mc.ikHandle( n = prefix + '_ikh', sol = 'ikSplineSolver', sj = chainJoints[0], ee = chainJoints[-1],
                           c = chainCurve, ccv = 0, parentCurve = 0 )[0]
    
    mc.hide( chainIk )
    mc.parent( chainIk, rigmodule.PartsNt )
    
    # make chain curve clusters
    
    chainCurveCVs = mc.ls( chainCurve + '.cv[*]', fl = 1 )
    numChainCVs = len( chainCurveCVs )
    chainCurveClusters = []
    
    for i in range( numChainCVs ):
        
        cls = mc.cluster( chainCurveCVs[i], n = prefix + 'Cluster%d' % ( i + 1 ) )[1]
        chainCurveClusters.append( cls )
    
    mc.hide( chainCurveClusters )
    mc.parent( chainCurve, rigmodule.PartsNt )
    
    # make attach groups
    baseAttachGrp = mc.group( n = prefix + 'BaseAttach_grp', em = 1, p = rigmodule.Parts )
    mc.delete( mc.pointConstraint( chainJoints[0], baseAttachGrp ) )    
    
    # make controls
    chainControls = []
    
    for i in range( numChainCVs ):
        
        if i == 1 or i == numChainCVs -2:
            continue
        
        chainCtrl = control.Control( prefix = prefix +'%d' % ( i + 1 ), shape = 'circleX', colorName = colorName, 
                                     moveTo = chainCurveClusters[i], scale = ctrlScale * 2, ctrlParent = rigmodule.Controls )

        
        chainControls.append( chainCtrl )
    
    # orient controls
    if not controlsWorldOrient:
        for i in range( len( chainControls ) ):
        
            if i + 1 == len( chainControls ):
                mc.delete( mc.orientConstraint( chainJoints[-1], chainControls[i].Off ) )
                break
                
            mc.delete( mc.aimConstraint( chainControls[i + 1].Off, chainControls[i].Off, aimVector = (1, 0, 0),
                              upVector = (0, 1, 0), worldUpType = 'vector', worldUpVector = worldUpVec[worldUpVector] ) )
        
    # lock rotation for middle controls
    if not fkParenting:
        middleControls = chainControls[1:-1]
        for chainCtrl in middleControls:
            for at in ['.rx', '.ry', '.rz']:
                mc.setAttr( chainCtrl.C + at, l = True, k = False, cb = False )
        
    # parent controls
    if fkParenting:
        for i in range( len( chainControls ) ):
            
            if i == 0:
                
                continue
            mc.parent( chainControls[i].Off, chainControls[i - 1].C )
                
    # attach clusters
    for i in range( numChainCVs ):
        if i == 0 or i == 1:
            mc.parent( chainCurveClusters[i], chainControls[0].C )
            continue
        
        if i == numChainCVs - 1 or i == numChainCVs - 2:
            mc.parent( chainCurveClusters[i], chainControls[-1].C )
            continue
    
        mc.parent( chainCurveClusters[i], chainControls[i - 1].C )
    
    # attach controls
    mc.parentConstraint( baseAttachGrp, chainControls[0].Off, mo = 1 )
    
    
    if advancedTwist:   
        mc.setAttr( chainIk + '.dTwistControlEnable', 1 )
        mc.setAttr( chainIk + '.dWorldUpType', 4 )
        mc.connectAttr( chainControls[0].C + '.worldMatrix[0]', chainIk + '.dWorldUpMatrix' )
        mc.connectAttr( chainControls[-1].C + '.worldMatrix[0]', chainIk + '.dWorldUpMatrixEnd' )
    else:
        # add twist attribute
        twistAt = 'twist'
        mc.addAttr( chainControls[-1].C, ln = twistAt, k = 1 )
        mc.connectAttr( chainControls[-1].C + '.' + twistAt, chainIk + '.twist' )
    
    if stretch:
        # add stretching
        stretchAmountAt = 'stretchAmount'
        mc.addAttr( chainControls[0].C, ln = stretchAmountAt, at = 'float', k = True, min = 0, max = 1, dv = 1 )
        chainStretchAmountPlug = chainControls[0].C + '.' + stretchAmountAt
        chainStretchRes = joint.stretchyJointChain( chainJoints[:-1], curve = chainCurve, scalePlug = rigmodule.getModuleScalePlug(), prefix = prefix + 'ChainStretch', useCurve = True, stretchAmountPlug = chainStretchAmountPlug )
        
    
    
    return{
        'module':rigmodule,
        'mainGrp':rigmodule.Main,
        'ctrlGrp':rigmodule.Controls,    
        'controls':chainControls,
        'attachGrp':baseAttachGrp,
        'stretchRes': chainStretchRes
        }

def build( 
            startJnt,
            endJnt,
            ikcurve,
            subCurve = None,
            prefix = 'newtail',
            ctrlScale = 1.0,
            baseRigData = None,
            localToggle = False
            ):
    
    '''
    Note:
    - ikcurve should have less CVs good for animation control
    - subcure should be the same shape and size curve, only with more detail
    
    :param startJnt: str, tail start joint
    :param endJnt: str, tail end joint
    :param ikcurve: str, curve to be used for IK handle setup, main IK controls will be made based on its CVs
    :param subCurve: str, curve to be used for detailed control, created automaticly if None
    :param prefix: str, prefix for naming new objects
    :param ctrlScale: float, scale for size of control objects
    :param baseRigData: rigbase.base build(), base rig data returned from rigbase.base build() to connect visibility channels etc. to the main base
    :param localToggle: bool, add toggle attributes on local Root control
    :return: dictionary with rig objects
    '''
    
    #===========================================================================
    # module
    #===========================================================================
    
    rigmodule = module.Module( prefix )
    rigmodule.parent( baseRigData = baseRigData )
    rigmodule.connect( baseRigData = baseRigData )
        
    # ==============================================
    # curve and IK solver
    # ==============================================
    
    mc.parent( ikcurve, rigmodule.PartsNt )
    
    # make system joints
    skinJoints = joint.listChainStartToEnd( startJnt, endJnt )    
    ikjoints = _buildDuplicateChain( skinJoints, rigmodule, prefix = prefix + 'Sys', connectWithDriver = False, radiusMulti = 0.8, parentObj = None )
    
    # duplicate curve for IK spline
    ikBaseCurve = mc.duplicate( ikcurve, n = prefix + 'IkBase_crv' )[0]
    
    # upres provided curve
    origSpansNum = mc.getAttr( ikcurve + '.spans' )
    mc.rebuildCurve( ikcurve, rebuildType = 0, spans = ( origSpansNum + 3 ) * 2, degree = 3, ch = 0, replaceOriginal = True )
    
    # setup IK spline handle
    chainIk = mc.ikHandle( n = prefix + '_ikh', sol = 'ikSplineSolver', sj = ikjoints[0], ee = ikjoints[-1], c = ikcurve, ccv = 0, parentCurve = 0 )[0]
    rigmodule.connectIkFk( chainIk + '.ikBlend' )
    mc.parent( chainIk, rigmodule.PartsNt )
    
    
    # ==============================================
    # main global ctrl
    # ==============================================
    
    rootCtrl = control.Control( prefix = prefix + 'Root', shape = 'inverseCrown', colorName = 'orange', translateTo = ikjoints[0], scale = ctrlScale * 4, ctrlParent = rigmodule.Controls, lockHideChannels = ['rz'] )
    attribute.addSection( rootCtrl.C )
    
    if localToggle:
        
        rigmodule.customToggleObject( rootCtrl.C )
    
    # connect basic twist
    twistAt = 'twist'
    mc.addAttr( rootCtrl.C, ln = twistAt, at = 'float', k = True )
    mc.connectAttr( rootCtrl.C + '.' + twistAt, chainIk + '.twist' )
    mc.setAttr( chainIk + '.twistType', 3 )  # twist type easeInOut
    
    # add stretching
    stretchAmountAt = 'stretchAmount'
    mc.addAttr( rootCtrl.C, ln = stretchAmountAt, at = 'float', k = True, min = 0, max = 1, dv = 1 )
    chainStretchAmountPlug = rootCtrl.C + '.' + stretchAmountAt
    chainStretchRes = joint.stretchyJointChain( ikjoints, curve = ikcurve, scalePlug = rigmodule.getModuleScalePlug(), prefix = prefix + 'ChainStretch', useCurve = True, stretchAmountPlug = chainStretchAmountPlug )
    
    # ==============================================
    # IK controls
    # ==============================================
    
    # build main controls
    
    curveCvs = mc.ls( ikBaseCurve + '.cv[*]', fl = 1 )
    tailIkControls = _makeTailIkControls( rootCtrl, curveCvs, prefix, ctrlScale, rigmodule )
    
    # bind curve to controls    
    mc.cluster( curveCvs[0], n = prefix + 'CurveCv0_cls', wn = ( rigmodule.LocalSpace, rigmodule.LocalSpace ), bs = 1 )
    for i in range( 1, len( curveCvs ) ):
        
        mc.cluster( curveCvs[i], n = prefix + 'CurveCv%d_cls' % ( i + 1 ), wn = ( tailIkControls[i - 1].C, tailIkControls[i - 1].C ), bs = 1 )
    
    # build sub controls
    subCurve = _makeCurveForSubControls( prefix, ikBaseCurve, curveCvs )
    subCurveCvs = mc.ls( subCurve + '.cv[*]', fl = 1 )
    tailIkSubControls = old_makeTailIkSubControls( rootCtrl, subCurveCvs, prefix, ctrlScale, rigmodule )
    _attachControlsToCurve( tailIkSubControls, ikBaseCurve, rigmodule )
    
    # bind curve to controls
    
    mc.cluster( subCurveCvs[0], n = prefix + 'SubCurveCv0_cls', wn = ( rigmodule.LocalSpace, rigmodule.LocalSpace ), bs = 1 )
    for i in range( 1, len( subCurveCvs ) ): mc.cluster( subCurveCvs[i], n = prefix + 'SubCurveCv%d_cls' % ( i + 1 ), wn = ( tailIkSubControls[i - 1].C, tailIkSubControls[i - 1].C ), bs = 1 )
    
    #===========================================================================
    # make skin and twist joints
    #===========================================================================
    
    twistJoints = _buildDuplicateChain( ikjoints, rigmodule, prefix = prefix + 'Twist', connectWithDriver = True, radiusMulti = 1.2, parentObj = rigmodule.Parts )
    
    mc.hide( ikjoints )
    
    # ==============================================
    # twist controls
    # ==============================================
    
    upVectorCtrl = _buildTwistUpVectorControl( ikjoints[0], ikjoints[-1], rigmodule, prefix, ctrlScale )
    mc.parentConstraint( tailIkControls[-1].C, upVectorCtrl.Off, sr = ['x', 'y', 'z'], mo = 1 )
    
    twistControls = _buildTwistSetup( rootCtrl, ikjoints, skinJoints, twistJoints, ikBaseCurve, curveCvs, upVectorCtrl, rigmodule, prefix + 'Twist', ctrlScale, chainStretchAmountPlug )
    
    # ==============================================
    # IK controls space switching
    # ==============================================
    
    constraint.makeSwitch( rootCtrl.Off, rigmodule.Toggle, 'allSpaceTrans', ['local', 'global', 'body'], 'parentConstraint', [rigmodule.LocalSpace, rigmodule.GlobalSpace, rigmodule.BodySpace], 1, defaultIdx = 0, skipRotation = True )
    constraint.makeSwitch( rootCtrl.Off, rigmodule.Toggle, 'allSpaceRot', ['local', 'global', 'body'], 'orientConstraint', [rigmodule.LocalSpace, rigmodule.GlobalSpace, rigmodule.BodySpace], 1, defaultIdx = 2 )
    constraint.makeSwitch( upVectorCtrl.Off, rigmodule.Toggle, 'upVectorSpace', ['local', 'global', 'body'], 'orientConstraint', [ikjoints[-1], rigmodule.GlobalSpace, rigmodule.BodySpace], 1, defaultIdx = 2 )
    
    # setup tail controls parenting and switching
    
    customSpaceGroups = []
    
    for i in range( len( tailIkControls ) ):
        
        localSpaceObj = tailIkControls[i - 1].C
        defaultVal = 1
        
        if i == 0:
            
            localSpaceObj = rootCtrl.C
            defaultVal = 0
        
        customSpaceGrp = transform.makeGroup( prefix = '%sExtraASpace_%d' % ( prefix, i + 1 ) )
        customSpaceGroups.append( customSpaceGrp )
        mc.parent( customSpaceGrp, rigmodule.Parts )
        
        constraint.makeSwitch( tailIkControls[i].Off, tailIkControls[i].C, 'space', ['local', 'global', 'root', 'extraA'], 'parentConstraint', [localSpaceObj, rigmodule.GlobalSpace, rootCtrl.C, customSpaceGrp], 1, defaultIdx = defaultVal )
    
    #===========================================================================
    # connect control sub curve to IK curve
    #===========================================================================
    
    mc.wire( ikcurve, w = subCurve, dropoffDistance = ( 0, 1000 ), n = prefix + 'SubCurve_wir' )
    
    #===========================================================================
    # FK controls
    #===========================================================================
    
    fkJoints = ikjoints[:-1]
    fkPrefixes = [ '%s%s%d' % ( prefix, 'Fk', i + 1 ) for i in range( len( fkJoints ) ) ]
    fkControls = general.makeFkControlChain( fkJoints, scale = ctrlScale * 6, connectR = True, constraintSeq = [], constraintFirst = True, prefixSeq = fkPrefixes, ctrlshape = 'circleZ' )
    
    mc.parent( fkControls[0].Off, rigmodule.Controls )
    rigmodule.connectIkFk( fkControls[0].Off + '.v', reversed = True )
    
    constraint.makeSwitch( fkControls[0].Off, rigmodule.Toggle, 'fkSpace', ['local', 'global', 'body'], 'parentConstraint', [rigmodule.LocalSpace, rigmodule.GlobalSpace, rigmodule.BodySpace], 1, defaultIdx = 0 )
    
    
    
    return {
            'module':rigmodule,
            'rootCtrl':rootCtrl,
            'twistControls':twistControls,
            'upVectorCtrl':upVectorCtrl,
            'tailIkControls':tailIkControls,
            'customSpaceGroups':customSpaceGroups
            }

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

