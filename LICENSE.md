## Agentcluster software license

    AGENTCLUSTER license 
    
    Copyright (c) 2014, Gilles Bouissac <agentcluster@gmail.com>
    All rights reserved.
    
    Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
    
    * Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution. 
    
    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
    THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDERS AND CONTRIBUTORS
    BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE
    GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
    LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. 

## Open source licenses

Some source files in this software are adaptations of source files from [snmpsim][snmpsim] distributed under this license:

    SNMP Simulator License 
    
    Copyright (c) 2005-2014, Ilya Etingof <ilya@glas.net> 
    All rights reserved.
    
    Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
    
    * Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
    
    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
    THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDERS AND CONTRIBUTORS
    BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE
    GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
    LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

### List of files with few modifications

    o-----------------------------------o------------------------------------o
    |          agentcluster             |               snmpsim              |
    o-----------------------------------o------------------------------------o
    | agentcluster/grammar/__init__.py  | snmpsim/grammar/__init__.py        |
    | agentcluster/grammar/abstract.py  | snmpsim/grammar/abstract.py        |
    | agentcluster/grammar/dump.py      | snmpsim/grammar/dump.py            |
    | agentcluster/grammar/mvc.py       | snmpsim/grammar/mvc.py             |
    | agentcluster/grammar/sap.py       | snmpsim/grammar/sap.py             |
    | agentcluster/grammar/snmprec.py   | snmpsim/grammar/snmprec.py         |
    | agentcluster/grammar/walk.py      | snmpsim/grammar/walk.py            |
    | agentcluster/record/__init__.py   | snmpsim/record/__init__.py         |
    | agentcluster/record/abstract.py   | snmpsim/record/abstract.py         |
    | agentcluster/record/dump.py       | snmpsim/record/dump.py             |
    | agentcluster/record/mvc.py        | snmpsim/record/mvc.py              |
    | agentcluster/record/sap.py        | snmpsim/record/sap.py              |
    | agentcluster/record/snmprec.py    | snmpsim/record/snmprec.py          |
    | agentcluster/record/walk.py       | snmpsim/record/walk.py             |
    o-----------------------------------o------------------------------------o

### List of files widely reworked

    o-----------------------------------o------------------------------------o
    |          agentcluster             |               snmpsim              |
    o-----------------------------------o------------------------------------o
    | agentcluster/confdir.py           | snmpsim/confdir.py                 |
    | agentcluster/database.py          | snmpsim/record/search/database.py  |
    | agentcluster/snapshot.py          | extract from script/snmpsimd.py    |
    o-----------------------------------o------------------------------------o

[snmpsim]: http://snmpsim.sourceforge.net/
