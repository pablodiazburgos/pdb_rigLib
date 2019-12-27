"""
advancedSkeleton @ utils
"""
import maya.cmds as mc
import maya.mel as mm

def fixCtrlColors():

    """
    Module to fix advanced skeleton auto rig controls colors to match the standard colors
    :return: None
    """
    #List all the controls in the scene to change color

    controlsShapes = mc.ls( type = 'nurbsCurve', s = True )

    [ mc.setAttr( s + '.ove', 1 ) for s in controlsShapes ]

    l_mainControls = []
    r_mainControls = []
    l_secondaryControls = []
    r_secondaryControls = []
    switchControls = []
    m_fkControls = []
    m_ikControls = []

    for s in controlsShapes:

        if s.endswith( 'LShape' ):
            l_mainControls.append( s )

        elif s.endswith( 'RShape' ):
            r_mainControls.append( s )

        elif s.startswith( 'FK' ) and s.endswith( 'MShape' ):
            m_fkControls.append( s )

        elif s.startswith( 'IK' ) and s.endswith( 'MShape' ):
            m_ikControls.append( s )

    for shape in l_mainControls:
        if 'Finger' in shape:
            l_secondaryControls.append( shape )

    for shape in r_mainControls:
        if 'Finger' in shape:
            r_secondaryControls.append( shape )

    for shape in controlsShapes:
        if shape.startswith( 'FKIK' ):
            switchControls.append( shape )

    # set colors
    [ mc.setAttr( s + '.ovc', 6) for s in l_mainControls ]
    [ mc.setAttr( s + '.ovc', 13) for s in r_mainControls ]

    [ mc.setAttr( s + '.ovc', 18) for s in l_secondaryControls ]
    [ mc.setAttr( s + '.ovc', 21) for s in r_secondaryControls ]

    [ mc.setAttr( s + '.ovc', 17) for s in m_fkControls ]
    [ mc.setAttr( s + '.ovc', 14) for s in m_ikControls ]

    [ mc.setAttr( s + '.ovc', 22) for s in switchControls ]

    print 'color changed!'

def mirrorCvPositions( cvs, mode = 'x' ):
    """

    :param cvs: list of vertex usually take it from mc.ls(sl = 1, fl = 1)
    :param mode: mirror axis , 'x' by default
    :return: none
    """

    for cv in cvs:

        strName = str( cv ).split( '|' )[-1]
        cvShortLeft = str( cv ).split( '.' )[-2]
        cvNumber = str( cv ).split( '.' )[-1]
        prefixName = cvShortLeft.split('_')[-2]
        cvShortRight = ''

        if cvShortLeft.endswith( '_LShape' ): cvShortRight = prefixName +  '_RShape' +  '.'  + cvNumber
        elif cvShortLeft.endswith( '_RShape' ): cvShortRight = prefixName +  '_LShape' +  '.'  + cvNumber


        else:

            mm.eval( 'warning("advancedSkeleton.mirrorCvPositions: cannot find mirror for ' + strName + ', doesn`t endswith with _L or _R")' )
            continue

        pos = mc.xform( strName, q = 1, ws = 1, t = 1 )


        if mode == 'x': mc.xform( cvShortRight, ws = 1, t = [ pos[0] * ( -1 ), pos[1], pos[2] ] )
        if mode == 'z': mc.xform( cvShortRight, ws = 1, t = [ pos[0], pos[1], pos[2] * ( -1 ) ] )


