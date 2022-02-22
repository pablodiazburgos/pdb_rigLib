'''
eyes module
@category Rigging
'''

import maya.cmds as mc

from utils import constraint
from utils import vector
from utils import transform
from utils import attribute
from utils import curve
from utils import joint

from base import control
from base import module

def simpleEyes( leftEyeJnt, rightEyeJnt, prefix = 'eye', baseRigData = None, ctrlScale = 1.0 ):

    '''
    simple eyes control rig with middle and L/R eye control and 3 space switches (local, global, body)
    
    @param leftEyeJnt:str, left eye joint
    @param rightEyeJnt: str, right eye joint
    @param prefix: str, prefix for naming new objects
    @param baseRigData: instance, base rig data returned from rigbase.base build() to connect visibility channels etc. to the main base
    @param ctrlScale: float, scale of controls
    @return: dictionary with rig objects
    '''
    
    if prefix.startswith( 'c_' ):
    
        lsideprefix = 'l_' + prefix[2:]
        rsideprefix = 'r_' + prefix[2:]
    
    elif not prefix.startswith( 'l_' ) and not prefix.startswith( 'r_' ):
        
        lsideprefix = 'l_' + prefix
        rsideprefix = 'r_' + prefix
        
    #===========================================================================
    # module
    #===========================================================================
    
    
    rigmodule = module.Module( prefix )
    rigmodule.connect( baseRigData = baseRigData )
    rigmodule.parent( baseRigData = baseRigData )
    
      
    #===========================================================================
    # controls
    #===========================================================================
    
    # setup per-eye controls
    
    leftEyeCtrl = control.Control( lockHideChannels = ['t'], prefix = lsideprefix, moveTo = leftEyeJnt, scale = 0.5 * ctrlScale, shape = 'cube', ctrlParent = rigmodule.Controls )
    mc.orientConstraint( leftEyeCtrl.C, leftEyeJnt, mo = 1 )
    
    rightEyeCtrl = control.Control( lockHideChannels = ['t'], prefix = rsideprefix, moveTo = rightEyeJnt, scale = 0.5 * ctrlScale, shape = 'cube', ctrlParent = rigmodule.Controls )
    mc.orientConstraint( rightEyeCtrl.C, rightEyeJnt, mo = 1 )
    
    
    midEyeGrp = mc.group( em = 1, n = prefix + 'MainSetup_grp', p = rigmodule.LocalSpace )
    mc.delete( mc.parentConstraint( leftEyeJnt, rightEyeJnt, midEyeGrp ) )
    
    mainEyeCtrl = control.Control( lockHideChannels = ['t'], prefix = prefix + 'Main', translateTo = midEyeGrp, scale = ctrlScale, shape = 'cube', ctrlParent = rigmodule.Controls )
    mc.connectAttr( rigmodule.Main + '.primaryCtrlVis', mainEyeCtrl.Off + '.v' )
    
    # setup mid ctrl aim
    
    targetPos = _simpleEyes_getTargetPosition( leftEyeJnt, rightEyeJnt )
    midEyeTargetGrp = mc.group( n = prefix + 'MainEyeTarget_grp', em = 1, p = midEyeGrp )
    mc.move( targetPos[0], targetPos[1], targetPos[2], midEyeTargetGrp, a = 1, ws = 1 )
    
    mc.aimConstraint( midEyeTargetGrp, mainEyeCtrl.Off, n = prefix + mainEyeCtrl.Off + 'aic', aim = [0, 0, 1], u = [0, 0, 1], wut = 'objectrotation', wu = [0, 0, 1], wuo = rigmodule.LocalSpace )
    mc.orientConstraint( mainEyeCtrl.C, leftEyeCtrl.Off, mo = 1 )
    mc.orientConstraint( mainEyeCtrl.C, rightEyeCtrl.Off, mo = 1 )
    
    
    #===========================================================================
    # space switching
    #===========================================================================
    
    constraint.makeSwitch( midEyeGrp, rigmodule.Toggle, 'space', ['local', 'global', 'body'], 'orientConstraint', [rigmodule.LocalSpace, rigmodule.GlobalSpace, rigmodule.BodySpace], 1, defaultIdx = 0 )
    
    spaceSwitchPlugs = [ rigmodule.Toggle + '.space' ]
    
    return {
            'module':rigmodule,
            'mainGrp':rigmodule.Main,
            'leftEyeCtrl':leftEyeCtrl,
            'rightEyeCtrl':rightEyeCtrl,
            'mainEyeCtrl':mainEyeCtrl,
            'globalSpaceGrp':rigmodule.GlobalSpace,
            'bodySpaceGrp':rigmodule.BodySpace,
            'localSpaceGrp':rigmodule.LocalSpace,
            'spaceSwitchPlugs':spaceSwitchPlugs,
            'toggleGrp':rigmodule.Toggle,
            'settingsGrp':rigmodule.Settings
            }
    
    
def _simpleEyes_getTargetPosition( leftEyeJnt, rightEyeJnt ):
    
    '''
    help function to get position of eye middle target
    - using vector math
    '''
    
    # get left and right eye joint vectors
    
    lJntStartVec = vector.makeMVector( mc.xform( leftEyeJnt, q = 1, t = 1, ws = 1 ) )
    lJntEnd = mc.listRelatives( leftEyeJnt, c = 1, typ = 'joint' )
    lJntEndVec = vector.makeMVector( mc.xform( lJntEnd, q = 1, t = 1, ws = 1 ) )
    
    rJntStartVec = vector.makeMVector( mc.xform( rightEyeJnt, q = 1, t = 1, ws = 1 ) )
    rJntEnd = mc.listRelatives( rightEyeJnt, c = 1, typ = 'joint' )
    rJntEndVec = vector.makeMVector( mc.xform( rJntEnd, q = 1, t = 1, ws = 1 ) )
    
    lJntVec = lJntEndVec - lJntStartVec
    rJntVec = rJntEndVec - rJntStartVec
    
    # make average vector and resulting position
    
    distMulti = 10.0
    averVec = ( lJntVec + rJntVec ) / 2.0
    averVec = averVec * distMulti
    
    midPosVec = ( lJntStartVec + rJntStartVec ) / 2.0
    targetPosVec = midPosVec + averVec
    
    return [ targetPosVec.x, targetPosVec.y, targetPosVec.z ]

def build( leftEyeJnt, rightEyeJnt, headJnt = None, prefix = 'eyes', baseRigData = None, sceneScale = 1.0, eyesChannelConnection = False, distanceMultiFactor = 10, keepControlsInEyeDirection = False ):

    '''
    eyes control rig with middle and L/R eye control and 3 space switches (local, global, body)
    
    :param leftEyeJnt: str, left eye joint
    :param rightEyeJnt: str, right eye joint
    :param headJnt: str, name of head joint - only used with keepControlsInEyeDirection option
    :param prefix: str, prefix for naming new objects
    :param keepControlsInEyeDirection: bool, keep eye controls in the line of eye joints direction
    :param baseRigData:instance, base rig data returned from rigbase.base build() to connect visibility channels etc. to the main base
    :param eyesChannelConnection: bool, use channel connection to eye joints instead of constraint, useful for local face rigs
    :param sceneScale: float, scale of controls
    :return: dictionary with rig objects
    '''
    
    if prefix.startswith( 'c_' ):
    
        lsideprefix = 'l_' + prefix[2:]
        rsideprefix = 'r_' + prefix[2:]
    
    elif not prefix.startswith( 'l_' ) and not prefix.startswith( 'r_' ):
        
        lsideprefix = 'l_' + prefix
        rsideprefix = 'r_' + prefix
    
    #===========================================================================
    # module
    #===========================================================================
    
    
    rigmodule = module.Module( prefix )
    rigmodule.connect( baseRigData = baseRigData )
    rigmodule.parent( baseRigData = baseRigData )
    
    #===========================================================================
    # controls
    #===========================================================================
    
    leftEyeTargetPos = _eye_getTargetPositionForEyeJnt( leftEyeJnt, sceneScale * distanceMultiFactor, keepControlsInEyeDirection )
    rightEyeTargetPos = _eye_getTargetPositionForEyeJnt( rightEyeJnt, sceneScale * distanceMultiFactor, keepControlsInEyeDirection )
    middletargetPos = transform.getAveragePositionFromList( [ leftEyeTargetPos, rightEyeTargetPos ] )
    
    midEyeGrp = mc.group( em = 1, n = prefix + 'MidEye_grp', p = rigmodule.LocalSpace )
    mc.delete( mc.parentConstraint( leftEyeJnt, rightEyeJnt, midEyeGrp ) )
    
    tempLeftEyeGrp = transform.makeGroup( prefix = 'tempLeye', pos = leftEyeTargetPos, matchPositionOnly = True, makeLocator = False )
    tempRightEyeGrp = transform.makeGroup( prefix = 'tempReye', pos = rightEyeTargetPos, matchPositionOnly = True, makeLocator = False )
    tempMidEyeGrp = transform.makeGroup( prefix = 'tempCeye', pos = middletargetPos, matchPositionOnly = True, makeLocator = False )
    
    # setup per-eye controls
    
    leftEyeCtrl = control.Control( lockHideChannels = ['r'], prefix = lsideprefix, moveTo = tempLeftEyeGrp, scale = 0.5 * sceneScale, shape = 'circleZ', ctrlParent = rigmodule.Controls )
    rightEyeCtrl = control.Control( lockHideChannels = ['r'], prefix = rsideprefix, moveTo = tempRightEyeGrp, scale = 0.5 * sceneScale, shape = 'circleZ', ctrlParent = rigmodule.Controls )
    mainEyeCtrl = control.Control( prefix = prefix + 'Main', moveTo = tempMidEyeGrp, scale = sceneScale, shape = 'circleZ', ctrlParent = rigmodule.Controls )
    
    rigmodule.Toggle = mainEyeCtrl.C
    
    # delete temp position grps
    mc.delete( [tempLeftEyeGrp,  tempRightEyeGrp, tempMidEyeGrp])
    
    # aim eye controls to eye joints
    
    if keepControlsInEyeDirection:
        
        mc.delete( mc.aimConstraint( leftEyeJnt, leftEyeCtrl.Off, aim = [0, 0, -1], u = [0, 1, 0], wut = 'objectrotation', wu = [1, 0, 0], wuo = headJnt ) )
        mc.delete( mc.aimConstraint( rightEyeJnt, rightEyeCtrl.Off, aim = [0, 0, -1], u = [0, 1, 0], wut = 'objectrotation', wu = [1, 0, 0], wuo = headJnt ) )
    
    # setup eyes aim
    
    mc.aimConstraint( midEyeGrp, mainEyeCtrl.C, aim = [0, 0, -1], u = [0, 1, 0], wut = 'objectrotation', wu = [0, 1, 0], wuo = rigmodule.LocalSpace )
    attribute.lockHideTransformVis( mainEyeCtrl.C, t = [0, 0], r = [1, 1] )
    mc.setAttr( mainEyeCtrl.C + '.ro', l = 1, k = 0 )
    mc.parent( leftEyeCtrl.Off, rightEyeCtrl.Off, mainEyeCtrl.C )
    
    # attach eye joints to aiming controls using group to keep relative eye orientation
    
    leftEyeJntGrp = transform.makeLocator( prefix = prefix + 'LeftEyeJnt', posRef = leftEyeJnt, parent = rigmodule.LocalSpace, simpleGroup = True )
    mc.aimConstraint( leftEyeCtrl.C, leftEyeJntGrp, aim = [0, 0, 1], u = [0, 1, 0], wut = 'objectrotation', wu = [0, 1, 0], wuo = rigmodule.LocalSpace )
    
    rightEyeJntGrp = transform.makeLocator( prefix = prefix + 'RightEyeJnt', posRef = rightEyeJnt, parent = rigmodule.LocalSpace, simpleGroup = True )
    mc.aimConstraint( rightEyeCtrl.C, rightEyeJntGrp, aim = [0, 0, 1], u = [0, 1, 0], wut = 'objectrotation', wu = [0, 1, 0], wuo = rigmodule.LocalSpace )
    
    #===========================================================================
    # connect eye joints rotation
    #===========================================================================
    
    eyeTopJoints = [leftEyeJnt, rightEyeJnt]
    eyeJntGrps = [leftEyeJntGrp, rightEyeJntGrp]
    
    if eyesChannelConnection:
        
        for i in range( 2 ):
            
            eyeJoints = joint.getlist( eyeTopJoints[i] )
            eyeDriverJoints = joint.duplicateChain( eyeJoints, suffix = 'Driver' )
            mc.parent( eyeDriverJoints[0], rigmodule.LocalSpace )
            rigmodule.connectSkeletonVis( eyeDriverJoints[0] )
            mc.parentConstraint( eyeJntGrps[i], eyeDriverJoints[0], mo = 1, st = ['x', 'y', 'z'] )
            eyeRo = mc.getAttr( eyeTopJoints[i] + '.ro' )
            mc.setAttr( eyeDriverJoints[0] + '.ro', eyeRo )
            
            for axis in ['x', 'y', 'z']:
                
                mc.connectAttr( eyeDriverJoints[0] + '.r' + axis, eyeTopJoints[i] + '.r' + axis )
            
            mc.connectAttr( eyeDriverJoints[0] + '.ro', eyeTopJoints[i] + '.ro' )
    
    else:
        
        for i in range( 2 ):
            
            mc.parentConstraint( eyeJntGrps[i], eyeTopJoints[i], mo = 1, st = ['x', 'y', 'z'] )
    
    
    #===========================================================================
    # space switching
    #===========================================================================
    
    attribute.addSection( mainEyeCtrl.C, 'adjust' )
    
    mainEyeCtrlSpaceSwitchGrp = transform.makeOffsetGrp( mainEyeCtrl.Off, suffix = 'SpaceSwitch' )
    constraint.makeSwitch( mainEyeCtrlSpaceSwitchGrp, rigmodule.Toggle, 'space', ['local', 'global', 'body'], 'parentConstraint', [rigmodule.LocalSpace, rigmodule.GlobalSpace, rigmodule.BodySpace], 1, defaultIdx = 0 )
    
    spaceSwitchPlugs = [ rigmodule.Toggle + '.space' ]
    
    
    # make connection line from main control to head
    curve.makeConnectionLine( mainEyeCtrl.C, midEyeGrp, prefix = prefix, overrideMode = 1, curveParent = rigmodule.Controls )
    
    return {
            'module':rigmodule,
            'mainGrp':rigmodule.Main,
            'leftEyeCtrl':leftEyeCtrl,
            'rightEyeCtrl':rightEyeCtrl,
            'mainEyeCtrl':mainEyeCtrl,
            'globalSpaceGrp':rigmodule.GlobalSpace,
            'bodySpaceGrp':rigmodule.BodySpace,
            'localSpaceGrp':rigmodule.LocalSpace,
            'spaceSwitchPlugs':spaceSwitchPlugs,
            'toggleGrp':rigmodule.Toggle,
            'settingsGrp':rigmodule.Settings
            }
    
def _eye_getTargetPositionForEyeJnt( eyeJnt, distanceFactor = 20.0, keepControlsInEyeDirection = False ):
    
    """
    function to get position of eye target based on its start and end joints
    
    use distanceFactor to scale distance of target
    """
    
    startVec = vector.makeMVector( mc.xform( eyeJnt, q = 1, t = 1, ws = 1 ) )
    offsetVec = vector.makeMVector( [0, 0, distanceFactor] )
    
    if keepControlsInEyeDirection:
        
        eyeJntChild = mc.listRelatives( eyeJnt, c = True, type = 'joint' )[0]
        eyeJntVec = vector.from2Objects( eyeJnt, eyeJntChild )
        offsetVec = eyeJntVec * distanceFactor
    
    jntVec = startVec + offsetVec
     
    
    
    return [jntVec.x, jntVec.y, jntVec.z]
    