
import logging
_logger = logging.getLogger( __name__ )

import pymel.core as pm

from ..base import control

from ..utils import matrix
from ..utils import name

#TODO check changing parent constraint to baseVolJnt from baseJnt to rotJnt Point constraint
#TODO and orient constraint from baseJnt this will help in strechy joints

def createFromJoint( 
                    baseJnt,
                    rotJnt,
                    prefix = '',
                    setupParent = '',
                    jointsParent = '',
                    controlsParent = '',
                    rSide = False
                     ):
    
    '''
    Creates a volume joints setup based on angle between two passed joints
    :param baseJnt: PyNode, base joint used to hold transforms
    :param rotJnt: PyNode, joint used as rotation reference for the angle calculations
    :param prefix: str, prefix for rename new objects
    :param structureParent: str, parent under this transform the setup groups
    :param jointsParent: str, parent under this transform the structure groups 
    :param controlsParent: str, parent under this transform the control groups
    :param rSide: bool, this should be true to pass down proper right side values
    '''
    
    # get prefix from baseJnt
    if not prefix:
        prefix = name.getBase( rotJnt.name() )
    
    prefix = prefix + 'Vol_'
    
    # create groups structure
    mainSetupGrp = pm.group( em = True, n = prefix + 'setup_grp', p = setupParent )
    childOffsetSetupGrp = pm.group( em = True, n = prefix + 'setupChildOffset_grp', p = mainSetupGrp )
    
    # make matrix constraint
    pm.delete(pm.parentConstraint( rotJnt, childOffsetSetupGrp ) )
    matrix.matrixParentConstraint( baseJnt, childOffsetSetupGrp, mo = True, connectTranslate = True, connectRotate = True, connectScale = False )
    
    # create setup group hierarchy and connections
    rotAngleReader, upAngleReader = _createSetupGroups( prefix, childOffsetSetupGrp, baseJnt, rotJnt, rSide )
    
    _logger.debug( "rotAngleReader: {}".format( rotAngleReader ) )
    _logger.debug( "upAngleReader: {}".format( upAngleReader ) )
    
    # create controls setup
    mainControlsGrp = pm.group( em = True, n = prefix + 'controls_grp', p = controlsParent )
    childOffsetControlsGrp = pm.group( em = True, n = prefix + 'controlsChildOffset_grp', p = mainControlsGrp )
  
    # make matrix constraint 
    pm.delete(pm.parentConstraint( rotJnt, childOffsetControlsGrp ) )
    matrix.matrixParentConstraint( baseJnt, childOffsetControlsGrp, mo = True, connectTranslate = True, connectRotate = True, connectScale = False )
    
    
    # create volume main base joint
    volBaseJnt = rotJnt.duplicate( po = True, n = prefix + 'main_jnt' )[0].setParent( jointsParent )
    volBaseJnt.setObjectColor(2) # dark yellow
    volBaseJnt.setRadius( rotJnt.getRadius() * 0.5 )
    pm.parentConstraint( baseJnt, volBaseJnt, mo = True )
    
    
    # create each control to later drive each volume joint passing specific joint attributes or values
    prefixSeq = ['N', 'S', 'E', 'W']
    currentValFlipSeq = [1.0, -1.0, 1.0, -1.0]
    ctrlShapeSeq = ['triangleZ', 'inverseTriangleZ', 'triangle', 'inverseTriangle']
    
    if rSide:
        currentValFlipSeq = [-1.0, 1.0, -1.0, 1.0]
        ctrlShapeSeq = ['inverseTriangleZ', 'triangleZ', 'inverseTriangle', 'triangle']
    
    transDefaultAxisSeq = ['.tz', '.tz', '.ty', '.ty']

    volCtrls = []
    
    for i in range( len(prefixSeq) ):
        
        ctrlPrefix = prefix + prefixSeq[i]
        currentValFlip = currentValFlipSeq[i]
        transDefaultAxis = transDefaultAxisSeq[i]
        ctrlShape = ctrlShapeSeq[i]
        
        # debug info
        _logger.debug( "ctrlPrefix: {}".format( ctrlPrefix ) )

    
        volCtrl = _createControl(ctrlPrefix, rotJnt, rotAngleReader, upAngleReader, childOffsetControlsGrp, currentValFlip, transDefaultAxis, ctrlShape)
        
        _createVolumeJoint( ctrlPrefix, volCtrl, volBaseJnt )
        
        volCtrls.append( volCtrl )
    
    return volCtrls
    
def _createSetupGroups(prefix, childOffsetSetupGrp, baseJnt, rotJnt, rSide ):
    '''
    Creates rotAngleReader and upAngleReader hierarchy and connections
    '''
    
    
    angleReaderNames = ['rotAngleReader', 'upAngleReader']
    upTrgvalues = [ (0, 0, -10), (0, -10, 0) ]
    aimValue = 10
    if rSide:
        upTrgvalues = [ (0, 0, 10), (0, 10, 0) ]
        aimValue = -10
    
    angleReaders = []
    
    for i in range(2):
        
        anglePrefix = prefix + angleReaderNames[i]
        
        mainAngleReaderGrp = childOffsetSetupGrp.duplicate( n = anglePrefix + '_main_grp', po = True )[0].setParent( childOffsetSetupGrp )
        
        # create averate rotation setup
        avgGrp = mainAngleReaderGrp.duplicate( n = anglePrefix + '_avg_grp', po = True )[0].setParent( mainAngleReaderGrp )
        
        startGrp = avgGrp.duplicate( n = anglePrefix + '_start_trg', po = True )[0].setParent( avgGrp )
        endGrp = avgGrp.duplicate( n = anglePrefix + '_end_trg', po = True )[0].setParent( avgGrp )
        avgGrp = avgGrp.duplicate( n = anglePrefix + '_avg_trg', po = True )[0].setParent( avgGrp )
        
        # make constraints for average groups so we can extracts the rotations from
        matrix.matrixParentConstraint( baseJnt, startGrp, mo = True, connectTranslate = False, connectRotate = True, connectScale = False )
        matrix.matrixParentConstraint( rotJnt, endGrp, mo = True, connectTranslate = False, connectRotate = True, connectScale = False )
        
        oriCons = pm.parentConstraint( startGrp, endGrp, avgGrp, mo = True )
        oriCons.interpType.set( 2 )

        # create rotation aim/up setup which will be used in angle calculations
        rotGrp = mainAngleReaderGrp.duplicate( n = anglePrefix + '_rot_grp', po = True )[0].setParent( mainAngleReaderGrp )
        angleGrp = rotGrp.duplicate( n = anglePrefix + '_angle_grp', po = True )[0].setParent( rotGrp )

        aimGrp = rotGrp.duplicate( n = anglePrefix + '_aim_trg', po = True )[0].setParent( angleGrp )
        aimGrp.displayHandle.set(1)
        aimGrp.translateX.set(aimValue)
        matrix.matrixParentConstraint( avgGrp, aimGrp, mo = True, connectTranslate = True, connectRotate = True, connectScale = False )
        
        upGrp = rotGrp.duplicate( n = anglePrefix + '_up_trg', po = True )[0].setParent( angleGrp )
        upGrp.displayHandle.set(1)
        upGrp.setTranslation( upTrgvalues[i] )
        
        # CREATE ANGLE IN BETWEEN CONNECTIONS
        angBtween = pm.createNode( 'angleBetween', n = anglePrefix + '_abw' )
        pm.addAttr( angBtween, ln = 'zAngle', at = 'float' )
        
        aimGrp.translate.connect( angBtween.vector1, f = True )
        upGrp.translate.connect( angBtween.vector2, f = True )
        
        # create plus minus average to substract 90 of the angle and keep it at 0 by default
        pmaZeroAngle = pm.createNode( 'plusMinusAverage', n = anglePrefix + '_zero_pma' )
        pmaZeroAngle.operation.set( 2 )
        pmaZeroAngle.input1D[0].set( 90 )
        angBtween.angle.connect( pmaZeroAngle.input1D[1] )
        
        # create multiply divide for angle readers
        mdlDoubleAngle = pm.createNode( 'multDoubleLinear', n = anglePrefix + '_double_mdl' )
        mdlDoubleAngle.input1.set( 2 )
        pmaZeroAngle.output1D.connect( mdlDoubleAngle.input2 )
        
        mdlDoubleAngle.output.connect( angBtween.zAngle )
            
        angleReaders.append( angBtween )
        
    
    return angleReaders
    
def _createControl (prefix, rotJnt, rotAngleReader, upAngleReader, childOffsetControlsGrp, currentValFlip, transDefaultAxis, ctrlShape):
    
    '''
    Create controls structure and connections
    '''
    
    controlIns = control.Control ( prefix = prefix, shape = ctrlShape, moveTo = rotJnt.name(), rotateTo = rotJnt.name(), colorName = 'secondary', scale = 2, ctrlParent = childOffsetControlsGrp.name(), defLockHide = ['v', 's'] ) 
    
    volCtrl = pm.PyNode( controlIns.C )
    
    # create control hierarchy with offset groups
    offCtrlGrp = pm.PyNode( controlIns.Off )
    startCtrlGrp = childOffsetControlsGrp.duplicate( n = prefix + '_start_grp', po = True )[0].setParent( offCtrlGrp )
    endCtrlGrp = childOffsetControlsGrp.duplicate( n = prefix + '_end_grp', po = True )[0].setParent( startCtrlGrp )
    volCtrl.setParent( endCtrlGrp )
    
    
    _createControlAttributes( volCtrl )
    
    # connect angle readers
    rotAngleReader.zAngle.connect( volCtrl.rotCurrentAngle )
    upAngleReader.zAngle.connect( volCtrl.upCurrentAngle )
    
    # make attributes connections
    _makeAttributesConnections( prefix, volCtrl, offCtrlGrp, endCtrlGrp, currentValFlip, transDefaultAxis )
    
    return volCtrl
    
def _createControlAttributes( volCtrl ):
    
    '''
    Create volume attributes for passed control
    '''
    
    # VOLUME OPTIONS
    pm.addAttr(volCtrl, ln = 'volumeJointOptions', at = 'enum', en = '________________', k = False) 
    volCtrl.volumeJointOptions.set(cb = True, l = True)
    
    pm.addAttr( volCtrl, ln = 'envelope', at = 'float', min = 0.0, max = 1.0, dv = 0.25, k = False )
    volCtrl.envelope.set( cb = True )
    
    # PUSH OPTIONS
    pm.addAttr( volCtrl, ln = 'pushOptions', at = 'enum', en = '________________', k = False )
    volCtrl.pushOptions.set(cb = True, l = True)
    
    pm.addAttr( volCtrl, ln = 'readFromAxis', at = 'enum', en = 'rot:up', k = False )
    volCtrl.readFromAxis.set(cb = True)
    
    pm.addAttr( volCtrl, ln = 'rotCurrentAngle', at = 'float', k = False )
    pm.addAttr( volCtrl, ln = 'upCurrentAngle', at = 'float', k = False )
    
    pm.addAttr( volCtrl, ln = 'currentAngle', at = 'float', k = False )
    volCtrl.currentAngle.set(cb = True)
    
    pm.addAttr( volCtrl, ln = 'minAngle', at = 'float', dv = -180, k = False )
    volCtrl.minAngle.set(cb = True)
    
    pm.addAttr( volCtrl, ln = 'startAngle', at = 'float', dv = 0, k = False )
    volCtrl.startAngle.set(cb = True)
    
    pm.addAttr( volCtrl, ln = 'maxAngle', at = 'float', dv = 180, k = False )
    volCtrl.maxAngle.set(cb = True)    

    pm.addAttr( volCtrl, ln = 'currentValue', at = 'float', k = False )
    volCtrl.currentValue.set(cb = True) 
    
    pm.addAttr( volCtrl, ln = 'defaultValue', at = 'float', dv = 0.1, k = False )
    volCtrl.defaultValue.set(l = True) 
    
    pm.addAttr( volCtrl, ln = 'minValue', at = 'float', k = False )
    volCtrl.minValue.set( cb = True) 
    
    pm.addAttr( volCtrl, ln = 'startValue', at = 'float', k = False )
    volCtrl.startValue.set( cb = True) 
    
    pm.addAttr( volCtrl, ln = 'maxValue', at = 'float', dv = 2.0, k = False )
    volCtrl.maxValue.set( cb = True) 
    
    # ROTATION OPTIONS
    pm.addAttr( volCtrl, ln = 'rotationOptions', at = 'enum', en = '________________', k = False )
    volCtrl.rotationOptions.set(cb = True, l = True)
    
    pm.addAttr( volCtrl, ln = 'rotOffset', at = 'float', k = False )
    volCtrl.rotOffset.set( cb = True) 
    
    pm.addAttr( volCtrl, ln = 'rotValue', at = 'float', min = -1.0, max = 1.0, dv = 0.5, k = False )
    volCtrl.rotValue.set( cb = True) 
    
    pm.addAttr( volCtrl, ln = 'upOffset', at = 'float', k = False )
    volCtrl.upOffset.set( cb = True) 
    
    pm.addAttr( volCtrl, ln = 'upValue', at = 'float', min = -1.0, max = 1.0, dv = 0.5, k = False )
    volCtrl.upValue.set( cb = True) 
    
def _makeAttributesConnections( prefix, volCtrl, offCtrlGrp, endCtrlGrp, currentValFlip, transDefaultAxis ):
    
    '''
    make all the connections needed by the control attributes
    '''
    
    _createOffsetCtrlGrpConnections( prefix, volCtrl, offCtrlGrp )
    
    _createEndCtrlGrpConnections( prefix, volCtrl, endCtrlGrp, currentValFlip, transDefaultAxis )
    
def _createOffsetCtrlGrpConnections( prefix, volCtrl, offCtrlGrp ):
 
    # read from axis condition to switch between upAngle and rotAngle 
    readAxisAngleCnd = pm.createNode( 'condition', n = prefix + '_readAxisAngle_cnd' )
    volCtrl.readFromAxis.connect( readAxisAngleCnd.firstTerm )
    volCtrl.rotCurrentAngle.connect( readAxisAngleCnd.colorIfTrueR )
    volCtrl.upCurrentAngle.connect( readAxisAngleCnd.colorIfFalseR )
    
    readAxisAngleCnd.outColorR.connect( volCtrl.currentAngle, f = True )
    volCtrl.currentAngle.lock()

    
    # create reducer multiply divide for later use in rotation offsets
    reducerMdv = pm.createNode( 'multiplyDivide', n = prefix + '_reducer_mdv' )
    volCtrl.rotCurrentAngle.connect( reducerMdv.input1Y )
    volCtrl.rotValue.connect( reducerMdv.input2X )
    volCtrl.upCurrentAngle.connect( reducerMdv.input1X )
    volCtrl.upValue.connect( reducerMdv.input2Y )
    
    # create plus minus average to sum offset from rotate and up angles values 
    rotOfsPma = pm.createNode( 'plusMinusAverage', n = prefix + '_rotOfs_pma' )
    volCtrl.rotOffset.connect( rotOfsPma.input2D[0].input2Dx )
    volCtrl.upOffset.connect( rotOfsPma.input2D[0].input2Dy )
    reducerMdv.outputX.connect( rotOfsPma.input2D[1].input2Dx )
    reducerMdv.outputY.connect( rotOfsPma.input2D[1].input2Dy )
    
    rotOfsPma.output2Dy.connect( offCtrlGrp.rotateY )
   
    #rotOfsPma.output2Dx.connect( offCtrlGrp.rotateZ )
    # reverse rotateZ value
    revRotOffMdl = pm.createNode( 'multDoubleLinear', n = prefix + '_reverseRotOfs_mdl' )
    rotOfsPma.output2Dx.connect( revRotOffMdl.input1 )
    revRotOffMdl.input2.set( -1 )
    
    revRotOffMdl.output.connect( offCtrlGrp.rotateZ )

def _createEndCtrlGrpConnections( prefix, volCtrl, endCtrlGrp, currentValFlip, transDefaultAxis ):
    
    # create range
    setRange = pm.createNode( 'setRange', n = prefix + '_rng' )
    volCtrl.startValue.connect( setRange.maxX )
    volCtrl.maxValue.connect( setRange.maxY )
    
    volCtrl.minValue.connect( setRange.minX )
    volCtrl.startValue.connect( setRange.minY )
    
    volCtrl.startAngle.connect( setRange.oldMaxX )
    volCtrl.maxAngle.connect( setRange.oldMaxY )

    volCtrl.minAngle.connect( setRange.oldMinX )
    volCtrl.startAngle.connect( setRange.oldMinY )
    
    volCtrl.currentAngle.connect( setRange.valueX )
    volCtrl.currentAngle.connect( setRange.valueY )
    
    # create condition with ranged values
    condi = pm.createNode( 'condition', n = prefix + '_cnd' )
    condi.operation.set(2) #greater than
    setRange.outValueX.connect( condi.colorIfFalseR )
    setRange.outValueY.connect( condi.colorIfTrueR )
    
    volCtrl.currentAngle.connect( condi.firstTerm )
    volCtrl.startAngle.connect( condi.secondTerm )
    
    # create multi double linear to multiply incoming ranged values with envelope from ctrl
    switchMdl = pm.createNode( 'multDoubleLinear', n = prefix + '_switch_mdl' )
    condi.outColorR.connect( switchMdl.input1 )
    volCtrl.envelope.connect( switchMdl.input2 )
    
    # create unit convresion to scale the values by 100
    unitConver = pm.createNode('unitConversion')
    unitConver.conversionFactor.set(100)
    switchMdl.output.connect( unitConver.input )
    
    # create unit convresion to scale the values by 100                              
    unitConver2 = pm.createNode('unitConversion')
    unitConver2.conversionFactor.set(100)
    volCtrl.defaultValue.connect( unitConver2.input)
    
    # create add double linear to sum switch output plus default value
    adl = pm.createNode( 'addDoubleLinear', n = prefix + '_adl' )
    unitConver2.output.connect( adl.input1 )                           
    unitConver.output.connect( adl.input2 )
    
    # create unit convresion to scale the values by 0.010                              
    unitConver = pm.createNode('unitConversion')
    unitConver.conversionFactor.set(0.010)
    adl.output.connect( unitConver.input )
    
    # flip mdl # THIS CHANGED DEPENDING IN WHICH CONTROL IS THIS MAKING CURRENT VALUE POS OR NEG BY DEFAULT
    flipMdl = pm.createNode( 'multDoubleLinear', n = prefix + '_flip_mdl' )
    flipMdl.input1.set( currentValFlip )
    unitConver.output.connect( flipMdl.input2 )
    
    flipMdl.output.connect( volCtrl.currentValue )
    volCtrl.currentValue.lock()
    
    # connect current value to endCtrlGrp # THIS TARGET ATTR SHOULD CHANGE DEPENDING IN WHICH CONTROL IS THIS
    
    # create unit conversion to scale the values by 100                             
    unitConver = pm.createNode('unitConversion')
    unitConver.conversionFactor.set(100)
    volCtrl.currentValue.connect( unitConver.input )
    
    pm.connectAttr(unitConver + '.output', endCtrlGrp + transDefaultAxis)
    #unitConver.output.connect( endCtrlGrp.translateZ)
    
def _createVolumeJoint( prefix, volCtrl, volBaseJnt ):
    
    '''
    creates a volume joint driven by the passed volCtrl
    '''
    
    volJnt = volBaseJnt.duplicate( po = True, n = prefix + '_jnt' )[0].setParent( volBaseJnt )
    pm.parentConstraint( volCtrl, volJnt )    

    
    
    
    
    