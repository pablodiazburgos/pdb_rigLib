""""
User interface for dream house toolbox kit containing multiple tools 
@author: Pablo Diaz Burgos
"""

# import modules
from PySide2 import QtCore
from PySide2 import QtUiTools
from PySide2 import QtWidgets
from PySide2 import QtGui

from shiboken2 import wrapInstance

import maya.cmds as mc
import maya.OpenMayaUI as omui
import maya.mel as mm

import sys
import os
import webbrowser

from .modelling import makeModelFolders
from .modelling import findSize
from .modelling import meshChecker
from .modelling import geoExporter
from .modelling import geoSnapshot


from .uvs import uvsTools

from .animation import makeAnimFolders
from .animation import animKeyOffset
from .animation import animationExporter
from .animation import animHelpButtons

from .utils import customStyleSheet

packagePath = 'C:/Users/Pablo Diaz Burgos/Documents/maya/pdb_rigLib/toolbox'

if not os.path.exists( packagePath ):
    packagePath = 'C:/Users/DreamAdmin/Documents/maya/pdb_rigLib/toolbox'
    
if packagePath not in sys.path:
    sys.path.append(packagePath)

#packagePath = 'C:\\hive\\Google Drive\\toolbox'    

def maya_main_window():
    
    """
    Return the Maya main window widget as a Python object
    """
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(long(main_window_ptr), QtWidgets.QWidget)

class DreamHouseToolBoxUI(QtWidgets.QDialog):
    
    dlg_instance = None
    
    @classmethod
    def showDialog( cls ):
        if not cls.dlg_instance:
            cls.dlg_instance = DreamHouseToolBoxUI()
            
        if cls.dlg_instance.isHidden():
            cls.dlg_instance.show()
        else:
            cls.dlg_instance.raise_()
            cls.dlg_instance.activateWindow()

    def __init__(self, parent=maya_main_window()):
        super(DreamHouseToolBoxUI, self).__init__(parent)

        self.setWindowTitle("Dream House ToolBox V001")
      
        self.setMaximumSize(100,800)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.CustomizeWindowHint)
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
        
        self.init_ui()
        self.create_layout()
        self.create_connections()
        self.connectSelectIconBtn()
        
        # set default maya units combo box
        defaultMayaUnit = mc.currentUnit( linear= True, q = True, f = True )
        try:
            self.ui.mayaUnits_cbx.setCurrentText(defaultMayaUnit)
        except:
            self.ui.mayaUnits_cbx.setCurrentText("centimeter")
        
        # set status bar default message
        self.statusBar.setStyleSheet("color: white")
        self.statusBar.showMessage( "Dream House ToolBox V001" )
        
        # temp
        #self.helpQTab =  self.ui.extraWidget_tab.help_tab
        #self.ui.extraWidget_tab.hide()
        #self.ui.extraWidget_tab.addTab()
                        
    def init_ui(self):
        
        f = QtCore.QFile(packagePath + "\\ui\\main_ui.ui")
        f.open(QtCore.QFile.ReadOnly)
        
        loader = QtUiTools.QUiLoader()
        self.ui = loader.load(f, parentWidget=None)

        f.close()

    def create_layout(self):
        self.ui.layout().setContentsMargins(6, 6, 6, 6)
        
        # add QtUi to main pyside2 layout
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addWidget( self.ui )
        
        # create statusbar
        self.statusBar = QtWidgets.QStatusBar()
        main_layout.addWidget( self.statusBar )
        
        self.customStyleSheet = customStyleSheet.CustomStyleSheet( self.ui )
                
    def create_connections(self):
        
        #=======================================================================
        # modelling tab  connection
        #=======================================================================
        
        # create model folders connections
        self.makeModelFolders = makeModelFolders.CreateModelFolders( self.ui, self.statusBar )
        self.makeModelFolders.setConnections()
        
        # create size connections
        self.connectSizeGuidesTool = findSize.SizeTool( self.ui, self.statusBar )
        self.connectSizeGuidesTool.setConnections()
        
        # reset geo connections
        self.meshChecker = meshChecker.MeshChecker( self.ui, self.statusBar )
        self.meshChecker.setConnections()
        
        # geometry snapshot connections
        self.geometrySnapshot = geoSnapshot.geometrySnapshot( self.ui, self.statusBar )
        self.geometrySnapshot.setConnections()
        
        # geometry exporter connections
        self.geometryFbxExporter = geoExporter.geometryExporter( self.ui, self.statusBar )
        self.geometryFbxExporter.setConnections()
        
        #=======================================================================
        # uvs tab connections
        #=======================================================================
        self.connectUvsTools = uvsTools.UvsTools( self.ui, self.statusBar )
        self.connectUvsTools.setConnections()
        
        #=======================================================================
        # animation tab connections
        #=======================================================================
        # create model folders connections
        self.makeAnimFolders = makeAnimFolders.CreateAnimFolders( self.ui, self.statusBar )
        self.makeAnimFolders.setConnections()
        
        # animation Key Offset
        self.connectAnimKeyOffset = animKeyOffset.AnimKeyOffset( self.ui, self.statusBar )
        self.connectAnimKeyOffset.setConnections()
        
        
        # animation exporter
        self.connectAnimExporter = animationExporter.AnimationExporter( self.ui, self.statusBar )
        self.connectAnimExporter.setConnections()
        
        # animation help buttons
        self.connectAnimHelpButtons = animHelpButtons.AnimHelpButtons( self.ui, self.statusBar )
        self.connectAnimHelpButtons.setConnections()
        '''
        #=======================================================================
        # help/suggestion button connections
        #=======================================================================
        self.ui.suggestion_btn.clicked.connect(self.suggestionPage)
        self.ui.mayaCommands_btn.clicked.connect( self.mayaCommandsPage )
        
        #self.ui.extraWidget_tab.tabBarDoubleClicked.connect(self.toggleExtraTabVis)
        '''

    def suggestionPage(self):
        
        webbrowser.open(url = 'https://docs.google.com/document/d/1yt9jm5fx_xiEqJ1X6CY6mhyg7NUSujWs4K7WD2M7DR8/edit?usp=sharing', 
                        new = 0, 
                        autoraise = True
                        )
        self.statusBar.setStyleSheet( "color: green" )
        self.statusBar.showMessage( "opening google doc for suggestions" )      
    
    def mayaCommandsPage(self):
        
        webbrowser.open(url = 'https://help.autodesk.com/cloudhelp/2018/ENU/Maya-Tech-Docs/Commands/index.html', 
                        new = 0, 
                        autoraise = True
                        )
        self.statusBar.setStyleSheet( "color: green" )
        self.statusBar.showMessage( "opening Maya Commands help page" )   
    
    def connectSelectIconBtn(self):
      
        # set selectFile button initial values
        self.ui.getModelFoldersPath_btn.setMaximumSize(20 , 20)
        self.ui.getModelFoldersPath_btn.setIcon(QtGui.QIcon(":fileOpen.png"))
        self.ui.getModelFoldersPath_btn.setIconSize( QtCore.QSize(18, 18) )
        self.ui.getModelFoldersPath_btn.setToolTip("Select File")
        
        self.ui.getSavePath_btn.setMaximumSize(20 , 20)
        self.ui.getSavePath_btn.setIcon(QtGui.QIcon(":fileOpen.png"))
        self.ui.getSavePath_btn.setIconSize( QtCore.QSize(18, 18) )
        self.ui.getSavePath_btn.setToolTip("Select File")
        
        self.ui.getGeoSnapshotPath_btn.setMaximumSize(20 , 20)
        self.ui.getGeoSnapshotPath_btn.setIcon(QtGui.QIcon(":fileOpen.png"))
        self.ui.getGeoSnapshotPath_btn.setIconSize( QtCore.QSize(18, 18) )
        self.ui.getGeoSnapshotPath_btn.setToolTip("Select File")
        
        self.ui.getCreateAnimFoldersPath_btn.setMaximumSize(20 , 20)
        self.ui.getCreateAnimFoldersPath_btn.setIcon(QtGui.QIcon(":fileOpen.png"))
        self.ui.getCreateAnimFoldersPath_btn.setIconSize( QtCore.QSize(18, 18) )
        self.ui.getCreateAnimFoldersPath_btn.setToolTip("Select File")