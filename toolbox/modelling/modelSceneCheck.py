"""
sanity scene model check to be sure model are ready to go down the pipe
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

class MeshChecker():
    
    def __init__(self):
        
        # initialize objects
        self.ui = ui
        self.statusBar = statusBar
        
    def _listAllTopObjects( self ):
        pass