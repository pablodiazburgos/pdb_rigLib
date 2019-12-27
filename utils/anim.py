"""
module for manipulation animation stuffs
@author: Pablo Diaz Burgos
"""

import maya.cmds as mc

from . import connect

def setDrivenKey( driver, driven, driverVals, drivenVals, intangtype = 'linear', outtangtype = 'linear', cleanDrivenPlug = True ):
    
    """
    function for easy creation of driven keys
    type of tangents:
    
    - fixed
    - linear
    - flat
    - step
    - slow
    - fast
    - spline
    - clamped
    - plateau
    - stepNext
    
    :param driver: str, driver plug ( object.attribute )
    :param driver: str, driven plug ( object.attribute )
    :param driverVals: list[ float ], driver values
    :param drivenVals: list[ float ], driven values
    :param intangtype: str, tangentType of the driven curve, Linear by default
    :param outtangtype: str, tangentType of the driven curve, Linear by default
    :param cleanDrivenPlug: bool, clean the driven attribute to connect the driven key
    """

    # clean the plug of the driven for connection
    if cleanDrivenPlug:
        setDrivenKey_CleanDrivenPlug( driven )
    
    # make SDK
    
    for i in range( len( driverVals ) ):
     
        driverVal = driverVals[i]
        drivenVal = drivenVals[i]
        
        mc.setDrivenKeyframe( driven , cd = driver, dv = driverVal, v = drivenVal )
    
    # adjust SDK
    
    drivencrv = mc.listConnections( driven, s = 1, d = 0, scn = 1 )[0]
    drivenCurves = [ drivencrv ]
    
    # make blend weighted node check
    
    if mc.nodeType( drivencrv ) in ['blendWeighted', 'pairBlend']:
        
        drivenCurves = mc.listConnections( drivencrv, scn = 1, s = 1, d = 0 )
    
    for drivenCrv in drivenCurves:
        mc.keyTangent( drivenCrv, e = 1, itt = intangtype, ott = outtangtype )


def setDrivenKey_CleanDrivenPlug( driven ):
    
    con = mc.listConnections( driven, scn = True, s = True, d = False )
    
    if not con: return
    
    if 'animCurve' in mc.nodeType( con[0], inherited = 1 ):
    
    # if driven was connected to animCurve node and this node wasn`t connected to anything else, delete it

        if len( mc.listConnections( con[0], d = 1, scn = 1 ) ) == 1:
            
            mc.delete( con[0] )
            
    # otherwise just disconnect it
    
    else: connect.disconnect( driven )

def createMotionPath( pathCurve, pathObject, name = 'new_mpath', follow = 1, fractionMode = 1, frontAxis = 'z', upAxis = 'y', worldUpType = 'scene', worldUpVector = [1, 0, 0], worldUpObject = '', uValue = 0.0, inverseFront = 0 ):

    mPathNode = mc.createNode( 'motionPath', n = name )
    
    mc.setAttr( mPathNode + '.f', follow )
    mc.setAttr( mPathNode + '.fm', fractionMode )
    mc.setAttr( mPathNode + '.fa', {'x':0, 'y':1, 'z':2}[frontAxis] )
    mc.setAttr( mPathNode + '.ua', {'x':0, 'y':1, 'z':2}[upAxis] )
    mc.setAttr( mPathNode + '.wut', {'scene':0, 'object':1, 'objectrotation':2, 'vector':3, 'normal':4}[worldUpType] )
    mc.setAttr( mPathNode + '.wu', worldUpVector[0], worldUpVector[1], worldUpVector[2] )
    mc.setAttr( mPathNode + '.uValue', uValue )
    mc.setAttr( mPathNode + '.inverseFront', inverseFront )
    
    if worldUpType == 'object' or worldUpType == 'objectrotation' and mc.objExists( worldUpObject ):
        
        mc.connectAttr( worldUpObject + '.worldMatrix', mPathNode + '.wum' )
    
    mc.connectAttr( pathCurve + '.worldSpace', mPathNode + '.geometryPath' )
    mc.connectAttr( mPathNode + '.msg', pathObject + '.specifiedManipLocation' )
    
    mc.connectAttr( mPathNode + '.' + 'rotate', pathObject + '.r' )
    mc.connectAttr( mPathNode + '.' + 'allCoordinates', pathObject + '.t' )
    
    return mPathNode

def checkMotionPath( obj ):
    '''
    test if object has motionPath node attached to it
    
    :param object: str, name of object to check
    :return: bool, True if motionPath was found
    '''
    
    objConnections = mc.listConnections( obj )
    
    if objConnections:
        
        motionPathNodes = mc.ls( objConnections, typ = 'motionPath' )
        if motionPathNodes: return True
    
    return False