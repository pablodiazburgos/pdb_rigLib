import maya.cmds as mc
from maya import OpenMaya as om


def mouthInicialPosition():
    
    # create a curve from edge selection to move the mouth surface
    guideCrv = mc.polyToCurve(n = 'tempMouth_crv')[0]
    mc.delete(guideCrv, ch = True)
    guideCrvShape = mc.listRelatives( guideCrv, s = True )[0]

    # define a list of 2 index which are left and right, top, bottom index of vertex ex: mouth_srf.cv[0:3][4]
    Acv = [ 3, 5 ]
    Bcv = [ 2, 6 ]
    Ccv = [ 1, 7 ]
    Dcv = [ 0, 8 ]
    Ecv = [ 11, 9 ]
    SECvs = [4, 10]
    surfaceName = 'mouth_srf'
    
    allCvs = [Acv, Bcv, Ccv, Dcv, Ecv, SECvs]
    
    # create a cluster per span of the surface and keep it in a list in the same order
    clsList = []
    for cvs in allCvs:
        
        tempClsList = []
        cvsA = cvs[0]
        cvsB = cvs[1]
        
        cls1 = mc.cluster( '{}.cv[0:3][{}]'.format(surfaceName, cvsA), n = 'cls{}'.format(cvsA) )[1]
        cls2 = mc.cluster( '{}.cv[0:3][{}]'.format(surfaceName, cvsB), n = 'cls{}'.format(cvsB) )[1]
        
        tempClsList.append(cls1)
        tempClsList.append(cls2)
        
        clsList.append(tempClsList)
   
    crvFn = om.MFnNurbsCurve(getDagPath( guideCrvShape ) )
    numJoints = 7
    
    for i in range(numJoints):
        parameter = crvFn.findParamFromLength(crvFn.length() * ( 1.0 / (numJoints - 1) ) * i)
        point = om.MPoint()
        crvFn.getPointAtParam(parameter, point)
       
        if i == 0 :
            jnt = mc.createNode("joint")
            mc.xform(jnt,t=[point.x,point.y,point.z])
            mc.delete( mc.parentConstraint( jnt, clsList[-1][0] ) )
            mc.delete(jnt)
            
        elif i == 6:
            jnt = mc.createNode("joint")
            mc.xform(jnt,t=[point.x,point.y,point.z])
            mc.delete( mc.parentConstraint( jnt, clsList[-1][1] ) )
            mc.delete(jnt)
            
        else:
            jnt = mc.createNode("joint")
            mc.xform(jnt,t=[point.x,point.y,point.z])
            
            jnt2 = mc.createNode("joint")
            mc.xform(jnt2,t=[point.x * -1,point.y,point.z])

            mc.delete( mc.parentConstraint( jnt, clsList[i - 1][0] ) )
            mc.delete( mc.parentConstraint( jnt2, clsList[i - 1][1] ) )
            
            mc.delete(jnt, jnt2)
        
    mc.delete(surfaceName, ch = True)    
    mc.delete(guideCrv)
        
def getDagPath(node=None):
    sel = om.MSelectionList()
    sel.add(node)
    d = om.MDagPath()
    sel.getDagPath(0, d)
    return d