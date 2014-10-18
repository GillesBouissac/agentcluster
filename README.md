# agentcluster

Run a cluster of simulated SNMP agents on a single device.

## What it can do
If you are working on a SNMP monitoring software and you need a free tool to simulate a network of agents, then __agentcluster__ may help you.  

To simulate an agent (the _simulated agent_) hosted on a physical device (the _simulated device_) on a device hosting __agentcluster__ (the _host device_) you need to:

* Change the _host device_ network settings to simulate the _simulated device_. Most of the time declare the _simulated device_ IP address is enough,
* Build a MIB snapshot for the _simulated agent_,  
* Write a simple configuration file to declare you new _simulated agent_ with this MIB.

When launched, __agentcluster__ will act as if all the _simulated agents_ where online, it will answer to SNMP requests on agents: `get-request`, `get-next-request` and `get-bulk-request`.
This will allow you to see how your monitoring software behave with the MIB without the need to have a physical device in test bed.  

__agentcluster__ implements the 3 version of the protocol: SNMPv1, SNMPv2c or SNMPv3 (auth/priv).

## What it cannot do... yet
It cannot do a lot of things, but let's stay focused on SNMP agent simulators:

* __agentcluster__ is first designed for monitoring, it will not answer to SNMP `set-request` designed to change the content of a MIB,
* __agentcluster__ cannot send `trap` or `inform` notifications. The reason is that they can easily be simulated with [NET-SNMP][netsnmp] tools [snmptrap][] and [snmpinform][],
* __agentcluster__ doesn't have a MIB variation engine, the only way to simulate MIB values changes is to replace a MIB file with another one with different MIB values. 

## Installation
I will describe the installation instructions for debian based operating systems because I ran my tests on squeeze/wheezy/Ubuntu.
For other operating system you may adapt some steps and... I don't know if it works.

### Prerequisites
You will need python engine:

* [python][python] 2.6 or later but before 3.3.

And some additional libraries from [pypi][]:

* [setuptools][setuptools-pypi] 0.6c11 or later but before 1.0, 
* [argparse][argparse-pypi] 1.2.1 or later,
* [pycrypto][pycrypto-pypi] 2.6 or later, 
* [pyasn1][pyasn1-pypi] 0.1.7 or later.
* [pysnmp][pysnmp-pypi] 4.2.4 or later,

Most of the time, installation of these libraries is straightforward: uncompress the archives then in each uncompressed directory run:  

    python setup.py install

On a linux operating system you may prefix the command with sudo as the installation is available for all users,
After installation you can remove the uncompressed directory. Refer to each library page for more details. 

### Agentcluster

Installation from the github repository:

* Download or clone the __agentcluster__ repository.
* From the root of the repository run the command: `python setup.py install`

On a linux operating system you may prefix the command with sudo as the installation is available for all users.

An that's all, __agentcluster__ is now installed on you _host device_.

## Running agentcluster
### Usage

    $ agentclusterd.py --help
    usage: agentclusterd.py [-h] [-v] [-l {console,syslog}]
                            [-a <root-dir> [<root-dir> ...]] [-c <cache-dir>]
                            [-m <delay>]
    
    SNMP Cluster of agents version 0.2.0
    
    optional arguments:
      -h, --help            show this help message and exit
      -v, --version         show program's version number and exit
      -l {console,syslog}, --log-dest {console,syslog}
                            Log output, default to syslog if not set
      -a <root-dir> [<root-dir> ...], --agent-dir <root-dir> [<root-dir> ...]
                            Path to root directories that will be scanned for
                            *.agent files. See below for default values if not
                            set.
      -c <cache-dir>, --cache-dir <cache-dir>
                            Path to a directory that contain application cache.
                            default: /tmp/agentcluster
      -m <delay>, --monitoring <delay>
                            Time in second between 2 configuration check
    
    Default list of data directories if [-a|--agent-dir] is not set:
      - /home/gilles/.agentcluster/data
      - /etc/agentcluster/data
      - /usr/local/lib/python2.7/dist-packages/agentcluster/data

Please note that default values are designed for debian operating systems. You may be forced to change them on other operating systems.

### Note for debian/Ubuntu operating systems

If you ran the setup on a debian based host, you now have __agentcluster__ installed as a new service.
The service will be started on next reboot. You can start/stop/check it right after installation with these commands:

    sudo service agentcluster start
    sudo service agentcluster stop
    sudo service agentcluster status

If you don't want it to run as a service you can disable it with:

    sudo update-rc.d agentcluster remove

It can be enabled again later with:

    sudo update-rc.d agentcluster defaults

## Configuration
#### Use case
Suppose we want to simulate a SNMPv3 agent that provides authentication and privacy. The agent is a router from TISTO company, we will call it "tisto":

    <root dir>/tisto/tisto.agent

We want it to listen on IPv4 address 127.0.0.1 (localhost) and port 33336.

#### Configuration

The _agent conf_ is a JSON format file:

    {
        "__comment__": [ "This file specifies the TISTO agent simulator" ],
        "name":     "tisto",

        "listen": {
            "udp": "127.0.0.1:33336"
        },

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
                "":              "Tisto.snmpwalk"
            }
        }
    }

Now we need to build the MIB file Tisto.snmpwalk.

#### MIB files
We need a MIB file to simulate our Tisto router. The easier way is to connect the real device and dump its whole MIB.
The result could then be commented and adjusted to the test we want to run.

In this example we will use the faster way of dumping a MIB using [snmpwalk][] or [snmpbulkget][]

    snmpwalk    -ObentU -v 3 -l authPriv -u usr-snmp -a SHA -x AES -A test-auth-password -X test-priv-password 192.168.0.1 .1 > <root dir>/tisto/Tisto.snmpwalk

or for SNMPv2c/SNMPv3 protocols only:

    snmpbulkget -ObentU -v 3 -l authPriv -u usr-snmp -a SHA -x AES -A test-auth-password -X test-priv-password 192.168.0.1 .1 > <root dir>/tisto/Tisto.snmpwalk

Everything is now ready to simulate the device.

#### Run and check configuration
By default, agentcluster assumes that the _host device_ runs a syslog server listening on port 514.
Then every informational log will be send using syslog. The level of information send to syslog is INFO, it will not show
every configuration mistakes in syslog.

To check the configuration the idea is to run agentcluster in a console with the option to send log to this console:

    agentclusterd.py -a <root dir> -l console

You will have on the console the debug logs that will show you everything bad or not:

* Messages from the main process (the cluster) are prefixed with the string `agentclusterd.py[<pid>]`,
* Messages from agents are prefixed with the agent name and its pid: `<agentname>[<pid>]` agentname is the __name__ defined in configuration.

#### Check that everything works as expected
Now that configuration is ok the last step is to check that the agents work as expected.
The configuration specifies the agent to listen on endpoint 127.0.0.1:33336, so while __agentcluster__ is running, just run:

    snmpwalk    -ObentU -v 3 -l authPriv -u usr-snmp -a SHA -x AES -A test-auth-password -X test-priv-password 127.0.0.1:33336 .1

or for SNMPv2c/SNMPv3 protocols:

    snmpbulkget -ObentU -v 3 -l authPriv -u usr-snmp -a SHA -x AES -A test-auth-password -X test-priv-password 127.0.0.1:33336 .1

This should produce the same results as when dumping the MIB from the real device.

## Don't forget

* Please avoid binding __agentcluster__ on a public address or make it at your own risks, remember that this is a test tool,
* Here are some concrete test results: [test results](./tests/results),
* There are some configuration sample in the directory [tests](./tests) of __agentcluster__ repository,
* There is a more configuration details in the file [DETAILS.md](DETAILS.md) in the same repository,
* There is now a tool that can be used to generate simple agent configuration to simulate large networks [conf-generator](./tools/conf-generator).

## License
__agentcluster__ software is free and open-source. It's being distributed under a liberal BSD-style [license](LICENSE.md).


[python]: http://www.python.org/
[pypi]: https://pypi.python.org
[setuptools-pypi]: https://pypi.python.org/pypi/setuptools/0.6c11
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

