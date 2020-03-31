"""
Module to make limbs
@category Rigging @subcategory rig
"""
#TODO: add reference twist and space switches
#TODO: stretch and bendy
#TODO: doIkLimit fuction is not working yet
#TODO: study transform.rotateAlignToWorld

import maya.cmds as mc

from ..base import module
from ..base import control

from ..utils import name
from ..utils import shape
from ..utils import transform
from ..utils import constraint
from ..utils import curve
from ..utils import joint
from ..utils import distanceBetween
from ..utils import connect
from ..utils import attribute
from ..utils import vector

straightLimitPercentAt = 'straightLimitPerc'
currentLengthPercentAt = 'currentLengthPerc'

# straight limit percent
# this is default value, it is recommended to adjust this to lower values
# based on character skeleton straight pose
straightLimitPercent = 0.999

def build_old( 
            upperJnt,
            midJnt,
            endJnt,
            ikPoleVecRef,
            prefix = 'new',
            baseRigData = None,
            ctrlScale = 1.0,
            flatWorldXZ = False,
            doWorldAlignedEnd = True,
            buildIkRotCtl = True,
            endOrientRefObject = '',
            doIkLimit = False,
            isLeg = False,
            stretchyAndBendy = False,
            buildBendySubControls = False,
            buildMiddleTweaker = True,
            buildSnapSetup = False
            ):
    

    
    """
    :param upperJnt: str, upper joint
    :param midJnt: str, middle joint
    :param endJnt: str, end joint ( e.g wrist/hand joint )
    :param ikPoleVecRef: str, reference object for position of IK pole vector control
    :param prefix: str, prefix for naming new objects
    :param baseRigData: instance, base rig data returned from rigbase.base build() to connect visibility channels etc. to the main base
    :param ctrlScale: float, scale of controls
    :param flatWorldXZ: str, orienting IK control based on end joint X aiming, useful for foot controls in leg module
    :param doWorldAlignedEnd:bool, works only if buildIkRotCtl is True, build IK end control aligned with world
    :param buildIkRotCtl: bool, only used by arm module - build IK rotation control for using both rotation of world control or local elbow joint orientation
    :param endOrientRefObject: str, optional, reference object for end IK control orientation
    :param doIkLimit: bool, build IK length limit system to prevent IK pop effect when IK goes fully straight
    :param isLeg: bool, helps to orient Toggle control when module is used for leg setup and control shape
    :param buildMiddleTweaker: bool, build tweak control to move elbow or knee joint on top resulting joint rotation
    :param buildBendySubControls: bool, build sub controls per each joint for Stretchy Bendy setup
    :param stretchyAndBendy: bool, for now only when buildMiddleTweaker is True, make stretchy and bendy setup
    :param buildSnapLocators: bool, create a reference locators needed for fkik snap
    :return: dictionary with rig objects
    """
    # in case we are building Middle Tweakers work on duplicate chain
    if buildMiddleTweaker:
    
        driverJointNames = [ name.removeSuffix( j ) + 'Driver' for j in [ upperJnt, midJnt, endJnt ] ]
        driverJoints = joint.duplicateChain( [ upperJnt, midJnt, endJnt ], newjointnames = driverJointNames )
        
        midTweakUpperJnt = upperJnt
        midTweakLowerJnt = midJnt
        midTweakEndJnt = driverJoints[2]
        
        upperJnt = driverJoints[0]
        midJnt = driverJoints[1]
        
        mc.parent( endJnt, driverJoints[1] )
        mc.parent( driverJoints[2], midTweakLowerJnt )
    
    # get some initial values about the joints
    
    shoulderRot = mc.getAttr( upperJnt + '.r' )[0]
    elbowRot = mc.getAttr( midJnt + '.r' )[0]
    
    if not mc.objExists( endOrientRefObject ):
        
        endOrientRefObject = None
    
    if isLeg:
        ikCtrlShape = 'foot'
    else:
        ikCtrlShape = 'cube'
        
    #===========================================================================
    # module
    #===========================================================================    
    
    rigmodule = module.Module( prefix )
    rigmodule.parent( baseRigData = baseRigData )
    rigmodule.connect( baseRigData = baseRigData )
    
    # =============================
    # IK
    # =============================
    
    limbIk = mc.ikHandle( n = prefix + 'Main_ikh', sol = 'ikRPsolver', sj = upperJnt, ee = endJnt )[0]
    rigmodule.connectIkFk( limbIk + '.ikBlend' )
    
    
    # IK hand controls
    ik1Ctrl = control.Control( prefix = prefix + 'Ik1', translateTo = endJnt, rotateTo = endOrientRefObject, scale = ctrlScale * 4, shape = ikCtrlShape, ctrlParent = rigmodule.Controls )
    
    ikRotCtrl = None
    
    # make toggle control
    toggleCtrl = control.Control( prefix = prefix + 'Toggle', lockHideChannels = ['t', 'r'], translateTo = endJnt, rotateTo = endJnt, scale = ctrlScale * 5, colorName = 'secondary', shape = 't', ctrlParent = rigmodule.Controls )
    
    rotateToggleCtrlShape = None
    
    if isLeg and name.getSide( prefix ) == 'l':
        
        rotateToggleCtrlShape = True
    
    elif not isLeg and name.getSide( prefix ) == 'r':
        
        rotateToggleCtrlShape = True
    
    if rotateToggleCtrlShape:
    
        shape.translateRotate( toggleCtrl.C, rot = [180, 0, 0], localSpace = True )
    
    
    # add toggle to rig module
    rigmodule.customToggleObject( toggleCtrl.C )
    mc.parentConstraint( endJnt, toggleCtrl.Off, mo = True )
    
    # make flat orient object for IK controls
    if flatWorldXZ and not endOrientRefObject:
        
        localMoveRef = transform.makeLocator( prefix = prefix + 'TEMP_IkCtrlLocalMoveRef', moveRef = endJnt, simpleGroup = True )
        sideSign = name.getSideAsSign( prefix )
        transform.rotateAlignToWorld( localMoveRef, primaryAxisVector = [sideSign, 0, 0], worldAxisToKeep = ['x', 'z'], alignTwist = True )
        
        tempWorldGrp = mc.group( n = prefix + 'TEMP_worldRotate_grp', em = True, p = localMoveRef )
        mc.rotate( 0, 90, 0, tempWorldGrp, os = True )
        
        mc.delete( mc.orientConstraint( tempWorldGrp, ik1Ctrl.Off ) )
        mc.delete( localMoveRef, tempWorldGrp )
    
    # build IkRot control
    if buildIkRotCtl:
        
        ikRotCtrl = control.Control( prefix = prefix + 'IkRot', lockHideChannels = ['t'], moveTo = endJnt, scale = ctrlScale * 4, shape = 'circleX', colorName = 'secondary', ctrlParent = ik1Ctrl.C )
    
    rigmodule.connectIkFk( ik1Ctrl.Off + '.v' )
    mc.hide( limbIk )
    
    # IK pole vector control
    
    ikPvCtrl = control.Control( lockHideChannels = ['r'], prefix = prefix + 'IkPoleVector', translateTo = ikPoleVecRef, scale = ctrlScale, shape = 'diamond', ctrlParent = rigmodule.Controls )
    rigmodule.connectIkFk( ikPvCtrl.Off + '.v' )

    # =============================
    # build IK handle setup
    # =============================
    
    # build pole vector 90 degrees offset
    
    ikPvOffsetGrp = mc.group( n = prefix + 'IkPvOffsetAim_grp', em = 1, p = rigmodule.Parts )
    mc.pointConstraint( upperJnt, ikPvOffsetGrp )
    ikAimConst = mc.aimConstraint( ik1Ctrl.C, ikPvOffsetGrp, n = prefix + 'IkPvOffsetAim_aic', aim = [1, 0, 0], u = [0, 0, 1], wut = 'object', wuo = ikPvCtrl.C )[0]
    
    ikPvGrp = mc.group( n = prefix + 'IkPv_grp', em = 1, p = ikPvCtrl.C )
    mc.parent( ikPvGrp, ikPvOffsetGrp )
    
    mc.poleVectorConstraint( ikPvGrp, limbIk )
    mc.setAttr( ikAimConst + '.offsetX', 90 )
    mc.setAttr( limbIk + '.twist', -90 )
    
    # setup follow space for IK pole vector
    
    ikAimJntData = joint.makeTwistRefJoint( endJnt, upperJnt, rigmodule.LocalSpace, prefix + 'IkAim' )
    
    # setup hand or foot space for IK pole vector
    ikPvFootGrp = transform.makeGroup( prefix = prefix + 'PVfootSpace', referenceObj = ikPvCtrl.C, parentObj = rigmodule.LocalSpace, pos = [0, 0, 0], matchPositionOnly = True )
    mc.parentConstraint( ik1Ctrl.C, ikPvFootGrp, mo = True, sr = ['x', 'y', 'z'] )
    
    # add follow space as new member of module class
    rigmodule.FollowSpace = ikAimJntData['refjoint']
    
    mc.parent( ikAimJntData['ikHandle'], rigmodule.LocalSpace )
    mc.parent( ikAimJntData['mainGrp'], rigmodule.Parts )
    mc.pointConstraint( upperJnt, ik1Ctrl.C, ikAimJntData['refjoint'] )
    
    # make limb straighten limit setup using limitation of IK handle
    ikAttachGrp = transform.makeGroup( prefix = prefix + 'IkAttachGrp', referenceObj = limbIk, parentObj = ik1Ctrl.C )
    
    attachLimbIkHandle( 
                    prefix = prefix,
                    limbIkList = [limbIk],
                    rigmodule = rigmodule,
                    attachControl = ik1Ctrl.C,
                    ikAttachGrp = ikAttachGrp,
                    limbJointList = [upperJnt, midJnt, endJnt],
                    doLimit = doIkLimit,
                    stretchyAndBendy = stretchyAndBendy
                    )

    # add pole vector visual connection line
    
    poleVecLine = curve.makeConnectionLine( midJnt, ikPvCtrl.C )
    
    mc.parent( poleVecLine, rigmodule.Controls )
    rigmodule.connectIkFk( poleVecLine + '.v' )

    # make reference group to align IK rot control with wrist
    
    if buildIkRotCtl:
        
        elbowIkRotGrp = mc.group( n = prefix + 'IkRotElbowAlign_grp', em = 1, p = midJnt )
        mc.delete( mc.orientConstraint( endJnt, elbowIkRotGrp ) )
        
        worldIkRotGrp = mc.group( n = prefix + 'IkRotWorldAlign_grp', em = 1, p = ik1Ctrl.C )
        
      
        if doWorldAlignedEnd:
            
            transform.rotateAlignToReference( worldIkRotGrp, ik1Ctrl.C )
        
        else:
            
            mc.delete( mc.orientConstraint( endJnt, worldIkRotGrp ) )
        
        
        # IK controls attach and space switching        
        mc.pointConstraint( endJnt, ikRotCtrl.Off, n = prefix + name.removeSuffix( ikRotCtrl.Off ) + '_poc' )
    
    
    # =============================
    # make switches
    # =============================
    
    endSpaceName = 'hand'
    
    if isLeg:
        
        endSpaceName = 'foot'
        
    constraint.makeSwitch( ikPvCtrl.Off, rigmodule.Toggle, 'ikPoleVecSpace', ['local', 'global', 'follow', 'body', endSpaceName], 'parentConstraint', [rigmodule.LocalSpace, rigmodule.GlobalSpace, rigmodule.BodySpace, ikAimJntData['refjoint'], ikPvFootGrp],maintainOffset = 1, defaultIdx = 2 )
    
    
    constraint.makeSwitch( ik1Ctrl.Off, rigmodule.Toggle, 'ikSpace', ['local', 'global', 'body'], 'parentConstraint', [rigmodule.LocalSpace, rigmodule.GlobalSpace, rigmodule.BodySpace], maintainOffset = 1, defaultIdx = 1 )
    
    if buildIkRotCtl:
        
        ikRotSpaceAt = 'ikRotSpace'
        constraint.makeSwitch( ikRotCtrl.Off, rigmodule.Toggle, ikRotSpaceAt, ['fk', 'ik'], 'orientConstraint', [elbowIkRotGrp, worldIkRotGrp ], 0, defaultIdx = 1 )
        connect.reverse( rigmodule.Toggle + '.' + ikRotSpaceAt, ikRotCtrl.Off + '.v' )
    
    
    # =============================
    # FK
    # =============================
    
    # switch off IK blend for safe build of FK controls
    
    _safeFkBuildSwitch( rigmodule, upperJnt, midJnt, shoulderRot, elbowRot )
    
    # build FK controls
    
    fkPrefixSeq = []
    fkJointList = [ upperJnt, midJnt, endJnt ]
    
    if buildMiddleTweaker:
        
        fkJointList = [ midTweakUpperJnt, midTweakLowerJnt, endJnt ]
    
    for i, j in enumerate( fkJointList ):
        
        baseJntName = name.removeSide( j ).capitalize()
        p = prefix + 'Fk' + name.removeSuffix( baseJntName )
        fkPrefixSeq.append( p )
       
    upperFkCtrl = control.Control( lockHideChannels = [], prefix = fkPrefixSeq[0], moveTo = upperJnt, scale = 4 * ctrlScale, shape = 'cubeOnBaseX', ctrlParent = rigmodule.Controls )
    midFkCtrl = control.Control( lockHideChannels = ['t'], prefix = fkPrefixSeq[1], moveTo = midJnt, scale = 3 * ctrlScale, shape = 'cubeOnBaseX', ctrlParent = upperFkCtrl.C )
    endFkCtrl = control.Control( lockHideChannels = ['t'], prefix = fkPrefixSeq[2], moveTo = endJnt, scale = 3 * ctrlScale, shape = 'cubeOnBaseX', ctrlParent = midFkCtrl.C )
    
    # connect FK controls to joints    
    mc.orientConstraint( upperFkCtrl.C, upperJnt )
    mc.connectAttr( upperFkCtrl.C + '.ro', upperJnt + '.ro' )
    
    for c, j in zip( [midFkCtrl, endFkCtrl], [midJnt, endJnt] ):
        
        mc.connectAttr( c.C + '.r', j + '.r' )
        mc.connectAttr( c.C + '.ro', j + '.ro' )
    '''
    # lock mid joint unwanted rotation axis
    for axis in ['x', 'y' ]:
        
        mc.setAttr( midFkCtrl.C + '.r' + axis, l = 1, k = 0 )
    '''
    # attach FK controls to joints
    if stretchyAndBendy:
        
        for i, ctrl, jnt in zip( range( 2 ), [midFkCtrl, endFkCtrl], [midJnt, endJnt] ):
            
            print 'ctrl, jnt', ctrl.Off, jnt
            
            mc.connectAttr( jnt + '.tx', ctrl.Off + '.tx' )
            
            print 'connected:', ctrl.Off, jnt
            
    # connect ikfk reverse vis to fk control
    ikFkReverse = mc.createNode( 'reverse', n = prefix + 'IkFk_rev' )
    rigmodule.connectIkFk( ikFkReverse + '.ix' )
    mc.connectAttr( ikFkReverse + '.ox', upperFkCtrl.Off + '.v' )
   
    # mc.parentConstraint( rigmodule.LocalSpace, upperFkCtrl.Off, mo = True )
    
    # ---------------------
    # FK and hand switches
    # ---------------------
    
    # make group for IK space target for end joint, which is oriented the same as the joint
    ikEndJntTargetGrp = mc.group( n = prefix + 'IkSafeOffsetHand_grp', em = 1, p = endJnt )
    mc.parent( ikEndJntTargetGrp, ik1Ctrl.C )
    
    if buildIkRotCtl:
        
        mc.parent( ikEndJntTargetGrp, ikRotCtrl.C )
        mc.makeIdentity( ikEndJntTargetGrp, a = 0, r = 1 )
    
    constraint.makeSwitch( upperFkCtrl.Off, rigmodule.Toggle, 'fkSpace', ['local', 'global', 'body'], 'orientConstraint', [rigmodule.LocalSpace, rigmodule.GlobalSpace, rigmodule.BodySpace], 1, defaultIdx = 2 )
    constraint.makeSwitch( endFkCtrl.Off, rigmodule.Toggle, 'fkHandSpace', ['local', 'global', 'body'], 'orientConstraint', [midJnt, rigmodule.GlobalSpace, rigmodule.BodySpace], 1 )
    constraint.makeSwitch( endJnt, rigmodule.Toggle, 'fkIk', ['fk', 'ik'], 'orientConstraint', [endFkCtrl.C, ikEndJntTargetGrp ], 0 )
   
    # set IK as default
    
    mc.setAttr( rigmodule.Toggle + '.fkIk', 1 )
    
    #===========================================================================
    # IK base control
    #===========================================================================
    
    ikBaseCtrl = control.Control( lockHideChannels = ['rx', 'rz'], prefix = prefix + 'IkBase', translateTo = upperJnt, scale = 3.5 * ctrlScale, shape = 'sphere' )
    mc.parentConstraint( rigmodule.LocalSpace, ikBaseCtrl.Off, mo = 1 )
    mc.parent( ikBaseCtrl.Off, rigmodule.Controls )
    rigmodule.connectIkFk( ikBaseCtrl.Off + '.v' )
    
    # attach position of upper joint to IK base control and FK upper control
    if isLeg:
        
        upperJntPointConst = mc.pointConstraint( upperFkCtrl.C, ikBaseCtrl.C, upperJnt )[0]
        constraint.setupDualConstraintBlend( upperJntPointConst, rigmodule.getIkFkAt() )

    #===========================================================================
    # add middle tweaker control and joints
    #===========================================================================
    
    if buildMiddleTweaker:
        
        mc.connectAttr( upperJnt + '.t', midTweakUpperJnt + '.t' )
        
        armJoints = [upperJnt, midJnt, endJnt]
        middleTweakJoints = [ midTweakUpperJnt, midTweakLowerJnt, midTweakEndJnt ]
        
        _buildMiddleTweaker( rigmodule, prefix, armJoints, middleTweakJoints, ctrlScale, upperFkCtrl, ikBaseCtrl, stretchyAndBendy, buildBendySubControls )
    
    
    if buildSnapSetup:
        _buildSnapSetup( rigmodule, prefix, toggleCtrl.C, upperJnt, midJnt, endJnt, upperFkCtrl.C, midFkCtrl.C, endFkCtrl.C, ik1Ctrl.C, ikPvCtrl.C, limbIk )

    return {
    'module':rigmodule,
    'mainGrp':rigmodule.Main,
    'ctrlGrp':rigmodule.Controls,
    'ik1Ctrl':ik1Ctrl,
    'ikRotCtrl':ikRotCtrl,
    'ikBaseCtrl':ikBaseCtrl,
    'fkControls':[ upperFkCtrl, midFkCtrl, endFkCtrl ],
    'limbIk':limbIk,
    'globalSpaceGrp':rigmodule.GlobalSpace,
    'bodySpaceGrp':rigmodule.BodySpace,
    'localSpaceGrp':rigmodule.LocalSpace,
    'toggleGrp':rigmodule.Toggle,
    'settingsGrp':rigmodule.Settings,
    'upperJnt':upperJnt,
    'midJnt':midJnt,
    'toggleCtrl':toggleCtrl,
    'ikAttachGrp':ikAttachGrp
    }

def _buildMiddleTweaker( rigmodule, prefix, armJoints, tweakJoints, ctrlScale, upperFkCtrl, ikBaseCtrl, stretchyAndBendy, buildSubControls = False ):
    
    """
    :param subControls: bool, add subcontrols to bendy joints
    """
    
    # tweakJointNames = [ name.removeSuffix( j ) + 'Tweaker' for j in [ upperJnt, lowerJnt, endJnt ] ]
    # tweakJoints = joint.duplicateChain( [ upperJnt, lowerJnt, endJnt ], newjointnames = tweakJointNames )
    
    upperJnt = armJoints[0]
    lowerJnt = armJoints[1]
    endJnt = armJoints[2]
    
    # this is how tweak joints are used
    upperTweakJnt = tweakJoints[0]
    lowerTweakJnt = tweakJoints[1]
    endTweakJnt = tweakJoints[2]
    
    
    # attach position of upper tweak joint
    # constraint.makeSwitch( upperTweakJnt, rigmodule.Toggle, 'fkIk', ['fk', 'ik'], 'pointConstraint', [upperFkCtrl.C, ikBaseCtrl.C ], 0 )
    
    # adjust radius
    
    mainJointRad = mc.getAttr( upperJnt + '.radi' )
    temp = [ mc.setAttr( j + '.radi', mainJointRad * 1.2 ) for j in tweakJoints ]
    
    upperTweakerIk = mc.ikHandle( n = prefix + 'UpperTweaker_ikh', sol = 'ikSCsolver', sj = tweakJoints[0], ee = tweakJoints[1] )[0]
    lowerTweakerIk = mc.ikHandle( n = prefix + 'LowerTweaker_ikh', sol = 'ikSCsolver', sj = tweakJoints[1], ee = tweakJoints[2] )[0]
    
    mc.hide( upperTweakerIk, lowerTweakerIk )
    
    # make tweaker control
    
    tweakerCtrl = control.Control( lockHideChannels = ['r'], prefix = prefix + 'Tweaker', translateTo = lowerJnt, scale = 3.0 * ctrlScale, colorName = 'secondary', shape = 'sphere', ctrlParent = rigmodule.Controls )
    
    tweakerLocalDriverGrp = transform.makeGroup( prefix = prefix + 'TweakerLocalDriver', referenceObj = tweakerCtrl.C, parentObj = rigmodule.Parts )
    mc.orientConstraint( upperJnt, tweakerLocalDriverGrp, mo = 1 )
    mc.pointConstraint( lowerJnt, tweakerLocalDriverGrp, mo = 1 )
    
    # make local and global space switch for Tweaker control
    constraint.makeSwitch( tweakerCtrl.Off, rigmodule.Toggle, 'tweakerSpace', ['local', 'global'], 'parentConstraint', [tweakerLocalDriverGrp, rigmodule.GlobalSpace], 1, defaultIdx = 0 )
    
    
    # attach IK handles and joint chain
    
    mc.parent( upperTweakerIk, tweakerCtrl.C )
    mc.parent( lowerTweakerIk, lowerJnt )
    mc.connectAttr( endJnt + '.t', lowerTweakerIk + '.t' )
    
    
    # setup joint stretch scale
    
    distRatioNodes = []
    
    for nodePrefix, objA, objB, scaleJnt in zip( [ 'Upper', 'Lower' ], [ upperJnt, tweakerCtrl.C ], [ tweakerCtrl.C, endJnt ], [ tweakJoints[0], tweakJoints[1] ] ):
        
        origDist = transform.measureDistanceBetween2Objs( objA, objB )
        distNode = distanceBetween.buildAndConnect( objA, objB, prefix = prefix + nodePrefix + 'Tweaker' )
        scaleCompensNode = mc.createNode( 'multDoubleLinear', n = prefix + nodePrefix + 'Tweaker_mdl' )
        mc.setAttr( scaleCompensNode + '.i1', origDist )
        mc.connectAttr( rigmodule.getModuleScalePlug(), scaleCompensNode + '.i2' )
        distRatioNode = mc.createNode( 'multiplyDivide', n = prefix + nodePrefix + 'Tweaker_mdv' )
        distRatioNodes.append( distRatioNode )
        mc.setAttr( distRatioNode + '.operation', 2 )
        mc.connectAttr( distNode + '.distance', distRatioNode + '.i1x' )
        mc.connectAttr( scaleCompensNode + '.o', distRatioNode + '.i2x' )
        mc.connectAttr( distRatioNode + '.ox', scaleJnt + '.sx' )
    
    # make stretchy and bendy setup
    
    if stretchyAndBendy:
        
        # add attributes
        
        bendyAmount = 'bendyAmount'
        mc.addAttr( rigmodule.Toggle, ln = bendyAmount, at = 'float', k = True, min = 0, max = 1, dv = 0 )
        
        
        # make bending space frame setup
        
        bendySetupGrp = mc.group( n = prefix + 'BendySetup_grp', em = True, p = rigmodule.Parts )
        bendSpaceAimedGrp = transform.makeGroup( prefix = prefix + 'BendySpaceAimed', referenceObj = endJnt, parentObj = bendySetupGrp, matchPositionOnly = True )
        mc.pointConstraint( upperJnt, endJnt, bendSpaceAimedGrp )
        mc.aimConstraint( upperJnt, bendSpaceAimedGrp, aim = [1, 0, 0], u = [0, 0, 1], wuo = tweakJoints[1], wut = 'objectrotation' )
        
        bendSpaceTangentGrp = mc.group( n = prefix + 'BendySpaceTangent_grp', p = bendSpaceAimedGrp, em = True )
        mc.pointConstraint( tweakJoints[1], bendSpaceTangentGrp )
        
        # make bendy CV holders
        
        upperLength = transform.measureDistanceBetween2Objs( upperJnt, lowerJnt )    
        lowerLength = transform.measureDistanceBetween2Objs( lowerJnt, endJnt )
        
        tangentPercentage = 0.5
        upperCVoffset = upperLength * tangentPercentage
        lowerCVoffset = lowerLength * -tangentPercentage
        
        upperBendyCvGrp = mc.group( n = prefix + 'BendyUpperBendCvHolder_grp', p = bendSpaceTangentGrp, em = True )
        upperBendyCvGrpPosMultiNode = mc.createNode( 'multDoubleLinear', n = prefix + 'BendyUpperBendCvHolderT_mdv' )
        mc.setAttr( upperBendyCvGrpPosMultiNode + '.i1', upperCVoffset )
        mc.connectAttr( distRatioNodes[0] + '.ox', upperBendyCvGrpPosMultiNode + '.i2' )
        mc.connectAttr( upperBendyCvGrpPosMultiNode + '.o', upperBendyCvGrp + '.tx' )
        
        lowerBendyCvGrp = mc.group( n = prefix + 'BendyLowerBendCvHolder_grp', p = bendSpaceTangentGrp, em = True )
        lowerBendyCvGrpPosMultiNode = mc.createNode( 'multDoubleLinear', n = prefix + 'BendyLowerBendCvHolderT_mdv' )
        mc.setAttr( lowerBendyCvGrpPosMultiNode + '.i1', lowerCVoffset )
        mc.connectAttr( distRatioNodes[1] + '.ox', lowerBendyCvGrpPosMultiNode + '.i2' )
        mc.connectAttr( lowerBendyCvGrpPosMultiNode + '.o', lowerBendyCvGrp + '.tx' )
        
        
        tangentPercentageRemainder = 1 - tangentPercentage
        
        upperStraightCvGrp = mc.group( n = prefix + 'BendyUpperStraightHolder_grp', p = bendSpaceAimedGrp, em = True )
        upperStraightPCon = mc.pointConstraint( upperJnt, tweakJoints[1], upperStraightCvGrp )[0]
        upperStraightPConWeightAts = constraint.getWeightAttrs( upperStraightPCon )
        mc.setAttr( upperStraightPCon + '.' + upperStraightPConWeightAts[0], tangentPercentage )
        mc.setAttr( upperStraightPCon + '.' + upperStraightPConWeightAts[1], tangentPercentageRemainder )
        
        lowerStraightCvGrp = mc.group( n = prefix + 'BendyLowerStraightHolder_grp', p = bendSpaceAimedGrp, em = True )
        lowerStraightPCon = mc.pointConstraint( endJnt, tweakJoints[1], lowerStraightCvGrp )[0]
        lowerStraightPConWeightAts = constraint.getWeightAttrs( lowerStraightPCon )
        mc.setAttr( lowerStraightPCon + '.' + lowerStraightPConWeightAts[0], tangentPercentage )
        mc.setAttr( lowerStraightPCon + '.' + lowerStraightPConWeightAts[1], tangentPercentageRemainder )
        
        # make bendy blend groups
        
        upperBendyBlendGrp = mc.group( n = prefix + 'BendyUpperBlend_grp', p = bendSpaceAimedGrp, em = True )
        upperBendyBlendGrpPointConst = mc.pointConstraint( upperStraightCvGrp, upperBendyCvGrp, upperBendyBlendGrp )[0]
        constraint.setupDualConstraintBlend( upperBendyBlendGrpPointConst, rigmodule.Toggle + '.' + bendyAmount )
        
        lowerBendyBlendGrp = mc.group( n = prefix + 'BendyLowerBlend_grp', p = bendSpaceAimedGrp, em = True )
        lowerBendyBlendGrp = mc.pointConstraint( lowerStraightCvGrp, lowerBendyCvGrp, lowerBendyBlendGrp )[0]
        constraint.setupDualConstraintBlend( lowerBendyBlendGrp, rigmodule.Toggle + '.' + bendyAmount )
        
        # make bendy curves
        
        bendySetupNtGrp = mc.group( n = prefix + 'BendySetupNt_grp', em = True, p = rigmodule.PartsNt )
        
        upperBendyCrv = curve.from2objects( lowerJnt, upperJnt, prefix = prefix + 'UpperBendy', degree = 2 )
        lowerBendyCrv = curve.from2objects( lowerJnt, endJnt, prefix = prefix + 'UpperBendy', degree = 2 )
        
        mc.parent( upperBendyCrv, lowerBendyCrv, bendySetupNtGrp )
        
        # offset middle curve CVs
        
        upperMidCvPos = mc.xform( upperBendyBlendGrp, q = True, t = True, ws = True )
        mc.xform( upperBendyCrv + '.cv[1]', t = upperMidCvPos, ws = True )
        
        lowerMidCvPos = mc.xform( lowerBendyBlendGrp, q = True, t = True, ws = True )
        mc.xform( lowerBendyCrv + '.cv[1]', t = lowerMidCvPos, ws = True )
        
        # attach bendy curves
        
        mc.cluster( upperBendyCrv + '.cv[2]', n = prefix + 'UpperBendyStart_cls', wn = [upperJnt, upperJnt], bs = True )
        mc.cluster( upperBendyCrv + '.cv[1]', n = prefix + 'UpperBendyMid_cls', wn = [upperBendyBlendGrp, upperBendyBlendGrp], bs = True )
        mc.cluster( upperBendyCrv + '.cv[0]', n = prefix + 'UpperBendyStart_cls', wn = [tweakJoints[1], tweakJoints[1]], bs = True )
        
        mc.cluster( lowerBendyCrv + '.cv[0]', n = prefix + 'LowerBendyStart_cls', wn = [tweakJoints[1], tweakJoints[1]], bs = True )
        mc.cluster( lowerBendyCrv + '.cv[1]', n = prefix + 'LowerBendyMid_cls', wn = [lowerBendyBlendGrp, lowerBendyBlendGrp], bs = True )
        mc.cluster( lowerBendyCrv + '.cv[2]', n = prefix + 'LowerBendyStart_cls', wn = [endJnt, endJnt], bs = True )
        
        # make joints
        
        upperBendyJoints, upperBendyIk = joint.makeFromCurveWithOptions( upperBendyCrv, prefix = prefix + 'BendyUpper', doIK = 1, doStretchy = 1, numJoints = 6, scalePlug = rigmodule.getModuleScalePlug() )
        mc.parent( upperBendyIk, rigmodule.PartsNt )
        upperBendyJointsOffsetGrp = transform.makeOffsetGrp( upperBendyJoints[0], inOrigin = True )
        mc.parent( upperBendyJointsOffsetGrp, rigmodule.Joints )
        mc.orientConstraint( tweakJoints[0], upperBendyJointsOffsetGrp, mo = True )
        
        lowerBendyJoints, lowerBendyIk = joint.makeFromCurveWithOptions( lowerBendyCrv, prefix = prefix + 'BendyLower', doIK = 1, doStretchy = 1, numJoints = 6, scalePlug = rigmodule.getModuleScalePlug() )
        mc.parent( lowerBendyIk, rigmodule.PartsNt )
        lowerBendyJointsOffsetGrp = transform.makeOffsetGrp( lowerBendyJoints[0], inOrigin = True )
        mc.parent( lowerBendyJointsOffsetGrp, rigmodule.Joints )
        mc.orientConstraint( tweakJoints[1], lowerBendyJointsOffsetGrp, mo = True )
        
        # adjust joints radius
        
        mainJntRadius = mc.getAttr( tweakJoints[0] + '.radius' )
        
        for jntList in [upperBendyJoints, lowerBendyJoints]:
            
            for jnt in jntList:
                
                mc.setAttr( jnt + '.radius', mainJntRadius )
        
        # add sub controls for detailed adjustments
        
        subControls = []
        
        if buildSubControls:
            
            driverSubJoints = upperBendyJoints[1:-1] + lowerBendyJoints[1:-1]
            
            for dj in driverSubJoints:
                
                jntPrefix = name.removeSuffix( dj )
                dj = mc.rename( dj, jntPrefix + 'Base_jnt' )
                sj = joint.makeSingleJoint( prefix = jntPrefix, refObject = dj, refJointRadiusMulti = 1.3, colorIdx = 1, parentObj = dj, freezeRotation = True )
                
                sjCtrl = control.Control( prefix = jntPrefix, moveTo = dj, defLockHide = ['v'], shape = 'circle', scale = ctrlScale * 3, colorName = 'secondary', ctrlParent = rigmodule.Controls )
                subControls.append( sjCtrl )
                
                mc.parentConstraint( dj, sjCtrl.Off )
                mc.parentConstraint( sjCtrl.C, sj )
                mc.scaleConstraint( sjCtrl.C, sj )
                
        
        # add joints twist
        twistUpperOffsetAt = 'bendyUpperTwistOffset'
        mc.addAttr( rigmodule.Toggle, ln = twistUpperOffsetAt, at = 'float', k = True )
        twistUpperOffsetPlug = rigmodule.Toggle + '.' + twistUpperOffsetAt
        
        upperTwistRefJntData = joint.makeTwistRefJoint( baseJnt = tweakJoints[0], endJnt = tweakJoints[1], refObject = rigmodule.LocalSpace, prefix = prefix + 'BendyUpperTwist', twistOffsetDriverPlug = twistUpperOffsetPlug )
        mc.hide( upperTwistRefJntData['refjoint'], upperTwistRefJntData['ikjoint'], upperTwistRefJntData['ikHandle'] )
        connect.negate( upperTwistRefJntData['mainGrp'] + '.twist', upperBendyIk + '.twist', prefix = prefix + 'BendyUpperTwistNegate_utl' )
        
        lowerTwistRefJntData = joint.makeTwistRefJoint( baseJnt = tweakJoints[1], endJnt = endJnt, refObject = endJnt, prefix = prefix + 'BendyLowerTwist' )
        mc.hide( lowerTwistRefJntData['refjoint'], lowerTwistRefJntData['ikjoint'], lowerTwistRefJntData['ikHandle'] )
        mc.connectAttr( lowerTwistRefJntData['mainGrp'] + '.twist', lowerBendyIk + '.twist' )
        
def _safeFkBuildSwitch( rigmodule, shoulderJnt, elbowJnt, shoulderRot, elbowRot ):
    
    '''
    switch to FK and set original joint values
    '''
    
    mc.setAttr( rigmodule.Toggle + '.fkIk', 0 )
    mc.setAttr( shoulderJnt + '.r', shoulderRot[0], shoulderRot[1], shoulderRot[2] )
    mc.setAttr( elbowJnt + '.r', elbowRot[0], elbowRot[1], elbowRot[2] )
    
def _connectIkHandle( limbIk, ik1Ctrl, rigmodule, ikPvCtrl ):
    
    mc.pointConstraint(ik1Ctrl.C, limbIk, mo = True)
    mc.parent( limbIk, rigmodule.PartsNt )    
    mc.poleVectorConstraint( ikPvCtrl.C, limbIk )
    
def attachLimbIkHandle( 
                        prefix,
                        limbIkList,
                        rigmodule,
                        attachControl,
                        ikAttachGrp,
                        limbJointList,
                        doLimit = True,
                        straightLimitPercent = 0.998,
                        stretchyAndBendy = False,
                        addAttributes = True
                        ):    
    
    '''
    attach IK handle to rig module, with optional soft limit by default
    
    
    :param prefix: str, prefix to name new objects
    :param limbIkList: list(str), name of limb IK handle
    :param rigmodule: instance, Module.module instance 
    :param ikAttachGrp: str, name of transform name for attaching IK handle
    :param limbJointList: list(str), list of limb joint names from top down
    :param doLimit: bool, flag to create length limit setup
    :param straightLimitPercent: float, default straight limb limit percent value
    :param stretchyAndBendy: bool, if True then make this setup stretchy, bendy part is currently made in buildMiddleTweaker setup
    :param addAttributes: bool, add driving limit percent attribute to Settings group of provided rigmodule and connect it to the system
    :return: None
    '''    
    prefix = prefix + 'IkAttach'
    ikAttachGrpName = prefix + 'IkAttach_grp'

    # add stretch amount attribute
    stretchAmountAt = 'stretchAmount'
    upperFkStretchValAt = 'fkStretchUpper'
    lowerFkStretchValAt = 'fkStretchLower'
    
    if stretchyAndBendy:
        
        mc.addAttr( rigmodule.Toggle, ln = stretchAmountAt, at = 'float', k = True, min = 0, max = 1, dv = 1 )
        mc.addAttr( rigmodule.Toggle, ln = upperFkStretchValAt, at = 'float', k = True, min = 0.01, max = 3, dv = 1 )
        mc.addAttr( rigmodule.Toggle, ln = lowerFkStretchValAt, at = 'float', k = True, min = 0.01, max = 3, dv = 1 )
    

    if not doLimit:
        
        for limbIk in limbIkList:
            
            transform.parent( [limbIk], parentObj = ikAttachGrp )
            
        if not stretchyAndBendy:
            
            return 
    

        # add stretch option
    
        aimMeasureGrp = transform.makeGroup( prefix = prefix + 'AimStretchMeasure', referenceObj = limbJointList[0], parentObj = rigmodule.LocalSpace )
        mc.aimConstraint( ikAttachGrp, aimMeasureGrp, aim = [1, 0, 0], u = [0, 0, 1], wut = 'none' )
        attachPointMeasureGrp = mc.group( n = prefix + 'AttachStretchMeasure', em = True, p = aimMeasureGrp )
        mc.pointConstraint( ikAttachGrp, attachPointMeasureGrp, skip = ['y', 'z'] )
    
        origDist = mc.getAttr( attachPointMeasureGrp + '.tx' )
        stretchRatioNode = mc.createNode( 'multiplyDivide', n = prefix + 'StretchRatio_mdv' )
        mc.setAttr( stretchRatioNode + '.operation', 2 )  # divide
        mc.connectAttr( attachPointMeasureGrp + '.tx', stretchRatioNode + '.i1x' )
        mc.setAttr( stretchRatioNode + '.i2x', origDist )    
        
        # IK FK blend
        ikfkStretchBlendNode = mc.createNode( 'multDoubleLinear', n = prefix + 'IkFkStretchBlend_mdl' )
        mc.connectAttr( rigmodule.Toggle + '.' + stretchAmountAt, ikfkStretchBlendNode + '.i1' )
        mc.connectAttr( rigmodule.getIkFkAt(), ikfkStretchBlendNode + '.i2' )
        
        clampNode = mc.createNode( 'clamp', n = prefix + 'StretchClamp_clp' )
        mc.setAttr( clampNode + '.minR', 1.0 )
        mc.setAttr( clampNode + '.maxR', 10.0 )
        mc.connectAttr( stretchRatioNode + '.ox', clampNode + '.inputR' )
    
        # connect stretch
        fkStretchValueAts = [upperFkStretchValAt, lowerFkStretchValAt]
        
        for i, jnt in enumerate( [limbJointList[1], limbJointList[2]] ):
            
            stretchResultBlendNode = mc.createNode( 'blendColors', n = prefix + 'StretchResult%d_blc' % ( i + 1 ) )
            mc.connectAttr( ikfkStretchBlendNode + '.o', stretchResultBlendNode + '.blender' )
            mc.connectAttr( clampNode + '.outputR', stretchResultBlendNode + '.color1R' )
            
            fkStretchValueAt = fkStretchValueAts[i]            
            mc.connectAttr( rigmodule.Toggle + '.' + fkStretchValueAt, stretchResultBlendNode + '.color2R' )
            
            multiNode = mc.createNode( 'multDoubleLinear', n = prefix + 'StretchTx_%d_mdl' % ( i + 1 ) )
            origTranslateVal = mc.getAttr( jnt + '.tx' )
            mc.setAttr( multiNode + '.i1', origTranslateVal )
            mc.connectAttr( stretchResultBlendNode + '.outputR', multiNode + '.i2' )
            mc.connectAttr( multiNode + '.o', jnt + '.tx' )
            
        
        return   
    
    #===========================================================================
    # build limit IK handle attachment
    #===========================================================================
    
    # get straight joints length
    
    straightLength = transform.measureDistanceBetweenMultipleObjects( limbJointList )
    limitLenNodes = []
    
    # make aimed limit group
    
    straightLengthAt = 'straightLength'
    
    aimedGrp = mc.group( n = prefix + 'Aimed_grp', em = 1, p = rigmodule.Parts )
    mc.addAttr( aimedGrp, ln = straightLengthAt, at = 'float' )
    mc.setAttr( aimedGrp + '.' + straightLengthAt, straightLength, l = 1 )
    
    mc.pointConstraint( limbJointList[0], aimedGrp )
    mc.aimConstraint( attachControl, aimedGrp, aim = [1, 0, 0], u = [0, 0, 1], wu = [0, 0, 1], wuo = rigmodule.LocalSpace, wut = 'objectrotation' )
        
    # make current length group
    currentLengthGrp = mc.group( n = prefix + 'CurrentLength_grp', em = 1, p = aimedGrp )
    mc.pointConstraint( attachControl, currentLengthGrp )
    currentPercentNode = mc.createNode( 'multiplyDivide', n = prefix + 'CurrentLengthPercent_mdv' )
    mc.setAttr( currentPercentNode + '.operation', 2 )  # divide
    mc.connectAttr( currentLengthGrp + '.tx', currentPercentNode + '.i1x' )
    mc.connectAttr( aimedGrp + '.' + straightLengthAt, currentPercentNode + '.i2x' )
    
    maxCurrentLengthVal = mc.getAttr( currentLengthGrp + '.tx' )    
    
    for limbIk in limbIkList:
        
        limbIkPrefix = name.removeSuffix( limbIk )
        
        # get current length IK handle ratio
        ikClosestJnt = transform.findClosestObject( limbIk, limbJointList )
        ikClosestJntIndex = limbJointList.index( ikClosestJnt )
        ikCurrentLengthVal = transform.measureDistanceBetweenMultipleObjects( limbJointList[:ikClosestJntIndex + 1] )
        currentLengthRatio = ikCurrentLengthVal / maxCurrentLengthVal
        
        # make limit position group
        limitPositionGrp = mc.group( n = limbIkPrefix + 'LimitPosition_grp', em = 1, p = aimedGrp )
        limitLenNode = mc.createNode( 'multDoubleLinear', n = limbIkPrefix + 'LimitLength_mdl' )
        limitLenNodes.append( limitLenNode )
        mc.connectAttr( aimedGrp + '.' + straightLengthAt, limitLenNode + '.i1' )
        mc.setAttr( limitLenNode + '.i2', straightLimitPercent )
        limitLenRatioNode = mc.createNode( 'multDoubleLinear', n = limbIkPrefix + 'LimitLengthRatio_mdl' )
        mc.setAttr( limitLenRatioNode + '.i1', currentLengthRatio, l = 1 )
        mc.connectAttr( limitLenNode + '.o', limitLenRatioNode + '.i2' )
        mc.connectAttr( limitLenRatioNode + '.o', limitPositionGrp + '.tx' )
        
        # make IK attach group
        # WIP - currently hard limit - remapValue to be added
        
        ikLimitedGrp = mc.group( n = limbIkPrefix + 'IkLimited_grp', em = 1, p = limitPositionGrp )
        mc.delete( mc.pointConstraint( limbIk, ikLimitedGrp ) )
        mc.transformLimits( ikLimitedGrp, enableTranslationX = [0, 1], translationX = [0, 0] )
        
        limbIkParents = mc.listRelatives( limbIk, p = True )
        
        if limbIkParents:
            
            mc.parentConstraint( limbIkParents[0], ikLimitedGrp, mo = True )
        
        else:
            
            mc.pointConstraint( ikAttachGrp, ikLimitedGrp, mo = True )
        
        mc.parent( limbIk, ikLimitedGrp )
    
    # setup constraint blend for IK handle
    if stretchyAndBendy:
        
        ikStretchPosGrp = mc.group( n = prefix + 'IkStretchPos_grp', em = 1, p = limitPositionGrp )
        mc.pointConstraint( ikAttachGrp, ikStretchPosGrp )
        
        for limbIk in limbIkList:
            
            limbIkConst = mc.pointConstraint( ikLimitedGrp, ikStretchPosGrp, limbIk, mo = True )[0]
            constraint.setupDualConstraintBlend( limbIkConst, driverat = rigmodule.Toggle + '.' + stretchAmountAt )
        
                    
    # create stretchy system with IK limit
    # NOTE: currently only works on 2-bone IK setups
    if stretchyAndBendy:
        
        # compute current stretch with IK limit
        stretchPercentNode = mc.createNode( 'multiplyDivide', n = prefix + 'StretchPercent_mdv' )
        mc.setAttr( stretchPercentNode + '.operation', 2 )  # divide
        mc.connectAttr( currentLengthGrp + '.tx', stretchPercentNode + '.i1x' )
        mc.connectAttr( limitLenNode + '.o', stretchPercentNode + '.i2x' )
        stretchClampToOneNode = mc.createNode( 'clamp', n = prefix + 'StretchClampToOne_clp' )
        mc.setAttr( stretchClampToOneNode + '.minR', 1 )
        mc.setAttr( stretchClampToOneNode + '.maxR', 1000 )
        mc.connectAttr( stretchPercentNode + '.outputX', stretchClampToOneNode + '.inputR' )
        
        ikStretchAmountNode = mc.createNode( 'multDoubleLinear', n = prefix + 'StretchIkAmount_mdl' )
        mc.connectAttr( rigmodule.Toggle + '.' + stretchAmountAt, ikStretchAmountNode + '.i1' )
        rigmodule.connectIkFk( ikStretchAmountNode + '.i2' )
        
        # connect main limb joints to stretching
        jntLimbPrefixes = ['upper', 'lower']
        
        for i, ( jnt, jntPrefix ) in enumerate( zip( [limbJointList[1], limbJointList[2]], jntLimbPrefixes ) ):
            
            jntAxisMultiNode = mc.createNode( 'multDoubleLinear', n = prefix + 'StretchJointAxis%d' % ( i + 1 ) )
            jntTx = mc.getAttr( jnt + '.tx' )
            mc.setAttr( jntAxisMultiNode + '.i1', jntTx )
            
            connect.multiplyDifference( stretchClampToOneNode + '.outputR', destplug = jntAxisMultiNode + '.i2',
                                        multPlug = ikStretchAmountNode + '.o', prefix = prefix + 'Stretch%d' % ( i + 1 ), baseValue = 1.0 )
            
            stretchAddAt = jntPrefix + 'StretchMultiAdd'
            mc.addAttr( rigmodule.Toggle, ln = stretchAddAt, at = 'float', k = True )
            stretchAddNode = mc.createNode( 'addDoubleLinear', n = prefix + 'StretchJointAdd%d' % ( i + 1 ) )
            mc.connectAttr( jntAxisMultiNode + '.o', stretchAddNode + '.i1' )
            mc.connectAttr( rigmodule.Toggle + '.' + stretchAddAt, stretchAddNode + '.i2' )
            
            mc.connectAttr( stretchAddNode + '.o', jnt + '.tx' )
            
    # make control attributes and connect them to the system
    if addAttributes:
        
        _attachLimbIkHandle_addAttributes( 
                                          rigmodule,
                                          limitLenNodes = limitLenNodes,
                                          currentPercentNode = currentPercentNode,
                                          straightLimitPercentAt = straightLimitPercentAt,
                                          currentLengthPercentAt = currentLengthPercentAt,
                                          straightLimitPercent = straightLimitPercent
                                          )        
        
def _attachLimbIkHandle_addAttributes( rigmodule, limitLenNodes = None, currentPercentNode = None, straightLimitPercentAt = 'straightLimitPerc', currentLengthPercentAt = 'currentLengthPerc', straightLimitPercent = 0.998 ):
    
    '''
    Internal Function
    
    add driving attributes and connect them to translate limit system
    for IK handle attach setup
    '''
    
    mc.addAttr( rigmodule.Settings, ln = straightLimitPercentAt, at = 'float', k = 1, min = 0.5, max = 1.0, dv = straightLimitPercent )
    mc.addAttr( rigmodule.Settings, ln = currentLengthPercentAt, at = 'float', k = 1 )
    
    for limitLenNode in limitLenNodes:
        
        mc.connectAttr( rigmodule.Settings + '.' + straightLimitPercentAt, limitLenNode + '.i2' )
    
    mc.connectAttr( currentPercentNode + '.ox', rigmodule.Settings + '.' + currentLengthPercentAt )

def _buildSnapSetup( rigmodule, prefix, toggleCtrl, upperJnt, midJnt, endJnt, upperFkCtrl, midFkCtrl, endFkCtrl, ik1Ctrl, ikPvCtrl, limbIk  ):
    
    '''
    create a duplicate of both chain, fk - ik and move it with same setup so we can use it as reference for
    fk - ik snap
    '''
    # make fk duplicate setup
    driverJointNames = [ name.removeSuffix( j ) + 'FkDriven' for j in [ upperJnt, midJnt, endJnt ] ]
    drivenFkJnts = joint.duplicateChain( [ upperJnt, midJnt, endJnt ], newjointnames = driverJointNames )
    mc.parent( drivenFkJnts[0], rigmodule.Joints )
    
    # connect FK controls to joints    
    mc.orientConstraint( upperFkCtrl, drivenFkJnts[0] )
    mc.connectAttr( upperFkCtrl + '.ro', drivenFkJnts[0] + '.ro' )
    
    for c, j in zip( [midFkCtrl, endFkCtrl], [drivenFkJnts[1], drivenFkJnts[2] ]):
        
        mc.connectAttr( c + '.r', j + '.r' )
        mc.connectAttr( c + '.ro', j + '.ro' )
    
    mc.pointConstraint( upperJnt, drivenFkJnts[0], mo = True )
    
    # make ik duplicate setup
    driverJointNames = [ name.removeSuffix( j ) + 'ikDriven' for j in [ upperJnt, midJnt, endJnt ] ]
    drivenIkJnts = joint.duplicateChain( [ upperJnt, midJnt, endJnt ], newjointnames = driverJointNames )
    mc.parent( drivenIkJnts[0], rigmodule.Joints )
    
    # create messsage attributes so fkik script will know what to take
    _createMessageAttributes( prefix, toggleCtrl, upperJnt, midJnt, endJnt, upperFkCtrl, midFkCtrl, endFkCtrl, ik1Ctrl, ikPvCtrl, limbIk, drivenIkJnts, drivenFkJnts )
    
def _createMessageAttributes( prefix, toggleCtrl, upperJnt, midJnt, endJnt, upperFkCtrl, midFkCtrl, endFkCtrl, ik1Ctrl, ikPvCtrl, limbIk, drivenIkJnts, drivenFkJnts ):
    
    '''
    create message attributes to later access to multiple info no matter name changes eg: ik-fk snap
    '''
    # add an attribute to make toggle control to make it valid for fk-ik snap
    mc.addAttr( toggleCtrl, ln = 'fkIkSnapable', dt = 'string' )
    
    #===========================================================================
    # add respective message attributes with connections
    #===========================================================================
    # limb joints
    mc.addAttr( toggleCtrl, ln = 'upperJnt', at = 'message' )
    mc.connectAttr( upperJnt + '.message', toggleCtrl + '.upperJnt' )
    
    mc.addAttr( toggleCtrl, ln = 'midJnt', at = 'message' )
    mc.connectAttr( midJnt + '.message', toggleCtrl + '.midJnt' )
    
    mc.addAttr( toggleCtrl, ln = 'endJnt', at = 'message' )
    mc.connectAttr( endJnt + '.message', toggleCtrl + '.endJnt' )
    
    # fk controls
    mc.addAttr( toggleCtrl, ln = 'upperFkControl', at = 'message' )
    mc.connectAttr( upperFkCtrl + '.message', toggleCtrl + '.upperFkControl' )   
    
    mc.addAttr( toggleCtrl, ln = 'midFkControl', at = 'message' )
    mc.connectAttr( midFkCtrl + '.message', toggleCtrl + '.midFkControl' )   
    
    # the ref object is the ik control to have ik orient in fk space
    mc.addAttr( toggleCtrl, ln = 'endFkControl', at = 'message' )
    mc.connectAttr( endFkCtrl + '.message', toggleCtrl + '.endFkControl' )    
    
    # driven fk joints
    mc.addAttr( toggleCtrl, ln = 'upperFkDrivenJnt', at = 'message' )
    mc.connectAttr( drivenFkJnts[0] + '.message', toggleCtrl + '.upperFkDrivenJnt' )    
    
    mc.addAttr( toggleCtrl, ln = 'midFkDrivenJnt', at = 'message' )
    mc.connectAttr( drivenFkJnts[1] + '.message', toggleCtrl + '.midFkDrivenJnt' )  
    
    mc.addAttr( toggleCtrl, ln = 'endFkDrivenJnt', at = 'message' )
    mc.connectAttr( drivenFkJnts[2] + '.message', toggleCtrl + '.endFkDrivenJnt' )  
    
    # driven ik joints
    mc.addAttr( toggleCtrl, ln = 'upperIkDrivenJnt', at = 'message' )
    mc.connectAttr( drivenIkJnts[0] + '.message', toggleCtrl + '.upperIkDrivenJnt' )    
    
    mc.addAttr( toggleCtrl, ln = 'midIkDrivenJnt', at = 'message' )
    mc.connectAttr( drivenIkJnts[1] + '.message', toggleCtrl + '.midIkDrivenJnt' )  
    
    mc.addAttr( toggleCtrl, ln = 'endIkDrivenJnt', at = 'message' )
    mc.connectAttr( drivenIkJnts[2] + '.message', toggleCtrl + '.endIkDrivenJnt' ) 
    
    # ik controls
    mc.addAttr( toggleCtrl, ln = 'ikControl', at = 'message' )
    mc.connectAttr( ik1Ctrl + '.message', toggleCtrl + '.ikControl' )

    
    mc.addAttr( toggleCtrl, ln = 'pvControl', at = 'message' )
    mc.connectAttr( ikPvCtrl + '.message', toggleCtrl + '.pvControl' )
    
    mc.addAttr( toggleCtrl, ln = 'limbIk', at = 'message' )
    mc.connectAttr( limbIk + '.message', toggleCtrl + '.limbIk' )
    
    snapRefLoc = transform.makeGroup( prefix = prefix + 'SnapRef', 
                                      referenceObj = ik1Ctrl, 
                                      parentObj = drivenFkJnts[2], 
                                      matchPositionOnly = False, 
                                      makeLocator = True )
    
    snapOffGrp = transform.makeOffsetGrp( snapRefLoc )
    mc.hide( snapOffGrp )
    mc.addAttr( toggleCtrl, ln = 'snapLoc', at = 'message' )
    mc.connectAttr( snapRefLoc + '.message', toggleCtrl + '.snapLoc' )   
    
def old_createMessageAttributes( prefix, toggleCtrl, upperJnt, midJnt, endJnt, upperFkCtrl, midFkCtrl, endFkCtrl, ik1Ctrl, ikPvCtrl, limbIk ):
    
    '''
    create message attributes to later access to multiple info no matter name changes eg: ik-fk snap
    '''
    # add an attribute to make toggle control to make it valid for fk-ik snap
    mc.addAttr( toggleCtrl, ln = 'fkIkSnapable', dt = 'string' )
    
    #===========================================================================
    # add respective message attributes with connections
    #===========================================================================
    # limb joints
    mc.addAttr( toggleCtrl, ln = 'upperJnt', at = 'message' )
    mc.connectAttr( upperJnt + '.message', toggleCtrl + '.upperJnt' )
    
    mc.addAttr( toggleCtrl, ln = 'midJnt', at = 'message' )
    mc.connectAttr( midJnt + '.message', toggleCtrl + '.midJnt' )
    
    mc.addAttr( toggleCtrl, ln = 'endJnt', at = 'message' )
    mc.connectAttr( endJnt + '.message', toggleCtrl + '.endJnt' )
    
    # fk controls
    mc.addAttr( toggleCtrl, ln = 'upperFkControl', at = 'message' )
    mc.connectAttr( upperFkCtrl + '.message', toggleCtrl + '.upperFkControl' )
    
    mc.addAttr( toggleCtrl, ln = 'midFkControl', at = 'message' )
    mc.connectAttr( midFkCtrl + '.message', toggleCtrl + '.midFkControl' )
    
    mc.addAttr( toggleCtrl, ln = 'endFkControl', at = 'message' )
    mc.connectAttr( endFkCtrl + '.message', toggleCtrl + '.endFkControl' )    
    
    # ik controls
    mc.addAttr( toggleCtrl, ln = 'ikControl', at = 'message' )
    mc.connectAttr( ik1Ctrl + '.message', toggleCtrl + '.ikControl' )
    
    mc.addAttr( toggleCtrl, ln = 'pvControl', at = 'message' )
    mc.connectAttr( ikPvCtrl + '.message', toggleCtrl + '.pvControl' )
    
    mc.addAttr( toggleCtrl, ln = 'limbIk', at = 'message' )
    mc.connectAttr( limbIk + '.message', toggleCtrl + '.limbIk' )
    
    snapRefLoc = transform.makeGroup( prefix = prefix + 'SnapRef', 
                                      referenceObj = ik1Ctrl, 
                                      parentObj = endFkCtrl, 
                                      matchPositionOnly = False, 
                                      makeLocator = True )
    
    snapOffGrp = transform.makeOffsetGrp( snapRefLoc )
    mc.hide( snapOffGrp )
    mc.addAttr( toggleCtrl.C, ln = 'snapLoc', at = 'message' )
    mc.connectAttr( snapRefLoc + '.message', toggleCtrl.C + '.snapLoc' )    

def build(
            upperJnt,
            midJnt,
            endJnt,
            ikPoleVecRef,
            prefix = 'new',
            baseRigData = None,
            ctrlScale = 1.0,
            isLeg = False,
            endOrientRefObject = '',
            flatWorldXZ = False,
            buildTwistJoints = True,
            twistJointsNumber = 5,
            stretch = True
            ):
    """
    :param upperJnt: str, upper joint
    :param midJnt: str, middle joint
    :param endJnt: str, end joint ( e.g wrist/hand joint )
    :param ikPoleVecRef: str, reference object for position of IK pole vector control
    :param prefix: str, prefix for naming new objects
    :param baseRigData: instance, base rig data returned from rigbase.base build() to connect visibility channels etc. to the main base
    :param ctrlScale: float, scale of controls
    :param isLeg: bool, helps to orient Toggle control when module is used for leg setup and control shape
    :param endOrientRefObject: str, optional, reference object for end IK control orientation
    :param flatWorldXZ: str, orienting IK control based on end joint X aiming, useful for foot controls in leg module
    :param buildTwistJoints: bool, create twist joints setup
    :param twistJointsNumber: int, number of joints is going to be create by twist setup
    :param stretch: bool, create stretch setup ( it works with or without twist setup )
    :return dictionary of multiple items from module
    """
    
    #===========================================================================
    # make rig module
    #===========================================================================
    rigmodule = module.Module( prefix )
    rigmodule.parent( baseRigData = baseRigData )
    rigmodule.connect( baseRigData = baseRigData )    
    
    fkJoints, ikJoints = _createFkIkDuplicateChains(rigmodule, upperJnt, midJnt, endJnt)
    
    # get some initial values about the joints
    upperJntRot = mc.getAttr( upperJnt + '.r' )[0]
    midJntRot = mc.getAttr( midJnt + '.r' )[0]
    
    if not mc.objExists( endOrientRefObject ):
        
        endOrientRefObject = None
    
    if isLeg:
        ikCtrlShape = 'foot'
    else:
        ikCtrlShape = 'cube'
    
    # =======================================================================
    
    # make toggle control
    toggleCtrl = control.Control( prefix = prefix + 'Toggle', lockHideChannels = ['t', 'r'], translateTo = endJnt, rotateTo = endJnt, scale = ctrlScale * 5, colorName = 'secondary', shape = 't', ctrlParent = rigmodule.Controls )
    
    # adjust default toggle control orientation shape
    shape.translateRotate( toggleCtrl.C, rot = [90, 0, 90], localSpace = True )
    
    if isLeg:
        shape.translateRotate( toggleCtrl.C, pos = [0, 0, 0], rot = [90, 0, 0], localSpace = True, relative = True )
    
    
    rotateToggleCtrlShape = None
    
    if isLeg and name.getSide( prefix ) == 'l':
        
        rotateToggleCtrlShape = True
    
    elif not isLeg and name.getSide( prefix ) == 'r':
        
        rotateToggleCtrlShape = True
    
    if rotateToggleCtrlShape:
    
        shape.translateRotate( toggleCtrl.C, rot = [180, 0, 0], localSpace = True )
    
    # add toggle to rig module
    rigmodule.customToggleObject( toggleCtrl.C )
    mc.parentConstraint( endJnt, toggleCtrl.Off, mo = True )
    
    #===========================================================================
    # ik - fk joints connection to bind joints
    #===========================================================================
    bindJnts = [ upperJnt, midJnt, endJnt ]
    _connectIkFkJoints( bindJnts, fkJoints, ikJoints, rigmodule )
    
    #===========================================================================
    # build FK controls
    #===========================================================================
    
    fkPrefixSeq = []
    fkJointList = fkJoints
    
    # make fk joints names sequence for naming controls
    for i, j in enumerate( [upperJnt, midJnt, endJnt] ):
        
        baseJntName = name.removeSide( j ).capitalize()
        p = prefix + 'Fk' + name.removeSuffix( baseJntName )
        fkPrefixSeq.append( p )
       
    upperFkCtrl = control.Control( lockHideChannels = [], prefix = fkPrefixSeq[0], moveTo = upperJnt, scale = 4 * ctrlScale, shape = 'cubeOnBaseX', ctrlParent = rigmodule.Controls )
    midFkCtrl = control.Control( lockHideChannels = ['t'], prefix = fkPrefixSeq[1], moveTo = midJnt, scale = 3 * ctrlScale, shape = 'cubeOnBaseX', ctrlParent = upperFkCtrl.C )
    endFkCtrl = control.Control( lockHideChannels = ['t'], prefix = fkPrefixSeq[2], moveTo = endJnt, scale = 3 * ctrlScale, shape = 'cubeOnBaseX', ctrlParent = midFkCtrl.C )
    
    # connect FK controls to joints    
    mc.orientConstraint( upperFkCtrl.C, fkJointList[0] )
    mc.pointConstraint( upperFkCtrl.C, fkJointList[0], mo = True )
    mc.connectAttr( upperFkCtrl.C + '.ro', fkJointList[0] + '.ro' )
    
    for c, j in zip( [ midFkCtrl, endFkCtrl ], [ fkJointList[1], fkJointList[2] ] ):
        
        mc.connectAttr( c.C + '.r', j + '.r' )
        mc.connectAttr( c.C + '.ro', j + '.ro' )
    
    rigmodule.connectIkFk( upperFkCtrl.Off + '.v', reversed = True )    
    
    '''
    # lock mid joint unwanted rotation axis
    for axis in ['x', 'y' ]:
        
        mc.setAttr( midFkCtrl.C + '.r' + axis, l = 1, k = 0 )
    '''
        
    #===========================================================================
    # IK setup
    #===========================================================================
    limbIk = mc.ikHandle( n = prefix + 'Main_ikh', sol = 'ikRPsolver', sj = ikJoints[0], ee = ikJoints[2] )[0]
    #rigmodule.connectIkFk( limbIk + '.ikBlend' )
    
    # IK hand controls
    ik1Ctrl = control.Control( prefix = prefix + 'Ik1', translateTo = endJnt, rotateTo = endOrientRefObject, scale = ctrlScale * 4, shape = ikCtrlShape, ctrlParent = rigmodule.Controls )
    
   
    # make flat orient object for IK controls
    if flatWorldXZ and not endOrientRefObject:
        
        localMoveRef = transform.makeLocator( prefix = prefix + 'TEMP_IkCtrlLocalMoveRef', moveRef = endJnt, simpleGroup = True )
        sideSign = name.getSideAsSign( prefix )
        transform.rotateAlignToWorld( localMoveRef, primaryAxisVector = [sideSign, 0, 0], worldAxisToKeep = ['x', 'z'], alignTwist = True )
        
        tempWorldGrp = mc.group( n = prefix + 'TEMP_worldRotate_grp', em = True, p = localMoveRef )
        mc.rotate( 0, 90, 0, tempWorldGrp, os = True )
        
        mc.delete( mc.orientConstraint( tempWorldGrp, ik1Ctrl.Off ) )
        mc.delete( localMoveRef, tempWorldGrp )
    
    # ik control vis switch
    rigmodule.connectIkFk( ik1Ctrl.Off + '.v' )
    mc.hide( limbIk )
    
    # IK pole vector control
    ikPvCtrl = control.Control( lockHideChannels = ['r'], prefix = prefix + 'IkPoleVector', translateTo = ikPoleVecRef, scale = ctrlScale * 5 , shape = 'diamond', ctrlParent = rigmodule.Controls )
    rigmodule.connectIkFk( ikPvCtrl.Off + '.v' )
    
    # make pole vector safe group to make pole vector constraint
    pvAttachGrp = transform.makeGroup( prefix = prefix + 'PvAttachGrp', referenceObj = ikPvCtrl.C, parentObj = ikPvCtrl.C )
    mc.poleVectorConstraint( pvAttachGrp, limbIk )
    
#     ikPvOffsetGrp = mc.group( n = prefix + 'IkPvOffsetAim_grp', em = 1, p = rigmodule.Parts )
#     mc.pointConstraint( ikJoints[0], ikPvOffsetGrp )
#     ikAimConst = mc.aimConstraint( ik1Ctrl.C, ikPvOffsetGrp, n = prefix + 'IkPvOffsetAim_aic', aim = [1, 0, 0], u = [0, 0, 1], wut = 'object', wuo = ikPvCtrl.C )[0]
#     
#     ikPvGrp = mc.group( n = prefix + 'IkPv_grp', em = 1, p = ikPvCtrl.C )
#     mc.parent( ikPvGrp, ikPvOffsetGrp )
#     
#     mc.poleVectorConstraint( ikPvGrp, limbIk )
#     mc.setAttr( ikAimConst + '.offsetX', 90 )
#     mc.setAttr( limbIk + '.twist', -90 )  
 
    ikAttachGrp = transform.makeGroup( prefix = prefix + 'IkAttachGrp', referenceObj = limbIk, parentObj = ik1Ctrl.C )
    mc.parent( limbIk, ikAttachGrp )
 
    # make group for IK space target for end joint, which is oriented the same as the joint
    ikEndJntTargetGrp = mc.group( n = prefix + 'IkSafeOffsetHand_grp', em = 1, p = endJnt, r = True )
    mc.parent( ikEndJntTargetGrp, ik1Ctrl.C )
    ikEndSafeOrientConstraintGrp = mc.group( n = prefix + 'IkSafeOrientConstraint_grp', em = 1, p = ikEndJntTargetGrp, r = True )
    mc.orientConstraint( ikEndSafeOrientConstraintGrp, ikJoints[2] )
    mc.connectAttr( ik1Ctrl.C + '.ro', ikJoints[2] + '.ro' )
   
   # make pv line 
    poleVecLine = curve.makeConnectionLine( ikJoints[1], ikPvCtrl.C ) 
    mc.parent( poleVecLine, rigmodule.Controls )
    rigmodule.connectIkFk( poleVecLine + '.v' )
    
    #===========================================================================
    # make switches
    #===========================================================================
    # ik switches
    
    # setup hand or foot space for IK pole vector
    ikPvFootGrp = transform.makeGroup( prefix = prefix + 'PVfootSpace', referenceObj = ikPvCtrl.C, parentObj = rigmodule.LocalSpace, pos = [0, 0, 0], matchPositionOnly = True )
    mc.parentConstraint( ik1Ctrl.C, ikPvFootGrp, mo = True, sr = ['x', 'y', 'z'] )
    
    endSpaceName = 'hand'
    
    if isLeg:
        
        endSpaceName = 'foot'
        
    constraint.makeSwitch( ikPvCtrl.Off, rigmodule.Toggle, 'ikPoleVecSpace', ['local', 'global', 'body', endSpaceName], 'parentConstraint', [rigmodule.LocalSpace, rigmodule.GlobalSpace, rigmodule.BodySpace, ikPvFootGrp],maintainOffset = 1, defaultIdx = 1 )
    constraint.makeSwitch( ik1Ctrl.Off, rigmodule.Toggle, 'ikSpace', ['local', 'global', 'body'], 'parentConstraint', [rigmodule.LocalSpace, rigmodule.GlobalSpace, rigmodule.BodySpace], maintainOffset = 1, defaultIdx = 1 )
    
    # fk and hand switches
   
    # make end fk orient contraint connection fix so space switch would work properly
    fkEndJntTargetGrp = mc.group( n = prefix + 'fkSafeOffsetHand_grp', em = 1, p = endJnt, r = True )
    mc.parent( fkEndJntTargetGrp, endFkCtrl.C )
    fkEndSafeOrientConstraintGrp = mc.group( n = prefix + 'fkSafeOrientConstraint_grp', em = 1, p = fkEndJntTargetGrp, r = True )
    
    # disconnect direct connection and make constraint
    for axis in ['x', 'y', 'z']:
        connect.disconnect( '{}.r{}'.format( fkJoints[2], axis ) )
    mc.orientConstraint( fkEndSafeOrientConstraintGrp, fkJoints[2] )
    
    constraint.makeSwitch( upperFkCtrl.Off, rigmodule.Toggle, 'fkSpace', ['local', 'global', 'body'], 'orientConstraint', [rigmodule.LocalSpace, rigmodule.GlobalSpace, rigmodule.BodySpace], 1, defaultIdx = 2 )
    constraint.makeSwitch( endFkCtrl.Off, rigmodule.Toggle, 'fkHandSpace', ['local', 'global', 'body'], 'orientConstraint', [fkJoints[1], rigmodule.GlobalSpace, rigmodule.BodySpace], 1 )
  

    # set IK as default
    mc.setAttr( rigmodule.Toggle + '.fkIk', 1 )
    
    #===========================================================================
    # IK base control
    #===========================================================================
    ikBaseCtrl = control.Control( lockHideChannels = ['rx', 'rz'], prefix = prefix + 'IkBase', translateTo = upperJnt, scale = 1.4 * ctrlScale, shape = 'sphere' )
    mc.parentConstraint( rigmodule.LocalSpace, ikBaseCtrl.Off, mo = 1 )
    mc.parent( ikBaseCtrl.Off, rigmodule.Controls )
    rigmodule.connectIkFk( ikBaseCtrl.Off + '.v' )
    
    # attach position of upper joint to IK base control and FK upper control
    if isLeg:
        upperJntPointConst = mc.pointConstraint( ikBaseCtrl.C, ikJoints[0] )
    
    #===========================================================================
    # Twist setup
    #===========================================================================
    twistData = None
    if buildTwistJoints:
        twistData = _twistSetup( prefix, twistJointsNumber, upperJnt, midJnt, endJnt, rigmodule )
        
    #===========================================================================
    # stretch setup
    #===========================================================================
    if stretch:
        _addIkStretchSetup( rigmodule, prefix, ikJoints, ik1Ctrl, upperJnt, twistData, toggleCtrl )
    
    
    return {
    'module':rigmodule,
    'mainGrp':rigmodule.Main,
    'ctrlGrp':rigmodule.Controls,
    'ik1Ctrl':ik1Ctrl,
    'pvCtrl': ikPvCtrl,
    'ikBaseCtrl':ikBaseCtrl,
    'fkControls':[ upperFkCtrl, midFkCtrl, endFkCtrl ],
    'limbIk':limbIk,
    'globalSpaceGrp':rigmodule.GlobalSpace,
    'bodySpaceGrp':rigmodule.BodySpace,
    'localSpaceGrp':rigmodule.LocalSpace,
    'toggleGrp':rigmodule.Toggle,
    'settingsGrp':rigmodule.Settings,
    'upperJnt':upperJnt,
    'midJnt':midJnt,
    'toggleCtrl':toggleCtrl,
    'ikAttachGrp':ikAttachGrp,
    'ikJoints':ikJoints,
    'fkJoints':fkJoints,
    'twistData': twistData
    }

def _createFkIkDuplicateChains(rigmodule, upperJnt, midJnt, endJnt):
    
    '''
    create a duplicate of bind chain for fk and ik setups
    :return fk and ik joint chains
    '''
    
    # make duplicate chains for ik and fk
    fkJointNames = [ name.removeSuffix( j ) + 'Fk' for j in [ upperJnt, midJnt, endJnt ] ]
    fkJoints = joint.duplicateChain( [ upperJnt, midJnt, endJnt ], newjointnames = fkJointNames )
    
    ikJointNames = [ name.removeSuffix( j ) + 'Ik' for j in [ upperJnt, midJnt, endJnt ] ]
    ikJoints = joint.duplicateChain( [ upperJnt, midJnt, endJnt ], newjointnames = ikJointNames )
    
    mc.parent( ikJoints[0], rigmodule.Joints )
    mc.parent( fkJoints[0], rigmodule.Joints )
    
    # set some Colors and different radius
    jointRad = mc.getAttr( upperJnt + '.radius' )
    
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

def _addIkStretchSetup( rigmodule, prefix, ikJoints, ik1Ctrl, upperJnt, twistData, toggleCtrl ):
    
    '''
    Add ik stretch setup
    '''
    # Add stretch attrs to control
    _addIkStretchAttributes( ik1Ctrl )
    
    # create locators for distances node reference
    upperJntParent = mc.listRelatives( upperJnt, p = True )[0]
    startLoc = mc.spaceLocator( n = prefix + 'StretchStart_loc' )[0]
    
    mc.delete( mc.parentConstraint( ikJoints[0], startLoc ) )
    mc.parent( startLoc, rigmodule.Parts )
    mc.parentConstraint( upperJntParent, startLoc, mo = True )
    
    # create stretch distance node
    stretchDis = mc.createNode( 'distanceBetween', n = prefix + 'StretchDistance_dis' )
    mc.connectAttr( startLoc + '.worldMatrix[0]', stretchDis + '.inMatrix1' )
    mc.connectAttr( ik1Ctrl.C + '.worldMatrix[0]', stretchDis + '.inMatrix2' )
    stretchDisOutPlug = stretchDis + '.distance'
    
    # get straight total distance
    vecA = vector.from2Objects( ikJoints[0], ikJoints[1], normalized = False )
    vecB = vector.from2Objects( ikJoints[1], ikJoints[2], normalized = False)
    straightLength = vecA.length() + vecB.length()
    
    # global scale compensate
    globalScaleMdl = mc.createNode( 'multDoubleLinear', n = prefix + 'ScaleCompStretch_mdl' )
    mc.setAttr( globalScaleMdl + '.input1', straightLength )
    mc.connectAttr( rigmodule.getModuleScalePlug(), globalScaleMdl + '.input2' )
    globalScaleOutPlug = globalScaleMdl + '.output'
    
    # create stretch ratio multiply divide
    stretchRatioMdv = mc.createNode( 'multiplyDivide', n = prefix + 'StretchRatio_mdv' )
    mc.setAttr( stretchRatioMdv + '.operation', 2 ) # divide operation
    mc.connectAttr( stretchDisOutPlug, stretchRatioMdv + '.input1X' )
    mc.connectAttr( globalScaleOutPlug, stretchRatioMdv + '.input2X' )
    stretchRatioOutPlug = stretchRatioMdv + '.outputX'
    
    # create stretch condition to avoid automatic shrink
    stretchCon = mc.createNode( 'condition', n = prefix + 'StretchCond_con' )
    mc.setAttr( stretchCon + '.operation', 3 ) # greater or equal operation
    mc.connectAttr( stretchDisOutPlug, stretchCon + '.firstTerm' )
    mc.connectAttr( globalScaleOutPlug, stretchCon + '.secondTerm' )
    mc.connectAttr( stretchRatioOutPlug, stretchCon + '.colorIfTrueR' )
    stretchConOutPlug = stretchCon + '.outColorR'
    
    # create blend2Attrs node for stretch switch
    stretchSwitchBta = mc.createNode( 'blendTwoAttr', n = prefix + 'StretchSwitch_bta' )
    mc.connectAttr( ik1Ctrl.C + '.stretchAmount', stretchSwitchBta + '.attributesBlender' )
    mc.setAttr( stretchSwitchBta + '.input[0]', 1 )
    mc.connectAttr( stretchConOutPlug, stretchSwitchBta + '.input[1]' )
    stretchSwitchOutPlug = stretchSwitchBta + '.output'
    
    # create manual stretch multiplier
    stretchManualMdl = mc.createNode( 'multDoubleLinear', n = prefix + 'StretchManual_mdl' )
    mc.connectAttr( stretchSwitchOutPlug, stretchManualMdl + '.input1' )
    mc.connectAttr( ik1Ctrl.C + '.stretchManual', stretchManualMdl + '.input2' )
    stretchManualOutPlug = stretchManualMdl + '.output'
    
    # create upper stretch multiplier
    stretchUpperMdl = mc.createNode( 'multDoubleLinear', n = prefix + 'stretchUpper_mdl' )
    mc.connectAttr( ik1Ctrl.C + '.stretchUpper', stretchUpperMdl + '.input1' )
    mc.connectAttr( stretchManualOutPlug, stretchUpperMdl + '.input2' )
    stretchUpperOutPlug = stretchUpperMdl + '.output'
    
    # create lower stretch multiplier
    stretchLowerMdl = mc.createNode( 'multDoubleLinear', n = prefix + 'StretchLower_mdl' )
    mc.connectAttr( ik1Ctrl.C + '.stretchLower', stretchLowerMdl + '.input1' )
    mc.connectAttr( stretchManualOutPlug, stretchLowerMdl + '.input2' )
    stretchLowerOutPlug = stretchLowerMdl + '.output'
    
    # connect upper stretch to ik joint
    upperPrefix = name.removeSuffix( ikJoints[1] )
    txVal = mc.getAttr( ikJoints[1] + '.tx' )
    stretchUpperJntMdl = mc.createNode( 'multDoubleLinear', n = upperPrefix + 'Stretch_mdl' )
    mc.setAttr( stretchUpperJntMdl + '.input1', txVal )
    mc.connectAttr( stretchUpperOutPlug, stretchUpperJntMdl + '.input2' )
    stretchUpperJntOutPlug = stretchUpperJntMdl + '.output'
    
    mc.connectAttr( stretchUpperJntOutPlug, ikJoints[1] + '.tx' )
    
    # connect lower stretch to ik joint
    lowerPrefix = name.removeSuffix( ikJoints[2] )
    txVal = mc.getAttr( ikJoints[2] + '.tx' )
    stretchLowerJntMdl = mc.createNode( 'multDoubleLinear', n = lowerPrefix + 'Stretch_mdl' )
    mc.setAttr( stretchLowerJntMdl + '.input1', txVal )
    mc.connectAttr( stretchLowerOutPlug, stretchLowerJntMdl + '.input2' )
    stretchLowerJntOutPlug = stretchLowerJntMdl + '.output'
    
    mc.connectAttr( stretchLowerJntOutPlug, ikJoints[2] + '.tx' )
    
    if twistData:
        _stretchTwistJoints( prefix, twistData, ik1Ctrl, stretchUpperOutPlug, stretchLowerOutPlug, toggleCtrl )
    
def _addIkStretchAttributes( ik1Ctrl ):
    
    '''
    Add default attributes for ik stretch
    '''
    
    attribute.addSection( ik1Ctrl.C, sectionName = 'Stretch' )
    
    mc.addAttr( ik1Ctrl.C, ln = 'stretchAmount', at = 'float', k = True, min = 0, max = 1, dv = 1 )
    mc.addAttr( ik1Ctrl.C, ln = 'volumetric', at = 'float', k = True, min = 0, max = 1, dv = 0 )
    mc.addAttr( ik1Ctrl.C, ln = 'stretchManual', at = 'float', k = True, min = -10, max = 10, dv = 1 )
    mc.addAttr( ik1Ctrl.C, ln = 'stretchUpper', at = 'float', k = True, min = -10, max = 10, dv = 1 )
    mc.addAttr( ik1Ctrl.C, ln = 'stretchLower', at = 'float', k = True, min = -10, max = 10, dv = 1 )
    
def _twistSetup( prefix, twistJointsNumber, upperJnt, midJnt, endJnt, rigmodule ):
    
    
    
    #===========================================================================
    # upper - mid  setup
    #===========================================================================
    
    # set shoulder to T pose when making reference joints
    upperJntJo = mc.getAttr( upperJnt + '.jo' )[0]
    mc.setAttr( upperJnt + '.joy', 0 )    
    
    refJnt = mc.listRelatives( upperJnt, p = True )[0]
    
    upperPartdata = joint.makeTwistJoints( upperJnt, refJnt, twistJointsNumber )
    
    mc.setAttr( upperJnt + '.joy', upperJntJo[1] )
    
    #===========================================================================
    # mid - end setup
    #===========================================================================

    lowePartData = joint.makeTwistJoints( midJnt, endJnt, twistJointsNumber )
    
    twistJointsDataList = [ upperPartdata, lowePartData ]
    
    return twistJointsDataList 

def _stretchTwistJoints( prefix, twistData, ik1Ctrl, stretchUpperOutPlug, stretchLowerOutPlug, toggleCtrl ):
    
    '''
    add stretch setup to twist joints
    '''
    
    posPrefixList = [ 'Upper', 'Lower' ]
    i = 0
    
    for posPrefix, stretchOutPlug in zip( posPrefixList, [ stretchUpperOutPlug, stretchLowerOutPlug ] ):
        
        stretchTwistSwitch = mc.createNode( 'blendTwoAttr', n = prefix + 'Stretch{}TwistSwitch_bta'.format( posPrefix ) )
        mc.connectAttr( toggleCtrl.C + '.fkIk', stretchTwistSwitch + '.attributesBlender' )
        mc.setAttr( stretchTwistSwitch + '.input[0]', 1 )
        mc.connectAttr( stretchOutPlug, stretchTwistSwitch + '.input[1]' )
        stretchTwistSwitchOutPlug = stretchTwistSwitch + '.output'
        
        TwistJoints = twistData[i]['twistjoints']
        
        # stretch and translate compensate
        
        txVal = mc.getAttr( TwistJoints[1] + '.tx' )
        stretchTwistMdl = mc.createNode( 'multDoubleLinear', n = prefix + 'Stretch{}Twist_mdl'.format( posPrefix ) )
        mc.setAttr( stretchTwistMdl + '.input1', txVal )
        mc.connectAttr( stretchTwistSwitchOutPlug, stretchTwistMdl + '.input2' )
        stretchTwistOutPlug = stretchTwistMdl + '.output'
        
        # squash setup
        squashTwistMdv = mc.createNode( 'multiplyDivide', n = prefix + 'Squash{}Twist_mdl'.format( posPrefix ) )
        mc.setAttr( squashTwistMdv + '.operation', 2 ) # divide operation
        mc.setAttr( squashTwistMdv + '.input1X', 1 )
        mc.connectAttr( stretchTwistSwitchOutPlug, squashTwistMdv + '.input2X' )
        squashTwistOutPlug = squashTwistMdv + '.outputX'
        
        # volumetric switch
        squashTwistSwitch = mc.createNode( 'blendTwoAttr', n = prefix + 'Volumetric{}TwistSwitch_bta'.format( posPrefix ) )
        mc.connectAttr( ik1Ctrl.C + '.volumetric', squashTwistSwitch + '.attributesBlender' )
        mc.setAttr( squashTwistSwitch + '.input[0]', 1 )
        mc.connectAttr( squashTwistOutPlug, squashTwistSwitch + '.input[1]' )
        squashTwistSwitchOutPlug = squashTwistSwitch + '.output'
        
        for twistJnt in TwistJoints[1:]:
            
            mc.connectAttr( stretchTwistOutPlug, twistJnt + '.tx' )
        
        # squash connection
        if i == 0:
            TwistJoints = TwistJoints[1:]
        
        for twistJnt in TwistJoints:
        
            mc.connectAttr( squashTwistSwitchOutPlug, twistJnt + '.sy' )
            mc.connectAttr( squashTwistSwitchOutPlug, twistJnt + '.sz' )
        
        i += 1
        

        
        
        
    
    