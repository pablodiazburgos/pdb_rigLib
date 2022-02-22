''''
head module 
@category Rigging @subcategory Rig
'''

import maya.cmds as mc

from utils import constraint
from utils import name
from utils import shape
from utils import transform
from utils import joint
from utils import connect

from base import control
from base import module

from rig import general

def build( 
        headJnt,
        jawJnt,
        headFkParent = None,
        lastNeckJnt = None,
        prefix = 'head',
        jawPrefix = 'jaw',
        upperJawPrefix = 'upperJaw',
        baseRigData = None,
        ctrlScale = 1.0,
        jawTranslate = True,
        alignWithHeadJoint = True,
        buildJaw = True,
        buildUpperJaw = False,
        upperJawJnt = None,
        neckModule = None
        ):
    
    '''
    build head, jaw and neck IK/FK setup
    
    :param headJnt: str, head joint
    :param jawJnt: str, jaw joint
    :param headFkParent: str, object to be parent for head FK control, if not provided headFk can be constrained in post-build
    :param lastNeckJnt: str, optional, last neck joint to be used for rotation compensation in case of head joint position offset
    :param prefix: str, prefix for naming main objects
    :param jawPrefix: str, prefix for naming jaw objects
    :param baseRigData: instance, class instance rigbase.base build(), base rig data returned from rigbase.base build() to connect visibility channels etc. to the main base
    :param ctrlScale: float, scale of controls
    :param jawTranslate: bool, optional, connect translate channels to jaw joint and open them on jaw control
    :param alignWithHeadJoint: bool, align head control with head joint keeping its world axis
    :param buildJaw: bool, build jaw control, useful when just there is separate face rig and just head needs to be made
    :param buildUpperJaw: bool, if buildJaw is True build upper jaw control and also duplicate jaw joint if there was no upperJawJnt provided
    :param upperJawJnt: str, optional, name of upper jaw joint, in case there no provided it will be duplicated from jawJnt
    :param neckModule: rigbase.Module instance, rig module of Neck (neck.build) to get its IK FK driven by head module
    :return: dictionary with rig objects
    '''
    
    #===========================================================================
    # get some more objects
    #===========================================================================
    
    jawEndJnt = mc.listRelatives( jawJnt, c = 1, typ = 'joint' )[0]
    headEndJnt = mc.listRelatives( headJnt, c = 1, typ = 'joint' )[0]
    
    #===========================================================================
    # module
    #===========================================================================
    
    rigmodule = module.Module( prefix )
    rigmodule.parent( baseRigData = baseRigData )
    rigmodule.connect( baseRigData = baseRigData )
    
    # make toggle control
    toggleCtrl = control.Control( prefix = prefix + 'Toggle', lockHideChannels = ['t', 'r'], translateTo = headEndJnt, scale = ctrlScale * 5, colorName = 'secondary', shape = 't', ctrlParent = rigmodule.Controls )
    mc.parentConstraint( headJnt, toggleCtrl.Off, mo = True )
    rigmodule.customToggleObject( toggleCtrl.C )
    
    rigmodule.addIkFkAt()
    
    # drive neck module IKFK by head module
    if neckModule:
        
        neckIkFkAt = neckModule.getIkFkAt()
        headIkFkAt = rigmodule.getIkFkAt()
        connect.disconnect( neckIkFkAt )
        rigmodule.connectIkFk( neckIkFkAt )
        mc.setAttr( neckIkFkAt, k = False )
    
    #===========================================================================
    # head control
    #===========================================================================
    
    head1IkCtrl = control.Control( prefix = prefix + 'Ik1', translateTo = headJnt, scale = 4 * ctrlScale, shape = 'diamond' )
    headEndJnt = mc.listRelatives( headJnt, c = 1, type = 'joint' )[0]
    shape.translateRotate( head1IkCtrl.C, pos = [0, 0, 0], rot = [90, 0, 0], localSpace = True, relative = True, deleteHistory = True )
    shape.centerPointsToObjects( [ head1IkCtrl.C ], [ headJnt, headEndJnt ] )
    rigmodule.connectIkFk( head1IkCtrl.Off + '.v' )
    headIkVisGrp = _makeVisGrp( head1IkCtrl.Off, rigmodule.Controls )
    
    head2IkCtrl = control.Control( prefix = prefix + 'Ik2', translateTo = headJnt, lockHideChannels = ['t'], scale = 1 * ctrlScale, ctrlParent = head1IkCtrl.C, shape = 'singleRotation', colorName = 'secondary' )
    
    if alignWithHeadJoint:
        
        # we assume first child of the head joint will be end head joint
        headTargetGrp = transform.makeGroup( prefix = prefix + 'HeadAim_grp', referenceObj = headJnt, parentObj = headJnt )
        mc.setAttr( headTargetGrp + '.tx', 1 )
        mc.delete( mc.aimConstraint( headTargetGrp, head1IkCtrl.Off, aim = [0, 1, 0], u = [1, 0, 0], wu = [0, 0, -1], wut = 'objectrotation', wuo = headJnt ) )
        mc.delete( headTargetGrp )

    # space switching
    
    constraint.makeSwitch( head1IkCtrl.Off, rigmodule.Toggle, 'rotationSpace', ['local', 'global', 'body'], 'orientConstraint', [rigmodule.LocalSpace, rigmodule.GlobalSpace, rigmodule.BodySpace], 1, defaultIdx = 2 )
    constraint.makeSwitch( head1IkCtrl.Off, rigmodule.Toggle, 'translationSpace', ['local', 'global', 'body'], 'parentConstraint', [rigmodule.LocalSpace, rigmodule.GlobalSpace, rigmodule.BodySpace], 1, defaultIdx = 0, skipRotation = 1 )
    
    #===========================================================================
    # jaw control
    #===========================================================================
    
    jawCtrl = None
    jawLockChannels = ['t']
    
    if buildJaw:
        
        if jawTranslate:
            
            jawLockChannels = []
        
        jawCtrl = control.Control( lockHideChannels = jawLockChannels, prefix = jawPrefix, moveTo = jawJnt, scale = ctrlScale * 3, shape = 'circle', ctrlParent = rigmodule.Controls, colorName = 'green' )
        shape.centerPointsToObjects( [ jawCtrl.C ], [ jawJnt, jawEndJnt ] )
        
        # connect jaw to controls
        mc.parentConstraint( headJnt, jawCtrl.Off, mo = 1 )
        
        for channel in ['r']:
            
            for axis in ['x', 'y', 'z']:
                
                mc.connectAttr( jawCtrl.C + '.' + channel + axis, jawJnt + '.' + channel + axis )
        
        mc.connectAttr( jawCtrl.C + '.ro', jawJnt + '.ro' )
        
        # connect translation to jaw
        
        if jawTranslate:
            
            mc.pointConstraint( jawCtrl.C, jawJnt )
            
    #===========================================================================
    # upper jaw control
    #===========================================================================
    
    upperJawCtrl = None
    
    if buildJaw and buildUpperJaw:
        
        upperJawEndJnt = None
        if upperJawJnt:
            
            if not mc.objExists( upperJawJnt ):
                
                upperJawJnt = None
        
        if not upperJawJnt:
            
            upperJawJoints = joint.duplicateChain( [jawJnt, jawEndJnt], prefix = upperJawPrefix )
            upperJawJnt = upperJawJoints[0]
            upperJawEndJnt = upperJawJoints[1]
        
        else:
            
            upperJawEndJnt = mc.listRelatives( upperJawJnt, c = True, type = 'joint' )[0]
        
        if jawTranslate:
            
            jawLockChannels = []
        
        upperJawCtrl = control.Control( lockHideChannels = jawLockChannels, prefix = upperJawPrefix, moveTo = upperJawJnt, scale = ctrlScale * 2.5, shape = 'circle', ctrlParent = rigmodule.Controls, colorName = 'lightOrange' )
        shape.centerPointsToObjects( [ upperJawCtrl.C ], [ upperJawJnt, upperJawEndJnt ] )
        
        # connect jaw to controls
        
        mc.parentConstraint( headJnt, upperJawCtrl.Off, mo = 1 )
        
        for channel in ['r']:
            
            for axis in ['x', 'y', 'z']:
                
                mc.connectAttr( upperJawCtrl.C + '.' + channel + axis, upperJawJnt + '.' + channel + axis )
        
        mc.connectAttr( upperJawCtrl.C + '.ro', upperJawJnt + '.ro' )
        
        # connect translation to jaw
        
        if jawTranslate:
            
            mc.pointConstraint( upperJawCtrl.C, upperJawJnt )
      
                
    # head fk controls
    
    headFkCtrl = control.Control( lockHideChannels = ['t'], prefix = prefix + 'Fk', moveTo = headJnt, scale = ctrlScale * 3, shape = 'circle', ctrlParent = rigmodule.Controls, colorName = 'secondary' )
    shape.centerPointsToObjects( [ headFkCtrl.C ], [ headJnt, headEndJnt ] )
    
    if not headFkParent:
        
        headFkParent = rigmodule.LocalSpace
    
    ikFkReverse = mc.createNode( 'reverse', n = prefix + 'HeadFkVis_rev' )
    rigmodule.connectIkFk( ikFkReverse + '.ix' )
    mc.connectAttr( ikFkReverse + '.ox', headFkCtrl.Off + '.v' )
    
    mc.parentConstraint( headFkParent, headFkCtrl.Off, sr = ['x', 'y', 'z'], mo = True )
    localFkOrientGrp = transform.makeGroup( prefix = prefix + 'HeadFkOrientLocal', parentObj = rigmodule.LocalSpace )
    constraint.makeSwitch( headFkCtrl.Off, rigmodule.Toggle, 'fkHeadOrient', ['local', 'global', 'body'], 'orientConstraint', [localFkOrientGrp, rigmodule.GlobalSpace, rigmodule.BodySpace], 1, defaultIdx = 0 )
    
    if lastNeckJnt:
        
        headNeckOffsetGrp = transform.makeGroup( prefix = prefix + 'HeadNeckOffset', referenceObj = lastNeckJnt, parentObj = lastNeckJnt )
        mc.delete( mc.orientConstraint( headJnt, headNeckOffsetGrp ) )
        constraint.makeSwitch( headNeckOffsetGrp, rigmodule.Toggle, 'fkIk', ['fk', 'ik'], 'orientConstraint', [ headFkCtrl.C, head3IkCtrl.C ], 1 )
        mc.parentConstraint( headNeckOffsetGrp, headJnt, mo = True )
    
    else:
        constraint.makeSwitch( headJnt, rigmodule.Toggle, 'fkIk', ['fk', 'ik'], 'orientConstraint', [ headFkCtrl.C, head2IkCtrl.C ], 1 )
    
    return {
            'module':rigmodule,
            'head1IkCtrl':head1IkCtrl,
            'head2IkCtrl':head2IkCtrl,
            'jawCtrl':jawCtrl,
            'upperJawCtrl':upperJawCtrl,
            'mainGrp':rigmodule.Main,
            'fkControls':[headFkCtrl],
            'localSpaceGrp':rigmodule.LocalSpace,
            'globalSpaceGrp':rigmodule.GlobalSpace,
            'bodySpaceGrp':rigmodule.BodySpace,
            'localSpaceFkGrp':localFkOrientGrp,
            'toggleGrp':rigmodule.Toggle,
            'settingsGrp':rigmodule.Settings
            }
            
def _makeVisGrp( controlGrp, parent ):

    visGrpName = name.removeSuffix( controlGrp ) + 'CtlVis_grp'
    visGrp = mc.group( n = visGrpName , em = 1, p = parent )
    mc.parent( controlGrp, visGrp )
    
    return visGrp
    
def buildIclone(
                baseRigData,
                headJnt,
                neckJnt,
                prefix = 'head',
                ctrlScale = 1.0
                ):

    '''
    build simple fk head for iclone rigs
    :param baseRigData: instance, class instance rigbase.base build(), base rig data returned from rigbase.base build() to connect visibility channels etc. to the main base
    :param headJnt: str, head joint
    :param neckJnt: str, neck joints , this will be the attach to head control
    :param prefix: str, string to rename new objects
    :return dictionary with rig objects
    '''
    #===========================================================================
    # module
    #===========================================================================
    
    rigmodule = module.Module( prefix )
    rigmodule.parent( baseRigData = baseRigData )
    rigmodule.connect( baseRigData = baseRigData )
    
    # make fk control
    
    headCtrl = control.Control(
             prefix=prefix,
             scale=ctrlScale,
             translateTo=headJnt,
             rotateTo=headJnt,
             ctrlParent=rigmodule.Controls,
             shape = 'diamond',
             defLockHide = ['s','v'],
             )
    
    headEndJnt = mc.listRelatives( headJnt, c = 1, type = 'joint' )[0]
    shape.translateRotate( headCtrl.C, pos = [0, 0, 0], rot = [90, 0, 0], localSpace = True, relative = True, deleteHistory = True )
    shape.centerPointsToObjects( [ headCtrl.C ], [ headJnt, headEndJnt ] )

    mc.connectAttr( headCtrl.C + '.ro', headJnt + '.ro' )
    mc.parentConstraint( headCtrl.C, headJnt, mo = True )
    
    # attach control and make space switch
    mc.parentConstraint( neckJnt, headCtrl.Off, sr = ['x', 'y', 'z'], mo = True )

    constraint.makeSwitch( headCtrl.Off, headCtrl.C, 'fkHeadOrient', ['local', 'global', 'body'], 'orientConstraint', [rigmodule.LocalSpace, rigmodule.GlobalSpace, rigmodule.BodySpace], 1, defaultIdx = 0 )
    
    return{
        'module':rigmodule,
        'control':headCtrl,
        'mainGrp':rigmodule.Main,
        'localSpaceGrp':rigmodule.LocalSpace,
        'globalSpaceGrp':rigmodule.GlobalSpace,
        'bodySpaceGrp':rigmodule.BodySpace,
        }
    
    
    
    
    
    
    
    
    
    