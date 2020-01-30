'''
constraint library
@category Rigging @subcategory Utils
'''

import maya.cmds as mc
import maya.mel as mm

from . import anim
from . import transform
from . import name

#TODO: study makeSwitch and multiSwitch fuctions


def setupDualConstraintBlend(consnode, driverat, targetorder = [0, 1]):
    
    '''
    create blend between 2 constraint targets (which is often the case)
    
    :param consnode: str, constraint node (e.g. aimConstraint node name)
    :param driverat: str, driver attribute as 'object.attribute'
    :param targetorder: list( int, int ), order of targets linked to driver values, by default this is value:0 -> target:0, value:1 -> target:1
    :return: None
    '''
    
    wtats = getWeightAttrs(consnode)
    
    anim.setDrivenKey(driverat, consnode + '.' + wtats[ targetorder[0] ], [0, 1], [1, 0])
    anim.setDrivenKey(driverat, consnode + '.' + wtats[ targetorder[1] ], [0, 1], [0, 1])

def getWeightAttrs(constraintNode):
    
    '''
    get weight attribute names from given constraint node
    
    :param constraintNode: str, constraint node (e.g. aimConstraint node name)
    :return: None
    '''
    
    objNodeType = mc.nodeType(constraintNode)
    cmd = str(objNodeType) + ' -q -wal ' + str(constraintNode)
    allAts = mm.eval(cmd)
    
    return allAts

def removeAll(obj):
    
    '''
    :param obj: str, object to get its constraint(s) deleted
    :return: list (str), names of deleted constraints
    
    Simple function to remove constraints from object
    '''
    
    cons = mc.listConnections(obj, t = 'constraint', s = 1, d = 0)
    if cons: mc.delete(cons)
    
    return cons

def makeSwitch(drivenObj, switchObj, switchAttrName, switchEnums, constraintType, targets, maintainOffset = 1, defaultIdx = -1, skipRotation = False, blendValues = False):

    '''
    Create space switch with making constraint, attribute and space switch system
    
    :param drivenObj: str, object to be constrained by space switch system
    :param switchObj: str, object holding an attribute controling current space value (attribute is created if not existing)
    :param switchAttrName: str, name of space switch attribute (going to be enum type, but can be existing int type too)
    :param switchEnums: list( str ), names of spaces (e.g. 'local ', 'global', 'body'), optionaly used as enum if new attribute needs to be made
    :param constraintType: str, type of constraint same as the command (e.g. 'parentConstraint' or 'orientConstraint')
    :param targets: list( str ), names of objects representing the spaces in the same order as space switching
    :param maintainOffset: bool, use offset on constraint (true by default)
    :param defaultIdx: int, index of default space (applied to either enum or int attribute), default is 1 if there are 2 values - for FK/IK
    :param skipRotation: bool, skip connecting rotation of driven object, only for parentConstraint (or other TransRot switches)
    :param blendValues: bool, will create 0-1 blend attribute to change weights of the constraint (only works with 2 targets)
    :return: str, name of constraint node
    '''
    
    # check number of targets
    
    if blendValues and len(targets) > 2:
            
            raise Exception('cannot setup switch in Blend Values mode with more then 2 targets')
    
    # adjust default switch value
    
    if defaultIdx == -1:
        
        if len(targets) == 2:  # we assume this could be FK/IK switch used very often
            
            defaultIdx = 1
        
        else:
            
            defaultIdx = 0
    
    
    # make parented targets
    
    parTargets = []
    
    for i, t in enumerate(targets):
        
        newObjName = switchEnums[i] + '_' + drivenObj + '_' + constraintType + '_grp'
        newObj = mc.group(em = 1, r = 1, p = drivenObj, n = newObjName)
        
        if maintainOffset:
        
            newObj = mc.parent(newObj, t, a = 1)[0]
            
        else:
        
            newObj = mc.parent(newObj, t, r = 1)[0]
        
        parTargets.append(newObj)
    
    # make constraint and connect weight attrs
    
    if constraintType == 'orientConstraint':
        
        constraintType = 'parentConstraint -st x -st y -st z '
    
    skipRotationStr = ''
    if skipRotation:
        
        skipRotationStr = ' -sr x -sr y -sr z '
    
    constraintCmd = constraintType + skipRotationStr    
    for t in parTargets:
        
        constraintCmd = constraintCmd + ' ' + str(t)
        
    constraintCmd = constraintCmd + ' ' + str(drivenObj)
    
    constraintNode = mm.eval(constraintCmd)[0]    
    weightAttrs = getWeightAttrs(constraintNode)
    
    # make constraint blending more stable - use shortest interpolation
    mc.setAttr(constraintNode + '.interpType', 2)
    
    switchEnumString = ''
    for en in switchEnums: switchEnumString = switchEnumString + en + ':'
    
    if not mc.objExists(switchObj + '.' + switchAttrName):
        
        if blendValues:
            
            mc.addAttr(switchObj, ln = switchAttrName, at = 'float', k = 1, dv = defaultIdx, min = 0, max = 1)
            mc.addAttr(switchObj, ln = switchAttrName + 'Name', at = 'enum', enumName = switchEnumString)
            mc.setAttr(switchObj + '.' + switchAttrName + 'Name', cb = 1)
            mc.connectAttr(switchObj + '.' + switchAttrName, switchObj + '.' + switchAttrName + 'Name')
            
        else:
            
            mc.addAttr(switchObj, ln = switchAttrName, at = 'enum', enumName = switchEnumString, k = 1, dv = defaultIdx)
    
    weightPlugs = [ constraintNode + '.' + a for a in weightAttrs ]
    
    multiSwitch(switchObj, weightPlugs, switchAttrName, blendValues)
    
    # set default switch value
    # skip if there is connection or attribute is locked
    
    try:

        mc.setAttr(switchObj + '.' + switchAttrName, defaultIdx)

    except:

        pass
    
    return constraintNode

def multiSwitch(driverObject, drivenPlugs, driverAttr = 'multiSwitchValue', blendValues = False):
    
    '''
    :param driverObject: str, object to drive the plugs via SDK, driverAttr will be created if doesn`t exist
    :param driverAttr: str, name of int attr to drive switching with 0-base values
    :param drivenPlugs: list( str ), plugs to be getting boolean values (0,1)
    :param blendValues: bool, will create 0-1 blend attribute to change weights
    
    :summary: makes a boolean switch for multiple plugs using 0-base range
    :summary: SDK switch is made on driverObject object
    '''

    atrType = 'short'
    if blendValues: atrType = 'float'
    
    if not mc.objExists(driverObject + '.' + driverAttr):
        
        mc.addAttr(driverObject, ln = driverAttr, at = atrType, k = 1)
    
    
    # make sure that SDK can be made
    
    connectedPlug = mc.listConnections(driverObject + '.' + driverAttr, s = 1, d = 0, p = 1)
    if connectedPlug:
        
        mc.disconnectAttr(connectedPlug[0], driverObject + '.' + driverAttr)
    
    driverOrigVal = mc.getAttr(driverObject + '.' + driverAttr)
    mc.setAttr(driverObject + '.' + driverAttr, l = 0)
    
    
    # make switch SDK
    
    for i in range(len(drivenPlugs)):
        
        mc.setAttr(driverObject + '.' + driverAttr, i)
        
        for j in range(len(drivenPlugs)):
            
            value = 0
            if j == i:
                
                value = 1
            
            mc.setDrivenKeyframe(drivenPlugs[j], cd = driverObject + '.' + driverAttr, v = value)
        
    # after SDK is made, set back original value and reconnect the connection, if there was any
    
    mc.setAttr(driverObject + '.' + driverAttr, driverOrigVal)
    if connectedPlug:
        
        mc.connectAttr(connectedPlug[0], driverObject + '.' + driverAttr)

def pointConstraintToCurve(curve, objects, prefix = ''):
    
    '''
    point constraint objects to curve to closest point on curve,
    using nearestPointOnCurve and pointOnCurveInfo nodes
    '''
    
    if not prefix:
        
        prefix = name.removeSuffix(objects[0])
        prefix = name.removeEndNumbers(prefix)
    
    nearpointnode = mc.createNode('nearestPointOnCurve', n = prefix + '_npc')
    mc.connectAttr(curve + '.worldSpace', nearpointnode + '.inputCurve')
    
    worldgrps = []
    
    for i, j in enumerate(objects):
        
        pos = mc.xform(j, q = 1, t = 1, ws = 1)
        mc.setAttr(nearpointnode + '.inPosition', pos[0], pos[1], pos[2])
        param = mc.getAttr(nearpointnode + '.parameter')
        
        pointnode = mc.createNode('pointOnCurveInfo', n = prefix + '%d_pci' % i)
        mc.connectAttr(curve + '.worldSpace', pointnode + '.inputCurve')
        mc.setAttr(pointnode + '.parameter', param)
        
        # make world position group
        
        worldgrp = mc.group(n = prefix + 'CurveWorld%d_grp', em = 1)
        mc.connectAttr(pointnode + '.position', worldgrp + '.t')
        mc.pointConstraint(worldgrp, j)
        
        worldgrps.append(worldgrp)
        
    
    mc.delete(nearpointnode)
    
    return worldgrps    
