    #===========================================================================
    # VOLUME JOINTS SETUP
    #===========================================================================
    rigmodule = module.Module( 'volumeJoints' )
    rigmodule.connect( baseRigData = baseRigData )
    rigmodule.parent( baseRigData = baseRigData )   
    
    #=======================================================================
    # SPINE JOINTS
    #=======================================================================

    spineUpOffsetValSeq = [0, 0, 2.5, 5.0, 10.0]
    for i in range(len( spineJoints ) - 1 ):
        baseJnt = spineJoints[i - 1]
        if i == 0:
            baseJnt = pelvisJnt
        
        rotJnt = spineJoints[i]
        
        volCtrlN, volCtrlS, volCtrlE, volCtrlW = volumeJoints.createFromJoint( 
                                                 baseJnt = pm.PyNode( baseJnt ),
                                                 rotJnt = pm.PyNode( rotJnt ),
                                                 prefix = 'spine{}'.format( i + 1 ),
                                                 setupParent = rigmodule.Parts,
                                                 jointsParent = rigmodule.Joints,
                                                 controlsParent = rigmodule.Controls,
                                                 rSide = False
                                                 )
        # control N 
        volCtrlN.minValue.set( 2 )
        volCtrlN.maxValue.set( -0.6 )
        volCtrlN.upOffset.set( -spineUpOffsetValSeq[i] )
        
        # control S 
        volCtrlS.minValue.set( -0.6 )
        volCtrlS.upOffset.set( spineUpOffsetValSeq[i] )
        
        # control E 
        volCtrlE.readFromAxis.set( 1 ) # up
        volCtrlE.minValue.set( 2 )
        volCtrlE.maxValue.set( -0.6 )
        volCtrlE.rotOffset.set( -spineUpOffsetValSeq[i] )
        
        # control W 
        volCtrlW.readFromAxis.set( 1 ) # up
        volCtrlW.minValue.set( -0.6 )

    #=======================================================================
    # NECK
    #=======================================================================
    
    # NECK1_JNT
    volCtrlN, volCtrlS, volCtrlE, volCtrlW = volumeJoints.createFromJoint( 
                                             baseJnt = pm.PyNode( spineJoints[-2] ),
                                             rotJnt = pm.PyNode( neckJoints[0] ),
                                             prefix = 'neck1',
                                             setupParent = rigmodule.Parts,
                                             jointsParent = rigmodule.Joints,
                                             controlsParent = rigmodule.Controls,
                                             rSide = False
                                             )
    # control N 
    volCtrlN.upOffset.set( 20 )
    volCtrlN.minValue.set( 2 )
    volCtrlN.maxValue.set( -0.4 )
   
    
    # control S 
    volCtrlS.upOffset.set( -20 )
    volCtrlS.minValue.set( -0.4 )
    
    
    # control E 
    volCtrlE.readFromAxis.set( 1 ) # up
    volCtrlE.rotOffset.set(-7.5)
    volCtrlE.minValue.set( 2 )
    volCtrlE.maxValue.set( -0.6 )
    
    # control W 
    volCtrlW.readFromAxis.set( 1 ) # up
    volCtrlW.rotOffset.set(-20)
    volCtrlW.minValue.set( 0 )

    #=================================================================================
    # NECK2_JNT
    volCtrlN, volCtrlS, volCtrlE, volCtrlW = volumeJoints.createFromJoint( 
                                             baseJnt = pm.PyNode( neckJoints[0] ),
                                             rotJnt = pm.PyNode( neckJoints[1] ),
                                             prefix = 'neck2',
                                             setupParent = rigmodule.Parts,
                                             jointsParent = rigmodule.Joints,
                                             controlsParent = rigmodule.Controls,
                                             rSide = False
                                             )
    # control N 
    volCtrlN.upOffset.set( 10 )
    volCtrlN.minValue.set( 2 )
    volCtrlN.maxValue.set( -0.4 )
    
    # control S 
    volCtrlS.upOffset.set( -10 )
    volCtrlS.minValue.set( -0.4 )
    
    # control E 
    volCtrlE.readFromAxis.set( 1 ) # up
    volCtrlE.rotOffset.set(-5.0)
    volCtrlE.minValue.set( 2 )
    volCtrlE.maxValue.set( -0.6 )
    
    # control W 
    volCtrlW.readFromAxis.set( 1 ) # up
    volCtrlW.rotOffset.set(-2.5)
    volCtrlW.minValue.set( 0 )
    
    #=================================================================================
    # NECK3_JNT
    volCtrlN, volCtrlS, volCtrlE, volCtrlW = volumeJoints.createFromJoint( 
                                             baseJnt = pm.PyNode( neckJoints[1] ),
                                             rotJnt = pm.PyNode( neckJoints[2] ),
                                             prefix = 'neck3',
                                             setupParent = rigmodule.Parts,
                                             jointsParent = rigmodule.Joints,
                                             controlsParent = rigmodule.Controls,
                                             rSide = False
                                             )
    # control N 
    volCtrlN.upOffset.set( 0 )
    volCtrlN.minValue.set( 2 )
    volCtrlN.maxValue.set( -0.4 )
    
    # control S 
    volCtrlS.upOffset.set( 0 )
    volCtrlS.minValue.set( -0.4 )
    
    # control E 
    volCtrlE.readFromAxis.set( 1 ) # up
    volCtrlE.rotOffset.set( 5 )
    volCtrlE.minValue.set( 2 )
    volCtrlE.maxValue.set( -0.6 )
    
    # control W 
    volCtrlW.readFromAxis.set( 1 ) # up
    volCtrlW.rotOffset.set( 22 )
    volCtrlW.minValue.set( 0 )
    
    #===========================================================================
    # HEAD
    #===========================================================================

    volCtrlN, volCtrlS, volCtrlE, volCtrlW = volumeJoints.createFromJoint( 
                                             baseJnt = pm.PyNode( neckJoints[-2] ),
                                             rotJnt = pm.PyNode( headJnt ),
                                             prefix = 'head1',
                                             setupParent = rigmodule.Parts,
                                             jointsParent = rigmodule.Joints,
                                             controlsParent = rigmodule.Controls,
                                             rSide = False
                                             )
    # control N 
    volCtrlN.upOffset.set( -10 )
    volCtrlN.minValue.set( 2 )
    volCtrlN.maxValue.set( 0 )
    
    # control S 
    volCtrlS.upOffset.set( 10 )
    
    # control E 
    volCtrlE.readFromAxis.set( 1 ) # up
    volCtrlE.rotOffset.set( -10 )
    volCtrlE.minValue.set( 2 )
    volCtrlE.maxValue.set( -0.4 )
    
    # control W 
    volCtrlW.readFromAxis.set( 1 ) # up
    volCtrlW.rotOffset.set( 45 )
    volCtrlW.minValue.set( -1 )
    
   
    
    rSide = False
    
    for i, side in enumerate( ['l_', 'r_'] ):
        
        #=======================================================================
        # HIPS
        #=======================================================================
        upperTwistJoints = legsRig[i]['upperTwistData']['twistjoints']
        lowerTwistJoints = legsRig[i]['lowerTwistData']['twistjoints']
        
        volCtrlN, volCtrlS, volCtrlE, volCtrlW = volumeJoints.createFromJoint( 
                                                 baseJnt = pm.PyNode( pelvisJnt ),
                                                 rotJnt = pm.PyNode( side + hipJnt ),
                                                 prefix = '{}hip1'.format(side),
                                                 setupParent = rigmodule.Parts,
                                                 jointsParent = rigmodule.Joints,
                                                 controlsParent = rigmodule.Controls,
                                                 rSide = rSide
                                                 )
        
                        
        
        
        # per part modifications
        
        # control N 
        volCtrlN.upOffset.set(35)
        volCtrlN.minValue.set( 1 )
        volCtrlN.maxValue.set( -2 )
        
        # control S 
        volCtrlS.upOffset.set(5)
        volCtrlS.minValue.set(-1)
        
        # control E 
        volCtrlE.readFromAxis.set( 1 ) # up
        volCtrlE.minValue.set( 2 )
        volCtrlE.maxValue.set( -0.6 )
        
        # control W 
        volCtrlW.rotOffset.set(-5)
        volCtrlW.readFromAxis.set( 1 ) # up
        volCtrlW.minValue.set( -0.2 )

        #=======================================================================
        # KNEES
        #=======================================================================
        
        volCtrlN, volCtrlS, volCtrlE, volCtrlW = volumeJoints.createFromJoint( 
                                                 baseJnt = pm.PyNode( side + hipJnt ),
                                                 rotJnt = pm.PyNode(side + kneeJnt),
                                                 prefix = '{}knee1'.format(side),
                                                 setupParent = rigmodule.Parts,
                                                 jointsParent = rigmodule.Joints,
                                                 controlsParent = rigmodule.Controls,
                                                 rSide = rSide
                                                 )
        # control N 
        volCtrlN.readFromAxis.set( 1 ) # up
        
        # control S 
        volCtrlS.readFromAxis.set( 1 ) # up
        
        # control E 
        volCtrlE.readFromAxis.set( 1 ) # up
        volCtrlE.rotOffset.set(30)
        
        # control W 
        volCtrlW.readFromAxis.set( 1 ) # up
        
        #=======================================================================
        # ANKLES
        #=======================================================================
        
        volCtrlN, volCtrlS, volCtrlE, volCtrlW = volumeJoints.createFromJoint( 
                                                 baseJnt = pm.PyNode( side + kneeJnt ),
                                                 rotJnt = pm.PyNode(side + footJnt),
                                                 prefix = '{}foot1'.format(side),
                                                 setupParent = rigmodule.Parts,
                                                 jointsParent = rigmodule.Joints,
                                                 controlsParent = rigmodule.Controls,
                                                 rSide = rSide
                                                 )
        # control N 
        volCtrlN.rotOffset.set(70)
        volCtrlN.upOffset.set(-25)
        volCtrlN.minValue.set( 2 )
        volCtrlN.maxValue.set( -1 )

        # control S 
        volCtrlS.rotOffset.set(45)
        volCtrlS.upOffset.set(32)
        volCtrlS.minValue.set( -1 )
        
        # control E 
        volCtrlE.readFromAxis.set( 1 ) # up
        volCtrlE.rotOffset.set(30)
        volCtrlE.minValue.set( 2 )
        volCtrlE.maxValue.set( -0.4 )
        
        # control W 
        volCtrlW.readFromAxis.set( 1 ) # up
        volCtrlW.rotOffset.set(75)
        volCtrlW.minValue.set( -0.7 )


        #=======================================================================
        # TOES
        #=======================================================================
        
        volCtrlN, volCtrlS, volCtrlE, volCtrlW = volumeJoints.createFromJoint( 
                                                 baseJnt = pm.PyNode( side + footJnt ),
                                                 rotJnt = pm.PyNode(side + toeJnt),
                                                 prefix = '{}toe1'.format(side),
                                                 setupParent = rigmodule.Parts,
                                                 jointsParent = rigmodule.Joints,
                                                 controlsParent = rigmodule.Controls,
                                                 rSide = rSide
                                                 )
        # control N 

        # control S 

        # control E 
        volCtrlE.readFromAxis.set( 1 ) # up
        volCtrlE.minValue.set( 2 )
        volCtrlE.maxValue.set( 0 )
        
        # control W 
        volCtrlW.readFromAxis.set( 1 ) # up


        #=======================================================================
        # CLAVICLES
        #=======================================================================
        
        volCtrlN, volCtrlS, volCtrlE, volCtrlW = volumeJoints.createFromJoint( 
                                                 baseJnt = pm.PyNode( spineJoints[-2] ),
                                                 rotJnt = pm.PyNode(side + clavicleJnt),
                                                 prefix = '{}clavicle1'.format(side),
                                                 setupParent = rigmodule.Parts,
                                                 jointsParent = rigmodule.Joints,
                                                 controlsParent = rigmodule.Controls,
                                                 rSide = rSide
                                                 )
        # control N 
        volCtrlN.minValue.set( 2 )
        volCtrlN.maxValue.set( 0 )
        
        # control S 

        # control E 
        volCtrlE.readFromAxis.set( 1 ) # up
        volCtrlE.rotOffset.set( 35 )
        volCtrlE.minValue.set( 2 )
        volCtrlE.maxValue.set( 0 )
        
        # control W 
        volCtrlW.readFromAxis.set( 1 ) # up
        volCtrlW.rotOffset.set( -35 )
        volCtrlW.minValue.set( -1.6 )
        
        
        #=======================================================================
        # SHOULDERS
        #=======================================================================
        
        volCtrlN, volCtrlS, volCtrlE, volCtrlW = volumeJoints.createFromJoint( 
                                                 baseJnt = pm.PyNode( side + clavicleJnt ),
                                                 rotJnt = pm.PyNode(side + shoulderJnt),
                                                 prefix = '{}shoulder1'.format(side),
                                                 setupParent = rigmodule.Parts,
                                                 jointsParent = rigmodule.Joints,
                                                 controlsParent = rigmodule.Controls,
                                                 rSide = rSide
                                                 )
        # control N 
        volCtrlN.upOffset.set( -7.5 )
        volCtrlN.minValue.set( 2 )
        volCtrlN.maxValue.set( -1 )        
        
        # control S 
        volCtrlS.upOffset.set( -55 )
        volCtrlS.minValue.set( -1 )
        volCtrlS.maxValue.set( 0 )    
        volCtrlS.upValue.set( 0.2 )    
        
        # control E 
        volCtrlE.readFromAxis.set( 1 ) # up
        volCtrlE.upValue.set( 0.35 ) 
        
        # control W 
        volCtrlW.readFromAxis.set( 1 ) # up
        volCtrlW.minValue.set( 2 )
        volCtrlW.maxValue.set( 0 )  
        volCtrlW.upValue.set( 0.65 ) 

        #=======================================================================
        # ELBOWS
        #=======================================================================
        
        volCtrlN, volCtrlS, volCtrlE, volCtrlW = volumeJoints.createFromJoint( 
                                                 baseJnt = pm.PyNode( side + shoulderJnt ),
                                                 rotJnt = pm.PyNode(side + elbowJnt),
                                                 prefix = '{}elbow1'.format(side),
                                                 setupParent = rigmodule.Parts,
                                                 jointsParent = rigmodule.Joints,
                                                 controlsParent = rigmodule.Controls,
                                                 rSide = rSide
                                                 )
        # control N 
        volCtrlN.readFromAxis.set( 1 ) # up

        # control S 
        volCtrlS.readFromAxis.set( 1 ) # up

        # control E 
        volCtrlE.readFromAxis.set( 1 ) # up
        volCtrlE.minValue.set( 0.2 )
        volCtrlE.rotOffset.set( 15 )
        
        # control W 
        volCtrlW.readFromAxis.set( 1 ) # up
        volCtrlW.rotOffset.set( -10 )
        
        #=======================================================================
        # HANDS
        #=======================================================================
        
        volCtrlN, volCtrlS, volCtrlE, volCtrlW = volumeJoints.createFromJoint( 
                                                 baseJnt = pm.PyNode( side + elbowJnt ),
                                                 rotJnt = pm.PyNode(side + handJnt),
                                                 prefix = '{}hand1'.format(side),
                                                 setupParent = rigmodule.Parts,
                                                 jointsParent = rigmodule.Joints,
                                                 controlsParent = rigmodule.Controls,
                                                 rSide = rSide
                                                 )
        # control N 
        volCtrlN.minValue.set( 2 )
        volCtrlN.maxValue.set( 0 )

        # control S 
        volCtrlS.minValue.set( -0.4 )
        volCtrlS.upOffset.set( 10 ) 
        
        # control E 
        volCtrlE.readFromAxis.set( 1 ) # up
        volCtrlE.minValue.set( 2 )
        volCtrlE.maxValue.set( 0 )  
        volCtrlE.rotOffset.set( -5 )
                
        # control W 
        volCtrlW.readFromAxis.set( 1 ) # up
        volCtrlW.rotOffset.set( 15 )
        
        rSide = True
