'''
matrix 
:category Rigging @subcategory Utils
:tags matrix wtAddMatrix blend
'''

import maya.cmds as mc


def makeBlendMatrices( transforms, prefix = 'mxblend' ):
    
    matrixBlend = mc.createNode( 'wtAddMatrix', n= prefix + '_wam' )
    
    for i,t in enumerate( transforms ):
        
        mc.connectAttr( t + '.wm', matrixBlend + '.wtMatrix[' + str(i) + '].m' )
        mc.setAttr( matrixBlend + '.wtMatrix[' + str(i) + '].w', 1.0 )
    
    return matrixBlend
    
    
    
    
