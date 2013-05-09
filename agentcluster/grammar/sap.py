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
