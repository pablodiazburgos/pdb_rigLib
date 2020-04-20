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

bodyBindJointsSelection = [
                        u'l_elbow1TwistPart1_jnt',
                        u'l_elbow1TwistPart2_jnt',
                        u'l_elbow1TwistPart3_jnt',
                        u'l_elbow1TwistPart4_jnt',
                        u'l_elbow1TwistPart5_jnt',
                        u'l_hip1TwistPart1_jnt',
                        u'l_hip1TwistPart2_jnt',
                        u'l_hip1TwistPart3_jnt',
                        u'l_hip1TwistPart4_jnt',
                        u'l_hip1TwistPart5_jnt',
                        u'l_knee1TwistPart1_jnt',
                        u'l_knee1TwistPart2_jnt',
                        u'l_knee1TwistPart3_jnt',
                        u'l_knee1TwistPart4_jnt',
                        u'l_knee1TwistPart5_jnt',
                        u'l_shoulder1TwistPart1_jnt',
                        u'l_shoulder1TwistPart2_jnt',
                        u'l_shoulder1TwistPart3_jnt',
                        u'l_shoulder1TwistPart4_jnt',
                        u'l_shoulder1TwistPart5_jnt',
                        u'r_elbow1TwistPart1_jnt',
                        u'r_elbow1TwistPart2_jnt',
                        u'r_elbow1TwistPart3_jnt',
                        u'r_elbow1TwistPart4_jnt',
                        u'r_elbow1TwistPart5_jnt',
                        u'r_hip1TwistPart1_jnt',
                        u'r_hip1TwistPart2_jnt',
                        u'r_hip1TwistPart3_jnt',
                        u'r_hip1TwistPart4_jnt',
                        u'r_hip1TwistPart5_jnt',
                        u'r_knee1TwistPart1_jnt',
                        u'r_knee1TwistPart2_jnt',
                        u'r_knee1TwistPart3_jnt',
                        u'r_knee1TwistPart4_jnt',
                        u'r_knee1TwistPart5_jnt',
                        u'r_shoulder1TwistPart1_jnt',
                        u'r_shoulder1TwistPart2_jnt',
                        u'r_shoulder1TwistPart3_jnt',
                        u'r_shoulder1TwistPart4_jnt',
                        u'r_shoulder1TwistPart5_jnt',
                        u'l_toes1_jnt',
                        u'l_foot1_jnt',
                        u'r_toes1_jnt',
                        u'r_foot1_jnt',
                        u'pelvis1_jnt',
                        u'head1_jnt',
                        u'jaw1_jnt',
                        u'neck3_jnt',
                        u'neck2_jnt',
                        u'neck1_jnt',
                        u'l_thumbFing3_jnt',
                        u'l_thumbFing2_jnt',
                        u'l_thumbFing1_jnt',
                        u'l_indexFing3_jnt',
                        u'l_indexFing2_jnt',
                        u'l_indexFing1_jnt',
                        u'l_indexFingBase1_jnt',
                        u'l_middleFing3_jnt',
                        u'l_middleFing2_jnt',
                        u'l_middleFing1_jnt',
                        u'l_ringFing3_jnt',
                        u'l_ringFing2_jnt',
                        u'l_ringFing1_jnt',
                        u'l_pinkyFing3_jnt',
                        u'l_pinkyFing2_jnt',
                        u'l_pinkyFing1_jnt',
                        u'l_middleFingBase1_jnt',
                        u'l_ringFingBase1_jnt',
                        u'l_pinkyFingBase1_jnt',
                        u'l_hand1_jnt',
                        u'r_thumbFing3_jnt',
                        u'r_thumbFing2_jnt',
                        u'r_thumbFing1_jnt',
                        u'r_indexFing3_jnt',
                        u'r_indexFing2_jnt',
                        u'r_indexFing1_jnt',
                        u'r_middleFing3_jnt',
                        u'r_middleFing2_jnt',
                        u'r_middleFing1_jnt',
                        u'r_ringFing3_jnt',
                        u'r_ringFing2_jnt',
                        u'r_ringFing1_jnt',
                        u'r_pinkyFing3_jnt',
                        u'r_pinkyFing2_jnt',
                        u'r_pinkyFing1_jnt',
                        u'r_pinkyFingBase1_jnt',
                        u'r_ringFingBase1_jnt',
                        u'r_indexFingBase1_jnt',
                        u'r_middleFingBase1_jnt',
                        u'r_hand1_jnt',
                        u'l_clavicle1_jnt',
                        u'r_clavicle1_jnt',
                        u'spine5_jnt',
                        u'spine4_jnt',
                        u'spine3_jnt',
                        u'spine2_jnt',
                        u'spine1_jnt'
 ]