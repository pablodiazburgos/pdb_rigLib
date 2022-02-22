'''
functions for working with mesh and polygons
@category Rigging @subcategory Utils
'''

import maya.cmds as mc
import shape

def getClosestMeshInfo( meshObject, refTransform = None, refPosition = [0, 0, 0] ):
    
    '''
    given reference transform return closest mesh information list: position, UV, face index and vertex index
    
    :param meshObject: str, mesh object name: transform or its shape
    :param refTransform: str, reference transform to have center point to search from, if None, then use refPosition
    :param refPosition: optionaly, if refTransform was None, use provided world position values
    :return: list( list(float3), list(float3), list(float2), int, int ) - combined values: position, normal, UV parameters, face index, vertex index
    '''
    
    # get input info
    
    meshShape = shape.getShape( meshObject, useLongName = True )[0]
    
    if refTransform:
        
        tempGrp = mc.group( n = refTransform + 'Temp_grp', em = True )
        mc.delete( mc.pointConstraint( refTransform, tempGrp ) )
        refPosition = mc.xform( tempGrp, q = 1, t = 1, ws = 1 )
        mc.delete( tempGrp )
    
    # connect mesh
    
    cpmNode = mc.createNode( 'closestPointOnMesh', n = 'closestMeshInfo_cpm' )
    mc.setAttr( cpmNode + '.inPosition', refPosition[0], refPosition[1], refPosition[2] )
    mc.connectAttr( meshShape + '.worldMatrix[0]', cpmNode + '.inputMatrix' )
    mc.connectAttr( meshShape + '.worldMesh[0]', cpmNode + '.inMesh' )
    
    # get results
    
    closestPosition = mc.getAttr( cpmNode + '.position' )[0]
    closestNormal = mc.getAttr( cpmNode + '.normal' )[0]
    closestUvParam = [ mc.getAttr( cpmNode + '.parameterU' ), mc.getAttr( cpmNode + '.parameterV' ) ]
    closestFaceIdx = mc.getAttr( cpmNode + '.closestFaceIndex' )
    closestVertexIdx = mc.getAttr( cpmNode + '.closestVertexIndex' )
    
    # delete mesh info node
    
    mc.delete( cpmNode )
    
    return [ closestPosition, closestNormal, closestUvParam, closestFaceIdx, closestVertexIdx ]

def getClosestEdgePair( meshObject, refTransform = None, refPosition = [0, 0, 0] ):
    
    '''
    this function returns pair of edges which are on the closest face to reference transform
    As this is mainly made for rivets, function find opposie edges (if possible),
    now it just takes 1. and 3. edge, which works fine for 3 and 4 edges faces
    
    :param meshObject: str, mesh object name: transform or its shape
    :param refTransform: str, reference transform to have center point to search from, if None, then use refPosition
    :param refPosition: optionaly, if refTransform was None, use provided world position values
    :return: list( int, int ), list with 2 edges indeces of closes edges to transform
    '''
    
    closestInfoList = getClosestMeshInfo( meshObject, refTransform, refPosition )
    meshShape = shape.getShape( meshObject )[0]
    closestFace = '%s.f[%d]' % ( meshShape, closestInfoList[3] )
    
    faceRes = mc.polyInfo( closestFace, faceToEdge = 1 )[0]
    faceResSplit = faceRes.split()[2:]
    edgesIdxList = [ int( edgeStr ) for edgeStr in faceResSplit ]
    
    edgePair = [ edgesIdxList[0], edgesIdxList[2] ]
    
    return edgePair