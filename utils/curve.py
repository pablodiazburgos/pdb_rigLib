'''
functions for working with curves (nurbsCurves and bezierCurves)
@category Rigging @subcategory Utils
'''

import maya.cmds as mc
import maya.OpenMaya as om

from . import apiwrap
from . import name
from . import shape


def makeConnectionLine( objectA, objectB, prefix = '', overrideMode = 1, curveParent = '' ):
    
    '''
    :param objectA: str, first object to attach curve to
    :param objectB: str, second object to attach curve to
    :param prefix: str, prefix for new created nodes
    :param overrideMode: int (valid values: 0,1,2), turn on overrideDisplay for new curve and use this number for its enum type (normal, template, reference)
    :param curveParent: str, optional, name of parent for created connection curve
    :return: str, name of the curve
    '''
    
    objABase = name.removeSuffix( objectA )
    objBBase = name.removeSuffix( objectB )
    
    if prefix == '': prefix = objABase + '_' + objBBase
    
    line = from2objects( objectA, objectB, prefix = prefix, spans = 1, degree = 1 )
    
    mc.cluster( line + '.cv[0]', n = prefix + 'A_cluster', wn = ( objectA, objectA ), bs = 1 )
    mc.cluster( line + '.cv[1]', n = prefix + 'B_cluster', wn = ( objectB, objectB ), bs = 1 )
    
    lineShape = mc.listRelatives( line, s = 1 )[0]
    mc.setAttr( line + '.it', 0, l = 1 )
    mc.setAttr( line + '.ove', 1 )
    mc.setAttr( line + '.ovdt', overrideMode )
    
    # parent curve
    
    if mc.objExists( curveParent ):
        
        mc.parent( line, curveParent )
    
    
    return line

def from2positions( posA, posB, prefix = 'new', spans = 1, degree = 3 ):
    
    '''
    make curve between 2 points in space
    
    :param posA: list( float, float, float ), first position to build curve from
    :param posB:list( float, float, float ), second position to build curve from
    :param prefix: str, prefix for new created nodes
    :param spans: number of spans for new curve
    :param degree: int, degree of new curve
    :return: str, name of new curve
    '''
    
    if degree == 2:
        
        crv = makeSecondDegree( posA, posB, prefix = prefix )
        return crv
    
    crv = mc.curve( n = prefix + '_crv', p = ( posA, posB ), d = 1 )
    shape.fixShapesName( crv )
    
    mc.rebuildCurve( crv, keepRange = False, spans = spans, degree = degree )
    
    return crv
    
def from2objects( objectA, objectB, prefix = '', spans = 1, degree = 3 ):
    
    '''
    make curve between 2 objects
    
    :param objectA: str, first object to attach curve to
    :param objectB: str, second object to attach curve to
    :param prefix: str, prefix for new created nodes
    :param spans: int, number of spans for new curve
    :param degree: int, degree of new curve
    :return: str, name of new curve
    '''
    
    nullA = mc.group( n = 'nullA_from2objects_grp', em = 1 )
    nullB = mc.group( n = 'nullB_from2objects_grp', em = 1 )
    
    mc.delete( mc.pointConstraint( objectA, nullA ) )
    mc.delete( mc.pointConstraint( objectB, nullB ) )
    
    posA = mc.xform( nullA, q = 1, t = 1, ws = 1 )
    posB = mc.xform( nullB, q = 1, t = 1, ws = 1 )
    
    mc.delete( nullA, nullB )
    
    line = from2positions( posA, posB, prefix = prefix, spans = spans, degree = degree )
    
    return line

def makeSecondDegree( posA, posB, prefix = 'new' ):
    
    """
    make curve with degree 2
    
    :param posA: list(float,float,float), first position to build curve from
    :param posB: list(float,float,float), second position to build curve from
    :param prefix: str, prefix for new created nodes
    :return: str, name of new curve
    """
    
    vecA = om.MVector( posA[0], posA[1], posA[2] )
    vecB = om.MVector( posB[0], posB[1], posB[2] )
    vecMid = ( ( vecB - vecA ) / 2.0 ) + vecA
    posMid = [vecMid.x, vecMid.y, vecMid.z]
    
    crv = mc.curve( n = prefix + '_crv', p = ( posA, posMid, posB ), d = 2 )
    shape.fixShapesName( crv )
    
    return crv

def getCVpositions( curve ):
    
    '''
    return list of CV positions in world space
    
    :param curve: str, nurbs curve to read CV positions
    :return: list( list( float, float, float), ... ) - list with 3-float values lists
    '''
    
    curveCvs = mc.ls( curve + '.cv[*]', fl = 1 )
    
    positions = [ mc.xform( cv, q = 1, t = 1, ws = 1 ) for cv in curveCvs ]
    
    return positions