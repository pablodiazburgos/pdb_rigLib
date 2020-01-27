'''
mouth module 
@category Rigging @subcategory Rig
'''

import maya.cmds as mc

from ..base import control
from ..base import module

from ..utils import name
from ..utils import anim
from ..utils import transform
from ..utils import connect

def buildSimpleLips(
                    mouthBuilderGrp,
                    baseRigData,
                    jawJnt,
                    headJnt,
                    prefix = 'lips',
                    ctrlScale = 1.0,
                    jawFollowValues = [ 0, 0.050, 0.050, 0.5, 0.5, 0.9, 0.9, 1.0 ],
                    upperJawJnt = None,
                    upperJawFollowValues = [ 1, 0.9, 0.9, 0.5, 0.5, 0.050, 0.050, 0 ]
                    ):
    
    """
    build local setup for 8 lips joints (3 uppers ,3 lowers and corners)
    :param mouthBuilderGrp: str, group that contains the lips joints
    :param baseRigData: instance, base rig data returned from rigbase.base build() to connect visibility channels etc. to the main base
    :param jawJnt: str, name of jaw joint
    :param headJnt: str, name of head joint
    :param prefix: str, prefix to new objects
    :param ctrlScale: float, scale for new objects
    :return list with lips controls
    """
    
    #===========================================================================
    # module
    #===========================================================================
    
    rigmodule = module.Module( prefix )
    rigmodule.connect( baseRigData = baseRigData )
    rigmodule.parent( baseRigData = baseRigData )
    
    # make a local holder joint
    jointHolder = mc.joint( n = 'lipsLocal_jnt' )
    mc.parent( jointHolder, rigmodule.PartsNt )
    mc.delete( mc.pointConstraint( jawJnt, jointHolder ) )
    
    # make a clean jaw jnt to connect to holder grp     
    transform.makeOffsetGrp( jawJnt )
    
    if upperJawJnt:
        transform.makeOffsetGrp( upperJawJnt )
    
    # get a list with lips joints
    lipJnts = mc.listRelatives( mouthBuilderGrp, c = True )
    
    MultNodes = []
    lipCtrls = []
    
    for jnt, followVal, upperJawFollowVal in zip( lipJnts, jawFollowValues, upperJawFollowValues):
        
        lipName = name.removeSuffix( jnt )
        
        lipCtrl = control.Control( prefix = lipName, translateTo = jnt,rotateTo = jnt, scale = 2.0 * ctrlScale, shape = 'diamond', ctrlParent = rigmodule.Controls, defLockHide = ['v'] )
        
        # parent and cleanJoint
        mc.parent( jnt, rigmodule.PartsNt )
        transform.makeOffsetGrp( jnt )
                
        # make direct connection
        for at in ['.t', '.r', '.s']:
            for ax in ['x', 'y', 'z']:
                mc.connectAttr( lipCtrl.C + at + ax,  jnt + at + ax )
                
        # attach jaw to a clean rotate group with direct connection and create a mult node to slow the movement
        rotHolderGrp = mc.group( em = True, r = True, p = jawJnt, n = lipName + '_rotHolder_grp' )
        offHolderGrp = transform.makeOffsetGrp( rotHolderGrp )
        mc.parent( offHolderGrp, rigmodule.Controls  )
        mc.parent( lipCtrl.Off, rotHolderGrp )
        
        if upperJawJnt:
            upperHolderGrp = transform.makeOffsetGrp( rotHolderGrp, prefix = lipName + 'Upper' )
        
        mc.parentConstraint( headJnt, offHolderGrp, mo = True )

        for attr in ['.t', '.r']:
            mdNode = mc.createNode( 'multiplyDivide', n = lipName + attr + '_mld' )
            
            for axis in ['x', 'y', 'z']:
                
                capAxis = axis.capitalize()
                
                mc.connectAttr( jawJnt + attr + axis, mdNode + '.input1%s' % capAxis )
                mc.setAttr( mdNode + '.input2%s' % capAxis, followVal )
                
                mc.connectAttr( mdNode + '.output%s' % capAxis, rotHolderGrp + attr + axis )
        
        
        if upperJawJnt:
            upperJawPrefix = name.getBase( upperJawJnt )
            
            for attr in ['.t', '.r']:
                uppermdNode = mc.createNode( 'multiplyDivide', n = lipName + 'Upper' + attr + '_mld' )
                
                for axis in ['x', 'y', 'z']:
                    
                    capAxis = axis.capitalize()
                    
                    mc.connectAttr( upperJawJnt + attr + axis, uppermdNode + '.input1%s' % capAxis )
                    mc.setAttr( uppermdNode + '.input2%s' % capAxis, upperJawFollowVal )
                    
                    mc.connectAttr( uppermdNode + '.output%s' % capAxis, upperHolderGrp + attr + axis )
                    
            MultNodes.append( uppermdNode )
        
        MultNodes.append( mdNode )
        
            
        lipCtrls.append( lipCtrl )
        
    return {
            'lipsCtrls': lipCtrls,
            'MultNodes': MultNodes,
            'module': rigmodule
            }


































