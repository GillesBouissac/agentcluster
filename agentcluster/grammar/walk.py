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
from pysnmp.proto import rfc1902
from pyasn1.compat.octets import octs2str
from agentcluster.grammar import abstract

class WalkGrammar(abstract.AbstractGrammar):
    # case-insensitive keys as snmpwalk output tend to vary
    tagMap = {
        'OID:':         rfc1902.ObjectName,
        'INTEGER:':     rfc1902.Integer,
        'STRING:':      rfc1902.OctetString,
        'BITS:':        rfc1902.Bits,
        'HEX-STRING:':  rfc1902.OctetString,
        'GAUGE32:':     rfc1902.Gauge32,
        'COUNTER32:':   rfc1902.Counter32,
        'COUNTER64:':   rfc1902.Counter64,
        'IPADDRESS:':   rfc1902.IpAddress,
        'OPAQUE:':      rfc1902.Opaque,
        'UNSIGNED32:':  rfc1902.Unsigned32,  # this is not needed
        'TIMETICKS:':   rfc1902.TimeTicks     # this is made up
    }

    # possible DISPLAY-HINTs parsing should occur here
    def __getStringFilter(self):
        def __stringFilter(value):
            if not value:
                return value
            elif value[0] == value[-1] == '"':
                return value[1:-1]
            elif value.find(':') > 0:
                for x in value.split(':'):
                    for y in x:
                        if y not in '0123456789ABCDEFabcdef':
                            return value
                return [ int(x, 16) for x in value.split(':') ]
            else:
                return value
        return __stringFilter

    def __getOpaqueFilter(self):
        def __opaqueFilter(value):
            return [int(y, 16) for y in value.split(' ')]
        return __opaqueFilter

    def __getBitsFilter(self):
        def __bitsFilter(value):
            return ''.join(['%.2x' % int(y, 16) for y in value.split(' ')])
        return __bitsFilter

    def __getHexStringFilter(self):
        def __hexStringFilter(value):
            return [int(y, 16) for y in value.split(' ')]
        return __hexStringFilter

    def __init__(self):
        self.filterMap = {
            'OPAQUE:':      self.__getOpaqueFilter(),
            'STRING:':      self.__getStringFilter(),
            'BITS:':        self.__getBitsFilter(),
            'HEX-STRING:':  self.__getHexStringFilter()
        }

    def parse(self, line):
        line = octs2str(line).strip(" \t\n\r").decode('ascii', 'ignore').encode() # drop possible 8-bits
        if line.startswith('#') or len(line)==0:
            # Ignore comment or empty line
            return None,None,None
        splitted = line.split(' = ', 1)
        oid   = splitted[0]
        value = splitted[1]
        if oid and oid[0] == '.':
            oid = oid[1:]
        if value.startswith('Wrong Type (should be'):
            value = value[value.index(': ')+2:]
        if value.startswith('No more variables left in this MIB View'):
            value = 'STRING: '
        try:
            tag, value = value.split(' ', 1)
        except ValueError:
            # this is implicit snmpwalk's fuzziness
            if value == '""' or value == 'STRING:':
                tag = 'STRING:'
                value = ''
            else:
                tag = 'TimeTicks:'
        return oid, tag.upper(), self.filterMap.get(tag, lambda x: x)(value.strip())
