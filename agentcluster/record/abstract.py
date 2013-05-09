from agentcluster.exception import ClusterException
from agentcluster.grammar import abstract

class AbstractRecord:
    grammar = abstract.AbstractGrammar()
    ext = ''

    def evaluateOid(self, oid):
        raise ClusterException('Method not implemented at %s' % self.__class__.__name__)

    def evaluateValue(self, oid, tag, value, **context):
        raise ClusterException('Method not implemented at %s' % self.__class__.__name__)

    def evaluateTag(self, tag):
        raise ClusterException('Method not implemented at %s' % self.__class__.__name__)

    def evaluate(self, line, **context):
        raise ClusterException('Method not implemented at %s' % self.__class__.__name__)

    def formatOid(self, oid):
        raise ClusterException('Method not implemented at %s' % self.__class__.__name__)

    def formatValue(self, oid, value, **context):
        raise ClusterException('Method not implemented at %s' % self.__class__.__name__)

    def format(self, oid, value, **context):
        raise ClusterException('Method not implemented at %s' % self.__class__.__name__)

