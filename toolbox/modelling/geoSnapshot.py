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

import os

class geometrySnapshot():
    
    def __init__( self, ui, statusBar ):
        
        self.ui = ui
        self.statusBar = statusBar
   
    def setConnections(self):
        
        self.ui.getGeoSnapshotPath_btn.clicked.connect( self.getGeoSnapshotSavePath )
        
    def getGeoSnapshotSavePath(self):
        saveDir = QtWidgets.QFileDialog.getExistingDirectory(self.ui, 'Save Directory', '')
        if saveDir:
            self.ui.savePath_lne.setText(saveDir)