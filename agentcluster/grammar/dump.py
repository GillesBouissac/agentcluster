from pyasn1.compat.octets import octs2str
from pyasn1.type import univ
from pysnmp.proto import rfc1902
from agentcluster.grammar import abstract

class DumpGrammar(abstract.AbstractGrammar):
    tagMap = {
        '0': rfc1902.Counter32,
        '1': rfc1902.Gauge32,
        '2': rfc1902.Integer32,
        '3': rfc1902.IpAddress,
        '4': univ.Null,
        '5': univ.ObjectIdentifier,
        '6': rfc1902.OctetString,
        '7': rfc1902.TimeTicks,
        '8': rfc1902.Counter32,  # an alias
        '9': rfc1902.Counter64,
    }

    def __getNullFilter(self):
        def __nullFilter(value):
            return '' # simply drop whatever value is there when it's a Null
        return __nullFilter

    def __getUnhexFilter(self):
        def __unhexFilter(value):
            if value[:5].lower() == 'hex: ':
                value = [ int(x, 16) for x in value[5:].split('.') ]
            elif value[0] == '"' and value[-1] == '"':
                value = value[1:-1]
            return value
        return __unhexFilter

    def __init__(self):
        self.filterMap = {
            '4': self.__getNullFilter(),
            '6': self.__getUnhexFilter()
        }

    def parse(self, line):
        line = octs2str(line).strip(" \t\n\r")
        if line.startswith('#') or len(line)==0:
            # Ignore comment or empty line
            return None,None,None
        oid, tag, value = octs2str(line).split('|', 2)
        return oid, tag, self.filterMap.get(tag, lambda x: x)(value.strip())

