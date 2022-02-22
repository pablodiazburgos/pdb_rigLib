'''
functions for working with surfaces (nurbsSurface) 
@category Rigging @subcategory Utils
@tags surfaceObj nurbs
'''

import maya.cmds as mc

import name
import shape

def getUvCvSizes( surfaceObj ):
    
    '''
    return list with size of U and V CV points of nurbsSurface
    
    @param surfaceObj: name of surfaceObj object
    @type surfaceObj: str
    @return: list(int) - list with 2 int numbers, 0- U value, 1- V value
    '''
    
    formU = mc.getAttr( surfaceObj + '.formU' )
    formV = mc.getAttr( surfaceObj + '.formV' )
    
    degreeU = mc.getAttr( surfaceObj + '.degreeUV' )[0][0]
    degreeV = mc.getAttr( surfaceObj + '.degreeUV' )[0][1]
    
    spansU = mc.getAttr( surfaceObj + '.spansUV' )[0][0]
    spansV = mc.getAttr( surfaceObj + '.spansUV' )[0][1]
    
    maxU = spansU
    maxV = spansV
    
    # adjust number of CV points if parameter is non-linear degree
    # and open form
    
    if formU == 0 and degreeU > 1:
        
        maxU = spansU + degreeU
    
    if formV == 0 and degreeV > 1:
        
        maxV = spansV + degreeV
    
    return [ maxU, maxV ]

def getClosestPointOnSurfaceFromPosition( worldPosition, surfaceObj, normalizeCoords = False ):
    
    '''
    get closest point on surfaceObj, return both parameter and world position
    
    :param object: str, name of transform object
    :param surfaceObj: str, name of nurbsSurface object
    :return: list( list( float, float ), list( float, float, float ) ) - first list has UV parameters and second has world position
    '''
    
    prefix = 'getClosestPointOnSurf'
    
    closestNode = mc.createNode( 'closestPointOnSurface', n = prefix + '_cps' )
    surfaceShape = shape.getShapes( surfaceObj )[0]
    
    mc.connectAttr( surfaceShape + '.worldSpace[0]', closestNode + '.inputSurface' )
    
    mc.setAttr( closestNode + '.inPosition', worldPosition[0], worldPosition[1], worldPosition[2] )
    
    closestPos = mc.getAttr( closestNode + '.position' )[0]
    closestParamU = mc.getAttr( closestNode + '.parameterU' )
    closestParamV = mc.getAttr( closestNode + '.parameterV' )
    closestParams = [ closestParamU, closestParamV ]
    
    mc.delete( closestNode )
    
    if normalizeCoords:
        
        closestParams = getNormalizedCoordinates( surfaceObj, closestParams )
    
    return [ closestParams, closestPos ]

def getClosestPointOnSurface( object, surfaceObj, normalizeCoords = False ):
    
    '''
    get closest point on surfaceObj, return both parameter and world position
    
    @param object: str, name of transform object
    @param surfaceObj: str, name of nurbsSurface object
    @return: list( list( float, float ), list( float, float, float ) ) - first list has UV parameters and second has world position
    '''
    
    tempGrp = mc.createNode( 'transform', n = 'TEMP_position_query_grp_' + object )
    mc.pointConstraint( object, tempGrp )
    objectWorldPos = mc.xform( tempGrp, q = 1, t = 1, ws = 1 )
    mc.delete( tempGrp )
    
    closestParams, closestPos = getClosestPointOnSurfaceFromPosition( objectWorldPos, surfaceObj, normalizeCoords )
    
    return [ closestParams, closestPos ]