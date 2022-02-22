"""
hand module
@category Rigging @subcategory Rig
"""

import maya.cmds as mc

import general

from base import module

from utils import name
from utils import joint


def build(
            baseRigData,
            handJnt,
            topFingJnts,
            prefix = 'new',
            ctrlScale = 1.0,
            doConstraintRot = False,
            enableFingerTranslate = True,
            withEndJoints = False
            ):
    
    """
    setup hand
    (this module sets up fingers of the hand, hand controls are part of arm module)
    
    :param handJnt: str, hand joint
    :param topFingJnts: list(str), proximal phalanx joints of all fingers, starting from thumb, then index etc.
    :param prefix: str, name used for every new object
    :param ctrlScale: float, scale of controls
    :param doConstraintRot: bool, constraint rotation of finger joints to controls instead of connecting local rotation
    :param enableFingTranslate: bool, constraint finger joints position to controls
    :param baseRigData: rigbase.base.build() instance, base rig data returned from rigbase.base build() to connect visibility channels etc. to the main base
    :param withEndJoints: bool, create a control at the end of the finger joint chain
    :return: dictionary with rig objects
    """
    
    # names
    side = name.getSide( prefix )
    
    #===========================================================================
    # module
    #===========================================================================
    
    rigmodule = module.Module( prefix )
    rigmodule.connect( baseRigData = baseRigData )
    rigmodule.parent( baseRigData = baseRigData )
    
    # make return directory
    
    fingerCtrls = [ None ] * 5
    
    for i, topJnt in enumerate( topFingJnts ):
        
        chainFingerJnts = joint.listHierarchy( topJnt, withEndJoints = withEndJoints )
        
        prefix = name.getBase( topJnt )
        
        fingerRigData = general.makeFkControlChain( chain = chainFingerJnts, 
                                                    prefix = prefix, 
                                                    scale = ctrlScale, 
                                                    connectR = True, 
                                                    connectT = enableFingerTranslate, 
                                                    useConstraints = doConstraintRot, 
                                                    constraintFirst = False, 
                                                    ctrlshape = 'circle', 
                                                    ctrlColorName = 'secondary', 
                                                    ctrlParent = rigmodule.Controls )
                    


        mc.parentConstraint( handJnt, fingerRigData[0].Off, mo = True)

        fingerCtrls[i] =  fingerRigData 
    
        

    return {
            'thumbControls': fingerCtrls[0],
            'indexControls': fingerCtrls[1],
            'middleControls': fingerCtrls[2],
            'ringControls': fingerCtrls[3],
            'pinkyControls': fingerCtrls[4],
            'module':rigmodule
            }
