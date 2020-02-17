"""
module to take a snapshot of the current view in maya and save it out in disk
@author: Pablo Diaz Burgos
"""

# import modules
from PySide2 import QtCore
from PySide2 import QtUiTools
from PySide2 import QtWidgets
from PySide2 import QtGui

import maya.cmds as mc
import maya.mel as mm
import maya.OpenMaya as api
import maya.OpenMayaUI as apiUI


import os

perspectiveModelPanel = 'modelPanel4'
imageWidth = 1920
imageHeight = 1080

class geometrySnapshot():
    
    def __init__( self, ui, statusBar ):
        
        self.ui = ui
        self.statusBar = statusBar
   
    def setConnections(self):
        
        self.ui.getGeoSnapshotPath_btn.clicked.connect( self.getGeoSnapshotSavePath )
        self.ui.openGeoSnapshotFolder_btn.clicked.connect( self.openGeoSnapshotFolder )
        self.ui.exportGeoSnapshot_btn.clicked.connect( self.exportGeoSnapshot )
        
    def getGeoSnapshotSavePath(self):
        saveDir = QtWidgets.QFileDialog.getExistingDirectory(self.ui, 'Save Directory', '')
        if saveDir:
            self.ui.saveGeoSnapshotPath_lne.setText(saveDir)
            
    def openGeoSnapshotFolder(self):
        
        self.path = self.ui.saveGeoSnapshotPath_lne.text()
        # check save path 
        if not os.path.exists( self.path ):
            
            self.statusBar.showMessage("Given path does not exist, cannot open file explorer")
            self.statusBar.setStyleSheet("color: red")
            return
        
        self.statusBar.showMessage("Opening file path in OS browser")
        self.statusBar.setStyleSheet("color: green")        
        os.startfile( self.path )    
    
    def exportGeoSnapshot(self):
        
        # get some information
        
        # check if there is a file name
        self.fileName = self.ui.geoSnapshotFileName_lne.text()
        if not self.fileName:
            self.statusBar.showMessage("Please specify a name for the snapshot files")
            self.statusBar.setStyleSheet("color: red")
                    
        # create file path and files names
        prefixNames = [
                    'wireframeSnapshot',
                    'modelSnapshot'
                    ]
        
        self.modelPanelInfo = self._getModelPanelInfo()
        
        wosState = True

        for prefix in prefixNames:
            
            # turn off no needed model panel info
            mc.modelEditor( 
                            perspectiveModelPanel, 
                            e = True, 
                            grid = False, 
                            headsUpDisplay = False,
                            wos = wosState 
                            )
            mc.refresh()
            
            # get some path info
            self.name = '{}_{}'.format( prefix, self.fileName )
            self.fullPath = '{}/{}.jpg'.format( self.ui.saveGeoSnapshotPath_lne.text(), self.name )
            self.path = self.ui.saveGeoSnapshotPath_lne.text()
            
            # check if save path exists
            if not os.path.exists( self.path ):
                self.statusBar.showMessage("Given path does not exist, cannot export file")
                self.statusBar.setStyleSheet("color: red")
                return
            
            # check if full path already exists and ask for overwrite file
            if os.path.exists( self.fullPath ):
                result = QtWidgets.QMessageBox.question(self.ui, "Existing file", "Current file already exists. Continue?")
            
            
                if result == QtWidgets.QMessageBox.StandardButton.Yes:
                    self._export()
                    self.statusBar.setStyleSheet("color: green")
                    self.statusBar.showMessage( 'File overwritten: {}'.format( self.fullPath ) )
                else:
                    self.statusBar.setStyleSheet( "color: yellow" )
                    self.statusBar.showMessage( 'you press "No", nothing happened ' )
                    return              
            else:
                self._export()
            
            wosState = False
            
        self._setModelPanelInfo()
            
    def _getModelPanelInfo(self):
        
        infoDir = {}
        
        infoDir['gridState'] = mc.modelEditor( perspectiveModelPanel, q = True, grid = True )
        infoDir['hudState'] = mc.modelEditor( perspectiveModelPanel, q = True, headsUpDisplay = True )
        infoDir['wosState'] = mc.modelEditor( perspectiveModelPanel, q = True, wos = True )
        
        return infoDir
            
    def _export(self):
        
        #Set Background color
        #mc.displayRGBColor( 'background', 0, 0, 0 )
        
        #read the color buffer from the view, and save the MImage to disk
        image = api.MImage()
        view = apiUI.M3dView.active3dView()
        view.readColorBuffer(image, True)
        
        utilVariable1 = api.MScriptUtil() #Create new MScriptUtil
        utilPointer1 = utilVariable1.asUintPtr() #Set its type to Unsigned Intiger, which getSize() wants
        
        utilVariable2 = api.MScriptUtil() #Create new MScriptUtil
        utilPointer2 = utilVariable2.asUintPtr() #Set its type to Unsigned Intiger, which getSize() wants
        
        #Call getSize(), which will write the width and height into the pointers provided to it:
        image.getSize( utilPointer1, utilPointer2 ) 
        
        #Get actual values out of the pointers, and save them into variables width and height:
        width = utilVariable1.getUint(utilPointer1)
        height = utilVariable2.getUint(utilPointer2)
        
        #Print the values:
        print "Width: %s" %width
        print "Height: %s" %height
        
        ##### Resize the image: ######
        image.resize(imageWidth,imageHeight,True)
        print "----- RESIZING -----"
        
        #Use getsize() again to get the changed values:
        image.getSize( utilPointer1, utilPointer2 )
        
        #Get the actual values from the pointers again
        width = utilVariable1.getUint(utilPointer1)
        height = utilVariable2.getUint(utilPointer2)
        
        #Print the new values after resize:
        print "New Width: %s" %width
        print "New Height: %s" %height
        
        #Write image into a file:
        image.writeToFile( self.fullPath, 'jpg' )
        
    def _setModelPanelInfo(self):
        
        mc.modelEditor( perspectiveModelPanel, e = True, grid = self.modelPanelInfo['gridState'] )
        mc.modelEditor( perspectiveModelPanel, e = True, headsUpDisplay = self.modelPanelInfo['hudState'] )
        mc.modelEditor( perspectiveModelPanel, e = True, wos = self.modelPanelInfo['wosState'] )
        
        
            
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        