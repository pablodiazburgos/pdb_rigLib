"""
rig_spine.py

spine control setup
"""

import maya.cmds as mc

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
        ctrlScale = 1.0
        ):
  

    # make module
    moduleObjs = module.make( prefix = prefix )

    # define spine shape
    spineCrvShape = mc.listRelatives( spineCurve, s = True )[0]

    # make locators on spine

    mc.select(spineCurve,r=True)
    sel=mc.ls(sl=True)

    curveDegree= mc.getAttr(sel[0] +'.degree')
    curveSpans= mc.getAttr(sel[0] + '.spans')
    
    spineLocators = []
    
    for i in range(curveDegree+curveSpans):
        oval=mc.getAttr(sel[0] + '.cv['+ str(i) + ']')
        
        oLocator= mc.spaceLocator( n = 'spine_drv_01')

        mc.setAttr(oLocator[0] + '.translateX', oval[0][0])
        mc.setAttr(oLocator[0] + '.translateY', oval[0][1])
        mc.setAttr(oLocator[0] + '.translateZ', oval[0][2])
        
        spineLocators.append( oLocator[0] )

    # create decomposeMatrix and connect with locators
    spineMatrix = []
    for i in range( len( spineLocators ) ):
        dcmNode = mc.createNode('decomposeMatrix',n = '%s%s%02d' %( prefix,'_decomposeMatrix_', i + 1 ) )
        spineMatrix.append( dcmNode )

    for i in range(5):
  
        mc.connectAttr(spineLocators[i]+'.worldMatrix[0]', spineMatrix[i]+'.inputMatrix', f=True) 
        mc.connectAttr(spineMatrix[i]+'.outputTranslate', spineCrvShape+'.controlPoints[%s]' % i, f=True)

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

    mc.parentConstraint( FKCtrl01['c'], FKCtrl02['inf'], mo = True )
    mc.parentConstraint( COGCtrl['c'],  FKCtrl01['inf'], mo = True )
    mc.parentConstraint( FKCtrl02['c'], chestCtrl['inf'], mo = True)
    mc.parentConstraint( FKCtrl01['c'], IKCtrl03['inf'], mo = True )
    mc.parentConstraint( COGCtrl['c'],  IKCtrl01['inf'], mo = True )
    mc.parentConstraint( chestCtrl['c'],IKCtrl04['inf'], mo = True )
    mc.parentConstraint( IKCtrl01['c'], IKCtrl02['inf'], mo = True )

    #fix position the controls iks spine controls
    moveZ=mc.getAttr(IKCtrl02['off']+'.translateZ')
    res=moveZ+30
    resf=res-moveZ
    mc.hilite(IKCtrl02['c'])
    mc.select(IKCtrl02['c']+'.cv[0:7]',r=True)
    mc.move(0,0,resf ,r=True)
    mc.hilite(IKCtrl02['c'],u=True)
    mc.select(cl=True)

    moveZ2=mc.getAttr(IKCtrl03['off']+'.translateZ')
    res=moveZ-moveZ2
    resf=30+res
    mc.hilite(IKCtrl03['c'])
    mc.select(IKCtrl03['c']+'.cv[0:7]',r=True)
    mc.move(0,0,resf ,r=True)
    mc.hilite(IKCtrl03['c'],u=True)
    mc.select(cl=True)
    
    moveZ3=mc.getAttr(IKCtrl04['off']+'.translateZ')
    res=moveZ-moveZ3
    resf=30+res
    mc.hilite(IKCtrl04['c'])
    mc.select(IKCtrl04['c']+'.cv[0:7]',r=True)
    mc.move(0,5,resf ,r=True)
    mc.hilite(IKCtrl04['c'],u=True)
    mc.select(cl=True)
    
    # connect controls with spine locators
    connectList = [IKCtrl01, IKCtrl02, IKCtrl03, IKCtrl04, chestCtrl]
    for ctrl, locator in zip( connectList, spineLocators ):
        mc.parentConstraint( ctrl['c'], locator, mo = True )

    #create AIM Constraint

    mc.select(spineTarget[1],r=True)
    mc.select(spineTarget[0],tgl=True)
    mc.aimConstraint(worldUpObject=spineVector[0])

    mc.select(spineTarget[2],r=True)
    mc.select(spineTarget[1],tgl=True)
    mc.aimConstraint(worldUpObject=spineVector[1])

    mc.select(spineTarget[3],r=True)
    mc.select(spineTarget[2],tgl=True)
    mc.aimConstraint(worldUpObject=spineVector[2])

    mc.select(spineTarget[4],r=True)
    mc.select(spineTarget[3],tgl=True)
    mc.aimConstraint(worldUpObject=spineVector[3])

    mc.select(spineTarget[5],r=True)
    mc.select(spineTarget[4],tgl=True)
    mc.aimConstraint(worldUpObject=spineVector[4])

    mc.select(spineTarget[6],r=True)
    mc.select(spineTarget[5],tgl=True)
    mc.aimConstraint(worldUpObject=spineVector[5])

    spineTgtAim = []
    for i in range( len(spineTarget) - 1 ):
        consNode = spineTarget[i]+'_aimConstraint1'
        spineTgtAim.append( consNode )
        
    for obj in spineTgtAim:
        mc.setAttr(obj+'.worldUpType', 1)
        mc.setAttr(obj+'.upVectorY', 1)

    #create point Constraint of locators
    mc.pointConstraint( spineVector[6], spineVector[0], spineVector[3] ,mo=True)  
    mc.setAttr(spineVector[3]+'_pointConstraint1.offsetY', 0)

    mc.pointConstraint( spineVector[6], spineVector[3], spineVector[5] ,mo=True)
    mc.setAttr(spineVector[5]+'_pointConstraint1.'+spineVector[6]+'W0', 0.66)
    mc.setAttr(spineVector[5]+'_pointConstraint1.'+spineVector[3] +'W1', 0.33)    
    mc.setAttr(spineVector[5]+'_pointConstraint1.offsetY', 0)

    mc.pointConstraint( spineVector[6], spineVector[3], spineVector[4] ,mo=True)
    mc.setAttr(spineVector[4]+'_pointConstraint1.'+spineVector[6]+'W0', 0.33)
    mc.setAttr(spineVector[4]+'_pointConstraint1.'+spineVector[3] +'W1', 0.66)    
    mc.setAttr(spineVector[4]+'_pointConstraint1.offsetY', 0)

    mc.pointConstraint( spineVector[3], spineVector[0], spineVector[2] ,mo=True)
    mc.setAttr(spineVector[2]+'_pointConstraint1.'+spineVector[3]+'W0', 0.66)
    mc.setAttr(spineVector[2]+'_pointConstraint1.'+spineVector[0] +'W1', 0.33)    
    mc.setAttr(spineVector[2]+'_pointConstraint1.offsetY', 0)

    mc.pointConstraint( spineVector[3], spineVector[0], spineVector[1] ,mo=True)
    mc.setAttr(spineVector[1]+'_pointConstraint1.'+spineVector[3]+'W0', 0.33)
    mc.setAttr(spineVector[1]+'_pointConstraint1.'+spineVector[0] +'W1', 0.66)    
    mc.setAttr(spineVector[1]+'_pointConstraint1.offsetY', 0)
    

    mc.parent( spineVector, moduleObjs['NoXFormGrp'] )
    mc.parent( spineTarget, moduleObjs['NoXFormGrp'] )
    mc.parent( spineLocators, moduleObjs['NoXFormGrp'] )
    mc.parent(spineVector[6],chestCtrl['c'])
    mc.parent(spineVector[0],IKCtrl01['c'])
    mc.setAttr(spineVector[6]+'.visibility' ,0)
    mc.setAttr(spineVector[0]+'.visibility' ,0)
    mc.parent( spineCurve, moduleObjs['NoXFormGrp'] )

    #conservation of volume

    mc.createNode('curveInfo',n=spineCrvShape+'_curveInfo')
    mc.connectAttr(spineCrvShape+'.worldSpace[0]',spineCrvShape+'_curveInfo'+'.inputCurve',f=True)
    mc.createNode('multiplyDivide',n=spineCrvShape+'_multiplyDivide')
    mc.connectAttr(spineCrvShape+'_curveInfo'+'.arcLength',spineCrvShape+'_multiplyDivide'+'.input2X',f=True)
    inpuntX=mc.getAttr(spineCrvShape+'_multiplyDivide'+'.input2X')
    mc.setAttr(spineCrvShape+'_multiplyDivide'+'.input1X',inpuntX)
    mc.setAttr(spineCrvShape+'_multiplyDivide'+'.operation',2)


    spinePmaNode = mc.createNode('plusMinusAverage',n=spineCrvShape+'plusMinusAverage')
    mc.setAttr(spineCrvShape+'plusMinusAverage'+'.input2D[0].input2Dx',1)
    mc.connectAttr(spineCrvShape+'_multiplyDivide'+'.outputX', spineCrvShape+'plusMinusAverage'+'.input2D[1].input2Dx')
    mc.setAttr(spineCrvShape+'plusMinusAverage'+'.operation',2)

    
    animeSpineGrp = mc.group(em=True,n='anim_spine')
    mc.setKeyframe('anim_spine.translateX',v=0,time=[0])
    mc.setKeyframe('anim_spine.translateX',v=-2,time=[10])
    mc.setKeyframe('anim_spine.translateX',v=0,time=[20])


    for i, jnt in enumerate(spineJoints):
        frameCacheNode = mc.createNode('frameCache',n= '%s%s%02d' % ( spineCrvShape, '_frameCache_', i + 1) )
        mc.connectAttr( animeSpineGrp +'.translateX', frameCacheNode +'.stream', f=True)
        mdvNode = mc.createNode('multiplyDivide',n=spineCrvShape+'_multiplyDivide_01')
        mc.connectAttr(spinePmaNode +'.output2Dx', mdvNode +'.input1X',f=True)
        mc.connectAttr( frameCacheNode+'.varying', mdvNode +'.input2X',f=True)
        
        spineJntPma = mc.createNode('plusMinusAverage',n=spineCrvShape+'plusMinusAverage_01')
        mc.setAttr( spineJntPma + '.input2D[0].input2Dx',1 )
        mc.connectAttr(mdvNode +'.outputX', spineJntPma +'.input2D[1].input2Dx')
        
        mc.connectAttr(spineJntPma +'.output2Dx',spineJoints[i]+'.scaleY',f=True)
        mc.connectAttr(spineJntPma +'.output2Dx',spineJoints[i]+'.scaleZ',f=True)
        
        if i == 4:
            mc.disconnectAttr(spineJntPma+'.output2Dx',spineJoints[i]+'.scaleY')   
            mc.disconnectAttr(spineJntPma+'.output2Dx',spineJoints[i]+'.scaleZ')
            mc.parent( animeSpineGrp, moduleObjs['NoXFormGrp'] )
        
    return {
            'moduleObjs':moduleObjs,
            #'bodyCtrl':bodyCtrl
            }
    