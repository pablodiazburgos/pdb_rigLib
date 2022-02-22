'''
rivet
@category Rigging @subcategory Utils
@tags rivet button

functions for making rivet setup on meshes and nurbs
'''

import maya.cmds as mc

from utils import name
from utils import shape
from utils import surface
from utils import mesh
from utils import hair
from utils import transform



def rivetObjectsToGeometry( objectList, attachGeometry, prefix = '', rivetsParentGrp = 'rivetParent_grp', useObjectsAsRivets = False, parentRivets = True ):
    
    '''
    make rivets on given geometry (mesh or nurbsSurface) for list of transform objects
    - by default make locators as rivets and parentConstraint provided objects to them
    - there is also option useObjectsAsRivets to directly connect translate/rotate of provided objects, which can save performance as well
        but these objects will be moved and rotated
    
    :param objectList: list(str), list of transform objects to be attached
    :param attachGeometry: str, name of geometry that will hold the rivets
    :param prefix: str, prefix for naming new objects
    :param rivetsParentGrp: optional, str, parent group to keep rivet locators (the group will not be made if parentRivets is False)
    :param useObjectsAsRivets: bool, use provided objects in objectList to be riveted (their translate/rotate will change), otherwise make locators
    :param parentRivets: parent rivet objects (locators or from object list) under rivet group
    :return: list(str), list of rivet locators
    '''
    
    # make prefix
    
    if not prefix:
        
        prefix = name.removeSuffix( attachGeometry ) + 'Rivet'
    
    # make rivet parent group
    
    if not mc.objExists( rivetsParentGrp ) and parentRivets:
        
        rivetsParentGrp = mc.group( n = rivetsParentGrp, em = 1 )
    
    # create rivets
    
    attachShape = shape.getShape( attachGeometry )[0]
    geometryType = mc.nodeType( attachShape )
    rivetLocs = []
    
    for i, obj in enumerate( objectList ):
        
        # make rivet locator
        
        objPrefix = prefix + str( i + 1 )
        rivetObject = None
        
        if useObjectsAsRivets:
            
            rivetObject = obj
        
        else:
            
            rivetObject = mc.spaceLocator( n = prefix + '_' + objPrefix + '_loc' )[0]
            mc.delete( mc.parentConstraint( obj, rivetObject ) )

        rivetLocs.append( rivetObject )

        if parentRivets:
            
            rivetObjectParent = mc.listRelatives( rivetObject, p = 1 )
            doParentRivetObject = False
            
            if not rivetObjectParent: doParentRivetObject = True
            if rivetObjectParent and not rivetObjectParent[0] == rivetsParentGrp: doParentRivetObject = True
            if doParentRivetObject: rivetObject = mc.parent( rivetObject, rivetsParentGrp )[0]
        
        
        # make rivet
        
        objprefix = name.removeSuffix( obj )
        
        if geometryType == 'nurbsSurface':
            
            closestParamsOnSurf = surface.getClosestPointOnSurface( rivetObject, attachGeometry )[0]
            attachToSurface( rivetObject, surfaceObj = attachShape, prefix = objPrefix, params = closestParamsOnSurf )
            
        if geometryType == 'mesh':
            
            edgeIdxs = mesh.getClosestEdgePair( attachShape, refTransform = obj )
            edges = [ '%s.e[%d]' % ( attachShape, idx ) for idx in edgeIdxs ]
            res = classicrivet_mesh( edges, shapeobj = attachShape, object = rivetObject, prefix = objPrefix )
        
        # attach object to rivet
        
        if not useObjectsAsRivets:
            
            mc.parentConstraint( rivetObject, obj, mo = 1 )
    
    
    return [ rivetLocs, rivetsParentGrp ]

def attachToSurface( object, surfaceObj, prefix = '', params = [0.5, 0.5] ):
    
    '''
    function used by rivet to attach object to nurbsSurface
    
    :param object: str,name of transform object to be attached
    :param surfaceplug: str, name of nurbs shape output plug (this can be loft node or anything with NURBS data output)
    :param prefix: str, prefix for naming new objects
    :param params: list( float, float ), list with UV parameters to position object on surface
    :param usePercentage: bool, flag for using percentage for parameters on pointOnSurfaceInfo
    :return: list(str), list of objects names from attachment setup (pointOnSurfaceInfo node, aimConstraint node, pointConstraint node)
    '''
    
    # edit prefix
    
    if not prefix: prefix = name.removeSuffix( object ) + 'AttachToNurbs'
    
    # create surface follicle
    
    follicleXform, follicle = hair.makeFollicleOnSurface( 
                                                    surface = surfaceObj,
                                                    prefix = prefix,
                                                    uvCoordinates = params,
                                                    useCustomParent = True,
                                                    customParent = object
                                                    )
    
    return [ follicleXform, follicle ]


def classicrivet_mesh( edges, shapeobj, object, prefix ):
    
    '''
    make classic rivet using surface from 2 edges
    
    NOTE:
    - function returns list with first item being list of shape input plugs
      shape input plugs can be used to be later reconnected to something else to prevent cycle
    
    
    :param edges: list( str ), 2 edges, e.g. ['pSphere1.e[237]', 'pSphere1.e[257]']
    :param object: str, name of object to be attached to rivet transform output
    :param prefix: str, name added to every new object
    :return: list( list(str), str, str, str ), ( (shapeinput1,shapeinput4), aimConstraint, pointOnSurfaceInfo, pointConstraint )
    '''
    
    #===========================================================================
    # create nurbs loft between edges
    #===========================================================================
    
    edges = mc.ls( edges, fl = 1 )
    namePOSI = ''
    
    # get edge indeces
    
    e1 = edges[0].split( '.e' )[1]
    e1 = e1.replace( '[', '' )
    e1 = e1.replace( ']', '' )
    e1 = float( e1 )
    
    e2 = edges[1].split( '.e' )[1]
    e2 = e2.replace( '[', '' )
    e2 = e2.replace( ']', '' )
    e2 = float( e2 )
    
    # create curves from edge
    
    nameCFME1 = mc.createNode( 'curveFromMeshEdge', n = prefix + 'A_cme' )
    mc.setAttr( nameCFME1 + '.ihi', 1 )
    mc.setAttr( nameCFME1 + '.ei[0]', e1 )
    
    nameCFME2 = mc.createNode( 'curveFromMeshEdge', n = prefix + 'B_cme' )
    mc.setAttr( nameCFME2 + '.ihi', 1 )
    mc.setAttr( nameCFME2 + '.ei[0]', e2 )
    
    # create loft
    
    nameLoft = mc.createNode( 'loft', n = prefix + 'Loft_lft' )    
    mc.setAttr( nameLoft + '.ic', s = 2 )
    mc.setAttr( nameLoft + '.u', 1 )
    mc.setAttr( nameLoft + '.rsn', 1 )
    mc.setAttr( nameLoft + '.autoReverse', False )
    
    # make connections
    
    mc.connectAttr( nameCFME1 + '.oc', nameLoft + '.ic[0]' )
    mc.connectAttr( nameCFME2 + '.oc', nameLoft + '.ic[1]' )
    mc.connectAttr( shapeobj + '.w', nameCFME1 + '.im' )
    mc.connectAttr( shapeobj + '.w', nameCFME2 + '.im' )
    
    # make nurbs shape
    
    nurbsobj = mc.createNode( 'nurbsSurface' )
    nurbsxform = mc.listRelatives( nurbsobj, p = 1 )[0]
    nurbsxform = mc.rename( nurbsxform, prefix + 'Loft_sur' )
    nurbsobj = mc.listRelatives( nurbsxform, s = 1 )[0]
    mc.hide( nurbsxform )
    objectparent = mc.listRelatives( object, p = 1 )
    
    if objectparent:
        
        mc.parent( nurbsxform, objectparent[0] )
    
    mc.connectAttr( nameLoft + '.outputSurface', nurbsobj + '.create' )
    
    # check and fix loft curve direction
    # compare perimeter of loft after reversing one curve
    origPerimLen = _measureLoftPerimeter( nurbsxform )
    
    reverseCurveNode = mc.createNode( 'reverseCurve', n = prefix + 'Loft_rvc' )
    mc.connectAttr( nameCFME1 + '.oc', reverseCurveNode + '.inputCurve' )
    mc.connectAttr( reverseCurveNode + '.outputCurve', nameLoft + '.ic[0]', f = True )
    reversedPerimLen = _measureLoftPerimeter( nurbsxform )
    
    if origPerimLen < reversedPerimLen:
        
        mc.connectAttr( nameCFME1 + '.oc', nameLoft + '.ic[0]', f = True )
        mc.delete( reverseCurveNode )
    
    #===========================================================================
    # attach object transform to surface
    #===========================================================================
    
    attachres = attachToSurface( object, surfaceObj = nurbsobj, prefix = prefix, params = [0.5, 0.5] )
    
    
    # add shape inputs list to return
    
    shapeinputs = [ [ nameCFME1 + '.im', nameCFME2 + '.im' ] ]
    
    
    results = shapeinputs + attachres
    
    
    return results

def _measureLoftPerimeter( loftSurface ):
    
    pos1 = mc.xform( loftSurface + '.cv[0][0]', q = 1, t = 1, ws = 1 )
    pos2 = mc.xform( loftSurface + '.cv[0][3]', q = 1, t = 1, ws = 1 )
    pos3 = mc.xform( loftSurface + '.cv[1][3]', q = 1, t = 1, ws = 1 )
    pos4 = mc.xform( loftSurface + '.cv[1][0]', q = 1, t = 1, ws = 1 )
    
    perimLength = transform.measureDistanceBetweenMultiplePositions( [pos1, pos2, pos3, pos4] )
    
    return perimLength
        