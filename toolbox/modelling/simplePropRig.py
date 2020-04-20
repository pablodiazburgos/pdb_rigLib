"""
Module to create simple rig for props
@author: Pablo Diaz Burgos
"""
from PySide2 import QtCore
from PySide2 import QtUiTools
from PySide2 import QtWidgets
from PySide2 import QtGui

import maya.cmds as mc
import maya.mel as mm

from ..utils import name
from ..utils import attribute


class CreateSimplePropRig():
    
    def __init__( self, ui, statusBar ):
        
        self.ui = ui
        self.statusBar = statusBar
        
    def createSimplePropRig(self):
        
        self.propGeo = mc.ls(sl = True, type = 'transform')[0]
        self.prefix = name.removeSuffix( self.propGeo )
        
        self._createBaseGroups()
        
    def _createBaseGroups(self):
        
        self.mainGroup = mc.group( em = True )