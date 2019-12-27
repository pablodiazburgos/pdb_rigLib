'''
saveSkinWeights in rigit.tools
@category Rigging @subcategory Tools
@tags skinCluster skin save load weights
@author jakub
'''


import json
import os
from string import atoi
from string import atof

import maya.cmds as mc
import maya.mel as mm
import maya.OpenMaya as om
import maya.OpenMayaAnim as oma

from ..utils import name
from ..utils import skinCluster
from ..utils import shape
from ..utils import apiwrap
from ..utils import surface


deformedSuffix = 'Deformed'  # this refers to suffix which Maya adds to deformed shapes of referenced transforms
supportedShapeExtensionDt = {'mesh':'vtx', 'nurbsSurface':'cv', 'nurbsCurve':'cv', 'lattice':'pt'}
skinningMethodKey = 'skinningMethod'
skinningMethodsDt = { 0:'classicLinear', 1:'dualQuaternion', 2:'weightBlended' }



def save( points, skincldef, wfile, verbose = True ):
    
    '''
    @param points: list of geometry point (vertex) names
    @type points: str list
    @param skincldef: name of skinCluster to save weights from
    @type skincldef: str
    @param wfile: weight file path (default extension should be *.skinwt )
    @type wfile: str
    @return: None
    
    saves skinCluster weights based on passed points (has to be from the same geometry shape)
    works on both whole geometry or just selection of points
    
    format: 1) info 2) shape 3) influences 4) weights <each line has point index + weights array>
    - weights per each point are written in the same order as they were connected to skinCluster
      at the time of saving the weights, this order is stored as Influences list in the file
    
    STORING OPTIMIZATION:
    
        If all points are passed, optimization does not check their index
        and so they must be passed in order from 0 index to last index,
        otherwise weights will not be written correctly
        (example getting all points: mc.ls( 'pCylinder.vtx[*]', fl=1 ) )
        
        If less then all points are passed, script will perform string parsing
        on each point name (e.g. 'pSphere2.vtx[279]' ) to get its index
    
    SUPPORTED SHAPES:
        
        mesh, nurbsCurve, nurbsSurface, lattice
    
    '''
    
    # get info about the object
    
    pointObject = mc.ls( points[0], o = 1 )[0]
    geoShape = shape.getShape( pointObject )[0]
    geoObject = mc.listRelatives( geoShape, p = 1 )[0]
    skinningMethod = mc.getAttr( skincldef + '.skinningMethod' )
    
    #===========================================================================
    # prepare lines for the file
    #===========================================================================
    
    writeLines = []
    
    # make header
    
    fileType = 'rigit saveSkinWeights - skinCluster weight file'
    fileInfo = [
                '#' + fileType + '\n',
                geoObject + '\n',
                skinningMethodKey + ' ' + skinningMethodsDt[skinningMethod] + '\n'
                ]
    
    # make weight lines for given points
    
    influences = mc.skinCluster( skincldef, q = 1, inf = 1 )
    influencesLines = [ inf + '\n' for inf in influences ]
    
    
    #===========================================================================
    # prepare weight lines
    #===========================================================================
    
    lineWeights = []
    influencesSize = len( influences )
    influenceIndeces = mc.getAttr( skincldef + '.matrix', mi = 1 )
    
    # prepare string index list in case only part of points were passed
    
    ext = _supportedShapeCheck_getExtension( geoShape, verbose )
    
    if not ext:
        
        if verbose:
                
                print '# getting index list from points ( %s ... ) failed, skipping saving its weights ...' % points[0]
                
        return
    
    # get index list of points
    
    allPointSize = len( mc.ls( geoShape + '.' + ext + '[*]', fl = True ) )
    pointSize = len( points )
    indexList = mc.getAttr( '%s.weightList' % ( skincldef ), multiIndices = True )
    addedInfo = ''
    
    if not allPointSize == pointSize:
        
        indexList = _getIndexListForPointList( points, geoShape, ext )
        addedInfo = ' out of %d' % allPointSize
    
    # print report about saving weights
    
    if verbose:
        
        print '# saving skinCluster weights for %s with %d point size%s' % ( geoObject, pointSize, addedInfo )
    
    
    # read weights and store them in array
    
    for i in indexList:
        
        pIdx = i
        pIdxStr = str( i )
        
        # in case of problem with index, skip this point
        # it will be left as default weight after loading weights
        if i == -1:
            
            continue
        
        pWeights = []
        weightListArrayAt = skincldef + '.weightList[' + str( pIdx ) + '].weights'
        
        # get just indeces present on this point
        # with sparse indeces, only some influence weights are stored
        
        pointInfIndeces = mc.getAttr( weightListArrayAt, multiIndices = True )
        
        if not pointInfIndeces:
            
            continue
        
        # get sparse weights on point
        
        sparsePWeights = mc.getAttr( weightListArrayAt )[0]
        sparsePWeightsIdx = 0
        
        # store non-sparse weights, adding missing influence weights as zero
        
        for infidx in influenceIndeces:
            
            if infidx in pointInfIndeces:
                
                pWeights.append( sparsePWeights[ sparsePWeightsIdx ] )
                sparsePWeightsIdx += 1
            
            else:
                
                pWeights.append( 0.0 )
        
        
        pWeightsStr = [ str( w ) for w in pWeights ]
        lineWeights.append( pIdxStr + ' ' + ' '.join( pWeightsStr ) + '\n' )
    
    # write into file
    
    fileobj = open( wfile, 'w' )
    writeLines = fileInfo + ['\n'] + influencesLines + ['\n'] + lineWeights
    fileobj.writelines( writeLines )
    
    fileobj.close()
    
    

def _getIndexListForPointList( points, geoShape, ext ):
    
    '''
    get list of indeces for given list of shape points
    - must be from the same geometry shape
    '''
    
    indexList = []
    
    allPoints = mc.ls( geoShape + '.' + ext + '[*]', fl = 1 )
    
    for pt in points:
        
        # in rare case where point from selection could not be found
        # in list of all points store it as -1 index
        if not pt in allPoints:
            
            indexList.append( -1 )
            continue
        
        ptIndex = allPoints.index( pt )
        indexList.append( ptIndex )
    
    return indexList
    
    

def loadCheck( wfile ):
    
    '''
    return values which are flagged true 
    
    @param wfile: weight file path
    @type wfile: str
    @return: list(str, etc.), values of parameters from file (0- geometry name)
    '''
    
    fileobj = open( wfile )
    lines = fileobj.readlines()
    
    # get file info
    
    geoNameFile = lines[1].replace( '\n', '' )
    
    # make values list
    
    returnList = [ geoNameFile ]
    
    
    return returnList
    

def load( wfile, verbose = True, prefix = '', removeDeformSuffix = None, shapeOverride = None, normalize = True, useCompInfluences = True, loadMethodOverride = None ):
    
    '''
    @param wfile: str, weight file path
    @param verbose: bool, print feedback from operations
    @param prefix: str, add prefix to each shape name before loading, useful for deformed referenced shapes saved without this prefix
    @param removeDeformSuffix: str, string with suffix to be removed from object name as read from weights file, used to resolve Maya reference shape renaming
    @param shapeOverride: str, override name of object for loading skinCluster weights, this is used only if value is not None
    @param normalize: bool, normalize weights after loading (geometry can become invisible sometimes if weights are not normalized)
    @param useCompInfluences: bool, use component influences, otherwise treat all influences like transform
    @param loadMethodOverride: str, override load skin weights method, valid methods are: 'setAttr', 'setWeights'
    @return: None
    
    load skinCluster weights
    - existing skinCluster: handles different influence order and missing influences
    - no skinCluster: creates new one with influences taken from weights file
    '''
    
    # internal switch to set method between classic setAttr per vertex point setting all its influence weights
    # and setWeights API function from MFnSkinCluster
    
    loadMethods = ['setAttr', 'setWeights']
    loadMethod = loadMethods[1]
    
    if loadMethodOverride:
        
        loadMethodIdx = loadMethods.index( loadMethodOverride )
    
    else:
        
        loadMethodIdx = loadMethods.index( loadMethod )
    
    # read weight file
    
    fileobj = open( wfile, mode = 'r' )
    lines = fileobj.readlines()
    fileobj.close()
    
    # get geometry object
    
    geoObj = lines[1].replace( '\n', '' )
    
    # get skinning method (new features - so we need to test for existance of line)
    testSkinningMethodLine = lines[2].replace( '\n', '' )
    skinningMethod = 0
    
    if testSkinningMethodLine.startswith( skinningMethodKey ):
        
        lineParts = testSkinningMethodLine.split( ' ' )
        
        if len( lineParts ) > 1:
            
            skinningMethodStr = lineParts[1]
            
            for k, v in skinningMethodsDt.items():
                
                if v == skinningMethodStr:
                    
                    skinningMethod = k
    
    
    # remove suffix
    
    if removeDeformSuffix and geoObj.endswith( removeDeformSuffix ):
        
        geoObj = geoObj[:-len( removeDeformSuffix )]
    
    # add prefix
    
    if prefix:
        
        geoObj = prefix + geoObj
    
    # check shape
    
    if shapeOverride:
        
        geoObj = shapeOverride
    
    # check that object exists
    
    if not mc.objExists( geoObj ):
        
        if verbose:
            
            print '# %s not found in scene, skipping it for loading weights ...' % geoObj
        
        return
    
    # make sure we have transform
    
    shapes = shape.getShape( geoObj )
    geoObj = mc.listRelatives( shapes[0], p = 1 )[0]
    
    
    # process text lines and influence order
    
    weightSpaceNum = 0
    pointIndexList = []
    lineValuesStrList = []
    
    for line in lines:
      
        if line == '\n':
            
            weightSpaceNum = weightSpaceNum + 1
            continue
        
        if weightSpaceNum == 2:
          
          line = line.replace( '\n', '' )
          lineValuesStr = line.split()
          pointIndexList.append( int( lineValuesStr[0] ) )
          lineValuesStrList.append( lineValuesStr[1:] )
    
    
    # get more information about geometry
    
    ext = _supportedShapeCheck_getExtension( shapes[0], verbose )
    geoCvList = mc.ls( geoObj + '.' + ext + '[*]', fl = 1 )
    pointSize = len( geoCvList )
    savedPointSize = len( pointIndexList )
    addedInfo = ' in total'
    
    if not pointSize == savedPointSize:
        
        addedInfo = ' from its %d points in total' % pointSize
    
    if verbose:
        
        print '# loading weights for %s for %d points%s' % ( geoObj, savedPointSize, addedInfo )
    
    
    # get influences in text file order
    
    influences = []
    influenceStartLineNum = 3
    
    if testSkinningMethodLine:
        
        influenceStartLineNum = 4
    
    for l in lines[influenceStartLineNum:]:
    
      if l == '\n':
          
          break
      
      else:
          
        l = l.replace( '\n', '' )
        influences.append( l )
    
    
    nonExistingInfs = [ inf for inf in influences if not mc.objExists( inf ) ]
    
    if len( nonExistingInfs ) > 0:
        
        printMissingInfs_printonly( nonExistingInfs )
        return ''
    
    
    # make skinCluster and add influences
    
    if verbose:
        
        print 'influences', influences
    
    try:
        
        addInflResult = skinCluster.makeSkinClusterAddInfluences( geoObj, influences, verbose = verbose, useCompInfluences = useCompInfluences )
    
    except:
        
        if verbose:
            
            print '# applying skinCluster deformer and adding influence failed with Maya error, geometry of %s could be corrupted' % geoObj
            
        return
    
    skincldef = addInflResult[0]
    scInfs = addInflResult[1]
    createdSkinCluster = addInflResult[2]
    
    # set skinning method type to deformer
    mc.setAttr( skincldef + '.skinningMethod', skinningMethod )
    
    # get influence order if skinCluster existed
    
    scInfOrder = []
    fileInfluenceBooleans = []
    
    for inf in scInfs:
        
        if inf in influences:
            
            infOrderIdx = influences.index( inf )
            scInfOrder.append( infOrderIdx )
            fileInfluenceBooleans.append( 1 )
        
        else:
            
            fileInfluenceBooleans.append( 0 )
    
    # load weights
    
    lineWeights = []
    infMaxIdx = len( influences ) - 1
    infMaxIdxStr = str( infMaxIdx )
    infSizeStr = str( len( influences ) )
    influenceIndeces = mc.getAttr( skincldef + '.matrix', mi = 1 )
    influenceInOrder = mc.listConnections( skincldef + '.matrix' )
    
    # reorder weight values based on current skinCluster influence order
    
    weightValuesInOrder = {}
    
    for pointIdx, lineValuesStr in zip( pointIndexList, lineValuesStrList ) :
        
        pointWeightsInOrder = []
        counter = 0
        
        for in_file in fileInfluenceBooleans:
            
            if in_file:
                
                w = atof( lineValuesStr[ scInfOrder[counter] ] )
                counter += 1
            
            else:
                
                # zero weight for influence which was in existing skinCluster
                # but not in list of influences in the file
                w = 0.0
                
            pointWeightsInOrder.append( w )
        
        weightValuesInOrder[ pointIdx ] = pointWeightsInOrder
    
    
    # load weights on skinCluster node
    
    shapeType = mc.nodeType( shapes[0] )
    
    if shapeType == 'nurbsSurface' or shapeType == 'lattice' or loadMethodIdx == 0:
        
        # _setWeightsSkinPercent( skincldef, weightValuesInOrder, influenceInOrder, geoCvList )
        _setWeightsAttr( skincldef, weightValuesInOrder, createdSkinCluster, infSizeStr, infMaxIdxStr, influenceIndeces )
    
    else:
        
        _setWeightsApi( skincldef, weightValuesInOrder, createdSkinCluster, pointSize, pointIndexList )
    
    
    # normalize weights
    
    if normalize:
        
        mc.select( geoObj )
        mc.skinPercent( skincldef, normalize = True )
    
    # turn on skinCluster envelope
    
    mc.setAttr( skincldef + '.en', 1 )
        

def _setWeightsAttr( skinClusterName, weightValuesInOrder, createdSkinCluster, infSizeStr, infMaxIdxStr, influenceIndeces ):
    
    
    for pointIdx, weightValues in weightValuesInOrder.items():
      
      if createdSkinCluster:
          
          weightValuesStr = [ str( w ) for w in weightValues ]
          pointWeightsStr = ' '.join( weightValuesStr )
          cmd = 'setAttr -size ' + infSizeStr + ' ' + skinClusterName + '.weightList[' + str( pointIdx ) + '].weights[0:' + infMaxIdxStr + '] ' + pointWeightsStr
          mm.eval( cmd )
          
      else:
          
          for i, idx in enumerate( influenceIndeces ):
              
              mc.setAttr( skinClusterName + '.weightList[' + str( pointIdx ) + '].weights[' + str( idx ) + ']', weightValues[i] )


def _setWeightsSkinPercent( skinClusterName, weightValuesInOrder, influenceInOrder, geoCvList ):
    
    for pointIdx, weightValues in weightValuesInOrder.items():
        
        geoCv = geoCvList[pointIdx]
        transformValueString = ''
        
        for inf, wt in zip( influenceInOrder, weightValues ):
            
            s = ' -transformValue %s %f' % ( inf, wt )
            transformValueString += s
        
        cmd = 'skinPercent %s %s %s' % ( transformValueString, skinClusterName, geoCv )
        mm.eval( cmd )
        


def _setWeightsApi( skinClusterName, weightValuesInOrder, createdSkinCluster, pointSize, pointIndexList ):
    
    # generate flat weight list
    
    flatWeights = []
    weightSpaceNum = 0
    
    for weightValues in weightValuesInOrder.values():
        
        flatWeights.extend( weightValues )
    
    # make API objects
    
    shapeMObject = apiwrap.getMObject( skinClusterName )
    fnSkinCluster = oma.MFnSkinCluster( shapeMObject )
    
    skinPath = om.MDagPath()
    fnSkinCluster.getPathAtIndex( 0, skinPath )
    
    shapeobj = mc.deformer( skinClusterName, q = 1, g = 1 )[0]
    shapeComponents = _prepareShapeComponents( shapeobj, skinClusterName, pointSize, pointIndexList )
    
    # prepare influence indeces
    
    inflIndeces = mc.getAttr( skinClusterName + '.matrix', mi = 1 )
    inflIndecesMIntAr = om.MIntArray()
    
    for idx in inflIndeces:
        
        inflIndecesMIntAr.append( idx )
    
    # prepare weight values
    
    valuesMDoubleAr = om.MDoubleArray()
    
    for v in flatWeights:
        
        valuesMDoubleAr.append( v )
    
    fnSkinCluster.setWeights( skinPath, shapeComponents, inflIndecesMIntAr, valuesMDoubleAr )
    
    
def _prepareShapeComponents( shapeobj, skinClusterName, pointSize, pointIndexList ):
    
    # get components from shape
    
    shapeType = mc.nodeType( shapeobj )
    
    if shapeType == 'mesh':
        
        pointsComponents = om.MFnSingleIndexedComponent()
        elementArray = _prepareShapeComponents_elementArray( pointSize, pointIndexList, shapeobj, shapeType )
        shapeComponents = pointsComponents.create( om.MFn.kMeshVertComponent )
        pointsComponents.addElements( elementArray )
    
    if shapeType == 'nurbsCurve':
        
        pointsComponents = om.MFnSingleIndexedComponent()
        elementArray = _prepareShapeComponents_elementArray( pointSize, pointIndexList, shapeobj, shapeType )
        shapeComponents = pointsComponents.create( om.MFn.kCurveCVComponent )
        pointsComponents.addElements( elementArray )
    
    if shapeType == 'nurbsSurface':
        
        pointsComponents = om.MFnDoubleIndexedComponent()
        elementArray1, elementArray2 = _prepareShapeComponents_elementArray( pointSize, pointIndexList, shapeobj, shapeType )
        shapeComponents = pointsComponents.create( om.MFn.kSurfaceCVComponent )
        pointsComponents.addElements( elementArray1, elementArray2 )
    
    if shapeType == 'lattice':
        
        pointsComponents = om.MFnTripleIndexedComponent()
        elementArray1, elementArray2, elementArray3 = _prepareShapeComponents_elementArray( pointSize, pointIndexList, shapeobj, shapeType )
        shapeComponents = pointsComponents.create( om.MFn.kLatticeComponent )
        pointsComponents.addElements( elementArray1, elementArray2, elementArray3 )
    
    
    return shapeComponents    



def _prepareShapeComponents_elementArray( pointSize, pointIndexList, shapeobj, shapeType ):
    
    '''
    prepare element array based on shape type
    '''
    
    if shapeType == 'mesh' or shapeType == 'nurbsCurve':
        
        elementArray = om.MIntArray()
        
        for i in range( pointSize ):
            
            if i in pointIndexList:
                
                elementArray.append( i )
        
        return elementArray
    
    
    if shapeType == 'nurbsSurface':
        
        uvSizesU, uvSizesV = surface.getUvCvSizes( shapeobj )
        elementArray1 = om.MIntArray()
        elementArray2 = om.MIntArray()
        pointIdx = 0
        
        for u in range( uvSizesU ):
            
            for v in range( uvSizesV ):
                
                if pointIdx in pointIndexList:
                    
                    elementArray1.append( u )
                    elementArray2.append( v )
                
                pointIdx += 1
        
        return [elementArray1, elementArray2]
    
    
    if shapeType == 'lattice':
        
        sDivisions = mc.getAttr( shapeobj + '.sDivisions' )
        tDivisions = mc.getAttr( shapeobj + '.tDivisions' )
        uDivisions = mc.getAttr( shapeobj + '.uDivisions' )
        
        elementArray1 = om.MIntArray()
        elementArray2 = om.MIntArray()
        elementArray3 = om.MIntArray()
        pointIdx = 0
        
        for u in range( uDivisions ):
            
            for t in range( tDivisions ):
                
                for s in range( sDivisions ):
                    
                    if pointIdx in pointIndexList:
                        
                        elementArray1.append( s )
                        elementArray2.append( t )
                        elementArray2.append( u )
                    
                    pointIdx += 1
        
        return [elementArray1, elementArray2, elementArray3]
    
    
    
    

def loadFromDir( dirpath, geoList = [], extension = 'skinwt', verbose = True, prefix = '', removeDeformSuffix = False, useCompInfluences = True ):
    
    '''
    load weights from all files in given directory
    assuming each file name is same as mesh name
    
    @param dirpath: directory path
    @type dirpath: str
    @param geoList: optional to load weights only for objects in this list, if list is empty, all objects weights are loaded
    @type geoList: list str
    @param extension: file extension for each new file
    @type extension: str
    @param verbose: print feedback from operations
    @type verbose: bool
    @param prefix: add prefix to each shape name before loading, useful for deformed referenced shapes saved without this prefix
    @type prefix: str
    @param removeDeformSuffix: remove "*Deform" suffix before searching for shape, it gets added by Maya when saving scene with referenced deformed shapes
    @type removeDeformSuffix: bool
    @param useCompInfluences: use component influences, otherwise treat all influences like transform
    @type useCompInfluences: bool
    @return: None
    '''
    
    if dirpath.endswith( '/' ) == 0: dirpath = dirpath + '/'
    
    dirFiles = os.listdir( dirpath )
    weightFiles = [ dirpath + f for f in dirFiles if f.count( '.' + extension ) ]
    
    
    # get all geometry shapes
    
    checkObjects = False
    shapeNames = []
    
    # consider if something is in geometry list
    # we want to only load weights for these objects
    
    if geoList:
        
        checkObjects = True
        
    
    for f in weightFiles:
      
      objName = loadCheck( f )[0]
      
      if checkObjects:
          
          if not objName in geoList:
              
              continue
      
      load( f, 1, prefix, removeDeformSuffix, useCompInfluences = useCompInfluences )
      


def saveToDir( objects, dirpath, extension = 'skinwt', verbose = True ):
  
  '''
  save weights of given objects to given directory
  file name is the same as the mesh name, plus given extension
  
  @param objects: list of objects to save their skinCluster weights
  @type objects: list( str )
  @param dirpath: directory to save files to (will name each file <NAME_OF_OBJECT.EXTENSION> )
  @type dirpath: str
  @param extension: file extension for each new file
  @type extension: str
  @return: None
  '''
  
  if dirpath.endswith( '/' ) == 0: dirpath = dirpath + '/'
  
  for o in objects:
  
    sc = skinCluster.getRelated( o )
    
    if not sc or mc.objExists( sc ) == 0:
        
        if verbose:
            
            print '# no skinCluster found on %s, skipping saving weights on this one' % o
        
        continue
    
    mShort = name.short( o )
    mShort = name.removeNamespace( mShort )
    weightsFile = dirpath + mShort + '.' + extension
    
    shapeobjs = shape.getShape( o )
    
    if not shapeobjs:
        
        if verbose:
            
            print '# no shapes found on object %s, skipping saving weights on this one' % o
        
        continue
    
    else:
        
        shapeobj = shapeobjs[0]
    
    ext = _supportedShapeCheck_getExtension( shapeobj, verbose )
    
    if not ext:
        
        continue
    
    points = mc.ls( o + '.' + ext + '[*]', fl = 1 )
    save( points, sc, weightsFile, verbose )


def _supportedShapeCheck_getExtension( shapeobj, verbose = True ):
    
    '''
    given shape object function will return shape component string extension
    if it is supported, otherwise return False
    '''
    
    shapeType = mc.nodeType( shapeobj )
    
    supportedShapeExtensionDt = {'mesh':'vtx', 'nurbsSurface':'cv', 'nurbsCurve':'cv', 'lattice':'pt'}
    supportedShapeTypes = supportedShapeExtensionDt.keys()
    
    if shapeType in supportedShapeTypes:
        
        ext = supportedShapeExtensionDt[ shapeType ]
        return ext
    
    else:
        
        if verbose:
            
            '# shape object %s did not match any supported type: %s, skipping saving weights on this one' % ( shapeobjs, shapeType )
        
        return False
    
    



def printMissingInfs_printonly( missingInfs ):
    
    print ''
    print '# influences (listed below) not found, cannot make skinCluster'
    print missingInfs
    print ''
    
    
def saveBlendWeights( filePath, deformerNode ):
    
    '''
    save skinCluster blend weights array attribute values
    
    @param filePath: name of file path made of folder and filename, extension is optional ('/dir1/dir2/dir3/muscleA_wire')
    @type filePath: str
    @param deformerNode: name of deformer node
    @type deformerNode: str
    @return: filePath with extension ('/dir1/dir2/dir3/muscleA_wire.wts')
    '''
    
    # check file
    
    filePathname, fileextension = os.path.splitext( filePath )
    if not fileextension: filePath += wtextension
    
    # read weights from deformer node
    
    deformerType = mc.nodeType( deformerNode )
    
    weightsDt = { 'deformerName': deformerNode, 'deformerType':deformerType }
    wlistIndeces = mc.getAttr( deformerNode + '.blendWeights', multiIndices = 1 )
    
    if not wlistIndeces:
        
        wlistIndeces = []
    
    weightsListDt = {}
    valuesDt = {}
    
    for idx in wlistIndeces:
        
        wvalue = mc.getAttr( deformerNode + '.blendWeights[%d]' % idx )
        valuesDt[ idx ] = wvalue
    
    weightsDt['weights'] = valuesDt
    
    # write file    
    
    fileobj = open( filePath, mode = 'w' )    
    json.dump( weightsDt, fileobj, sort_keys = True, indent = 4, separators = ( ',', ': ' ) )
    fileobj.close()
    
    return filePath

        
def loadBlendWeights( filePath, deformerNode = '', verbose = True ):
    
    '''
    save deformer Weights array attribute values, deformer node needs to be provided
    
    @param filePath: name of file path made of folder and filename, if no extension, default one will be used ('/dir1/dir2/dir3/muscleA_wire')
    @type filePath: str
    @param deformerNode: optional, name of deformer node (name is written in the file, but this can work as override)
    @type deformerNode: str
    @return: None
    '''
    
    # check file
    
    filePathname, fileextension = os.path.splitext( filePath )
    if not fileextension: filePath += wtextension
    
    # read from file
    
    fileobj = open( filePath, mode = 'rb' )
    fileobjStr = fileobj.read()
    weightsDt = json.loads( fileobjStr )
    fileobj.close()
    
    # check info from file
    
    if not deformerNode:
        
        # if no deformer was specified try to use deformer name in the file
        
        deformerNode = weightsDt['deformerName']
        
        if not mc.objExists( deformerNode ):
            
            raise Exception( '# deformer node named as %s in file %s not found' % ( deformerNode, filePath ) )
    
    
    # set values to deformer node
    
    valuesDt = weightsDt['weights']
    
    for idx, wvalue in valuesDt.items():
        
        idxInt = int( idx )
        mc.setAttr( '%s.blendWeights[%d]' % ( deformerNode, idxInt ), wvalue )
        


