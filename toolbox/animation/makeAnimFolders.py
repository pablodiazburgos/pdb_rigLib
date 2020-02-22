"""
module to create base folders structure for Dream House Studios Animators
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

class CreateAnimFolders():
    
    def __init__( self, ui, statusBar ):
        
        self.ui = ui
        self.statusBar = statusBar
   
    def setConnections(self):
        
        self.ui.getCreateAnimFoldersPath_btn.clicked.connect( self.getAnimFoldersSavePath )
        self.ui.openAnimFolders_btn.clicked.connect( self.openAnimFolders )
        self.ui.createAnimFolders_btn.clicked.connect( self.createFolders )
        
    def getAnimFoldersSavePath(self):
        saveDir = QtWidgets.QFileDialog.getExistingDirectory(self.ui, 'Save Directory', '')
        if saveDir:
            self.ui.createAnimFoldersPath_lne.setText(saveDir)
            
    def openAnimFolders(self):
        
        self.path = self.ui.createAnimFoldersPath_lne.text()
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
        self.assetName = self.ui.createAnimFoldersName_lne.text()
        self.rootDir = self.ui.createAnimFoldersPath_lne.text()
        self.projectType = self.ui.createAnimFolders_cbx.currentIndex()
        
        if not os.path.exists( self.rootDir ):
            
            self.statusBar.showMessage("Given path does not exist, please specify folders path")
            self.statusBar.setStyleSheet("color: red")
            return
        
        if not self.assetName:
            self.statusBar.showMessage("No Name found, please specify a Name")
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
            
            if self.projectType:
                self.makeProjectTypeSubFolders(mainFolderDir = mainFolderDir)
            else:
                self.makeAnimTypeSubFolders(mainFolderDir = mainFolderDir)
            
            self.statusBar.showMessage("'{}' folders structure type '{}' created".format( self.assetName, self.ui.createAnimFolders_cbx.currentText() ))
            self.statusBar.setStyleSheet("color: green")
            
        
    def makeProjectTypeSubFolders(self, mainFolderDir = ''):
        
        # sub folder names
        projectFolders = [
                    'assets',
                    'assets/rigs',
                    'assets/props',
                    'assets/enviroments',
                    'animations'
                     ]
        
        # define version in sub folders

        for folder in projectFolders:
            fullPath = os.path.join(mainFolderDir, folder)
            
            if not os.path.exists(fullPath):
                    os.mkdir(fullPath)
    
    def makeAnimTypeSubFolders(self, mainFolderDir = ''):
        
        # sub folder names
        projectFolders = [
                    'playblast',
                    'anim',
                    'anim/versions',
                    'anim/temp',
                    'baked',
                    'baked/versions',
                    'feedback',
                    'references'
                     ]
        
        # define version in sub folders

        for folder in projectFolders:
            fullPath = os.path.join(mainFolderDir, folder)
            
            if not os.path.exists(fullPath):
                    os.mkdir(fullPath)
   
