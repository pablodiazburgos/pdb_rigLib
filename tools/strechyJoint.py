"""
strechyJoint at pdb_rigLib.tools
@category Rigging
"""

import pymel.core as pm

import logging
_logger = logging.getLogger( __name__ )


from ..utils import matrix

def setupFromJoint( 
                    rigModule, 
                    strechyJnt, 
                    ikDriver, 
                    mainGrpDriver, 
                    rotateLock = [], 
                    squash = False 
                    ):
    
    
    """
    setup strechy joint using a joint as base
    
    :param prefix: str, prefix for new created objects
    :param rigModule: instance, module instance to parent strechy systems
    :param strechyJnt: pynode, joint to make strechy setups
    :param ikDriver: pynode, tranform to drive the ik 
    :param mainGrpDriver: pynode, transform to drive the main group of the strechy joint 
    :param rotateLock: list(str), transform to drive the main group of the strechy joint
    :param squash: bool, add squash behavior to strechy joint
    
    """
    # get prefix to rename new objects
    if len( strechyJnt.name().split('_') ) > 2:  prefix = strechyJnt.name()[:-4]
    
    # create main group to hold the strechy joints
    mainGrp = pm.group( n = prefix + 'Main_grp', em = True, p = rigModule.Joints )
    mainGrp.setTranslation( strechyJnt.getTranslation(space = 'world'), space = 'world' )
    mainGrp.setRotation( strechyJnt.getRotation(space = 'world'), space = 'world' )
    
    #pm.parentConstraint( mainGrpDriver, mainGrp, mo = True, sr = ['x', 'y', 'z'] )
    matrix.matrixParentConstraint( mainGrpDriver, mainGrp, mo = True, connectTranslate = True, connectRotate = False, connectScale = False )
    
    strechyJnt.setParent( mainGrp )
    
    # make locators
    startLoc = pm.spaceLocator(n = prefix + 'Start_loc')
    startLoc.visibility.set( False )
    startLoc.setParent( mainGrp )
    startLoc.setTranslation( strechyJnt.getTranslation(space = 'world'), space = 'world' )
    
    endLoc = pm.spaceLocator(n = prefix + 'End_loc')
    endLoc.visibility.set( False )
    endLoc.setParent(ikDriver)
    endLoc.setTranslation( strechyJnt.getChildren()[0].getTranslation(space = 'world'), space = 'world' )
    
    # create ik
    _logger.debug( "strechyJnt: {}".format( strechyJnt.name() ) )
    _logger.debug( "strechyJnt_Children: {}".format( strechyJnt.getChildren()[0].name() ) )

    ikHandle = pm.ikHandle( sj = strechyJnt, ee = strechyJnt.getChildren()[0], solver = 'ikSCsolver', n = prefix + '_ikh' )[0] 
    ikHandle.setParent( endLoc )
    ikHandle.visibility.set( False )
    
    # make strech setup
    _stretchSetup(prefix, startLoc, endLoc, strechyJnt, squash, rigModule)
    
    # lock no needed attributes
    if rotateLock:
        for at in rotateLock:
            pm.setAttr( strechyJnt.name() + '.r{}'.format( at ), l = True)
    
def _stretchSetup(prefix, startLoc, endLoc, strechyJnt, squash, rigModule):
    
    # create and connect distance info
    disNode = pm.createNode( 'distanceBetween', n = prefix + '_dis' )
    startLoc.worldMatrix[0].connect( disNode.inMatrix1 )
    endLoc.worldMatrix[0].connect( disNode.inMatrix2 )
    
    # global scale adjustment
    rigModuleMainGrp = pm.PyNode( rigModule.Main )
    scaleCompMdl = pm.createNode( 'multDoubleLinear', n  = prefix + 'ScaleComp_mdl' )
    rigModuleMainGrp.moduleScale.connect( scaleCompMdl.input1 )
    scaleCompMdl.input2.set( disNode.distance.get() )
    
    # make stretch connections
    stretchMdv = pm.createNode( 'multiplyDivide', n = prefix + 'Stretch_mdv' )
    stretchMdv.operation.set( 2 )
    
    disNode.distance.connect( stretchMdv.input1X )
    scaleCompMdl.output.connect( stretchMdv.input2X )
    
    stretchMdv.outputX.connect( strechyJnt.scaleX )
    
    if squash:
        # make squash connections
        squashMdv = pm.createNode( 'multiplyDivide', n = prefix + 'Squash_mdv' )
        squashMdv.operation.set( 2 )
      
        scaleCompMdl.output.connect( squashMdv.input1X )
        disNode.distance.connect( squashMdv.input2X )
        
        squashMdv.outputX.connect( strechyJnt.scaleY )
        squashMdv.outputX.connect( strechyJnt.scaleZ )
            
        
        
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    