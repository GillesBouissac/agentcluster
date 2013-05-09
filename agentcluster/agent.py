#!/usr/bin/env python
#
from multiprocessing import Process
from multiprocessing.queues import JoinableQueue
from pysnmp import debug
from pysnmp.entity import engine, config
from pysnmp.entity.rfc3413 import cmdrsp, context
from agentcluster import AnyJsonDecoder
from agentcluster.exception import ClusterException
from agentcluster.snmpsetup import *
from agentcluster.transport import SocketHelper
import logging.config
import os
import signal
import sys
import threading
import time

__all__ = ["Agent"]
logger = logging.getLogger('agentcluster.agent')

class Agent(Process):
    """
        Agent entry point.

        We use Process instead of threads because Python threading model does not give enough control:
        acquire() methods are not interruptible and cannot be "timeouted". Therefore there is no possibility
        to stop a thread waiting for I/O. We cannot even combine waiting on multiple synchronization object
        in a single wait which could give a solution to this lack.
    """

    #
    # The following parameters are intended to be set after JSON conf file has been read in method parse
    #
    # Name of this virtual agent
    name = None;
    engineID = None;
    # Listen parameters
    listen = None;
    # Parameters for variations used by this agent
    variation = None;
    # Parameters for each snmp version
    snmpv1  = None;
    snmpv2c = None;
    snmpv3  = None;

    def __init__(self, confFile, tokens_start, parent_pid, monitoring_period):
        Process.__init__(self)

        self.monitoring_period = monitoring_period
        self.parent_pid = parent_pid
        self.tokens_start = tokens_start
        self.socketHelper = SocketHelper()

        # Set configuration from file
        self.parse (confFile)
        pass;

    def run(self):
        transportDispatcher = None;
        try:
            # Initialize the engine
            self.tokens_start.get();
            if self.active is not None and self.active.lower()=="false":
                logger.info ( 'Agent "%s": inactive', self.name );
                # Generates a deadlock to enter in sleep mode
                # Only an external signal can break this deadlock
                self.tokens_start.task_done();
                queue = JoinableQueue()
                queue.put(object());
                queue.join();

            logger.info ( 'Agent "%s": run', self.name );
            logger.debug ( 'EngineID="%s"', self.engineID );
            snmpEngine = engine.SnmpEngine(snmpEngineID=self.engineID)

            logger.debug ( 'Agent "%s": Configure transport layer', self.name );
            for protocol, params in self.listen.__dict__.items():
                if type(params) is list:
                    for param in params:
                        (domain, socket) = self.socketHelper.openSocket( protocol, param.encode('ascii'));
                        config.addSocketTransport( snmpEngine, domain, socket )
                else:
                    (domain, socket) = self.socketHelper.openSocket( protocol, params.encode('ascii'));
                    config.addSocketTransport( snmpEngine, domain, socket )

            logger.debug ( 'Agent "%s": Configure application layer', self.name );
            snmpContext = context.SnmpContext(snmpEngine)
            if self.snmpv1  is not None: SnmpConfHelperV1().configure(snmpEngine, snmpContext, self.snmpv1);
            if self.snmpv2c is not None: SnmpConfHelperV2().configure(snmpEngine, snmpContext, self.snmpv2c);
            if self.snmpv3  is not None: SnmpConfHelperV3().configure(snmpEngine, snmpContext, self.snmpv3);

            cmdrsp.GetCommandResponder(snmpEngine, snmpContext)
            cmdrsp.SetCommandResponder(snmpEngine, snmpContext)
            cmdrsp.NextCommandResponder(snmpEngine, snmpContext)
            cmdrsp.BulkCommandResponder(snmpEngine, snmpContext)


            logger.debug ( 'Agent "%s": Configured', self.name );
            self.tokens_start.task_done();

            logger.debug ( 'Starting parent and database watchdog' );
            self.monitor = Watchdog(self.parent_pid, self.monitoring_period)
            self.monitor.start()

            # Job will never end unless killed
            logger.debug ( 'Agent "%s": Running dispatcher', self.name );
            transportDispatcher = snmpEngine.transportDispatcher
            transportDispatcher.jobStarted(1) 
            transportDispatcher.runDispatcher()

        except KeyboardInterrupt:
            logger.debug ( 'Agent "%s": interrupted', self.name );
        except Exception:
            logger.error ( 'Unexpected exception cached in agent: %s', sys.exc_info()[1] );
            logger.debug ( "", exc_info=True );
        finally:
            if transportDispatcher != None:
                transportDispatcher.closeDispatcher()
            logger.info ( 'Agent "%s": end', self.name );
            logging.shutdown()
            try:
                self.tokens_start.task_done();
            except:
                pass;

    def parse(self, confFile):
        parsed = AnyJsonDecoder().decode( open(confFile).read() )
        self.__dict__.update(parsed.__dict__);
        if self.name is None:
            msg = 'Agent name is mandatory in conf file %s' % (confFile);
            logger.error ( msg );
            raise ClusterException(msg);
        if self.snmpv1 is None and self.snmpv2c is None and self.snmpv3 is None:
            msg = 'Agent "%s": no protocol specified in conf file %s' % (self.name, confFile);
            logger.error ( msg );
            raise ClusterException(msg);
        confPath = os.path.abspath( os.path.dirname(confFile) );
        if self.snmpv1  is not None: self.snmpv1.confPath  = confPath;
        if self.snmpv2c is not None: self.snmpv2c.confPath = confPath;
        if self.snmpv3  is not None: self.snmpv3.confPath  = confPath;


class Watchdog(threading.Thread):
    """ Daemon thread that check the parent thread and commit suicide if parent is missing """
    
    def __init__(self, parent_pid, monitoring_period):
        threading.Thread.__init__(self)
        self.parent_pid        = parent_pid
        self.monitoring_period = monitoring_period
        self.daemon            = True

    def run(self):
        if self.parent_pid is None:
            logger.debug ( 'No parent process to monitor, watchdog disabled' );
            return
        logger.debug ( 'Parent watchdog started, period: %ss', self.monitoring_period );
        while True:
            time.sleep(self.monitoring_period)
            try:
                os.kill(self.parent_pid, 0)
            except:
                logger.debug ( 'Parent process killed, suicide this agent' );
                logging.shutdown()
                # Rage quit should be universal
                os.kill(os.getpid(), signal.SIGKILL)
                return

if __name__ == "__main__":
    """ Use this when debugging agents """
    logging.config.fileConfig( "../agentcluster-log.conf" )
    pysnmplogger = logging.getLogger('pysnmp')
    if pysnmplogger.isEnabledFor(logging.DEBUG):
        debug.setLogger(debug.Debug("all"))
    logger.info ( 'Test agent alone' );
    tokens_start = JoinableQueue()
    tokens_start.put(object());
    agent = Agent ( "../tests/agents/linux/linux.agent", tokens_start, None, 0 );
    agent.run()

