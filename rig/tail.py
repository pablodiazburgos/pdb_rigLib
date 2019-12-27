"""
module for tails, tentacles , aerial kind of stuffs
"""

import maya.cmds as mc

from ..base import module
from ..base import control

def buildSimpleIk(
                  chainJoints,
                  chainCurve,
                  prefix = 'tail',
                  ctrlScale = 1.0,
                  colorName = 'primary',
                  fkParenting = True,
                  baseRigData = None,
                  controlsWorldOrient = False,
                  advancedTwist = False,
                  worldUpVector = 'posY'
                  ):
    """
    Note: currently setup only works with 7 cvs 3 degree curve and create 5 controls
    later should be improve to work with n numbers of cvs and be able to create n number of controls
    
    :param chainJoints: list( str ), list of chain joints
    :param chainCurve: str, name of chain cubic curve
    :param prefix: str, prefix to name new objects
    :param rigScale: float, scale factor for size of controls
    :param fkParenting: bool, parent each control to previous one to make FK chain
    :param baseRigData: instance of base.module.Base class
    :param controlsWorldOrient: keep orientation of controls to world
    :param worldUpVector: world up vector for local control orient
    :return: dictionary with rig module objects
    """
    
    #===========================================================================
    # module
    #===========================================================================    
    
    rigmodule = module.Module( prefix )
    rigmodule.parent( baseRigData = baseRigData )
    rigmodule.connect( baseRigData = baseRigData )
    
    # make world up vector directory for later use in orient controls
    worldUpVec = { 'posY':(0, 1, 0), 'negY':(0, -1, 0), 'posZ':(0, 0, 1), 'negZ':(0, 0, -1) }
    
    # make IK handle
    
    chainIk = mc.ikHandle( n = prefix + '_ikh', sol = 'ikSplineSolver', sj = chainJoints[0], ee = chainJoints[-1],
                           c = chainCurve, ccv = 0, parentCurve = 0 )[0]
    
    mc.hide( chainIk )
    mc.parent( chainIk, rigmodule.PartsNt )
    
    # make chain curve clusters
    
    chainCurveCVs = mc.ls( chainCurve + '.cv[*]', fl = 1 )
    numChainCVs = len( chainCurveCVs )
    chainCurveClusters = []
    
    for i in range( numChainCVs ):
        
        cls = mc.cluster( chainCurveCVs[i], n = prefix + 'Cluster%d' % ( i + 1 ) )[1]
        chainCurveClusters.append( cls )
    
    mc.hide( chainCurveClusters )
    mc.parent( chainCurve, rigmodule.PartsNt )
    
    # make attach groups
    baseAttachGrp = mc.group( n = prefix + 'BaseAttach_grp', em = 1, p = rigmodule.Parts )
    mc.delete( mc.pointConstraint( chainJoints[0], baseAttachGrp ) )    
    
    # make controls
    chainControls = []
    
    for i in range( numChainCVs ):
        
        if i == 1 or i == numChainCVs -2:
            continue
        
        chainCtrl = control.Control( prefix = prefix +'%d' % ( i + 1 ), shape = 'circleX', colorName = colorName, 
                                     moveTo = chainCurveClusters[i], scale = ctrlScale * 2, ctrlParent = rigmodule.Controls )

        
        chainControls.append( chainCtrl )
    
    # orient controls
    if not controlsWorldOrient:
        for i in range( len( chainControls ) ):
        
            if i + 1 == len( chainControls ):
                mc.delete( mc.orientConstraint( chainJoints[-1], chainControls[i].Off ) )
                break
                
            mc.delete( mc.aimConstraint( chainControls[i + 1].Off, chainControls[i].Off, aimVector = (1, 0, 0),
                              upVector = (0, 1, 0), worldUpType = 'vector', worldUpVector = worldUpVec[worldUpVector] ) )
        
    # lock rotation for middle controls
    if not fkParenting:
        middleControls = chainControls[1:-1]
        for chainCtrl in middleControls:
            for at in ['.rx', '.ry', '.rz']:
                mc.setAttr( chainCtrl.C + at, l = True, k = False, cb = False )
        
    # parent controls
    if fkParenting:
        for i in range( len( chainControls ) ):
            
            if i == 0:
                
                continue
            mc.parent( chainControls[i].Off, chainControls[i - 1].C )
                
    # attach clusters
    for i in range( numChainCVs ):
        if i == 0 or i == 1:
            mc.parent( chainCurveClusters[i], chainControls[0].C )
            continue
        
        if i == numChainCVs - 1 or i == numChainCVs - 2:
            mc.parent( chainCurveClusters[i], chainControls[-1].C )
            continue
    
        mc.parent( chainCurveClusters[i], chainControls[i - 1].C )
    
    # attach controls
    mc.parentConstraint( baseAttachGrp, chainControls[0].Off, mo = 1 )
    
    
    if advancedTwist:   
        mc.setAttr( chainIk + '.dTwistControlEnable', 1 )
        mc.setAttr( chainIk + '.dWorldUpType', 4 )
        mc.connectAttr( chainControls[0].C + '.worldMatrix[0]', chainIk + '.dWorldUpMatrix' )
        mc.connectAttr( chainControls[-1].C + '.worldMatrix[0]', chainIk + '.dWorldUpMatrixEnd' )
    else:
        # add twist attribute
        twistAt = 'twist'
        mc.addAttr( chainControls[-1].C, ln = twistAt, k = 1 )
        mc.connectAttr( chainControls[-1].C + '.' + twistAt, chainIk + '.twist' )
    
    return{
        'module':rigmodule,
        'mainGrp':rigmodule.Main,
        'ctrlGrp':rigmodule.Controls,    
        'controls':chainControls,
        'attachGrp':baseAttachGrp
        }
    
    
    
    
    
    
    
    
    
    
    
    
    
    