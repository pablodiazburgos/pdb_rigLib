'''
gameTools at rigLib.tools
@category Rigging @subcategory Tools
@tags game setup assets joints engine export

tools specific for game rigs
'''

import maya.cmds as mc

from ..utils import joint
from ..utils import name
from ..utils import skinCluster


def createGameJoints( skinnedObjects = [], gamePrefix = 'game_', baseRigData = None ):
    
    '''
    Get the skinned joints for the passed objects, makes a duplicate and connected via constraint
    Script should keep same hierarchy as the original joints with no groups or extra transforms
    Useful to create a clean joint hierarchy for game engine driven by the usual rig
    
    :param skinnedObjects: list( str ), list of skinned objects to get joints from ( if not skin found just ignore it )
    :param gamePrefix: str, prefix to name the game joints
    :param baseRigData: instance, base rig data returned from rigbase.base build() if None the parentGrp group would be world
    :return set, maya selection set with with all the new game joints included to easy bake and export
    '''
    # make sure nothing is selected
    mc.select(cl = True)
    
    # create the group for game joints 
    parentGrp = 'gameJoints_grp'
    parentGrpName = 'gameJoints_grp'
    if not mc.objExists( parentGrp ):
        parentGrp = mc.group( em = True, n = parentGrpName )
        
    # parent parentGrp in proper location
    if baseRigData:
        mc.parent( parentGrp, baseRigData['baseNoTransGrp'] )
    
    # get skinned joint with a function
    scJoints = getSkinnedJoints( skinnedObjects )
    
    # create game joints from skinned joints 
    _gameJointsSetup( scJoints, gamePrefix, parentGrp )
    
def getSkinnedJoints( skinnedObjects ):
        
    # Filter the passed objects to be sure it has some shape and will work with skinCluster.getRelated() function
    filteredSkinnedObjects = []
    
    for item in skinnedObjects:
        shapeObj = mc.listRelatives( item, s = True )
        if not shapeObj:
            continue
        
        filteredSkinnedObjects.append( item )
        
    
    # get all the skinned joints to passed objects skin clusters
    allSkinClusters = []
   
    for geo in filteredSkinnedObjects:
        
        sc = skinCluster.getRelated( geo )
        if not sc:
            continue
        allSkinClusters.append( sc )
        
    # get skinned joints
    scJoints = []

    for sc in allSkinClusters:
        
        infs = mc.skinCluster( sc, q = True, inf = True )
        scJoints.extend( infs )
        
    scJoints = list( set( scJoints ) )
    
    return scJoints

def _gameJointsSetup( scJoints, gamePrefix, parentGrp ):
    
    for scJnt in scJoints:
        
        # check if parent if already in the list (need this to be able to reconstruct the hierarchy)
        scJntParent = mc.listRelatives( scJnt, p = True )[0]
        if not scJntParent in scJoints and mc.nodeType( scJntParent ) == 'joint':
            scJoints.append( scJntParent )
    
    gameParentList = []
    fullGamejoints = []
    
    # create the game joint , get their parent and his driver joint
    for scJnt in scJoints:
        scJntParent = mc.listRelatives( scJnt, p = True )[0]
        gameJntParent = gamePrefix + scJntParent
        
        gameJnt = mc.duplicate( scJnt, n = gamePrefix + scJnt, po = True )[0]
        mc.parent( gameJnt, parentGrp )
        
        if mc.nodeType( scJntParent ) == 'joint':
            gameParentList.append( [ gameJnt, gameJntParent, scJnt ] )
        
        fullGamejoints.append( gameJnt )
        
    #  parent game joint in proper hierarchy and constraint from driver joint
    for gameParent in gameParentList:

        mc.parent( gameParent[0], gameParent[1] )
        mc.parentConstraint( gameParent[2], gameParent[0], mo = True )
        mc.scaleConstraint( gameParent[2], gameParent[0], mo = True )
        
    # create game joints set
    gameJointsSet = mc.sets( n = 'gameJoints_set' )
    mc.sets( fullGamejoints , add = gameJointsSet )
    
    # make root connection
    gameRootJnt = mc.listRelatives( parentGrp, c = True, type = 'joint' )[0]
    origRootJnt = gameRootJnt[ len( gamePrefix ): ]
    
    mc.parentConstraint( origRootJnt, gameRootJnt, mo = True )
    mc.scaleConstraint( origRootJnt, gameRootJnt, mo = True )
    
    # clean extra transforms under parent group
    parentGrpChilds = mc.listRelatives( parentGrp, c = True )

    
