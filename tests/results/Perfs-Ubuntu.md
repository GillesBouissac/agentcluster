# Load test on Ubuntu

## Test conditions

## Hardware

Configuration:

| Component  | Characteristics  |
| ---------- | ---------------- |
| Processor  | AMD Phenom II X6 |
| Nb core    | 6                |
| RAM        | 4Go              |

## Parameters

The test was initialized with:

| Parameter            | Value   |
| -------------------- | -------:|
| Nb interfaces        | 20000   |
| Nb agents            |   100   |
| Nb address per agent |   200   |

MIB for test            tests/agents/linux/LinuxHost.snmpwalk (462 OIDs)

## Commands used to initialize the test:

    # Create ip interfaces
    sudo agentcluster-conf-generator.sh ip create 10.10.0.0 100 200 eth0
    
    # Create agent configurations
    agentcluster-conf-generator.sh agent create 10.10.0.0 100 200 33333 .agentcluster/data/ .agentcluster/template/
    
    # Start agentcluster
    agentclusterd.py -l console -a .agentcluster/data/

## Measures

### from host device

Initialisation

| Time (real)                            | Value           |
| -------------------------------------- | ---------------:|
| Create ip interfaces                   | __2m  0.854s__  |
| Create agent configurations            |    __20.561s__  |
| Start agentcluster (mibs not compiled) |        __32s__  |
| Start agentcluster (mibs compiled)     |         __4s__  |

Resource consumption per agent. Command used to obtain values:

     ps -eo rss,vsize,args --sort rss |grep agentcluster

| Indicator           | Min value  | Max value  |
| ------------------- | ----------:| ----------:|
| VSIZE:              | 216 116 Ko | 289 848 Ko |
| RSS:                |  15 244 Ko |  18 424 Ko |
| Compiled MIB (disk) |     824 Ko |            |

Resource consumption total

| Indicator           | Value             |
| ------------------- | -----------------:|
| VSIZE               | __29 200 916 Ko__ |
| RSS                 |  __1 705 508 Ko__ |
| Compiled MIB (disk) |     __82 400 Ko__ |

### Measures from local client

This test is started on the host device and therefore doesn't involve network.

    # snmp-walk one at a time (462 OIDs)
    time snmpwalk -v 2c -c public 10.10.25.10:33333 >/dev/null
Average: __655 ms__

    # snmp-get one at a time
    time snmpget  -v 2c -c public 10.10.25.10:33333 .1.3.6.1.2.1.1.1.0 >/dev/null
Average:  __25 ms__












