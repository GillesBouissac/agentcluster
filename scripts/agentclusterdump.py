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
# Description:  Dump the content of the index database in readable form
#
from agentcluster import __version__, confdir, searchFiles
from agentcluster.database import Database
import os
import argparse
import agentcluster
import logging.config

logger = logging.getLogger('agentcluster.dbdump')
default_log_file = os.path.join ( agentcluster.__path__[0], "agentcluster-log-console.conf")
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

