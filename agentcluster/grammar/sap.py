#
# Copyright (c) 2005-2014, Ilya Etingof <ilya@glas.net> 
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
from pyasn1.compat.octets import octs2str
from pyasn1.type import univ
from pysnmp.proto import rfc1902
from agentcluster.grammar import abstract

class SapGrammar(abstract.AbstractGrammar):
    tagMap = {
        'Counter': rfc1902.Counter32,
        'Gauge': rfc1902.Gauge32,
        'Integer': rfc1902.Integer32,
        'IpAddress': rfc1902.IpAddress,
#        '<not implemented?>': univ.Null,
        'ObjectID': univ.ObjectIdentifier,
        'OctetString': rfc1902.OctetString,
        'TimeTicks': rfc1902.TimeTicks,
        'Counter64': rfc1902.Counter64
    }

    def __getStringFilter(self):
        def __stringFilter(value):
            if value[:2] == '0x':
                value = [ int(value[x:x+2], 16) for x in range(2, len(value[2:])+2, 2) ]
            return value
        return __stringFilter

    def __init__(self):
        self.filterMap = {
            'OctetString': self.__getStringFilter()
        }

    def parse(self, line):
        line = octs2str(line).strip(" \t\n\r")
        if line.startswith('#') or len(line)==0:
            # Ignore comment or empty line
            return None,None,None
        oid, tag, value = [ x.strip() for x in octs2str(line).split(',', 2) ]
        return oid, tag, self.filterMap.get(tag, lambda x: x)(value.strip())
