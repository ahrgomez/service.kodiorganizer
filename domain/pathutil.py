import os
import traceback

import notificationsutil

if os.name == "nt":
  fs_encoding = ""
else:
  fs_encoding = "utf8"

def encode(path):
    if not type(path) == unicode:
        path = unicode(path, "utf-8", "ignore")

        if fs_encoding:
          path = path.encode(fs_encoding, "ignore")

    return path

def exists(path):
    path = encode(path)
    try:
          return os.path.exists(path)
    except:
      notificationsutil.writelog("KO: pathutil.exists: %s" %(path))
      notificationsutil.writelog(traceback.format_exc())
      return False

def join(*paths):
    return os.path.join(*paths)

def mkdir(path):
    path = encode(path)
    try:
        os.mkdir(path)
    except:
        notificationsutil.writelog("KO: pathutil.mkdir: %s" %(path))
        notificationsutil.writelog(traceback.format_exc())
        return False
    else:
        return True

def validate(path):
    chars = ":*?<>|"
    if path.find(":\\") == 1:
        unidad = path[0:3]
        path = path[2:]
    else:
        unidad = ""

    return unidad + ''.join([c for c in path if c not in chars])

def writefile(path, data):
    path = encode(path)
    try:
        f = open(path, "wb")
        f.write(data)
        f.close()
    except:
        notificationsutil.writelog("KO: pathutil.write: %s" %(path))
        notificationsutil.writelog(traceback.format_exc())
        return False
    else:
        return True

def basename(path):
    return split(path)[1]