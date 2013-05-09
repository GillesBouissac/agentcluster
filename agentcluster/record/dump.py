from pyasn1.error import PyAsn1Error
from pyasn1.type import univ
from agentcluster.exception import ClusterException
from agentcluster.grammar import dump
from agentcluster.record import abstract
import sys

class DumpRecord(abstract.AbstractRecord):
    grammar = dump.DumpGrammar()
    ext = 'dump'

    def evaluateOid(self, oid):
        return univ.ObjectIdentifier(oid)

    def evaluateTag(self, tag):
        return self.grammar.tagMap[tag]

    def evaluateValue(self, oid, tag, value, **context):
        return self.grammar.tagMap[tag](value)

    def evaluate(self, line, **context):
        oid, tag, value = self.grammar.parse(line)
        oid = self.evaluateOid(oid)
        if context.get('oidOnly'):
            value = None
        else:
            try:
                oid, tag, value = self.evaluateValue(oid, tag, value, **context)
            except PyAsn1Error:
                raise ClusterException('value evaluation for %s = %r failed: %s\r\n' % (oid, value, sys.exc_info()[1]))
        return oid, value

    def formatOid(self, oid):
        return univ.ObjectIdentifier(oid).prettyPrint()

    def formatValue(self, oid, value, **context):
        return self.formatOid(oid), self.getTagByType(value), str(value)

    def format(self, oid, value, **context):
        textOid, textTag, textValue = self.formatValue(oid, value, **context)
        return self.grammar.build(
            textOid, textTag, textValue
        )
