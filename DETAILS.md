# agentcluster in detail

Run a cluster of simulated SNMP agents on a single device.

This document is provided for more details about the architecture and configuration of __agentcluster__.

## Why another SNMP simulator ?
I needed a very simple free agent simulator to test a SNMPv3 monitoring software. During my research I've found [snmpsim][] which seemed to be exactly what I needed.
After some tests I realized that it was not possible to easily simulate multiple devices with different addresses, ports, arbitrary SNMPv3 contexNames and
engineIDs without code modifications.

I began modifying the code and finally reached some point where there were so much modifications that it wasn't __snmpsim__ any more.
So I decided to fork the project with another name and to make it public in case someone else have the same needs.

This tool is now very different from __snmpsim__ but it still have the same roots, it relies on the library [pysnmp][] and share the same MIB file formats.

## How it works
### Cluster monitoring

__agentcluster__ is made of a main process, the daemon `agentclusterd.py` which creates and monitors one child process `agent.py` (the _agent process_) for each simulated agent. 
You just starts the daemon and it will handle the _agent processes_ for you according to its configuration.

Configuration is specified by a list of directories (the _root dirs_) on startup.
The first thing it does is recursively browse each given _root dirs_ to search for files named `*.agent` (the _agent confs_).

Each _agent conf_ specify the agent parameters, for each _agent conf_, there is one _agent process_.

__agentcluster__ can be started before any configuration is available in its _root dirs_, it will find no agent configuration but this is not the end of the story.
A parameter given on the command line tells _agentcluster_ the configuration check frequency.

If no _agent conf_ was found on the first start, it will restart checking later. The check follow these rules:

* If a new _agent conf_ is discovered, a new _agent process_ is started to handle this configuration,
* If an _agent conf_ has been deleted, the associated _agent process_ is stopped.

An _agent conf_ file renaming is handled as two operations delete/create, so the old agent is stopped and a new one is started.
Changes in the content of an _agent conf_ are handled by agent monitoring below.

### Agent monitoring

When started, an _agent process_ is given its _agent conf_. It first parse it and start monitoring it to detect content change.
The Agent monitoring frequency is the same as the Cluster monitoring frequency. Change detection is based on content comparison, so a simple change in the date of the file has no effect.

The _agent conf_ contains references to MIB databases. database files are monitored as well during _agent conf_ monitoring.
When a new MIB database is discovered or an existing one is modified, the _agent process_ compiles it before using it.

The MIBs are compiled for maximum performances on reading. Each MIB is associated to one compiled database placed in the cache directory
given on startup.

The syntax of _agent confs_ allows to reference the same MIB file from multiple agents. But they will try to compile the same MIB to the same database file and finally this will not work.
The best solution to share MIBs between agents is to make symlinks (if the system allows it of course) because they allow to have different MIB file path for the same content.

## Configuration
### Host device configuration
Each _agent process_ can be bound to one or more couple `<@IP>:<port>` and even `unix socket` which are called __endpoints__.
You can use existing addresses on your _host device_ or you can add more ip addresses if you need to simulate a large number of agents.
This is known as multihoming and you can easily find a way to do it on the web as most operating system support it.

As an example I will show you how to do it on debian based systems. On such system, the network configuration is located in the file `/etc/network/interface`.
It will typically contain something like that:

    auto lo
    iface lo inet loopback
    
    auto eth0
    iface eth0 inet dhcp

To add a new specific address, just add this to this file:

    auto eth0:1
    iface eth0:1 inet static
        address 192.168.1.1
        netmask 255.255.255.0

This will declare a new IP interface started automatically on device start. It is possible to start/stop it with commands like:

    ifup eth0:1
    ifdown eth0:1

You can repeat this configuration for each address you need by incrementing the alias number `eth0:x`.
The list of started interfaces can be obtained with `ifconfig`.

### Agent configuration
When your _host device_ is configured, you can declare the agents.
The best way to do it is to create one sub-directory per agent in a _root dirs_ (remember, _root dirs_ are specified on command line).

Suppose we want to simulate a SNMPv3 agent that provides authentication and privacy. The agent is a router from TISTO company, we will call it "tisto".
In this example we use only one _root dir_

    <root dir>/tisto/tisto.agent

#### metadata
The _agent conf_ is a JSON format file. First we define the agent metadata:

    {
        "__comment__": [ "This file specifies the TISTO agent simulator" ],
        "name":     "tisto",
        "engineID": "0102030405060708090A",
        "active":   "True",

        "listen": {
            "udp": "127.0.0.1:33336"
        },

        "snmpv1":  { ... SNMPv1  protocol specific params ... },
        "snmpv2c": { ... SNMPv2c protocol specific params ... },
        "snmpv3":  { ... SNMPv3  protocol specific params ... }
    }

Parameters description (remember they are reloaded periodically):

* __name__: mandatory: agent identifier used for logging, there is no naming constraints,
* __engineID__: optional: this is the context engineID, only used for SNMPv3 agent if provided. Il not the SNMP stack will compute one itself,
* __active__: optional: boolean value (True/False) telling if the agent should be started or not. Useful to stop an agent without loosing its configuration.
Default to 'True' if not given,
* __listen__: mandatory: specifies the transport protocol _endpoints_ to use on this agent. 3 types of transport are supported: __udp__, __udp6__ and __unix__,
* __snmpv1__, __snmpv2c__, __snmpv3__: described on next chapters.

The _endpoint_ format depends on the type of transport:

* __udp__: the agent will listen on one or more "`<IPv4>:<port>`" _endpoints_:
   * If only one _endpoint_ is needed this simple syntax can be used: `"udp": "127.0.0.1:33336"`,
   * `<port>` is optional and defaults to 161 if not set,
   * Multiple _endpoints_ can be specified by providing a JSON list: `"udp": [ "127.0.0.1:33336", "192.192.0.1:33342" ]`,

* __udp6__: the agent will listen on one or more "`[<IPv6>]:<port>`" _endpoints_:
   * If only one _endpoint_ is needed this simple syntax can be used: `"udp6": "[::1]:33401"`,
   * `<port>` is optional and defaults to 161 if not set,
   * Multiple _endpoints_ can be specified by providing a JSON list: `"udp6":  [ "[::1]", "[::1]:33401" ]`.

* __unix__: the agent will listen on one or more "`unix socket`" _endpoints_:
   * This only work on *nix operating system,
   * _endpoints_ are pathnames to the unix socket,
   * Again one or more _endpoints_ can be specified.

A single agent can listen on multiple udp / udp6 / unix _endpoints_ simultaneously as in this example:

    "listen": {
        "udp":   "127.0.0.1",
        "udp6":  [ "[::1]", "[::1]:33401" ],
        "unix":  [ "/var/tisto", "/var/tisto2"]
    },

#### SNMPv1/SNMPv2
The syntax is the same for both protocols.
The parameters sections __snmpv1__ and __snmpv2c__ contains 2 subsections as in this example:

    "snmpv2c": {
        "users": [
            { "name": "v2public"},
            { "name": "v2linux"}
        ],
        "mib": {
            "v2public": "Linksys.snmpwalk",
            "v2linux":  "LinuxHost.snmpwalk"
        }
    }

* __users__: defines a list of credentials that must be given by the SNMP manager in order to be granted read rights:
   * With SNMPv1/v2c credentials are communities,
   * Communities only have one parameter: the community __name__,
   * You can provide multiple communities on one agent for one type of protocol.

* __mib__: list of MIB files accessible with the protocol:
   * Each MIB is named by one of the previous declared community,
   * If the same community is repeated multiple time, only the last MIB file is used, other are ignored,
   * The community is associated with the path of the file containing the MIB,
   * The path is relative to the _agent conf_ file.

#### SNMPv3
The root structure is similar to the one of SNMPv1/v2c:

    "snmpv3": {

        "users": [
            {
                "name":      "usr-snmp",
                "authAlgo":  "sha",
                "privAlgo":  "aes",
                "authPass":  "test-auth-password",
                "privPass":  "test-priv-password"
            }
        ],
        "mib": {
            "":                 "Solaris.snmpwalk",
            "Linksys":          "Linksys.snmpwalk",
            "Windows-snmpwalk": "WindowsXp.snmpwalk",
            "Windows-sapwalk":  "WindowsXp.sapwalk"
        }
    }

* __users__: defines a list of credentials that must be given by the SNMP manager in order to be granted read rights:
   * For SNMPv3, users have a name but also 4 security parameters discussed below,
   * You can provide multiple v3 users on the same agent.

* __mib__: list of MIB files accessible with the protocol:
   * Each MIB is named by an arbitrary contextName. The SNMP manager must provide the right contextName to access the required MIB,
   * The default context name is the empty string,
   * The contextName is associated with the path of the file containing the MIB,
   * If the same contextName is repeated multiple time, only the last MIB file is used, other are ignored,
   * The path is relatively to the _agent conf_ file.

SNMPv3 allow 3 security model for each user:

* _noAuthNoPriv_: No user authentication, no privacy (no encryption). Use following parameters to configure this model:
   * __authAlgo__: "none",
   * __privAlgo__: "none",
   * __authPass__: useless, ignored if given,
   * __privPass__: useless, ignored if given.

* _AuthNoPriv_: User is authenticated, no privacy (no encryption). Use following parameters to configure this model:
   * __authAlgo__: one of the list below,
   * __privAlgo__: "none",
   * __authPass__: authentication password: arbitrary string,
   * __privPass__: useless, ignored if given.

* _AuthPriv_: User is authenticated, privacy (encryption) is active. Use following parameters to configure this model:
   * __authAlgo__: one of the list below,
   * __privAlgo__: one of the list below,
   * __authPass__: authentication password: arbitrary string,
   * __privPass__: encryption password: arbitrary string.

* _NoAuthPriv_: This model is forbidden by protocol.

List of supported values for __authAlgo__:

    "md5",
    "sha",
    "none".

List of supported values for __privAlgo__:

    "des",
    "3des",
    "aes",
    "aes128",
    "aes192",
    "aes256",
    "none".

#### MIB files
There is 3 possibilities to obtain MIB files:

* You can build the MIB file by hand, this is a very long process but it is not impossible,
* Or you can get a MIB from anyone else that has already done the job and then adjust value to your test cases,
* Or you can a scan the whole MIB of a real agent and then adjust value to your test cases.

The first method only need your brain and the various RFCs or device specific MIB definitions.

In order to ease the second method, __agentcluster__ is compatible with the same formats as snmpsim:

* .snmprec:  snapshots obtained with [snmprec][] tool but without variation as variations are not implemented in __agentcluster__,
* .snmpwalk: snapshots obtained with [snmpwalk][] or [snmpbulkget][].

It is then possible to get MIB dumps from someone that already did the job or from another test.

For the third method, tools like [snmprec][], [snmpwalk][] or [snmpbulkget][] are provided and are directly usable.

Example of command lines to obtain snmpwalk MIB dumps:

    snmpwalk    -ObentU -v 3 -l authPriv -u usr-snmp -a SHA -x AES -A test-auth-password -X test-priv-password 192.168.0.1 .1 > mibdump.snmpwalk

or for SNMPv2c/SNMPv3 protocols:

    snmpbulkget -ObentU -v 3 -l authPriv -u usr-snmp -a SHA -x AES -A test-auth-password -X test-priv-password 192.168.0.1 .1 > mibdump.snmpwalk

After a first snapshot is obtained, you can edit values with a text editor an add comments:

* Empty lines are ignored,
* Lines beginning with `#` are ignored.



Voilà,  
I hope this tool will help, it helped me.


[python]: http://www.python.org/
[pypi]: https://pypi.python.org
[setuptools-pypi]: https://pypi.python.org/pypi/setuptools/0.6c11
[snmprec]: http://snmpsim.sourceforge.net/snapshotting.html
[snmpsim]: http://snmpsim.sourceforge.net/
[pysnmp]: http://pysnmp.sourceforge.net/
[argparse-pypi]: https://pypi.python.org/pypi/argparse/1.2.1
[pysnmp-pypi]: https://pypi.python.org/pypi/pysnmp/4.2.4
[pycrypto-pypi]: https://pypi.python.org/pypi/pycrypto/2.6
[pyasn1-pypi]: https://pypi.python.org/pypi/pyasn1/0.1.7
[netsnmp]: http://www.net-snmp.org/
[snmptrap]: http://www.net-snmp.org/docs/man/snmptrap.html
[snmpinform]: http://www.net-snmp.org/docs/man/snmptrap.html
[snmpwalk]: http://www.net-snmp.org/docs/man/snmpwalk.html
[snmpbulkget]: http://www.net-snmp.org/docs/man/snmpbulkget.html

