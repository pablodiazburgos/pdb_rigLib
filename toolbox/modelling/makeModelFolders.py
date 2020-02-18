"""
module to create base folders structure for Dream House Studios modellers
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

class CreateModelFolders():
    
    def __init__( self, ui, statusBar ):
        
        self.ui = ui
        self.statusBar = statusBar
   
    def setConnections(self):
        
        self.ui.getModelFoldersPath_btn.clicked.connect( self.getModelFoldersSavePath )
        self.ui.openModelFolders_btn.clicked.connect( self.openModelFolders )
        self.ui.createModelFolders_btn.clicked.connect( self.createFolders )
        
    def getModelFoldersSavePath(self):
        saveDir = QtWidgets.QFileDialog.getExistingDirectory(self.ui, 'Save Directory', '')
        if saveDir:
            self.ui.createModelFoldersPath_lne.setText(saveDir)
            
    def openModelFolders(self):
        
        self.path = self.ui.createModelFoldersPath_lne.text()
        # check save path 
        if not os.path.exists( self.path ):
            
            self.statusBar.showMessage("Given path does not exist, cannot open file explorer")
            self.statusBar.setStyleSheet("color: red")
            return
        
        self.statusBar.showMessage("Opening file path in OS browser")
        self.statusBar.setStyleSheet("color: green")        
        os.startfile( self.path )
        
    def createFolders(self):
        # check if asset name and path are ok
        self.assetName = self.ui.createModelFoldersAssetName_lne.text()
        self.rootDir = self.ui.createModelFoldersPath_lne.text()
        
        if not os.path.exists( self.rootDir ):
            
            self.statusBar.showMessage("Given path does not exist, please specify folders path")
            self.statusBar.setStyleSheet("color: red")
            return
        
        if not self.assetName:
            self.statusBar.showMessage("No Asset name found, please specify an Asset name")
            self.statusBar.setStyleSheet("color: red")
            return
        
        # create path and folder for main rig folder
        mainFolderDir = os.path.join(self.rootDir, self.assetName)
        if os.path.exists(mainFolderDir):
            self.statusBar.showMessage("'{}' already exists in given path, nothing created".format( self.assetName ))
            self.statusBar.setStyleSheet("color: yellow")
            return
            
        else:
            os.mkdir(mainFolderDir)
            self.makeSubFolders(mainFolderDir = mainFolderDir)
            
            self.statusBar.showMessage("'{}' model folders structure created".format( self.assetName ))
            self.statusBar.setStyleSheet("color: green")
            
        
    def makeSubFolders(self, mainFolderDir = ''):
        # define version and temp folder names
        version = 'versions'
        temp = 'temp'
        
        # sub folder names
        modelFolders = [
                    'cc',
                    'textures',
                    'export',
                    'export/obj',
                    'export/obj/{}'.format( version ),
                    'export/fbx',
                    'export/fbx/{}'.format( version ),
                    'maya',
                    'substance',
                    'blender',
                    'zbrush',
                    'marvelous'
                     ]
        
        # define version in sub folders

        versionTempFolders = modelFolders[6:]
        
        for folder in modelFolders:
            
            modelFullPath = os.path.join(mainFolderDir, folder)
            
            newModelFullPath = [modelFullPath]
            # check if version and temp folders should be included
            if folder in versionTempFolders:
                versionFullPath = os.path.join(modelFullPath, version)
                tempFullPath = os.path.join(modelFullPath, temp)
                
                newModelFullPath.append(versionFullPath)
                newModelFullPath.append(tempFullPath)
            
            # make the folders
            for path in newModelFullPath:
                if not os.path.exists(path):
                    os.mkdir(path)
        
