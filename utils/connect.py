"""
module to manipule some connections
"""

import maya.cmds as mc

def disconnect( plug, source = True, destination = False ):
    
    """
    function to disconnect attributes
    :param plug: str, plug attribute to clean e.g: 'elbow1_jnt.sx'
    :param source: bool, disconnect the source attribute from the given plug
    :param destination: bool, disconnect the destination attributes from the given plug
    :return list[ [str], [str] ], disconnected attributes depending of what was pass 
    """
    
    results = [ [], [] ]
    
    if source:
        # check if there's any source attribute and remove the connections 
        cons = mc.listConnections( plug, s = 1, d = 0, p = 1 )
        if cons:
            
            for con in cons:
                mc.disconnectAttr( con, plug )
                
        results[0] = cons
            
    if destination:
        
        # check if there's any source attribute and remove the connections 
        cons = mc.listConnections( plug, s = 0, d = 1, p = 1)
        
        if cons:
            
            for con in cons:
                
                mc.disconnectAttr( plug, con )
                
        results[1] = cons
    
    return results
    
def reverse( sourceplug, destplug, prefix = 'utilnode' ):
    
    '''
    takes source plug and makes a reverse connection to destination plug
    NOTE: currently only works with single attribute (not compounds like rotate etc.)
    
    :param sourceplug: str, name of source plug (OBJECT.ATTRIBUTE)
    :param destplug: str, name of destination plug (OBJECT.ATTRIBUTE)
    :param prefix: str, prefix name for new objects
    :return: str, name of new reverse node
    '''
    
    revnode = mc.createNode( 'reverse', n = prefix + '_rev' )
    mc.connectAttr( sourceplug, revnode + '.ix' )
    mc.connectAttr( revnode + '.ox', destplug, f = 1 )
    
    return revnode

def multiplySingle( sourceplug, destplug, multValue = 1.0, multPlug = None, prefix = 'multValueNode' ):

    """
    single value plug connection with multiply
    Option to give multiply plug connection instead of static value

    :param sourceplug: str, name of source plug (object.attribute)
    :param destplug: str, optional, name of destination plug (object.attribute)
    :param multValue: float, multiply static value
    :param multPlug: str, optional, name of single value multiply value plug in format <OBJECT.ATTRIBUTE>
    :param prefix: str, prefix name for new objects
    :return: str, name of new multiple node
    """

    multNode = mc.createNode( 'multDoubleLinear', n = prefix + 'Multi_mdl' )
    mc.connectAttr( sourceplug, multNode + '.i1' )

    if multPlug:

        mc.connectAttr( multPlug, multNode + '.i2' )

    else:

        mc.setAttr( multNode + '.i2', multValue )

    mc.connectAttr( multNode + '.o', destplug )

    return destplug

def removeFromAllSets( object ):
    
    '''
    remove parsed object from all sets (objectSet type)
    
    :param object:str, object name
    :return: list(str), names of all sets which this object was connected to
    '''
    
    setList = mc.listConnections( object, d = 1, s = 0, type = 'objectSet' )
    memberSets = []
    
    if not setList:
        
        return memberSets
    
    
    for setName in setList:
        
        if mc.sets( object, isMember = setName ):
            
            mc.sets( object, rm = setName )
            memberSets.append( setName )    
    
    return memberSets

def multiplyDifference( sourceplug, destplug = None, multPlug = None, prefix = 'utilnode', baseValue = 1.0, multiplyValue = 0.5 ):
    
    """
    multiply difference from given base value and then add back
    Useful to change proportions of values that go above or below 1.0
    
    :param sourceplug: str, name of source plug (object.attribute)
    :param destplug: str, optional, name of destination plug (object.attribute)
    :param multPlug: str, optional, name of single value multiply value plug in format <OBJECT.ATTRIBUTE> to multiply difference value
    :param prefix: str, prefix name for new objects
    :param baseValue: float, base value to keep unchanged from source value
    :param multiplyValue: float, if multPlug is None, this value will be used to multiply difference value
    :return: str, output plug which can be connected to other nodes
    """
    
    minusBaseValueNode = mc.createNode( 'addDoubleLinear', n = prefix + 'MinusBaseValue_adl' )
    mc.connectAttr( sourceplug, minusBaseValueNode + '.i1' )
    mc.setAttr( minusBaseValueNode + '.i2', -baseValue )
    
    multiplyDifferenceNode = mc.createNode( 'multDoubleLinear', n = prefix + 'MultByValue_mdl' )
    mc.connectAttr( minusBaseValueNode + '.o', multiplyDifferenceNode + '.i1' )
    
    if multPlug:
        
        mc.connectAttr( multPlug, multiplyDifferenceNode + '.i2' )
    
    else:
        
        mc.setAttr( multiplyDifferenceNode + '.i2', multiplyValue )
        
    
    addToBaseValueNode = mc.createNode( 'addDoubleLinear', n = prefix + 'AddToBaseValue_adl' )
    mc.setAttr( addToBaseValueNode + '.i1', baseValue )
    mc.connectAttr( multiplyDifferenceNode + '.o', addToBaseValueNode + '.i2' )
    
    if destplug:
        
        mc.connectAttr( addToBaseValueNode + '.o', destplug )
    
    return addToBaseValueNode + '.o'

def negate( sourceplug, destplug = None, prefix = 'utilnode' ):
    
    '''
    negate single input value: X * (-1)
    
    :param sourceplug: str, name of source plug (object.attribute)
    :param destplug: str, name of destination plug (object.attribute)
    :param prefix: str, prefix name for new objects
    :return: str, name of new inverse node
    '''
    if not prefix:
        
        nodeName = sourceplug.split( '.' )[-2]
        prefix = name.removeSuffix( nodeName )
        
    multnode = mc.createNode( 'multDoubleLinear', n = prefix + '_mdl' )
    mc.setAttr( multnode + '.i2', -1 )
    mc.connectAttr( sourceplug, multnode + '.i1' )
    
    if destplug:
        
        mc.connectAttr( multnode + '.o', destplug, f = 1 )
    
    return multnode
