"""
eyelids module
@category Rigging @subcategory Rig
"""
import maya.cmds as mc

from base import module
from base import control

from utils import name
from utils import shape
from utils import attribute
from utils import transform


def singleJoint( 
                eyeJnt,
                upperEyelidJnt,
                lowerEyelidJnt,
                prefix = 'l_eyelids',
                ctrlScale = 1.0,
                baseRigData = None,
                makeConstraint = False,
                fleshyLids = False,
                eyesMainCtrl = ''
                ):
    
    """
    simple eyelids setup using single eyelid joint for upper and lower eyelid
    
    NOTE: setup system assumes that upper and lower eyelid joints are duplicated and rotated joints from eye joint.
            Their rotation has to be zeroed out.
            
        To attach this module, it is recommended to use rigmodule.LocalSpace to be constrained to head joint.
        Example:
        mc.parentConstraint( headJnt, l_eyelidsData['module'].LocalSpace, mo = True )
    
    :param eyeJnt: str, main eye joint
    :param upperEyelidJnt: str, upper eyelid joint
    :param lowerEyelidJnt: str, lower eyelid joint
    :param prefix: str, prefix for the object to be created
    :param ctrlScale: float, scale for module objects
    :param baseRigData: instance, instance of base.build() class
    :param fleshyLids: bool, fleshy setup that follows the eye joint, "eyesMainCtrl" needs to be passed
    :param eyesMainCtrl: str, eyes main control to hold the fleshy lids attributes
    :return dictionary, containing the module 
    """
    
    #===========================================================================
    # module groups
    #===========================================================================
    
    rigmodule = module.Module( prefix )
    rigmodule.connect( baseRigData = baseRigData )
    rigmodule.parent( baseRigData = baseRigData )
    
    
    #===========================================================================
    # create controls
    #===========================================================================
    
    eyelidJoints = [upperEyelidJnt, lowerEyelidJnt]
    eyelidJointPrefixes = ['Upper', 'Lower']
    eyelidControls = []
    
    if not makeConstraint:
    
        for eyelidJnt, eyelidPrefix in zip( eyelidJoints, eyelidJointPrefixes ):
            
            ctrlPrefix = prefix + eyelidPrefix
            ctrl = control.Control( prefix = ctrlPrefix, lockHideChannels = ['t'], moveTo = eyelidJnt, colorName = 'secondary', scale = ctrlScale * 2, shape = 'circleX', ctrlParent = rigmodule.Controls )
            eyelidControls.append( ctrl )
            
            mc.connectAttr( ctrl.C + '.r', eyelidJnt + '.r' )
            mc.connectAttr( ctrl.C + '.ro', eyelidJnt + '.ro' )
        
        mc.parentConstraint( rigmodule.LocalSpace, rigmodule.Controls, mo = True )
        
    else:
        for eyelidJnt, eyelidPrefix in zip( eyelidJoints, eyelidJointPrefixes ):
            
            ctrlPrefix = prefix + eyelidPrefix
            ctrl = control.Control( prefix = ctrlPrefix, lockHideChannels = ['t'], moveTo = eyelidJnt, colorName = 'secondary', scale = ctrlScale * 2, shape = 'circleX', ctrlParent = rigmodule.Controls )
            eyelidControls.append( ctrl )
            
            mc.orientConstraint( ctrl.C, eyelidJnt, mo = True )
        
        mc.parentConstraint( rigmodule.LocalSpace, rigmodule.Controls, mo = True )
        
    # FLESHY SETUP
    if fleshyLids:
        
        # create needed attributes
        fleshyAt = 'fleshyLids'
        fleshyFollowAt = 'LidFollow'
        
        if not mc.attributeQuery(fleshyAt, node = eyesMainCtrl, exists = True):
            attribute.addSection( eyesMainCtrl, fleshyAt )
        
        mc.addAttr(eyesMainCtrl, ln = prefix + fleshyFollowAt, at = 'float', min = 0.0, max = 1.0, dv = 0.5, k = True )
        
        for i, (eyelidPrefix, followVal) in enumerate( zip( eyelidJointPrefixes,[ 0.75, 0.2 ] ) ):
            
        
            # create offsetgroup to drive the eyelid
            offsetLidGrp = transform.makeOffsetGrp(eyelidControls[i].C, suffix = '{}LidFleshyOffset'.format( eyelidPrefix ))
            
            # create multiple divide to follow the eye
            followMdv = mc.createNode( 'multiplyDivide', n = prefix + '{}LidFleshy_mdv'.format(eyelidPrefix) )
            
            # set follow values
            mc.setAttr( followMdv + '.input2X', 0.1 )
            mc.setAttr( followMdv + '.input2Y', 0.1 )
            mc.setAttr( followMdv + '.input2Z', followVal )
            
            # connect driver joint
            mc.connectAttr( eyeJnt + '.rotate', followMdv + '.input1' )
            
            # create multiplier compensate
            multCompMdl = mc.createNode( 'multDoubleLinear', n = prefix + '{}LidFleshyMultCompansate_mdl' )
            mc.connectAttr( eyesMainCtrl + '.' + prefix + fleshyFollowAt, multCompMdl + '.input1' )
            mc.setAttr( multCompMdl + '.input2', 2 )
            
            # fix final follow values 
            followFixMdv = mc.createNode( 'multiplyDivide', n = prefix + '{}LidFleshyFix_mdv'.format(eyelidPrefix) )
            mc.connectAttr( followMdv + '.output', followFixMdv + '.input1' )
            for at in ['X','Y','Z']:
                mc.connectAttr( multCompMdl + '.output', followFixMdv + '.input2{}'.format(at) )
                
            # connect to offset driven group
            mc.connectAttr( followFixMdv + '.output', offsetLidGrp + '.rotate'  )
            
    return {
            'module':rigmodule,
            'controls':eyelidControls
            } 
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    