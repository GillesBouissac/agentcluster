from agentcluster.exception import ClusterException

class AbstractGrammar:
    def parse(self, line):
        raise ClusterException('Method not implemented at %s' % self.__class__.__name__)

    def build(self, oid, tag, val):
        raise ClusterException('Method not implemented at %s' % self.__class__.__name__)

    def getTagByType(self, val):
        raise ClusterException('Method not implemented at %s' % self.__class__.__name__)
