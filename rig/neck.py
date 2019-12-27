"""
neck @ rig
"""

import maya.cmds as mc

from . import general

from ..base import module
from ..base import control

from ..utils import joint
from ..utils import name
from ..utils import shape
from ..utils import transform
from ..utils import vector
from ..utils import anim



def build_old(
        neckJoints,
        headJnt,
        neckCurve,
        prefix = 'neck',
        rigScale = 1.0,
        baseRig = None
        ):
    """
    build function to create neck rig setup
    :param neckJoints: list( str ), list of 6 neck joints
    :param headJnt: str, head joint at the end of the neck joint chain
    :param neckCurve: str, name of neck cubic curve with 5 CVs matching first 5 spine joints
    :param prefix: str, prefix to name new objects
    :param rigScale: float, scale factor for size controls
    :param baseRig: instance of base.module.Base class
    :return: dictionary with rig module objects
    """

    # make rig module

    rigModule = module.Module( prefix = prefix, baseObj = baseRig )

    # make neck curve clusters

    neckCurveCVs = mc.ls( neckCurve + '.cv[*]', fl = True )
    numNeckCVs = len( neckCurveCVs )
    neckCurveClusters = []

    for i in range( numNeckCVs ):

        cls = mc.cluster( neckCurveCVs[i], n = prefix + 'Cluster%d' % ( i + 1 ) )[1]
        neckCurveClusters.append( cls )

    mc.hide( neckCurveClusters )

    # parent neck curve
    mc.parent( neckCurve, rigModule.partsNoTransGrp )

    # make attach groups

    bodyAttachGrp = mc.group( n = prefix + 'BodyAttach_grp', em = True, p = rigModule.partsGrp )
    baseAttachGrp = mc.group( n = prefix + 'BaseAttach_grp', em = True, p = rigModule.partsGrp )

    mc.delete( mc.pointConstraint( neckJoints[0], baseAttachGrp ) )

    # make controls

    headMainCtrl = control.Control( prefix = prefix + 'HeadMain', translateTo = neckJoints[-1], scale = rigScale * 5,
                                    parent = rigModule.controlsGrp, shape ='circleZ' )

    headLocalCtrl = control.Control( prefix = prefix + 'HeadLocal', translateTo = headJnt, rotateTo = headJnt,
                                     scale = rigScale * 4, parent = headMainCtrl.C, shape ='circleX' )

    middleCtrl = control.Control( prefix = prefix + 'Middle', translateTo = neckCurveClusters[2], rotateTo = neckJoints[2],
                                     scale = rigScale * 4, parent = rigModule.controlsGrp, shape ='circleX' )

    # attach controls
    mc.parentConstraint( headMainCtrl.C, baseAttachGrp, middleCtrl.off, sr = [ 'x', 'y', 'z' ], mo = True )
    mc.orientConstraint( baseAttachGrp, middleCtrl.off, mo = True )
    mc.parentConstraint( bodyAttachGrp, headMainCtrl.off, mo = True )

    # attach clusters

    mc.parent( neckCurveClusters[3:], headMainCtrl.C )
    mc.parent( neckCurveClusters[2], middleCtrl.C )
    mc.parent( neckCurveClusters[:2], baseAttachGrp )

    # attach joints

    mc.orientConstraint( headLocalCtrl.C, headJnt, mo = True )

    # make IK handle

    neckIK = mc.ikHandle( n = prefix + '_ikh', sol = 'ikSplineSolver', sj = neckJoints[0], ee = neckJoints[-1],
                           c = neckCurve, ccv = False, parentCurve = False)[0]

    mc.hide( neckIK)
    mc.parent( neckIK, rigModule.partsNoTransGrp )

    # setup IK twist

    mc.setAttr( neckIK + '.dTwistControlEnable', 1 )
    mc.setAttr( neckIK + '.dWorldUpType', 4 )
    mc.connectAttr( headMainCtrl.C + '.worldMatrix[0]', neckIK + '.dWorldUpMatrixEnd' )
    mc.connectAttr( baseAttachGrp + '.worldMatrix[0]', neckIK + '.dWorldUpMatrix' )


    return { 'module':rigModule, 'baseAttachGrp':baseAttachGrp, 'bodyAttachGrp':bodyAttachGrp }
 

def build( 
        neckJoints,
        ikCurve,
        spineEndJnt,
        prefix = 'neck',
        baseRigData = None,
        ctrlScale = 1.0
        ):
    
    '''
    build neck IK/FK setup
    
    :param neckJoints: list( str ), neck joints with last being head joint
    :param ikCurve: str, curve for neck ikSpline solver (in future could be made automaticly
    :param prefix: str, prefix for naming main objects
    :param baseRigData:instance,  base rig data returned from rigbase.base build() to connect visibility channels etc. to the main base
    :param ctrlScale: float, scale of controls
    :param chestJnt: str, joint to attach the toggle ctrl to
    :return: dictionary with rig objects
    '''
    #===========================================================================
    # module
    #===========================================================================    
    
    rigmodule = module.Module( prefix )
    rigmodule.parent( baseRigData = baseRigData )
    rigmodule.connect( baseRigData = baseRigData )
    rigmodule.addIkFkAt()
    
    # base group
    
    baseGroup = mc.group( n = prefix + 'Base_grp', em = 1, p = neckJoints[0] )
    mc.delete( mc.aimConstraint( neckJoints[-1], baseGroup, aim = [1, 0, 0], u = [0, 0, 1], wut = 'scene', wu = [0, 0, 1] ) )
    mc.parent( baseGroup, rigmodule.LocalSpace )
    
    headIkAttachGrp = mc.group( n = prefix + 'HeadAttach_grp', em = 1 )
    mc.delete( mc.pointConstraint( neckJoints[-1], headIkAttachGrp ) )
    mc.parent( headIkAttachGrp, rigmodule.Parts ) 
    
    # neck tangent controls
    
    headTangentCtrl, chestTangentCtrl, headTgPositionGrpStretchPlug = _neckTangentControls( neckJoints, prefix, ikCurve, rigmodule, ctrlScale, headIkAttachGrp, baseGroup )
    
    
    # neck spline IK
    
    neckIk = mc.ikHandle( n = prefix + '_ikh', sol = 'ikSplineSolver', sj = neckJoints[0], ee = neckJoints[-1], c = ikCurve, ccv = 0, pcv = 0 )[0]
    
    mc.parent( neckIk, rigmodule.PartsNt )
    mc.setAttr( neckIk + '.it', 0 )
    rigmodule.connectIkFk( neckIk + '.ikBlend' )
    
    ikCurve = mc.rename( ikCurve, prefix + '_crv' )
    mc.parent( ikCurve, rigmodule.PartsNt )
    
    mc.setAttr( ikCurve + '.it', 0 )    

    #===========================================================================
    # IK helpers
    #===========================================================================
    
    # neck twist setup
    
    neckTwistRefData = joint.makeTwistRefJoint( neckJoints[0], neckJoints[-1], headIkAttachGrp )
    mc.parent( neckTwistRefData['mainGrp'], rigmodule.LocalSpace )
    
    mc.hide( neckTwistRefData['mainGrp'] )
    
    neckTwistMulti = mc.createNode( 'multDoubleLinear', n = prefix + 'Twist_multi' )
    mc.connectAttr( neckTwistRefData['refjoint'] + '.rx', neckTwistMulti + '.i1' )
    mc.setAttr( neckTwistMulti + '.i2', 0.5 )
    mc.connectAttr( neckTwistMulti + '.o', neckIk + '.twist' )

    # neck FK controls
    
    fkCtrlNames = []
    for i in range( len( neckJoints ) - 1 ): fkCtrlNames.append( prefix + 'Fk' + str( i + 1 ) )
    fkCtrlNames.append( prefix + 'Fk' )
    
    fkControlScale = ctrlScale * 4    
    fkControls = general.makeFkControlChain( prefixSeq = fkCtrlNames, chain = neckJoints[:-1], scale = fkControlScale, constraintFirst = True, ctrlParent = rigmodule.Main, ctrlshape = 'circle' )
    
    mc.parent( fkControls[0].Off, rigmodule.Controls )
    mc.parentConstraint( rigmodule.LocalSpace, fkControls[0].Off, mo = 1 )
    
    # connect vis
    rigmodule.connectIkFk( fkControls[0].Off + '.v', reversed = True  )
    
#     ikFkReverse = mc.createNode( 'reverse' )
#     rigmodule.connectIkFk( ikFkReverse + '.ix' )
#     mc.connectAttr( ikFkReverse + '.ox', fkControls[0].Off + '.v' )
    
    return {
            'module':rigmodule,
            'mainGrp':rigmodule.Main,
            'fkControls':fkControls,
            'localSpaceGrp':rigmodule.LocalSpace,
            'globalSpaceGrp':rigmodule.GlobalSpace,
            'bodySpaceGrp':rigmodule.BodySpace,
            'toggleGrp':rigmodule.Toggle,
            'settingsGrp':rigmodule.Settings,
            'headIkAttachGrp':headIkAttachGrp,
            }    
    
def buildIclone(
                spineRigData,
                neckJnt,
                chestJnt,
                prefix = 'neck',
                ctrlScale = 1.0
                ):
    
    '''
    :param spineRigData:instance, spine rig module to parent neck objects
    :param neckJnt: str, neck joint to create control
    :param chestJnt: str, joint to attach neck control
    :param ctrlScale: float, scale of controls
    :param prefix: str, prefix for naming main objects
    :return: dictionary with rig objects
    '''
    # create control for neck joint and attach it
    neckCtrl = control.Control(
                 prefix=prefix,
                 scale=ctrlScale,
                 translateTo=neckJnt,
                 rotateTo=neckJnt,
                 ctrlParent=spineRigData['module'].Controls,
                 shape = 'circle',
                 defLockHide = ['s','v'],
                 rotOrd = 3,
                 )
    
    mc.connectAttr( neckCtrl.C + '.ro', neckJnt + '.ro' )
    mc.parentConstraint( neckCtrl.C, neckJnt, mo = True )
    mc.parentConstraint( chestJnt, neckCtrl.Off, mo = True )
    
    return {
            'control': neckCtrl
            }
    
def buildCC(
            neckJoints,
            prefix = 'neck',
            baseRigData = None,
            ctrlScale = 1.0
            ):
    '''
    :param neckJoints: list( str ), neck joints with last being head joint
    :param prefix: str, prefix for naming main objects
    :param baseRigData:instance,  base rig data returned from rigbase.base build() to connect visibility channels etc. to the main base
    :param ctrlScale: float, scale of controls
    :return: dictionary with rig objects
    '''
    #===========================================================================
    # module
    #===========================================================================    
    
    rigmodule = module.Module( prefix )
    rigmodule.parent( baseRigData = baseRigData )
    rigmodule.connect( baseRigData = baseRigData )
    
    # neck FK controls
    
    fkCtrlNames = []
    for i in range( len( neckJoints ) ): fkCtrlNames.append( prefix + 'Fk' + str( i + 1 ) )
    
    fkControlScale = ctrlScale * 4    
    fkControls = general.makeFkControlChain( prefixSeq = fkCtrlNames, chain = neckJoints, scale = fkControlScale, constraintFirst = True, ctrlParent = rigmodule.Main, ctrlshape = 'circle' )
    
    mc.parent( fkControls[0].Off, rigmodule.Controls )
    mc.parentConstraint( rigmodule.LocalSpace, fkControls[0].Off, mo = 1 )
    
    return {
            'module':rigmodule,
            'mainGrp':rigmodule.Main,
            'fkControls':fkControls,
            'localSpaceGrp':rigmodule.LocalSpace,
            'globalSpaceGrp':rigmodule.GlobalSpace,
            'bodySpaceGrp':rigmodule.BodySpace,
            'toggleGrp':rigmodule.Toggle,
            'settingsGrp':rigmodule.Settings,
            }   
    
def _neckTangentControls( neckJoints, prefix, ikCurve, rigmodule, ctrlScale, headIkAttachGrp, baseGroup ):
    
    '''
    setup neck tangent controls
    '''
    
    # tangent controls
    
    headTangentCtrl = control.Control( rotOrd = 0, lockHideChannels = ['t'], defLockHide = ['v', 'sx', 'sz'], prefix = prefix + 'HeadTangent', translateTo = headIkAttachGrp, scale = 3 * ctrlScale, shape = 'circle', ctrlParent = rigmodule.Controls, colorName = 'secondary' )
    chestTangentCtrl = control.Control( rotOrd = 0, lockHideChannels = ['t'], defLockHide = ['v', 'sx', 'sz'], prefix = prefix + 'ChestTangent', translateTo = baseGroup, scale = 3 * ctrlScale, shape = 'circle', ctrlParent = rigmodule.Controls, colorName = 'secondary' )
    
    mc.setAttr( headTangentCtrl.Off + '.v', 0 , l = True, k = False )
    mc.setAttr( chestTangentCtrl.Off + '.v', 0 , l = True, k = False )
    
    drivetatname = 'aim'
    mc.addAttr( headTangentCtrl.C, ln = drivetatname, at = 'float', min = 0, max = 1, k = 1 )
    mc.addAttr( chestTangentCtrl.C, ln = drivetatname, at = 'float', min = 0, max = 1, k = 1 )
    
    ikCurvecvs = mc.ls( ikCurve + '.cv[*]', fl = 1 )
    
    mc.pointConstraint( baseGroup, chestTangentCtrl.Off )
    headTgPositionGrp = _makeNeckTangentAttachSetup( rigmodule, prefix, headIkAttachGrp, headTangentCtrl, baseGroup )
    
    headTgPositionGrpStretchPlug = headTgPositionGrp + '.tx'
    
    _neckTangentControls_aimBlendSetup( neckJoints[-1], neckJoints[-2], ikCurvecvs[-2], headTangentCtrl.Off, baseGroup, headTgPositionGrp, prefix + 'HeadTangent', headTangentCtrl.C + '.' + drivetatname, revshape = True )
    _neckTangentControls_aimBlendSetup( neckJoints[0], neckJoints[1], ikCurvecvs[1], chestTangentCtrl.Off, headTgPositionGrp, baseGroup, prefix + 'ChestTangent', chestTangentCtrl.C + '.' + drivetatname, revshape = False )
    
    
    # neck spline clusters
    
    ikCurveCvs = mc.ls( ikCurve + '.cv[*]', fl = 1 )
    
    neckHeadClst = ''
    neckChestClst = ''
    
    ikCurveCvsLen = len( ikCurveCvs )
    
    if not ikCurveCvsLen == 4: raise Exception( 'neck curve must have 4 CVs, but has %d' % ikCurveCvsLen )
    
    neckHeadClst = mc.cluster( [ ikCurve + '.cv[2]', ikCurve + '.cv[3]' ], n = prefix + 'Head_clst' )[1]
    neckChestClst = mc.cluster( [ ikCurve + '.cv[0]', ikCurve + '.cv[1]' ], n = prefix + 'Chest_clst' )[1]
    
    mc.hide( neckHeadClst, neckChestClst )
    
    #===========================================================================
    # attach tangent clusters
    #===========================================================================
    
    mc.parent( neckChestClst, chestTangentCtrl.C )
    mc.parent( neckHeadClst, headTangentCtrl.C )
    
    return [ headTangentCtrl, chestTangentCtrl, headTgPositionGrpStretchPlug ]
    
def _makeNeckTangentAttachSetup( rigmodule, prefix, headIkAttachGrp, headTangentCtrl, baseGroup ):
    
    '''
    attach head tangent control position so it keeps tangency while main IK control is moving
    '''
    
    prefixTan = prefix + 'Tangent'
    
    aimGrp = transform.makeLocator( prefix = prefixTan + 'Aim', moveRef = baseGroup, parent = rigmodule.LocalSpace, simpleGroup = True )
    mc.aimConstraint( headIkAttachGrp, aimGrp, aim = [1, 0, 0], u = [0, 0, 1], wu = [0, 0, 1], wuo = rigmodule.LocalSpace, wut = 'objectrotation' )
    
    positionGrp = transform.makeLocator( prefix = prefixTan + 'Position', posRef = headTangentCtrl.C, rotRef = aimGrp, parent = aimGrp, simpleGroup = True )
    
    mc.pointConstraint( positionGrp, headTangentCtrl.Off )
    mc.orientConstraint( headIkAttachGrp, positionGrp, mo = 1 )
    
    return positionGrp    

def _neckTangentControls_aimBlendSetup( jntstart, jntaim, aimcurvecv, ctrlobj, targetparentobj, restparentobj, prefix, driverat, revshape ):
    
    '''
    setup dual tanget setup
    '''
    
    # find closest world axis based on start and aim joint
    
    jointaxis = vector.from2Objects( jntstart, jntaim )
    
    closestaxis = transform.closestObjectAxisToVector( ctrlobj, comparevector = jointaxis )
    
    upaxis = [0, 0, 1]
    if not closestaxis[2] == 0: upaxis = [0, 1, 0]
    
    # make rest aim and up groups
    
    restAimGrp = mc.group( n = prefix + 'Rest_grp', em = 1, p = ctrlobj )
    cvpos = mc.xform( aimcurvecv, q = 1, t = 1, ws = 1 )
    
    mc.move( cvpos[0], cvpos[1], cvpos[2], restAimGrp, ws = 1 )
    mc.parent( restAimGrp, restparentobj )
    
    upGrp = mc.group( n = prefix + 'Up_grp', em = 1, p = ctrlobj )
    mc.move( upaxis[0], upaxis[1], upaxis[1], upGrp, os = 1 )
    mc.parent( upGrp, restparentobj )
    
    
    # setup aim constraint
    
    aimcons = mc.aimConstraint( restAimGrp, targetparentobj, ctrlobj, aim = [0, 1, 0], u = [0, 0, 1], wut = 'object', wuo = upGrp )[0]
    aimwtats = mc.aimConstraint( aimcons, q = 1, weightAliasList = 1 )
    
    anim.setDrivenKey( driverat, aimcons + '.' + aimwtats[0], [0, 1], [1, 0] )
    anim.setDrivenKey( driverat, aimcons + '.' + aimwtats[1], [0, 1], [0, 1] )
    
    
    # reverse shape of control
    
    # if revshape: _neckTangentControls_reverseShape( ctrlobj, closestaxis )    

    
    
    
    
    
