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
