#!/usr/bin/env python
#
# Name:         SnmpCluster
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
#       OS:               Only tested on Linux environment (Ubuntu).
#

from multiprocessing import JoinableQueue
from pysnmp import debug
from agentcluster import __version__, confdir, Any
from agentcluster.agent import Agent
from agentcluster.browser import AgentBrowser
from datetime import datetime, timedelta
import argparse
import logging.config
import os
import stat
import sys
import threading
import time

logger = logging.getLogger('agentcluster.main')
pysnmplogger = logging.getLogger('pysnmp')

class SnmpCluster:

    # List of instantiated agents indexed by their conf file full path
    agents = {};
    # Agent restart delay after crash
    monitoring_period = 30
    # This tokens will be used to wait for child Agents configuration
    tokens_start = JoinableQueue()
    # The monitoring thread
    watchdog = None

    def __init__(self, options):
        if options.monitoring is not None:
            self.monitoring_period = options.monitoring

    def parse_confs(self,conf_dir):
        logger.info ( 'Parsing conf directories for agent specifications' );
        agentBrowser = AgentBrowser();
        agentBrowser.browse(conf_dir)
        for conf in agentBrowser.foundFiles:
            conf = os.path.abspath(conf)
            logger.debug ( 'Found agent specifications in %s', conf );
            # Records this new agent placeholder
            self.agents[conf] = Any( **{"stamp":os.stat(conf)[8], "handle":None} );

    def relaunch_agent(self, conf):
        try:
            agent = self.agents[conf].handle
            # Kill a previous agent if any
            if agent!=None:
                logger.debug ( 'Killing agent %d', agent.ident );
                agent.terminate()
                self.agents[conf].handle = None
            # Instantiate a new agent from this conf file and record it
            logger.debug ( 'Starting agent for configuration %s', conf );
            agent = Agent(conf, self.tokens_start, os.getpid(), self.monitoring_period);
            self.agents[conf].handle = agent
            self.agents[conf].stamp = os.stat(conf)[8]
        except Exception:
            logger.error ( 'Exception launching agent: %s', sys.exc_info()[1] );
            logger.debug ( "", exc_info=True );
            return;
        # In order to sequence child start: give one token and wait till the child is started
        # This is easier to read logs
        agent.start()
        self.tokens_start.put(object())
        self.tokens_start.join()

    def run(self):

        try:
            logger.info ( 'Snmp cluster Server starting' );

            # Search for agent specifications
            self.parse_confs(confdir.data);

            logger.debug ( 'Starting agent watchdog' );
            self.watchdog = Watchdog(self)
            self.watchdog.start()

            # Generates a deadlock to enter in sleep mode
            # Only an external signal can break this deadlock
            logger.info ( 'Server started' );
            queue = JoinableQueue()
            queue.put(object());
            queue.join();

        except KeyboardInterrupt:
            logger.info ( 'Server interrupted' );
        except Exception:
            logger.error ( 'Exception cached in main process: %s', sys.exc_info()[1] );
            logger.debug ( "", exc_info=True );
        finally:
            # First stop the monitoring to avoid restarting killed agents
            if self.watchdog is not None:
                self.watchdog.shutdown = True
                self.watchdog.join()
            for _,infos in self.agents.items():
                logger.debug ( 'Killing agent %d', infos.handle.ident );
                infos.handle.terminate()
            logger.info ( 'Snmp cluster Server end' );
            logging.shutdown()

class Watchdog(threading.Thread):
    """ Daemon thread that check the status of each child and restart it if necessary """

    # True when the server is shutting down
    shutdown = False

    def __init__(self, server):
        threading.Thread.__init__(self)
        self.server   = server
        self.period   = timedelta ( seconds = self.server.monitoring_period )
        self.daemon   = True

    def run(self):
        logger.info ( 'Agent monitoring started' );
        period_start = datetime.now()-self.period
        while True:
            if (datetime.now()-period_start) >= self.period:
                for (conf,infos) in self.server.agents.items():
                    need_restart=False
                    if infos.handle is None: 
                        logger.debug ( 'Agent need to be started: %s', conf );
                        need_restart=True
                    elif not infos.handle.is_alive():
                        logger.debug ( 'Agent has been killed: %s', conf );
                        need_restart=True
                    if os.path.exists(conf) and os.stat(conf)[8]>infos.stamp:
                        logger.debug ( 'Agent configuration has been changed: %s', conf );
                        need_restart=True
                    if need_restart:
                        self.server.relaunch_agent(conf);
                # Start a new period
                period_start = datetime.now()
            # Polling for shutdown must be fast
            time.sleep(1)
            if self.shutdown:
                logger.info ( 'Monitoring end' );
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
    parser = argparse.ArgumentParser(description='SNMP Cluster of agents, by Gilles Bouissac. version %s'%__version__)
    parser.add_argument( '-v', '--version', action='version', version=('%(prog)s '+__version__) )
    parser.add_argument( '-l', '--log-config', metavar='<log-conf-file>', help='Path to a python log config file in dictionary format', type=file_type_r )
    parser.add_argument( '-a', '--agent-dir', metavar='<agent-config-dir>', nargs='+', help='Path to directories that will be scanned for .agent specification files', type=dir_type )
    parser.add_argument( '-c', '--cache-dir', metavar='<cache-dir>', help='Path to a directory that will contain application cache. default: %(default)s', default=confdir.cache )
    parser.add_argument( '-m', '--monitoring', metavar='<delay>', help='This is the time in second to monitor agent activity', type=int, choices=range(1,3600), default=30 )
    # parser.add_argument( '-m', '--variation-modules-dir', metavar='<path/to/variations>', help='Path to a directory containing variation classes', type=dir_type )
    options = parser.parse_args()

    # Global parameters
    if options.log_config is not None:
        logging.config.fileConfig(options.log_config)
    if options.agent_dir is not None:
        for ddir in options.agent_dir: confdir.data.append(ddir)
    if options.cache_dir is not None:
        confdir.cache = options.cache_dir;
    if pysnmplogger.isEnabledFor(logging.DEBUG):
        debug.setLogger(debug.Debug("all"))

    # Instantiate the server and start it
    server = SnmpCluster(options)
    server.run()

