'''
transformWrapper
@category Rigging @subcategory Tools
@tags transform joint driver wrap wrapper shape blend
'''
import maya.cmds as mc

from ..utils import name
from ..utils import constraint
from ..utils import connect

from ..tools import rivet

def makePlaneDrivers( prefix = 'driverPlanes', transforms = None, size = 1.0, normalAxis = [1, 0, 0], attachTransforms = True ):
    
    """
    Make simple polygonal planes that can later be wrapped or skinned to drive list of transforms
    
    NOTE: can be used to attach muscle controls. Polygon planes can be skinned to skeleton and this will drive muscles.
            Polygons skin weights can be then edited to change muscles movement.
            
        Size can be important for transforms close to each other for automatic rivet attachment - attachTransforms option.
        Make size smaller if transforms are closer to each other.
    
    :param transforms: list(str), list of transforms (joints, controls etc.) to be driven by rivets on created mesh
    :param prefix: str, prefix for naming new objects
    :param size: float, constant for setting size of various new objects
    :param normalAxis: list(float,float,float), vector setting orientation of polygon plane for each transform
    :param attachTransforms: bool, attach transforms using rivets, this will also remove all connections to transforms TR channels
    :return: list(str) - 0: name of attach polymesh
    """
    
    polyMeshes = []
    
    for t in transforms:
        
        poly = mc.polyPlane( axis = normalAxis, sx = 1, sy = 1, ch = False, width = size, height = size )[0]
        mc.parent( poly, t, r = True )
        mc.parent( poly, w = True )
        polyMeshes.append( poly )
        
    if len(polyMeshes)> 1:
        
        mergedPolymesh = mc.polyUnite( polyMeshes, ch = False )[0]
    
    else:
        
        mergedPolymesh = polyMeshes[0]
    
    mergedPolymesh = mc.rename( mergedPolymesh, prefix + 'Merged_pxy' )
    
    #===========================================================================
    # attach transforms
    #===========================================================================
    
    rivetParentGrp = None
    
    if attachTransforms:
        
        attachRes = makePlaneDrivers_attachTransforms( prefix, transforms, mergedPolymesh )
        rivetParentGrp = attachRes[0]
    
    
    return [mergedPolymesh, rivetParentGrp]

def makePlaneDrivers_attachTransforms( prefix, transforms, mergedPolymesh ):
    
    """
    makePlaneDrivers() helper function to attach transforms
    """
    
    # first remove all connections and constraints from transforms
    # so they can be constrained to rivets
    for t in transforms:
        
        constraint.removeAll( t )
        
        for at in ['t', 'r', 'tx', 'ty', 'tz', 'rx', 'ry', 'rz']:
            
            try:
                
                connect.disconnect( at, source = True, destinations = False )
                
            except:
                
                pass
    
    rivetParentGrp = prefix + 'rivetParent_grp'
    rivetsResult = rivet.rivetObjectsToGeometry( transforms, attachGeometry = mergedPolymesh, prefix = prefix, rivetsParentGrp = rivetParentGrp, useObjectsAsRivets = False, parentRivets = True )
    
    rivetParentGrp = rivetsResult[1]
    
    return [rivetParentGrp]
    