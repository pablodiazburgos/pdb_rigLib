"""
general rigs systems
@category Rigging @subcategory Rig
"""

import maya.cmds as mc
from collections import OrderedDict

from base import control
from base import module

from utils import name
from utils import shape

def makeFkControlChain( chain, 
                        prefix = '', 
                        scale = 1.0, 
                        connectR = True, 
                        connectT = False, 
                        useConstraints = False,
                        constraintSeq = [], 
                        constraintFirst = False, 
                        prefixSeq = [], 
                        ctrlshape = 'cubeOnBase', 
                        ctrlColorName = None,
                        worldOrient = False, 
                        ctrlParent = None ):
    
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
        

        rotateCtrl = chain[i]
        if worldOrient:
            rotateCtrl = ''
        
        ctrl = control.Control( lockHideChannels = lockHideList, prefix = jntPrefix, shape = ctrlshape, colorName = ctrlColorName, translateTo = chain[i],  rotateTo = rotateCtrl, rotOrd = rotOrd, scale = scale, ctrlParent = ctrlParentObj )
        
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

def smartFkControlChain(
                        chain,
                        ctrlsNumber = 4,
                        prefix = '', 
                        scale = 1.0, 
                        prefixSeq = [], 
                        ctrlshape = 'cubeOnBase', 
                        ctrlColorName = None, 
                        ctrlParent = None 
                         ):
    
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
    # define some limit for passed ctrlsNumber value so script wont break
    if ctrlsNumber > len( chain ):
        ctrlsNumber = len( chain )
    if ctrlsNumber < 2:
        ctrlsNumber = 2
    
    if not prefix:
        prefix = name.getBase( chain[0] )
    
    if len( prefixSeq ) is not ctrlsNumber:
        prefixSeq = []
    
    if not prefixSeq:
        prefixSeq = [ '%s%d' % ( prefix, i + 1 ) for i in range( ctrlsNumber ) ]
    
    # create main group which hold all the controls
    if ctrlParent:
        controlsGrp = mc.group(em = True, p = ctrlParent,  n = prefix + 'FkControls_grp' )
    else:
        controlsGrp = mc.group(em = True, w = True, n = prefix + 'FkControls_grp' )
    
    # create controls
    lockHideList = ['t']
    ctrlsList = []
    for i in range( ctrlsNumber ):
        ctrl = control.Control( lockHideChannels = lockHideList, prefix = prefixSeq[i], shape = ctrlshape, colorName = ctrlColorName, scale = scale, ctrlParent = controlsGrp )
        ctrlsList.append( ctrl )
    
    # divisions to know how many jnts will drive each ctrl  
    jntPerCtrl = len( chain )/ctrlsNumber
    modRes = len( chain ) % ctrlsNumber

    # define how many joint will control each control
    jntPerCtrlList = []
    
    for i in range( ctrlsNumber ):
    
        if i < modRes:
            jntPerCtrlList.append( jntPerCtrl + 1 )
        else:
            jntPerCtrlList.append( jntPerCtrl )
    
    # create a list with the same length of the total of joints but with the controls duplicated by the number of
    # joints each control will drive
    fullCtrlsList = []
    for ctrl, repNum in zip( ctrlsList, jntPerCtrlList ):

        for i in range( repNum ):
            fullCtrlsList.append( ctrl )
    
    
    jntsToCtrlDic = OrderedDict()
    for jnt, ctrl in zip( chain, fullCtrlsList ):
        
        jntsToCtrlDic[jnt] = ctrl
    
    # create a dictionary to define the joint which the control will get the position from and also the driver
    # joint to contrl the offsetGrp of the control
    
    ctrlsDrivers = OrderedDict()
    for i, ( jnt,ctrl ) in enumerate( jntsToCtrlDic.items() ):
        
        if ctrl in ctrlsDrivers.keys():
            continue
        else:
            if i == 0:
                ctrlsDrivers[ctrl] = [ jnt, jnt ]
            else:
                ctrlsDrivers[ctrl] = [ jnt, chain[i - 1] ]
    
    #  move and orient controls to proper joints, also contrainst to the offset grp from driverJnts
    for i, (ctrl, joints) in enumerate( ctrlsDrivers.items() ):
        
        mc.delete( mc.parentConstraint( joints[0], ctrl.Off ) )
        
        if i == 0:
            continue
        
        mc.parentConstraint( joints[1], ctrl.Off, mo = True )
    
    # connect ctrls to joints rotation
    for i, (jnt, ctrl ) in enumerate( jntsToCtrlDic.items() ):
        
        if i == 0:
            mc.parentConstraint( ctrl.C, jnt, mo = True )
        else:
            for axis in ['.rx', '.ry', '.rz']:
                mc.connectAttr( ctrl.C + axis, jnt + axis )
            mc.connectAttr( ctrl.C + '.ro', jnt + '.ro' )
    
    return [controlsGrp, ctrlsList]