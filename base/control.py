"""
module for making rig controls 
"""
#TODO: check colorIdx problem when is -1 by default, also was giving problem of reference before assignment on build function

import maya.cmds as mc

from ..utils import name
from . import controlShapes

rigCtrlAt = 'animatedCtrl'
rigInternalCtrlAt = 'internalCtrl'

class Control():
    """
    class for building rig control
    """

    def __init__(self,
                 prefix='new',
                 scale=1.0,
                 translateTo='',
                 rotateTo='',
                 moveTo = '',
                 ctrlParent='',
                 shape = 'circle',
                 lockHideChannels = [],
                 defLockHide = ['s','v'],
                 colorIdx = 22,
                 colorName = '',
                 rotOrd = 3,
                 animated = True,
                 noOff = False
                 ):
        """
        :param prefix: str, prefix to name new objects
        :param scale: float, scale value for size of control shapes
        :param translateTo: str, reference object for control position
        :param rotateTo: str, reference object for control orientation
        :param moveTo, str, reference object for control rotation and translation
        :param ctrlParent: str, object to be parent of new control
        :param shape: str, contrl shape type
        :param lockChannels: list( str ), list of channels on controls to be locked and non-keyable
        :param defLockHide: list( str ), list of channels to lock by default , scale and visibility
        :param colorIdx: int, color index of control
        :param colorName: str, set the color to primary, secondary or put a color ex. 'green', 'blue'
        :param rotOrd: int, integer from 1 to 5 options, this would be the default rotate order of the control
        :param animated: bool, by fault true , it means will be used for animation purposes , if false it will be with the suffix "_icl" with means internal control
        :param noOff: bool, if True the offset grp for the control won't be created
        :return None
        """
        # make the scope of all the local args to pass into another function
        localArgs = locals()
        
        # define public member
        self.C = None
        self.Off = None
        
        self._build( localArgs )


    def _build(self, args):

        # define local args
        prefix = args['prefix']
        scale = args['scale']
        translateTo = args['translateTo']
        rotateTo = args['rotateTo']
        moveTo = args['moveTo']
        ctrlParent = args['ctrlParent']
        shape = args['shape']
        lockChannels = args['lockHideChannels']
        defLockHide = args['defLockHide']
        colorIdx = args['colorIdx']
        colorName = args['colorName']
        rotOrd = args['rotOrd']
        animated = args['animated']
        noOff = args['noOff']
        
        # get color id
        side = name.getSide( prefix )
        colorIdx = self._getColorId(side, colorIdx, colorName)
        
        # make the control and offset name
        ctrlName, offsetName = self._makeNames( prefix, animated )
        
        # check if the controls is unique in the scene
        self._checkUniqueCtrlName( ctrlName )
        
        # create the control
        control = self._makeControl( ctrlName, shape, colorIdx, scale )
        self._fixAttributes(control,  defLockHide, lockChannels, rotOrd, animated)
        
        # make control offset and match transforms
        offset = self._makeControlOffset( control, offsetName, noOff )
        self._parentOffset( control, offset, ctrlParent, noOff)
        self._matchTransform(offset, translateTo, rotateTo, moveTo, noOff)
        
        # update instance data
        self.C = control
        self.Off = offset
  
    def _makeNames(self, prefix, animated):
        
        if animated:        
            controlName = prefix + '_ctl'
            offsetName = prefix + 'CtlOffset_grp'
        else:
            controlName = prefix + '_icl'
            offsetName = prefix + 'IclOffset_grp'                
        
        return [ controlName, offsetName ]

    def _getColorId(self, side, colorIdx, colorName):
        
        # define default colorId yellow
        defaultColorIdx = 22 
        
        if colorName == 'blue':
            colorIdx = 6
        if colorName == 'red':
            colorIdx = 13
        if colorName == 'yellow':
            colorIdx = 22
        if colorName == 'darkgreen':
            colorIdx = 26
        if colorName == 'orange':
            colorIdx = 31
        if colorName == 'purple':
            colorIdx = 9
        if colorName == 'lightBlue':
            colorIdx = 18
        if colorName == 'lightRed':
            colorIdx = 20
        if colorName == 'lightOrange':
            colorIdx = 21
        if colorName == 'green':
            colorIdx = 14
        if colorName == 'midGreen':
            colorIdx = 25
        if colorName == 'darkRed':
            colorIdx = 4
       
        # if color name is primary define the color by side
        if colorName == 'primary' or colorName == '':
            if side == 'l':
                colorIdx = 6
            elif side == 'r':
                colorIdx = 13
            else:
                colorIdx = 22
            
        # if color name is secondary define the color by side
        if colorName == 'secondary':
            if side == 'l':
                colorIdx = 18
            elif side == 'r':
                colorIdx = 20
            else:
                colorIdx = 14
        
        return colorIdx
     
    def _checkUniqueCtrlName(self, ctrlName):
        
        matches = mc.ls( ctrlName )
        
        if matches:
            raise Exception('# cannot create the control %s because is not unique in the scene' % ctrlName)

    def _makeControl(self, ctrlName, shape, colorIdx, scale):
        
        # make the curve shape 
        
        if shape == '' or shape == 'circle': control = controlShapes.circle( degree = 3 )
        elif shape == 'circleX': control = controlShapes.circle( normal = 'x' )
        elif shape == 'circleY': control = controlShapes.circle( normal = 'y' )
        elif shape == 'circleZ': control = controlShapes.circle( normal = 'z' )
        elif shape == 'star': control = controlShapes.star()
        elif shape == 'cross': control = controlShapes.cross()
        elif shape == 'foot': control = controlShapes.foot()
        elif shape == 'fist': control = controlShapes.fist()
        elif shape == 'arrow': control = controlShapes.arrow()
        elif shape == 'crown': control = controlShapes.crown()
        elif shape == 'cube': control = controlShapes.cube()
        elif shape == 'cubeOnBase': control = controlShapes.cubeOnBase()
        elif shape == 'cubeOnBaseX': control = controlShapes.cubeOnBaseX()
        elif shape == 'diamond': control = controlShapes.diamond()
        elif shape == 'move': control = controlShapes.move()
        elif shape == 'rotation': control = controlShapes.rotation()
        elif shape == 'singleRotation': control = controlShapes.singleRotation()
        elif shape == 'sphere': control = controlShapes.sphere()
        elif shape == 'spikeCross': control = controlShapes.spikeCross()
        elif shape == 'starSimple': control = controlShapes.starSimple()
        elif shape == 'vis': control = controlShapes.vis()
        elif shape == 'inverseCrown': control = controlShapes.inverseCrown()
        elif shape == 'square': control = controlShapes.square()
        elif shape == 'squareX': control = controlShapes.square( normal = [1, 0, 0] )
        elif shape == 'squareY': control = controlShapes.square()
        elif shape == 'squareZ': control = controlShapes.square( normal = [0, 0, 1] )
        elif shape == 't': control = controlShapes.t()
        elif shape == 'moveSimple': control = controlShapes.moveSimple()
        elif shape == 'triangle': control = controlShapes.triangle()
        
        else: raise( Exception( 'unregistered shape name "%s"' % shape ) )
        
        control = mc.rename( control, ctrlName )
        #=======================================================================
        # put the color in the control shape and adjust scale
        #=======================================================================
        
        for s in mc.listRelatives( control, s = 1 ):
            
            mc.setAttr( control + '.s', scale, scale, scale )
            mc.makeIdentity( control, a = 1, s = 1 )
                
            mc.setAttr( s + '.ove', 1 )
            mc.setAttr( s + '.ovc', colorIdx )
        
        return control
    
    def _fixAttributes(self, control, defLockHide, lockChannels, rotOrd, animated):
        
        # if is for animation create a special attribute
        if animated:
            mc.addAttr( control, ln = rigCtrlAt, dt = 'string' )
        else:
            mc.addAttr( control, ln = rigInternalCtrlAt, dt = 'string' )
        
        
        # check and expose rotation order if need it
        
        if self._exposeRotateOrder( defLockHide, lockChannels ) == 0:
            
            mc.setAttr( '%s.ro' % control, rotOrd, k = True  )
        
        # block attrs
        
        atList = []
        for at in defLockHide + lockChannels:
            if at == 't' or at == 'r' or at == 's':
                for ax in [ 'x', 'y', 'z' ]:
                    atList.append( at + ax )
            else:       
                atList.append ( at )
        
        for attr in atList:
            mc.setAttr( '%s.%s' % ( control, attr ), l = True, k = False, cb = False  )
    
    def _exposeRotateOrder(self, defLockHide, lockChannels):
        
        if 'r' in defLockHide: return 1
        if 'r' in lockChannels: return 1
        
        defLockHideCounter = 0
        lockChannelsCounter = 0
        
        for a in [ 'x', 'y', 'z' ]:
            
            if ( 'r' + a ) in defLockHide: defLockHideCounter += 1
            if ( 'r' + a ) in lockChannels: lockChannelsCounter += 1
            
            if defLockHideCounter == 2 or lockChannelsCounter == 2: return 1
            
        return 0
    
    def _makeControlOffset(self, control, offsetName, noOff):
        
        if noOff: return None
        
        offsetGrp = mc.group(em = True, n = offsetName)
        
        mc.parent( control, offsetGrp )
        
        return offsetGrp
    
    def _parentOffset(self,control, offset, ctrlParent, noOff):
        
        if not ctrlParent or not mc.objExists( ctrlParent ): return
        
        if noOff or not mc.objExists( offset ): mc.parent( control, ctrlParent )
        
        else:
            mc.parent( offset, ctrlParent )

    def _matchTransform(self, offset, translateTo, rotateTo, moveTo, noOff):
        """
        match the control transform to given object , only works if there's a offset grp
        """
        if noOff: return 
        
        if translateTo and mc.objExists(translateTo): mc.delete(mc.pointConstraint( translateTo, offset ) )
        
        if rotateTo and mc.objExists( rotateTo ): mc.delete( mc.orientConstraint( rotateTo, offset ) )

        if moveTo: mc.delete( mc.parentConstraint( moveTo, offset ) )

















