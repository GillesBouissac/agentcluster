from agentcluster.grammar import sap
from agentcluster.record import dump

class SapRecord(dump.DumpRecord):
    grammar = sap.SapGrammar()
    ext = 'sapwalk'
