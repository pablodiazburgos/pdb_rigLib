"""
Module to make the base structure of folders and subfolders for rigging
@category Rigging
@author: Pablo Diaz Burgos
"""

import os
import shutil

from ..rigpresets.generic import rig

class CreateFolders():
    
    def __init__(self, rootDir, assetName):
        
        # check if rootDir exists
        rootDirCheck = os.path.exists( rootDir )

        if not rootDirCheck:
            
            raise Exception('# not able to find %s, please check the path' % rootDir)

        self.assetName = assetName
        self.rootDir = rootDir
        
    def makeFolders(self):
        
        # create path and folder for main rig folder
        mainFolderDir = os.path.join(self.rootDir, self.assetName)
        if not os.path.exists(mainFolderDir):
            os.mkdir(mainFolderDir)
            
        self.makeSubFolders(mainFolderDir = mainFolderDir)
    
    def makeSubFolders(self, mainFolderDir = ''):
        # sub folder names
        rigFolders = ['model',
                     'rig',
                     'builder',
                     'controlShapes',
                     'anim',
                     'playblast',
                     'temp',
                     'scripts',
                     'scripts/python',
                     'weights',
                     'weights/skinCluster',
                     'weights/blendWeights',
                     'weights/deformers'
                     ]
        
        # define version in sub folders
        version = 'versions'
        nonVersion = rigFolders[6:]
        
        for folder in rigFolders:
            
            rigFullPath = os.path.join(mainFolderDir, folder)
            
            newRigFullPath = [rigFullPath]
            # check if version folder should be included
            if not folder in nonVersion:
                versionFullPath = os.path.join(rigFullPath, version)
                newRigFullPath.append(versionFullPath)
            
            # make the folders
            for path in newRigFullPath:
                if not os.path.exists(path):
                    os.mkdir(path)
    
    def copyRigScript(self, rigType):
        
        """
        copy rig script to folders
        """
        parentDir = os.path.join( self.rootDir, self.assetName )
        pythonScriptFolder = 'scripts/python'
        initFile = '__init__.py'
        genericRigFile = 'rig.py'
        genericRigFileSource = genericRigFile
        genericGameFile = 'rig_game.py'
        
        if rigType == 'game':
            genericRigFileSource = genericGameFile

        rigModuleDir = '%sRig' % self.assetName
        rigModuleDestinationDir = os.path.join( parentDir, pythonScriptFolder )
        rigScriptFileDestinationDir = os.path.join( rigModuleDestinationDir, rigModuleDir )
        
        rigFileDir = os.path.dirname( rig.__file__ )
        rigScriptFilepathSource = os.path.join( rigFileDir, genericRigFileSource )
        
        rigScriptFilepathDest = os.path.join( rigScriptFileDestinationDir, genericRigFile )
        rigModuleInitFilepathDest = os.path.join( rigScriptFileDestinationDir, initFile )
        
        # make folders and files
        
        if not os.path.exists( rigScriptFileDestinationDir ):
            
            os.mkdir( rigScriptFileDestinationDir )
            
        if not os.path.exists( rigModuleInitFilepathDest ):
            
            open( rigModuleInitFilepathDest, 'a' ).close()
        
        if not os.path.exists( rigScriptFilepathDest ):
            
            shutil.copy( rigScriptFilepathSource, rigScriptFilepathDest )
        
        
def make(rootDir, assetName, rigType = ''):
    """
    function to make the base folder to make a rig 
    :param rootDir: str, directory where we want to create the folders
    :param assetName: str, name of the main folder and the asset to work with
    :param rigType: str, optional type or rig (only generic is supported right now)
    :return: None
    """
    
    createFolders = CreateFolders(rootDir, assetName)
    createFolders.makeFolders()
    createFolders.copyRigScript( rigType )

    print '# base folder structure created for %s in %s' % (assetName, rootDir)
    
    
