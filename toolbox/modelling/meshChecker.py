"""
module with multiple tools to check different issues may happend with geometry 
"""
# ... 
import maya.cmds as mc
import maya.mel as mm

selTypeDictionary = {'ngones': 3, 'tris': 1}  # Dictionary for geo artifacts (ngones/triangles)
defaultSG = 'initialShadingGroup'

class MeshChecker():
    
    def __init__(self, ui, statusBar):
        
                # get buttons state
        
        # initialize objects
        self.ui = ui
        self.statusBar = statusBar
        self.originalSG = {}
        
    def setConnections(self):
        
        self.ui.resetGeo_btn.clicked.connect( self.resetGeo )
        self.ui.deleteHistory_btn.clicked.connect( self.deleteHistory )
        self.ui.nGones_btn.clicked.connect( self.checkArtifactFaces )
        self.ui.triangles_btn.clicked.connect( lambda: self.checkArtifactFaces( artifactType = 'tris') )
        self.ui.cleanGeo_btn.clicked.connect( self.cleanGeo )
        self.ui.shderBack_btn.clicked.connect( self.shaderBack )
        self.ui.absoluteZero_btn.clicked.connect( self.absoluteZero )
    
    def resetGeo(self):
        
        # get buttons state
        self.transform = self.ui.resetTransforms_cbx.isChecked()
        self.basePivot = self.ui.basePivot_btn.isChecked()
        self.zeroPivot = self.ui.zeroPivot_btn.isChecked()
        self.keepPivot = self.ui.keepPivot_btn.isChecked()
        self.centerPivot = self.ui.centerPivot_btn.isChecked()

        
        
        self.objectList = mc.ls( sl = True, type = 'transform' )
        
        if not self.objectList:
            
            self.statusBar.showMessage("Please select at least one object" ) 
            self.statusBar.setStyleSheet("color: yellow")
            return
        
        for obj in self.objectList:
            if self.transform:
                mc.makeIdentity( obj, apply = True, t = True, r = True, s = True, pn = True )
            
            if self.centerPivot:
                mc.xform( obj, cp = True )

            if self.basePivot:
               
                bboxPos = mc.getAttr( '{0}.boundingBoxMin'.format( obj ) )[0]
                mc.xform( obj, cp = True )
                pivotOriginalPos = mc.xform( obj, q = True, ws = True, rp = True )
                mc.xform( obj, piv = ( pivotOriginalPos[0], bboxPos[1], pivotOriginalPos[2] ), ws = True )
                
            if self.zeroPivot:
                mc.xform( obj, piv = (0, 0, 0) )
            
            if self.keepPivot:
                pass
            
        mc.select( self.objectList )
        self.statusBar.showMessage('Reset Geometry done for selected objects')
        self.statusBar.setStyleSheet("color: green")    
    
    def deleteHistory(self):
        
        # get button state
        self.nonDeformer = self.ui.nonDeformer_cbx.isChecked()
        
        objectList = mc.ls( sl = True, type = 'transform' )
            
        if not objectList:
            
            self.statusBar.showMessage("Please select at least one object")
            self.statusBar.setStyleSheet("color: yellow") 
            return
        
        for obj in objectList:
            if self.nonDeformer:
                mc.bakePartialHistory(obj, ppt = True)
            else:
                mc.delete( obj, ch = True )
                
        self.statusBar.showMessage('History deleted for selected Objects')
        self.statusBar.setStyleSheet("color: green")    

    def checkArtifactFaces(self, artifactType = 'ngones'):
        
        '''
        :param artifactType: str, filter type to select faces of artifacts, supported types('ngones', 'tris')
        '''
        # check is something is selected
        self.objectList = mc.ls( sl = True, type = 'transform' )
        
        if not self.objectList:
            
            self.statusBar.showMessage("Please select at least one object" ) 
            self.statusBar.setStyleSheet("color: yellow")
            return
        
        # make sure passed artifactType is valid
        if not artifactType in selTypeDictionary.keys():
            self.statusBar.showMessage("'{}' is not a valid artifact type, please pass a valid one" ) 
            self.statusBar.setStyleSheet("color: red")
            return 
        
        # get artifacts faces 
        mc.polySelectConstraint( m=3, t=8, sz=selTypeDictionary[artifactType], topology=0)
        matchFaces = mc.ls( fl = True, sl = True )
        
        mc.polySelectConstraint(m=0, t=8, sz=3, topology=0)  # Reset select constrain to defaults after storage

        # if not matching faces just return it 
        if not matchFaces:
            self.statusBar.showMessage("No artifact faces found" ) 
            self.statusBar.setStyleSheet("color: green")
            return            
        
        # store original shaders assigments in originalShader dir
        for obj in self.objectList:
            
            returnSG = self._getSG(obj)
            
            if not returnSG:
                self.originalSG[obj] = defaultSG
            else:
                self.originalSG[obj] = returnSG
        
        self._assingTempShader(faces = matchFaces, artifactType = artifactType)
        
        mc.select( self.objectList )
        
        self.statusBar.showMessage("Temporary shader assigned for found artifacts" ) 
        self.statusBar.setStyleSheet("color: green")

    def _assingTempShader(self, faces, artifactType ):
        
        if artifactType == 'ngones':
            faceType = 'Ngones'
            shaderColor = [1, 0, 0]
        if artifactType == 'tris':
            faceType = 'Tris'
            shaderColor =[0, 1, 0]
        
        tempShadingGroupName = 'temp{}ShadingGroup1'.format( faceType )
        tempShaderName = 'temp{}Shader1'.format( faceType )
        
        # check if shader already exists
        if mc.objExists( tempShadingGroupName ):
            tempShadingGroup = tempShadingGroupName
            tempShader = tempShaderName
        else:                
            # create shader
            tempShadingGroup = mc.sets( name = tempShadingGroupName, renderable=True, empty=True )
            tempShader = mc.shadingNode( 'lambert', name = tempShaderName, asShader=True )
            
            # assing shader color based on type
            mc.setAttr( '{}.color'.format( tempShader ),shaderColor[0], shaderColor[1], shaderColor[2], type='double3' )
            mc.surfaceShaderList( tempShader, add = tempShadingGroup )
        
        mc.sets( faces, e=True, forceElement = tempShadingGroup )
                
    def shaderBack(self):
        
        # define temp shaders name
        ngoneShaderName = 'tempNgonesShader1'
        ngoneSGName = 'tempNgonesShadingGroup1'
        
        trisShaderName = 'tempTrisShader1'
        trisSGName = 'tempTrisShadingGroup1'
        
        # check is something is selected
        self.objectList = mc.ls( sl = True, type = 'transform' )
        
        if not self.objectList:
            
            self.statusBar.showMessage("Please select at least one object" ) 
            self.statusBar.setStyleSheet("color: yellow")
            return

        # apply original shader to object... if there is nothing in original shader just pass 
        for obj in self.objectList:
            if not obj in self.originalSG.keys():
                continue
            
            mc.sets(obj, e=True, forceElement=self.originalSG[obj])
        
            del self.originalSG[obj]
            
        # check if there is any mesh connected to temp shders... if not just delete it
        if not mc.listConnections( ngoneSGName, type = 'mesh' ):
            mc.delete( ngoneSGName, ngoneShaderName )
            
        if not mc.listConnections( trisSGName, type = 'mesh' ):
            mc.delete( trisSGName, trisShaderName )
    
        
        self.statusBar.showMessage("Original shaders assigned for selected objects" ) 
        self.statusBar.setStyleSheet("color: green")             
                         
    def _getshader(self, object ):
        
        '''
        get shader assigned to object (transform or shape can be passed)
        
        :param object: str, name of object to look for a shader
        :return: str, name of shader, return None if no shader was found
        '''
        
        objshapes = mc.listRelatives( object, s = 1, f = 1, noIntermediate = 1 )
        if not objshapes: return None
        
        shadingengine = mc.listConnections( objshapes[0], type = 'shadingEngine' )
        if not shadingengine: return None
        shadernode = mc.listConnections( shadingengine[0] + '.surfaceShader' )
        if not shadernode: return None
        
        return shadernode[0]
    
    def _getSG(self, object ):
        
        '''
        get shading group assigned to object (transform or shape can be passed)
        
        :param object: str, name of object to look for a shader
        :return: str, name of shading group, return None if no shader was found
        '''
        
        objshapes = mc.listRelatives( object, s = 1, f = 1, noIntermediate = 1 )
        if not objshapes: return None
        
        shadingengine = mc.listConnections( objshapes[0], type = 'shadingEngine' )
        if not shadingengine: return None
        
        return shadingengine[0]
    
    def cleanGeo(self):
        # check is something is selected
        self.objectList = mc.ls( sl = True, type = 'transform' )
        
        if not self.objectList:
            
            self.statusBar.showMessage("Please select at least one object" ) 
            self.statusBar.setStyleSheet("color: yellow")
            return
        
        returnVal = mm.eval('polyCleanupArgList 4 { "0","1","1","0","0","0","0","0","0","1e-05","1","1e-05","0","1e-05","0","-1","0","0" };')
        print 'returnVal:', returnVal
        
        self.statusBar.showMessage("Selected geo cleaned" ) 
        self.statusBar.setStyleSheet("color: green")    
        
        mc.select( self.objectList )
        
    def absoluteZero(self):
       
        objectList = mc.ls( sl = True, type = 'transform' )
        
        if not objectList:
            
            self.statusBar.showMessage("Please select at least one object")
            self.statusBar.setStyleSheet("color: yellow") 
            return
        
        for object in objectList:
            mc.move( 0, 0, 0, object, rpr = True)
            
        self.statusBar.showMessage('Selected objects moved to absolute zero')
        self.statusBar.setStyleSheet("color: green")  
    
    
    
    
    
    