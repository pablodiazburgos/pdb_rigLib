"""
name @utils

Utilities to work with names and strings
"""

import re
import maya.cmds as mc

def removeSuffix( name ):

    """
    Remove suffix from given name string
    :param name: str, given name string to process
    :return: str, name without suffix
    """

    edits = name.split( '_' )

    if len( edits ) < 2:

        return name

    suffix = '_' + edits[-1]
    nameNoSuffix = name[ : -len( suffix )]

    return nameNoSuffix

def getSide( name ):
    """
    Get the side for the given string
    
    :param name: str, name to get the side of
    :return 'l', 'r', ''
    """
    
    # make sure is not a full dag path
    edit = name.split('|')[-1]
    
    # make sure is lowerCase and return the side
    edit = edit.lower()
    
    if edit.startswith('l_'): return 'l'
    if edit.startswith('r_'): return 'r'
    
    return ''

def checkClashingNames():
    
    """
    check if there is any clashing name in the scene , if there is something it will return in a list
    """
    
    clashedNames = [ o for o in mc.ls() if o.count('|') ]
    
    return clashedNames

def removePrefix( name ):
    """
    Remove prefix from given name string
    :param name: str, given name string to process
    :return: str, name without prefix
    """
    # get short name 
    edit = name.split('|')[-1]
    
    edit = edit.split('_')
    
    prefix = edit[0] + '_'
    
    nameNoPrefix = name[ len( prefix ): ]
    
    return nameNoPrefix

def short ( name ):
    
    return  name.split( '|' )[-1]

def removeSide( name ):
    
    """
    remove the side from given name in case that exists
    :param name: str, name to remove the side
    :return str, given name without side
    """
    
    lside = 'l_'
    rside = 'r_'
    midside = 'c_'
    
    edit = name
    
    if name[:2] in [ lside, rside, midside ]:
        
        edit = name[2:]
    
    return edit

def removeNamespace( name ):
    
    if not ':' in name: return name
    
    edit = name.split( ':' )[-1]
    
    return  edit

def removeEndNumbers( name ):
    
    '''
    :param name: str, string to strip off numbers off the end
    :return str, without end number
    
    remove all numbers at the end of the name, e.g. 'l_leg1' --> 'l_leg'
    '''
    
    pattern = re.compile( '[0-9]*$' )
    res = re.search( pattern, name )
    endlen = len( res.group( 0 ) )
    
    if not endlen: return name
    else: return name[ 0:len( name ) - endlen ]

def getBase( name, keepSide = True ):
    
    edit = name.split( '|' )[-1]
    edit = removeEndNumbers( edit )
    
    if name.count( '_' ):
        
        edit = removeSuffix( edit )
        editLowerCase = edit.lower()
        edit = removeEndNumbers( edit )
        
        if editLowerCase.startswith( 'l_' ) or editLowerCase.startswith( 'r_' ):
            
            if not keepSide:
                
                return edit[2:]
    
    
    return edit    

def getSideAsSign( name ):
    
    '''
    :param name: str, object`s name
    :return: int, valid values: -1,0,1
    
    return 0 for center, 1 for left and -1 for right
    '''
    
    editStr = name.lower()
    
    if len( name ) > 1:
        
        editStr = getSide( name )
    
    if editStr == 'l': return 1
    if editStr == 'r': return -1
    
    return 0

def getAvailableNamespace( namespaceName ):
    
    '''
    this function will check given namespace and return the same if there is no such namespace,
    but in case this namespace already exists in scene, it will increment +1 until this is unique
    
    NOTE: this works locally in any current namespace, which can be under other namespace then root ":",
          it is user or function to set the local namespace before this function is used
    '''
    
    allNsList = mc.namespaceInfo( ls = 1 )
    
    availableNamespace = namespaceName
    
    # remove numbers from end of namespace for incrementing
    
    namespaceNameNoNums = removeEndNumbers( namespaceName )
    counter = 1
    whatIfCount = 1000
    
    while availableNamespace in allNsList:
        
        edit = namespaceNameNoNums + '_%03d' % counter
        availableNamespace = edit
        
        if counter > whatIfCount:
            
            break
    
    return availableNamespace

def getSuffix(name):
    """
    Get suffix for the given string
    
    :param name: str, name to get the side of
    :return if suffix will return suffix or None in case nothing was found
    """
    name = short( name )
    
    if name.count( '_' ) == 0:
        
        return ''
    
    edit = name.split( '_' )[-1]
    
    return edit