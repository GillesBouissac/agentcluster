from agentcluster import confdir, md5sum
from pyasn1.compat.octets import str2octs
from pyasn1.type import univ
from whichdb import whichdb
import anydbm as dbm
import logging
import os
import sys

logger = logging.getLogger('agentcluster.database')

def oid2str( oid ):
    return ".".join( [ '%s' % x for x in oid ] )

def str2oid( oidstr ):
    return [ int(x) for x in oidstr.split(".") ]

class Database:

    # Version of the database structure
    version = "1.0"

    # Maintain the list of all declared databases
    all = []

    def __init__(self, textFile, textParser):
        self.sourceFile = textFile
        self.textParser = textParser
        self.__dbFile = textFile
        self.__dbFile = self.__dbFile + os.path.extsep + 'dbm'
        self.__dbFile = os.path.join(confdir.cache, os.path.splitdrive(self.__dbFile)[1].replace(os.path.sep, '_'))
        self.__db = self.__text = None
        self.__dbType = '?'
        Database.all.append(self)

    def __str__(self):
        return 'Data file %s, %s-indexed, %s' % (
            self.sourceFile, self.__dbType, self.__db and 'opened' or 'closed'
        )

    def isOpen(self):
        return self.__db is not None

    def check_cache(self,cachedir):
        if not os.path.exists(cachedir):
            logger.info ( 'Creating cache directory %s...', cachedir );
            try:
                os.makedirs(cachedir)
            except OSError:
                logger.critical( 'ERROR: %s: %s', cachedir, sys.exc_info()[1] );
                sys.exit(-1)
            else:
                logger.debug ( 'Cache directory created' );

    def isUpToDate(self):
        """ Check if index database is up to date """
        textFileSum = md5sum(self.sourceFile)
        upToDate      = False
        for dbFile in ( self.__dbFile + os.path.extsep + 'db', self.__dbFile ):
            try:
                if not os.path.exists(dbFile):
                    # Database doesn't exist, try next one
                    continue;
                if not whichdb(dbFile):
                    # Not in a readable format
                    logger.debug ( 'Database not in a readable format: %s', dbFile );
                    break;
                # From here, database exists and is readable
                db = dbm.open(dbFile)
                if textFileSum != db["__source_md5__"]:
                    logger.debug ( 'Source file checksum differs from the one used to build the database: %s', self.sourceFile );
                    db.close()
                    break;
                if not db["__version__"] == Database.version:
                    logger.debug ( 'Database version "%s" doesn\'t match this version "%s"', db["__version__"], Database.version );
                    db.close()
                    break;
                db.close()
                # Everything is ok with the existing database
                upToDate = True
                break;
            except Exception:
                pass
        return upToDate

    def refresh (self):
        """ Rebuild the index from source file """

        # The cache directory must exist
        self.check_cache(confdir.cache)

        # In case something has already been done with this objecttextFileStamp
        self.close();

        # these might speed-up indexing
        db_oids = []
        open_flags = 'nfu' 
        while open_flags:
            try:
                db = dbm.open(self.__dbFile, open_flags)
                db["__version__"]    = Database.version
                db["__source_md5__"] = md5sum(self.sourceFile)
            except Exception:
                open_flags = open_flags[:-1]
                if not open_flags:
                    raise
            else:
                break

        text = open(self.sourceFile, 'rb')

        logger.debug ( 'Building index %s for data file %s (open flags \"%s\")', self.__dbFile, self.sourceFile, open_flags );

        # Build the "direct" indexes to have direct access to values
        nb_direct = nb_next = 0
        lineNo = 0
        while 1:

            try:
                oid = line = None
                while not oid:
                    line = text.readline()
                    lineNo += 1
                    if not line: break
                    oid, tag, val = self.textParser.grammar.parse(line)
                if not oid: break
            except Exception:
                db.close()
                exc = sys.exc_info()[1]
                try:
                    os.remove(self.__dbFile)
                except OSError:
                    pass
                raise Exception('Data error at %s:%d: %s' % ( self.sourceFile, lineNo, exc ) )

            try:
                _oid     = self.textParser.evaluateOid(oid)
            except Exception:
                db.close()
                exc = sys.exc_info()[1]
                try:
                    os.remove(self.__dbFile)
                except OSError:
                    pass
                raise Exception( 'OID error at %s:%d: %s' % ( self.sourceFile, lineNo, exc ) )

            try:
                _tag = self.textParser.evaluateTag(tag)
            except Exception:
                logger.warn ( 'Validation error at line %s, tag %r: %s', lineNo, tag, sys.exc_info()[1] );

            try:
                _val = self.textParser.evaluateValue( oid, tag, val, dataValidation=True)
            except Exception:
                logger.warn ( 'Validation error at line %s, value %r: %s', lineNo, val, sys.exc_info()[1] );

            # for lines serving subtrees, type is empty in tag field
            db[oid] = '%s,%d,%s,%s' % (oid2str(_oid), tag[0] == ':', _tag, _val)
            db_oids.append ( _oid );
            nb_direct = nb_direct+1

        # Build the "next" indexes to have direct access to next values

        # First we need oids splitted into nodes. We cannot sort them by string
        #   comparison: "1"<"10"<"2" and we want 1<2<10
        db_oids.sort()
        for i in range(len(db_oids)-1):
            oid         = db_oids[i]
            oid_txt     = oid2str(oid)
            # The easy one
            key      = "next."+oid_txt
            db[key]  = oid2str(db_oids[i+1])
            nb_next  = nb_next+1
            # Now the parents: their next is current oid unless they already have one next
            nodes = oid[:-1]
            for n in range(len(nodes)):
                key     = "next." + oid2str(nodes[:n+1])
                if not db.has_key(key):
                    db[key] = oid_txt
                    nb_next = nb_next+1
        # The last one have no next
        key = "next." + oid2str(db_oids[ len(db_oids)-1 ])
        db[key] = ""
        nb_next = nb_next+1

        text.close()
        db.close()
        logger.debug ( 'Index ok: %d direct entries, %d next entries' % (nb_direct,nb_next) );
        self.__dbType = whichdb(self.__dbFile)

    def create(self):
        if not self.isUpToDate():
            self.refresh();
        self.__dbType = whichdb(self.__dbFile)
        return self

    def str2class(self, class_full_name):
        module_tree = class_full_name.split(".")
        module_name = ".".join(module_tree[:-1])
        class_name  = module_tree[-1:][0]
        m = __import__(module_name, globals(), locals(), class_name)
        # get the class, will raise AttributeError if class cannot be found
        c = getattr(m, class_name)
        return c

    def lookup(self, oid):
        """ Returns the record which oid is exactly the given one or None if the record doesn't exist """
        oid, is_subtree, tag, val = self.__db[oid].split(str2octs(','), 3)
        try:
            tag_class = self.str2class(tag);
        except Exception:
            logger.error ( 'Could not interpret tag %s', tag, exc_info=True );
            raise
        return univ.ObjectIdentifier(oid), is_subtree, tag_class, tag_class(val)

    def lookup_next(self, oid):
        """ Returns the record which oid is the closest after the given one or None if none exist after """
        next_oid = self.__db["next." + oid]
        return self.lookup(next_oid)

    def dump(self):
        """ Dump current database """
        self.dump_from_file(self.__dbFile)

    def dump_from_file(self, dbfile):
        """ Dump a database in debug log level """
        logger.debug ( "Dumping database %s", dbfile );
        db = dbm.open(dbfile, 'r')
        oids = db.keys();
        oids.sort()
        for oid in oids:
            logger.debug ( "  %s = %s", oid, db[oid] );
        db.close()

    def open(self):
        self.__db = dbm.open(self.__dbFile)

    def close(self):
        if self.__text!=None:self.__text.close()
        if self.__db!=None:self.__db.close()
        self.__db = self.__text = None
