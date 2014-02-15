#!/usr/bin/env python
"""
   SNMP Agent cluster

   SNMP Agent cluster is a tool that acts as pool of SNMP Agents built
   into real physical devices, from SNMP Manager's point of view.
   Simulator builds and uses a database of physical device's SNMP footprints 
   to respond like their original counterparts do.

   This tool is derived from SNMP simulator (http://sourceforge.net/projects/snmpsim/)

"""
from subprocess import call
import os
import sys

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
    'scripts':  [ 'scripts/agentclusterd.py', 'scripts/agentclusterdump.py' ],
    'packages': [ 'agentcluster', 'agentcluster.grammar', 'agentcluster.record' ]
} )

# install default log configuration file
params['package_data'] = {}
params['package_data']['agentcluster'] = [ 'agentcluster-log.conf', 'agentclusterdump-log.conf' ]

# install tests as data_files
params['data_files'] = []
for root,_,filenames in os.walk('tests'):
    target_root= 'share/agentcluster/' + '/'.join(os.path.split(root))
    for filename in filenames:
        params['data_files'].append(
            # path must be in independant format: "/" separator
            ( target_root, [ os.path.join(root,filename) ] )
        )

# install log conf files as data_files
if 'py2exe' in sys.argv:
    import py2exe
    # fix executables
    params['console'] = params['scripts']
    del params['scripts']
    # pysnmp used by agentcluster and snmpsim dynamically loads some of its *.py files
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

    # additional modules to be sure they are imported
    for m in ('dbm', 'gdbm', 'dbhash', 'dumbdb', 'shelve', 'random', 'math', 'bisect', 'hashlib',
              'sqlite3', 'subprocess', 'logging', 'argparse', 'threading', 'multiprocessing', 'time', 'datetime'):
        try:
            __import__(m)
        except ImportError:
            continue
        else:
            params['options']['py2exe']['includes'].append(m)


import distutils.command.install as old_install_mod
old_install = old_install_mod.install
from distutils.cmd import Command

class AgClusterInstallDebianService(Command):
    description = "Install agentcluster as service"
    user_options = []
    init_script_src = "debian/etc/init.d/agentcluster"
    init_script_dst = "/etc/init.d/agentcluster"
    cache_dir          = "/var/local/agentcluster"
    data_dir        = "/etc/agentcluster"
    def initialize_options(self): pass
    def finalize_options(self): pass
    def get_outputs(self): return [
        self.init_script_dst,
        self.data_dir,
        self.cache_dir
    ]
    def run(self):
        print "installing service script %s" % self.init_script_dst
        call(["cp", self.init_script_src, self.init_script_dst])
        print "changing mode of %s to 755" % self.init_script_dst
        call(["chmod", "755", self.init_script_dst])
        print "installing service %s" % self.init_script_dst
        call(["update-rc.d", "agentcluster", "defaults"])
        print "creating cache directory %s" % self.cache_dir
        call(["mkdir", "-p", self.cache_dir])
        print "preparing conf directory %s" % self.data_dir
        call(["mkdir", "-p", self.data_dir])

class AgClusterInstall(old_install):
    def is_debian_compatible(self):
        try:
            import platform
            (distname,_,_) = platform.linux_distribution()
            if distname in ( 'debian', 'Ubuntu' ): return True
        except:
            pass
        return False
    sub_commands = old_install.sub_commands + [('install_debian_service', is_debian_compatible),]

params['cmdclass'] = {
    'install':                  AgClusterInstall,
    'install_debian_service':   AgClusterInstallDebianService
}

setup(**params)
