"""
footRigLocators
@category Rigging @subcategory Tools
@tags build rig foot locators
"""

import maya.cmds as mc

from utils import name
from utils import vector
from utils import transform

def build(ankleJoint, toeJoint, toeEndJoint, prefix = '', scale = 1.0 ):
    
    '''
    for rig build scene, Make foot locators around the foot joints to be used as foot rig build template
    Locators made will be: Heel, Tip, Out, In (out/in are for side tilting)
    NOTE: Placement system assumes that feet are on the ground (world Y zero)
    
    :param ankleJoint: str, ankle joint
    :param toeJoint: str, toe joint
    :param toeEndJoint: str, toe end joint
    :return: list(str), locators: heel, tip, out, in
    '''
    # get side and prefix
    side = name.getSide( ankleJoint )
    sideundscore = ''
    if not side == '': sideundscore = side + '_'
    
    prefixundscore = ''
    if not prefix == '': prefixundscore = prefixundscore + '_'
    
    #===========================================================================
    # make all locators first
    #===========================================================================
    
    locBaseNames = [ 'heel', 'tip', 'inFoot', 'outFoot' ]
    locNames = [ sideundscore + prefixundscore + basename + '_loc' for basename in locBaseNames ]
    
    locs = []
    for locName in locNames: locs.append( mc.spaceLocator( n= locName )[0] )
    
    # adjust locator shape scale
    
    locSc = scale * 1.5
    for loc in locs: mc.setAttr( loc + '.localScale', locSc, locSc, locSc )
    
    #===========================================================================
    # place HEEL and TOE locators
    #===========================================================================
    
    ankleVec = vector.makeMVector( mc.xform( ankleJoint, q=1, t=1, ws=1 ) )
    toeVec = vector.makeMVector( mc.xform( toeJoint, q=1, t=1, ws=1 ) )
    toeEndVec = vector.makeMVector( mc.xform( toeEndJoint, q=1, t=1, ws=1 ) )
    
    # place heel
    # slightly behind ankle joint on the ground
    
    ankleHeelVec = (ankleVec - toeVec) * 0.5
    ankleHeelVecPos = ankleVec + ankleHeelVec
    mc.setAttr( locs[0] + '.t', ankleHeelVecPos.x, 0, ankleHeelVecPos.z )
    
    # place toe
    # just under the toe end
    
    mc.setAttr( locs[1] + '.t', toeEndVec.x, 0, toeEndVec.z )
    
    #===========================================================================
    # place Out and In locators
    #===========================================================================
    
    # make temporary locators to get the in and out positions
    tempInLocator = mc.spaceLocator( n = 'tempInLoc' )[0]
    tempInLocOffGrp = transform.makeOffsetGrp( tempInLocator )
    mc.xform( tempInLocOffGrp, ws = True, t = ( toeEndVec.x, 0, toeEndVec.z ) )
    mc.xform( tempInLocOffGrp, rp = ( toeVec.x, 0, toeVec.z ), ws = True )
    
    tempOutLocator = mc.spaceLocator( n = 'tempOutLoc' )[0]
    tempOutLocOffGrp = transform.makeOffsetGrp( tempOutLocator )
    mc.xform( tempOutLocOffGrp, ws = True, t = ( toeEndVec.x, 0, toeEndVec.z ) )
    mc.xform( tempOutLocOffGrp, rp = ( toeVec.x, 0, toeVec.z ), ws = True )
    
    negval = -90
    posVal = 90
    
    if side in [ 'l', 'c', '' ]:
        
        mc.setAttr( tempInLocOffGrp + '.ry', negval )
        mc.setAttr( tempOutLocOffGrp + '.ry', posVal )
            
        newInPos = mc.xform( tempInLocator, ws = True, t = True, q = True )
        newOutPos = mc.xform( tempOutLocator, ws = True, t = True, q = True )
        
        mc.xform( locs[2], ws = True, t = ( newInPos[0], newInPos[1], newInPos[2] ) )
        mc.xform( locs[3], ws = True, t = ( newOutPos[0], newOutPos[1], newOutPos[2] ) )
        
    if side == 'r':
        
        mc.setAttr( tempInLocOffGrp + '.ry', posVal )
        mc.setAttr( tempOutLocOffGrp + '.ry', negval )
        
        newInPos = mc.xform( tempInLocator, ws = True, t = True, q = True )
        newOutPos = mc.xform( tempOutLocator, ws = True, t = True, q = True )
        
        mc.xform( locs[2], ws = True, t = ( newInPos[0], newInPos[1], newInPos[2] ) )
        mc.xform( locs[3], ws = True, t = ( newOutPos[0], newOutPos[1], newOutPos[2] ) )
    
    mc.delete( tempInLocOffGrp, tempOutLocOffGrp )
    
    # done
    return locs
    
def mirrorFootLocs():
    
    '''
    mirror foot locators from left position to right position
    Note: code assumes that right locators already exists
    '''    
    lside = 'l_'
    rside = 'r_'
    
    for locSuffix in ['heel_loc', 'tip_loc', 'inFoot_loc', 'outFoot_loc']:
        
        lLoc = lside + locSuffix
        rLoc = rside + locSuffix
        
        lLocPos = mc.xform( lLoc, ws = True, q = True, t = True )
        
        # set values for rLoc negating X axis
        mc.xform( rLoc, ws = True, t = ( lLocPos[0]*-1, lLocPos[1], lLocPos[2] ) )
    
    
    
    
    
    
    
    
    