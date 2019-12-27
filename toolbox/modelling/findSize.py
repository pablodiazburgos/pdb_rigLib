"""
module to create size guides for object transform
@author: Pablo Diaz Burgos
"""

import maya.cmds as mc

class SizeTool():
    
    def __init__( self, ui, statusBar ):
        
        self.ui = ui
        self.statusBar = statusBar
        self.statusColor = None
    
    def setConnections(self):
        
        self.ui.findSize_btn.clicked.connect( self.createObjectSize )
        self.ui.findeSizeDelSel_btn.clicked.connect( self.deleteSelectedSizeGuides )
        self.ui.findeSizeDelAll_btn.clicked.connect( self.deleteAllSizeGuides )

    def createObjectSize(self, objectList = None):
        """
        creates a distance node per axis based on bounding box
        :param objectList: list ( str ), objects to get sizes
        """
        
        objectList = mc.ls( sl = True, type = 'transform' )
        
        if not objectList:
            
            self.statusBar.showMessage("Please select at least one object") 
            self.statusBar.setStyleSheet("color: yellow") 
            return
        
        measureNodesGrp = 'measureNodes_grp'

        for obj in objectList:
            
            self.obj = obj
            
            # create a top group to hold each transform distances node
            if not mc.objExists( measureNodesGrp ):
                mc.group( em = True, n = measureNodesGrp )
            
            # check if there is transforms in passed obj   
            self.stopFunc = None
            
            self._transformsCheck()
            
            
            self._checkIfGeo()
            
            print 'stopFunc:', self.stopFunc
            
            if self.stopFunc:
                mc.select( self.obj )
                return
            
            objName = obj + '_distance_grp'
            # check if size guides already exists
            if mc.objExists( objName ):
                
                print "# %s already exists... skipping" % objName
                self.statusBar.showMessage('Distance for {0} already exists ... skip'.format( obj ) )
                self.statusBar.setStyleSheet("color: yellow")
                return
            
            objGrp = mc.group(em = True, p = measureNodesGrp, n = objName )
            
            bbMin = mc.getAttr( '%s.boundingBoxMin' % obj )[0]
            bbMax = mc.getAttr( '%s.boundingBoxMax' % obj )[0]
            
    
            for i, v in enumerate( ['X', 'Y', 'Z'] ):
                
                # assign color id
                idColor = -1
                
                if v == 'X': idColor = 13
                if v == 'Y': idColor = 14
                if v == 'Z': idColor = 6
                
                # assign real position in the right index
                if i == 0:
                    maxPos = [ bbMax[0], bbMin[1], bbMin[2] ]
                
                if i == 1:
                    maxPos = [ bbMin[0], bbMax[1], bbMin[2] ]
            
                if i == 2:
                    maxPos = [ bbMin[0], bbMin[1], bbMax[2] ]
                    
                
                disNodeShape = mc.distanceDimension( sp = (bbMin[0], bbMin[1], bbMin[2] ), ep = ( maxPos[0], maxPos[1], maxPos[2] ))
                
                # assign color to distance shape
                mc.setAttr(disNodeShape + '.ove', 1)
                mc.setAttr(disNodeShape + '.ovc', idColor)
                
                # rename distance locs and parent
                disLocs = mc.listConnections( disNodeShape )
                
                if not mc.objExists( '%s_startXYZ_loc' % obj ):
                    
                    strartLoc = mc.rename(disLocs[0], '%s_startXYZ_loc' %  obj )
                    mc.parent(strartLoc, objGrp)
                    self._lockHideChannels( strartLoc )
                    
                endLoc = mc.rename(disLocs[1], '%s_end%s_loc' % ( obj, v ))
                mc.parent(endLoc, objGrp)
                
                skipAxis = v.lower()
                self._lockHideChannels( endLoc, skipAxis )
                
                # get distance transform man, rename an parent
                disTransform = mc.listRelatives(disNodeShape, p = True)[0]
                disNode = mc.rename(disTransform, '%s_%sAxis_dis'% ( obj, v ) )
                
                self._lockHideChannels( disNode )
                
                mc.parent(disNode, objGrp)
        
            mc.parentConstraint( obj, objGrp, mo = True )
            mc.scaleConstraint( obj, objGrp, mo = True )
            
            # select all the passed objects
            mc.select( objectList )
            
            self.statusBar.showMessage ( "Size guides created for selected objects" )
            self.statusBar.setStyleSheet( "color: green" )
            
    def deleteSelectedSizeGuides(self, objectList = None ):
        
        """
        creates a distance node per axis based on bounding box
        :param objectList: list ( str ), objects to delete size guides
        """
        
        objectList = mc.ls( sl = True, type = 'transform' )
        
        if not objectList:
            
            self.statusBar.showMessage("Please select at least one object")
            self.statusBar.setStyleSheet("color: yellow" )
            return
        
        for obj in objectList:
            
            objName = obj + '_distance_grp'
            
            if mc.objExists( objName ):
                
                mc.delete( objName )
                self.statusBar.showMessage('Distance guides deleted for selected objects')
                self.statusBar.setStyleSheet("color: green")
            else:
                self.statusBar.showMessage('Please select at least one object')
                self.statusBar.setStyleSheet( "color: yellow")
                return
                
    def deleteAllSizeGuides( self ):
        
        measureNodesGrp = 'measureNodes_grp'
        if mc.objExists( measureNodesGrp ):
            
            mc.delete( measureNodesGrp )
            self.statusBar.showMessage('All size guides were deleted')
            self.statusBar.setStyleSheet("color: green")
            
        else:
            
            self.statusBar.showMessage('No size guides were found')
            self.statusBar.setStyleSheet("color: yellow")
            return
                
    def _lockHideChannels(self, obj, skipAxis = None):
        
        xformVals = ['.t', '.r', '.s']
        
        axis = ['x', 'y', 'z']
    
        xformAxis = []
        for x in xformVals:
            for ax in axis:
                xformAxis.append( x + ax )
        
        if skipAxis:
            removeVal = '.t' + skipAxis
            xformAxis.remove( removeVal )
       
        for xform in xformAxis:
            mc.setAttr( obj + xform, l = True, k = False, cb = False )
         
    def _transformsCheck(self):
        
        for attr in ['.t', '.r']:
            for ax in ['x', 'y', 'z']:
                
                if mc.getAttr(self.obj + attr + ax) != 0.0:
                  self.statusBar.showMessage('Transforms for "{0}" are not freezed, cannot create size guides'.format( self.obj ) )   
                  self.statusBar.setStyleSheet("color: red") 
                  
                  print "-----> inside t check"
                  
                  self.stopFunc = True
                  return 
                else:
                  continue
     
        for ax in ['x', 'y', 'z']:
            if mc.getAttr(self.obj + '.s' + ax) != 1.0:
              self.statusBar.showMessage('Transforms for "{0}" are not freezed, cannot create size guides'.format( self.obj ) )   
              self.statusBar.setStyleSheet( "color: red" ) 
              
              print "-----> inside s check"
              
              self.stopFunc = True
            else:
              continue
          
    def _checkIfGeo(self):      
        
        shapeObj = mc.listRelatives( self.obj, s = True )
        
        if not shapeObj:
            
            self.statusBar.showMessage('"{0}" does not have shape object, cannot create guides'.format( self.obj ) )  
            self.statusBar.setStyleSheet("color: red")
            
            self.stopFunc = True
            return 
        
        validTypes = ['mesh', 'nurbsSurface']
        
        if not mc.nodeType( shapeObj ) in validTypes:
            
            self.statusBar.showMessage('"{0}" is not valid to create guides'.format( self.obj )  ) 
            self.statusBar.setStyleSheet("color: red")
            
            self.stopFunc = True
            return 
        
        pass
            
            
          
          
          
          
          
          