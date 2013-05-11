#!/usr/bin/env python
#
# Name:         AgentCluster
# Author:       Gilles Bouissac
# Description:  This module is able to simulate a network of SNMP agents on one single host
#               Each agent has its own IP, port, protocol versions, users, mibs, communities, contextes.
#
# Credits:      This module is derived from snmpsim module (http://snmpsim.sourceforge.net).
#
# Enhancements from snmpsim:
#
#       multiple engines: This module is able to instantiate multiple virtual agents in child processes.
#                         Each agent is defined declaratively into a JSON file.
#
#       dynamic:          Snapshots files are reloaded automatically when modified
#                         agents are restarted automatically when definition files are modified
#
#       performances:     No more dichotomy based on file seek, searches are exclusively based on database.
#                         GetNexts are deterministic.
#
#       snapshots:        We can use comments (line beginning with #) and empty lines in snapshot files
#
# Refactoring:
#
#       logging:          Change sys.stdout.write to Python logging framework. this allow to send logs
#                         to console/syslog/file etc... just with a conf file
#
#       options:          Change use of getopt to argparse
#
# Compatibility:
#
#       snmprec.py:       Will not be integrated, you can use snmpsim version to produce snapshots
#                         from mib definition files
#       mib2dev.py:       Will not be integrated, you can use snmpsim version to produce snapshots
#                         from live snmp agents to produce snmprec files
#
# Restrictions:
#
#       variations:       Not integrated, maybe one day
#       index MIB:        Not integrated, maybe one day
#
#       Python:           Only tested with v2.6 and v2.7
#       OS:               Only tested on Linux environment (Ubuntu 64/Squeeze 64).
#
from agentcluster import __version__, confdir, Any, md5sum, searchFiles
from agentcluster.agent import Agent
from agentcluster.database import Database
from datetime import datetime, timedelta
from multiprocessing import JoinableQueue
from multiprocessing.process import current_process
from pysnmp import debug
import agentcluster
import argparse
import logging.config
import os
import stat
import sys
import threading
import time

logger = logging.getLogger('agentcluster.main')
pysnmplogger = logging.getLogger('pysnmp')

class AgentCluster:
    """ Main process class """

    def __init__(self, options):
        # Agent restart delay after crash
        self.monitoring_period = 30
        # The monitoring thread
        self.watchdog = None

        if options.monitoring is not None:
            self.monitoring_period = options.monitoring

    def run(self):

        try:
            logger.info ( 'Agent cluster server starting' );

            logger.info ( 'Configurations will be scanned in directories:' );
            for directory in confdir.data:
                logger.info ( '  o %s', os.path.abspath(directory) );

            self.watchdog = Watchdog(self.monitoring_period)
            self.watchdog.start()

            # Generates a deadlock to enter in sleep mode
            # Only an external signal can break this deadlock
            logger.info ( 'Agent cluster server started' );
            queue = JoinableQueue()
            queue.put(object());
            queue.join();

        except KeyboardInterrupt:
            logger.info ( 'Agent cluster server interrupted' );
        except Exception:
            logger.error ( 'Exception catched in main process: %s', sys.exc_info()[1] );
            logger.debug ( "", exc_info=True );
        finally:
            # First stop the monitoring to avoid restarting killed agents
            if self.watchdog is not None:
                self.watchdog.shutdown = True
                self.watchdog.join()
            logger.info ( 'Agent cluster server end' );
            logging.shutdown()

class Watchdog(threading.Thread):
    """ Daemon thread that check the status of each child and restart it if necessary """

    def __init__(self, monitoring_period):
        threading.Thread.__init__(self)
        self.period   = timedelta ( seconds = monitoring_period )
        self.daemon   = True
        # True when the server is shutting down
        self.shutdown = False
        # List of instantiated agents indexed by their conf file full path
        self.agents = {};
        # This tokens will be used to wait for child Agents configuration
        self.tokens_start = JoinableQueue()

    def parse_confs(self,conf_dir):
        try:
            agents = {}
            for conf in searchFiles(conf_dir, lambda _,ext: ext=='agent'):
                conf = os.path.abspath(conf)
                # Records this new agent placeholder
                agents[conf] = Any( **{"sum":0, "current_sum":md5sum(conf), "handle":None} );
        except Exception:
            logger.error ( 'Exception parsing conf %s', sys.exc_info()[1] );
            logger.debug ( "", exc_info=True );
            return;
        return agents

    def agent_stop(self, conf):
        try:
            agent = self.agents[conf].handle
            # Kill a previous agent if any
            if agent!=None:
                logger.info ( 'Agent "%s" stopped: %s', agent.name, conf );
                agent.terminate()
                self.agents[conf].handle = None
        except Exception:
            logger.error ( 'Exception while killing agent: %s', sys.exc_info()[1] );
            logger.debug ( "", exc_info=True );
            return;

    def agent_start(self, conf, conf_sum):
        try:
            # Instantiate a new agent from this conf file and record it
            agent = Agent(conf, self.tokens_start, os.getpid(), self.period.total_seconds());
            self.agents[conf].handle = agent
            self.agents[conf].sum    = conf_sum
            # In order to sequence child start: give one token and wait till the child is started
            # This is easier to read logs
            agent.start()
            self.tokens_start.put(object())
            self.tokens_start.join()
            logger.info ( 'Agent "%s" started: %s', agent.name, conf );
        except Exception:
            logger.error ( 'Exception launching agent: %s', sys.exc_info()[1] );
            logger.debug ( "", exc_info=True );
            return;

    def agents_check(self):
        """ Check that every agent is running and launch them if necessary """

        # Builds the list of agents that should be running
        required_agents = self.parse_confs(confdir.data)

        # Kills running agents that are no more required
        for (conf,infos) in self.agents.copy().items():
            if conf not in required_agents:
                self.agent_stop(conf)
                del self.agents[conf]

        # Fills ref list with new data
        if not required_agents:
            return;
        for (conf,infos) in required_agents.items():
            if conf not in self.agents:
                self.agents[conf] = infos
            else:
                self.agents[conf].current_sum = infos.current_sum;

        # Finally start those missing or
        #         restart those whose configuration has changed
        for (conf,infos) in self.agents.items():
            need_restart=False
            if infos.handle is None: 
                logger.debug ( 'Agent need to be started: %s', conf );
                need_restart=True
            elif not infos.handle.is_alive():
                logger.debug ( 'Agent "%s" has been killed: %s', infos.handle.name, conf );
                need_restart=True
            elif infos.current_sum!=infos.sum:
                logger.debug ( 'Agent "%s" configuration has been changed: %s', infos.handle.name, conf );
                need_restart=True
            if need_restart:
                self.agent_stop(conf);
                self.agent_start(conf,infos.current_sum);

    def database_gc(self):
        """ Remove database that are not up to date """
        try:
            # We try, if we cannot this is maybe because the db is loaded and will be refreshed by its owner
            for conf in searchFiles(confdir.cache, lambda _,ext: ext in ['db', 'dbm'] ):
                if not Database.isDbUpToDate ( conf ):
                    logger.info ( 'Cleaning obsolete database %s', conf );
                    os.remove(conf)
                    continue
        except:
            logger.debug ( 'Database cannot be cleaned %s', sys.exc_info()[1] );

    def run(self):
        logger.info ( 'Master watchdog started' );
        period_start = datetime.now()-self.period
        while True:
            if (datetime.now()-period_start) >= self.period:
                try:
                    self.agents_check()
                    self.database_gc()
                except:
                    logger.debug ( 'Exception in master watchdog %s', sys.exc_info()[1] );
                # Start a new period
                period_start = datetime.now()
            # Polling for shutdown must be fast
            time.sleep(1)
            if self.shutdown:
                logger.info ( 'Master watchdog end' );
                for _,infos in self.agents.items():
                    logger.debug ( 'Killing agent %d', infos.handle.ident );
                    infos.handle.terminate()
                return


if __name__ == "__main__":

    def dir_type (string):
        inode = os.lstat(string)
        if not stat.S_ISDIR(inode.st_mode):
            msg = "%s is not a valid directory"%string
            raise argparse.ArgumentTypeError(msg)
        return string
    
    def file_type_r (string):
        inode = os.lstat(string)
        if not stat.S_ISREG(inode.st_mode):
            msg = "%s is not a valid directory"%string
            raise argparse.ArgumentTypeError(msg)
        return string

    # Process command-line options
    default_log_file = os.path.join ( agentcluster.__path__[0], "agentcluster-log.conf")
    epilog = "Default list of data directories if [-a|--agent-dir] is not set:\n"
    for directory in confdir.data:
        epilog += "  - %s\n" % directory
    epilog += "\n"
    epilog += "Default log configuration file if [-l|--log-config] is not set:\n"
    epilog += "  - %s\n" % default_log_file
    parser = argparse.ArgumentParser(description='SNMP Cluster of agents, by Gilles Bouissac. version %s'%__version__, epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument( '-v', '--version',    action='version', version=('%(prog)s '+__version__) )
    parser.add_argument( '-l', '--log-config', metavar='<log-conf-file>', type=file_type_r, help='Path to a python log config file in dictionary format' )
    parser.add_argument( '-a', '--agent-dir',  metavar='<agent-config-dir>', type=dir_type, nargs='+', help='Path to data directories that will be scanned for *.agent files. See below for default values if not set.' )
    parser.add_argument( '-c', '--cache-dir',  metavar='<cache-dir>', default=confdir.cache, help='Path to a directory that will contain application cache. default: %(default)s' )
    parser.add_argument( '-m', '--monitoring', metavar='<delay>', type=int, choices=range(2,3600), default=30, help='This is the maximum time in second to detect configuration file changes' )
    # parser.add_argument( '-m', '--variation-modules-dir', metavar='<path/to/variations>', help='Path to a directory containing variation classes', type=dir_type )
    options = parser.parse_args()

    # Global parameters
    if options.log_config:
        logging.config.fileConfig(options.log_config)
    elif os.path.exists(default_log_file):
        logging.config.fileConfig(default_log_file)
    if options.agent_dir:
        confdir.data = []
        for ddir in options.agent_dir:
            confdir.data.append(ddir)
    if options.cache_dir:
        confdir.cache = options.cache_dir;
    if pysnmplogger.isEnabledFor(logging.DEBUG):
        debug.setLogger(debug.Debug("all"))

    # Instantiate the server and start it
    current_process().name = os.path.split(__file__)[1]
    server = AgentCluster(options)
    server.run()
