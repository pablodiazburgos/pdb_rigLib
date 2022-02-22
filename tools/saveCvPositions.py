'''
save / load position for Cvs
@category Rigging
@tags cv position save load xml

Saving and loading CV positions using XML files
'''

import os.path
import string
from xml.dom import minidom
from xml.dom.minidom import Document

import maya.cmds as mc
import maya.mel as mel

from utils import name


def save( path, objects ):
    
    '''
    Save positions of CVs of nurbs curve shapes, later could support other types
    
    :param path:str, file path, e.g. '/u/jbk/shapedata/nicecurves.xml'
    :param objects: list( str ) names of objects (curves) to save CV positions
    :return: None
    '''
    
    # check file path
    
    pathDir = os.path.dirname( path )
    
    if not os.path.exists( pathDir ):
        
        raise Exception( 'directory doesnt exist, cannot save shapes, path: %s' % pathDir )
    
    doc = Document()
    xml = doc.createElement( 'SHAPE_CV_POSITIONS' )
    doc.appendChild( xml )
    
    objectList = []
    
    for obj in objects:
        shapesList = mc.listRelatives( obj, s = 1 )
        
        if len( shapesList ) > 1:
            
            objectList.extend( shapesList )
        else:
            
            objectList.extend( [ obj ] )
            
    
    for o in objectList:
        
        objdoc = doc.createElement( 'OBJECT' )
        xml.appendChild( objdoc )
        
        oShort = name.short( o )
        objdoc.setAttribute( 'name', oShort )
        
        # type
        shapesList = mc.listRelatives( o, s = 1, f = 1 )
        
        if not shapesList:
            
            type = mc.nodeType( o )
        
        else:
        
            type = mc.nodeType( shapesList[0] )
        
        
        objdoc.setAttribute( 'type', type )
        
        # cv positions
        
        cvdoc = doc.createElement( 'controlPoints' )
        objdoc.appendChild( cvdoc )
        
        
        
        cvs = mc.ls( ( o + '.cv[*]' ), l = 1, fl = 1 )
        
        for i in range( len( cvs ) ):
            pos = mc.xform( cvs[i], q = 1, ws = 1, t = 1 )
            cvdoc.setAttribute( ( 'cv' + str( i ) ), ( str( pos[0] ) + ' ' + str( pos[1] ) + ' ' + str( pos[2] ) ) )
        
        # override color
        
        displayDoc = doc.createElement( 'display' )
        objdoc.appendChild( displayDoc )
        
        shapes = mc.listRelatives( o, s = 1 )
        
        if not shapes: shapes = [o]
        
        if isinstance( shapes, list ) and mc.getAttr( shapes[0] + '.ove' ) == 1:
            
            displayDoc.setAttribute( 'ove', '1' )
            displayDoc.setAttribute( 'ovc', str( mc.getAttr( shapes[0] + '.ovc' ) ) )
        
        else:
            
            displayDoc.setAttribute( 'ove', '0' )
            displayDoc.setAttribute( 'ovc', str( mc.getAttr( shapes[0] + '.ovc' ) ) )
            
            
    
    file = open( path, 'w' )
    pretty = doc.toprettyxml( indent = '     ' )
    file.write( pretty )
    file.close



def load( path, objects = [], loadColor = False, verbose = True ):
    
    '''
    Load positions of CVs of nurbs curve shapes, later could support other types
    
    :param path: str, file path, e.g. '/u/jbk/shapedata/nicecurves.xml'
    :param objects: list( str ), names of objects (curves) to load CV positions, if None is passed, all objects will be loaded 
    :return: None
    '''
    
    # check file path
    
    if not os.path.exists( path ):
        
        raise Exception( 'path doesnt exist, cannot load shapes, path: %s' % path )
    
    # check if should be passed only object or it relative shapes
    
    objectList = []
    
    for obj in objects:
        shapesList = mc.listRelatives( obj, s = 1 )
        
        if len( shapesList ) > 1:
            
            objectList.extend( shapesList )
        else:
            
            objectList.extend( [ obj ] )
            
    objects = objectList
    
    # open xml file using minidom module
    
    doc = minidom.parse( path )
    
    objectEs = doc.getElementsByTagName( 'OBJECT' )
    
    objectShorts = []
    
    if objects:
        
        for o in objects:
            
            objectShorts.append( name.short( o ) )
    
    for e in objectEs:
        
        objname = e.getAttribute( 'name' )
        
        if objects and not objname in objectShorts:
            
            continue
        
        if not mc.objExists( objname ):
            
            if verbose: print '# loading shapes. Object %s doesn`t exist, skipping' % objname
            continue
        
        compTyp = ''
        
        if( e.getAttribute( 'type' ) == 'nurbsCurve' ):
            
            compTyp = 'cv'
        
        if not mc.objExists( objname + '.' + compTyp + '[*]' ):
            
            continue
        
        cvs = mc.ls( ( objname + '.' + compTyp + '[*]' ), l = 1, fl = 1 )
        cvsE = e.getElementsByTagName( 'controlPoints' )[0]
        
        for i in range( len( cvs ) ):
            
            posStr = cvsE.getAttribute( 'cv' + str( i ) )
            posList = string.split( posStr )
            
            if not posList or len( posList ) < 3:
                
                continue
            
            px = string.atof( posList[0] )
            py = string.atof( posList[1] )
            pz = string.atof( posList[2] )
            
            mc.xform( objname + '.cv[' + str( i ) + ']', ws = 1, t = [px, py, pz] )
        
        if loadColor:
            
            shapes = mc.listRelatives( objname, s = 1 )
            if not shapes: shapes = [objname]
            if isinstance( shapes, list ):
                
                displayE = e.getElementsByTagName( 'display' )[0]
                oveVal = displayE.getAttribute( 'ove' )
                ovcVal = displayE.getAttribute( 'ovc' )
                ovcValI = string.atoi( ovcVal )
                
                if oveVal == '1': mc.setAttr( shapes[0] + '.ovc', ovcValI )
            
            
            
            
