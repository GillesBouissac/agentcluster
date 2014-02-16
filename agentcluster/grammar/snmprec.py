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
from pysnmp.proto import rfc1902, rfc1905
from pyasn1.compat.octets import octs2str, str2octs
from pyasn1.type import univ
from agentcluster.grammar.abstract import AbstractGrammar

class SnmprecGrammar(AbstractGrammar):
    tagMap = {}
    for t in ( rfc1902.Gauge32,
               rfc1902.Integer32,
               rfc1902.IpAddress,
               univ.Null,
               univ.ObjectIdentifier,
               rfc1902.OctetString,
               rfc1902.TimeTicks,
               rfc1902.Opaque,
               rfc1902.Counter32,
               rfc1902.Counter64,
               rfc1905.NoSuchObject,
               rfc1905.NoSuchInstance,
               rfc1905.EndOfMibView ):
        tagMap[str(sum([ x for x in t.tagSet[0] ]))] = t

    def build(self, oid, tag, val): return str2octs('%s|%s|%s\n' % (oid, tag, val))

    def parse(self, line):
        line = octs2str(line).strip(" \t\n\r")
        if line.startswith('#') or len(line)==0:
            # Ignore comment or empty line
            return None,None,None
        splitted = line.split('|', 2)
        return splitted[0],splitted[1],splitted[2]

    # helper functions

    def getTagByType(self, value):
        for tag, typ in self.tagMap.items():
            if typ.tagSet[0] == value.tagSet[0]:
                return tag
        else:
            raise Exception('error: unknown type of %s' % (value,))

    def hexifyValue(self, value):
        if value.tagSet in (univ.OctetString.tagSet,
                            rfc1902.Opaque.tagSet,
                            rfc1902.IpAddress.tagSet):
            nval = value.asNumbers()
            if nval and nval[-1] == 32 or \
                    [ x for x in nval if x < 32 or x > 126 ]:
                return ''.join([ '%.2x' % x for x in nval ])
