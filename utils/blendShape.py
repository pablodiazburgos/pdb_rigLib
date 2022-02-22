'''
module to work with blendshapes at pdb_rigLib.utils
@category Rigging
'''
#TODO: finish  invertTargetVtxWeights module

import maya.cmds as mc
import maya.OpenMaya as om

import name

def invertTargetVtxWeights( baseGeo, sourceBls, targetBls, blsNode = None ):
    
    '''
    Function to invert target blendshape weights, helps to extract micro blendshapes from macro blendshapes
    :param baseGeo: str, driven geo which is being affected by the blendshape node
    :param sourceBls: str, name of source blendshape to get weights from to invert
    :param targetBls: str, name of target blendshape to set inverted weights
    :param blsNode: str, (optional) name of the blendshape node , if nothing passed script would try to get it automatic
    '''
    
    # get blendShape node in case is not provided
    if not blsNode:
        
        blsNodes = getBlendShapeNodes( baseGeo )
        
        if len( blsNodes ) > 1 :
            om.MGlobal_displayError( "# Multiple blendshapes nodes connected to {}, please specify which one you wanna use ".format( baseGeo ) )
        
        elif not blsNodes:
            om.MGlobal_displayError( "# No blendshapes nodes found connected to {}".format( baseGeo ) )
        else:
            blsNode = blsNodes[0]
            
    #===========================================================================
    # check if source and target shapes exists
    #===========================================================================
    targetAliasNames = getTargetNames( blsNode )
    if not sourceBls in targetAliasNames: om.MGlobal_displayError( "# '{}' not found in blendShape Node '{}'".format( sourceBls, blsNode ) )
    if not targetBls in targetAliasNames: om.MGlobal_displayError( "# '{}' not found in blendShape Node '{}'".format( targetBls, blsNode ) )   
    
def getBlendShapeNodes( deformedGeo ):
    
    '''
    function to get blendshape nodes connected to provided object
    :param deformedGeo: str, deformed object by blendshape to look in
    :return list(str), list of blendShape nodes found connected to provided object
    '''
    
    hist = mc.listHistory( deformedGeo )
    blendShapesNodes = mc.ls( hist, type = 'blendShape' )
    
    return blendShapesNodes
    
def getBlendShapeTargetIndeces( blsNode ):
    
    '''
    Get list of target indices from provided blendShape node
    
    :param blsNode: str, source blendShape
    :return list(str), list of target indices
    '''
    
    targetIndeces = mc.getAttr( blsNode + '.weight', mi = 1 )
    
    return targetIndeces

def getTargetVtxWeights( targetBls, blendShapeNode ):
    pass

def getTargetNames( blsNode ):
    
    '''
    query aliases of target weight attributes
    
    :param bsnode: str, source blendShape
    :return: list(str), list of target names
    '''
    
    weightIndeces = getBlendShapeTargetIndeces( blsNode )
    
    aliasNames = [ mc.aliasAttr( '%s.weight[%d]' % ( blsNode, i ), q = 1 ) for i in weightIndeces ]
    
    return aliasNames

def getGeoFromBlendShape( blsNode ):
    
    '''
    get geometry transform object deformed by provided blendShape node
    
    :param bsNode: str, name of blendShape node
    :return: str, name of geometry transform which has shape deformed by this blendShape, if nothing found returns None
    '''
    
    his = mc.listHistory( blsNode, f = 1 )
    shapeTypes = ['mesh', 'nurbsSurface', 'nurbsCurve', 'lattice']
    geoObject = None
    
    for h in his:
        
        if mc.nodeType( h ) in shapeTypes:
            
            geoObject = h
            break
        
    return geoObject

def extractAllShapesFromNode( blsNode, suffix = '_bls', parentGroup = None ):
    
    '''
    extract all the shapes from given blendshape with value 1.0 by default
    and parent new shpes under new group
    :param blsNode: str, blendShape node
    :param suffix: str, suffix to rename extracted shapes
    :param parentGroup: str, if parent group is provided, new shapes will be parented under it, otherwise new group is made
    :return: list(str), index 0 - name of new shapes group, indeces 1-n - names of generated shape objects
    '''
    
    # get base information to work with
    meshToDuplicate = getGeoFromBlendShape( blsNode )
    targetIndices = getBlendShapeTargetIndeces( blsNode )
    targetNames = getTargetNames( blsNode )
    
    # create parent group in case it doesnt exists 
    parentGroupName = 'extractedBls_grp'
    if not parentGroup and not mc.objExists( parentGroupName ):
        parentGroup = mc.group( em = True, n = parentGroupName, w = True )
        
    # make a loop to duplicate and parent each target shape
    
    duplicatedObjectList = []
    for idx, obj in enumerate( targetNames ):
        # if suffix is already "_bls" just use current name
        retSuffix = name.getSuffix( obj )
        if retSuffix == 'bls':
            suffix = ''
        originalVal = mc.getAttr( '%s.%s' % ( blsNode, targetNames[idx] ) )# get original value
        mc.setAttr( '%s.%s' % ( blsNode, targetNames[idx] ), 1 )
        duplicatedGeo = mc.duplicate( meshToDuplicate, n = obj + suffix )
        mc.parent( duplicatedGeo, parentGroup )
        duplicatedObjectList.append( duplicatedGeo )
        mc.setAttr( '%s.%s' % ( blsNode, targetNames[idx] ), originalVal ) # set to originalVal
        
    return [ parentGroup, duplicatedObjectList ] 
    
def addTarget( blsNode, targetGeos, baseGeo = None, defVal = 0.0 ):
    
    '''
    add new targets to existing blendShape node
    :param blsNode: str, blendShape node name
    :param targetGeos: list( str ), list of target geos to add in
    :param baseGeo: str, optional, destination geometry for adding targets (if not provided script will try to find it)
    :param defVal: float, default value for target shape 
    :return None
    '''
    if not baseGeo:
        baseGeo = getGeoFromBlendShape( blsNode )           
    
    
    bsindeces = getBlendShapeTargetIndeces( blsNode )
    if bsindeces: lastindex = bsindeces[-1]
    else: lastindex = 0
    
    startidx = lastindex + 1
    upperidxrange = startidx + len( targetGeos )
    newindeces = range( startidx, upperidxrange )
    
    for idx, targetGeo in zip( newindeces, targetGeos ):
        
        mc.blendShape( blsNode, e = 1, target = ( baseGeo, idx, targetGeo, 1.0 ) )
        mc.setAttr( '%s.weight[%d]' % ( blsNode, idx ), defVal )

def makeBlendShapeCombo( blsNode, targetA, targetB, comboBls ):
    
    '''
    create combo for 2 targets triggering a 3rd one... useful for correctives blendshapes
    :param blsNode: str, BlendShape node name
    :param targetA: str, First target blendshape which actives the combo one
    :param targetB: str, Second target blendshape which actives the combo one
    :param comboBls: str, Combo blendshape (usually a corrective)
    :return list( str, str), MultiDoubleLinear - ConditionNode
    '''
    
    # get combo prefix to rename new objects
    comboPrefix = name.removeSuffix( comboBls )
    
    multNode = mc.createNode('multDoubleLinear', n = comboPrefix + '_mdl')
    
    # create condition to prevent corrective go above one 
    conNode = mc.createNode('condition', n = comboPrefix + '_con')
    mc.setAttr( conNode + '.operation', 3 ) # greater or equal
    mc.setAttr( conNode + '.secondTerm', 1.0 )
    mc.setAttr( conNode + '.colorIfTrueR', 1.0 )
    
    # make connections
    
    mc.connectAttr( blsNode + '.' + targetA, multNode + '.input1' )
    mc.connectAttr( blsNode + '.' + targetB, multNode + '.input2' )
    
    mc.connectAttr( multNode + '.output', conNode + '.firstTerm' )
    mc.connectAttr( multNode + '.output', conNode + '.colorIfFalseR' )
    
    
    mc.connectAttr( conNode + '.outColorR',  blsNode + '.' + comboBls )
    

    return [ multNode, conNode ]










