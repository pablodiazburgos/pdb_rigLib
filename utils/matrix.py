'''
matrix 
:category Rigging @subcategory Utils
:tags matrix wtAddMatrix blend
'''

import maya.cmds as mc
import pymel.core as pm

from . import name

def makeBlendMatrices( transforms, prefix = 'mxblend' ):
    
    matrixBlend = mc.createNode( 'wtAddMatrix', n= prefix + '_wam' )
    
    for i,t in enumerate( transforms ):
        
        mc.connectAttr( t + '.wm', matrixBlend + '.wtMatrix[' + str(i) + '].m' )
        mc.setAttr( matrixBlend + '.wtMatrix[' + str(i) + '].w', 1.0 )
    
    return matrixBlend
    
def matrixParentConstraint( target, object, mo = False, connectTranslate = True, connectRotate = True, connectScale = False ):
    """
    Creates a parent constraint based on matrices
    :param target, pynode, constriant target node
    :object object
    """
    # create prefix for new nodes
    tgtPrefix =  name.getBase( target.name() )
    objPrefix =  name.getBase( object.name() )
    
    # convert objects to pymel objects for easier matrix stuffs
    
    prefix = tgtPrefix + objPrefix
    
    # create multi matrix and decompose matrix
    multiMatrix = pm.createNode( 'multMatrix', n = prefix + '_mmx' )
    decomMatrix = pm.createNode( 'decomposeMatrix', n = prefix + '_dcm' )
    
    # create default connections
    multiMatrix.matrixSum.connect( decomMatrix.inputMatrix, force = True )
    
    # make connections
    if mo:
        localOffsetMatrix = object.getMatrix( worldSpace = True ) * target.getMatrix( worldSpace = True ).inverse()
        
        multiMatrix.matrixIn[0].set( localOffsetMatrix )
        target.worldMatrix[0].connect(  multiMatrix.matrixIn[1] )     
        object.parentInverseMatrix[0].connect( multiMatrix.matrixIn[2] )
        
    else:
        
        target.worldMatrix[0].connect(  multiMatrix.matrixIn[0] )     
        object.parentInverseMatrix[0].connect( multiMatrix.matrixIn[1] )
    
    
    if connectTranslate:
        decomMatrix.outputTranslate.connect( object.translate )
        
    if connectRotate:
        decomMatrix.outputRotate.connect( object.rotate )

    if connectScale:
        decomMatrix.outputScale.connect( object.scale )
        
    return {
            'decomMatrix':decomMatrix,
            'multMatrix':multiMatrix
            }
