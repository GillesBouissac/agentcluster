from agentcluster.database import Database, oid2str
from pyasn1.type import univ
from pysnmp.smi import exval
from pysnmp.smi.instrum import AbstractMibInstrumController
import logging

__all__ = ["SnapshotFile", "SnapshotFileController"]
logger = logging.getLogger('agentcluster.snapshot')

class SnapshotFile (AbstractMibInstrumController):

    openedQueue = []
    maxQueueEntries = 15  # max number of open text and index files

    def __init__(self, textFile, textParser):
        self.__textParser = textParser
        self.__textFile = textFile
        self._db = Database(self.__textFile, self.__textParser)

    def indexText(self):
        self._db.create()
        return self

    def close(self):
        self._db.close()

    def openDb(self):
        if not self._db.isOpen():
            if len(SnapshotFile.openedQueue) > self.maxQueueEntries:
                SnapshotFile.openedQueue[0].close()
                del SnapshotFile.openedQueue[0]
            SnapshotFile.openedQueue.append(self)
            self._db.open()

    def processVarBinds(self, varBinds, nextFlag=False, setFlag=False):

        self.openDb()

        rspVarBinds = []
        for oid,_ in varBinds: 
            textOid = str( univ.OctetString( oid2str(oid) ) )

            if nextFlag:
                try:
                    (_oid, _, _tag, _val) = self._db.lookup_next( textOid )
                    subtreeFlag = False
                except KeyError:
                    rspVarBinds.append((oid, exval.endOfMib))
                    continue
            else:
                try:
                    (_oid, subtreeFlag, _tag, _val) = self._db.lookup( textOid )
                    subtreeFlag, int(subtreeFlag), True
                except KeyError:
                    rspVarBinds.append((oid, exval.noSuchInstance))
                    continue

            # _oid     = parser.evaluateOid(_oid)
            # _,_,_val = parser.evaluateValue(_oid,_tag,_val)
            rspVarBinds.append ( ( _oid, _val ) )

        return rspVarBinds
 
    def __str__(self):
        return str(self._db)

#
# Maps one or more snapshot file to SNMP engine
#
class SnapshotFileController (AbstractMibInstrumController):
    def __init__(self, dataFile):
        self.__dataFile = dataFile

    def __str__(self): return str(self.__dataFile)

    def readVars(self, varBinds, acInfo=None):
        return self.__dataFile.processVarBinds(varBinds, False)

    def readNextVars(self, varBinds, acInfo=None):
        return self.__dataFile.processVarBinds(varBinds, True)

    def writeVars(self, varBinds, acInfo=None):
        return self.__dataFile.processVarBinds(varBinds, False, True)

