'''
apiwrap (wrappers for Maya Python API)
@category Rigging @subcategory Utils

NOTE: !! functions returning new Python API 2.0 must have prefix "api2_" to prevent messing up other calls !!
	"om" namespace will still be used for old API, as it`s done in other modules. This will allow more easy refactoring
	to API 2.x when it`s properly implemented
'''

import maya.OpenMaya as om

def getMFnMesh( objectname ):
	
	"""
	get MFnMesh instance from given mesh object transform
	
	@param objectname: name of object (short or long)
	@type objectname: str
	@return: MFnMesh object
	"""
	
	dagpath = getDagPath( objectname )
	mFnMeshObj = om.MFnMesh( dagpath )
	
	return mFnMeshObj

def getDagPath( objectname ):
	
	'''
	get dagpath from object`s name
	
	:param objectname:str, name of object (short or long)
	:return: MDagPath object
	'''
	
	msel = om.MSelectionList()
	msel.add( objectname )
	dagpath = om.MDagPath()
	msel.getDagPath( 0, dagpath )
	
	return dagpath

def getMObject( objectname ):
	
	'''
	get dagpath from object`s name
	
	@param objectname: name of object (short or long)
	@type objectname: str
	@return: MDagPath object
	'''
	
	msel = om.MSelectionList()
	msel.add( objectname )
	mObject = om.MObject()
	msel.getDependNode( 0, mObject )
	
	return mObject
