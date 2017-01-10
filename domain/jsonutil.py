import traceback
import json

def load(*args, **kwargs):
    if not "object_hook" in kwargs:
        kwargs["object_hook"] = to_utf8
        
    try:    
      value = json.loads(*args, **kwargs)
    except:

      xbmc.log("KO: jsonutil.load:", xbmc.LOGERROR)
      xbmc.log(traceback.format_exc(), xbmc.LOGERROR)
      value = {}
     
    return value

def to_utf8(dct):

    if isinstance(dct, dict):
        return dict((to_utf8(key), to_utf8(value)) for key, value in dct.iteritems())
    elif isinstance(dct, list):
        return [to_utf8(element) for element in dct]
    elif isinstance(dct, unicode):
        return dct.encode('utf-8')
    else:
        return dct