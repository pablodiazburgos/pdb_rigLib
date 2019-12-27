import inspect
import sys
from os.path import dirname 

# I'm going to define this little function to make this cleaner
# It's going to have a flag to let you specify the userPath you want to clear out
# But otherwise I'd going to assume that it's the userPath you're running the script from (_file_) 
def resetSessionForScript(userPath=None):
    if userPath is None:
      userPath = dirname(_file_)
    # Convert this to lower just for a clean comparison later  
    userPath = userPath.lower()

    toDelete = []
    # Iterate over all the modules that are currently loaded
    for key, module in sys.modules.iteritems():
      # There's a few modules that are going to complain if you try to query them
      # so I've popped this into a try/except to keep it safe
      try:
        # Use the "inspect" library to get the moduleFilePath that the current module was loaded from
          moduleFilePath = inspect.getfile(module).lower()
          
          # Don't try and remove the startup script, that will break everything
          if moduleFilePath == _file_.lower():
              continue
          
          # If the module's filepath contains the userPath, add it to the list of modules to delete
          if moduleFilePath.startswith(userPath):
              print "Removing %s" % key
              toDelete.append(key)
      except:
          pass
    
    # If we'd deleted the module in the loop above, it would have changed the size of the dictionary and
    # broken the loop. So now we go over the list we made and delete all the modules
    for module in toDelete:
        print ("".join(module), "was reloaded")
        del (sys.modules[module])

_all_ = ['resetSessionForScript']
