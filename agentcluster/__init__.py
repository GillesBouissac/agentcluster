#
# Copyright (c) 2014, Gilles Bouissac <agentcluster@gmail.com>
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
#   * Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE
# GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
__version__ = '0.2.0'

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
