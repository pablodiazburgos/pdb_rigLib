"""
Module to switch ik and fk with out any pop and make proper key frames 
"""

import maya.cmds as mc
import maya.OpenMaya as om

def switch():
    
    # define items
    ikFkAttr = 'fkIkSnapable'
    fkControls = []
    
    # list all the selected items
    itemsSelection = mc.ls( sl = True, type = 'transform' )
    for item in itemsSelection:
        
        # check if selection is a snapable control
        userAttrs = mc.listAttr( item, ud = True )
        if not ikFkAttr in userAttrs:
            print '# No {} attribute found in {} ... skipping '.format( ikFkAttr, item )
            continue
        
        # define fk-ik snap items
        
        # joints
        upperJnt = mc.listConnections( item + '.upperJnt' )[0]
        midJnt = mc.listConnections( item + '.midJnt' )[0]
        endJnt = mc.listConnections( item + '.endJnt' )[0]
        
        # fk controls
        upperFkControl = mc.listConnections( item + '.upperFkControl' )[0]
        midFkControl = mc.listConnections( item + '.midFkControl' )[0]
        endFkControl = mc.listConnections( item + '.endFkControl' )[0]
        
        # ik controls
        ikControl = mc.listConnections( item + '.ikControl' )[0]
        pvControl = mc.listConnections( item + '.pvControl' )[0]      
        limbIk = mc.listConnections( item + '.limbIk' )[0]
        
        # driven joints 
        upperFkDrivenJnt = mc.listConnections( item + '.upperFkDrivenJnt' )[0]
        midFkDrivenJnt = mc.listConnections( item + '.midFkDrivenJnt' )[0]
        endFkDrivenJnt = mc.listConnections( item + '.endFkDrivenJnt' )[0]
        
        upperIkDrivenJnt = mc.listConnections( item + '.upperIkDrivenJnt' )[0]
        midIkDrivenJnt = mc.listConnections( item + '.midIkDrivenJnt' )[0]
        endIkDrivenJnt = mc.listConnections( item + '.endIkDrivenJnt' )[0]      
        
        # snap loc reference for fk to ik
        snapLoc = mc.listConnections( item + '.snapLoc' )[0]
        
        # get fk-ik state
        toggleState = mc.getAttr( item + '.fkIk' )
        
        if toggleState != 0 and toggleState != 1:
            print '# {} fkIk attribute must be  0 or 1 ... cannot be an inbetween value ... skipping'.format( item )
            continue
        
        # get time values
        currentFrame = mc.currentTime( q = True )
        prevFram = currentFrame - 1.0
        
        # make snap from fk to ik
        if toggleState == 0:
            
            # go to previous frame and make key frames
            mc.currentTime( prevFram, e = True )
            mc.setKeyframe( item, at = '.fkIk' )
            mc.setKeyframe( upperFkControl )
            mc.setKeyframe( midFkControl )
            mc.setKeyframe( endFkControl )
            # go back to current frame and make the switch from fk to ik
            mc.currentTime( currentFrame, e = True )
            
            # get pv position
            pvPos = _findPoleVectorPosition(topJnt = upperFkDrivenJnt, midJnt = midFkDrivenJnt, endJnt = endFkDrivenJnt, posOffset = 0.8)
            
            mc.xform( pvControl, ws = True, t = ( pvPos['position'][0], pvPos['position'][1],  pvPos['position'][2] ) )
            mc.delete(mc.parentConstraint( snapLoc, ikControl) )
            #mc.delete( mc.pointConstraint( snapLoc, limbIk ) )
            
            mc.setKeyframe( ikControl )
            mc.setKeyframe( pvControl )
            
            mc.setAttr( item + '.fkIk', 1 )
            mc.setKeyframe( item, at = '.fkIk' )
        
        # make snap from ik to fk
        if toggleState == 1:
            
            # go to previous frame and make key frames
            mc.currentTime( prevFram, e = True )
            
            mc.setKeyframe( item, at = '.fkIk' )
            mc.setKeyframe( ikControl )
            mc.setKeyframe( pvControl )
            
            # go back to current frame and make the switch from ik to fk
            mc.currentTime( currentFrame, e = True )
            
            # move fk controls to ik joints position
            mc.delete(mc.orientConstraint( upperJnt, upperFkControl) )
            mc.delete(mc.orientConstraint( midJnt, midFkControl ) )
            mc.delete(mc.orientConstraint( endJnt, endFkControl ) )
            
            # set keyframes
            for ctrl in [upperFkControl, midFkControl, endFkControl]:
                mc.setKeyframe( ctrl )
            
            mc.setAttr( item + '.fkIk', 0 )
            mc.setKeyframe( item, at = '.fkIk' )
            
def _findPoleVectorPosition( topJnt, midJnt, endJnt, posOffset = 2 ):
    
    """
    find the position for pole vector
    :param topJnt: str, top joint of chain to get pv position (e.g hip/shoulder)
    :param midJnt: str, mid joint of chain to get pv position (e.g knee/elbow)
    :param endJnt: str, end join of the chain to get pv position (e.g foot/hand)
    :return dictionary, with position values
    """
    # get inital vectors
    mid = mc.xform(midJnt ,q= 1 ,ws = 1,t =1 )
    midV = _makeMVector( values = (mid[0] ,mid[1],mid[2]) )
    
    startEnd = _from2Objects( topJnt, endJnt, normalized = True )
    startMid = _from2Objects( topJnt, midJnt, normalized = True )
    
    # create vector projection
    dotP = startMid * startEnd
    proj = float(dotP) / float(startEnd.length())
    startEndN = startEnd.normal()
    projV = startEndN * proj
    
    arrowV = startMid - projV
    arrowV*= posOffset * 200
    finalV = arrowV + midV
    
    pos = [ finalV.x, finalV.y, finalV.z ]
    
    return {
            'position': pos,
            }
            
def _makeMVector( values = [0.0, 0.0, 0.0] ):
    
    '''
    :summary: wrapper to make MVector instance from list of floats
    :param values: list(float, float, float) 3 numbers to make vector
    :type values: list of floats     
    
    :return: OpenMaya.MVector
    '''
    
    return om.MVector( values[0], values[1], values[2] )
            
def _from2Objects( objA, objB, normalized = True ):
    
    '''
    :param objA: str, first object
    :param objB: str, second object
    :param normalized: bool, optional, normalize resulting vector
    :return: list of 3 floats
    
    make vector using world positions of 2 given objects
    NOTE: order of passed objects matters - object B is the one "more far" or "later in time"
    '''
    
    avect = _makeMVector( _getPositionFromObj( objA ) )
    bvect = _makeMVector( _getPositionFromObj( objB ) )
    
    resvect = bvect - avect
    
    if normalized:
        
        resvect.normalize()
    
    
    return resvect

def _getPositionFromObj( obj ):
    
    """
    get world position from reference object
    
    :param obj: str, name of reference object
    :return: str, name of group
    """
    
    grp = mc.group( n = obj + '_ref_grp', em = True )
    mc.delete( mc.parentConstraint( obj, grp ) )
    pos = mc.xform( grp, q = 1, t = 1, ws = 1 )
    mc.delete( grp )
    
    return pos