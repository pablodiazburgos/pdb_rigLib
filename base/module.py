"""
Class for make every rig module and parent into the base structure
"""

import maya.cmds as mc


sceneObjectType = 'rig'

from . import control

from ..utils import attribute
from ..utils import anim
from ..utils import connect
from ..utils import name

rigModuleNameAt = 'rigModuleName'
controlSectionVisAt = 'controlVis'
moduleVisSuffixAt = 'Vis'
controlVisAt = 'controlVis'
mainCtrlVisAt = 'mainCtrlVis'
primaryCtrlVisAt = 'primaryCtrlVis'

ikFkSwitch = False  # False value will make float blend between IK / FK, True will make boolean switch


class Module():

    """
    class for building module rig structure
    """
    
    # add class variables
    
    rigModuleNameAt = 'rigModuleName'
    rigModulePartAt = 'rigModulePart'
    fkIkAt = 'fkIk'
    customTogglePart = 'custom_toggle'
    
    
    def __init__(
                self,
                prefix = 'new',
                baseObj = None
                ):
        """
        :param prefix: str, prefix to name new objects
        :param baseObj: instance, instance of base class
        :return instance, module object instance
        
        module group structure:
        
        Main
        L____ControlVis - controls and their offset groups - also used to turn off visibility of module controls
                L____ Controls - parent of controls and their offsets
        L____ Joints - main place to put joints, some of them can be in parts as well
        L____ Scale - group measuring realtive scale of module
        L____ Parts - any other objects
                L____ partsNt Nt means No transform, parent ik handles , curves or deformed geo here
                L____ LocalSpace - group which xform represents local space of module
                L____ BodySpace - group which xform represents creature body space
                L____ GlobalSpace - group which xform represents creature global space
        L____ Properties - group holding settings sub groups
                L____ Toggle - group holding IkFk and Space Switch attributes
                L____ - group holding Settings attributes ( not keyable )
        """
        
        # initialize module members to pass class __init__()
        
        self.Main = None
        self.ControlsVis = None
        self.Controls = None
        self.Joints = None
        self.Parts = None
        self.PartsNt = None
        self.LocalSpace = None
        self.BodySpace = None
        self.GlobalSpace = None
        self.Toggle = None
        self.Scale = None
        self.Settings = None
        self.ToggleOrig = None  # member to store original toggle group in case Custom Toggle object is initialised
        
        #=======================================================================
        #  build module
        #=======================================================================
        
        self._createGroups( prefix ) # create sub groups and define public members
        self._addAttributes( prefix )
        self._sortGroups()
        self._setAndConnectAttrs()

    #===========================================================================
    #  PUBLIC METHODS
    #===========================================================================
    
    def parent(self, baseRigData = None, customParent = None):
        
        '''
        convenience function to parent module to correct group under main rig

        :param baseRigData: instance, dictionary instance from base.build(), top rig dictionary with information about module parent object
        :param customParent: str, custom parent group, if this is used then baseRigData is ignored
        :return: None
        '''
        
        if baseRigData:
            
            parentObj = baseRigData['modulesGrp']
        
        elif customParent:
            
            parentObj = customParent
        
        
        try:
            
            mc.parent( self.Main, parentObj )
        
        except:
            
            pass
    
    def connect( self, baseRigData = None, visCtrlName = '', ctrlVisDriver = '' ):
        
        '''
        make connections to module from external attributes
        this makes connections easy one step and also more standard
        
        NOTE:
            
            - more driver plugs can be added, now there is just visibility
            - if baseRigData is provided, module creates visibility attribute on that baseRig
                 vis control and connects it to the module
        
        states of driver attribute:
        0 - no visibility
        1 - main
        
        :param baseRigData: class instance base.build(), dictionary used to find top rig plugs to connect to all module parts (mainVis, Skeleton etc.) 
        :param visCtrlName: str, optional if baseRigData is None, name of Vis control, this is currently 'vis_ctl'
        :param ctrlVisDriver: str, name of plug ("object.attribute") to drive control visibility, int/enum type of range 0-2
        :return: None
        '''
        
        if baseRigData:
            
            visCtrlName = baseRigData['visCtrl'].C
        
        if visCtrlName:
            
            # connect main visibility
            
            mc.connectAttr( visCtrlName + '.jointVis', self.Main + '.skeletonVis', f = 1 )
            mc.setAttr( self.Joints + '.ove', 1 )
            mc.connectAttr( visCtrlName + '.jointDispType', self.Joints + '.ovdt', f = 1 )
            
            # first make main section
            
            if not mc.objExists( visCtrlName + '.' + controlSectionVisAt ):
                
                attribute.addSection( visCtrlName, 'controlVis' )
            
            # add module vis attribute
            
            moduleName = mc.getAttr( self.Main + '.' + Module.rigModuleNameAt )
            moduleVisAt = moduleName + moduleVisSuffixAt
            
            if not mc.objExists( visCtrlName + '.' + moduleVisAt ):
                
                mc.addAttr( visCtrlName, ln = moduleVisAt, at = 'enum', enumName = 'off:prim', k = 1, dv = 1 )
            
            mc.setAttr( visCtrlName + '.' + moduleVisAt, cb = 1 )
            
            # now connect module to driving visibility control
            
            anim.setDrivenKey( visCtrlName + '.' + controlVisAt, self.Main + '.' + mainCtrlVisAt, [0, 1], [0, 1] )
            anim.setDrivenKey( visCtrlName + '.' + moduleVisAt, self.Main + '.' + primaryCtrlVisAt, [0, 1], [0, 1] )
            
        
        if mc.objExists( ctrlVisDriver ):
            
            anim.setDrivenKey( ctrlVisDriver, self.Main + '.' + primaryCtrlVisAt, [0, 1], [0, 1] )
    
    def connectPrimaryVis( self, obj ):
        
        '''
        connect primary visibility from module to object
        
        :param obj: str, object to have its visibility driven by module
        :type obj: str
        :return: None
        '''
        
        connect.disconnect( obj + '.v' )
        mc.connectAttr( self.Main + '.' + primaryCtrlVisAt, obj + '.v', f = 1 )
        
    def connectPartsVis( self, obj ):
        
        '''
        connect parts visibility from module to object (help joints, locators etc.)
        
        :param obj: str, object to have its visibility driven by module
        :return: None
        '''
        
        mc.connectAttr( self.Main + '.partsVis', obj + '.v', f = 1 )
    
    def connectSkeletonVis( self, obj ):
        
        '''
        connect skeleton visibility from module to object (help joints, locators etc.)
        
        :param obj: str, object to have its visibility driven by module
        :return: None
        '''
        
        mc.connectAttr( self.Main + '.skeletonVis', obj + '.v', f = 1 )

    def connectIkFk( self, objAttr, reversed = False ):
        
        '''
        connect IkFk from module to object attribute (visibility, ikBlend etc.)
        Object attribute should be in plug format: <OBJECT.ATTRIBUTE>
        
        :param objAttr: str, object attribute to be driven by module
        :return: None
        '''
        
        self.addIkFkAt()
        
        if reversed:
            
            objectName = mc.ls( objAttr, o = 1 )[0]
            prefix = name.removeSuffix( objectName )
            
            reverseNode = mc.createNode( 'reverse', n = prefix + 'IkFk_rev' )
            mc.connectAttr( reverseNode + '.ox', objAttr )
            objAttr = reverseNode + '.ix'
        
        mc.connectAttr( self.Toggle + '.' + Module.fkIkAt, objAttr, f = 1 )

    def addIkFkAt( self ):
        
        '''
        add fkIk enum switch attribute with convention naming
        
        default value is set to 1 for IK, which seems to be used most often
        '''
        
        # check if attribute was not already added by connectFkIk function
        if not mc.objExists( self.Toggle + '.' + Module.fkIkAt ):
            
            if ikFkSwitch:
                
                mc.addAttr( self.Toggle, ln = Module.fkIkAt, at = 'enum', enumName = 'fk:ik', k = 1, min = 0, max = 1, dv = 1 )
            
            else:
                
                mc.addAttr( self.Toggle, ln = Module.fkIkAt, at = 'float', k = 1, min = 0, max = 1, dv = 1 )
        
        return self.Toggle + '.' + Module.fkIkAt

    def connectScale( self, obj ):
        
        '''
        connect module scale to given object
        
        :param obj: str, object to have its scale driven by module
        :return: None
        '''
        
        for axis in ['x', 'y', 'z']: mc.connectAttr( self.Main + '.moduleScale', obj + '.s' + axis, f = 1 )

    def connectScaleToPlug( self, objectplug ):
        
        '''
        connect module scale to given plug, <OBJECT.ATTRIBUTE>
        
        :param objectplug: str, object plug to have its scale driven by module
        :return: None
        '''
        
        mc.connectAttr( self.Main + '.moduleScale', objectplug, f = 1 )        

    def getModuleScalePlug( self ):
        
        '''
        return name of module instance scale plug <OBJECT.ATTRIBUTE>
        
        :return: str
        '''
        
        return self.Main + '.moduleScale'

    def getIkFkAt( self ):
        
        '''
        return name of IkFk attribute (will be made if not existing)
        
        :return: str
        '''
        
        self.addIkFkAt()
        
        return self.Toggle + '.' + Module.fkIkAt

    def customToggleObject( self, customToggleObject ):
        
        """
        define custom Toggle object, which will be used in this module instance
        instead of usual default Toggle group
        For example, this can be a hand switch control
        
        :param customToggleObject: str, name of custom toggle object
        :return: None
        """
        
        self.ToggleOrig = self.Toggle
        self.Toggle = customToggleObject
        self._addModuleIDs( customToggleObject, Module.customTogglePart )
        
        # connect Ik Fk
        if mc.objExists( self.ToggleOrig + '.' + Module.fkIkAt ):
            
            self.addIkFkAt()
            mc.connectAttr( self.Toggle + '.' + Module.fkIkAt, self.ToggleOrig + '.' + Module.fkIkAt )


    #===========================================================================
    #  PRIVATE METHODS
    #===========================================================================

    def customToggleObject( self, customToggleObject ):
        
        """
        define custom Toggle object, which will be used in this module instance
        instead of usual default Toggle group
        For example, this can be a hand switch control
        
        :param customToggleObject: str, name of custom toggle object
        :return: None
        """
        
        self.ToggleOrig = self.Toggle
        self.Toggle = customToggleObject
        self._addModuleIDs( customToggleObject, Module.customTogglePart )
        
        # connect Ik Fk
        if mc.objExists( self.ToggleOrig + '.' + Module.fkIkAt ):
            
            self.addIkFkAt()
            mc.connectAttr( self.Toggle + '.' + Module.fkIkAt, self.ToggleOrig + '.' + Module.fkIkAt )
        

    def _createGroups(self, prefix):
        
        self.Main = mc.group( em = 1, n = prefix + 'Module_grp' )
        self.ControlsVis = mc.group( em = 1, n = prefix + 'ControlsVis_grp' )
        self.Controls = mc.group( em = 1, n = prefix + 'Controls_grp' )
        self.Joints = mc.group( em = 1, n = prefix + 'Joints_grp' )
        self.Parts = mc.group( em = 1, n = prefix + 'Parts_grp' )
        self.PartsNt = mc.group( em = 1, n = prefix + 'PartsNoTrans_grp' )
        self.LocalSpace = mc.group( em = 1, n = prefix + 'LocalSpace_grp' )
        self.BodySpace = mc.group( em = 1, n = prefix + 'BodySpace_grp' )
        self.GlobalSpace = mc.group( em = 1, n = prefix + 'GlobalSpace_grp' )
        self.Toggle = mc.group( em = 1, n = prefix + 'Toggle_grp' )
        self.ToggleOrig = self.Toggle
        self.Scale = mc.group( em = 1, n = prefix + 'Scale_grp' )
        self.Settings = mc.group( em = 1, n = prefix + 'Settings_grp' )
        self.Properties = mc.group( em = 1, n = prefix + 'Properties_grp' )
        
        self._moduleGrps = [
                            self.Main, self.Controls, self.ControlsVis, self.Joints, self.Parts,
                            self.PartsNt, self.LocalSpace, self.BodySpace, self.GlobalSpace,
                            self.Toggle, self.Scale, self.Settings, self.Properties
                            ]   
        
        self._moduleGrpNames = [ 'main', 'controls', 'controlsVis', 'skeleton', 'parts', 'partsNt',
                                'localSpace', 'bodySpace', 'globalSpace',
                                'toggle', 'scale', 'settings', 'properties' ]        
        
    def _addAttributes(self, prefix):
        
        # module IDs
        
        for modGrp, modGrpType in zip( self._moduleGrps, self._moduleGrpNames ):
            
            self._addModuleIDs( modGrp, modGrpType )
        
        # message interface
        
        mc.addAttr( self.Main, ln = 'controls', at = 'message', multi = 1 )
        
        # module interface        
        
        mc.addAttr( self.Main, ln = Module.rigModuleNameAt, dt = 'string' )
        mc.setAttr( self.Main + '.' + Module.rigModuleNameAt, prefix, typ = 'string', l = 1 )
        mc.addAttr( self.Main, ln = 'moduleScale', at = 'double', k = 1 )
        
        mc.addAttr( self.Main, ln = mainCtrlVisAt, at = 'bool', k = 1, dv = True )
        mc.addAttr( self.Main, ln = primaryCtrlVisAt, at = 'bool', k = 1, dv = True )
        mc.addAttr( self.Main, ln = 'skeletonVis', at = 'bool', k = 1, dv = False )
        mc.addAttr( self.Main, ln = 'partsVis', at = 'bool', k = 1, dv = False )

    def _addModuleIDs(self, object, moduleID ):
        
        mc.addAttr( object, ln = Module.rigModulePartAt, dt = 'string' )
        mc.setAttr( object + '.' + Module.rigModulePartAt, moduleID, type = 'string', l = True )
        
    def _sortGroups(self):
        
        mc.parent( self.ControlsVis, self.Main )
        mc.parent( self.Controls, self.ControlsVis )
        mc.parent( self.Joints, self.Main )
        mc.parent( self.Parts, self.Main )
        mc.parent( self.PartsNt, self.Parts )
        mc.parent( self.LocalSpace, self.Parts )
        mc.parent( self.BodySpace, self.Parts )
        mc.parent( self.GlobalSpace, self.Parts )
        mc.parent( self.Properties, self.Main )
        mc.parent( self.Settings, self.Properties )
        mc.parent( self.Toggle, self.Properties )
        mc.parent( self.Scale, self.Main )
        
    def _setAndConnectAttrs(self):
        
        mc.setAttr( self.Parts + '.v', 0 )
        mc.setAttr( self.PartsNt + '.it', 0, l = True )
        mc.setAttr( self.Scale + '.it', 0, l = 1 )
        attribute.lockHideTransformVis( self.Settings )
        attribute.lockHideTransformVis( self.Toggle )
        
        mc.scaleConstraint( self.Main, self.Scale )
        mc.connectAttr( str( self.Scale ) + '.sx', str( self.Main ) + '.moduleScale' )
        
        mc.connectAttr( self.Main + '.' + mainCtrlVisAt, self.ControlsVis + '.v' )
        mc.connectAttr( self.Main + '.' + primaryCtrlVisAt, self.Controls + '.v' )
        mc.connectAttr( self.Main + '.skeletonVis', self.Joints + '.v' )
        mc.connectAttr( self.Main + '.partsVis', self.Parts + '.v' )
        
        
        
        
        
        