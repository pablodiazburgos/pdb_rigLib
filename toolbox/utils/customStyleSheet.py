'''
Module to assign custom style sheet for dream house toolbox
'''

# import modules
from PySide2 import QtCore
from PySide2 import QtUiTools
from PySide2 import QtWidgets
from PySide2 import QtGui

import maya.cmds as mc
import maya.mel as mm


class CustomStyleSheet():
    
    def __init__(self, ui):
        
                # get buttons state
        
        # initialize objects
        self.ui = ui
        self._setStyleSheet()
        self._setOpenFolderIcons()
        
    def _setStyleSheet(self):
        pass
    '''
        self.ui.setStyleSheet(
            "QGroupBox {  border: 0.5px solid; border-radius: 7px; \
                    border-color: rgb(149, 196, 132); padding-top: 10px; font-style: italic;} \
                        \
                    QPushButton {border-radius: 4px; border: \
                    0.5px solid; border-color: rgb(149, 196, 132); min-height: 17px; background-color:\
                    rgb(45, 45, 45);} \
                    QPushButton::hover {border-radius: 4px; border: \
                    0.5px solid; border-color: rgb(85, 255, 127); min-height: 17px; background-color:\
                    rgb(65, 65, 65);} \
                    QPushButton::pressed {background-color:\
                    rgb(20, 20, 20);} \
                    QComboBox {border-radius: 4px; background-color: rgb(47, 79, 79); border: \
                    0.5px solid; border-color: rgb(85, 255, 127); min-height: 17px; background-color:\
                    rgb(45, 45, 45);} \
                    QLineEdit {border-radius: 4px; border: \
                    0.5px solid; border-color: rgb(85, 255, 127); min-height: 17px; background-color:\
                    rgb(45, 45, 45);} \
                    QTabBar::tab:selected {background-color: rgb(47, 79, 79); border: \
                    0.5px solid; border-color: rgb(85, 255, 127); background-color:\
                    rgb(45, 45, 45); text-decoration: underline;} \
                    QTabBar::tab:hover {background-color: rgb(47, 79, 79); border: \
                    0.5px solid; border-color: rgb(255, 255, 255); background-color:\
                    rgba(80, 80, 80,1);} \
                    QTabBar::tab {min-width: 10px; padding: 2px; background-color:\
                    rgb(45, 45, 45); border: 0.5px; border-color: rgb(230, 230, 230); padding: \
                    5px;}")
        
        #self.ui.modelling_tab.setStyleSheet("QPushButton, QLineEdit, QGroupBox, QComboBox {border-color: rgb(170, 150, 0);}")
        #self.ui.Uvs_tab.setStyleSheet("QPushButton, QLineEdit, QGroupBox, QComboBox {border-color: rgb(170, 150, 0);}")
    '''
   
    def _setOpenFolderIcons(self):
            
        # set selectFile button initial values
        self.ui.getSavePath_btn.setMaximumSize(20 , 20)
        self.ui.getSavePath_btn.setIcon(QtGui.QIcon(":fileOpen.png"))
        self.ui.getSavePath_btn.setIconSize( QtCore.QSize(18, 18) )
        self.ui.getSavePath_btn.setToolTip("Select File")
        
        # set saveAnimPath button initial values
        self.ui.getSaveAnimPath_btn.setMaximumSize(20 , 20)
        self.ui.getSaveAnimPath_btn.setIcon(QtGui.QIcon(":fileOpen.png"))
        self.ui.getSaveAnimPath_btn.setIconSize( QtCore.QSize(18, 18) )
        self.ui.getSaveAnimPath_btn.setToolTip("Select File")