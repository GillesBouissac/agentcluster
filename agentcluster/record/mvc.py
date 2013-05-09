from agentcluster.grammar import mvc
from agentcluster.record import dump

class MvcRecord(dump.DumpRecord):
    grammar = mvc.MvcGrammar()
    ext = 'MVC'  # an alias to .dump
