
'''
hair module 
@category Rigging @subcategory Utils
@tags hair hairSystem follicle rivet hair mesh nurbs info parameter uv dynamic
'''


import maya.cmds as mc
import maya.mel as mm


from . import shape
from . import name
from . import transform
from . import surface
from . import mesh
from . import connect



def makeFollicleOnSurface( surface = '', prefix = 'new', uvCoordinates = [0, 0], useCustomParent = False, customParent = None ):
    
    '''
    @param surface: str, mesh or nurbsSurface
    @param prefix: str, prefix of follicle
    @param uvCoordinates: list(float), 2 values for UV attachment of follicle
    @param useCustomParent: bool, use custom parent for follice shape, useful to re-use existing transforms
    @param customParent: str, name of custom parent transform for follicle
    @return: list(str), names with new objects: 0- follicle transform, 1- follicle shape
    '''
    
    shapetype = shape.getType( surface )
    supportedShapes = ['mesh', 'nurbsSurface']
    
    if not shapetype in supportedShapes:
        
        raise Exception( '# %s type from object %s does not match any of %s' % ( shapetype, surface, supportedShapes ) )
    
    folic = mc.createNode( 'follicle', n = prefix + '_folShape' )
    folicTrans = mc.listRelatives( folic, p = 1 )[0]
    folicParent = folicTrans
    
    if useCustomParent:
        
        mc.parent( folic, customParent, relative = True, shape = True )
        mc.delete( folicTrans )
        folicParent = customParent
    
    #===========================================================================
    # connect surface to follicle node
    #===========================================================================
    
    mc.connectAttr( surface + '.worldMatrix', folic + '.inputWorldMatrix' )
    
    if shapetype == 'nurbsSurface':
        
        geoOutputPlug = surface + '.local'
        mc.connectAttr( geoOutputPlug, folic + '.inputSurface' )
    
    if shapetype == 'mesh':
        
        geoOutputPlug = surface + '.outMesh'
        mc.connectAttr( geoOutputPlug, folic + '.inputMesh' )
    
    
    #===========================================================================
    # set parameter values and connect result to follicle transform
    #===========================================================================
    
    mc.setAttr( folic + '.parameterU', uvCoordinates[0] )
    mc.setAttr( folic + '.parameterV', uvCoordinates[1] )
    
    mc.connectAttr( folic + '.outTranslate', folicParent + '.t' )
    mc.connectAttr( folic + '.outRotate', folicParent + '.r' )
    
    
    return [ folicParent, folic ]