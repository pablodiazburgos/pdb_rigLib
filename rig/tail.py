"""
module for tails, tentacles , aerial kind of stuffs
"""

#TODO: deep study of spine module

import maya.cmds as mc
import pymel.core as pm

from ..utils import constraint
from ..utils import joint
from ..utils import vector
from ..utils import curve
from ..utils import transform
from ..utils import attribute
from ..utils import name
from ..utils import matrix
from ..utils import anim
from ..utils import connect
from ..utils import shape

from ..base import module
from ..base import control

from . import general

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
            localToggle = False,
            rootCtrlShape = 'inverseCrown',
            rootCtrlColor = 'orange'
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
    :param rootCtrlShape: str, shape for root control
    :param rootCtrlColor: str, color for root control
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
    
    rootCtrl = control.Control( prefix = prefix + 'Root', shape = rootCtrlShape, colorName = rootCtrlColor, translateTo = ikjoints[0], scale = ctrlScale * 4, ctrlParent = rigmodule.Controls, lockHideChannels = ['rz'] )
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

def _buildDuplicateChain( ikjoints, rigmodule, prefix, connectWithDriver = False, radiusMulti = 1.5, parentObj = None ):
    
    """
    make duplicate chain
    """
    
    newChain = joint.duplicateChain( jointlist = ikjoints, prefix = prefix )
    
    # adjust radius size
    origRadius = mc.getAttr( ikjoints[0] + '.radius' )
    [ mc.setAttr( j + '.radius', origRadius * radiusMulti ) for j in newChain ]
    
    # connect joints
    if connectWithDriver:
        
        for i, ( ikj, fkj ) in enumerate( zip( ikjoints, newChain ) ):
            
            if i == 0:
                
                mc.parentConstraint( ikj, fkj, mo = True )
            
            else:
                            
                mc.connectAttr( ikj + '.t', fkj + '.t' )
                mc.connectAttr( ikj + '.r', fkj + '.r' )
                mc.connectAttr( ikj + '.ro', fkj + '.ro' )
    
    # parent joint chain
    if parentObj:
        
        mc.parent( newChain[0], parentObj )
    
    
    return newChain     
    
def _makeTailIkControls( rootCtrl, cvs, prefix, scale, rigmodule ):
    
    '''
    make main IK controls
    '''
    
    # make controls
    
    ikControls = []
    
    for i in range( 1, len( cvs ) ):

        cvpos = mc.xform( cvs[i], q = 1, t = 1, ws = 1 )
        tempPosGrp = mc.group( n = prefix + 'tempPosReference_grp', w = True, em = True )
        mc.xform( tempPosGrp, t = ( cvpos[0], cvpos[1], cvpos[2] ) )
        cvCtrl = control.Control( prefix = prefix + 'Ik%d' % i, moveTo = tempPosGrp, shape = 'cube', lockHideChannels = ['r'], scale = scale * 4, ctrlParent = rootCtrl.C )
        ikControls.append( cvCtrl )
        rigmodule.connectIkFk( cvCtrl.Off + '.v' )
        
        mc.delete( tempPosGrp )
    
    # make connection lines between controls
    
    conlineGrp = mc.group( n = prefix + 'IkControlsConLines_grp', p = rigmodule.Controls, em = 1 )
    rigmodule.connectIkFk( conlineGrp + '.v' )
    
    for i in range( 1, len( cvs ) - 1 ):
        
        ctrlA = ikControls[i - 1]
        if i == 0: ctrlA = rootCtrl
        conline = curve.makeConnectionLine( ctrlA.C, ikControls[i].C, prefix = '%sIkCtrlConLine%d' % ( prefix, ( i + 1 ) ) )
        mc.parent( conline, conlineGrp )
        
    return ikControls
    
def _makeCurveForSubControls( prefix, ikBaseCurve, curveCvs ):
    
    # double density of curve CVs
    
    subControlsNum = ( len( curveCvs ) * 2 ) - 4
    baseCurveCVpositions = curve.getCVpositions( ikBaseCurve )
    subCurve = mc.duplicate( ikBaseCurve, n = prefix + '_sub_crv' )[0]
    
    mc.rebuildCurve( subCurve, rebuildType = 0, spans = subControlsNum, degree = 3, ch = 0, replaceOriginal = True )
    
    subCurveCvs = mc.ls( subCurve + '.cv[*]', fl = 1 )
    
    # move CVs to mid positions
    subCurveCVpositions = []
    
    for i in range( len( subCurveCvs ) ):
        
        if i > 0 and ( i + 1 ) % 2 == 0:
            
            nextIdx = ( i + 1 ) / 2
            prevIdx = nextIdx - 1
            
            nextPosVec = vector.makeMVector( baseCurveCVpositions[ nextIdx ] )
            prevPosVec = vector.makeMVector( baseCurveCVpositions[ prevIdx ] )
            midPosVec = ( nextPosVec + prevPosVec ) / 2.0
            
            subCurveCVpositions.append( [ midPosVec.x, midPosVec.y, midPosVec.z ] )
        
        else:
            
            baseIdx = i / 2
            subCurveCVpositions.append( baseCurveCVpositions[ baseIdx ] )
    
    for i in range( len( subCurveCvs ) ):
        
        mc.xform( subCurve + '.cv[%d]' % i, t = subCurveCVpositions[i], ws = True )
    
    
    return subCurve

def old_makeTailIkSubControls( rootCtrl, cvs, prefix, scale, rigmodule ):
    
    '''
    make sub IK controls
    '''
    
    # make controls
    
    controlsPartGrp = mc.group( n = prefix + 'SubControls_grp', em = 1, p = rootCtrl.C )
    secondaryVisCtrlAt = 'subControlsVis'
    mc.addAttr( rootCtrl.C, ln = secondaryVisCtrlAt, k = True, min = 0, max = 1, dv = 0 )
    mc.connectAttr( '{}.{}'.format( rootCtrl.C, secondaryVisCtrlAt ), controlsPartGrp + '.v' )
    
    ikControls = []
    
    for i in range( 1, len( cvs ) ):
        
        cvpos = mc.xform( cvs[i], q = 1, t = 1, ws = 1 )
        tempPosGrp = mc.group( n = prefix + 'tempPosReference_grp', w = True, em = True )
        mc.xform( tempPosGrp, t = ( cvpos[0], cvpos[1], cvpos[2] ) )
        cvCtrl = control.Control( prefix = prefix + 'IkSub%d' % i, moveTo = tempPosGrp, lockHideChannels = ['r'], shape = 'squareZ', colorName = 'green', scale = scale * 3, ctrlParent = controlsPartGrp )
        ikControls.append( cvCtrl )
        
        mc.delete( tempPosGrp )
    
    # make connection lines between controls
    
    conlineGrp = mc.group( n = prefix + 'IkSubControlsConLines_grp', p = rigmodule.Controls, em = 1 )
    rigmodule.connectIkFk( conlineGrp + '.v' )
    
    for i in range( 1, len( cvs ) - 1 ):
        
        ctrlA = ikControls[i - 1]
        if i == 0:
            
            ctrlA = rootCtrl
        
        conline = curve.makeConnectionLine( ctrlA.C, ikControls[i].C, prefix = '%sIkSubCtrlConLine%d' % ( prefix, ( i + 1 ) ) )
        mc.parent( conline, conlineGrp )
        
    return ikControls

def _makeTailIkSubControls( toggleCtrl, cvs, prefix, scale, rigmodule ):
    
    '''
    make sub IK controls
    '''
    
    # make controls
    
    controlsPartGrp = mc.group( n = prefix + 'SubControls_grp', em = 1, p = rigmodule.Controls )
    secondaryVisCtrlAt = 'subControlsVis'
    mc.addAttr( toggleCtrl.C, ln = secondaryVisCtrlAt, k = True, min = 0, max = 1, dv = 0 )
    mc.connectAttr( '{}.{}'.format( toggleCtrl.C, secondaryVisCtrlAt ), controlsPartGrp + '.v' )
    
    ikControls = []
    
    for i in range( 1, len( cvs ) ):
        
        cvpos = mc.xform( cvs[i], q = 1, t = 1, ws = 1 )
        tempPosGrp = mc.group( n = prefix + 'tempPosReference_grp', w = True, em = True )
        mc.xform( tempPosGrp, t = ( cvpos[0], cvpos[1], cvpos[2] ) )
        cvCtrl = control.Control( prefix = prefix + 'IkSub%d' % i, moveTo = tempPosGrp, lockHideChannels = ['r'], shape = 'squareY', colorName = 'green', scale = scale * 3, ctrlParent = controlsPartGrp )
        ikControls.append( cvCtrl )
        
        mc.delete( tempPosGrp )
    
    # make connection lines between controls
    
    conlineGrp = mc.group( n = prefix + 'IkSubControlsConLines_grp', p = rigmodule.Controls, em = 1 )
    mc.connectAttr( controlsPartGrp + '.v', conlineGrp + '.v' )
    
    for i in range( 1, len( cvs ) - 1 ):
        
        ctrlA = ikControls[i - 1]
        if i == 0:
            
            ctrlA = rigmodule.LocalSpace
            conline = curve.makeConnectionLine( ctrlA, ikControls[i].C, prefix = '%sIkSubCtrlConLine%d' % ( prefix, ( i + 1 ) ) )

        else:
            
            conline = curve.makeConnectionLine( ctrlA.C, ikControls[i].C, prefix = '%sIkSubCtrlConLine%d' % ( prefix, ( i + 1 ) ) )
            mc.parent( conline, conlineGrp )
            
    return ikControls
    
def _attachControlsToCurve( controls, ikAttachCurve, rigmodule ):
    
    '''
    attach position of controls to curve
    '''
    
    controlObjs = [ c.Off for c in controls ]
    worldGrps = constraint.pointConstraintToCurve( ikAttachCurve, controlObjs )
    
    mc.parent( worldGrps, rigmodule.PartsNt )    

def _buildTwistUpVectorControl( startJnt, endJnt, rigmodule, prefix, ctrlScale ):
    
    '''
    build control for changing twist up vector
    '''
    
    upVectorCtrl = control.Control( prefix = '%sTwistUpVector' % prefix, lockHideChannels = ['t', 'ry', 'rz'], moveTo = endJnt, shape = 'circleX', scale = ctrlScale * 6.5, ctrlParent = rigmodule.Controls, colorName = 'orange' )
    rigmodule.connectIkFk( upVectorCtrl.Off + '.v' )
    
    return upVectorCtrl

def _buildTwistSetup( rootCtrl, ikjoints, skinJoints, twistJoints, ikcurve, curveCvs, upVectorCtrl, rigmodule, prefix, ctrlScale, chainStretchAmountPlug ):
    
    '''
    make twist controls along the tail joints
    '''
    
    twistControls = []
    cvposlist = []
    numCvs = len( curveCvs )
    
    twistControlsGrp = mc.group( n = '%sControls_grp' % prefix, em = 1, p = rigmodule.Controls )
    #rigmodule.connectIkFk( twistControlsGrp + '.v' )
    
    twistVisCtrlAt = 'twistControlsVis'
    mc.addAttr( rootCtrl.C, ln = twistVisCtrlAt, k = True, min = 0, max = 1, dv = 0 )
    mc.connectAttr( '{}.{}'.format( rootCtrl.C, twistVisCtrlAt ), twistControlsGrp + '.v' )
    
    
    incrementsData = joint.jointsMaxIncrementWithRemainder( ikjoints, numCvs )
    jointIndeces = incrementsData[0]
    jointIncrements = incrementsData[1]
    
    
    # ===================================================
    # build controls
    # ===================================================
    
    twistAmountIncrem = 1.0 / ( numCvs - 1 )
    twistAmount = twistAmountIncrem    
    twistAmounts = []
    
    for i in range( numCvs ):
        
        if i == 0:
            
            refctrlGrp = mc.group( n = '%sRefStart_grp' % prefix, em = 1, p = ikjoints[0] )
            mc.parent( refctrlGrp, twistControlsGrp )
            twistAmounts.append( 0 )
            continue
        
        if i == numCvs - 1: twistAmount = 1
        
        twistCtrl = control.Control( prefix = '%s%d' % ( prefix, i ), lockHideChannels = ['t', 'ry', 'rz'], moveTo = ikjoints[jointIndeces[i]], shape = 'arrow', scale = ctrlScale * 4, ctrlParent = twistControlsGrp, colorName = 'green' )
        mc.addAttr( twistCtrl.C, ln = 'tipTwistAmount', min = 0, max = 1, dv = twistAmount, k = 1 )
        
        twistAmounts.append( twistAmount )
        twistControls.append( twistCtrl )
        
        twistAmount += twistAmountIncrem
    
    
    controlObjects = [refctrlGrp] + twistControls
    
    # ===================================================
    # attach twist controls
    # ===================================================
    
    # build another ik spline joints, but running opposite
    
    opsikjoints = _buildTwistSetupOppositeIkJoints( ikjoints, ikcurve, prefix, rigmodule, chainStretchAmountPlug )
    opjointsOriGrp = mc.group( n = '%sOposJointOri_grp' % prefix, em = 1, p = opsikjoints[-1] )
    mc.parent( opjointsOriGrp, mc.listRelatives( ikjoints[0], p = 1 )[0] )
    mc.parent( opsikjoints[-1], opjointsOriGrp )
    opjointrootOriConst = mc.orientConstraint( upVectorCtrl.C, opjointsOriGrp, mo = 1 )[0]
    mc.setAttr( opjointrootOriConst + '.interpType', 2 )
    
    # attach twist controls
    
    for i in range( numCvs ):
        
        if i == 0:
            
            mc.parentConstraint( ikjoints[jointIndeces[i]], controlObjects[i], sr = ['x', 'y', 'z'] )
            continue
        
        mc.parentConstraint( ikjoints[jointIndeces[i]], controlObjects[i].Off, sr = ['x', 'y', 'z'] )
        
        _buildTwistSetupCtrlAim( controlObjects[i], ikjoints[jointIndeces[i]], ikjoints[jointIndeces[i] - 1], opsikjoints[jointIndeces[i]], twistAmounts[i], controlObjects[i].C + '.tipTwistAmount', upVectorCtrl, '%sTwist%d' % ( prefix, ( i + 1 ) ), rigmodule )
    
    
    # ===================================================
    # build twist and curl chains
    # ===================================================
    
    twistGroups = []
    curlGroups = []
    
    for i in range( len( ikjoints ) ):
        
        curlGrp = mc.group( n = prefix + 'Curl%d_grp' % ( i + 1 ), p = twistJoints[i], em = True )
        twistGrp = mc.group( n = prefix + 'Main%d_grp' % ( i + 1 ), p = curlGrp, em = True )
        
        if not i == ( len( ikjoints ) - 1 ):
            
            mc.parent( twistJoints[i + 1], curlGrp )
        
        curlGroups.append( curlGrp )
        twistGroups.append( twistGrp )
        
        # constraint skin joints to the null
        mc.parentConstraint( twistGrp, skinJoints[i], mo = True )
    
    #===========================================================================
    # setup curl rotation
    #===========================================================================
    
    _setupCurlChainRotation( upVectorCtrl, curlGroups, prefix )
    
    # ===================================================
    # interpolate inbetween twist joints rotation
    # ===================================================
    
    for i in range( numCvs ):
        
        if i == 0:
            
            continue
        
        # setup main joint twist
        
        currentJntIdx = jointIndeces[i]
        
        mc.orientConstraint( controlObjects[i].C, twistGroups[currentJntIdx], sk = ['y', 'z'] )
        
        # setup inbetween joint twist
        
        prevJntIdx = jointIndeces[i - 1]
        
        if jointIncrements[i] < 2:
            
            continue  # skip if there are no joints between
        
        currentJntWeightIncrem = 1.0 / jointIncrements[i]
        currentJntWeight = currentJntWeightIncrem
        
        for idx in range( prevJntIdx + 1, currentJntIdx ):            
            
            # setup rotation blend
            
            rotationBlend = mc.createNode( 'blendTwoAttr', n = '%sTwistBlendJntRot%d_bta' % ( prefix, idx ) )
            
            mc.setAttr( rotationBlend + '.attributesBlender', currentJntWeight )
            mc.connectAttr( twistGroups[prevJntIdx] + '.rx', rotationBlend + '.i[0]' )
            mc.connectAttr( twistGroups[currentJntIdx] + '.rx', rotationBlend + '.i[1]' )
            mc.connectAttr( rotationBlend + '.o', twistGroups[idx] + '.rx' )
            
            # add increment
            
            currentJntWeight += currentJntWeightIncrem
    
    
    return [refctrlGrp] + twistControls

def _buildTwistSetupOppositeIkJoints( ikjoints, ikcurve, prefix, rigmodule, chainStretchAmountPlug ):
    
    '''
    build another ik spline solution, but running opposite
    '''
    
    # make opposite joint chain
    
    jointparents = mc.listRelatives( ikjoints[0], p = 1 )
    jointparent = None
    
    if jointparents:
        
        jointparent = jointparents[0]
    
    else:
        
        jointparent = rigmodule.Joints
        mc.parent( ikjoints[0], jointparent )
    
    
    opjointnames = [ prefix + 'Opposite%d' % ( i + 1 ) for i in range( len( ikjoints ) ) ]
    opjointroot = joint.duplicateChain( ikjoints, opjointnames )[0]
    
    # unparent joints, otherwise reroot function would mess up the hierarchy
    
    mc.parent( opjointroot, w = 1 )
    opjoints = joint.getlist( opjointroot )
    mc.reroot( opjoints[-1] )
    mc.parent( opjoints[-1], jointparent )
    
    opjoints = joint.getlist( opjoints[-1] )
    opjointsrev = opjoints[:]
    opjointsrev.reverse()
    
    # reverse curve
    opcurve = mc.duplicate( ikcurve, n = prefix + 'Opposite_crv' )[0]
    mc.blendShape( ikcurve, opcurve, n = prefix + 'OppositeCrv_bs', w = ( 0, 1 ) )
    mc.reverseCurve( opcurve, ch = 1 )
    
    # apply ik solver
    # root on curve is off, so root can be constrained to end of main joint chain
    opchainIk = mc.ikHandle( rootOnCurve = 0, n = prefix + 'Opposite_ikh', sol = 'ikSplineSolver', sj = opjoints[0], ee = opjoints[-1], c = opcurve, ccv = 0, parentCurve = 0 )[0]
    rigmodule.connectIkFk( opchainIk + '.ikBlend' )
    mc.parent( opchainIk, rigmodule.PartsNt )
    
    # connect opposite joint chain visibility
    rigmodule.connectPartsVis( opjoints[0] )
    
    # attach opposite joints to main joints
    mc.pointConstraint( ikjoints[-1], opjoints[0] )
    
    # add stretch
    chainStretchRes = joint.stretchyJointChain( opjointsrev[:-1], curve = opcurve, scalePlug = rigmodule.getModuleScalePlug(), prefix = prefix + 'ChainStretchOpposite', useCurve = True, stretchAmountPlug = chainStretchAmountPlug )
    
    return opjointsrev

def _buildTwistSetupCtrlAim( twistCtrl, ikjoint, ikjointaim, opjoint, wtAmount, wtAtr, upVectorCtrl, prefix, rigmodule ):
    
    '''
    create aim constraint with blending up vector between parent joint and Up Vector ctrl
    '''
    
    # make upVectorGrp to match ref joint orientation
    
    upVectorGrp = mc.group( n = prefix + 'UpVector_grp', em = 1, p = ikjoint )
    mc.parent( upVectorGrp, rigmodule.PartsNt )
    mc.orientConstraint( upVectorCtrl.C, upVectorGrp, mo = 1 )
    
    # use wtAddMatrix node to blend input ref objects
    # and feed that to twist control up vector
    
    mxblendnode = matrix.makeBlendMatrices( [ opjoint, ikjoint ], prefix = prefix )
    
    mc.connectAttr( wtAtr, mxblendnode + '.wtMatrix[0].weightIn' )
    
    minusNode = mc.createNode( 'plusMinusAverage', n = prefix + 'WeightDifer_pma' )
    mc.setAttr( minusNode + '.operation', 2 )
    mc.setAttr( minusNode + '.i1[0]', 1 )
    mc.connectAttr( wtAtr, minusNode + '.i1[1]' )
    mc.connectAttr( minusNode + '.o1', mxblendnode + '.wtMatrix[1].weightIn' )
    
    # make aim constraint
    aimconst = mc.aimConstraint( ikjointaim, twistCtrl.Off, aim = [-1, 0, 0], u = [0, 0, 1], wu = [0, 0, 1], wut = 'objectrotation' )[0]
    mc.connectAttr( mxblendnode + '.matrixSum', aimconst + '.worldUpMatrix', f = 1 )
    
def _setupCurlChainRotation( ctrl, objectChain, prefix ):
    
    """
    setup curl rotation
    """
    
    # add attributes
    curlYAt = 'curlY'
    curlZAt = 'curlZ'
    angleMultiAt = 'angleMulti'
    biasPosAt = 'biasPos'
    biasAngleYAt = 'biasAngleY'
    biasAngleZAt = 'biasAngleZ'
    biasMultiValAt = 'biasMultiVal'
    attribute.addSection( ctrl.C )
    
    maxRange = 100
    attributeSpan = 10
    numObjects = float( len( objectChain[1:-1] ) )
    spanIncrement = ( maxRange - attributeSpan ) / numObjects
    startAngle = 90
    endAngle = 30
    angleIncrement = ( startAngle - endAngle ) / numObjects
    
    biasMaxRange = 10
    biasMinFalloffJoints = 6.0
    biasFalloffRatio = biasMinFalloffJoints / numObjects
    biasFalloff = biasFalloffRatio * biasMaxRange
    if biasFalloff > biasMaxRange:
        
        biasFalloff = biasMaxRange
        
    biasIncrem = biasMaxRange / ( numObjects - 1 )
    
    mc.addAttr( ctrl.C, ln = angleMultiAt, at = 'float', min = -2, max = 2, k = True, dv = 1 )
    mc.addAttr( ctrl.C, ln = biasPosAt, at = 'float', min = 0, max = biasMaxRange, k = True, dv = 1 )
    mc.addAttr( ctrl.C, ln = biasAngleYAt, at = 'float', k = True, dv = 0 )
    mc.addAttr( ctrl.C, ln = biasAngleZAt, at = 'float', k = True, dv = 0 )
    
    curlMultiNodes = []
    
    for at in [curlYAt, curlZAt]:
        
        mc.addAttr( ctrl.C, ln = at, at = 'float', min = -maxRange, max = maxRange, k = True )
        nodePrefix = prefix + curlYAt.capitalize()
        curlAngleMultiNode = mc.createNode( 'multDoubleLinear', n = nodePrefix + 'AngleMulti_mdl' )
        mc.connectAttr( ctrl.C + '.' + angleMultiAt, curlAngleMultiNode + '.i1' )
        mc.connectAttr( ctrl.C + '.' + at, curlAngleMultiNode + '.i2' )
        curlMultiNodes.append( curlAngleMultiNode )
    
    
    driverValue = 0
    angleMaxValue = startAngle
    biasParam = 0
    
    # reverse objects order to start from last one
    objectChain.reverse()
    
    for i, obj in enumerate( objectChain[1:-1] ):
        
        driverValues = [ -driverValue - attributeSpan, -driverValue, driverValue, driverValue + attributeSpan ]
        drivenValues = [ -angleMaxValue, 0, 0, angleMaxValue ]
        
        # make bias driver node
        biasDriverVals = [biasParam - biasFalloff, biasParam, biasParam + biasFalloff]
        biasDrivenVals = [0, 1, 0]
        mc.addAttr( obj, ln = biasMultiValAt, at = 'float', k = False )
        anim.setDrivenKey( ctrl.C + '.' + biasPosAt, obj + '.' + biasMultiValAt, biasDriverVals, biasDrivenVals, intangtype = 'flat', outtangtype = 'flat' )
        
        for at, multiNode, axis, biasAngleAt in zip( [curlYAt, curlZAt], curlMultiNodes, ['y', 'z'], [biasAngleYAt, biasAngleZAt] ):
            
            anim.setDrivenKey( ctrl.C + '.' + at, obj + '.r' + axis, driverValues, drivenValues )
            animNode = mc.listConnections( obj + '.r' + axis )[0]
            
            nodePrefix = prefix + at.capitalize() + '%d' % ( i + 1 )
            
            biasMultiNode = mc.createNode( 'multDoubleLinear', n = nodePrefix + 'BiasMulti_mdl' )
            mc.connectAttr( obj + '.' + biasMultiValAt, biasMultiNode + '.i1' )
            mc.connectAttr( ctrl.C + '.' + biasAngleAt, biasMultiNode + '.i2' )
            
            curlAngleMultiNode = mc.createNode( 'multDoubleLinear', n = nodePrefix + 'AngleMulti_mdl' )
            mc.connectAttr( ctrl.C + '.' + angleMultiAt, curlAngleMultiNode + '.i1' )
            mc.connectAttr( animNode + '.o', curlAngleMultiNode + '.i2' )
            
            angleAddNode = mc.createNode( 'addDoubleLinear', n = nodePrefix + 'AngleAdd_adl' )
            mc.connectAttr( curlAngleMultiNode + '.o', angleAddNode + '.i1' )
            mc.connectAttr( biasMultiNode + '.o', angleAddNode + '.i2' )
            
            connect.disconnect( obj + '.r' + axis )
            mc.connectAttr( angleAddNode + '.o', obj + '.r' + axis )
            
        
        # increment values
        driverValue += spanIncrement
        angleMaxValue -= angleIncrement
        biasParam += biasIncrem

def _createFkIkDuplicateChains(skinJoints, parentObj):
    
    '''
    create a duplicate of bind chain for fk and ik setups
    :return fk and ik joint chains
    '''
    # make duplicate chains for ik and fk
    fkJointNames = [ name.removeSuffix( j ) + 'Fk' for j in  skinJoints  ]
    fkJoints = joint.duplicateChain(  skinJoints , newjointnames = fkJointNames )
    
    ikJointNames = [ name.removeSuffix( j ) + 'Ik' for j in  skinJoints  ]
    ikJoints = joint.duplicateChain(  skinJoints , newjointnames = ikJointNames )
    
    # parent objects
    if parentObj:
        
        mc.parent( ikJoints[0], parentObj )
        mc.parent( fkJoints[0], parentObj )
    else:
        mc.parent(ikJoints[0], w = True)
        mc.parent(fkJoints[0], w = True)
    
    # set some Colors and different radius
    jointRad = mc.getAttr( skinJoints[0] + '.radius' )
    
    fkIkJointList = fkJoints, ikJoints
    newRad = jointRad * 1.3
    jntColor = 22
    for chainJnts in fkIkJointList:
        
        for j in chainJnts:
            mc.setAttr( j + '.radius', newRad )
            mc.setAttr( j + '.ove', 1 )
            mc.setAttr( j + '.ovc', jntColor )
        
        newRad = newRad * 1.3
        jntColor = 13
        
    return fkJoints, ikJoints

def _connectIkFkJoints( bindJnts, fkJoints, ikJoints, rigmodule ):
    
    for bind,fk,ik in zip( bindJnts, fkJoints, ikJoints):
        
        constraintName = mc.parentConstraint( fk, bind, mo = True )[0]
        mc.parentConstraint( ik, bind, mo = True )
        constraintAttr = constraint.getWeightAttrs(constraintName)
        
        rigmodule.connectIkFk( '{}.{}'.format( constraintName, constraintAttr[1] ) )
        rigmodule.connectIkFk( '{}.{}'.format( constraintName, constraintAttr[0] ), reversed = True )


def _createAndPositionTwistLocs( prefix, ikcurve, twistUpVec, ikJoints ):
    
    # create locators for twist reference using pymel
    startIkJnt = pm.PyNode( ikJoints[0] )
    endIkJnt = pm.PyNode( ikJoints[-1] )
    startTwistLoc = pm.spaceLocator( n = '%sTwistRefStart_loc' % prefix )
    endTwistLoc = pm.spaceLocator( n = '%sTwistRefEnd_loc' % prefix )
    
    # get length of curve to multiply by the ref vector
    curveLen = curve.getLength( ikcurve )
    
    # create reference vector based on passed string 
    if twistUpVec == "xAxis":
        refVec = pm.dt.Vector.xAxis
    elif twistUpVec == "xNegAxis":
        refVec = pm.dt.Vector.xNegAxis
    elif twistUpVec == "yAxis":
        refVec = pm.dt.Vector.yAxis
    elif twistUpVec == "yNegAxis":
        refVec = pm.dt.Vector.yNegAxis
    elif twistUpVec == "zAxis":
        refVec = pm.dt.Vector.zAxis
    elif twistUpVec == "zNegAxis":
        refVec = pm.dt.Vector.zNegAxis        
    else:
        raise ValueError("# String passed for 'twistUpVec' argument is not valid ")
        
    # position locators
    refVecExtented = refVec * curveLen
    for loc, jnt in zip( [startTwistLoc, endTwistLoc], [startIkJnt, endIkJnt] ):
        jntPosVec = pm.xform( jnt, q = True, ws = True, t = True )
        loc.setTranslation( jntPosVec  + refVecExtented )
        
        
        
    return [startTwistLoc.name(), endTwistLoc.name()]
    
def _ikSplineTwistSetup( prefix, rootCtrl, tailIkControls, chainIk, ikcurve, ikJoints,  twistUpVec, rigmodule ):
    
    startTwistLoc, endTwistLoc = _createAndPositionTwistLocs( prefix, ikcurve, twistUpVec, ikJoints )
    
    # parent locators
    twistLocsGrp = mc.group( em = True, n = '%sRefTwistLocs_grp', p = rigmodule.Parts )
    mc.parent( startTwistLoc, endTwistLoc, twistLocsGrp )
    
    # active advaced twist attributes from ik solver
    mc.setAttr( '%s.%s' % ( chainIk, 'dTwistControlEnable' ), 1 )
    mc.setAttr( '%s.%s' % ( chainIk, 'dWorldUpType' ), 2 )
    mc.setAttr( '%s.%s' % ( chainIk, 'dForwardAxis' ), 0 )
    mc.setAttr( '%s.%s' % ( chainIk, 'dTwistControlEnable' ), 1 )
    
    # connect locators
    mc.connectAttr( startTwistLoc + '.worldMatrix[0]', chainIk + '.dWorldUpMatrix' )
    mc.connectAttr( endTwistLoc + '.worldMatrix[0]', chainIk + '.dWorldUpMatrixEnd' )
    
    # make constraints
    mc.parentConstraint( rootCtrl.C, startTwistLoc, mo = True, sr = ['x', 'y', 'z'] )
    # unlock last ik control rotation
    attribute.openAllTransformVis( tailIkControls[-1].C,  r = True )
    mc.parentConstraint( tailIkControls[-1].C, endTwistLoc, mo = True, sr = ['x', 'y', 'z'] )

def buildIkFk(
            startJnt,
            endJnt,
            ikcurve,
            subCurve = None,
            prefix = 'tail',
            ctrlScale = 1.0,
            baseRigData = None,
            localToggle = False,
            twistUpVec = "zNegAxis",
            controlsWorldOrient = False,
            stretch = True
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
    :param twistUpVec: str, reference vector to place ik twist locators option are: "xAxis", "xNegAxis", "yAxis", "yNegAxis", "zAxis", "zNegAxis"
    :param controlsWorldOrient: bool, if passed ik controls and subcontrols will have world orient
    :param stretch: bool, create stretch system for ik joints
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
    
    skinJoints = joint.listChainStartToEnd( startJnt, endJnt )
    
    # make Ik - Fk joints
    fkJoints, ikJoints = _createFkIkDuplicateChains( skinJoints, parentObj = rigmodule.Joints )
    
    # connect ik/fk joints bind joints
    _connectIkFkJoints( skinJoints, fkJoints, ikJoints, rigmodule )
    
    # make toggle control
    toggleCtrl = control.Control( prefix = prefix + 'Toggle', lockHideChannels = ['t', 'r'], translateTo = startJnt, rotateTo = startJnt, scale = ctrlScale * 15, colorName = 'secondary', shape = 't', ctrlParent = rigmodule.Controls )
    
    # adjust default toggle control orientation shape
    shape.translateRotate( toggleCtrl.C, rot = [0, 90, 0], localSpace = True )
    
    # duplicate curve for IK spline
    ikBaseCurve = mc.duplicate( ikcurve, n = prefix + 'IkBase_crv' )[0]
    
    # upres provided curve
    origSpansNum = mc.getAttr( ikcurve + '.spans' )
    mc.rebuildCurve( ikcurve, rebuildType = 0, spans = ( origSpansNum + 3 ) * 2, degree = 3, ch = 0, replaceOriginal = True )
    
    # setup IK spline handle
    chainIk = mc.ikHandle( n = prefix + '_ikh', sol = 'ikSplineSolver', sj = ikJoints[0], ee = ikJoints[-1], c = ikcurve, ccv = 0, parentCurve = 0 )[0]
    mc.parent( chainIk, rigmodule.PartsNt )

    # ==============================================
    # main global ctrl
    # ==============================================
    
    rootCtrl =  control.Control( prefix = prefix + 'Root', shape = 'inverseCrown', colorName = 'orange', translateTo = ikJoints[0], rotateTo =  ikJoints[0], scale = ctrlScale * 4, ctrlParent = rigmodule.Controls, lockHideChannels = [] )
    shape.translateRotate( rootCtrl.C, rot = [0, 0, 90], localSpace = True )
    rigmodule.connectIkFk( rootCtrl.Off + '.v' )
    #attribute.addSection( rootCtrl.C )
    
    
    if localToggle:
        rigmodule.customToggleObject( toggleCtrl.C )
    
    # ==============================================
    # IK controls
    # ==============================================
    
    # build main controls
    curveCvs = mc.ls( ikBaseCurve + '.cv[*]', fl = 1 )
    tailIkControls = _makeTailIkControls( rootCtrl, curveCvs, prefix, ctrlScale, rigmodule )
    
    # orient controls
    if not controlsWorldOrient:
        for i in range( len( tailIkControls ) ):
            mc.delete( mc.orientConstraint( rootCtrl.C, tailIkControls[i].Off ) )
                
    # bind curve to controls    
    mc.cluster( curveCvs[0], n = prefix + 'CurveCv0_cls', wn = ( rigmodule.LocalSpace, rigmodule.LocalSpace ), bs = 1 )
    for i in range( 1, len( curveCvs ) ):
        mc.cluster( curveCvs[i], n = prefix + 'CurveCv%d_cls' % ( i + 1 ), wn = ( tailIkControls[i - 1].C, tailIkControls[i - 1].C ), bs = 1 )
    
    # build sub controls
    subCurve = _makeCurveForSubControls( prefix, ikBaseCurve, curveCvs )
    subCurveCvs = mc.ls( subCurve + '.cv[*]', fl = 1 )
    tailIkSubControls = _makeTailIkSubControls( toggleCtrl, subCurveCvs, prefix, ctrlScale, rigmodule )
    _attachControlsToCurve( tailIkSubControls, ikBaseCurve, rigmodule )
    
    # orient sub controls controls
    if not controlsWorldOrient:
        for i in range( len( tailIkSubControls ) ):
            mc.delete( mc.orientConstraint( rootCtrl.C, tailIkSubControls[i].Off ) )
    
    # bind curve to controls
    mc.cluster( subCurveCvs[0], n = prefix + 'SubCurveCv0_cls', wn = ( rigmodule.LocalSpace, rigmodule.LocalSpace ), bs = 1 )
    for i in range( 1, len( subCurveCvs ) ): mc.cluster( subCurveCvs[i], n = prefix + 'SubCurveCv%d_cls' % ( i + 1 ), wn = ( tailIkSubControls[i - 1].C, tailIkSubControls[i - 1].C ), bs = 1 )

    # ==============================================
    # IK controls space switching
    # ==============================================
    '''    
    constraint.makeSwitch( rootCtrl.Off, rigmodule.Toggle, 'allSpaceTrans', ['local', 'global', 'body'], 'parentConstraint', [rigmodule.LocalSpace, rigmodule.GlobalSpace, rigmodule.BodySpace], 1, defaultIdx = 0, skipRotation = True )
    constraint.makeSwitch( rootCtrl.Off, rigmodule.Toggle, 'allSpaceRot', ['local', 'global', 'body'], 'orientConstraint', [rigmodule.LocalSpace, rigmodule.GlobalSpace, rigmodule.BodySpace], 1, defaultIdx = 2 )
    constraint.makeSwitch( upVectorCtrl.Off, rigmodule.Toggle, 'upVectorSpace', ['local', 'global', 'body'], 'orientConstraint', [ikjoints[-1], rigmodule.GlobalSpace, rigmodule.BodySpace], 1, defaultIdx = 2 )
    '''
    # setup tail controls parenting and switching
    
    customSpaceGroups = []
    
    for i in range( len( tailIkControls ) ):
        
        localSpaceObj = tailIkControls[i - 1].C
        defaultVal = 1
        
        if i == 0:
            
            localSpaceObj = rootCtrl.C
            defaultVal = 0
        '''
        customSpaceGrp = transform.makeGroup( prefix = '%sExtraASpace_%d' % ( prefix, i + 1 ) )
        customSpaceGroups.append( customSpaceGrp )
        mc.parent( customSpaceGrp, rigmodule.Parts )
        '''
        constraint.makeSwitch( tailIkControls[i].Off, tailIkControls[i].C, 'space', ['local', 'global'], 'parentConstraint', [localSpaceObj, rigmodule.GlobalSpace], 1, defaultIdx = defaultVal )


    #===========================================================================
    # connect control sub curve to IK curve
    #===========================================================================
    
    mc.wire( ikcurve, w = subCurve, dropoffDistance = ( 0, 1000 ), n = prefix + 'SubCurve_wir' )
    
    #===========================================================================
    # Ik Twist setup
    #===========================================================================
    
    _ikSplineTwistSetup( prefix, rootCtrl, tailIkControls, chainIk, ikcurve, ikJoints,  twistUpVec, rigmodule )
    
    if stretch:
        # add stretching
        stretchAmountAt = 'stretchAmount'
        mc.addAttr( toggleCtrl.C, ln = stretchAmountAt, at = 'float', k = True, min = 0, max = 1, dv = 1 )
        chainStretchAmountPlug = toggleCtrl.C + '.' + stretchAmountAt
        chainStretchRes = joint.stretchyJointChain( ikJoints, curve = ikcurve, scalePlug = rigmodule.getModuleScalePlug(), prefix = prefix + 'ChainStretch', useCurve = True, stretchAmountPlug = chainStretchAmountPlug )
        
    
    
    
    #===========================================================================
    # FK controls
    #===========================================================================
    
    fkChainFixed = fkJoints[:-1]
    #fkPrefixes = [ '%s%s%d' % ( prefix, 'Fk', i + 1 ) for i in range( len( fkJoints ) ) ]
    fkControlsGrp, fkControls = general.smartFkControlChain(
                                            chain = fkChainFixed,
                                            ctrlsNumber = 5,
                                            prefix = prefix + "Fk", 
                                            scale = ctrlScale * 4.0 , 
                                            ctrlshape = 'circleX', 
                                            ctrlColorName = 'primary', 
                                            ctrlParent = rigmodule.Controls 
                                             )
    rigmodule.connectIkFk( fkControlsGrp + '.v', reversed = True )
    #constraint.makeSwitch( fkControls[0].Off, rigmodule.Toggle, 'fkSpace', ['local', 'global', 'body'], 'parentConstraint', [rigmodule.LocalSpace, rigmodule.GlobalSpace, rigmodule.BodySpace], 1, defaultIdx = 0 )
    
    return {
            'module':rigmodule,
            'rootCtrl':rootCtrl,
            'tailIkCtrls':tailIkControls,
            'tailFkCtrls': fkControls,
            'customSpaceGroups':customSpaceGroups,
            'toogleCtrl': toggleCtrl
            }    














