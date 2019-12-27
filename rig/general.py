"""
general rigs systems
@category Rigging @subcategory Rig
"""

import maya.cmds as mc

from ..base import control
from ..base import module

from ..utils import name
from ..utils import shape

def makeFkControlChain( chain, prefix = '', scale = 1.0, connectR = True, connectT = False, useConstraints = False, constraintSeq = [], constraintFirst = False, prefixSeq = [], ctrlshape = 'cubeOnBase', ctrlColorName = None, ctrlParent = None ):
    
    '''
    make FK controls based on joint chain
    
    :param chain: list( str ), list of joints to make the fk controls
    :param prefix: str, prefix to name all controls and new objects
    :param scale: float, scale of controls (argument for Control class)
    :param connectR: bool, to make rotation connections from control to joint
    :param connectT: bool, connect translation channels using pointConstraint, so FK can be also used to move joints
    :param useConstraints: bool, use constraints to connection rotation from controls
    :param constraintSeq: list( bool ) list of boolean values for each joint, True = constraint, False = make direct connection
    :param constraintFirst: bool, first control can be constrained, useful to orient to transforms which are not parent of chain
    :param prefixSeq: list( str ), list of prefixes for each joint, useful to custom name controls, otherwise joint names will be used
    :param ctrlshape: str, use Control module registered shape name
    :param ctrlColorName: str, use Control module registered color name
    :param ctrlParent: str, optional, name of top FK control parent
    :return: list of Control instances, same order as passed joint list
    '''
    useCtrlNames = False
    
    if prefixSeq:
        
        useCtrlNames = True
    
    if len( constraintSeq ) is not len( chain ):
        
        constraintSeq = []
        
        for i in range( len( chain ) ):
            
            constraintSeq.append( False )
    
    if useConstraints:
        
        constraintSeq = []
        
        for i in range( len( chain ) ):
            
            constraintSeq.append( True )
    
    if constraintFirst: constraintSeq[0] = True    
    
    #===============================================================================
    # controls
    #===============================================================================
    
    controls = []
    
    for i in range( len( chain ) ):
        
        ctrlParentObj = ''
        
        if i > 0:
            
            ctrlParentObj = controls[i - 1].C
        
        elif ctrlParent:
            
            ctrlParentObj = ctrlParent
        
        rotOrd = mc.getAttr( chain[i] + '.ro' )
        baseName = name.getBase( chain[i] )
        side = name.getSide( chain[i] )
        jntPrefix = '%s%d' % ( prefix, i + 1 )
        
        if not prefix:
            
            jntPrefix = name.removeSuffix( chain[i] )
        
        if useCtrlNames:
            
            jntPrefix = prefixSeq[i]
        
        lockHideList = ['t']
        
        if connectT:
            
            lockHideList = []
        
        ctrl = control.Control( lockHideChannels = lockHideList, prefix = jntPrefix, shape = ctrlshape, colorName = ctrlColorName, moveTo = chain[i], rotOrd = rotOrd, scale = scale, ctrlParent = ctrlParentObj )
        
        if connectR:
            
            if constraintSeq[i]:  # check if joint should be constrained
            
                mc.orientConstraint( ctrl.C, chain[i], mo = 1 )
                
            else:  # make local rotate connection
                
                mc.connectAttr( ctrl.C + '.r', chain[i] + '.r' )
                mc.connectAttr( ctrl.C + '.ro', chain[i] + '.ro' )
        
        if connectT:
            
            mc.pointConstraint( ctrl.C, chain[i] )
        
        controls.append( ctrl )
    
    return controls