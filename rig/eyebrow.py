'''
eyebrows module
@category Rigging @subcategory Rig
'''

import maya.cmds as mc

from ..utils import name
from ..utils import shape
from ..utils import constraint
from ..utils import transform

from ..base import control
from ..base import module

def simpleJoints( 
            innerJnt,
            midJnt,
            outerJnt,
            mainLocator = None,
            prefix = 'l_eyebrow',
            ctrlScale = 1.0,
            baseRigData = None,
            relativeMode = False,
            lockFor2d = False
            ):
    
    """
    simple setup based on 3 joints - inner, middle, outer
    
    NOTE: setup can be used both in relative and absolute ways, 
            because joints have channel connections
            
    :param innerJnt: str, inner eyebrow joint
    :param midJnt: str, middle eyebrow joint
    :param outerJnt: str, outer eyebrow joint
    :param mainLocator: str, optional, main locator is reference for main control, if not provided middle joint is used
    :param prefix: str, prefix for naming new objects
    :param ctrlScale: scale of controls
    :param baseRigData: instance, value from rigbase.base build(), top rig class instance used for connecting module to rig
    :param relativeMode: bool, build joint group with inheritance off to stay in origin, useful for local face setups
    :param lockFor2d: bool, lock eyebrows controls TX, RX and RY channels to restrict its movement in 2d local plane
    :return: dictionary, Module instance and other values from the module
    """
    
    #===========================================================================
    # module
    #===========================================================================
    
    rigmodule = module.Module( prefix )
    rigmodule.connect( baseRigData = baseRigData )
    rigmodule.parent( baseRigData = baseRigData )
    
    #===========================================================================
    # joints
    #===========================================================================
    
    mc.parent( innerJnt, midJnt, outerJnt, rigmodule.Joints )
    
    #===========================================================================
    # controls
    #===========================================================================
    
    if not mainLocator:
        
        mainLocator = midJnt
    
    lockHideChannels = []
    if lockFor2d:
        
        lockHideChannels = ['tz', 'rx', 'ry']
    
    mainCtrl = control.Control( prefix = prefix + 'Main', lockHideChannels = lockHideChannels, moveTo = mainLocator, shape = 'circleZ', scale = ctrlScale * 2, ctrlParent = rigmodule.Controls)
    
    subControls = []
    controlsRelativeDriverGrp = mc.group( n = prefix + 'ControlsRelativeJointDriver_grp', em = True, p = rigmodule.Controls )
    
    # setup controls and joints to follow main rig
    mc.parentConstraint( rigmodule.LocalSpace, rigmodule.Controls, mo = True )
    
    if not relativeMode:
        
        mc.parentConstraint( rigmodule.LocalSpace, rigmodule.Joints, mo = True )
    
    subJointsPrefixes = ['Inner', 'Mid', 'Outer']
    subDriverGroups = []
    for jnt, subJointPrefix in zip( [innerJnt, midJnt, outerJnt], subJointsPrefixes ):
        
        
        subCtrl = control.Control( prefix = prefix + subJointPrefix, colorName = 'secondary', lockHideChannels = lockHideChannels, moveTo = jnt, shape = 'move', scale = ctrlScale * 1, ctrlParent = mainCtrl.C )
        subControls.append( subCtrl )
        
        subDriverGrp = transform.makeGroup( prefix = prefix + subJointPrefix + 'LocalDriver', referenceObj = subCtrl.C, parentObj = controlsRelativeDriverGrp )
        subDriverGroups.append( subDriverGrp )
        mc.parentConstraint( subCtrl.C, subDriverGrp )
        mc.connectAttr( subCtrl.C + '.s', subDriverGrp + '.s' )
        
    # drive joints by groups - local setup
    for jnt, subGrp in zip( [innerJnt, midJnt, outerJnt], subDriverGroups ):
        
        # reset joint orient before connections from non-joint transform
        mc.setAttr( jnt + '.jo', 0, 0, 0 )
        
        for channel in ['t', 'r', 's']:
            
            for axis in ['x', 'y', 'z']:
                
                mc.connectAttr( subGrp + '.' + channel + axis, jnt + '.' + channel + axis )
        
        mc.connectAttr( subGrp + '.ro', jnt + '.ro' )
    
    
    return {
            'module':rigmodule,
            'mainCtrl':mainCtrl,
            'subControls':subControls
            }
