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
