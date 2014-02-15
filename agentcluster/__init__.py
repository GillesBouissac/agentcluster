
# Module Version Numbers: http://www.python.org/dev/peps/pep-0396/
__version__ = '0.1.1'

import hashlib
import json
import os

class Any:
    """ Class intended to be filled with members read from a JSON file """
    def __init__(self, **_dict):
        self.__dict__.update(_dict)

class AnyJsonDecoder(json.JSONDecoder):
    """
        Default JSON decoder reads key as unicode we cannot use them to map them directly into class members.
        This class do this and instantiate an Any class for each object found in a JSON file.
        Of course, in the JSON file, keys must be valid python keywords to allow direct access.
    """
    def __init__(self):
        json.JSONDecoder.__init__(self, object_hook=self.dict_to_object)
    def dict_to_object(self, d):
        args = dict( (key.encode('ascii'), value) for key, value in d.items())
        inst = Any(**args)
        return inst

def md5sum(filename):
    # Code from http://stackoverflow.com/a/11143944/2366884
    md5 = hashlib.md5()
    with open(filename,'rb') as f: 
        for chunk in iter(lambda: f.read(128*md5.block_size), b''): 
            md5.update(chunk)
    return md5.hexdigest()

def searchFiles (fsElements, acceptCb=None):
    if type(fsElements) is not list:
        fsElements = [ fsElements ]
    foundFiles = []
    for fsElement in fsElements:
        fsElement = os.path.abspath(fsElement);
        for root, _, filenames in os.walk(fsElement, followlinks=True):
            for filename in filenames:
                fullpath = root + os.path.sep + filename
                fext = os.path.splitext(filename)[1][1:]
                if acceptCb and not acceptCb(fullpath, fext):
                    continue
                foundFiles.append(fullpath);
    return foundFiles
