import os
import sys
import tempfile

__all__ = ["variation", "data", "cache"]

if sys.platform[:3] == 'win':
    variation = [
        os.path.join(os.environ['HOMEPATH'], 'agentcluster', 'Variation'),
        os.path.join(os.environ['APPDATA'], 'agentcluster', 'Variation'),
        os.path.join(os.environ['PROGRAMFILES'], 'agentcluster', 'Variation'),
        os.path.join(os.path.split(__file__)[0], 'variation')
    ]
    data = [
        os.path.join(os.environ['HOMEPATH'], 'agentcluster', 'Data'),
        os.path.join(os.environ['APPDATA'], 'agentcluster', 'Data'),
        os.path.join(os.environ['PROGRAMFILES'], 'agentcluster', 'Data'),
        os.path.join(os.path.split(__file__)[0], 'data')
    ]
else:
    variation = [
        os.path.join(os.environ['HOME'], '.agentcluster', 'variation'),
        os.path.join('/', 'etc', 'agentcluster', 'variation'),
        os.path.join(os.path.split(__file__)[0], 'variation')
    ]
    data = [
        os.path.join(os.environ['HOME'], '.agentcluster', 'data'),
        os.path.join('/', 'etc', 'agentcluster', 'data'),
        os.path.join(os.path.split(__file__)[0], 'data')
    ]

cache = os.path.join(tempfile.gettempdir(), 'agentcluster')
