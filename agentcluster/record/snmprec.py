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
from agentcluster.grammar import snmprec
from agentcluster.record import dump

class SnmprecRecord(dump.DumpRecord):
    grammar = snmprec.SnmprecGrammar()
    ext = 'snmprec'

    def evaluateTag(self, tag):
        if tag and tag[-1] == 'x':
            tag = tag[:-1]
        return self.grammar.tagMap[tag]

    def evaluateValue(self, oid, tag, value, **context):
        if tag and tag[-1] == 'x':
            tag = tag[:-1]
            hexvalue = value
        else:
            hexvalue = None

        if hexvalue is None:
            return oid, tag, self.grammar.tagMap[tag](value)
        else:
            return self.grammar.tagMap[tag](hexValue=hexvalue)

    def formatValue(self, oid, value, **context):
        if 'nohex' in context and context['nohex']:
            hexvalue = None
        else:
            hexvalue = self.grammar.hexifyValue(value)

        textTag = self.grammar.getTagByType(value)

        if hexvalue:
            textTag, textValue = textTag + 'x', hexvalue
        else:
            textTag, textValue = textTag, str(value)

        return self.formatOid(oid), textTag, textValue
