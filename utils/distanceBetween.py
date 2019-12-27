'''
functions for working with distanceBetween nodes 
@category Rigging @subcategory Utils
'''

import maya.cmds as mc

def buildAndConnect( objectA, objectB, prefix = 'distanceMeter' ):
    
    """
    build distance node and connect it with 2 given transforms
    
    @param objectA: str, first transfom
    @param objectB: str, second transfom
    @param prefix: str, prefix to name new node
    @return: str, name of new distance node
    """
    
    dbNode = mc.createNode( 'distanceBetween', n = prefix + '_dbn' )
    
    # connect matrix
    
    mc.connectAttr( objectA + '.worldMatrix', dbNode + '.inMatrix1' )
    mc.connectAttr( objectB + '.worldMatrix', dbNode + '.inMatrix2' )
    
    # connect points
    # in case both objects are cluster handles
    
    clusterShapesA = mc.listRelatives( objectA, c = 1, type = 'clusterHandle' )
    clusterShapesB = mc.listRelatives( objectB, c = 1, type = 'clusterHandle' )
    
    if clusterShapesA and clusterShapesB:
        
        mc.connectAttr( objectA + '.center', dbNode + '.point1' )
        mc.connectAttr( objectB + '.center', dbNode + '.point2' )
    
    
    
    return dbNode
    
