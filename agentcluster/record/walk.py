from agentcluster.grammar import walk
from agentcluster.record import dump

class WalkRecord(dump.DumpRecord):
    grammar = walk.WalkGrammar()
    ext = 'snmpwalk'
