#!/usr/bin/env python
#
# Copyright (c) 2014, Gilles Bouissac <agentcluster@gmail.com>
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
from agentcluster import AnyJsonDecoder, makeAppName
from agentcluster.database import Database
from agentcluster.exception import ClusterException
from agentcluster.snmpsetup import *
from agentcluster.transport import SocketHelper
from datetime import datetime, timedelta
from multiprocessing import Process
from multiprocessing.queues import JoinableQueue
from pysnmp import debug
from pysnmp.entity import engine, config
from pysnmp.entity.rfc3413 import cmdrsp, context
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

    def __init__(self, confFile, tokens_start, parent_pid, monitoring_period):
        Process.__init__(self)
        self.monitoring_period = monitoring_period
        self.parent_pid = parent_pid
        self.tokens_start = tokens_start
        self.socketHelper = SocketHelper()

        # The following parameters are intended to be set after JSON conf file has been read in method parse

        # Name of this virtual agent
        self.name = "";
        self.engineID = None;
        # Listen parameters
        self.listen = None;
        # Parameters for variations used by this agent
        self.variation = None;
        # Parameters for each snmp version
        self.snmpv1  = None;
        self.snmpv2c = None;
        self.snmpv3  = None;

        # Set configuration from file
        self.parse (confFile)

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

            engineID_bin=None;
            if self.engineID!=None:
                try:
                    engineID_bin = self.engineID.decode("hex");
                except Exception:
                    logger.warn ( 'Cannot convert configured engine ID to byte array, engine ID ignored: %s', self.engineID );
                    logger.debug ( "", exc_info=True );
            else:
                logger.debug ( "No context engineID specified, let pysnmp generate one" );

            snmpEngine = engine.SnmpEngine(snmpEngineID=engineID_bin);

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
            logger.error ( 'Unexpected exception catched in agent: %s', sys.exc_info()[1] );
            logger.error ( "", exc_info=True );
        finally:
            if transportDispatcher != None:
                transportDispatcher.closeDispatcher()
            logger.info ( 'Agent "%s": end', self.name );
            logging.shutdown()
            try:
                # Issue #3: Python 2.7.6 releases the parent process if children is killed
                # not Python 2.6.6 so we must still release the token. 
                self.tokens_start.task_done();
            except:
                pass;
            # Issue #3: This agent is no longer usable so commit suicide to be sure
            # This process won't become a zombie and that parent will start a new agent 
            os.kill(os.getpid(), signal.SIGKILL)

    def parse(self, confFile):
        parsed = AnyJsonDecoder().decode( open(confFile).read() )
        self.__dict__.update(parsed.__dict__);
        if parsed.name is None:
            msg = 'Agent name is mandatory in conf file %s' % (confFile);
            logger.error ( msg );
            raise ClusterException(msg);
        self.name = makeAppName(parsed.name)
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
        self.parent_pid     = parent_pid
        self.period         = timedelta ( seconds = monitoring_period )
        self.daemon         = True

    def conf_check(self):
        for db in Database.all:
            if not db.isUpToDate():
                logger.info ( 'Configuration file changed: %s', db.sourceFile );
                db.refresh();
        return

    def run(self):
        if self.parent_pid is None:
            logger.debug ( 'No parent process to monitor, watchdog disabled' );
            return
        logger.info ( 'Agent watchdog started' );
        period_start = datetime.now()-self.period
        while True:
            if (datetime.now()-period_start) >= self.period:
                try:
                    self.conf_check()
                except:
                    logger.debug ( 'Exception in agent watchdog %s', sys.exc_info()[1] );
                # Start a new period
                period_start = datetime.now()
            # Polling for shutdown must be fast
            time.sleep(1)
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
    logging.config.fileConfig( "../scripts/agentcluster-log.conf" )
    pysnmplogger = logging.getLogger('pysnmp')
    if pysnmplogger.isEnabledFor(logging.DEBUG):
        debug.setLogger(debug.Debug("all"))
    logger.info ( 'Test agent alone' );
    tokens_start = JoinableQueue()
    tokens_start.put(object());
    agent = Agent ( "../tests/agents/windows/windows.agent", tokens_start, None, 0 );
    agent.run()

