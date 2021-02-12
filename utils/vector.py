'''
module to work with vectors
@category Rigging @subcategory Utils
'''

import maya.cmds as mc
import maya.OpenMaya as om

def makeMVector( values = [0.0, 0.0, 0.0] ):
    
    '''
    :summary: wrapper to make MVector instance from list of floats
    :param values: list(float, float, float) 3 numbers to make vector
    :type values: list of floats     
    
    :return: OpenMaya.MVector
    '''
    
    return om.MVector( values[0], values[1], values[2] )

def from2Objects( objA, objB, normalized = True ):
    
    '''
    :param objA: str, first object
    :param objB: str, second object
    :param normalized: bool, optional, normalize resulting vector
    :return: list of 3 floats
    
    make vector using world positions of 2 given objects
    NOTE: order of passed objects matters - object B is the one "more far" or "later in time"
    '''
    
    avect = makeMVector( _getPositionFromObj( objA ) )
    bvect = makeMVector( _getPositionFromObj( objB ) )
    
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

def getCrossProduct( vecA, vecB, normalize = True ):
    
    '''
    get the cross product between 2 passed vectors
    :param vecA: str, first object
    :param vecB: str, second object
    :param normalized: bool, optional, normalize resulting vector
    :return cross product between 2 vectors
    '''
    
    resCrossProd = vecA ^ vecB
    
    if normalize:
        
        resCrossProd.normalize()
    
    return resCrossProd