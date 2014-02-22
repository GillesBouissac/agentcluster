#!/bin/bash
#
# Copyright (c) 2014, Gilles Bouissac <agentcluster@gmail.com>
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
#   * Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation
#     and/or other materials provided with the distribution.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE
# GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

set -e
set -u

TEMPLATE_AGENT='
{
    "name": 	"${agent-name}",
    "active": 	"True",
    "listen": {
        "udp": [
            ${endpoints}
        ]
    },
    "snmpv2c": {
        "users": [
            { "name": "public"}
        ],
        "mib": {
            "public": "${agent-mib}"
        }
    }
}
'

function ipv4_address_to_string() {
    remainder=$1

    digit_1=$(( remainder >> 24 ))
    remainder=$(( remainder - (digit_1 << 24) ))
    digit_2=$(( remainder >> 16 ))
    remainder=$(( remainder - (digit_2 << 16) ))
    digit_3=$(( remainder >> 8 ))
    remainder=$(( remainder - (digit_3 << 8) ))
    digit_4=$(( remainder >> 0 ))
    remainder=$(( remainder - (digit_4 << 0) ))

    echo "${digit_1}.${digit_2}.${digit_3}.${digit_4}"
}

function ipv4_address_from_string() {
    ip_string=$1

    digit_1=$(echo $ip_string |sed -E "s/^([0-9]+)[.]([0-9]+)[.]([0-9]+)[.]([0-9]+)$/\1/")
    digit_2=$(echo $ip_string |sed -E "s/^([0-9]+)[.]([0-9]+)[.]([0-9]+)[.]([0-9]+)$/\2/")
    digit_3=$(echo $ip_string |sed -E "s/^([0-9]+)[.]([0-9]+)[.]([0-9]+)[.]([0-9]+)$/\3/")
    digit_4=$(echo $ip_string |sed -E "s/^([0-9]+)[.]([0-9]+)[.]([0-9]+)[.]([0-9]+)$/\4/")

    [ "$digit_1" != "$ip_string" ] || { echo "ERROR: Invalid IPv4 address '"$ip_string"'" >&2; exit 1; }
    [ "$digit_2" != "$ip_string" ] || { echo "ERROR: Invalid IPv4 address '"$ip_string"'" >&2; exit 1; }
    [ "$digit_3" != "$ip_string" ] || { echo "ERROR: Invalid IPv4 address '"$ip_string"'" >&2; exit 1; }
    [ "$digit_4" != "$ip_string" ] || { echo "ERROR: Invalid IPv4 address '"$ip_string"'" >&2; exit 1; }

    echo $(( (digit_1 << 24) | (digit_2 << 16) | (digit_3 << 8) | (digit_4 << 0) ))
}

function syntax() {
    {
        if [ $# -eq 1 ]; then
            echo ""
            echo "ERROR: $1"
        fi
        echo ""
        echo "SYNTAX: $(basename $0) <object> <action> <params>"
        echo ""
        echo "  objects:"
        echo "      ip    : actions are executed immediately on IP addresses, IP configuration is lost on reboot."
        echo "      agent : actions are executed on agentcluster configuration files."
        echo ""
        echo "  objects specific syntaxes:"
        echo "      $(basename $0) ip    create|delete <first_address> <nb_agent> <nb_bind> <device>"
        echo "      $(basename $0) agent create|delete <first_address> <nb_agent> <nb_bind> <port> <agent-root-dir> <mibs-dir>"
        echo ""
        echo "  create|delete:    action: create configuration or delete it"
        echo "  <first_address>:  first IPv4 address to create/delete. There will be <nb_agent>x<nb_bind> addresses starting from this one"
        echo "  <nb_agent>:       nb agents to configure"
        echo "  <nb_bind>:        nb addresses per agent"
        echo "  <device>:         network device on which IP aliases will be added (ex:eth0)"
        echo "  <port>:           the port to bind on every agent (ex:161)"
        echo "  <agent-root-dir>: the directory where agents configurations will be created/deleted"
        echo "  <mib-dir>:        the directory containing mibs files for future agents"
        echo ""
    }>&2
    exit 1
}

function action_create_ip_addresses () {
    address=$first_address
    cpt=0
    while [ $cpt -lt $nb_addresses ]; do
        cpt=$(( cpt + 1 ))
        percent=$(( (100*cpt)/nb_addresses ))

        agent_address=$(ipv4_address_to_string $address)
        printf "\r\033[KCreating address No %6d: %-50s[%3d%%]" "$cpt" "${agent_address}" "$percent"
        ip addr add ${agent_address}/24 dev "$device" label "${device}:${cpt}" || true
        address=$(( address + 1 ))
    done
    echo ""
}
function action_delete_ip_addresses () {
    address=$first_address
    cpt=0
    while [ $cpt -lt $nb_addresses ]; do
        cpt=$(( cpt + 1 ))
        percent=$(( (100*cpt)/nb_addresses ))

        agent_address=$(ipv4_address_to_string $address)
        printf "\r\033[KDeleting address No %6d: %-50s[%3d%%]" "$cpt" "${agent_address}" "$percent"
        ip addr del ${agent_address}/24 dev "$device" label "${device}:${cpt}" || true
        address=$(( address + 1 ))
    done
    echo ""
}

NETIF_CONF_FILE="/etc/network/interfaces"
NETIF_TAG_START="##AGENTCLUSTER-ADDRESSES-START"
NETIF_TAG_END="##AGENTCLUSTER-ADDRESSES-END"
function action_create_netifs () {
    #
    # This function works but is not published because adding a lot of
    #   interfaces can drastically slows down the host device boot
    #
    echo "Create agentcluster configuration in ${NETIF_CONF_FILE}"
    address=$first_address
    {
        echo "${NETIF_TAG_START}"
    } >> "${NETIF_CONF_FILE}"
    cpt=0
    while [ $cpt -lt $nb_addresses ]; do
        cpt=$(( cpt + 1 ))
        percent=$(( (100*cpt)/nb_addresses ))

        agent_address=$(ipv4_address_to_string $address)
        printf "\r\033[KCreating address No %6d: %-50s[%3d%%]" "$cpt" "${agent_address}" "$percent"
        {
            echo "auto ${device}:${cpt}"
            echo "iface ${device}:${cpt} inet static"
            echo "    address ${agent_address}"
            echo "    netmask 255.255.255.0"
        } >> "${NETIF_CONF_FILE}"
        address=$(( address + 1 ))
    done
    {
        echo "${NETIF_TAG_END}"
    } >> "${NETIF_CONF_FILE}"
    echo ""
}
function action_delete_netifs () {
    echo "Remove agentcluster configuration from ${NETIF_CONF_FILE}"
    sed -i "/${NETIF_TAG_START}/,/${NETIF_TAG_END}/d" "${NETIF_CONF_FILE}"
}

function action_create_agents () {
    address=$first_address
    mib_files_count=${#mib_files[@]}
    cpt_mib=0
    cpt=0
    while [ $cpt -lt $nb_agents ]; do
        cpt=$(( cpt + 1 ))
        percent=$(( (100*cpt)/nb_agents ))

        mib_file=${mib_files[$cpt_mib]}
        mib_file_basename=$(basename "${mib_file}")
        cpt_mib=$(( cpt_mib + 1 ))
        [ $cpt_mib -lt $mib_files_count ] || cpt_mib=0

        agent_name="agent-${cpt}"
        printf "\r\033[KCreating agent %-10s MIB:%-50s[%3d%%]" "${agent_name}" "${mib_file_basename}" "$percent"

        agent_dir="${root_dir}/${agent_name}"
        mkdir -p "${agent_dir}" 1>/dev/null

        agent_conf="${agent_dir}/agent.agent"
        agent_mib="${agent_dir}/${mib_file_basename}"
        echo "${TEMPLATE_AGENT}" > "${agent_conf}"
        ln -s "${mib_file}" "${agent_mib}" 1>/dev/null
        sed -i "s/\${agent-mib}/${mib_file_basename}/g" "${agent_conf}" 1>/dev/null
        sed -i "s/\${agent-name}/${agent_name}/g"       "${agent_conf}" 1>/dev/null

        endpoints=""
        cpt_add=0
        while [ $cpt_add -lt $nb_bind ]; do
            cpt_add=$(( cpt_add + 1 ))

            agent_address=$(ipv4_address_to_string $address)
            endpoint="\"$agent_address:$port\""
            if [ "$endpoints" = "" ]; then
                endpoints="$endpoint"
            else
                endpoints="$endpoints, $endpoint"
            fi
            address=$(( address + 1 ))
        done
        sed -i "s/\${endpoints}/${endpoints}/g" "${agent_conf}"
    done
    echo ""
}
function action_delete_agents () {
    echo "Deleting agents configurations from ${root_dir}"
    rm -r "${root_dir}"/* || true
}

if [ $# -le 2 ]; then
    syntax
fi

action=""
object=""
first_address=""
nb_agent=0
nb_bind=0
nb_addresses=0

# PARAM 1
case "$1" in
    ip)
        object=$1
        nb_params=4
        ;;
    agent)
        object=$1
        nb_params=6
        ;;
    *)
        syntax "Bad object name $1"
        ;;
esac
shift

# PARAM 2
case "$1" in
    delete|create)
        action=$1
        ;;
    *)
        syntax "Bad action name $1"
        ;;
esac
shift

if [ $nb_params -ne $# ]; then
    syntax "Bad number of params: $# while $nb_params expected"
fi

if [ $nb_params -gt 0 ]; then
    # PARAM 3
    first_address=$(ipv4_address_from_string "$1")
    shift
    nb_params=$((nb_params-1))
fi

if [ $nb_params -gt 0 ]; then
    # PARAM 4
    nb_agents=$1
    let ${nb_agents} || syntax "Bad number for nb_agent: \'$nb_agents\'"
    shift
    nb_params=$((nb_params-1))
fi

if [ $nb_params -gt 0 ]; then
    # PARAM 5
    nb_bind=$1
    let ${nb_bind} || syntax "Bad number for nb_bind: \'$nb_bind\'"
    shift
    nb_params=$((nb_params-1))
fi
nb_addresses=$(( nb_agents * nb_bind ))


case "$object" in

    ip)
        [ $(id -u) -eq 0 ] || {
            echo "This command only works with sudo"
            exit 2
        }
        device=""
        if [ $nb_params -gt 0 ]; then
            # PARAM 6
            device=$1
            [ -r "/sys/class/net/$device" ] || syntax "Bad network device given: '"$device"\'"
            shift
            nb_params=$((nb_params-1))
        fi
        case "$action" in
            create)
                action_create_ip_addresses
            ;;
            delete)
                action_delete_ip_addresses
            ;;
        esac
        ;;

    agent)
        port=""
        root_dir=""
        mib_dir=""
        mib_files=("")
        if [ $nb_params -gt 0 ]; then
            # PARAM 6
            port=$1
            let ${port} || syntax "Bad number for port: \'$port\'"
            shift
            nb_params=$((nb_params-1))
        fi
        if [ $nb_params -gt 0 ]; then
            # PARAM 7
            [ -d "$1" ] || syntax "agent-root-dir '"$1"' doesn't exist"
            pushd "$1" >/dev/null
            root_dir="$PWD"
            popd >/dev/null
            [ "$root_dir" != "/" ] && [ "$root_dir" != "//" ] || syntax "agent-root-dir cannot be '/' or '//' "
            shift
            nb_params=$((nb_params-1))
        fi
        if [ $nb_params -gt 0 ]; then
            # PARAM 8
            [ -d "$1" ] || syntax "mib-dir '"$1"' doesn't exist"
            pushd "$1" >/dev/null
            mib_dir="$PWD"
            popd >/dev/null
            shift
            nb_params=$((nb_params-1))
            mib_files=($mib_dir/*)
        fi
        case "$action" in
            create)
                action_create_agents
            ;;
            delete)
                action_delete_agents
            ;;
        esac
        ;;

esac

exit 0

