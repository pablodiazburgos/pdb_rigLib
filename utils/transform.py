"""
transform @utils

Functions to manipulate and create transforms
"""

import math

import maya.cmds as mc
import maya.OpenMaya as om

import name
import vector

def makeOffsetGrp( obj, prefix = '', suffix = 'Offset', inOrigin = False ):
    
    '''
    @param obj: object to be parented under new offset group
    @type obj: str
    @param prefix: optional, prefix to be as base of the name, if empty then base name is made from passed object
    @type prefix: str
    @param suffix: suffix to be added to object prefix to name offset group
    @type suffix: str
    @param inOrigin: if True, create offset group in world origin, if False, keep same transform as given object
    @type inOrigin: bool
    @return: str, name of new offset group
    
    simple make new parent above given object, for visibility connections or to zero out its transforms     
    '''
    
    #===========================================================================
    # make the name
    #===========================================================================
    
    if not prefix:
        
        prefix = name.removeSuffix( obj )
    
    offname = prefix + suffix + '_grp'
    
    
    #===========================================================================
    # make offset group
    #===========================================================================
    
    if inOrigin:
        
        offgrp = mc.group( n = offname, em = 1 )
    
    else:
        
        offgrp = mc.group( n = offname, p = obj, em = 1 )
    
    parentobj = mc.listRelatives( obj, p = 1 )
    
    if parentobj:
        
        mc.parent( offgrp, parentobj[0] )
        
    elif not inOrigin:
        
        mc.parent( offgrp, w = 1 )    
    
    mc.parent( obj, offgrp )
    
    return offgrp

def createJntVtxPos(name = name):

    sel = mc.ls(sl=True , fl=True)[0]

    #get vtx position , create jnt and copy vtx pos to jnt
    vtxPos = mc.xform(sel, ws=True, t=True, q=True)
    mc.select(cl=True)

    jntName = name + '_jnt'
    jnt = mc.joint(n=jntName)

    mc.xform(jnt, ws=True, t=(vtxPos[0],vtxPos[1], vtxPos[2] ))

    for i in ["root", "inf", "pos"]:

        grp = mc.group(n = '%s_%s_grp', em = True %  (i, name ) )

        mc.delete(mc.parentConstraint(jnt, grp, mo=False))
        if i == "inf":
            mc.parent(i, "root_%s_grp" % name)
        elif i == "pos":
            mc.parent(i, "inf_%s_grp" % name)

def makeLocator( prefix = 'new', pos = [0, 0, 0], rot = [0, 0, 0], posRef = '', rotRef = '', moveRef = '', parent = '', simpleGroup = False ):
    
    '''
    make Maya Locator with some options to move it and parent it
    
    :param prefix: str, prefix to name locator
    :param pos:list( float, float, float ), position for locator
    :param rot: ist( float, float, float ), rotation for locator
    :param posRef: str, reference object to translate locator
    :param rotRef: str, reference object to rotate locator
    :param moveRef: str, reference object to rotate and translate locator (overrides both Pos and Rot reference objects)
    :param parent: str, parent object for locator
    :param simpleGroup: bool, if True, just make empty group ("null")
    :return: str, name of new locator transform
    '''
    
    # make locator or group
    
    if simpleGroup:
        
        null = mc.group( n = prefix + '_grp', em = 1 )
    
    else:
        
        null = mc.spaceLocator( n = prefix + '_loc' )[0]
    
    
    # position and rotate nullator
    
    if moveRef and mc.objExists( moveRef ):
        
        mc.delete( mc.parentConstraint( moveRef, null ) )
        
    else:
        
        if not mc.objExists( posRef ): mc.xform( null, t = pos, ws = 1 )
        else: mc.delete( mc.pointConstraint( posRef, null ) )
        
        if not mc.objExists( rotRef ): mc.xform( null, ro = rot, ws = 1 )
        else: mc.delete( mc.orientConstraint( rotRef, null ) )
    
    if parent and mc.objExists( parent ): mc.parent( null, parent )
    
    
    # return new nullator
    
    return null   

def rotateAlignToWorld( alignObject, primaryAxisVector = [1, 0, 0], worldAxisToKeep = ['x'], alignTwist = True ):
    
    """
    rotate given object to align with world and only keep selected axis offset
    TIP: good for aligning foot joint with Y world plane, or for clavicles to align with world X and Y plane
    How this works: reference transform is given to this function and is rotated,
                    this object can be then used as reference or directly
    
    :param alignObject: str, name of object to be aligned with rotation to selected world plane
    :param primaryAxisVector: list(float,float,float), list with 3 floats defining object space primary aim axis
    :param worldAxisToKeep: list(str), names of axes to keep in quaternion world space aiming alignement
    :param alignTwist: bool, align object twist rotation as well, axis for this will be chosen automaticly
    :return: None 
    """
    
    # normalize primary axis vector
    primaryAxisVectorVec = vector.makeMVector( primaryAxisVector )
    primaryAxisVectorVec.normalize()
    primaryAxisVector = [ primaryAxisVectorVec.x, primaryAxisVectorVec.y, primaryAxisVectorVec.z ]
    
    
    axisSign = primaryAxisVector[0] + primaryAxisVector[1] + primaryAxisVector[2]
    
    primaryAxisVectorVecMove = primaryAxisVector[:]
    primaryAxisVector = [ abs( primaryAxisVector[0] ), abs( primaryAxisVector[1] ), abs( primaryAxisVector[2] ) ]
    
    # prepare align twist vector
    allaxis = ['x', 'y', 'z']
    
    for axiskeep in worldAxisToKeep:
        
        allaxis.remove( axiskeep.lower() )
    
    skipUpAxis = allaxis[0]
    upVectorMove = {'x':[1, 0, 0], 'y':[0, 1, 0], 'z':[0, 0, 1]}[skipUpAxis]
    upVector = {'x':[1 * axisSign, 0, 0], 'y':[0, 1 * axisSign, 0], 'z':[0, 0, 1 * axisSign]}[skipUpAxis]
    
    # prepare align setup
    prefix = name.removeSuffix( alignObject )
    
    alignObjectAim = mc.group( n = prefix + 'alignObjectAim', em = 1, p = alignObject )
    alignObjectAimUp = mc.group( n = prefix + 'alignObjectAimUp', em = 1, p = alignObject )
    mc.move( primaryAxisVectorVecMove[0], primaryAxisVectorVecMove[1], primaryAxisVectorVecMove[2], alignObjectAim, objectSpace = True )
    mc.move( upVectorMove[0], upVectorMove[1], upVectorMove[2], alignObjectAimUp, objectSpace = True )
    mc.parent( [alignObjectAim, alignObjectAimUp], w = 1 )
    mc.delete( mc.pointConstraint( alignObject, alignObjectAim, skip = worldAxisToKeep ) )
    
    if alignTwist:
        
        mc.delete( mc.pointConstraint( alignObject, alignObjectAimUp, skip = skipUpAxis ) )
    
    # rotate object
    mc.delete( mc.aimConstraint( alignObjectAim, alignObject, aim = primaryAxisVector, u = upVector, wut = 'object', wuo = alignObjectAimUp ) )
    mc.delete( alignObjectAim, alignObjectAimUp )
    
def rotateAlignToReference( toalignobj, refobject, refXasobj = [0, -1, 0], refYasobj = [-1, 0, 0] ):
    
    '''
    aim object X axis and Y axis as up vector to specified directions within reference object space
    tip: useful for specific aiming to other object`s axis
    
    :param toalignobj: str, transform object to be aligned by rotation
    :param refobject: str, transform object to used as orientation reference
    :param refXasobj: list( float, float, float ) specify axis in reference object`s local space which our object will aim with X axis
    :param refYasobj: list( float, float, float ) specify axis in reference object`s local space which our object will aim up vector with Y axis
    :return: None
    '''
    
    targetnull = mc.group( n = 'rotateAlignToReferenceTarget_grp', em = 1, p = refobject )
    mc.setAttr( targetnull + '.t', refXasobj[0], refXasobj[1], refXasobj[2] )
    
    mc.delete( mc.aimConstraint( targetnull, toalignobj, aim = [1, 0, 0], u = [0, 1, 0], wut = 'objectrotation', wuo = refobject, wu = refYasobj ) )
    
    mc.delete( targetnull )    

def makeGroup( prefix = 'new', referenceObj = '', parentObj = '', pos = [0, 0, 0], matchPositionOnly = False, makeLocator = False ):
    
    '''
    creates a transform from a given type
    e.g. myJnt = createTransform('jnt', 'l', 'hand', 'l_arm2_jnt', 'l_handPar_grp')
    
    :param prefix: str, prefix of the transform to be created (suffix will be added according to type)
    :param referenceObj: str, reference transform to be matched
    :param parentObj: str, object to parent the transfrom to
    :param pos: list(float,float,float), world position for new group, referenceObj will override this
    :param matchPositionOnly: bool, match only position of given reference object
    :param makeLocator: bool, make locator instead of group
    :return: str, name of new transform
    '''
    
    if not makeLocator:
        
        obj = mc.group( em = True, n = prefix + '_grp' )
        mc.move( pos[0], pos[1], pos[2], obj )
    
    else:
        
        obj = mc.spaceLocator( p = ( pos[0], pos[1], pos[2] ), n = prefix + '_loc' )[0]
    
    
    # if reference object exists get transfrom and match
    
    if mc.objExists( referenceObj ):
        
        if matchPositionOnly:
            
            mc.delete( mc.pointConstraint( referenceObj, obj ) )
        
        else:
            
            mc.delete( mc.parentConstraint( referenceObj, obj ) )
        
    else:
        
        pass
    
    # parent new transform
    
    if mc.objExists( parentObj ):
        
        obj = mc.parent( obj, parentObj )
        obj = obj[0]
        
    else:
        
        obj = obj
    
    
    return obj

def parent( objects, parentObj, objectNames = [], relative = False, world = False ):
    
    """
    simply parent objects under parent
    this will skip operation if object is already under parent
    
    :param objects: list(str), list of objects to be parented
    :param parentObj: str, name of parent object, this will not be used if world is True
    :param objectNames: list(str), optional, names for renaming objects after parenting, needs to have same length like objects list
    :param relative: bool, relative parenting
    :param world: bool, parent object to world
    :return: None
    """
    
    if not objectNames:
        
        for i in range( len( objects ) ):
            
            objectNames.append( None )
    
    for o, n in zip( objects, objectNames ):
        
        parentsList = getParentList( o, ascending = True )
        
        if parentsList and world:
            
            mc.parent( o, world=True, r = relative )
            continue
        
        if parentsList and not world:
            
            if parentObj == parentsList[0]:
                
                pass
            
            else:
                
                mc.parent( o, parentObj, r = relative )
        
        else:
            
            mc.parent( o, parentObj, r = relative )
        
        if n:
            
            mc.rename( o, n )
            
def getParentList( obj, ascending = True, verbose = False, longNames = False ):
    
    '''
    get list of object parents
    
    :param obj: str, name of object to get its parent list from
    :param ascending: bool, if true parent list is ascending, if false list is descending
    :param fullNames: bool, return parent full names, will return short names by default
    :param verbose: bool, prints function results
    :param longNames: bool, return long names
    :return: list(str), list of parents in order starting from closest parent to top parent
    '''
    
    parents = []
    parentList = mc.listRelatives( obj, f = True, p = True )
    
    
    # check if parent is the world
    if not parentList:
        
        if verbose:
            
            print '# %s parent is world' % obj
            
        return []
    
    
    # split str and delete first empty item    
    parentsRes = parentList[0].split( '|' )[1:]
    
    # get long names
    if longNames:
        
        parentsLongName = []
        for i, p in enumerate( parentsRes ):
            
            parentItems = parentsRes[:i + 1]
            pLongName = '|'.join( parentItems )
            pLongName = '|' + pLongName
            parentsLongName.append( pLongName )
        
        parentsRes = parentsLongName
    
    parentsRes.reverse()    
    
    return parentsRes

def closestObjectAxisToVector( obj, comparevector = [1, 0, 0] ):
    
    '''
    return local object axis vector (e.g. [1,0,0] for X) closest to given world space vector (e.g. [0.2,0.1,0.8])
    
    @param obj: reference object
    @type obj: str
    @param comparevector: world space vector to compare with axes vectors of reference object
    @type comparevector: list( float, float, float )
    @return: list( float, float, float ), signed float values of closest local space axis
    
    NOTE: given vector will be normalized
          output list of floats can be easily used in aimConstraint command aim or up axis
    '''
    
    comparev = vector.makeMVector( [ comparevector[0], comparevector[1], comparevector[2] ] )
    comparev.normalize()
    
    objmx = mc.xform( obj, q = 1, m = 1, ws = 1 )
    objxv = vector.makeMVector( [ objmx[0], objmx[1], objmx[2] ] )
    objyv = vector.makeMVector( [ objmx[4], objmx[5], objmx[6] ] )
    objzv = vector.makeMVector( [ objmx[8], objmx[9], objmx[10] ] )
    
    # get dot products with each object`s axis
    
    xdot = comparev * objxv
    ydot = comparev * objyv
    zdot = comparev * objzv
    
    # set X as closest axis by default
    # get sign of dot product as well
    
    closestax = [ 1, 0, 0 ]
    sign = cmp( xdot, 0 )
    
    
    # make absolute dot product values
    
    xdota = math.fabs( xdot )
    ydota = math.fabs( ydot )
    zdota = math.fabs( zdot )
    
    # compare if other axes are closer
    
    if ydota > xdota:
        
        closestax = [ 0, 1, 0 ]
        sign = cmp( ydot, 0 )
        
        if zdota > ydota:
            
            closestax = [ 0, 0, 1 ]
            sign = cmp( zdot, 0 )
    
    elif zdota > xdota:
        
        closestax = [ 0, 0, 1 ]
        sign = cmp( zdot, 0 )
    
    if sign == 0: sign = 1.0
    
    closestaxsigned = [ sign * n for n in closestax ]
    
    
    return closestaxsigned

def getAveragePositionFromList( positionsList ):
    
    """
    get average position from list of positions (or any XYZ float values)
    
    @param positionList: list( (float,float,float)n ), list of XYZ float value lists
    @return: list( float, float, float ), list of XYZ values computed by averaging all given XYZ values
    """
    
    vectors = [ vector.makeMVector( values = [x, y, z] ) for x, y, z in positionsList ]
    
    vectorsSum = vector.makeMVector()
    
    for v in vectors:
        
        vectorsSum += v
    
    vectorsAverage = vectorsSum / len( positionsList )
    
    return [ vectorsAverage[0], vectorsAverage[1], vectorsAverage[2] ]

def measureDistanceBetweenMultiplePositions( positionList ):
    
    '''
    return sum of distances between chain of positions
    This depends on order of objects as they were passed to function,
    ideal for measuring length of geometry CVs perimeter
    
    :param objectList: list(str), list of transform names
    :return: float, distance sum
    '''
    
    distancesum = 0.0
    
    for i in range( 1, len( positionList ) ):
        
        distancesum += measureDistanceBetween2Points( positionList[i - 1], positionList[i] )
    
    return distancesum

def measureDistanceBetween2Points( pointA, pointB ):
    
    '''
    :param objectA: list(3 floats), first point
    :param objectB: list(3 floats), second point
    :return: float, distance between given points in same space
    '''
    
    vectA = vector.makeMVector( [ pointA[0], pointA[1], pointA[2] ] )
    vectB = vector.makeMVector( [ pointB[0], pointB[1], pointB[2] ] )
    pointDif = vectB - vectA
    
    return pointDif.length()

def measureDistanceBetweenMultipleObjects( objectList ):
    
    '''
    return sum of distances between chain of transforms
    This depends on order of objects as they were passed to function,
    ideal for measuring joint chain length
    
    @param objectList: list of transform names
    @type objectList: list(str)
    @return: float, distance sum
    '''
    
    distancesum = 0.0
    
    for i in range( 1, len( objectList ) ):
        
        distancesum += measureDistanceBetween2Objs( objectList[i - 1], objectList[i] )
    
    return distancesum

def measureDistanceBetween2Objs( objectA, objectB ):
    
    '''
    @param objectA: first object
    @type objectA: str
    @param objectB: second object
    @type objectB: str
    @return: float, distance between given objects
    '''
    
    # first make clean transforms in case user provided transforms have some frozen offsets (happens with clusterHandles)
    
    tempobjA = mc.group( n = 'measureDistanceBetween2ObjsA_grp', em = 1 )
    mc.pointConstraint( objectA, tempobjA )
    tempobjB = mc.group( n = 'measureDistanceBetween2ObjsB_grp', em = 1 )
    mc.pointConstraint( objectB, tempobjB )
    
    # measure distance
    
    pointA = vector.makeMVector( mc.xform( tempobjA, q = 1, t = 1, ws = 1 ) )
    pointB = vector.makeMVector( mc.xform( tempobjB, q = 1, t = 1, ws = 1 ) )
    pointDif = pointB - pointA
    
    mc.delete( tempobjA, tempobjB )
    
    return pointDif.length()

def findClosestObject( refobject, objects ):
    
    '''
    @param refobject: reference object to check distance to other objects
    @type refobject: str
    @param objects: objects to be compared which one is closest
    @type objects: list(str)
    @return: str, name of closest object
    '''
    
    closestObj = objects[0]
    minDist = measureDistanceBetween2Objs( refobject, objects[0] )
    
    for o in objects:
        
        dist = measureDistanceBetween2Objs( refobject, o )
        
        if minDist > dist:
            
            closestObj = o
            minDist = dist
    
    return closestObj
    
def reorientRightHandLoc():
    buildObjsGrp = 'build_objects_grp'
    if not mc.objExists( buildObjsGrp ):
        mc.group( n = buildObjsGrp, em = True )
    lHandJnt = 'l_hand1_jnt'
    rHandJnt = 'r_hand1_jnt'
    lLoc = 'l_handOrientRef_loc'
    mc.delete( mc.pointConstraint( lHandJnt, lLoc ) )
    refLoc = mc.duplicate( lLoc )[0]
    mirrorGrp = mc.group( em = 1 )
    mc.parent( refLoc, mirrorGrp )
    mc.setAttr( mirrorGrp + '.sx', -1 )
    mc.parent( refLoc, w = 1 )
    mc.makeIdentity( refLoc, a = 1, s = 1 )
    rLoc = 'r_handOrientRef_loc'
    if not mc.objExists( rLoc ):
        rLoc = mc.spaceLocator( n = rLoc )[0]
    
    print 'rLoc', rLoc
    lLocLocalScale = mc.getAttr( lLoc + '.localScale' )[0]
    mc.setAttr( rLoc + '.localScale', lLocLocalScale[0], lLocLocalScale[1], lLocLocalScale[2] )
    mc.delete( mc.pointConstraint( rHandJnt, rLoc ) )
    mc.parent( rLoc, refLoc )
    mc.setAttr( rLoc + '.r', 0, 180, 0 )
    parent( [lLoc, rLoc], buildObjsGrp )
    mc.delete( mirrorGrp, refLoc )
    # display local rotation axis
    [ mc.setAttr( loc + '.displayLocalAxis', 1 ) for loc in [lLoc, rLoc] ]

def createOffsetChild( obj, prefix = '', tOffset = ( 0.0, 0.0, 0.0 ), rOffset = ( 0.0, 0.0, 0.0 ), mode = 'grp' ):
    
    '''
    creates a child transform with an offset
    
    @param obj: object to create child of
    @type obj: str
    @param prefix: prefix of the child
    @type prefix: str
    @param tOffset: vector or list for translation offset
    @type tOffset: list(float,float,float)
    @param rOffset: vector or list for rotation offset
    @type rOffset: list(float,float,float)
    @param mode: type of transform to be created
    @type mode: str, can be 'grp', 'jnt' or 'loc'
    @return: str, child transform
    '''
    
    if mode == 'jnt':
        
        raise Exception( '# "jnt" mode is not supported, use Maya joint command' )
    
    makeLoc = False
    
    if mode == 'loc':
        
        makeLoc = True
    
    if not prefix:
        
        prefix = name.removeSuffix( obj ) + 'OffChild'
    
    child = makeGroup( prefix = prefix, referenceObj = obj, parentObj = obj, makeLocator = makeLoc )
    mc.xform( child, t = tOffset, ro = rOffset, r = True )
    
    return child

