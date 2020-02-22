"""
module which containts buttons to help animation process
@author: Pablo Diaz Burgos
"""

# import modules
from PySide2 import QtCore
from PySide2 import QtUiTools
from PySide2 import QtWidgets
from PySide2 import QtGui

import maya.cmds as mc
import maya.mel as mm

class AnimHelpButtons():
    
    def __init__( self, ui, statusBar ):
        
        self.ui = ui
        self.statusBar = statusBar
        
    def setConnections(self):
        
        self.ui.freezeAllCtrls_btn.clicked.connect( self.freezeAll )
        self.ui.freezeSelCtrls_btn.clicked.connect( self.freezeSel )
        
    def freezeAll(self):
        controls = mc.ls(['*_ctl', '*:*_ctl'],type='transform')
        for c in controls:
            for channel in ['t','r']:
                for axis in ['x','y','z']:
                    try: mc.setAttr( c + '.' + channel + axis, 0.0 )
                    except: continue
                
        self.statusBar.showMessage("All controls freezed")
        self.statusBar.setStyleSheet("color: green")
  
    def freezeSel(self):
        controls = mc.ls(['*_ctl', '*:*_ctl'],type='transform', sl = True)

        if not controls:
            self.statusBar.showMessage("Please select at least one control") 
            self.statusBar.setStyleSheet("color: yellow") 
            return
    
        for c in controls:
            for channel in ['t','r']:
                for axis in ['x','y','z']:
                    try: mc.setAttr( c + '.' + channel + axis, 0.0 )
                    except: continue
        
        self.statusBar.showMessage("Selected controls freezed")
        self.statusBar.setStyleSheet("color: green")     