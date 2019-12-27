'''
Module to mirror Cvs position ... useful to mirror controls
'''

import maya.cmds as mc
import maya.OpenMaya as om


def mirrorCvPositions( cvs, mode = 'x' ):
    
    '''
    mirror positions of CVs based on their names: flipping left to right and right to left
    
    :param cvs: list(str), list of CVs (usually taken using mc.ls( sl=1, fl=1 )
    :param mode: str, flip axis, "x" by default as PF creatures are facing Z+
    :return: None
    '''
    
    for cv in cvs:
        
        cvShortLeft = str( cv ).split( '|' )[-1]
        cvShortRight = ''
        
        if cvShortLeft.startswith( 'l_' ): cvShortRight = 'r_' + cvShortLeft[2:]
        elif cvShortLeft.startswith( 'r_' ): cvShortRight = 'l_' + cvShortLeft[2:]
        
        else:
            
            om.MGlobal_displayWarning( 'utils.mirrorCvPositions: cannot find mirror for ' + cvShortLeft + ', doesn`t start with L_ or R_, idle...' )
            continue
        
        pos = mc.xform( cvShortLeft, q = 1, ws = 1, t = 1 )
        
        
        if mode == 'x': mc.xform( cvShortRight, ws = 1, t = [ pos[0] * ( -1 ), pos[1], pos[2] ] )
        if mode == 'z': mc.xform( cvShortRight, ws = 1, t = [ pos[0], pos[1], pos[2] * ( -1 ) ] )

