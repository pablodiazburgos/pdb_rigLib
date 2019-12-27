"""
module to deal with uvs for Dream House tool box
@author: Pablo Diaz Burgos
"""

# import modules
from PySide2 import QtCore
from PySide2 import QtUiTools
from PySide2 import QtWidgets
from PySide2 import QtGui

from ..utils import mesh

import maya.cmds as mc
import maya.mel as mm

class UvsTools():
    
    def __init__(self, ui, statusBar ):
        
        self.ui = ui
        self.statusBar = statusBar
        self.sourceObj = None
        self.targetObj = None
        
    def setConnections(self):
        
        self.ui.uvsFrom_btn.clicked.connect( self.populateSourceList )
        self.ui.uvsSourceClear_btn.clicked.connect( self.clearSourceList )
        self.ui.uvsTo_btn.clicked.connect( self.populateTargetList )
        self.ui.uvsSourceTarget_btn.clicked.connect( self.clearTargetList )
        self.ui.uvsTransferUvs_btn.clicked.connect( self.transferUvs )
        self.ui.fixTexPathWin_btn.clicked.connect( self.filePathWindow )
        self.ui.addLightMap_btn.clicked.connect( self.addLightmapSet )
  
    def populateSourceList(self):
        
        self.sourceObj = mc.ls( sl = True )
        
        if not self.sourceObj:
                
            self.statusBar.setStyleSheet( 'color: yellow' )
            self.statusBar.showMessage( 'Nothing selected, please select something' )
            
            return
            
        geoType = mesh.checkIFMesh( self.sourceObj[0] )
        
        if not geoType:
            
            self.statusBar.setStyleSheet( 'color: red' )
            self.statusBar.showMessage( 'Please select a "mesh" type object')
            
            return
        
        self.ui.uvsSource_lts.clear()
        self.ui.uvsSource_lts.addItem( self.sourceObj[0] )
        
        self.statusBar.setStyleSheet( 'color: green' )
        self.statusBar.showMessage( '"{}" mesh as source is loaded'.format( self.sourceObj[0] ) )                      
    
    def clearSourceList(self):
        
        self.ui.uvsSource_lts.clear()
        
        self.sourceObj = None
        
        self.statusBar.setStyleSheet( 'color: green' )
        self.statusBar.showMessage( 'Source list is cleaned')
        
    def populateTargetList(self):
        
        self.targetObj = mc.ls( sl = True )
        
        if not self.targetObj:
                
            self.statusBar.setStyleSheet( 'color: yellow' )
            self.statusBar.showMessage( 'Nothing selected, please select something' )
            
            return
            
        geoType = mesh.checkIFMesh(self.targetObj[0] )
        
        if not geoType:
            
            self.statusBar.setStyleSheet( 'color: red' )
            self.statusBar.showMessage( 'Please select a "mesh" type object')
            
            return
        
        self.ui.uvsTarget_lts.clear()
        self.ui.uvsTarget_lts.addItem( self.targetObj[0] )
        
        self.statusBar.setStyleSheet( 'color: green' )
        self.statusBar.showMessage( '"{}" mesh as Target is loaded'.format( self.targetObj[0] ) )                      
    
    def clearTargetList(self):
        
        self.ui.uvsTarget_lts.clear()
        self.targetObj = None
        
        self.statusBar.setStyleSheet( 'color: green' )
        self.statusBar.showMessage( 'Target list is cleaned')
    
    def transferUvs(self):
        
        # create dictionary to pass in the transfer attributes 
        
        sampleSpaceDic = {
                        'World': 0,
                        'Local': 1,
                        'Uv': 3,
                        'Component': 4,
                        'Topology': 5
                        }
        searchMethodDic = {
                        'Closest along normal': 0,
                        'Closest to point': 3
                        }
        
        sampleSpaceCbxText = self.ui.uvsSampleSpace_cbx.currentText()
        searchMethodCbxText = self.ui.uvsSearchMethod_cbx.currentText()
        
        # check if there is anything in the list 
        
        if not self.sourceObj:
            self.statusBar.setStyleSheet( 'color: red' )
            self.statusBar.showMessage( 'there is not source geo, please select one') 
            
            return
        
        if not self.targetObj:
            
            self.statusBar.setStyleSheet( 'color: red' )
            self.statusBar.showMessage( 'there is not target geo, please select one') 
            
            return            
        
               
        mc.transferAttributes( self.sourceObj[0], self.targetObj[0], sampleSpace = sampleSpaceDic[sampleSpaceCbxText], 
                               searchMethod = searchMethodDic[searchMethodCbxText],
                               sourceUvSpace = 'map1',
                               targetUvSpace = 'map1',
                               transferUVs = 2,
                               flipUVs = 0,
                               n = '%sTo%sAttributes#' % ( self.sourceObj[0], self.targetObj[0] )
                                )
        
        self.statusBar.setStyleSheet( 'color: green' )
        self.statusBar.showMessage( 'Uvs copied from "{}" to "{}"'.format( self.sourceObj[0], self.targetObj[0] ) ) 
    
    def addLightmapSet(self):
        
        # check is something is selected
        self.objectList = mc.ls( sl = True, type = 'transform' )
        
        if not self.objectList:
            
            self.statusBar.showMessage("Please select at least one object" ) 
            self.statusBar.setStyleSheet("color: yellow")
            return
        
        for obj in self.objectList:
            allUvs = mc.polyUVSet( obj, allUVSets = True , q = True )
            if 'lightMap' in allUvs:
                continue
            
            copyUvs = mc.polyUVSet( obj, cp = True, uvs = allUvs[0] )[0]
            mc.polyUVSet(obj, rename=True, newUVSet='lightMap', uvSet= copyUvs)

        self.statusBar.showMessage("Light map Uv set created for selected objects" ) 
        self.statusBar.setStyleSheet("color: green")
            
    def filePathWindow(self):
        
        mm.eval( 'filePathEditorWin;' ) 
        self.statusBar.showMessage( "file path window opened" )
        self.statusBar.setStyleSheet("color: green") 
        
        
        
        
        
        
        
        