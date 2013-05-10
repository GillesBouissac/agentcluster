#!/usr/bin/env python
"""
   SNMP Agent cluster

   SNMP Agent cluster is a tool that acts as pool of SNMP Agents built
   into real physical devices, from SNMP Manager's point of view.
   Simulator builds and uses a database of physical device's SNMP footprints 
   to respond like their original counterparts do.

   This tool is derived from SNMP simulator (http://sourceforge.net/projects/snmpsim/)

"""
import sys
import os
import glob

classifiers = """\
Development Status :: 5 - Production/Stable
Environment :: Console
Intended Audience :: Developers
Intended Audience :: Education
Intended Audience :: Information Technology
Intended Audience :: Science/Research
Intended Audience :: System Administrators
Intended Audience :: Telecommunications Industry
License :: OSI Approved :: BSD License
Natural Language :: English
Operating System :: OS Independent
Programming Language :: Python :: 2.6
Programming Language :: Python :: 2.7
Topic :: Communications
Topic :: System :: Monitoring
Topic :: System :: Networking :: Monitoring
"""

def howto_install_distribute():
    print("""
   Error: You need the distribute Python package!

   It's very easy to install it, just type (as root on Linux):

   wget http://python-distribute.org/distribute_setup.py
   python distribute_setup.py

   Then you could make eggs from this package.
""")

def howto_install_setuptools():
    print("""
   Error: You need setuptools Python package!

   It's very easy to install it, just type (as root on Linux):

   wget http://peak.telecommunity.com/dist/ez_setup.py
   python ez_setup.py

   Then you could make eggs from this package.
""")

try:
    from setuptools import setup
    params = {
        'install_requires': [ 'pysnmp>=4.2.4' ],
        'zip_safe': False  # this is due to data and variation dirs
        }
except ImportError:
    for arg in sys.argv:
        if 'egg' in arg:
            if sys.version_info[0] > 2:
                howto_install_distribute()
            else:
                howto_install_setuptools()
            sys.exit(1)
    from distutils.core import setup
    params = {}
    if sys.version_info[:2] > (2, 4):
        params['requires'] = [ 'pysnmp(>=4.2.2)' ]

doclines = [ x.strip() for x in __doc__.split('\n') if x ]

params.update( {
    'name': 'agentcluster',
    'version': open(os.path.join('agentcluster', '__init__.py')).read().split('\'')[1],
    'description': doclines[0],
    'long_description': ' '.join(doclines[1:]),
    'maintainer': 'Gilles Bouissac',
    'author': 'Gilles Bouissac',
    'url': 'http://github/TBD',
    'license': 'BSD',
    'platforms': ['any'],
    'classifiers': [ x for x in classifiers.split('\n') if x ],
    'scripts':  [ 'scripts/agentclusterd', 'scripts/agentclusterdump.py' ],
    'packages': [ 'agentcluster', 'agentcluster.grammar', 'agentcluster.record' ]
} )

params['data_files'] = []

# install tests as data_files
for x in os.walk('tests'):
    params['data_files'].append(
        ( 'agentcluster/' + '/'.join(os.path.split(x[0])),
          glob.glob(os.path.join(x[0], '*.snmprec')) + \
          glob.glob(os.path.join(x[0], '*.snmpwalk')) + \
          glob.glob(os.path.join(x[0], '*.sapwalk')) + \
          glob.glob(os.path.join(x[0], '*.agent')) )
    )

# install debian service script as data_files
for x in os.walk('debian'):
    params['data_files'].append(
        ( 'agentcluster/' + '/'.join(os.path.split(x[0])),
          glob.glob(os.path.join(x[0], 'agentcluster'))
        )
    )

# install log conf files as data_files
for x in os.walk('scripts'):
    params['data_files'].append(
        ( 'agentcluster/' + '/'.join(os.path.split(x[0])),
          glob.glob(os.path.join(x[0], '*.conf'))
        )
    )

if 'py2exe' in sys.argv:
    import py2exe
    # fix executables
    params['console'] = params['scripts']
    del params['scripts']
    # pysnmp used by agentcluster dynamically loads some of its *.py files
    params['options'] = {
        'py2exe': {
            'includes': [
                'pysnmp.smi.mibs.*',
                'pysnmp.smi.mibs.instances.*',
                'pysnmp.entity.rfc3413.oneliner.*'
            ],
            'bundle_files': 1,
            'compressed': True
        }
    }

    params['zipfile'] = None

    del params['data_files']  # no need to store these in .exe

    # additional modules used by agentcluster but not seen by py2exe
    for m in ('dbm', 'gdbm', 'dbhash', 'dumbdb', 'shelve', 'random', 'math', 'bisect', 'hashlib',
              'sqlite3', 'subprocess', 'logging', 'argparse', 'threading', 'multiprocessing', 'time', 'datetime'):
        try:
            __import__(m)
        except ImportError:
            continue
        else:
            params['options']['py2exe']['includes'].append(m)

setup(**params)
