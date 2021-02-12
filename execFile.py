import maya.cmds as mc
import pymel.core as pm

# imports
import pdb_rigLib.base.control as control
import pdb_rigLib.base.module as module

import pdb_rigLib.utils.transform as transform

# create module
rigModule = module.Module('lips')

# create extra needed grps
jnts_nt_grp = pm.group(em=True, n='lipsJointsNt_grp', p=rigModule.Main)
jnts_nt_grp.inheritsTransform.set(False)

# create local lip joint to hold weights
local_jnt = pm.createNode('joint', n='localLips1_jnt')
local_jnt.setParent(jnts_nt_grp)

# get cv order for joint creation
lCvNums = [i for i in range(51, 60, 1)]
lCvNums.extend([i for i in range(0, 20, 1)])

rCvNums = [i for i in range(21, 50, 1)]
rCvNums.reverse()

mCvNums = [20, 50]

fullCvList = [lCvNums, rCvNums, mCvNums]
sidesList = ['l_', 'r_', '']
# curves
hiCrv = pm.PyNode('fullLips_crv')
ctrlsCrv = pm.PyNode('controlsLips_crv')

lipsCrvsGrp = pm.PyNode('lipsCurves_grp')
lipsCrvsGrp.setParent(rigModule.PartsNt)

# create joints per Cv on full curve
for CvList, side in zip(fullCvList, sidesList):
    for i, cvId in enumerate(CvList):
        i += 1
        # create joint per Cv
        cv = pm.PyNode('{}.cv[{}]'.format(hiCrv, cvId))
        jnt = pm.createNode('joint', n='{}lips{}'.format(side, i))
        jnt.radius.set(0.5)
        jnt.setParent(jnts_nt_grp)

        # get param at point to use the pointOnCurveInfo node
        pciNode = pm.createNode('pointOnCurveInfo', n='{}lips{}_pci'.format(side, i))
        paramAtPointVal = hiCrv.getShapes()[0].getParamAtPoint(cv.getPosition())

        # make pci connections
        hiCrv.getShapes()[0].worldSpace[0].connect(pciNode.inputCurve)
        pciNode.parameter.set(paramAtPointVal)
        pciNode.position.connect(jnt.translate)

# CONTROLS AND CONTROL CURVE SETUP
lCtrlsCvs = [i for i in range(0, 5, 1)]

rCtrlsCvs = [i for i in range(6, 11, 1)]
rCtrlsCvs.reverse()

mCtrlsCvs = [11, 5]

fullCtrlsCvList = [lCtrlsCvs, rCtrlsCvs, mCtrlsCvs]

local_locs_grp = pm.group(em=True, p=rigModule.PartsNt, n='lips_localLocs_grp')
local_locs_grp.visibility.set(False)
localClean_locs_grp = pm.group(em=True, p=rigModule.PartsNt, n='lips_localLocsClean_grp')

# create controls
for CvList, side in zip(fullCtrlsCvList, sidesList):
    for i, cvId in enumerate(CvList):
        i += 1
        cv = pm.PyNode('{}.cv[{}]'.format(ctrlsCrv, cvId))

        # create loc for control position
        local_loc = pm.spaceLocator(n='{}lipsLocal{}_loc'.format(side, cvId))
        local_loc.setParent(local_locs_grp)
        cvPos = cv.getPosition()
        pm.xform(local_loc, t=cvPos, ws=True)

        lip_ctrl = control.Control(prefix='{}lips{}'.format(side, cvId), colorName='primary',
                                   defLockHide=['r', 's', 'v'], moveTo=local_loc.name(),
                                   shape='cube', scale=2, ctrlParent=rigModule.Controls)

        # connect local locator translate to curve control points
        local_loc.translate.connect(ctrlsCrv.getShapes()[0].attr('controlPoints[{}]'.format(cvId)))

        # create clean locators to drive local locs and will be also direct connected by controls
        clean_loc = local_loc.duplicate(n='{}lipsLocalClean{}_loc'.format(side, cvId))[0]
        clean_loc.setParent(localClean_locs_grp)
        clean_loc_offset_grp = transform.makeOffsetGrp(clean_loc.name())

        # drive locators
        pm.parentConstraint(clean_loc, local_loc, mo=True)
        pm.PyNode(lip_ctrl.C).translate.connect(clean_loc.translate)

# make wire
wire = pm.wire(hiCrv, w=ctrlsCrv, n='lips_wre')[0]

# print(fullVtxList)
