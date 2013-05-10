#!/usr/bin/env python
#
# Name:         DbDump
# Author:       Gilles Bouissac
# Description:  Dump the content of the index database in readable form
#
from agentcluster import confdir, searchFiles
from agentcluster.database import Database
import logging.config

logger = logging.getLogger('agentcluster.dbdump')
logging.config.fileConfig( "agentcluster-log.conf" )

# Browses databases:
db = Database( "", None )
for dbfile in searchFiles( [confdir.cache] ):
    db.dump_from_file(dbfile)

