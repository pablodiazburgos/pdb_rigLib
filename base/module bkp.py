"""
Class for make every rig module and parent into the base structure
"""

import maya.cmds as mc

sceneObjectType = 'rig'

import control


class Module():

    """
    class for building module rig structure
    """

    def __init__(
                self,
                prefix = 'new',
                baseObj = None
                ):
        """
        :param prefix: str, prefix to name new objects
        :param baseObj: instance of base.module.Base class
        :return None
        """

        self.topGrp = mc.group( n = prefix + 'ModuleGrp', em = 1 )

        self.controlsGrp = mc.group( n = prefix + 'ControlsGrp', em = 1, p = self.topGrp )
        self.jointsGrp = mc.group( n = prefix + 'JointsGrp', em = 1, p = self.topGrp )
        self.partsGrp = mc.group( n = prefix + 'PartsGrp', em = 1, p = self.topGrp )
        self.partsNoTransGrp = mc.group( n = prefix + 'PartsNoTransGrp', em = 1, p = self.topGrp )

        mc.hide( self.partsGrp, self.partsNoTransGrp )

        mc.setAttr(self.partsNoTransGrp + '.it', 0, l = 1)

        # parent module

        if baseObj:

            mc.parent( self.topGrp, baseObj.modulesGrp )

