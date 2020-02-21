"""
module to offset animation keys, either way selection or all controls, joints and blsNode in scene
@author: Pablo Diaz Burgos
"""

# import modules
from PySide2 import QtCore
from PySide2 import QtUiTools
from PySide2 import QtWidgets
from PySide2 import QtGui

import maya.cmds as mc
import maya.mel as mm

animObjectsFilter = ['*_ctl', 
               '*:*_ctl',
               '*_jnt', 
               '*:*_jnt', 
               '*_blsNode']

class AnimKeyOffset():
    
    def __init__( self, ui, statusBar ):
        
        self.ui = ui
        self.statusBar = statusBar

    def setConnections(self):
        
        self.ui.animKeyOffset_btn.clicked.connect( self.offsetKeys )
        
    def offsetKeys(self):
        
        # check if offset would be for all joints, controls and blsNode or just selected items
        allState = self.ui.animKeyOffsetTarget_cbx.currentIndex()
        comboBoxString = self.ui.animKeyOffsetTarget_cbx.currentText ()
        self.timeOffsetVal = self.ui.animKeyOffsetValue_lne.text()
        
        if allState:
            animObjects = mc.ls( animObjectsFilter )
            
        else:
            animObjects = mc.ls( sl = True )
            
            if not animObjects:
            
                # if target is selection and nothing is selected show an error
                self.statusBar.setStyleSheet( "color: red" )
                self.statusBar.showMessage( 'Target is set to "selected", please select something' )
                return
        
        # check if provided time offset value is ok
        if not self.timeOffsetVal:
            self.statusBar.showMessage("No Start frame provided... expect an 'integer' value ")
            self.statusBar.setStyleSheet("color: red")
            return
        
        if self.timeOffsetVal:
            # try to convert provided info to int
            try:
                self.timeOffsetVal = int( self.timeOffsetVal )
            except:
                self.statusBar.showMessage("Time offset value is not supported...please use an 'integer' type")
                self.statusBar.setStyleSheet("color: red")
                return
        
        # offset the animation keys of passed objects
        #if objects doesn't have any key it would skip it
        
        for obj in animObjects:
            activeKeys = mc.keyframe( obj, q = True, n = True )
            
            if not activeKeys:
                continue
            
            for activeKey in activeKeys:
                mc.keyframe(activeKey, edit=True, relative=True, timeChange = self.timeOffsetVal )
        
        self.statusBar.showMessage("keys for '{}' objects moved '{}' frames".format( comboBoxString, self.timeOffsetVal ))
        self.statusBar.setStyleSheet("color: green")