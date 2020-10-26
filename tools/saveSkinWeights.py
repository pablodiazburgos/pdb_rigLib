'''
saveSkinWeights in pdb_rigLib.tools
@category Rigging @subcategory Tools
@tags skinCluster skin save load weights
'''


import json
import os
from string import atoi
from string import atof
import ngSkinTools.importExport as ngIO
import re


import maya.cmds as mc
import pymel.core as pm
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

jsonExt = '.json'
wtextension = '.wts'
parallelInfoExt = '.info'

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
        
def saveNgSkinWeights( filePath, skinMesh ):
    """
    Save NG skin weights using ngSkinTools.importExport API 
    :param filePath: str, file path including file name and extension to save the skin info
    :param skinMesh: pyNode, mesh with the NG skinning info attached
    :return None
    """
    
    # prepare layers info
    layerData = ngIO.LayerData()
    layerData.loadFrom( skinMesh.name() )

    exporter = ngIO.JsonExporter()
    jsonContents = exporter.process(layerData)
    
    # convert json string to  json dir to update with the name of the 
    # skin mesh to use later in load function
    layersDt = json.loads( jsonContents )
    layersDt['skinMesh'] = skinMesh.name()
    layersDt['skinClusterName'] = skinCluster.getRelated( skinMesh.name() )
    
    # convert back json dir to json string so we can save it out
    jsonContents = json.dumps(layersDt,indent=2)
    # remove line break if next line is "whitespace + closing bracket or positive/negative number"
    jsonContents = re.sub(r'\n\s+(\]|\-?\d)',r"\1",jsonContents)

    # string "jsonContents" can now be saved to an external file
    fileObj = open( filePath, mode = 'w' )
    json.dump( jsonContents, fileObj )
    fileObj.close()
    
    print '# NGskin weights info for "{}" saved in:\n    {}'.format( skinMesh, filePath )

def saveParallelWeights( filePath, skinMesh = '' ):
    
    """
    Save parallel skin clusters into given file path
    NOTE:  NG  export API only exports the first skin cluster in the deformation order so
    it the script should be looping through all the skin clusters changing the deformation
    order and then exporting it individually 
    
    :param filePath: str, file path including file name and extension to save the skin info
    :param skinMesh: pyNode, mesh with the NG skinning info attached
    :return None 
    """
    # check if skinMesh is "mesh" type , NG only works with mesh
    if skinMesh.getShapes( noIntermediate = True )[0].nodeType() != 'mesh':
        pm.error( '# "{}" must be a transform with "mesh" type object shape'.format( skinMesh ) )
    
    # get all the skin clusters attached to the mesh
    skinClusters = skinCluster.getMultipleRelated( skinMesh )
    
    if not skinClusters:
        print '# No skin clusters attached to "{}"...Skipping'.format( skinMesh )
        return
    
    # directory to hold all the skin clusters info
    infoDt = {}
    skcFullPathList = []
        
    # loop through each skin cluster changing the deformation order to proper export
    
    for i, skc in enumerate(skinClusters):
        
        # create skin file name and extend it to the file path
        fileName = skc.name() + jsonExt
        skcFullPath = filePath + fileName
        
        # update skcFullPath
        skcFullPathList.append( skcFullPath )
        
        # make current skin the first one in the deformation order
        # create a new copy of the original skin cluster list
        skinClustersCopy = skinClusters[:] # creates a copy of the skinCluster list without being linked 
        currentSkc = skinClustersCopy.pop(i)
        
        for idx in range( len( skinClustersCopy ) ):
            pm.reorderDeformers( currentSkc.name(), skinClustersCopy[idx].name(), skinMesh.getShapes()[0].name() )
    
        saveNgSkinWeights( skcFullPath, skinMesh )
    
    # create info file wich will be holding the skin clusters deformation order
    # and associated skin clusters to the skinMesh
    infoPath = '{}{}_parallelSkin{}'.format( filePath, skinMesh.name(), parallelInfoExt )
    
    infoDt['skcDeformOrder'] = [skc.name() for skc in skinClusters]
    infoDt['skcFullPath'] = skcFullPathList
    infoDt['skinMesh'] = skinMesh.name()
    
    # save info file
    fileObj = open( infoPath, mode = 'w' )
    json.dump( infoDt, fileObj )
    fileObj.close()
    print infoDt

def loadNgSkinWeights( filePath ):
    '''
    Load skin weights layers and data from given file path
    '''
    
    
    fileobj = open( filePath, mode = 'rb' )
    fileobjStr = fileobj.read()
    layersStr = json.loads( fileobjStr )
    fileobj.close()
    
    importer = ngIO.JsonImporter()
    layerData = importer.process(layersStr)
    
    # get mesh target
    # convert previously serialized json string to json Dir 
    layersDt = json.loads(layersStr)
    skinMesh = layersDt.get('skinMesh')
    skinClusterName = layersDt.get( 'skinClusterName' )
    
    # get influence joints to create skin cluster
    infJoints = layerData.getAllInfluences()
   
    print 'skinClusterName:', skinClusterName
    print 'infJoints:', infJoints

    # create parallel skinning if the skinMesh already has one skin cluster attached
    skinCluster.createParallelSkinCluster( pm.PyNode( skinMesh ), skinClusterName, infJoints )
    
    layerData.saveTo( skinMesh )
    
    print '# NG skin weights and data assigned to "{}"'.format( skinMesh )
        
def loadParallelWeights( filePath ):
    '''
    loads parallel weights using Ng skin api which also initialize by default the Ng layers
    NOTE:  NG  export API only imports the first skin cluster in the deformation order so
    it the script should be looping through all the skin clusters changing the deformation
    order and then importing it individually 
    '''
    # check file
    filePathname, fileextension = os.path.splitext( filePath )
    if not fileextension: filePath += parallelInfoExt
    
    # read from file
    fileobj = open( filePath, mode = 'rb' )
    fileobjStr = fileobj.read()
    infoDt = json.loads( fileobjStr )
    fileobj.close()     
    
    # get some info from dir
    skcDeformOrder = infoDt.get('skcDeformOrder')
    skcFullPaths = infoDt.get('skcFullPath')
    skinMesh = infoDt.get('skinMesh')
    
    # check if the target mesh exists , if not just skip this load
    if not pm.objExists( skinMesh ):
        print '# could not find "{}"... skipping this load'.format( skinMesh )
        return
    
    # save all the skin clusters
    for skcPath in skcFullPaths:
        
        loadNgSkinWeights( skcPath )
        
    #reorder deformers
    skcRevDeformOrder = []
    for i in reversed( skcDeformOrder ):
        skcRevDeformOrder.append( i )
    
    for i in range( len(skcDeformOrder) ):
        
        skinClustersCopy = skcRevDeformOrder[:] # creates a copy of the skinCluster list without being linked 
        currentSkc = skinClustersCopy.pop(i)
        
        for idx in range( len( skinClustersCopy ) ):
            pm.reorderDeformers( currentSkc, skinClustersCopy[idx], skinMesh )
    
        
        
        
        
        
        
        
        
    
