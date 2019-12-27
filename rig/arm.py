'''
arm module
@category Rigging @subcategory Rig
'''

import maya.cmds as mc

from . import limb
from . import general

from ..base import control
from ..utils import shape
from ..utils import constraint
from ..utils import name
from ..utils import transform
from ..utils import connect

def build_old( 
            clavicleJnt,
            upperJnt,
            lowerJnt,
            endJnt,
            ikPoleVecRef,
            prefix = 'new',
            ctrlScale = 1.0,
            baseRigData = None,
            doWorldAlignedEnd = True,
            endOrientRefObject = '',
            stretchyAndBendy = False,
            buildBendySubControls = False,
            doIkLimit = False,
            buildMiddleTweaker = False
            
            ):

    '''
    build arm rig using limb rig as a base
    
    :param clavicleJnt: str, clavicle joint
    :param upperJnt: str, upper joint (shoulder)
    :param lowerJnt: str, lower joint (elbow)
    :param endJnt: str, end joint (wrist)
    :param ikPoleVecRef: str, reference object for position of IK pole vector control
    :param prefix: str, prefix for naming new objects
    :param ctrlScale: float, scale of controls
    :param baseRigData:instance, base rig data returned from rigbase.base build() to connect visibility channels etc. to the main base
    :param doWorldAlignedEnd: bool, works only if buildIkRotCtl is True, build IK end control aligned with world
    :param endOrientRefObject: str, optional, reference object for end IK control orientation,
    :param stretchyAndBendy: bool, build sub controls per each joint for Stretchy Bendy setup
    :param buildMiddleTweaker: bool, build tweak control to move elbow or knee joint on top resulting joint rotation
    :return: dictionary with rig objects
    '''
    
    limbData = limb.build( 
                upperJnt = upperJnt,
                midJnt = lowerJnt,
                endJnt = endJnt,
                ikPoleVecRef = ikPoleVecRef,
                prefix = prefix,
                baseRigData = baseRigData,
                ctrlScale = ctrlScale,
                doWorldAlignedEnd = doWorldAlignedEnd,
                buildIkRotCtl = False,
                endOrientRefObject = endOrientRefObject,
                doIkLimit = doIkLimit,
                isLeg = False,
                stretchyAndBendy = stretchyAndBendy,
                buildBendySubControls = buildBendySubControls,
                buildMiddleTweaker = buildMiddleTweaker
                )
    
    
    rigmodule = limbData['module']
    
    
    #===========================================================================
    # rig clavicle
    #===========================================================================
    
    # FK
    
    clavicleFkCtrl = None
    clavicleJntChild = mc.listRelatives( clavicleJnt, c = 1, typ = 'joint' )[0]
    shoulderFkRotateConst = mc.listConnections( limbData['fkControls'][0].Off + '.rx', type = 'constraint' )[0]
    shoulderFkLocalConstTarget = mc.listConnections( shoulderFkRotateConst + '.target' )[0]  # this will return local target group
    
    # lock FK shoulder translate channels
    for ax in ['x', 'y', 'z']:
        
        mc.setAttr( limbData['fkControls'][0].C + '.t' + ax, l = True, k = False )
   
    
    # IK
    # unlock IK shoulder translate and rotate channels
    for ax in ['x', 'y', 'z']:
        
        mc.setAttr( limbData['ikBaseCtrl'].C + '.t' + ax, l = 0, k = 1 )
        mc.setAttr( limbData['ikBaseCtrl'].C + '.r' + ax, l = 0, k = 1 )
    
    
    # attach base control and shoulder FK control
    
    constraint.removeAll( limbData['ikBaseCtrl'].Off )
    
    # tweak IK shoulder control
    side = name.getSide( prefix ) 
    clavicleJntGrp = transform.makeGroup( prefix = side + '_clavicleRef', referenceObj = clavicleJnt )   
    shoulderOrientGrp = mc.group( n = prefix + 'TEMPshoulderOrient_grp', em = True )
    
    if side == 'r':
        
        mc.rotate( 180, 0, 0, shoulderOrientGrp )
    
    mc.delete( mc.pointConstraint( clavicleJntGrp, limbData['ikBaseCtrl'].Off ) )
    mc.delete( mc.orientConstraint( shoulderOrientGrp, limbData['ikBaseCtrl'].Off ) )
    mc.delete( clavicleJntGrp, shoulderOrientGrp )
    
    shape.centerPointsToObjects( [ limbData['ikBaseCtrl'].C ], [ clavicleJntChild ] )
    
    # attach controls
    mc.parentConstraint( rigmodule.LocalSpace, limbData['ikBaseCtrl'].Off, sr = ['x', 'y', 'z'], mo = True )
    upperFkCtrl = limbData['fkControls'][0]
    

    mc.parent( upperFkCtrl.Off, limbData['ikBaseCtrl'].C )
    mc.disconnectAttr( limbData['toggleCtrl'].C + '.fkIk', limbData['ikBaseCtrl'].Off + '.v' )
    #mc.parent( rigmodule.ExtraASpace, clavicleJnt )
    #connect.disconnect( limbData['ikBaseCtrl'].Off + '.v', source = True, destination = False )
    

    
    ikBaseCtrlLocalObject = rigmodule.LocalSpace
    
    # make clavicle IK handle
    clavicleIk = mc.ikHandle( n = prefix + 'Clavicle_ikh', sol = 'ikSCsolver', sj = clavicleJnt, ee = limbData['upperJnt'] )[0]
    mc.parent( clavicleIk, rigmodule.Parts )
    mc.parentConstraint( limbData['ikBaseCtrl'].C, clavicleIk, mo = True, sr = ['x', 'y', 'z'] )
    mc.setAttr( clavicleIk + '.v', 0 )
    
    #_connectOrientFkIkHand( limbData, rigmodule, endJnt )
    
    return {            
        'rigdata':limbData,
        'module':rigmodule,
        'ik1Ctrl':limbData['ik1Ctrl'],
        'ikBaseCtrl':limbData['ikBaseCtrl'],
        'mainGrp':limbData['mainGrp'],
        'fkControls':limbData['fkControls'],
        'clavicleFkCtrl':clavicleFkCtrl,
        'clavicleIk':clavicleIk,
        'globalSpaceGrp':limbData['globalSpaceGrp'],
        'bodySpaceGrp':limbData['bodySpaceGrp'],
        'localSpaceGrp':limbData['localSpaceGrp'],
        'toggleGrp':limbData['toggleGrp'],
        'settingsGrp':limbData['settingsGrp'],
        'toggleCtrl':limbData['toggleCtrl']
        }

def build( 
            clavicleJnt,
            upperJnt,
            lowerJnt,
            endJnt,
            ikPoleVecRef,
            prefix = 'new',
            ctrlScale = 1.0,
            baseRigData = None,
            endOrientRefObject = '',
            buildTwistJoints = True,
            twistJointsNumber = 5
            ):

    '''
    build arm rig using limb rig as a base
    
    :param clavicleJnt: str, clavicle joint
    :param upperJnt: str, upper joint (shoulder)
    :param lowerJnt: str, lower joint (elbow)
    :param endJnt: str, end joint (wrist)
    :param ikPoleVecRef: str, reference object for position of IK pole vector control
    :param prefix: str, prefix for naming new objects
    :param ctrlScale: float, scale of controls
    :param baseRigData:instance, base rig data returned from rigbase.base build() to connect visibility channels etc. to the main base
    :param endOrientRefObject: str, optional, reference object for end IK control orientation,
    :param buildTwistJoints: bool, create twist joints setup
    :param twistJointsNumber: int, number of joints is going to be create by twist setup
    :return: dictionary with rig objects
    '''
    
    limbData = limb.build( 
                upperJnt = upperJnt,
                midJnt = lowerJnt,
                endJnt = endJnt,
                ikPoleVecRef = ikPoleVecRef,
                prefix = prefix,
                baseRigData = baseRigData,
                ctrlScale = ctrlScale,
                endOrientRefObject = endOrientRefObject,
                isLeg = False,
                buildTwistJoints = buildTwistJoints,
                twistJointsNumber = twistJointsNumber
                )
    
    
    rigmodule = limbData['module']
    
    
    #===========================================================================
    # rig clavicle
    #===========================================================================
    
    # FK
    
    clavicleFkCtrl = None
    clavicleJntChild = mc.listRelatives( clavicleJnt, c = 1, typ = 'joint' )[0]
    shoulderFkRotateConst = mc.listConnections( limbData['fkControls'][0].Off + '.rx', type = 'constraint' )[0]
    shoulderFkLocalConstTarget = mc.listConnections( shoulderFkRotateConst + '.target' )[0]  # this will return local target group
    
    # lock FK shoulder translate channels
    for ax in ['x', 'y', 'z']:
        
        mc.setAttr( limbData['fkControls'][0].C + '.t' + ax, l = True, k = False )
    
    # IK
    # unlock IK shoulder rotate channels and lock translate ones so it won't brake fk setup
    for ax in ['x', 'y', 'z']:
        
        mc.setAttr( limbData['ikBaseCtrl'].C + '.t' + ax, l = 1, k = 0 )
        mc.setAttr( limbData['ikBaseCtrl'].C + '.r' + ax, l = 0, k = 1 )
    
    
    # attach base control and shoulder FK control
    constraint.removeAll( limbData['ikBaseCtrl'].Off )
    
    # tweak IK shoulder control
    side = name.getSide( prefix ) 
    clavicleJntGrp = transform.makeGroup( prefix = side + '_clavicleRef', referenceObj = clavicleJnt )   
    shoulderOrientGrp = mc.group( n = prefix + 'TEMPshoulderOrient_grp', em = True )
    
    if side == 'r':
        
        mc.rotate( 180, 0, 0, shoulderOrientGrp )
    
    mc.delete( mc.pointConstraint( clavicleJntGrp, limbData['ikBaseCtrl'].Off ) )
    mc.delete( mc.orientConstraint( shoulderOrientGrp, limbData['ikBaseCtrl'].Off ) )
    mc.delete( clavicleJntGrp, shoulderOrientGrp )
    
    shape.centerPointsToObjects( [ limbData['ikBaseCtrl'].C ], [ clavicleJntChild ] )
    
    # attach controls
    mc.parentConstraint( rigmodule.LocalSpace, limbData['ikBaseCtrl'].Off, sr = ['x', 'y', 'z'], mo = True )
    upperFkCtrl = limbData['fkControls'][0]
    
    mc.parent( upperFkCtrl.Off, limbData['ikBaseCtrl'].C )
    mc.disconnectAttr( limbData['toggleCtrl'].C + '.fkIk', limbData['ikBaseCtrl'].Off + '.v' )
    
    # replace upper joint fk orient constraint for parent constraint so clavicle would drive
    constraint.removeAll( limbData['fkJoints'][0] )
    mc.parentConstraint( limbData['fkControls'][0].C, limbData['fkJoints'][0], mo = True )
    
    # make clavicle IK handle
    
    # create a duplicate of clavicle joint to be able to make an ik handle
    ikClavPrefix = name.removeSuffix( clavicleJnt )
    ikClavicleJnt = mc.duplicate( clavicleJnt, po = True, n = ikClavPrefix + 'Ik' )[0]
    mc.parent( ikClavicleJnt, limbData['module'].Joints )
    mc.parentConstraint( limbData['localSpaceGrp'], ikClavicleJnt, mo = True )
    mc.parentConstraint( ikClavicleJnt, clavicleJnt, mo = True )
    
    # set proper radius
    ikRadius = mc.getAttr( limbData['ikJoints'][0] + '.radius' )
    mc.setAttr( ikClavicleJnt + '.radius', ikRadius )
    mc.parent( limbData['ikJoints'][0], ikClavicleJnt )
    mc.setAttr( ikClavicleJnt + '.ove', 1 )
    mc.setAttr( ikClavicleJnt + '.ovc', 13 )
        
    
    # create ik 
    clavicleIk = mc.ikHandle( n = prefix + 'Clavicle_ikh', sol = 'ikSCsolver', sj = ikClavicleJnt, ee = limbData['ikJoints'][0] )[0]
    mc.parent( clavicleIk, rigmodule.Parts )
    mc.parentConstraint( limbData['ikBaseCtrl'].C, clavicleIk, mo = True, sr = ['x', 'y', 'z'] )
    mc.setAttr( clavicleIk + '.v', 0 )
    
    # hide ik and fk systems joints
    mc.hide( ikClavicleJnt, limbData['fkJoints'][0] )
    
    return {            
        'rigdata':limbData,
        'module':rigmodule,
        'ik1Ctrl':limbData['ik1Ctrl'],
        'ikBaseCtrl':limbData['ikBaseCtrl'],
        'mainGrp':limbData['mainGrp'],
        'fkControls':limbData['fkControls'],
        'clavicleFkCtrl':clavicleFkCtrl,
        'clavicleIk':clavicleIk,
        'globalSpaceGrp':limbData['globalSpaceGrp'],
        'bodySpaceGrp':limbData['bodySpaceGrp'],
        'localSpaceGrp':limbData['localSpaceGrp'],
        'toggleGrp':limbData['toggleGrp'],
        'settingsGrp':limbData['settingsGrp'],
        'toggleCtrl':limbData['toggleCtrl']
        }

def _connectOrientFkIkHand( limbData,rigmodule, endJnt ):
    
    fkPrefix = name.removeSuffix(limbData['fkControls'][0].C)
    ikPrefix = name.removeSuffix(limbData['ik1Ctrl'].C)
    
    fkOrientGrp = transform.makeGroup( prefix = fkPrefix + 'FkOrient_grp', referenceObj = endJnt, parentObj = limbData['fkControls'][2].C, pos = [0, 0, 0], matchPositionOnly = False )
    ikOrientGrp = transform.makeGroup( prefix = ikPrefix + 'IkOrient_grp', referenceObj = endJnt, parentObj = limbData['ik1Ctrl'].C, pos = [0, 0, 0], matchPositionOnly = False )
    #transform.makeGroup( prefix = prefix + 'PVfootSpace', referenceObj = ikPvCtrl.C, parentObj = rigmodule.LocalSpace, pos = [0, 0, 0], matchPositionOnly = True )

    handJntContraint = mc.orientConstraint( fkOrientGrp, ikOrientGrp, endJnt, mo = True )[0]
    constraint.setupDualConstraintBlend( handJntContraint, rigmodule.getIkFkAt() )


















