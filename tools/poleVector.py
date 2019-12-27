"""
functions to work with pole vector
"""

import math
import maya.cmds as mc
import maya.OpenMaya as om

from ..utils import vector

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