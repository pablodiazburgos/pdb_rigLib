"""
Module to switch ik and fk with out any pop
"""

import maya.cmds as mc
import maya.OpenMaya as om
import maya.OpenMayaUI as omui

from PySide2 import QtCore
from PySide2 import QtWidgets

from shiboken2 import wrapInstance


widthSize = 150
heightSize = 80


def switch( pvOffset = 0.8 ):
    
    # define items
    ikFkAttr = 'fkIkSnapable'
    fkControls = []
    
    # list all the selected items
    itemsSelection = mc.ls( sl = True, type = 'transform' )
    for item in itemsSelection:
        
        # check if selection is a snapable control
        userAttrs = mc.listAttr( item, ud = True )
        if not ikFkAttr in userAttrs:
            print '# No {} attribute found in {} ... skipping '.format( ikFkAttr, item )
            continue
        
        # define fk-ik snap items
        
        # fk joints
        upperFkJnt = mc.listConnections( item + '.upperFkJnt' )[0]
        midFkJnt = mc.listConnections( item + '.midFkJnt' )[0]
        endFkJnt = mc.listConnections( item + '.endFkJnt' )[0]
        
        # fk controls
        upperFkControl = mc.listConnections( item + '.upperFkControl' )[0]
        midFkControl = mc.listConnections( item + '.midFkControl' )[0]
        endFkControl = mc.listConnections( item + '.endFkControl' )[0]
        
        # fk joints
        upperIkJnt = mc.listConnections( item + '.upperIkJnt' )[0]
        midIkJnt = mc.listConnections( item + '.midIkJnt' )[0]
        endIkJnt = mc.listConnections( item + '.endIkJnt' )[0]
        
        # ik controls
        ikControl = mc.listConnections( item + '.ikControl' )[0]
        pvControl = mc.listConnections( item + '.ikPvControl' )[0]
        
        # snap ref loc
        snapRefLoc = mc.listConnections( item + '.snapLoc' )[0]
 
        
        # get fk-ik state
        toggleState = mc.getAttr( item + '.fkIk' )
        
        if toggleState != 0 and toggleState != 1:
            print '# {} fkIk attribute must be  0 or 1 ... cannot be an inbetween value ... skipping'.format( item )
            continue
        '''
        # get time values
        currentFrame = mc.currentTime( q = True )
        prevFram = currentFrame - 1.0
        '''
        # make snap from fk to ik
        if toggleState == 0:
            
            # get pv position
            pvPos = _findPoleVectorPosition(topJnt = upperFkJnt, midJnt = midFkJnt, endJnt = endFkJnt, posOffset = pvOffset)
            
            mc.xform( pvControl, ws = True, t = ( pvPos['position'][0], pvPos['position'][1],  pvPos['position'][2] ) )
            
            posCons = mc.pointConstraint( endFkJnt, ikControl )
            rotCon = mc.orientConstraint( snapRefLoc, ikControl )
            
            mc.setKeyframe( ikControl )
            mc.setKeyframe( pvControl )
            
            mc.delete( posCons, rotCon )
            '''
            # go to previous frame and make key frames
            mc.currentTime( prevFram, e = True )
            mc.setKeyframe( item, at = '.fkIk' )

            # go back to current frame and make the switch from fk to ik
            mc.currentTime( currentFrame, e = True )
            
            mc.setAttr( item + '.fkIk', 1 )
            mc.setKeyframe( item, at = '.fkIk' )
            '''
            mc.setAttr( item + '.fkIk', 1 )
            
            mc.select( item )
                    
        # make snap from ik to fk
        if toggleState == 1:
            
            # move fk controls to ik joints position
            for refRot, fkCtrl in zip( [ upperIkJnt, midIkJnt, endIkJnt ], [ upperFkControl, midFkControl, endFkControl ] ):
                
                oriCons = mc.orientConstraint( refRot, fkCtrl )
                mc.setKeyframe( fkCtrl )
                mc.delete( oriCons )
            '''
            # go to previous frame and make key frames
            mc.currentTime( prevFram, e = True )
            mc.setKeyframe( item, at = '.fkIk' )

            # set keyframes
            mc.setAttr( item + '.fkIk', 0 )
            mc.setKeyframe( item, at = '.fkIk' )
            '''
            mc.setAttr( item + '.fkIk', 0 )
            
def _findPoleVectorPosition( topJnt, midJnt, endJnt, posOffset = 2 ):
    
    """
    find the position for pole vector
    :param topJnt: str, top joint of chain to get pv position (e.g hip/shoulder)
    :param midJnt: str, mid joint of chain to get pv position (e.g knee/elbow)
    :param endJnt: str, end join of the chain to get pv position (e.g foot/hand)
    :return dictionary, with position values
    """
    # get inital vectors
    mid = mc.xform(midJnt ,q= 1 ,ws = 1,t =1 )
    midV = _makeMVector( values = (mid[0] ,mid[1],mid[2]) )
    
    startEnd = _from2Objects( topJnt, endJnt, normalized = True )
    startMid = _from2Objects( topJnt, midJnt, normalized = True )
    
    # create vector projection
    dotP = startMid * startEnd
    proj = float(dotP) / float(startEnd.length())
    startEndN = startEnd.normal()
    projV = startEndN * proj
    
    arrowV = startMid - projV
    arrowV*= posOffset * 200
    finalV = arrowV + midV
    
    pos = [ finalV.x, finalV.y, finalV.z ]
    
    return {
            'position': pos,
            }
            
def _makeMVector( values = [0.0, 0.0, 0.0] ):
    
    '''
    :summary: wrapper to make MVector instance from list of floats
    :param values: list(float, float, float) 3 numbers to make vector
    :type values: list of floats     
    
    :return: OpenMaya.MVector
    '''
    
    return om.MVector( values[0], values[1], values[2] )
            
def _from2Objects( objA, objB, normalized = True ):
    
    '''
    :param objA: str, first object
    :param objB: str, second object
    :param normalized: bool, optional, normalize resulting vector
    :return: list of 3 floats
    
    make vector using world positions of 2 given objects
    NOTE: order of passed objects matters - object B is the one "more far" or "later in time"
    '''
    
    avect = _makeMVector( _getPositionFromObj( objA ) )
    bvect = _makeMVector( _getPositionFromObj( objB ) )
    
    resvect = bvect - avect
    
    if normalized:
        
        resvect.normalize()
    
    
    return resvect

def _getPositionFromObj( obj ):
    
    """
    get world position from reference object
    
    :param obj: str, name of reference object
    :return: str, name of group
    """
    
    grp = mc.group( n = obj + '_ref_grp', em = True )
    mc.delete( mc.parentConstraint( obj, grp ) )
    pos = mc.xform( grp, q = 1, t = 1, ws = 1 )
    mc.delete( grp )
    
    return pos

def maya_main_window():
    
    """
    Return the Maya main window widget as a Python object
    """
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(long(main_window_ptr), QtWidgets.QWidget)

class ikFkSnapUI(QtWidgets.QDialog):
   
    dlg_instance = None
    
    @classmethod
    def showDialog( cls ):
        if not cls.dlg_instance:
            cls.dlg_instance = ikFkSnapUI()
            
        if cls.dlg_instance.isHidden():
            cls.dlg_instance.show()
        else:
            cls.dlg_instance.raise_()
            cls.dlg_instance.activateWindow()

    def __init__(self, parent=maya_main_window()):
        super(ikFkSnapUI, self).__init__(parent)

        self.setWindowTitle("pdb Ik-Fk Snap v001")
        
        self.setMinimumSize( widthSize, heightSize )
        self.setMaximumSize(widthSize, heightSize)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.CustomizeWindowHint)
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
        
        self.create_widgets()
        self.create_layout()
        self.create_connection()
        
    def create_widgets(self):
        self.switchBtn = QtWidgets.QPushButton( "Ik-Fk Switch" )
        self.switchBtn.setFixedHeight( 30 )
        
        self.pvOffsetDoubleSpin = QtWidgets.QDoubleSpinBox()
        self.pvOffsetDoubleSpin.setFixedWidth( 70 )
        self.pvOffsetDoubleSpin.setValue(0.8)
        self.pvOffsetDoubleSpin.setSingleStep( 0.2 )
        self.pvOffsetDoubleSpin.setRange( 0.0, 10.0 )
        
    def create_layout(self):
        formLayout = QtWidgets.QFormLayout()
        formLayout.addRow("pvOffset:", self.pvOffsetDoubleSpin)
        
        
        mainLayout = QtWidgets.QVBoxLayout(self)
        mainLayout.addLayout( formLayout )
        mainLayout.addWidget( self.switchBtn )
        
    def create_connection(self):
        self.switchBtn.clicked.connect( self.ikFkSwitch )

    def ikFkSwitch(self):
        pvOffVal = self.pvOffsetDoubleSpin.value()
        switch(pvOffset = pvOffVal)
