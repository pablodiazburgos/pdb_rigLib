"""
eyelids module
@category Rigging @subcategory Rig
"""
import maya.cmds as mc

from ..base import module
from ..base import control

from ..utils import name
from ..utils import shape



def singleJoint( 
                eyeJnt,
                upperEyelidJnt,
                lowerEyelidJnt,
                prefix = 'l_eyelids',
                ctrlScale = 1.0,
                baseRigData = None
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
    
    for eyelidJnt, eyelidPrefix in zip( eyelidJoints, eyelidJointPrefixes ):
        
        ctrlPrefix = prefix + eyelidPrefix
        ctrl = control.Control( prefix = ctrlPrefix, lockHideChannels = ['t'], moveTo = eyelidJnt, colorName = 'secondary', scale = ctrlScale * 2, shape = 'circleX', ctrlParent = rigmodule.Controls )
        eyelidControls.append( ctrl )
        
        mc.connectAttr( ctrl.C + '.r', eyelidJnt + '.r' )
        mc.connectAttr( ctrl.C + '.ro', eyelidJnt + '.ro' )
    
    mc.parentConstraint( rigmodule.LocalSpace, rigmodule.Controls, mo = True )
    
    # inheritance with eye joint - to be added
    
    
    return {
            'module':rigmodule,
            } 