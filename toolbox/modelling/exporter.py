"""
module to export items from maya through Dream House toolBox
@author: Pablo Diaz Burgos
"""
# import modules
from PySide2 import QtCore
from PySide2 import QtUiTools
from PySide2 import QtWidgets
from PySide2 import QtGui

import maya.cmds as mc
import maya.mel as mm

import os

class geometryExporter():
    
    def __init__( self, ui, statusBar ):
        
        self.ui = ui
        self.statusBar = statusBar
        
    def setConnections(self):
        
        self.ui.getSavePath_btn.clicked.connect( self.getSavePath )
        self.ui.mayaUnits_cbx.currentIndexChanged.connect( self.setMayaUnits )
        self.ui.exportGeo_btn.clicked.connect( self.exportFbxModel )
        self.ui.openSaveModelFolder_btn.clicked.connect( self.openSaveFolder )
        
    def setMayaUnits(self):
        
        currentText = self.ui.mayaUnits_cbx.currentText()
        mc.currentUnit( linear = currentText )
        self.statusBar.showMessage("Maya units set to: {}".format( currentText ) )
        self.statusBar.setStyleSheet("color: green")   
  
    def exportFbxModel(self):
        
        # try to load fbx plugin 
        if not mc.pluginInfo('fbxmaya', q = True, l = True):
            mc.loadPlugin('fbxmaya.mll')

        # get some info 
        self.filePath = '{}/{}.fbx'.format( self.ui.savePath_lne.text(), self.ui.fileName_lne.text() )
        self.path = self.ui.savePath_lne.text()
        self.exportAll = self.ui.exportGeo_cbx.currentIndex()
        self.fileName = self.ui.fileName_lne.text()

        # set fbx export settings
        mm.eval('FBXExportConvertUnitString  "{}"'.format( mc.currentUnit( q = True, linear = True, l = False ) ) )
        mm.eval('FBXExportInAscii -v true')
        mm.eval( 'FBXExportAnimationOnly -v false' )
        
        # check save path 
        if not os.path.exists( self.path ):
            
            self.statusBar.showMessage("Given path does not exist, cannot export file")
            self.statusBar.setStyleSheet("color: red")
            return
        
        # check if path already exists and ask for overwrite file
        if os.path.exists( self.filePath ):
            result = QtWidgets.QMessageBox.question(self.ui, "Existing file", "Current file already exists. Continue?")
        
        
            if result == QtWidgets.QMessageBox.StandardButton.Yes:
                self._export()
                self.statusBar.setStyleSheet( exportFbxModel.statusColor )
                self.statusBar.showMessage( 'File overwritten: {}'.format( filePath ) )
            else:
                self.statusBar.setStyleSheet( "color: yellow" )
                self.statusBar.showMessage( 'you press "No", nothing happened ' )
                return              
        else:
            self._export()
            
   
    def getSavePath(self):
        saveDir = QtWidgets.QFileDialog.getExistingDirectory(self.ui, 'Save Directory', '')
        if saveDir:
            self.ui.savePath_lne.setText(saveDir)
            
    def _export(self):
        
        if self.exportAll:
            mm.eval( 'FBXExport -f "{0}"'.format( self.filePath ) )
        else:
            if not mc.ls( sl = True ):
                self.statusBar.showMessage("Nothing is selected to export")
                self.statusBar.setStyleSheet("color: red") 
                
                return
                
            mm.eval( 'FBXExport -f "{0}" -s'.format( self.filePath ) )
            
        self.statusBar.showMessage('Exported File: {}'.format( self.filePath ) )
        self.statusBar.setStyleSheet("color: green")
    
    def openSaveFolder(self):
        
        self.path = self.ui.savePath_lne.text()
        # check save path 
        if not os.path.exists( self.path ):
            
            self.statusBar.showMessage("Given path does not exist, cannot open file explorer")
            self.statusBar.setStyleSheet("color: red")
            return
        
        self.statusBar.showMessage("Opening file path in OS browser")
        self.statusBar.setStyleSheet("color: green")        
        os.startfile( self.path )    
        
        
        
        
        
        
        
        
        