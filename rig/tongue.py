"""
tongue module
@category Rigging @subcategory Rig
"""

import maya.cmds as mc

import general

from base import module

from utils import name
from utils import joint

def buildFk(
            baseRigData,
            jawJnt,
            topTongueJnt,
            prefix = 'new',
            ctrlScale = 1.0,
            doConstraintRot = False,
            enableTranslate = True,
            constraintFirst = False
            ):
    
    """
    setup fk tongue
    
    :param handJnt: str, hand joint
    :param topFingJnts: list(str), proximal phalanx joints of all fingers, starting from thumb, then index etc.
    :param prefix: str, name used for every new object
    :param ctrlScale: float, scale of controls
    :param doConstraintRot: bool, constraint rotation of finger joints to controls instead of connecting local rotation
    :param enableFingTranslate: bool, constraint finger joints position to controls
    :param constraintFirst: bool, first control can be constrained, useful to orient to transforms which are not parent of chain
    :param baseRigData: rigbase.base.build() instance, base rig data returned from rigbase.base build() to connect visibility channels etc. to the main base
    :return: dictionary with rig objects
    """
    #===========================================================================
    # module
    #===========================================================================
    
    rigmodule = module.Module( prefix )
    rigmodule.connect( baseRigData = baseRigData )
    rigmodule.parent( baseRigData = baseRigData )
    
        
    tongueJnts = joint.listHierarchy( topTongueJnt, withEndJoints = False )
    
    prefix = name.getBase( topTongueJnt )
    
    tongueRigData = general.makeFkControlChain( chain = tongueJnts, 
                                                prefix = prefix, 
                                                scale = ctrlScale, 
                                                connectR = True, 
                                                connectT = enableTranslate, 
                                                useConstraints = doConstraintRot, 
                                                constraintFirst = constraintFirst, 
                                                ctrlshape = 'circle', 
                                                ctrlColorName = 'primary', 
                                                ctrlParent = rigmodule.Controls )
                


    mc.parentConstraint( jawJnt, tongueRigData[0].Off, mo = True)

    
    return{
        'module':rigmodule,
        'controls': tongueRigData
        }