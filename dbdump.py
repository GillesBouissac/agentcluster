#!/usr/bin/env python
#
# Name:         DbDump
# Author:       Gilles Bouissac
# Description:  Dump the content of the index database in readable form
#
from agentcluster import confdir
from agentcluster.browser import Browser
from agentcluster.database import RecordIndex
import logging.config

logger = logging.getLogger('agentcluster.dbdump')
logging.config.fileConfig( "agentcluster-log.conf" )

# Browses databases:
br = Browser()
br.browse( [confdir.cache] )

db = RecordIndex( "", None )
for dbfile in br.foundFiles:
    db.dump_from_file(dbfile)

