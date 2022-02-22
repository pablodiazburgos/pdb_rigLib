"""
base module to rig base hierarchy and connections
@category: Rigging
@author: Pablo Diaz Burgos
"""

import maya.cmds as mc

from utils import attribute
from utils import name
from utils import anim


import control
import module

controlVisAt = 'controlVis'

# TODO: add rig sets
# TODO: add comment for build function

def build(
        headJnt,
        topHeadObj = '',
        assetName = 'new',
        offsetAboveHeadY = None,
        scale = 1.0,
        doCheckClashingNames = True
        ):

    # checks if there is clashing names
    if doCheckClashingNames:
        checkClashingNames()
    
    # define model group
    modelGrp = assetName + '_model_grp'
    
    # build groups
    groupsData = _makeGroups( assetName, modelGrp )
    
    # build base controls
    if not offsetAboveHeadY: offsetAboveHeadY = scale * 10
    controlsData = _buildControls( groupsData['topGrp'], headJnt, topHeadObj, scale, offsetAboveHeadY )
    
    # parent all the created groups
    _parentAll( groupsData, controlsData )
    
    # add attributes 
    _addAttributes( controlsData, groupsData )
    
    return {
           'groupsData': groupsData,
           'controlsData': controlsData,
           'modelGrp':groupsData['assetModelGrp'],
           'mainGrp':groupsData['topGrp'],
           'modulesGrp':groupsData['baseModulesGrp'],
           'jointsGrp':groupsData['baseJointsGrp'],
           'baseControlsGrp':groupsData['baseCtrlsGrp'],
           'baseNoTransGrp':groupsData['baseNoTransGrp'],
           'global1Ctrl':controlsData['global1Ctrl'],
           'global2Ctrl':controlsData['global2Ctrl'],
           'visCtrl':controlsData['visCtrl']
            }
    
def checkClashingNames():
    
    clashedNames = name.checkClashingNames()
    
    if clashedNames:
        print "# Clashing names found in %s" % clashedNames
        raise Exception( "# Clashing names may cause problems to build the rig, please see the list above and fix it" )

def _makeGroups( assetName, modelGrp ):
    """
    make the base groups for the rig
    """
    topGrp = mc.group( n = '%s_rig_grp' % assetName, em = True )
    baseCtrlsGrp = mc.group( n = 'baseControls_grp', em = True)
    baseModulesGrp = mc.group( n = 'modules_grp', em = True)
    baseJointsGrp = mc.group( n = 'joints_grp', em = True)
    baseNoTransGrp = mc.group( n = 'baseNoTrans_grp', em = True)
    
    if mc.objExists( modelGrp ): 
        assetModelGrp = modelGrp
    else:
        assetModelGrp = mc.group( n = 'assetModel_grp', em = True)
    
    mc.setAttr( baseNoTransGrp + '.it', 0, l = True )
    
    attribute.lockHideTransformVis(topGrp)
    #attribute.lockHideTransformVis(assetModelGrp, s = True)
    
    return{
        'topGrp':topGrp,
        'baseCtrlsGrp':baseCtrlsGrp,
        'baseModulesGrp':baseModulesGrp,
        'baseJointsGrp':baseJointsGrp,
        'baseNoTransGrp':baseNoTransGrp,
        'assetModelGrp':assetModelGrp
        }
    
def _buildControls(topGrp, headJnt, topHeadObject, scale, offsetAboveHeadY):
    
    #make global1Ctrl
    global1Prefix = 'global1'
    global1LockHide = [ 'v' ]
    
    global1Ctrl = control.Control( prefix = global1Prefix, defLockHide = global1LockHide, colorName = 'midGreen', noOff = True, shape = 'star' )
    
    # fix the scale Attr
    for ax in [ 'y', 'z' ]:
        mc.setAttr( '%s.s%s' % ( global1Ctrl.C, ax ), k = False )
        mc.connectAttr( '%s.sx' % global1Ctrl.C, '%s.s%s' % ( global1Ctrl.C, ax ) )
        
    # make global2Ctrl
    global2Prefix = 'global2'
    
    global2Ctrl = control.Control(prefix = global2Prefix, colorName = 'darkRed', shape = 'move')
    
    # make vis controls
    visPrefix = 'vis'
    lockHideVis = ['t', 'r', 's', 'v']
    visCtrl = control.Control(prefix = visPrefix, colorName = 'yellow', shape = 'vis', defLockHide = lockHideVis)
    
    attachGrp = _attachObject( visCtrl.Off, headJnt, topHeadObject, offsetAboveHeadY )
    
    return {
            'global1Ctrl': global1Ctrl,
            'global2Ctrl': global2Ctrl,
            'visCtrl': visCtrl
            }

def _attachObject( obj, attachObj, topHeadObject, offsetY ):
    """
    :param obj: str, offset group of the control to attach
    :param attachObj: str, name of the head joint to attach the obj
    :param topHeadObject: str, reference object for base position of the obj e.g: topHeadJnt
    :param offsetY: float, value to offset in Y world axis from topHeadObject
    :return attachGrp
    """
    # create offsetY  for control offset
    controlPos = mc.xform( topHeadObject, ws = True, q = True, t = True )
    
    # move the obj to base object pos plus offset in Y 
    mc.xform( obj, t = [ controlPos[0], controlPos[1] + offsetY, controlPos[2] ] )
    
    attachGrp = None
    # create an attach grp to constraint to obj
    if attachObj and mc.objExists( attachObj ):
        attachPrefix = name.removeSuffix( attachObj )
        attachGrp = mc.group(n = '%sAttach_grp' % attachPrefix,  em = True, r = True )
        
        mc.parent( attachGrp, attachObj )
        mc.parentConstraint( attachGrp, obj, mo = True )
        
    return attachGrp

def _parentAll( groupsData, controlsData ):
    
    mc.parent( controlsData['global1Ctrl'].C, groupsData['topGrp'] )
    mc.parent( controlsData['global2Ctrl'].Off, controlsData['global1Ctrl'].C )
    
    topCtrlParent = controlsData['global2Ctrl'].C
    
    mc.parent( groupsData['baseCtrlsGrp'], groupsData['baseModulesGrp'], groupsData['baseJointsGrp'], topCtrlParent )
    
    mc.parent( groupsData['baseNoTransGrp'], groupsData['assetModelGrp'], groupsData['topGrp'] )
    
    mc.parent( controlsData['visCtrl'].Off, groupsData['baseCtrlsGrp'] )

def _addAttributes( controlsData, groupsData ):
    """
    main fuction to add attributes of the base 
    """
    _addGlobalAttrsToVisCtrl( ctrl = controlsData['visCtrl'].C )
    _connectGlobalsToRig( visCtrl = controlsData['visCtrl'].C, groupsData = groupsData )
    
def _addGlobalAttrsToVisCtrl( ctrl ):
    attribute.addSection( ctrl, 'Settings' )
    
    mc.addAttr( ctrl, ln = 'geometryVis', at = 'enum', enumName = 'off:on', k = 1, dv = 1 )
    mc.addAttr( ctrl, ln = 'geometryDispType', at = 'enum', enumName = 'normal:template:reference', k = 1, dv = 2 )
    
    attribute.addSection( ctrl, 'controlSettings' )
    
    mc.addAttr( ctrl, ln = 'jointVis', at = 'enum', enumName = 'off:on', k = 1, dv = 0 )
    mc.addAttr( ctrl, ln = 'jointDispType', at = 'enum', enumName = 'normal:template:reference', k = 1, dv = 2 )
    
    mc.addAttr( ctrl, ln = controlVisAt, at = 'enum', enumName = 'off:on', k = 1, dv = 1 )
    
    addedAttrs = ['geometryVis', 'geometryDispType', 'jointVis', 'jointDispType', controlVisAt ]
    
    for at in addedAttrs:
        
        mc.setAttr( '%s.%s' % ( ctrl, at ), cb = True )
    
def _connectGlobalsToRig( visCtrl, groupsData ):
    
    # connect assetGrps attrs
    mc.setAttr( '%s.ove' % groupsData['assetModelGrp'], 1 )
    mc.connectAttr( '%s.geometryDispType' % visCtrl, '%s.ovdt' % groupsData['assetModelGrp'] )
    mc.connectAttr( '%s.geometryVis' % visCtrl, '%s.v' % groupsData[ 'assetModelGrp' ], f = True )
    
    # connect joints Attrs
    mc.setAttr( '%s.ove' % groupsData['baseJointsGrp'], 1 )
    mc.connectAttr( '%s.jointDispType' % visCtrl, '%s.ovdt' % groupsData['baseJointsGrp'] )
    mc.connectAttr( '%s.jointVis' % visCtrl, '%s.v' % groupsData[ 'baseJointsGrp' ], f = True )
    
    
def simpleBaseHierarchy(assetName):
    """
    function to make the simplest base hierarchy of a rig
    @param assetName: str, name of the top rig group and prop name
    @return: None
    """
    
    topGrp = mc.group( em = True, n = assetName )
    
    # main control and separator for extra attrs
    mainCtrl = mc.circle( n = 'main_ctl' )[0]
    mc.parent( mainCtrl, topGrp )
    attribute.addSection( mainCtrl, sectionName = 'Settings' )
    mc.setAttr( '%s.v' %  mainCtrl, k = False , cb = False, l = True )
    
    mainCtrlCls = mc.cluster( mainCtrl )[1]
    mc.setAttr( '%s.rx' % mainCtrlCls, 90 )
    mc.delete( mainCtrl, ch = True  )
    
    # connect the scales to X axis and hide the Y and Z axis
    for axis in [ 'y', 'z']:
        mc.connectAttr( '%s.sx' % mainCtrl, '%s.s%s' % (mainCtrl, axis ), f = True )
        mc.setAttr( '%s.s%s' % ( mainCtrl, axis ), k = False , cb = False )
    
    # geoGrp parent under topGrp and attribute creation
    geoGrp = mc.group( n = 'geo_grp', p = topGrp, em = True )
    mc.addAttr( mainCtrl, ln = 'geo_displayType', at = 'enum', en = 'normal:template:reference', k = True )
    mc.setAttr( '%s.ove' % geoGrp, 1 )
    mc.connectAttr( '%s.geo_displayType' % mainCtrl, '%s.overrideDisplayType' % geoGrp )
    
    mc.addAttr( mainCtrl, ln = 'geo_vis', at = 'enum', en = 'off:on', k = True, dv = 1 )  
    mc.connectAttr( '%s.geo_vis' % mainCtrl, '%s.v' % geoGrp )

    # create joints and controls groups
    for grp in [ 'joints', 'controls' ]:
        
        groupName = mc.group( n = '%s_grp' % grp, p = mainCtrl , em = True)
        mc.addAttr( mainCtrl, ln = '%s_vis' % grp, at = 'enum', en = 'off:on', k = True, dv = 1  )
        mc.connectAttr( '%s.%s_vis' % ( mainCtrl, grp ), '%s.v' % groupName )
