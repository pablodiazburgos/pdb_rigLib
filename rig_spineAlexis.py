"""
rig_spine.py

spine control setup
"""

import maya.cmds as cmds
import pymel.core as pm

from . import module
from . import controls


def build(
        spineCurve,
        spineJoints,
        spineTarget,
        spineVector,
        rootJnt,
        chestJnt,
        prefix = 'spine',
        ctrlScale = 1.0):


    # make module
    moduleObjs = module.make( prefix = prefix )

    # define spine shape
    spineCrvShape = cmds.listRelatives( spineCurve, s = True )[0]

    # make locators on spine

    cmds.select(spineCurve,r=True)
    sel=cmds.ls(sl=True)

    curveDegree= cmds.getAttr(sel[0] +'.degree')
    curveSpans= cmds.getAttr(sel[0] + '.spans')

    spineLocators = []

    for i in range(curveDegree+curveSpans):
        oval=cmds.getAttr(sel[0] + '.cv['+ str(i) + ']')

        oLocator= cmds.spaceLocator( n = 'spine_drv_01')

        cmds.setAttr(oLocator[0] + '.translateX', oval[0][0])
        cmds.setAttr(oLocator[0] + '.translateY', oval[0][1])
        cmds.setAttr(oLocator[0] + '.translateZ', oval[0][2])

        spineLocators.append( oLocator[0] )

    # create decomposeMatrix and connect with locators
    spineMatrix = []
    for i in range( len( spineLocators ) ):
        dcmNode = cmds.createNode('decomposeMatrix',n = '%s%s%02d' %( prefix,'_decomposeMatrix_', i + 1 ) )
        spineMatrix.append( dcmNode )

    for i in range(5):

        cmds.connectAttr(spineLocators[i]+'.worldMatrix[0]', spineMatrix[i]+'.inputMatrix', f=True)
        cmds.connectAttr(spineMatrix[i]+'.outputTranslate', spineCrvShape+'.controlPoints[%s]' % i, f=True)

    # make controls

    COGCtrl = controls.make( prefix = prefix + '_COG', ctrlScale = ctrlScale * 5, ctrlShape = 'square', matchObjectTr = spineLocators[0],matchObjectRt=spineLocators[0], parentObj = moduleObjs['controlsGrp'] )
    FKCtrl01 = controls.make( prefix = prefix + '_FK_01', ctrlScale = ctrlScale * 3, ctrlShape = 'square', matchObjectTr = spineLocators[1],matchObjectRt=spineLocators[1], parentObj = moduleObjs['controlsGrp'] )
    FKCtrl02 = controls.make( prefix = prefix + '_FK_02', ctrlScale = ctrlScale * 3, ctrlShape = 'square', matchObjectTr = spineLocators[2],matchObjectRt=spineLocators[2], parentObj = moduleObjs['controlsGrp'] )
    IKCtrl01 = controls.make( prefix = prefix + '_IK_01', ctrlScale = ctrlScale * 4.5, ctrlShape = 'circleY', matchObjectTr = spineLocators[0],matchObjectRt=spineLocators[0], parentObj = moduleObjs['controlsGrp'] )
    IKCtrl02 = controls.make( prefix = prefix + '_IK_02', ctrlScale = ctrlScale * 0.5, ctrlShape = 'circleZ', matchObjectTr = spineLocators[1],matchObjectRt=spineLocators[1], parentObj = moduleObjs['controlsGrp'] )
    IKCtrl03 = controls.make( prefix = prefix + '_IK_03', ctrlScale = ctrlScale * 0.5, ctrlShape = 'circleZ', matchObjectTr = spineLocators[2],matchObjectRt=spineLocators[2], parentObj = moduleObjs['controlsGrp'] )
    IKCtrl04 = controls.make( prefix = prefix + '_IK_04', ctrlScale = ctrlScale * 0.5, ctrlShape = 'circleZ', matchObjectTr = spineLocators[3],matchObjectRt=spineLocators[3], parentObj = moduleObjs['controlsGrp'] )
    chestCtrl = controls.make( prefix = prefix + '_Chest', ctrlScale = ctrlScale * 4.5, ctrlShape = 'circleY', matchObjectTr = spineLocators[4],matchObjectRt=spineLocators[4], parentObj =  moduleObjs['controlsGrp'] )

    '''
    # create ik controls list
    ikCtrls = []
    for i in range( len( spineLocators ) - 1 ):
        ikCtrl = controls.make( prefix = '%s%s%02d' %(prefix, '_IK_', i + 1), ctrlScale = ctrlScale * 4.5, ctrlShape = 'circleY', matchObjectTr = spineLocators[i],matchObjectRt=spineLocators[0], parentObj = moduleObjs['controlsGrp'] )
        ikCtrls.append( ikCtrl )
    '''
    # connect hiearchy spine controls

    cmds.parentConstraint( FKCtrl01['c'], FKCtrl02['inf'], mo = True )
    cmds.parentConstraint( COGCtrl['c'],  FKCtrl01['inf'], mo = True )
    cmds.parentConstraint( FKCtrl02['c'], chestCtrl['inf'], mo = True)
    cmds.parentConstraint( FKCtrl01['c'], IKCtrl03['inf'], mo = True )
    cmds.parentConstraint( COGCtrl['c'],  IKCtrl01['inf'], mo = True )
    cmds.parentConstraint( chestCtrl['c'],IKCtrl04['inf'], mo = True )
    cmds.parentConstraint( IKCtrl01['c'], IKCtrl02['inf'], mo = True )

    #fix position the controls iks spine controls
    moveZ=cmds.getAttr(IKCtrl02['off']+'.translateZ')
    res=moveZ+30
    resf=res-moveZ
    cmds.hilite(IKCtrl02['c'])
    cmds.select(IKCtrl02['c']+'.cv[0:7]',r=True)
    cmds.move(0,0,resf ,r=True)
    cmds.hilite(IKCtrl02['c'],u=True)
    cmds.select(cl=True)

    moveZ2=cmds.getAttr(IKCtrl03['off']+'.translateZ')
    res=moveZ-moveZ2
    resf=30+res
    cmds.hilite(IKCtrl03['c'])
    cmds.select(IKCtrl03['c']+'.cv[0:7]',r=True)
    cmds.move(0,0,resf ,r=True)
    cmds.hilite(IKCtrl03['c'],u=True)
    cmds.select(cl=True)

    moveZ3=cmds.getAttr(IKCtrl04['off']+'.translateZ')
    res=moveZ-moveZ3
    resf=30+res
    cmds.hilite(IKCtrl04['c'])
    cmds.select(IKCtrl04['c']+'.cv[0:7]',r=True)
    cmds.move(0,5,resf ,r=True)
    cmds.hilite(IKCtrl04['c'],u=True)
    cmds.select(cl=True)

    # connect controls with spine locators
    connectList = [IKCtrl01, IKCtrl02, IKCtrl03, IKCtrl04, chestCtrl]
    for ctrl, locator in zip( connectList, spineLocators ):
        cmds.parentConstraint( ctrl['c'], locator, mo = True )

    #create AIM Constraint

    cmds.select(spineTarget[1],r=True)
    cmds.select(spineTarget[0],tgl=True)
    cmds.aimConstraint(worldUpObject=spineVector[0])

    cmds.select(spineTarget[2],r=True)
    cmds.select(spineTarget[1],tgl=True)
    cmds.aimConstraint(worldUpObject=spineVector[1])

    cmds.select(spineTarget[3],r=True)
    cmds.select(spineTarget[2],tgl=True)
    cmds.aimConstraint(worldUpObject=spineVector[2])

    cmds.select(spineTarget[4],r=True)
    cmds.select(spineTarget[3],tgl=True)
    cmds.aimConstraint(worldUpObject=spineVector[3])

    cmds.select(spineTarget[5],r=True)
    cmds.select(spineTarget[4],tgl=True)
    cmds.aimConstraint(worldUpObject=spineVector[4])

    cmds.select(spineTarget[6],r=True)
    cmds.select(spineTarget[5],tgl=True)
    cmds.aimConstraint(worldUpObject=spineVector[5])

    spineTgtAim = []
    for i in range( len(spineTarget) - 1 ):
        consNode = spineTarget[i]+'_aimConstraint1'
        spineTgtAim.append( consNode )

    for obj in spineTgtAim:
        cmds.setAttr(obj+'.worldUpType', 1)
        cmds.setAttr(obj+'.upVectorY', 1)

    #create point Constraint of locators
    cmds.pointConstraint( spineVector[6], spineVector[0], spineVector[3] ,mo=True)
    cmds.setAttr(spineVector[3]+'_pointConstraint1.offsetY', 0)

    cmds.pointConstraint( spineVector[6], spineVector[3], spineVector[5] ,mo=True)
    cmds.setAttr(spineVector[5]+'_pointConstraint1.'+spineVector[6]+'W0', 0.66)
    cmds.setAttr(spineVector[5]+'_pointConstraint1.'+spineVector[3] +'W1', 0.33)
    cmds.setAttr(spineVector[5]+'_pointConstraint1.offsetY', 0)

    cmds.pointConstraint( spineVector[6], spineVector[3], spineVector[4] ,mo=True)
    cmds.setAttr(spineVector[4]+'_pointConstraint1.'+spineVector[6]+'W0', 0.33)
    cmds.setAttr(spineVector[4]+'_pointConstraint1.'+spineVector[3] +'W1', 0.66)
    cmds.setAttr(spineVector[4]+'_pointConstraint1.offsetY', 0)

    cmds.pointConstraint( spineVector[3], spineVector[0], spineVector[2] ,mo=True)
    cmds.setAttr(spineVector[2]+'_pointConstraint1.'+spineVector[3]+'W0', 0.66)
    cmds.setAttr(spineVector[2]+'_pointConstraint1.'+spineVector[0] +'W1', 0.33)
    cmds.setAttr(spineVector[2]+'_pointConstraint1.offsetY', 0)

    cmds.pointConstraint( spineVector[3], spineVector[0], spineVector[1] ,mo=True)
    cmds.setAttr(spineVector[1]+'_pointConstraint1.'+spineVector[3]+'W0', 0.33)
    cmds.setAttr(spineVector[1]+'_pointConstraint1.'+spineVector[0] +'W1', 0.66)
    cmds.setAttr(spineVector[1]+'_pointConstraint1.offsetY', 0)


    cmds.parent( spineVector, moduleObjs['NoXFormGrp'] )
    cmds.parent( spineTarget, moduleObjs['NoXFormGrp'] )
    cmds.parent( spineLocators, moduleObjs['NoXFormGrp'] )
    cmds.parent(spineVector[6],chestCtrl['c'])
    cmds.parent(spineVector[0],IKCtrl01['c'])
    cmds.setAttr(spineVector[6]+'.visibility' ,0)
    cmds.setAttr(spineVector[0]+'.visibility' ,0)
    cmds.parent( spineCurve, moduleObjs['NoXFormGrp'] )

    #conservation of volume

    cmds.createNode('curveInfo',n=spineCrvShape+'_curveInfo')
    cmds.connectAttr(spineCrvShape+'.worldSpace[0]',spineCrvShape+'_curveInfo'+'.inputCurve',f=True)
    cmds.createNode('multiplyDivide',n=spineCrvShape+'_multiplyDivide')
    cmds.connectAttr(spineCrvShape+'_curveInfo'+'.arcLength',spineCrvShape+'_multiplyDivide'+'.input2X',f=True)
    inpuntX=cmds.getAttr(spineCrvShape+'_multiplyDivide'+'.input2X')
    cmds.setAttr(spineCrvShape+'_multiplyDivide'+'.input1X',inpuntX)
    cmds.setAttr(spineCrvShape+'_multiplyDivide'+'.operation',2)


    spinePmaNode = cmds.createNode('plusMinusAverage',n=spineCrvShape+'plusMinusAverage')
    cmds.setAttr(spineCrvShape+'plusMinusAverage'+'.input2D[0].input2Dx',1)
    cmds.connectAttr(spineCrvShape+'_multiplyDivide'+'.outputX', spineCrvShape+'plusMinusAverage'+'.input2D[1].input2Dx')
    cmds.setAttr(spineCrvShape+'plusMinusAverage'+'.operation',2)


    animeSpineGrp = cmds.group(em=True,n='anim_spine')
    cmds.setKeyframe('anim_spine.translateX',v=0,time=[0])
    cmds.setKeyframe('anim_spine.translateX',v=-2,time=[10])
    cmds.setKeyframe('anim_spine.translateX',v=0,time=[20])


    for i, jnt in enumerate(spineJoints):
        frameCacheNode = cmds.createNode('frameCache',n= '%s%s%02d' % ( spineCrvShape, '_frameCache_', i + 1) )
        cmds.connectAttr( animeSpineGrp +'.translateX', frameCacheNode +'.stream', f=True)
        mdvNode = cmds.createNode('multiplyDivide',n=spineCrvShape+'_multiplyDivide_01')
        cmds.connectAttr(spinePmaNode +'.output2Dx', mdvNode +'.input1X',f=True)
        cmds.connectAttr( frameCacheNode+'.varying', mdvNode +'.input2X',f=True)

        spineJntPma = cmds.createNode('plusMinusAverage',n=spineCrvShape+'plusMinusAverage_01')
        cmds.setAttr( spineJntPma + '.input2D[0].input2Dx',1 )
        cmds.connectAttr(mdvNode +'.outputX', spineJntPma +'.input2D[1].input2Dx')

        cmds.connectAttr(spineJntPma +'.output2Dx',spineJoints[i]+'.scaleY',f=True)
        cmds.connectAttr(spineJntPma +'.output2Dx',spineJoints[i]+'.scaleZ',f=True)

        if i == 4:
            cmds.disconnectAttr(spineJntPma+'.output2Dx',spineJoints[i]+'.scaleY')
            cmds.disconnectAttr(spineJntPma+'.output2Dx',spineJoints[i]+'.scaleZ')
            cmds.parent( animeSpineGrp, moduleObjs['NoXFormGrp'] )

    return {
            'moduleObjs':moduleObjs,
            #'bodyCtrl':bodyCtrl
            }