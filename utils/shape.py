"""
module to work with shape functions
:author: Pablo Diaz Burgos
"""

import maya.cmds as mc

from . import name

def getShape( object, useLongName = False, noIntermediate = True, shapeTypes = [] ):
    """
    function to get the shape of the given object, if shape passed return it
    :param object: str, object to get the shapes from
    :param useLongName: bool, if true, function will return long shape name (shapes are more prone to clashing names)
    :param shapeTypes: list ( str ) types of shapes, if list is empty then all shapes will be returned
    :return list of shapes if found shapes 
    """
    
    # return object if it is a shape type
    
    objecttype = mc.nodeType( object )
    returnname = object
    returnnameLong = mc.ls( object, l = 1 )[0]
    
    if 'shape' in mc.nodeType( object, inherited = 1 ):
        
        if useLongName: return [returnnameLong]
        else: return [returnname]
    
    # return object shape if it was not shape itself
    
    if not shapeTypes:
        
        shapesfoundLong = mc.listRelatives( object, s = 1, f = 1, noIntermediate = noIntermediate )
    
    else:
        
        shapesfoundLong = mc.listRelatives( object, s = 1, f = 1, noIntermediate = noIntermediate, type = shapeTypes )
    
    if not shapesfoundLong: return []
    
    # get shape short names
    
    shapesfound = [ s.split( '|' )[-1] for s in shapesfoundLong ]
    
    
    if useLongName: return shapesfoundLong
    else: return shapesfound
    
def getComponentAttribute( objShape ):
    """
    return component attribute, for example 'cv' for nurbsCurve or 'vtx' for mesh
    :param objShape: str, object or object shape to get the component attributes
    :return str, name of the component
    """
    
    componentMaskDir = { 'mesh':'vtx', 'nurbsCurve':'cv', 'nurbsSurface':'cv', 'lattice':'pt' }
    
    shapeNode = getShape( objShape )[0]
    shapeType = mc.nodeType( shapeNode )
    
    if not shapeType in componentMaskDir.keys(): raise Exception( 'node type not supported' )
    
    compMask = componentMaskDir[ shapeType ]
    
    return compMask

def scale(object = '', scale = [1, 1, 1], local = True ):
    """
    object to scale the shape component along its local axis or 0 world position
    :param object: str, object to scale shape components
    :param: scale: list[ floatX, floatY, floatZ ], float values to scale per axis
    :param: local: str, define if will be scale from local pivot center of the world
    :return None
    """
    
    componentAt = getComponentAttribute( object )
    objShape = getShape(object)[0]
    componentList = '%s*.%s[*]' % (objShape[:-1], componentAt)
    
    pivotPos = [0, 0, 0]
    xformObj = object
    
    if not 'transform' in mc.nodeType(object):
        xformObj = mc.listRelatives( object, p = True )[0]
        
    if local: pivotPos = mc.xform( xformObj, q = True, t = True, ws = True )
    
    mc.scaleComponents( scale[0], scale[1], scale[2], componentList, pivot = pivotPos )

def fixShapesNameOld(obj = None):
    
    if obj:
        shapes = getShape( obj )
        for shp in shapes:
    
            parent = mc.listRelatives( shp, p = True )[0]
            name = parent + 'Shape'
            if shp != name:
                mc.rename( shp, name )
            
    else:
        # fix shape names
        import pymel.core as pm
        for shape in pm.ls(type='shape'):
            
            parent = shape.getParent()
            name = parent+'Shape'
            
            if shape.name() != name:
                print shape
                shape.rename(name)

def fixShapesName(shapeTransform):
    """
    fix shape names of a given transform object bcs Maya often doesn't name properly shape names
    
    :param shapeTransform: str, name of the transform object to rename shapes
    :return list (str), list of string with renamed shapes
    """
    
    shapesFound = mc.listRelatives( shapeTransform, s = True, f = True )
    if not shapesFound: return[]
    
    # rename to a temp name in case the prefix is already in use on some shapes
    temporalName = 'fixShapeNameTemporaryName#'
    for s in shapesFound: mc.rename( s, temporalName )
    
    # list again all the shapes with the temporary names
    shapesFound = mc.listRelatives( shapeTransform, s = True, f = True )
    
    newShapeNames = []
    
    # rename shapes same way as Maya does it 
    for i, s in enumerate( shapesFound ):
        
        shapeTransformShort = name.short( shapeTransform )
        fixedName = shapeTransformShort + 'Shape'
        if i > 0: fixedName = shapeTransformShort + 'Shape' + str (i)
        renamed = mc.rename( s, fixedName )
        newShapeNames.append( renamed )

    return newShapeNames
        
def translateRotate( shapeTransform, pos = [0, 0, 0], rot = [0, 0, 0], localSpace = False, relative = True, deleteHistory = True ):
    
    '''
    translate and rotate shape object components
    
    LIMITATION - currently only works with curves CVs
    
    :param shapeTransform: str, object transform with shape
    :param translate: list( floatX, floatY, floatZ ), translate values to move the shape
    :param rotate:list( floatX, floatY, floatZ ), rotate values to move the shape
    :param localSpace: bool, use local space of shape transform
    :param relative: bool, use relative translation and rotation
    :param deleteHistory: bool, delete history on shape as this function uses cluster
    :return: None or if deleteHistory is False return list with cluster node and xform
    '''
    
    compmask = getComponentAttribute( shapeTransform )
    objShapes = getShape(object = shapeTransform)
    allCvs = getAllComponentsList( objShapes, compmask )
    
    if localSpace:
        
        prefix = name.removeSuffix( shapeTransform ) + 'LocalShapeTransform'
        localOffsetGrp = mc.group( n = prefix + 'Offset_grp', em = 1, p = shapeTransform )
        localTransformGrp = mc.group( n = prefix + '_grp', em = 1, p = localOffsetGrp )
        mc.parent( localOffsetGrp, w = 1 )
        
        
        clDef, clXform = mc.cluster( allCvs, n = shapeTransform + 'Temp_cls', wn = [localTransformGrp, localTransformGrp], bs = True )
        mc.move( pos[0], pos[1], pos[2], localTransformGrp, r = relative, os = True )
        mc.rotate( rot[0], rot[1], rot[2], localTransformGrp, r = relative, os = True )
    
    else:
        
        clDef, clXform = mc.cluster( allCvs, n = shapeTransform + 'Temp_cls' )
        mc.move( pos[0], pos[1], pos[2], clXform, r = relative )
        mc.rotate( rot[0], rot[1], rot[2], clXform, r = relative )
    
    
    if deleteHistory:
        
        mc.delete( shapeTransform, ch = 1 )
    
    else:
        
        return [ clDef, clXform ]
    
def centerPointsToObjects( shapes, objects, deleteHistory = True ):
    
    '''
    Center shape points (CVs, verts etc..) between given number of objects, one to many
    
    :param shapes: list(str), shape objects (meshes etc.)
    :param objects: list(str), transforms as targets for centering
    :param deleteHistory: bool, delete history after applying cluster to offset points
    :return: None
    '''
    
    # filter shapes from transforms
    shapesFiltered = []
    for s in shapes:
        
        if mc.nodeType( s ) == 'transform':
            
            objShapes = getShape( s, useLongName = True )
            shapesFiltered.extend( objShapes )
        
        else:
            
            shapesFiltered.append( s )
            
    
    clDef, clXform = mc.cluster( shapesFiltered, n = shapes[0] + '_centerPoints_cls' )
    mc.delete( mc.pointConstraint( objects, clXform ) )
    
    if deleteHistory:
        
        mc.delete( shapesFiltered, ch = 1 )
    
    else:
        
        return [ clDef, clXform ]
    
def getType( object ):
    
    '''
    get shape type of provided object. In case transform was provided, get the type for its first shape
    
    :param object: str, object which can be transform or shape to get its shape type from
    :return: str, name of shape type, if no shape found, return None 
    '''
    
    shapes = getShape( object, useLongName = True )
    if not shapes: return None
    
    shapetype = mc.nodeType( shapes[0] )
    
    return shapetype

def getAllComponentsList( objShapes, compmask ):
    
    '''
    List all the cvs for provided shapes and return a list
    
    :param objShapes: list ( str ), list of shapes to look their components
    :param compmask: str, filter mask to list components
    :return list(str), all the components found in a flatten list 
    '''
    compList = []
    for shape in objShapes:
        components = mc.ls('%s.%s[*]' % (shape, compmask), fl = True )
        compList = list(set(compList + components))
        
    return compList    
    