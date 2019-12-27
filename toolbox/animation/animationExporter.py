"""
module to export animation from maya through Dream House toolBox
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
from string import lower

# define global variables
VIS_CTRL = 'vis_ctl'

class AnimationExporter():
    
    def __init__( self, ui, statusBar ):
        
        self.ui = ui
        self.statusBar = statusBar
        
    def setConnections(self):
        
        self.ui.getSaveAnimPath_btn.clicked.connect( self.getSavePath )
        self.ui.exportAnim_btn.clicked.connect( self.exportFbxAnimation )
        self.ui.openAnimPathFolder_btn.clicked.connect( self.openSaveFolder )
        
    def openSaveFolder(self):
        
        self.path = self.ui.animSavePath_lne.text()
        # check save path 
        if not os.path.exists( self.path ):
            
            self.statusBar.showMessage("Given path does not exist, cannot open file explorer")
            self.statusBar.setStyleSheet("color: red")
            return
        
        self.statusBar.showMessage("Opening file path in OS browser")
        self.statusBar.setStyleSheet("color: green")        
        os.startfile( self.path )
        
    def getSavePath(self):
        saveDir = QtWidgets.QFileDialog.getExistingDirectory(self.ui, 'Save Directory', '')
        if saveDir:
            self.ui.animSavePath_lne.setText(saveDir)
    
    def exportFbxAnimation(self):
        
        # try to load fbx plugin 
        if not mc.pluginInfo('fbxmaya', q = True, l = True):
            mc.loadPlugin('fbxmaya.mll')

        # get some info 
        self.filePath = '{}/{}.fbx'.format( self.ui.animSavePath_lne.text(), self.ui.animFileName_lne.text() )
        self.path = self.ui.animSavePath_lne.text()
        self.fileName = self.ui.animFileName_lne.text()
        
        # checkbox and time info
        self.exportMesh = self.ui.exportMesh_cbx.isChecked()
        self.startFrameVal = self.ui.startFrame_lne.text()
        self.endFrameVal = self.ui.endFrame_lne.text()
        
        # check if user provides right information
        if not self.startFrameVal:
            self.statusBar.showMessage("No Start frame provided... expect an 'integer' value ")
            self.statusBar.setStyleSheet("color: red")
            return
        
        if self.startFrameVal:
            # try to convert provided info to int
            try:
                self.startFrameVal = int( self.startFrameVal )
            except:
                self.statusBar.showMessage("Start frame value is not supported...please use an 'integer' type")
                self.statusBar.setStyleSheet("color: red")
                return
        
        # check if user provides right information
        if not self.endFrameVal:
            self.statusBar.showMessage("No end frame provided... expect an 'integer' value ")
            self.statusBar.setStyleSheet("color: red")
            return
        
        if self.endFrameVal:
            # try to convert provided info to int
            try:
                self.endFrameVal = int( self.endFrameVal )
            except:
                self.statusBar.showMessage("End frame value is not supported...please use an 'integer' type")
                self.statusBar.setStyleSheet("color: red")
                return 
        
        if self.endFrameVal <= self.startFrameVal:
            self.statusBar.showMessage("Start frame should be less than End frame")
            self.statusBar.setStyleSheet("color: red")
            return             
        
        self._setVisCtrlAttrsToExport( VIS_CTRL )
        
        # set fbx export settings
        # Geometry
        mm.eval("FBXExportSmoothingGroups -v true")
        mm.eval("FBXExportHardEdges -v false")
        mm.eval("FBXExportTangents -v false")
        mm.eval("FBXExportSmoothMesh -v true")
        mm.eval("FBXExportInstances -v false")
        
        # Animation
        mm.eval("FBXExportBakeComplexAnimation -v true")
        mm.eval("FBXExportBakeComplexStart -v {}".format( self.startFrameVal ) )
        mm.eval("FBXExportBakeComplexEnd -v {}".format( self.endFrameVal ) )
        mm.eval("FBXExportBakeComplexStep -v 1")
        mm.eval("FBXExportUseSceneName -v false")
        mm.eval("FBXExportQuaternion -v euler")
        mm.eval("FBXExportShapes -v true")
        mm.eval("FBXExportSkins -v true")
        # Constraints
        mm.eval("FBXExportConstraints -v false")
        
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
                self.statusBar.setStyleSheet("color: green")
                self.statusBar.showMessage( 'File overwritten: {}'.format( self.filePath ) )
            else:
                self.statusBar.setStyleSheet( "color: yellow" )
                self.statusBar.showMessage( 'you press "No", nothing happened ' )
                return              
        else:
            self._export()
        
        self._setVisCtrlAttrsToAnim( VIS_CTRL )
            
    def _export(self):
        
        assetModelGrp = 'assetModel_grp'
        jointGrps = 'joints_grp'
        
        # check if model and joints group exists
        if not mc.objExists(assetModelGrp):
            self.statusBar.showMessage("'{}' does not exist, cannot export file".format( assetModelGrp ) )
            self.statusBar.setStyleSheet("color: red")
            return 

        if not mc.objExists(jointGrps):
            self.statusBar.showMessage("'{}' does not exist, cannot export file".format( jointGrps ) )
            self.statusBar.setStyleSheet("color: red")
            return 
        
        # store current playback time and set a temporal time while export, then turn in back to original time
        oriMinTime = mc.playbackOptions( q = True, minTime = True)
        oriMaxTime = mc.playbackOptions( q = True, maxTime = True)
        mc.playbackOptions( minTime = self.startFrameVal, maxTime = self.startFrameVal )
        
        # make selection based on given info from user
        mc.select( cl = True )
        mc.select( jointGrps )
        
        if self.exportMesh:
            mc.select( assetModelGrp, add = True )
            
        mm.eval( 'FBXExport -f "{0}" -s'.format( self.filePath ) )
        
        mc.playbackOptions( minTime = oriMinTime, maxTime = oriMaxTime )
        
        self.statusBar.showMessage('Exported File: {}'.format( self.filePath ) )
        self.statusBar.setStyleSheet("color: green")    
   
    def _setVisCtrlAttrsToExport(self, visCtrl ):
        
        mc.setAttr('{}.geometryDispType'.format( visCtrl ), 0)
        mc.setAttr('{}.jointVis'.format( visCtrl ), 1)
        mc.setAttr('{}.jointDispType'.format( visCtrl ), 0)
        mc.modelEditor('modelPanel4', e = True, jx = True, j = True)
    
    def _setVisCtrlAttrsToAnim(self, visCtrl ):
        
        mc.setAttr('{}.geometryDispType'.format( visCtrl ), 2)
        mc.setAttr('{}.jointVis'.format( visCtrl ), 0)
        mc.setAttr('{}.jointDispType'.format( visCtrl ), 2)
