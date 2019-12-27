"""
multiple functions to deal with mesh items

"""

import maya.cmds as mc

def checkIFMesh( obj ):
    
    """
    check if passed object is a mesh type
    
    :param obj: str, object to check
    :return bool, true if is mesh type or false if not
    """
            
    shapeObj = mc.listRelatives( obj, s = True )
        
    if not shapeObj:
    
        return None
    
    validTypes = ['mesh']
    
    if not mc.nodeType( shapeObj[0] ) in validTypes:
        
        return None
    
    return True
        
        
          
          