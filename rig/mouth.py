'''
mouth module 
@category Rigging @subcategory Rig
'''

import maya.cmds as mc
import pymel.core as pm

from ..base import control
from ..base import module

from ..utils import name
from ..utils import anim
from ..utils import transform
from ..utils import connect
from ..utils import shape

#TODO: commment builLips func 
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


def buildLips(
                baseRigData,
                jawJnt,
                headJnt,
                upperJawJnt = '',
                followUpperJaw = False,
                prefix = 'lips',
                ctrlScale = 1.0,
                ):
    
    '''
    module to create a local lips setup with corner joints
    '''
    
    # create pynodes
    jawJnt = pm.PyNode( jawJnt )
    headJnt = pm.PyNode( headJnt )
    
    if followUpperJaw:
        headJnt = pm.PyNode( upperJawJnt )
    
    # define upper / lower / mid lips
    midUpperJnt = pm.PyNode('mouthUpperMid_jnt')
    midLowerJnt = pm.PyNode('mouthLowerMid_jnt')
    
    lUpperJnt = pm.PyNode('l_mouthUpper_jnt')
    lLowerJnt = pm.PyNode('l_mouthLower_jnt')
    rUpperJnt = pm.PyNode('r_mouthUpper_jnt')
    rLowerJnt = pm.PyNode('r_mouthLower_jnt')
    
    lUpperCornerJnt = pm.PyNode('l_mouthUpperCorner_jnt')
    lLowerCornerJnt = pm.PyNode('l_mouthLowerCorner_jnt')
    rUpperCornerJnt = pm.PyNode('r_mouthUpperCorner_jnt')
    rLowerCornerJnt = pm.PyNode('r_mouthLowerCorner_jnt')
    
    lCornerJnt = pm.PyNode('l_mouthCorner_jnt')
    rCornerJnt = pm.PyNode('r_mouthCorner_jnt')

    
    #===========================================================================
    # module
    #===========================================================================
    
    rigmodule = module.Module( prefix )
    rigmodule.connect( baseRigData = baseRigData )
    rigmodule.parent( baseRigData = baseRigData )
    
    # create a skin holder joint and parent it
    holderJnt = jawJnt.duplicate( po = True, n = prefix + 'Local1_jnt' )[0].setParent( rigmodule.PartsNt )
    
    
    #===========================================================================
    # create upper / lower joints setup
    #===========================================================================
    
    mainCtrls = []
    retMainCtrls = []
    
    for lipJoints, prefixName in zip ( [ [ lUpperJnt, midUpperJnt, rUpperJnt ], [ lLowerJnt, midLowerJnt, rLowerJnt ], [ lUpperCornerJnt, lCornerJnt, lLowerCornerJnt ], [ rUpperCornerJnt, rCornerJnt, rLowerCornerJnt ] ], ['upper', 'lower', 'l_corner', 'r_corner'] ):
        
        # create main and groups control which will drive joints 
        mainCtrl = control.Control(prefix =  prefixName + 'LipMain', shape = 'circle', moveTo = lipJoints[1].name(), rotateTo = lipJoints[1].name(), colorName = 'primary', scale = ctrlScale * 2, ctrlParent = rigmodule.Controls, defLockHide = ['v'])
        shape.translateRotate( mainCtrl.C, pos = [0, 0, 0], rot = [0, 90, 0], localSpace = True, relative = True )
        
        retMainCtrls.append( mainCtrl )
        
        mainCtrl = pm.PyNode( mainCtrl.C )
        mainCtrls.append( mainCtrl )
        
        # create mainLocalGrp to later hold upper/lower localLip joints
        mainLocalGrp = pm.group( n = prefixName + 'LipMainLocal_grp', em = True, w = True )
        mainLocalGrp.setTranslation( lipJoints[1].getTranslation( space = 'world' ), space = 'world' )
        mainLocalGrp.setRotation( lipJoints[1].getRotation( space = 'world' ), space = 'world' )
        mainLocalGrp.setParent( rigmodule.PartsNt )
        
        # create offsetGrp for mainLocalGrp so it can be driven by direct connection
        transform.makeOffsetGrp( mainLocalGrp.name() )
        
        # make direct connection
        mainCtrl.translate.connect( mainLocalGrp.translate )
        mainCtrl.rotate.connect( mainLocalGrp.rotate )
        mainCtrl.scale.connect( mainLocalGrp.scale )
        
        # create offset group per joint to be clean and it can be driven by direct connection
        for jnt in lipJoints:
            offGrp = pm.PyNode( transform.makeOffsetGrp( jnt.name() ) )
            offGrp.setParent( mainLocalGrp )
            
            # create control per joint and parent it
            prefix = name.removeSuffix( jnt.name() )
            jntCtrl = control.Control(prefix =  prefix, shape = 'square', moveTo = jnt.name(), rotateTo = jnt.name(), colorName = 'secondary', scale = ctrlScale * 0.5, ctrlParent = mainCtrl.name(), defLockHide = ['v'])
            shape.translateRotate( jntCtrl.C, pos = [0, 0, 0], rot = [90, 0, 0], localSpace = True, relative = True )

            # make direct connections
            jntCtrl = pm.PyNode( jntCtrl.C )
            
            jntCtrl.translate.connect( jnt.translate )
            jntCtrl.rotate.connect( jnt.rotate )
            jntCtrl.scale.connect( jnt.scale )
            
            
    # make contraints to globally drive the lips controls with the rig
    pm.parentConstraint( headJnt, mainCtrls[0].getParent(), mo = True )
    pm.parentConstraint( jawJnt, mainCtrls[1].getParent(), mo = True )
    
    pm.parentConstraint( jawJnt, headJnt, mainCtrls[2].getParent(), mo = True )
    pm.parentConstraint( jawJnt, headJnt, mainCtrls[3].getParent(), mo = True )
        

    return {
        'mainCtrls': retMainCtrls
            }







