"""
Dream House modelling sanity checker
@author: Pablo Diaz
"""
import pymel.core as pm
import maya.OpenMaya as om
import maya.OpenMayaUI as omui

from PySide2 import QtCore
from PySide2 import QtWidgets

from shiboken2 import wrapInstance

widthSize = 300 * 2
heightSize = 160 * 2

def maya_main_window():
    
    """
    Return the Maya main window widget as a Python object
    """
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(long(main_window_ptr), QtWidgets.QWidget)

class ModelCheckUI(QtWidgets.QDialog):
   
    dlg_instance = None
    
    @classmethod
    def showDialog( cls ):
        if not cls.dlg_instance:
            cls.dlg_instance = ModelCheckUI()
            
        if cls.dlg_instance.isHidden():
            cls.dlg_instance.show()
        else:
            cls.dlg_instance.raise_()
            cls.dlg_instance.activateWindow()

    def __init__(self, parent=maya_main_window()):
        super(ModelCheckUI, self).__init__(parent)

        self.setWindowTitle("Model Sanity Checker")
        
        self.setMinimumSize( widthSize, heightSize )
        self.setMaximumSize(widthSize, heightSize)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.CustomizeWindowHint)
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
        
        
        self.create_widgets()
        self.create_layout()
        self.create_connection()
        
    def create_widgets(self):
        self.check_btn = QtWidgets.QPushButton( "Scene Check" )

        self.printCheckWdg = QtWidgets.QPlainTextEdit()
        self.printCheckWdg.setReadOnly(True)
        self.printCheckWdg.setStyleSheet(" QPlainTextEdit {border-radius: 8px; border: \
                    0.5px solid; border-color: rgb(255, 255, 255); min-height: 17px; background-color:\
                    rgb(45, 45, 45);}" )
        
    def create_layout(self):
        buttonLayout = QtWidgets.QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget( self.check_btn )
        
        printCheckLayout = QtWidgets.QVBoxLayout()
        printCheckLayout.setContentsMargins(2, 2, 2, 2)
        printCheckLayout.setSpacing( 3 )
        printCheckLayout.setAlignment( QtCore.Qt.AlignTop )
        printCheckLayout.addWidget( self.printCheckWdg )
        
        mainLayout = QtWidgets.QVBoxLayout(self)
        mainLayout.setContentsMargins( 4, 4, 4, 4 )
        mainLayout.addLayout( printCheckLayout )
        mainLayout.addLayout( buttonLayout )
        mainLayout.addSpacing(4)
        
    def create_connection(self):
        self.check_btn.clicked.connect( self.modelSceneCheck )
        
    def modelSceneCheck(self):
        self.printCheckWdg.clear()
        
        # Extra cameras check
        self.printCheckWdg.appendHtml( ModelCheck().checkExtraCameras() )
        
        # Clashing names
        self.printCheckWdg.appendHtml( ModelCheck().checkClashingNames() )
        
        # Unknown nodes
        self.printCheckWdg.appendHtml( ModelCheck().checkUnknownNodes() )
        
        # Object Sets
        self.printCheckWdg.appendHtml( ModelCheck().checkObjectSets() )
        
        # Display Layers
        self.printCheckWdg.appendHtml( ModelCheck().checkDisplayLayers() )
        
        # Name Spaces
        self.printCheckWdg.appendHtml( ModelCheck().checkNameSpaces() )
        
        # NonZero transforms
        self.printCheckWdg.appendHtml( ModelCheck().checkNonZeroTfms() )
        
        # History
        self.printCheckWdg.appendHtml( ModelCheck().checkHistory() )
        
        # Suffix
        self.printCheckWdg.appendHtml( ModelCheck().checkSuffix() )
        
        # Animated objects
        self.printCheckWdg.appendHtml( ModelCheck().checkAnimatedTfms() )
        
        # Unassigned shaders
        #self.printCheckWdg.appendHtml( ModelCheck().checkUnassignedShaders() )
        
        print "working ..."
        
#==============================================================================
# logic
#==============================================================================

class ModelCheck():

    

    def __init__(self):
        self.fontSize = 15
    
    def generateHtmlString(self, showString, objectList):
        return '<p style="font-size:{0}px;color:{1};">{2}: {3} </p>'.format( self.fontSize, self.getHtmlColor( objectList ), showString, objectList )
    
    def getHtmlColor(self, returnList):
        if returnList: 
            return 'Tomato'
        else:
            return 'Green'
    
    def checkExtraCameras(self):
        extraCam = [ str( cam.getParent().name() ) for cam in pm.ls(type = 'camera') if not cam.getStartupCamera() ]
        
        showString = 'Extra Cameras'
        
        return self.generateHtmlString(showString, extraCam)
    
    def checkUnknownNodes(self):
        unkownNodes = [ str( ukNode.name() ) for ukNode in pm.ls( type = 'unknown' ) ]
        
        showString = 'Unknown Nodes'
        
        return self.generateHtmlString(showString, unkownNodes)

    def checkClashingNames(self):
        clashingNames = list( set( [str( o.name().split('|')[-1] ) for o in pm.ls() if '|' in o.name() ] ) )
        
        showString = 'Clashing Names'
        
        return self.generateHtmlString(showString, clashingNames)

    def checkObjectSets(self):
        defaultObjectSets = ['defaultLightSet', 'defaultObjectSet']
        
        objectSets = [ str( node.name() ) for node in  pm.ls(type = 'objectSet') if node.nodeType() == 'objectSet' and node.name() not in defaultObjectSets ]
        
        showString = 'Object Sets'
        
        return self.generateHtmlString( showString, objectSets )


    def checkDisplayLayers(self):
        defaultDisplayLayers = ['defaultLayer']
        
        displayLayers = [ str( node.name() ) for node in  pm.ls(type = 'displayLayer') if node.nodeType() == 'displayLayer' and node.name() not in defaultDisplayLayers ]
        
        showString = 'Display Layers'
        
        return self.generateHtmlString( showString, displayLayers )
    
    def checkNameSpaces(self):
        defaultNameSpaces = ['UI', 'shared']
        
        nameSpaces = [ str( nameSpace ) for nameSpace in pm.namespaceInfo(listOnlyNamespaces=True, recurse=True) if nameSpace not in defaultNameSpaces ]

        showString = 'Name Spaces'
        
        return self.generateHtmlString( showString, nameSpaces )
        
    def checkNonZeroTfms(self):
        
        allTfms = list( self._getAllSceneGeos() + self._getSceneGroups() )
        
        showString = 'NonZero Transforms'
        
        nonZeroTfs = []
        
        for tfm in allTfms:
            
            isDefaultVal = True
            
            if list( tfm.getTranslation() ) != [0, 0, 0]: isDefaultVal = False
            if list( tfm.getRotation() ) != [0, 0, 0]: isDefaultVal = False
            if list( tfm.getScale() ) != [1, 1, 1]: isDefaultVal = False
            
            if not isDefaultVal:
                nonZeroTfs.append( str( tfm.name() ) )
        
        return self.generateHtmlString( showString, nonZeroTfs )
    
    def checkHistory(self):
        
        showString = 'History'
        
        historyGeo = [ str( tfm.name() ) for tfm in self._getAllSceneGeos() if len( tfm.history() ) > 1 ]
        
        return self.generateHtmlString( showString, historyGeo )
    
    def checkSuffix(self):
        
        showString = 'Suffix Error'
        
        suffixError = []
        
        # check geometry suffix
        suffixError.extend( [ str( tfm.name() ) for tfm in self._getAllSceneGeos() if not tfm.name().endswith('_geo') ] )
        
        # check groups suffix
        suffixError.extend( [ str( tfm.name() ) for tfm in self._getSceneGroups() if not tfm.name().endswith('_grp') ] )

        return self.generateHtmlString( showString, suffixError )
        
    def checkAnimatedTfms(self):
        
        showString = 'Animated Objects'
        
        animatedTfms = list ( set( [ str( animCrv.destinations()[0].name() ) for animCrv in pm.ls(type = 'animCurve') ] ) )
        
        return self.generateHtmlString( showString, animatedTfms )

    def checkUnassignedShaders(self):
        
        showString = 'Unassigned Shaders'
        
        sceneGeo = self._getAllSceneGeos()
        
        sceneShaders = pm.ls(mat = True)[2:]
        
        usedShaders = [ geo.getShape().outputs(type = pm.nt.ShadingEngine)[0].inputs()[0] for geo in sceneGeo ]
        
        unAssignShaders = [ str( shd ) for shd in sceneShaders if shd not in usedShaders ]
        
        return self.generateHtmlString( showString, unAssignShaders )
        
    def _getAllSceneGeos(self):
        
        allTfms = pm.ls(type = 'transform')
        sceneGeos = []
        
        for tfm in allTfms:
            
            if tfm.getShapes() and tfm.getShapes()[0].nodeType() == 'mesh' :
                
                sceneGeos.append( tfm )
        
        return sceneGeos

    
    def _getSceneGroups(self):
        
        allTfms = pm.ls(type = 'transform')
        
        sceneGrps  = []
        
        for tfm in allTfms:
            if not tfm.getShapes() and tfm.nodeType() == "transform":
                sceneGrps.append( tfm )
                
        return sceneGrps

    

    












        