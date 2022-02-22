'''
module to make a vector trigger setup at pdb_rigLib.tools
@category Rigging
'''

import maya.cmds as mc

from utils import name

triggerSuffix = 'Trigger'

def makeVectorTrigger( driverTransform, mainGrpParent = '', prefix = '', suffix = 'Front', targetAxis = 'z', targetVal = 1, triggerAxis = 'y', triggerVal = -1  ):
    
    '''
    fuction to make a vector trigger setup using the angle between 2 vector
    :param driverTransform: str, object to drive the trigger locator and reference for base position
    :param mainGrpParent: str, parent of the main group for trigger setup
    :param prefix: str, prefix to name new objects
    :param suffix: str, suffix to name new objects
    :param targetAxis: str, axis to move the target locator
    :param targetVal: str, value to move the target locator for given targetAxis
    :param triggerAxis: str, axis to move the trigger locator
    :param triggerVal: str, value to move the target locator for given triggerAxis
    :return str, name of the end plusMinusAverage node result of the setup (this should drive a remap value to drive the desired object)
    '''
    
    suffix = suffix + triggerSuffix
    
    # get prefix
    if not prefix:
        prefix = name.removeSuffix( driverTransform )
    
    # get trigger setup parent transform
    if not mainGrpParent:
        mainGrpParent = mc.listRelatives( driverTransform, p = True )[0]
        
    if not mainGrpParent:
        mc.error( '# please specify a parent for trigger setup, no parent found for {}'.format( driverTransform ) )

    # make the base group to hold the trigger setup locators, orient and parent it 
    triggerSetupGrp = mc.group( em = True, n = prefix + suffix + '_grp', w = True )
    mc.delete( mc.pointConstraint( driverTransform, triggerSetupGrp ) )
    
    mc.parent( triggerSetupGrp, mainGrpParent )
    
    # create clean group to for trigger locator
    poseGrp = mc.duplicate( triggerSetupGrp, po = True, n = prefix + suffix + 'Pose_grp' )[0]
    mc.parent( poseGrp, triggerSetupGrp )
    
    # create and parent locators, also create decompose matrix for each loc
    locNamesSeq = [ 'Base', 'Target', 'Pose' ]
    locators = []
    dcMatrices = []
    
    for locName in locNamesSeq:
        
        loc = mc.spaceLocator( n = prefix + suffix + locName + '_loc' )[0]
        mc.delete( mc.pointConstraint( driverTransform, loc ) )
        mc.parent( loc, triggerSetupGrp )
        locators.append( loc )
        
        # create decompose matrix
        dcMatrix = mc.createNode('decomposeMatrix', n =  prefix + suffix + locName + '_dcm')
        mc.connectAttr( loc + '.worldMatrix', dcMatrix + '.inputMatrix' )
        dcMatrices.append( dcMatrix )
        
        
    mc.parent( locators[2], poseGrp )
    mc.parentConstraint( driverTransform, poseGrp, mo = True )
    
    # move pose and target locators
    mc.setAttr( locators[1] + '.t{}'.format( targetAxis ), targetVal )
    mc.setAttr( locators[2] + '.t{}'.format( triggerAxis ), triggerVal )
    
    #===========================================================================
    # math 
    #===========================================================================
    
    # get difference between base loc world position and target and pose world position 
    baseTargetDif = mc.createNode( 'plusMinusAverage', n = prefix + suffix + 'BaseTargetDif_pma' )
    mc.setAttr( baseTargetDif + '.operation', 2 ) # subtract operation
    mc.connectAttr( dcMatrices[1] + '.outputTranslate', baseTargetDif + '.input3D[0]' )
    mc.connectAttr( dcMatrices[0] + '.outputTranslate', baseTargetDif + '.input3D[1]' )
    
    basePoseDif = mc.createNode( 'plusMinusAverage', n = prefix + suffix + 'BasePoseDif_pma' )
    mc.setAttr( basePoseDif + '.operation', 2 ) # subtract operation
    mc.connectAttr( dcMatrices[2] + '.outputTranslate', basePoseDif + '.input3D[0]' )
    mc.connectAttr( dcMatrices[0] + '.outputTranslate', basePoseDif + '.input3D[1]' )
    
    # create the angleBetween node to calculate the angle between 2 given vectors
    angleBetween = mc.createNode('angleBetween', n = prefix + suffix + '_anb')
    mc.connectAttr( baseTargetDif + '.output3D', angleBetween + '.vector1' )
    mc.connectAttr( basePoseDif + '.output3D', angleBetween + '.vector2' )
    
    # get the division of the angle between given vectors and a custom given angle
    anglesDivide = mc.createNode( 'multiplyDivide', n = prefix + suffix +  '_mdv')
    mc.setAttr( anglesDivide + '.operation', 2 ) # divide operation
    
    mc.setAttr( anglesDivide + '.input2X', 90 ) # should be the same difference as the angle difference so by default is 1
    
    mc.connectAttr( angleBetween + '.angle', anglesDivide + '.input1X')
    
    # create a condition so value passed can't go above 1
    condition = mc.createNode( 'condition', n = prefix + suffix + '_cdn' )
    mc.setAttr( condition + '.operation', 2 ) # greater than operation
    mc.setAttr( condition + '.secondTerm', 1 )
    mc.setAttr( condition + '.colorIfTrueR', 1 )
    
    mc.connectAttr( anglesDivide + '.outputX',  condition + '.colorIfFalseR' )
    mc.connectAttr( anglesDivide + '.outputX',  condition + '.firstTerm' )
    
    # create end result plus minus average which gives a 0 to 1 value perfect to drive a remap node
    pmaResultNode = mc.createNode( 'plusMinusAverage', n = prefix + suffix + 'Result_pma' )
    mc.setAttr( pmaResultNode + '.operation', 2 ) # subtract operation
    mc.setAttr( pmaResultNode + '.input1D[0]', 1 )
    
    mc.connectAttr( condition + '.outColorR',  pmaResultNode + '.input1D[1]' )
    
    return pmaResultNode
    