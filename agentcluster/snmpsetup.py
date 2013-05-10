from pysnmp.entity import config
from agentcluster.exception import ClusterException
from agentcluster.record import dump, mvc, sap, walk, snmprec
from agentcluster.snapshot import SnapshotFile, SnapshotFileController
import logging
import os

__all__ = ["SnmpConfHelperV1", "SnmpConfHelperV2", "SnmpConfHelperV3"]
logger = logging.getLogger('agentcluster.snmp')

class SnmpConfHelperBase:
    recordSet = {
        dump.DumpRecord.ext: dump.DumpRecord(),
        mvc.MvcRecord.ext: mvc.MvcRecord(),
        sap.SapRecord.ext: sap.SapRecord(),
        walk.WalkRecord.ext: walk.WalkRecord(),
        snmprec.SnmprecRecord.ext: snmprec.SnmprecRecord()
    }

    def configure(self, snmpEngine, snmpContext, params):
        if (params is None) or (params.users is None):
            msg = 'Snmp configuration needs at least one user'
            logger.error ( msg );
            raise ClusterException(msg);
        self._configureUsers ( snmpEngine, snmpContext, params );
        self._configureMibs  ( snmpEngine, snmpContext, params );

    def _buildMibInstrum(self, confRootPath, snapshotPath ):
        logger.debug ( 'Creating mib instrum for "%s"', os.path.basename(snapshotPath) );
        snapshotFullPath = os.path.abspath ( confRootPath + os.path.sep + snapshotPath )
        dExt = os.path.splitext(snapshotFullPath)[1][1:]
        if dExt not in self.recordSet:
            msg = 'Usupported snapshot file extension, snapshot ignored %s' % (snapshotFullPath)
            logger.warning ( msg );
            return;
        snapshotFile = SnapshotFile( snapshotFullPath, self.recordSet[dExt]).indexText()
        return SnapshotFileController(snapshotFile)

class SnmpConfHelperV1(SnmpConfHelperBase):
    version="V1"

    def __init__(self):
        # List of contexts indexed by community
        self.contexts = {};

    def _configureMibs(self, snmpEngine, snmpContext, params):
        logger.debug ( 'Configure MIBs' );

        for community, snapshotPath in params.mib.__dict__.items():
            mibInstrum = self._buildMibInstrum ( params.confPath, snapshotPath )
            try:
                contextName = self.contexts[community]
                # Remove previous context if any
                snmpContext.unregisterContextName(contextName)
                # Registers the new context
                snmpContext.registerContextName(contextName, mibInstrum)
            except KeyError:
                msg = "Error: There is no user declared with the mib name '%s'" % community
                logger.debug ( msg );
                raise ClusterException( msg )

    def _configureUsers(self, snmpEngine, snmpContext, params):
        logger.debug ( 'Configure users' );
        for user in params.users:
            logger.debug ( 'Creating user "%s"', user.name );
            # Compute a fake context name                
            contextName = "%sSystem-context-%s" % (self.version,user.name)
            self.contexts[user.name] = contextName;
            # Register the community
            config.addV1System(snmpEngine=snmpEngine, securityName=contextName, communityName=user.name, contextName=contextName)

class SnmpConfHelperV2(SnmpConfHelperV1):
    version="V2c"
    pass;

class SnmpConfHelperV3(SnmpConfHelperBase):

    authAlgorithms = {
      'md5': config.usmHMACMD5AuthProtocol,
      'sha': config.usmHMACSHAAuthProtocol,
      'none': config.usmNoAuthProtocol
    }

    privAlgorithms = {
      'des': config.usmDESPrivProtocol,
      '3des': config.usm3DESEDEPrivProtocol,
      'aes': config.usmAesCfb128Protocol,
      'aes128': config.usmAesCfb128Protocol,
      'aes192': config.usmAesCfb192Protocol,
      'aes256': config.usmAesCfb256Protocol,
      'none': config.usmNoPrivProtocol
    }

    def _configureMibs(self, snmpEngine, snmpContext, params):
        logger.debug ( 'Configure MIBs' );

        for contextName, snapshotPath in params.mib.__dict__.items():
            mibInstrum = self._buildMibInstrum ( params.confPath, snapshotPath )
            # Remove previous context if any
            snmpContext.unregisterContextName(contextName)
            # Registers the new context
            snmpContext.registerContextName(contextName, mibInstrum)

    def _configureUsers(self, snmpEngine, snmpContext, params):
        logger.debug ( 'Configure users' );
        for user in params.users:
            logger.debug ( 'Creating user "%s"', user.name );

            # Parse authentication algorithm
            authAlgo = config.usmNoAuthProtocol;
            if user.authAlgo is not None:
                if not user.authAlgo in self.authAlgorithms:
                    msg = 'Invalid snmp V3 Authentification algorithm %s. Valid values are: %s' % (user.authAlgo, self.authAlgorithms.keys())
                    logger.error ( msg );
                    raise ClusterException(msg);
                else:
                    authAlgo = self.authAlgorithms[user.authAlgo.lower()];

            # Parse privacy algorithm
            privAlgo = config.usmNoPrivProtocol;
            if user.privAlgo is not None:
                if not user.privAlgo in self.privAlgorithms:
                    msg = 'Invalid snmp V3 Privacy algorithm %s. Valid values are: %s' % (user.privAlgo, self.privAlgorithms.keys())
                    logger.error ( msg );
                    raise ClusterException(msg);
                else:
                    privAlgo = self.privAlgorithms[user.privAlgo.lower()];

            # Check provided parameters
            if authAlgo==config.usmNoAuthProtocol and privAlgo!=config.usmNoPrivProtocol:
                msg = 'Privacy impossible without authentication for user: %s' % (user.name)
                logger.error ( msg );
                raise ClusterException(msg);

            if authAlgo!=config.usmNoAuthProtocol and user.authPass is None:
                msg = 'No authentication password given for user %s' % (user.name)
                logger.error ( msg );
                raise ClusterException(msg);

            if privAlgo!=config.usmNoPrivProtocol and user.privPass is None:
                msg = 'No privacy password given for user %s' % (user.name)
                logger.error ( msg );
                raise ClusterException(msg);

            # At least we can create the user
            config.addV3User( snmpEngine, user.name,
                authAlgo, user.authPass,
                privAlgo, user.privPass
            )
            pass;

        pass;


