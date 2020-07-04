"""
Leg @ rig
"""

#TODO: add fuction for quads when front legs has clavicle

import maya.cmds as mc

from ..base import module
from ..base import control


from ..utils import name
from ..utils import joint
from ..utils import anim
from ..utils import transform
from ..utils import attribute
from ..utils import shape
from ..utils import constraint

from . import limb

def simpleBuild(
        legJoints,
        topToeJoints,
        pvLocator,
        scapulaJnt = '',
        prefix = 'l_leg',
        rigScale = 1.0,
        baseRig = None
        ):

    """
    Module for leg rig creation
    :param legJoints: list( str ), shoulder - elbow - hand - toe - end toe
    :param topToeJoints: list( str ), top metacarpal toe joints
    :param pvLocator: str, reference locator for position of Pole Vector control
    :param scapulaJnt: str, optional, scapula joint, parent of top leg joints
    :param prefix: str, prefix to name new objects
    :param rigScale: float, scale factor for size of controls
    :param baseRig: instance of base.module.Base class
    :return: dictionary with rig module objects
    """

    # make rig module

    rigModule = module.Module( prefix = prefix, baseObj = baseRig )

    # make attach groups

    bodyAttachGrp = mc.group( n = prefix + 'BodyAttach_grp', em = True, p = rigModule.partsGrp )
    baseAttachGrp = mc.group( n = prefix + 'BaseAttach_grp', em = True, p = rigModule.partsGrp )

    # make controls

    if scapulaJnt:

        scapulaCtrl = control.Control( prefix = prefix + 'Scapula', translateTo = scapulaJnt, rotateTo = scapulaJnt,
                                       scale = rigScale * 3, parent = rigModule.controlsGrp, shape = 'sphere',
                                       lockChannels = [ 'ty', 'rx', 'rz', 's', 'v' ])

    footCtrl = control.Control( prefix = prefix + 'Foot', translateTo = legJoints[2], scale = rigScale * 3,
                                parent = rigModule.controlsGrp, shape = 'circleY' )

    ballCtrl = control.Control( prefix = prefix + 'Ball', translateTo = legJoints[3], rotateTo = legJoints[3],
                                       scale = rigScale * 2, parent = footCtrl.C, shape = 'circleZ')

    poleVectorCtrl = control.Control( prefix = prefix + 'PV', translateTo = pvLocator, scale = rigScale,
                                parent = rigModule.controlsGrp, shape = 'sphere' )

    toeIkControls = []

    for topToeJnt in topToeJoints:

        toePrefix = name.removeSuffix( topToeJnt )[:-1]
        toeEndJnt = mc.listRelatives( topToeJnt, ad = True, type = 'joint' )[0]

        toeIkCtrl = control.Control( prefix = toePrefix, translateTo = toeEndJnt, scale = rigScale,
                                     parent = footCtrl.C, shape = 'circleY' )

        toeIkControls.append( toeIkCtrl )

    # make ik handle

    if scapulaJnt:

        scapulaIK = mc.ikHandle( n = prefix + 'Scapula_ikh', sol = 'ikSCsolver', sj = scapulaJnt, ee = legJoints[0] )[0]

    legIK = mc.ikHandle( n = prefix + 'Main_ikh', sol = 'ikRPsolver', sj = legJoints[0], ee = legJoints[2] )[0]
    ballIK = mc.ikHandle( n = prefix + 'Ball_ikh', sol = 'ikRPsolver', sj = legJoints[2], ee = legJoints[3] )[0]
    mainToeIK = mc.ikHandle( n = prefix + 'MainToe_ikh', sol = 'ikRPsolver', sj = legJoints[3], ee = legJoints[4] )[0]

    mc.hide( legIK, ballIK, mainToeIK )

    for i, topToeJnt in enumerate( topToeJoints ):

        toePrefix = name.removeSuffix( topToeJnt )[:-1]
        topJoints = joint.listHierarchy( topToeJnt )

        toeIk = mc.ikHandle( n = toePrefix + '_ikh', sol = 'ikRPsolver', sj = topJoints[1], ee = topJoints[-1] )[0]
        mc.hide( toeIk )
        mc.parent( toeIk, toeIkControls[i].C )

    # attach controls

    mc.parentConstraint( bodyAttachGrp, poleVectorCtrl.off, mo = True )

    if scapulaJnt:

        mc.parentConstraint( baseAttachGrp, scapulaCtrl.off, mo = True )

    # attach objects to contorls

    mc.parent( legIK, ballCtrl.C )
    mc.parent( ballIK, mainToeIK, footCtrl.C )

    mc.poleVectorConstraint( poleVectorCtrl.C, legIK )

    if scapulaJnt:

        mc.parent( scapulaIK, scapulaCtrl.C )
        mc.pointConstraint( scapulaCtrl.C, scapulaJnt )

    # make pole vector connection line

    pvLinePos1 = mc.xform( legJoints[1], q = 1, t = 1, ws = 1 )
    pvLinePos2 = mc.xform( pvLocator, q = 1, t = 1, ws = 1 )
    poleVectorCrv = mc.curve( n = prefix + 'Pv_crv', d = 1 , p = [ pvLinePos1, pvLinePos2 ] )
    mc.cluster( poleVectorCrv + '.cv[0]', n = prefix + 'Pv1_cls', wn = [ legJoints[1], legJoints[1] ], bs = True )
    mc.cluster( poleVectorCrv + '.cv[1]', n = prefix + 'Pv2_cls', wn = [ poleVectorCtrl.C, poleVectorCtrl.C ], bs = True )
    mc.parent( poleVectorCrv, rigModule.controlsGrp )
    mc.setAttr( poleVectorCrv + '.template', 1 )

    return { 'module':rigModule, 'baseAttachGrp':baseAttachGrp, 'bodyAttachGrp':bodyAttachGrp }

def build_old( 
            upperJnt,
            lowerJnt,
            ankleJnt,
            toeJnt,
            ikPoleVecRef,
            prefix = 'new',
            ctrlScale = 1.0,
            baseRigData = None,
            flatWorldXZ = True,
            buildIkRotCtl = False,
            doReverseFoot = True,
            heelLoc = None,
            tipLoc = None,
            outFootLoc = None,
            inFootLoc = None,
            endOrientRefObject = '',
            doIkLimit = False,
            stretchyAndBendy = False,
            buildBendySubControls = False,
            buildMiddleTweaker = False
            ):
    
    '''
    build leg rig using limb rig as a base
    
    :param upperJnt: str, upper joint (hips)
    :param lowerJnt: str, lower joint (knee)
    :param ankleJnt: str, ankle joint
    :param toeJnt: str, toe joint
    :param ikPoleVecRef: str, reference object for position of IK pole vector control
    :param endJntXasworld: list (x,y,z), world axis which will be aligned to X axis of ankle joint object
    :param endJntYasworld: list (x,y,z), world axis which will be aligned to Y axis of ankle joint object
    :param prefix: str, prefix to name new objects
    :param ctrlScale: float, scale of controls
    :param baseRigData: instance, base rig data returned from rigbase.base build() to connect visibility channels etc. to the main base
    :param buildIkRotCtl: bool, - only used by arm module - build IK rotation control for using both rotation of world control or local elbow joint orientation
    :param doReverseFoot:bool, build reverse foot and its attributes like ballRoll etc.
    :param heelLoc: str, only used in mode doReverseFoot, heel pivot locator
    :param tipLoc: str, optional, tip of foot pivot locator - used in doReverseFoot and also main foot control setup
    :param outFootLoc: str, only used in mode doReverseFoot, outer foot side pivot locator
    :param inFootLoc: str, only used in mode doReverseFoot, inner foot side pivot locator
    :param endOrientRefObject: str, optional, reference object for end IK control orientation
    :param doIkLimit: bool, build IK length limit system to prevent IK pop effect when IK goes fully straight
    :return: dictionary with rig objects
    '''     

    limbData = limb.build( 
                upperJnt = upperJnt,
                midJnt = lowerJnt,
                endJnt = ankleJnt,
                ikPoleVecRef = ikPoleVecRef,
                prefix = prefix,
                baseRigData = baseRigData,
                ctrlScale = ctrlScale,
                flatWorldXZ = flatWorldXZ,
                doWorldAlignedEnd = False,
                buildIkRotCtl = buildIkRotCtl,
                endOrientRefObject = endOrientRefObject,
                doIkLimit = doIkLimit,
                isLeg = True,
                stretchyAndBendy = stretchyAndBendy,
                buildBendySubControls = buildBendySubControls,
                buildMiddleTweaker = buildMiddleTweaker
                )
    
    # limb info
    
    limbIk1Ctrl = limbData['ik1Ctrl']
    ankleFkCtrl = limbData['fkControls'][2]
    ikAttachGrp = limbData['ikAttachGrp']
    upperJnt = limbData['upperJnt']    
    
    
    fkFootData = _buildFkFoot( prefix, toeJnt, ankleJnt, limbIk1Ctrl, limbData['module'], ctrlScale )
    
    footIkHandles = []
    
    ikFootData = _buildIkFoot( prefix, doReverseFoot, limbIk1Ctrl, ikAttachGrp, ankleJnt, toeJnt, ctrlScale, limbData['limbIk'], limbData['mainGrp'], heelLoc, tipLoc, outFootLoc, inFootLoc )
    mc.parent( ikFootData['mainIkFootGrp'], limbData['ctrlGrp'] )
    footIkHandles = [ ikFootData['ankleIk'], ikFootData['toeIk'], ikFootData['tipIk'] ]

    # drive leg twist by rotation
    _driveIkTwistByCtrlRy( limbData['ikBaseCtrl'].C, limbData['limbIk'], prefix, doReverse = True )
    

    # connect ikFk
    
    for ikh in footIkHandles:
        
        if ikh:
            
            limbData['module'].connectIkFk( ikh + '.ikBlend' )
        
    # connect ctrl vis
    
    limbData['module'].connectPrimaryVis( ikFootData['mainIkFootGrp'] )
    
    return {
            'rigdata':limbData,
            'module':limbData['module'],
            'ik1Ctrl':limbData['ik1Ctrl'],
            'ikBaseCtrl':limbData['ikBaseCtrl'],
            'tipCtrl':ikFootData['tipCtrl'],
            'ikBallCtrl':ikFootData['ballCtrl'],
            'ikToeCtrl':ikFootData['toeCtrl'],
            'mainGrp':limbData['mainGrp'],
            'fkControls':limbData['fkControls'],
            'globalSpaceGrp':limbData['globalSpaceGrp'],
            'bodySpaceGrp':limbData['bodySpaceGrp'],
            'localSpaceGrp':limbData['localSpaceGrp'],
            'toggleGrp':limbData['toggleGrp'],
            'settingsGrp':limbData['settingsGrp'],
            'toggleCtrl':limbData['toggleCtrl']
            }

def build( 
            upperJnt,
            lowerJnt,
            ankleJnt,
            toeJnt,
            toeEndJnt,
            ikPoleVecRef,
            prefix = 'new',
            ctrlScale = 1.0,
            baseRigData = None,
            flatWorldXZ = True,
            doReverseFoot = True,
            heelLoc = None,
            tipLoc = None,
            outFootLoc = None,
            inFootLoc = None,
            endOrientRefObject = '',
            buildTwistJoints = True,
            twistJointsNumber = 5,
            stretch = True,
            snappablePv = True,
            bendy = True
            ):
    
    '''
    build leg rig using limb rig as a base
    
    :param upperJnt: str, upper joint (hips)
    :param lowerJnt: str, lower joint (knee)
    :param ankleJnt: str, ankle joint
    :param toeJnt: str, toe joint
    :param toeEndJnt: str, toe end joint
    :param ikPoleVecRef: str, reference object for position of IK pole vector control
    :param prefix: str, prefix to name new objects
    :param ctrlScale: float, scale of controls
    :param baseRigData: instance, base rig data returned from rigbase.base build() to connect visibility channels etc. to the main base
    :param doReverseFoot:bool, build reverse foot and its attributes like ballRoll etc.
    :param heelLoc: str, only used in mode doReverseFoot, heel pivot locator
    :param tipLoc: str, optional, tip of foot pivot locator - used in doReverseFoot and also main foot control setup
    :param outFootLoc: str, only used in mode doReverseFoot, outer foot side pivot locator
    :param inFootLoc: str, only used in mode doReverseFoot, inner foot side pivot locator
    :param endOrientRefObject: str, optional, reference object for end IK control orientation
    :param buildTwistJoints: bool, create twist joints setup
    :param twistJointsNumber: int, number of joints is going to be create by twist setup
    :return: dictionary with rig objects
    '''     

    limbData = limb.build( 
                upperJnt = upperJnt,
                midJnt = lowerJnt,
                endJnt = ankleJnt,
                ikPoleVecRef = ikPoleVecRef,
                prefix = prefix,
                baseRigData = baseRigData,
                ctrlScale = ctrlScale,
                flatWorldXZ = flatWorldXZ,
                endOrientRefObject = endOrientRefObject,
                isLeg = True,
                buildTwistJoints = buildTwistJoints,
                twistJointsNumber = twistJointsNumber,
                stretch = stretch,
                snappablePv = snappablePv,
                bendy = bendy
                )
    
    # instance of rig module
    rigmodule = limbData['module']
    
    # duplicate to create ik/fk toe, toe end joints and connect it to bind
    fkToeJnts, ikToeJnts = _createFkIkToes( rigmodule, toeJnt, toeEndJnt, limbData )
    
    # limb info
    fkJoints = limbData['fkJoints'] + fkToeJnts
    ikJoints = limbData['ikJoints'] + ikToeJnts
    
    limbIk1Ctrl = limbData['ik1Ctrl']
    ankleFkCtrl = limbData['fkControls'][2]
    ikAttachGrp = limbData['ikAttachGrp']
    upperJnt = limbData['upperJnt'] 

    fkFootData = _buildFkFoot( prefix, fkJoints, limbData['module'], ctrlScale )
    footIkHandles = []
    
    ikFootData = _buildIkFoot( prefix, doReverseFoot, limbIk1Ctrl, ikAttachGrp, ikJoints, ctrlScale, limbData['limbIk'], limbData['mainGrp'], heelLoc, tipLoc, outFootLoc, inFootLoc )
    mc.parent( ikFootData['mainIkFootGrp'], limbData['ctrlGrp'] )
    footIkHandles = [ ikFootData['ankleIk'], ikFootData['toeIk'], ikFootData['tipIk'] ]

    # drive leg twist by rotation
    _driveIkTwistByCtrlRy( limbData['ikBaseCtrl'].C, limbData['limbIk'], prefix, doReverse = True )
    
    '''
    # connect ikFk
    
    for ikh in footIkHandles:
        
        if ikh:
            
            limbData['module'].connectIkFk( ikh + '.ikBlend' )
    '''
    # connect ctrl vis
    
    limbData['module'].connectPrimaryVis( ikFootData['mainIkFootGrp'] )
    
    # hide fk/ik joints
    
    mc.hide( fkJoints[0], ikJoints[0] )
    
    return {
            'rigdata':limbData,
            'module':limbData['module'],
            'ik1Ctrl':limbData['ik1Ctrl'],
            'ikBaseCtrl':limbData['ikBaseCtrl'],
            'tipCtrl':ikFootData['tipCtrl'],
            'ikBallCtrl':ikFootData['ballCtrl'],
            'ikToeCtrl':ikFootData['toeCtrl'],
            'mainGrp':limbData['mainGrp'],
            'fkControls':limbData['fkControls'],
            'globalSpaceGrp':limbData['globalSpaceGrp'],
            'bodySpaceGrp':limbData['bodySpaceGrp'],
            'localSpaceGrp':limbData['localSpaceGrp'],
            'toggleGrp':limbData['toggleGrp'],
            'settingsGrp':limbData['settingsGrp'],
            'toggleCtrl':limbData['toggleCtrl']
            }

def _createFkIkToes( rigmodule, toeJnt, toeEndJnt, limbData ):
    
    '''
    create a duplicated of toe and toe end joints to make fk and ik setup
    '''
    fkAnkleJnt = limbData['fkJoints'][2]
    ikAnkleJnt = limbData['ikJoints'][2]
    
    fkJointNames = [ name.removeSuffix( j ) + 'Fk' for j in [ toeJnt, toeEndJnt ] ]
    fkJoints = joint.duplicateChain( [ toeJnt, toeEndJnt ], newjointnames = fkJointNames )
    
    ikJointNames = [ name.removeSuffix( j ) + 'Ik' for j in [ toeJnt, toeEndJnt ] ]
    ikJoints = joint.duplicateChain( [ toeJnt, toeEndJnt ], newjointnames = ikJointNames )
    
    mc.parent( ikJoints[0], ikAnkleJnt )
    mc.parent( fkJoints[0], fkAnkleJnt )
    
    # set some Colors and different radius
    fkIkJointList = fkJoints, ikJoints
    
    jointRad = mc.getAttr( fkAnkleJnt + '.radius' )
    jntColor = mc.getAttr( fkAnkleJnt + '.ovc' )
    for chainJnts in fkIkJointList:
        
        for j in chainJnts:
            mc.setAttr( j + '.radius', jointRad )
            mc.setAttr( j + '.ove', 1 )
            mc.setAttr( j + '.ovc', jntColor )
        
        jointRad = mc.getAttr( ikAnkleJnt + '.radius' )
        jntColor = mc.getAttr( ikAnkleJnt + '.ovc' )
    
    # create constraint connections
    bindJnts = [ toeJnt, toeEndJnt ]
    
    for bind,fk,ik in zip( bindJnts, fkJoints, ikJoints):
        
        constraintName = mc.parentConstraint( fk, bind, mo = True )[0]
        mc.parentConstraint( ik, bind, mo = True )
        constraintAttr = constraint.getWeightAttrs(constraintName)
        
        rigmodule.connectIkFk( '{}.{}'.format( constraintName, constraintAttr[1] ) )
        rigmodule.connectIkFk( '{}.{}'.format( constraintName, constraintAttr[0] ), reversed = True )
        
    return fkJoints, ikJoints
    
def _buildFkFoot_old( prefix, toeJnt, ankleJnt, limbIk1Ctrl, rigmodule, ctrlScale ):
    
    toeFkCtrl = control.Control( lockHideChannels = ['t'], prefix = prefix + 'ToeFK', shape = 'cubeOnBaseX', moveTo = toeJnt, scale = ctrlScale * 2, ctrlParent = rigmodule.Controls )
    
    rigmodule.connectIkFk( toeFkCtrl.Off + '.v', reversed = True )
    
    mc.parentConstraint( ankleJnt, toeFkCtrl.Off, mo = True )
    mc.connectAttr( toeFkCtrl.C + '.r', toeJnt + '.r' )
    mc.connectAttr( toeFkCtrl.C + '.ro', toeJnt + '.ro' )
    
    return {'toeFkCtrl':toeFkCtrl}
    
def _buildFkFoot( prefix, fkJoints , rigmodule, ctrlScale ):
    
    toeFkCtrl = control.Control( lockHideChannels = ['t'], prefix = prefix + 'FkToe1', shape = 'cubeOnBaseX', moveTo = fkJoints[3], scale = ctrlScale * 2, ctrlParent = rigmodule.Controls )
    
    rigmodule.connectIkFk( toeFkCtrl.Off + '.v', reversed = True )
    
    mc.parentConstraint( fkJoints[2], toeFkCtrl.Off, mo = True )
    mc.connectAttr( toeFkCtrl.C + '.r', fkJoints[3] + '.r' )
    mc.connectAttr( toeFkCtrl.C + '.ro', fkJoints[3] + '.ro' )
    
    return {'toeFkCtrl':toeFkCtrl}
        
def _buildIkFoot_old( prefix, doReverseFoot, limbIk1Ctrl, ikAttachGrp, ankleJnt, toeJnt, ctrlScale, limbIk, mainModuleGrp, heelLoc, tipLoc, outFootLoc, inFootLoc ):
    
    mainIkFootGrp = mc.group( n = prefix + 'MainIkFoot_grp', em = 1 )
    mc.parent( limbIk1Ctrl.Off, mainIkFootGrp )
    toeEndJnt = mc.listRelatives( toeJnt, c = 1, typ = 'joint' )[0]
    
    # make reverse foot IK handles
    ankleIk = mc.ikHandle( n = prefix + 'Foot_ikh', sol = 'ikSCsolver', sj = ankleJnt, ee = toeJnt )[0]
    toeIk = mc.ikHandle( n = prefix + 'Toe_ikh', sol = 'ikSCsolver', sj = toeJnt, ee = toeEndJnt )[0]
    
    tipIk = None
    tipJntRes = mc.listRelatives( toeEndJnt, c = 1, typ = 'joint' )
    
    if tipJntRes:
        
        tipIk = mc.ikHandle( n = prefix + 'Tip_ikh', sol = 'ikSCsolver', sj = toeEndJnt, ee = tipJntRes[0] )[0]
    
    mc.hide( ankleIk, toeIk )
    
    if tipIk:
        
        mc.hide( tipIk )
    
    # make reverse foot
    
    if doReverseFoot:
        
        revFootData = _buildReverseFoot( mainModuleGrp, limbIk1Ctrl, ikAttachGrp, prefix, ctrlScale, ankleJnt, toeJnt, toeEndJnt, limbIk, ankleIk, toeIk, tipIk, heelLoc, tipLoc, outFootLoc, inFootLoc )
    
    else:
        
        revFootData = _buildReverseFoot2ControlSys( limbIk1Ctrl, ikAttachGrp, prefix, ankleJnt, toeJnt, toeEndJnt, limbIk, ankleIk, toeIk, tipIk, heelLoc, tipLoc, mainModuleGrp, ctrlScale )
    
    return {
        'mainIkFootGrp':mainIkFootGrp,
        'ankleIk':ankleIk,
        'toeIk':toeIk,
        'tipIk':tipIk,
        'heelCtrl':revFootData['heelCtrl'],
        'tipCtrl':revFootData['tipCtrl'],
        'toeCtrl':revFootData['toeCtrl'],
        'ballCtrl':revFootData['ballCtrl']
        }    

def _buildIkFoot( prefix, doReverseFoot, limbIk1Ctrl, ikAttachGrp, ikJoints , ctrlScale, limbIk, mainModuleGrp, heelLoc, tipLoc, outFootLoc, inFootLoc ):
    
    mainIkFootGrp = mc.group( n = prefix + 'MainIkFoot_grp', em = 1 )
    mc.parent( limbIk1Ctrl.Off, mainIkFootGrp )
    
    # define joint names so can use same reverse foot setup
    ankleJnt = ikJoints[2]
    toeJnt = ikJoints[3]
    toeEndJnt = ikJoints[4]
    
    # make reverse foot IK handles
    ankleIk = mc.ikHandle( n = prefix + 'Foot_ikh', sol = 'ikSCsolver', sj = ankleJnt, ee = toeJnt )[0]
    toeIk = mc.ikHandle( n = prefix + 'Toe_ikh', sol = 'ikSCsolver', sj = toeJnt, ee = toeEndJnt )[0]
    
    tipIk = None
    tipJntRes = mc.listRelatives( toeEndJnt, c = 1, typ = 'joint' )
    
    if tipJntRes:
        
        tipIk = mc.ikHandle( n = prefix + 'Tip_ikh', sol = 'ikSCsolver', sj = toeEndJnt, ee = tipJntRes[0] )[0]
    
    mc.hide( ankleIk, toeIk )
    
    if tipIk:
        
        mc.hide( tipIk )
    
    # make reverse foot
    
    if doReverseFoot:
        
        revFootData = _buildReverseFoot( mainModuleGrp, limbIk1Ctrl, ikAttachGrp, prefix, ctrlScale, ankleJnt, toeJnt, toeEndJnt, limbIk, ankleIk, toeIk, tipIk, heelLoc, tipLoc, outFootLoc, inFootLoc )
    
    else:
        
        revFootData = _buildReverseFoot2ControlSys( limbIk1Ctrl, ikAttachGrp, prefix, ankleJnt, toeJnt, toeEndJnt, limbIk, ankleIk, toeIk, tipIk, heelLoc, tipLoc, mainModuleGrp, ctrlScale )
    
    return {
        'mainIkFootGrp':mainIkFootGrp,
        'ankleIk':ankleIk,
        'toeIk':toeIk,
        'tipIk':tipIk,
        'heelCtrl':revFootData['heelCtrl'],
        'tipCtrl':revFootData['tipCtrl'],
        'toeCtrl':revFootData['toeCtrl'],
        'ballCtrl':revFootData['ballCtrl']
        }    

def _buildReverseFoot( mainModuleGrp, limbIk1Ctrl, ikAttachGrp, prefix, ctrlScale, ankleJnt, toeJnt, toeEndJnt, limbIk, ankleIk, toeIk, tipIk, heelLoc, tipLoc, outFootLoc, inFootLoc ):
    
    '''
    build reverse foot setup
    '''
    
    mc.addAttr( limbIk1Ctrl.C, ln = 'reverseFoot', at = 'enum', enumName = '_____', k = 1 )
    mc.setAttr( limbIk1Ctrl.C + '.reverseFoot', cb = 1, l = 1 )
    
    revNames = ['Heel', 'Tip', 'Ball', 'OutFoot', 'InFoot', 'BallRoll']
    refObjs = [heelLoc, tipLoc, toeJnt, outFootLoc, inFootLoc, toeJnt]
    revGrps = []

    for i in range( len( revNames ) ):
      
      newGrp = mc.group( n = prefix + revNames[i] + '_grp', em = 1 )
      revGrps.append( newGrp )
      mc.delete( mc.pointConstraint( refObjs[i], newGrp ) )
      mc.delete( mc.orientConstraint( toeJnt, newGrp ) )
      
      if i is not 0:
          
          mc.parent( revGrps[i], revGrps[i - 1] )
      
    mainGrp = mc.group( n = prefix + 'MainRevFoot_grp', em = 1 )
    mc.delete( mc.pointConstraint( heelLoc, mainGrp ) )
    mc.delete( mc.orientConstraint( toeJnt, mainGrp ) )
    
    mc.parent( revGrps[0], mainGrp )
    
    # make reverse attributes
    
    mc.addAttr( limbIk1Ctrl.C, ln = 'ballRoll', at = 'float', k = 1 )
    mc.addAttr( limbIk1Ctrl.C, ln = 'tipRoll', at = 'float', k = 1 )
    mc.addAttr( limbIk1Ctrl.C, ln = 'heelRoll', at = 'float', k = 1 )
    mc.addAttr( limbIk1Ctrl.C, ln = 'ballTwist', at = 'float', k = 1 )
    mc.addAttr( limbIk1Ctrl.C, ln = 'tipTwist', at = 'float', k = 1 )
    mc.addAttr( limbIk1Ctrl.C, ln = 'heelTwist', at = 'float', k = 1 )
    mc.addAttr( limbIk1Ctrl.C, ln = 'footTilt', at = 'float', k = 1 )
    mc.addAttr( limbIk1Ctrl.C, ln = 'ballTilt', at = 'float', k = 1 )
    
    mc.connectAttr( limbIk1Ctrl.C + '.ballRoll', revGrps[5] + '.rz' )
    mc.connectAttr( limbIk1Ctrl.C + '.tipRoll', revGrps[1] + '.rz' )
    mc.connectAttr( limbIk1Ctrl.C + '.heelRoll', revGrps[0] + '.rz' )
    mc.connectAttr( limbIk1Ctrl.C + '.ballTwist', revGrps[2] + '.ry' )
    mc.connectAttr( limbIk1Ctrl.C + '.tipTwist', revGrps[1] + '.ry' )
    mc.connectAttr( limbIk1Ctrl.C + '.heelTwist', revGrps[0] + '.ry' )
    
    #anim.setDrivenKey( limbIk1Ctrl.C + '.footTilt', revGrps[3] + '.rx', [-10, 0], [-10, 0] )
    #anim.setDrivenKey( limbIk1Ctrl.C + '.footTilt', revGrps[4] + '.rx', [0, 10], [0, 10] )
    mc.transformLimits( revGrps[3] , rx = (0, 0), erx = ( 0,1 ) )
    mc.transformLimits( revGrps[4] , rx = (0, 0), erx = ( 1,0 ) )
    mc.connectAttr( limbIk1Ctrl.C + '.footTilt', revGrps[3] + '.rx' )
    mc.connectAttr( limbIk1Ctrl.C + '.footTilt', revGrps[4] + '.rx' )
    
    mc.connectAttr( limbIk1Ctrl.C + '.ballTilt', revGrps[5] + '.rx' )
    
    # =======================
    # create foot IK controls
    # =======================
    
    heelCtrl = None
    tipCtrl = None
    toeCtrl = control.Control( lockHideChannels = ['t'], prefix = prefix + 'ToeIk', moveTo = toeJnt, scale = ctrlScale * 1, ctrlParent = revGrps[4], colorName = 'secondary', shape = 'singleRotation' )
    ballCtrl = control.Control( lockHideChannels = ['t'], prefix = prefix + 'BallIk', moveTo = toeJnt, scale = ctrlScale * 2, ctrlParent = revGrps[5], colorName = 'secondary', shape = 'arrow' )
    
    # fix default orient for controls 
    shape.translateRotate( toeCtrl.C, pos = [0, 0, 0], rot = [90, 0, 0], localSpace = True, relative = True )
    shape.translateRotate( ballCtrl.C, pos = [0, 0, 0], rot = [-90, 0, 0], localSpace = True, relative = True )
    shape.translateRotate( ballCtrl.C, pos = [0, 0, 0], rot = [0, 90, 0], localSpace = True, relative = True )

    
    #===========================================================================
    # parent objects
    #===========================================================================
    
    # limb IK
    
    revFootIkHolder = mc.group( n = prefix + 'RevFootIkHolder_grp', em = 1, r = 1, p = limbIk )
    mc.parent( revFootIkHolder, ballCtrl.C )
    
    # IMPORTANT: we assume IK handle is parented under its own attach group, which is constrained to limb IK control
    ikAttachGrp = mc.listRelatives( limbIk, p = 1 )[0]
    mc.delete( mc.listConnections( ikAttachGrp + '.tx' , t = 'constraint', s = 1 ) )
    mc.pointConstraint( revFootIkHolder, ikAttachGrp )
    
    # reverse foot objects
    
    mc.parent( ankleIk, ballCtrl.C )
    mc.parent( toeIk, toeCtrl.C )
    mc.parent( mainGrp, limbIk1Ctrl.C )
    
    if tipIk:
        
        mc.parent( tipIk, toeCtrl.C )
    
    return {
            'mainGrp':mainGrp,
            'heelGrp':revGrps[0],
            'tipGrp':revGrps[1],
            'ballGrp':revGrps[2],
            'outFootGrp':revGrps[3],
            'inFootGrp':revGrps[4],
            'ballRollGrp':revGrps[5],
            'heelCtrl':heelCtrl,
            'tipCtrl':tipCtrl,
            'toeCtrl':toeCtrl,
            'ballCtrl':ballCtrl
            }
    
def _buildReverseFoot2ControlSys( limbIk1Ctrl, ikAttachGrp, prefix, ankleJnt, toeJnt, toeEndJnt, limbIk, ankleIk, toeIk, tipIk, heelLoc, tipLoc, mainModuleGrp, ctrlScale ):
    
    '''
    make simple 3 controls (heel, toes and tip) reverse foot setup
    '''
    
    # =======================
    # create foot IK controls
    # =======================
    
    tipCtrlPosRef = toeEndJnt
    
    if tipLoc:
        
        tipCtrlPosRef = tipLoc
    
    # add ball roll setup
    ballRollAt = 'ballRoll'
    ballRollGrp = transform.makeGroup( prefix = prefix + 'BallRoll', referenceObj = toeEndJnt, parentObj = limbIk1Ctrl.C )
    mc.delete( mc.orientConstraint( toeJnt, ballRollGrp ) )
    ballRollGrpOff = transform.makeOffsetGrp( ballRollGrp )
    
    # build controls
    heelCtrl = None
    tipCtrl = control.Control( lockHideChannels = ['t'], prefix = prefix + 'TipIk', translateTo = tipCtrlPosRef, rotateTo = toeEndJnt, scale = ctrlScale * 1, ctrlParent = limbIk1Ctrl.C, colorName = 'secondary', shape = 'singleRotation' )
    toeCtrl = control.Control( lockHideChannels = ['t'], prefix = prefix + 'ToeIk', moveTo = toeJnt, scale = ctrlScale * 1, ctrlParent = tipCtrl.C, colorName = 'secondary', shape = 'arrow' )
    ballCtrl = control.Control( lockHideChannels = ['t'], prefix = prefix + 'BallIk', moveTo = toeJnt, scale = ctrlScale * 1, ctrlParent = ballRollGrp, colorName = 'secondary', shape = 'singleRotation' )
    
    # fix default orient for controls 
    shape.translateRotate( tipCtrl.C, pos = [0, 0, 0], rot = [90, 0, 0], localSpace = True, relative = True )
    shape.translateRotate( toeCtrl.C, pos = [0, 0, 0], rot = [-90, 0, 0], localSpace = True, relative = True )
    shape.translateRotate( toeCtrl.C, pos = [0, 0, 0], rot = [0, 90, 0], localSpace = True, relative = True )
    shape.translateRotate( ballCtrl.C, pos = [0, 0, 0], rot = [90, 0, 0], localSpace = True, relative = True )
    
    
    attribute.addSection( ballCtrl.C )
    mc.addAttr( ballCtrl.C, ln = ballRollAt, at = 'float', k = True )
    mc.connectAttr( ballCtrl.C + '.' + ballRollAt, ballRollGrp + '.rz' )
    mc.parent( ballRollGrpOff, tipCtrl.C )
    
    if heelLoc:
        
        heelCtrl = control.Control( lockHideChannels = ['t'], prefix = prefix + 'HeelIk', translateTo = heelLoc, rotateTo = toeJnt, scale = ctrlScale * 1, ctrlParent = limbIk1Ctrl.C, colorName = 'secondary', shape = 'singleRotation' )
        mc.parent( tipCtrl.Off, heelCtrl.C )
    
        # fix default orient for controls 
        shape.translateRotate( heelCtrl.C, pos = [0, 0, 0], rot = [90, 0, 0], localSpace = True, relative = True )
        
    
    # ====================
    # hook up IK handles
    # ====================
    
    # limb IK
    mc.parent( ikAttachGrp, ballCtrl.C )
    
    
    # parent toe and heel IK    
    mc.parent( toeIk, toeCtrl.C )
    mc.parent( ankleIk, ballCtrl.C, )
    
    if tipIk:
        
        mc.parent( tipIk, tipCtrl.C )
    
    return {
            'heelCtrl':heelCtrl,
            'tipCtrl':tipCtrl,
            'toeCtrl':toeCtrl,
            'ballCtrl':ballCtrl
            }

def _driveIkTwistByCtrlRy( driverctrl, limbIk, prefix, doReverse = True ):
    
    '''
    connect Y rotation of given control to add to twist of the IK handle
    
    :param driverctrl: str, driver rotation control (no Control instance, just transform object)
    :param limbIk: str, limb IK handle
    :param prefix: str, prefix to name new objects
    :param doReverse: bool, reverse twist rotation
    :return: None
    '''
    
    twistmultiValue = 1
    
    if doReverse:
        
        twistmultiValue = -1
    
    mc.setAttr( driverctrl + '.ry', l = 0, k = 1 )
    multinode = mc.createNode( 'multDoubleLinear', n = prefix + 'IkTwist_mdl' )
    mc.connectAttr( driverctrl + '.ry', multinode + '.i1' )
    mc.setAttr( multinode + '.i2', twistmultiValue )
    addnode = mc.createNode( 'addDoubleLinear', n = prefix + 'IkTwist_add' )
    mc.connectAttr( multinode + '.o', addnode + '.i1' )
    mc.setAttr( addnode + '.i2', mc.getAttr( limbIk + '.twist' ) )
    mc.connectAttr( addnode + '.o', limbIk + '.twist' )    
