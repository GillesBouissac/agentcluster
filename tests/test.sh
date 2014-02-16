#!/usr/bin/env bash

set -u

echo "Start agentcluster in background"
../scripts/agentclusterd.py -a ./ -m 10 &
AGPID=$!

echo "Wait 2 secs for agentcluster readiness"
sleep 2

exec_test(){
    eval $1 | {
        while read LINE; do
            echo "        $LINE"
        done
    } || {
            echo ""
            echo "TEST ERROR"
            echo ""
            kill -9 $AGPID
            exit 1
    }
}

echo "Get some data from agent 'linux'"

echo "  snmp V1"
echo "    GET"
echo "      community: public"
exec_test "snmpget -ObentU -v 1 -c public localhost:33336 .1.3.6.1.2.1.2.2.1.2.2"
echo "    WALK"
echo "      community: public"
exec_test "snmpwalk -ObentU -v 1 -c public localhost:33336 .1.3.6.1.2.1.4.20"

echo "  snmp V2c"
echo "    GET"
echo "      community: v2public"
exec_test "snmpget -ObentU -v 2c -c v2public localhost:33336 .1.3.6.1.2.1.1.4.0"
echo "      community: v2linux"
exec_test "snmpget -ObentU -v 2c -c v2linux  localhost:33336 .1.3.6.1.2.1.1.4.0"
echo "    WALK"
echo "      community: v2public"
exec_test "snmpwalk -ObentU -v 2c -c v2public localhost:33336 .1.3.6.1.2.1.1"
echo "      community: v2linux"
exec_test "snmpwalk -ObentU -v 2c -c v2linux  localhost:33336 .1.3.6.1.2.1.4.20"
echo "    BULK"
echo "      community: v2public"
exec_test "snmpbulkget -ObentU -v 2c -c v2public localhost:33336 .1.3.6.1.2.1.1"
echo "      community: v2linux"
exec_test "snmpbulkget -ObentU -v 2c -c v2linux  localhost:33336 .1.3.6.1.2.1.4.20"

echo ""
echo "Get some data from agent 'windows'"

echo "  snmp V3"
echo "    GET"
echo "      context: default"
exec_test "snmpget -ObentU -v 3 -l authPriv -u usr-snmp -a SHA -x AES -A test-auth-password -X test-priv-password localhost:33333 .1.3.6.1.2.1.2.2.1.2.1"
echo "      context: snmpwalk"
exec_test "snmpget -ObentU -n snmpwalk -v 3 -l authPriv -u usr-snmp -a SHA -x AES -A test-auth-password -X test-priv-password localhost:33333 .1.3.6.1.2.1.2.2.1.2.1"
echo "      context: snmprec"
exec_test "snmpget -ObentU -n snmprec -v 3 -l authPriv -u usr-snmp -a SHA -x AES -A test-auth-password -X test-priv-password localhost:33333 .1.3.6.1.2.1.2.2.1.2.1"
echo "    WALK"
echo "      context: default"
exec_test "snmpwalk -ObentU -v 3 -l authPriv -u usr-snmp -a SHA -x AES -A test-auth-password -X test-priv-password localhost:33333 .1.3.6.1.2.1.6.13.1.4.127"
echo "      context: snmpwalk"
exec_test "snmpwalk -ObentU -n snmpwalk -v 3 -l authPriv -u usr-snmp -a SHA -x AES -A test-auth-password -X test-priv-password localhost:33333 .1.3.6.1.2.1.6.13.1.4.127"
echo "      context: snmprec"
exec_test "snmpwalk -ObentU -n snmprec -v 3 -l authPriv -u usr-snmp -a SHA -x AES -A test-auth-password -X test-priv-password localhost:33333 .1.3.6.1.2.1.6.13.1.4.127"
echo "    BULK"
echo "      context: default"
exec_test "snmpbulkget -ObentU -v 3 -l authPriv -u usr-snmp -a SHA -x AES -A test-auth-password -X test-priv-password localhost:33333 .1.3.6.1.2.1.6.13.1.4.127"
echo "      context: snmpwalk"
exec_test "snmpbulkget -ObentU -n snmpwalk -v 3 -l authPriv -u usr-snmp -a SHA -x AES -A test-auth-password -X test-priv-password localhost:33333 .1.3.6.1.2.1.6.13.1.4.127"
echo "      context: snmprec"
exec_test "snmpbulkget -ObentU -n snmprec -v 3 -l authPriv -u usr-snmp -a SHA -x AES -A test-auth-password -X test-priv-password localhost:33333 .1.3.6.1.2.1.6.13.1.4.127"

echo ""
echo "Get some data from agent 'Mixed device'"

echo "  snmp V2c"
echo "    GET"
echo "      community: v2c"
exec_test "snmpget -ObentU -v 2c -c v2c localhost:33401 .1.3.6.1.2.1.1.4.0"
echo "      community: public"
exec_test "snmpget -ObentU -v 2c -c public  localhost:33401 .1.3.6.1.2.1.1.1.0"
echo "    WALK"
echo "      community: v2c"
exec_test "snmpwalk -ObentU -v 2c -c v2c localhost:33401 .1.3.6.1.2.1.1"
echo "      community: public"
exec_test "snmpwalk -ObentU -v 2c -c public  localhost:33401 .1.3.6.1.2.1.1"
echo "    BULK"
echo "      community: v2c"
exec_test "snmpbulkget -ObentU -v 2c -c v2c localhost:33401 .1.3.6.1.2.1.1"
echo "      community: public"
exec_test "snmpbulkget -ObentU -v 2c -c public  localhost:33401 .1.3.6.1.2.1.1"

echo "  snmp V3"
echo "    GET"
echo "      context: default"
exec_test "snmpget -ObentU -v 3 -E 0102030405060708090A -l authPriv -u usr-snmp -a SHA -x AES -A test-auth-password -X test-priv-password localhost:33401 .1.3.6.1.2.1.1.4.0"
echo "      context: Linksys"
exec_test "snmpget -ObentU -n Linksys -v 3 -l authPriv -u usr-snmp -a SHA -x AES -A test-auth-password -X test-priv-password localhost:33401 .1.3.6.1.2.1.1.4.0"
echo "      context: Windows-snmpwalk"
exec_test "snmpget -ObentU -n Windows-snmpwalk -v 3 -l authPriv -u usr-snmp -a SHA -x AES -A test-auth-password -X test-priv-password localhost:33401 .1.3.6.1.2.1.2.2.1.2.1"
echo "      context: Windows-sapwalk"
exec_test "snmpget -ObentU -n Windows-sapwalk -v 3 -l authPriv -u usr-snmp -a SHA -x AES -A test-auth-password -X test-priv-password localhost:33401 .1.3.6.1.2.1.2.2.1.2.1"
echo "    WALK"
echo "      context: default"
exec_test "snmpwalk -ObentU -v 3 -l authPriv -u usr-snmp -a SHA -x AES -A test-auth-password -X test-priv-password localhost:33401 .1.3.6.1.2.1.1"
echo "      context: Linksys"
exec_test "snmpwalk -ObentU -n Linksys -v 3 -l authPriv -u usr-snmp -a SHA -x AES -A test-auth-password -X test-priv-password localhost:33401 .1.3.6.1.2.1.1"
echo "      context: Windows-snmpwalk"
exec_test "snmpwalk -ObentU -n Windows-snmpwalk -v 3 -l authPriv -u usr-snmp -a SHA -x AES -A test-auth-password -X test-priv-password localhost:33401 .1.3.6.1.2.1.6.13.1.4.127"
echo "      context: Windows-sapwalk"
exec_test "snmpwalk -ObentU -n Windows-sapwalk -v 3 -l authPriv -u usr-snmp -a SHA -x AES -A test-auth-password -X test-priv-password localhost:33401 .1.3.6.1.2.1.6.13.1.4.127"
echo "    BULK"
echo "      context: default"
exec_test "snmpbulkget -ObentU -v 3 -l authPriv -u usr-snmp -a SHA -x AES -A test-auth-password -X test-priv-password localhost:33401 .1.3.6.1.2.1.1"
echo "      context: Linksys"
exec_test "snmpbulkget -ObentU -n Linksys -v 3 -l authPriv -u usr-snmp -a SHA -x AES -A test-auth-password -X test-priv-password localhost:33401 .1.3.6.1.2.1.1"
echo "      context: Windows-snmpwalk"
exec_test "snmpbulkget -ObentU -n Windows-snmpwalk -v 3 -l authPriv -u usr-snmp -a SHA -x AES -A test-auth-password -X test-priv-password localhost:33401 .1.3.6.1.2.1.6.13.1.4.127"
echo "      context: Windows-sapwalk"
exec_test "snmpbulkget -ObentU -n Windows-sapwalk -v 3 -l authPriv -u usr-snmp -a SHA -x AES -A test-auth-password -X test-priv-password localhost:33401 .1.3.6.1.2.1.6.13.1.4.127"

echo "Stop agentcluster"
kill -15 $AGPID >/dev/null 2>&1

