'''
belt module
@category Rigging @subcategory rig
'''

#TODO: make world joint orientation optional

import maya.cmds as mc

from ..utils import name
from ..utils import shape


def makeFollicleBelt( beltSurface, numjoints, prefix = '', lengthParam = 'v' ):
    
    '''
    :param beltSurface: str, surface to build follicles and joints on
    :param numjoints: int, number of joints to build evenly along the surface length
    :param prefix: str, prefix for naming new created objects
    :param lengthParam: str, parameter to use as length on the provided nurbs surface, valid values are: 'u', 'v'
    :return: list( str, str, list ), list with name of top group, main group and list of joints
    
    makes specified number of joints and hair follicles (holding joints)#
    using V values by default for horizontal positions
    use these joints to skin your belt geometry
    
    NOTE: both polygons and NURBS are supported, polygons need to have 0-1 span non-overlapping UVs
    '''
    
    # get name from surface
    
    if not prefix:
        
        prefix = name.removeSuffix( beltSurface )
    
    # top group for all belt rigs
    
    topGrp = 'follicleBeltRigTop_grp'
    if not mc.objExists( topGrp ): topGrp = mc.group( n = topGrp, em = 1 )
    
    # main group
    
    mainGrp = mc.group( n = prefix + 'Main_grp', em = 1, p = topGrp )
    
    folicJntGrp = mc.group( n = prefix + 'FolicJoint_grp', em = 1, p = mainGrp )
    mc.setAttr( folicJntGrp + '.it', 0, l = 1 )
    mc.scaleConstraint( mainGrp, folicJntGrp )
    
    # surface param names
    
    lengthParam = lengthParam.upper()
    heightParam = 'U'  
    
    if lengthParam == 'U': heightParam = 'V'
    
    # make step size based on closed or open surface
    
    surfaceForm = 0

    surfaceShape = shape.getShape( beltSurface )

    if mc.nodeType( surfaceShape ) == 'nurbsSurface':

        surfaceForm = mc.getAttr( beltSurface + '.form' + lengthParam )
    
    stepDivider = numjoints

    if surfaceForm == 0:

        stepDivider = numjoints - 1
    
    verticCoord = 0.5
    horizCoordStep = 1.0 / stepDivider
    horizCoord = 0.0
    
    joints = []
    
    for i in range( numjoints ):
        
        # make follicle
        
        follicle = mc.createNode( 'follicle', n = prefix + 'Follicle' + str( i + 1 ) + '_folicShape' )
        follicleXform = mc.listRelatives( follicle, p = 1 )[0]
        mc.setAttr( follicle + '.v', 0 )
        
        mc.parent( follicleXform, folicJntGrp )
        
        mc.connectAttr( follicle + '.outTranslate', follicleXform + '.t' )
        mc.connectAttr( follicle + '.outRotate', follicleXform + '.r' )
        
        mc.connectAttr( beltSurface + '.local', follicle + '.inputSurface' )
        mc.connectAttr( beltSurface + '.worldMatrix', follicle + '.inputWorldMatrix' )
        
        mc.setAttr( follicle + '.parameter' + heightParam, verticCoord )
        mc.setAttr( follicle + '.parameter' + lengthParam, horizCoord )
        
        # make joint
        
        mc.select( cl = 1 )
        beltJnt = mc.joint( n = prefix + str( i + 1 ) + '_jnt' )
        mc.parent( beltJnt, follicleXform, r = 1 )
        
        joints.append( beltJnt )
        
        # orient joint to previous joint
#         
#         if i > 0:
#             
#             mc.aimConstraint( joints[ i - 1 ], beltJnt, aim = [1, 0, 0], u = [0, 0, 1], wut = 'objectrotation', wuo = follicleXform, wu = [0, 0, 1] )
#         
        horizCoord = horizCoord + horizCoordStep
    
    return [ topGrp, mainGrp, joints ]
   
    
