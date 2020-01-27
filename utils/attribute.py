"""
Utilities to deal with attributes
@category Rigging
"""

import maya.cmds as mc


def addSection( object, sectionName = 'Settings' ):
    
    mc.addAttr( object, at = 'enum', ln = sectionName, en = '________________', k = False )
    mc.setAttr( object + '.' + sectionName, l = True, cb = True )
    
def lockHideTransformVis( object, t = [1, 1], r = [1, 1], s = [1, 1], v = [1, 1] ):
    
    '''
    :param object: str, name of object to set its transform and visibility attributes lock/keyable states
    :param t: bool, translate states
    :param r: bool, translate states
    :param s: bool, translate states
    :param v: bool, translate states
    :return: None
    
    NOTE: first value 1 means LOCK, second value 1 means non-keyable (HIDE)
    lock and hide transform and visibility attributess
    '''
    
    xformvals = [ t, r, s ]
    
    # set lock and hide
    
    for i, x in enumerate( ['t', 'r', 's'] ):
        
        # only use full transform component for unlocking
        if xformvals[i][0] == 0:
            
            mc.setAttr( object + '.' + x, l = xformvals[i][0] )
        
        for axis in ['x', 'y', 'z']:
            
            mc.setAttr( object + '.' + x + axis, l = xformvals[i][0], k = ( 1 - xformvals[i][1] ) )
    
    mc.setAttr( object + '.v', l = v[0], k = ( 1 - v[1] ) )

def removeUserDefined( obj ):
    
    '''
    function for removing custom attributes from given object
    
    :param obj:str, object to have removed custom attributes
    :return: list(str), list of removed attribute names, empty if no custom attributes were found
    '''
    
    userDefinedAts = mc.listAttr( obj, ud = 1 )
    
    if not userDefinedAts:
        
        return []
    
    for atName in userDefinedAts:
        
        plug = '%s.%s' % ( obj, atName )
        if mc.objExists( plug ):
            
            mc.setAttr( plug, l = 0 )
            mc.deleteAttr( plug )
    
    return userDefinedAts

def openAllTransformVis( object, t = True, r = True, s = True, v = True ):
    
    '''
    unlock and unhide all transform attributes, options are available for more control
    In case Rotate is True, jointOrient channels will be unlocked too for joint type
    
    NOTE: if option is False, nothing is changed on the object
    
    @param object: name of object to set its transform and visibility attributes lock/keyable states
    @param object: str
    @param t: translate state
    @type t: bool
    @param r: translate state
    @type r: bool
    @param s: translate state
    @type s: bool
    @param v: translate state
    @type v: bool
    @return: None
    '''
    
    if t or r or s or v:
        
        mc.lockNode( object, l = 0 )
    
    for channel, value in zip( ['t', 'r', 's'], [t, r, s] ):
        
        if not value:
            
            continue
        
        for axis in ['x', 'y', 'z']:
            
            mc.setAttr( object + '.' + channel + axis, l = 0, k = 1 )
    
    if v:
        
        mc.setAttr( object + '.v', l = 0, k = 1 )
        
    # unlock joint orient
    if mc.nodeType( object ) == 'joint':
        
        if r:
            
            for axis in ['x', 'y', 'z']:
                
                mc.setAttr( object + '.jo' + axis, l = 0, k = 1 )
    