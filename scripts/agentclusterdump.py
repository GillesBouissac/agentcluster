#!/usr/bin/env python
#
# Name:         DbDump
# Author:       Gilles Bouissac
# Description:  Dump the content of the index database in readable form
#
from agentcluster import __version__, confdir, searchFiles
from agentcluster.database import Database
import os
import argparse
import agentcluster
import logging.config

logger = logging.getLogger('agentcluster.dbdump')
default_log_file = os.path.join ( agentcluster.__path__[0], "agentclusterdump-log.conf")
logging.config.fileConfig( default_log_file )

parser = argparse.ArgumentParser(description='SNMP Cluster of agents, by Gilles Bouissac. version %s'%__version__, formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument( '-c', '--cache-dir',  metavar='<cache-dir>', default=confdir.cache, help='Path to a directory that contain application cache. default: %(default)s' )
options = parser.parse_args()

if options.cache_dir:
    confdir.cache = options.cache_dir;

# Browses databases:
db = Database( "", None )
for dbfile in searchFiles( [confdir.cache] ):
    db.dump_from_file(dbfile)

