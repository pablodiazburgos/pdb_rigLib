'''
Module to make the retarget proccess from different mocap or joint animations to dhs biped rigs
@author: Pablo Diaz Burgos
'''

# import modules
from PySide2 import QtCore
from PySide2 import QtUiTools
from PySide2 import QtWidgets
from PySide2 import QtGui

import maya.cmds as mc
import maya.mel as mm


class AnimRetarget():
    
    def __init__( self, ui, statusBar ):
        
        self.ui = ui
        self.statusBar = statusBar
    
    def animRetarget(self ):
        
        pass