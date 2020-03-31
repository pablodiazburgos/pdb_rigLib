"""
functions to work with pole vector
"""

import math
import maya.cmds as mc
import maya.OpenMaya as om

from ..utils import vector
from ..utils import name

def findPoleVectorPosition( topJnt, midJnt, endJnt, posOffset = 2 ):
    
    """
    find the position for pole vector
    :param topJnt: str, top joint of chain to get pv position (e.g hip/shoulder)
    :param midJnt: str, mid joint of chain to get pv position (e.g knee/elbow)
    :param endJnt: str, end join of the chain to get pv position (e.g foot/hand)
    :return dictionary, with position and rotation values
    """
    # get inital vectors
    mid = mc.xform(midJnt ,q= 1 ,ws = 1,t =1 )
    midV = vector.makeMVector( values = (mid[0] ,mid[1],mid[2]) )
    
    startEnd = vector.from2Objects( topJnt, endJnt, normalized = True )
    startMid = vector.from2Objects( topJnt, midJnt, normalized = True )
    
    # create vector projection
    dotP = startMid * startEnd
    proj = float(dotP) / float(startEnd.length())
    startEndN = startEnd.normal()
    projV = startEndN * proj
    
    arrowV = startMid - projV
    arrowV*= posOffset * 1000
    finalV = arrowV + midV
    
    # get perpendicular vectors to find orientation
    cross1 = vector.getCrossProduct( startEnd, startMid, normalize = True )
    
    cross2 = vector.getCrossProduct( cross1, arrowV, normalize = True )

    matrixV = [arrowV.x , arrowV.y , arrowV.z , 0 , 
    cross1.x ,cross1.y , cross1.z , 0 ,
    cross2.x , cross2.y , cross2.z , 0,
    0,0,0,1]

    matrixM = om.MMatrix()
    
    om.MScriptUtil.createMatrixFromList(matrixV , matrixM)
    
    matrixFn = om.MTransformationMatrix(matrixM)
    
    rot = matrixFn.eulerRotation()
    
    rotX = rot.x/math.pi*180.0
    rotY = rot.y/math.pi*180.0
    rotZ = rot.z/math.pi*180.0
    
    rot = [rotX, rotY, rotZ]
    pos = [ finalV.x, finalV.y, finalV.z ]
    
    return {
            'position': pos,
            'rotation': rot
            }

def poleVectorReferenceLocator( topJnt, midJnt, endJnt, prefix = '' ):
    """
    Create a locator where pole vector should be... this locator gets affected by the joints plane
    this script should be used just temporary after find the right position just delete everything
    :param topJnt: str, top joint of chain to get pv position (e.g hip/shoulder)
    :param midJnt: str, mid joint of chain to get pv position (e.g knee/elbow)
    :param endJnt: str, end join of the chain to get pv position (e.g foot/hand)
    :param prefix: str, prefix to name new objects
    :return dictionary, with all the nodes to be deleted after the position is found
    """
    
    allNodes = []
    
    # create decompose matrix to get world position for each joint
    worldPosMatrix = []
    for jnt in [ topJnt, midJnt, endJnt ]:
        
        prefix = name.removeSuffix( jnt )
        
        dcMatrix = mc.createNode('decomposeMatrix', n =  prefix  + '_dcm')
        mc.connectAttr( jnt + '.worldMatrix', dcMatrix + '.inputMatrix' )
        worldPosMatrix.append( dcMatrix )
        
        allNodes.append( dcMatrix )
        
    
    # create startEnd and startMid vectors
    
    # start mid vector
    startMidVector = mc.createNode( 'plusMinusAverage', n = prefix + 'StartMidVector_pma' )
    mc.setAttr( startMidVector + '.operation', 2 ) # subtract operation
    
    mc.connectAttr( worldPosMatrix[1] + '.outputTranslate', startMidVector + '.input3D[0]' )
    mc.connectAttr( worldPosMatrix[0] + '.outputTranslate', startMidVector + '.input3D[1]' )
    
    allNodes.append( startMidVector )
    
    # start end vector
    startEndVector = mc.createNode( 'plusMinusAverage', n = prefix + 'StartEndVector_pma' )
    mc.setAttr( startEndVector + '.operation', 2 ) # subtract operation
    
    mc.connectAttr( worldPosMatrix[2] + '.outputTranslate', startEndVector + '.input3D[0]' )
    mc.connectAttr( worldPosMatrix[0] + '.outputTranslate', startEndVector + '.input3D[1]' )
    
    allNodes.append( startEndVector )
    
    # make projection from startMid to startEnd vector to find closest point from startEnd
    # length to mid vector
    
    # dot product
    projVector = mc.createNode( 'vectorProduct', n = prefix + 'ProjVector_vcp' )
    mc.connectAttr( startEndVector + '.output3D', projVector + '.input1' )
    mc.connectAttr( startMidVector + '.output3D', projVector + '.input2' )
    
    allNodes.append( projVector )
    
    # startend length
    startEndVectorLen = mc.createNode( 'vectorProduct', n = prefix + 'StartEndVectorLen_vcp' )
    mc.connectAttr( startEndVector + '.output3D', startEndVectorLen + '.input1' )
    mc.connectAttr( startEndVector + '.output3D', startEndVectorLen + '.input2' )
    
    allNodes.append( startEndVectorLen )
    
    # get the scalar value of projected vector
    projScalar = mc.createNode( 'multiplyDivide', n = prefix + 'ProjectedScalar_mdv' )
    mc.setAttr( projScalar + '.operation', 2 ) # divide operation
    mc.connectAttr( projVector + '.output', projScalar + '.input1' )
    mc.connectAttr( startEndVectorLen + '.output', projScalar + '.input2' )
    
    allNodes.append( projScalar )
    
    # multiply the startEndVector by the scalar value to get closest point to mid position
    startEndClosestPoint = mc.createNode( 'multiplyDivide', n = prefix + 'StartEndClosestPoint_mdv' )
    mc.connectAttr( startEndVector + '.output3D', startEndClosestPoint + '.input1' )
    mc.connectAttr( projScalar + '.output', startEndClosestPoint + '.input2' )
    
    allNodes.append( startEndClosestPoint )

    # move the startEnd closest point vector to right position
    closestPointVector = mc.createNode( 'plusMinusAverage', n = prefix + 'ClosestPointVector_pma' )
    mc.connectAttr( startEndClosestPoint + '.output', closestPointVector + '.input3D[0]' )
    mc.connectAttr( worldPosMatrix[0] + '.outputTranslate', closestPointVector + '.input3D[1]' )
    
    allNodes.append( closestPointVector )
    
    # create pole vector 
    initialPoleVector = mc.createNode( 'plusMinusAverage', n = prefix + 'InitialPoleVector_pma' )
    mc.setAttr( initialPoleVector + '.operation', 2 ) # subtract operation
    
    mc.connectAttr( worldPosMatrix[1] + '.outputTranslate', initialPoleVector + '.input3D[0]' )
    mc.connectAttr( closestPointVector + '.output3D', initialPoleVector + '.input3D[1]' )
    
    allNodes.append( initialPoleVector )
    
    # normalize pole vector
    normalizedPoleVector = mc.createNode( 'vectorProduct', n = prefix + 'NormalizedPoleVector_vcp' )
    mc.setAttr( normalizedPoleVector + '.operation', 0 ) # no operation
    mc.setAttr( normalizedPoleVector + '.normalizeOutput', 1 ) 
    mc.connectAttr( initialPoleVector + '.output3D', normalizedPoleVector + '.input1' )
    
    allNodes.append( normalizedPoleVector )
    
    # get total distance to extend the pole vector length
    totalLengthDis = _getTotalLength( topJnt, midJnt, endJnt, prefix )
    
    allNodes.extend( totalLengthDis )
    
    # extend pole vector length
    poleVectorExtended = mc.createNode( 'multiplyDivide', n = prefix + 'poleVectorExtended_mdv' )
    mc.connectAttr( normalizedPoleVector + '.output', poleVectorExtended + '.input1' )
    for ax in ['X', 'Y', 'Z']:
        
        mc.connectAttr( totalLengthDis[0] + '.output', poleVectorExtended + '.input2{}'.format( ax ) )
    
    # move the extended pole vector to right posisiton
    poleVector = mc.createNode( 'plusMinusAverage', n = prefix + 'poleVector_pma' )
    mc.connectAttr( poleVectorExtended + '.output', poleVector + '.input3D[0]' )
    mc.connectAttr( worldPosMatrix[1] + '.outputTranslate', poleVector + '.input3D[1]' )
    
    allNodes.append( poleVector ) 
    
    # create reference locator
    refLoc = mc.spaceLocator( n = prefix + 'PoleVector_loc' )[0]
    mc.connectAttr( poleVector + '.output3D', refLoc + '.translate'  )
    
    for ax in ['X', 'Y', 'Z']:
        mc.setAttr( refLoc + '.localScale{}'.format( ax ), 15 )
    
    allNodes.append( refLoc )
    
    return allNodes
    
def _getTotalLength( topJnt, midJnt, endJnt, prefix ):
        
        # start mid distance
        startMidDis = mc.createNode( 'distanceBetween', n = prefix + 'StartMid_dis' )
        mc.connectAttr( topJnt + '.worldMatrix[0]', startMidDis + '.inMatrix1' )
        mc.connectAttr( midJnt + '.worldMatrix[0]', startMidDis + '.inMatrix2' )
    
        # mid end distance
        midEndDis = mc.createNode( 'distanceBetween', n = prefix + 'MidEnd_dis' )
        mc.connectAttr( midJnt + '.worldMatrix[0]', midEndDis + '.inMatrix1' )
        mc.connectAttr( endJnt + '.worldMatrix[0]', midEndDis + '.inMatrix2' )
        
        # total distance
        totalDis = mc.createNode( 'addDoubleLinear', n = prefix + 'TotalLength_adl' )
        mc.connectAttr( startMidDis + '.distance', totalDis + '.input1' )
        mc.connectAttr( midEndDis + '.distance', totalDis + '.input2' )
        
        return [totalDis, startMidDis, midEndDis]
        
    
    
    
    