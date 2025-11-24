#!/usr/bin/env bash
# shellcheck disable=2120

#  Script: hhs-network.bash
# Created: Oct 5, 2019
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs/homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2025, HomeSetup team

# !NOTICE: Do not change this file. To customize your functions edit the file ~/.functions

# Requires ifconfig to work.
if __hhs_has ifconfig; then

  # @function: Display a list of active network interfaces.
  function __hhs_active_ifaces() {

    local all_ifaces=() if_name if_flags if_mtu if_list

    if [[ "$1" == "-h" || "$1" == "--help" ]]; then
      echo "usage: ${FUNCNAME[0]} [-flat]"
      return 1
    fi

    IFS=$'\n' read -r -d '' -a all_ifaces < <(ifconfig -a | grep '^[a-z0-9]*: ')
    IFS="${OLDIFS}"

    if [[ ${#all_ifaces[@]} == 0 ]]; then
      echo "${ORANGE}No active interfaces found !${NC}"
      return 1
    elif [[ ${#all_ifaces[@]} -gt 0 && ${*} =~ -flat ]]; then
      for iface in "${all_ifaces[@]}"; do
        if_name=$(awk '{ print $1 }' <<<"${iface%%:*}")
        if_list="${if_name} ${if_list}"
      done
      echo "${if_list}"
    else
      echo ' '
      echo "${YELLOW}Listing all network interfaces:${NC}"
      echo ' '
      for iface in "${all_ifaces[@]}"; do
        if_name=$(awk '{ print $1 }' <<<"${iface%%:*}")
        if_mtu=$(awk '{ print $4 }' <<<"${iface}")
        if_flags=$(awk '{ print $2 }' <<<"${iface}")
        printf "${HHS_HIGHLIGHT_COLOR}%-12s${NC}\tMTU=%-8d\t%-s\n" "${if_name}" "${if_mtu}" "${if_flags}"
      done
      echo ' '
    fi

    return 0
  }

  if __hhs_has route; then

    # @function: Display the associated machine IP of the given kind.
    # @param $1 [Opt] : The kind of IP to get.
    function __hhs_ip() {

      local ret_val=1 ip_kind if_name if_list if_ip if_prefix ip_srv_url='ipinfo.io'

      if [[ "$1" == "-h" || "$1" == "--help" ]]; then
        echo "usage: ${FUNCNAME[0]} [kind]"
        echo ''
        echo '    Arguments:'
        echo '      type : The kind of IP to get. One of [all|local|external|gateway|vpn]'
        echo ''
        echo '    Types:'
        echo '           all : Get all network IPv4'
        echo '         local : Get your local network IPv4'
        echo '      external : Get your external network IPv4'
        echo '       gateway : Get the gateway IPv4'
        echo '           vpn : Get your IPv4 assigned by your VPN server'
        echo ''
        echo '  Notes: '
        echo '    - If no kind is specified, all assigned IPv4s will be retrieved'
        return 1
      else
        ip_kind=${1:-all}
        if [[ ${ip_kind} =~ all|external ]]; then
          if_ip="$(curl -s --fail -m 3 "${ip_srv_url}" 2>/dev/null | grep -E '^ *"ip":' | awk '{print $2}')"
          [[ -n "${if_ip}" ]] && printf "%-10s: %-13s\n" "External" "${if_ip//[\",]/}"
        fi
        if [[ ${ip_kind} =~ all|gateway ]]; then
          [[ "Darwin" == "${HHS_MY_OS}" ]] && if_ip="$(route get default 2>/dev/null | grep 'gateway' | awk '{print $2}')"
          [[ "Linux" == "${HHS_MY_OS}" ]] && if_ip="$(route -n 2>/dev/null | grep 'UG[ \t]' | awk '{print $2}')"
          [[ -n "${if_ip}" ]] && printf "%-10s: %-13s\n" "Gateway" "${if_ip}"
        fi
        if_name='all|vpn|local|(lo|eth|en|wl|utun|tun)[a-z0-9]+'
        if [[ ${ip_kind} =~ ${if_name} ]]; then
          read -r -d '' -a if_list < <(__hhs_active_ifaces -flat 2>/dev/null)
          [[ "vpn" == "${ip_kind}" ]] && if_prefix='(utun|tun)[a-z0-9]+'
          [[ "local" == "${ip_kind}" ]] && if_prefix='(eth|en|wl)[a-z0-9]+'
          [[ -z "${if_prefix}" ]] && if_prefix="${ip_kind}"
          for iface in "${if_list[@]}"; do
            if [[ "all" == "${ip_kind}" || ${iface} =~ ${if_prefix} ]]; then
              if_ip="$(ifconfig "${iface}" 2>/dev/null | grep -E "inet " | awk '{print $2}')"
              [[ -n "${if_ip}" ]] && printf "%-10s: %-13s\n" "${iface}" "${if_ip}"
            fi
          done
          ret_val=0
        fi
      fi

      return ${ret_val}
    }

  fi

fi

# @function: Retrieve information about the specified IP.
# @param $1 [Req] : The IP to get information about.
function __hhs_ip_info() {

  local ipinfo ip_srv_url="http://ip-api.com/json/${1}"

  if [[ "$#" -le 0 || "$1" == "-h" || "$1" == "--help" ]]; then
    echo "usage: ${FUNCNAME[0]} <IPv4_address>"
    return 1
  else
    ipinfo="$(curl -s --fail -m 3 "${ip_srv_url}" 2>/dev/null)"
    status=$?
    if [[ $status -ne 0 ]]; then
      __hhs_errcho "${APP_NAME}" "Request to ${ip_srv_url} failed (exit=$status)."
    else
      if [[ -n "${ipinfo}" ]]; then
        __hhs_json_print "${ipinfo}"
      else
        echo "${ORANGE}No information found for IP ${1}.${NC}"
      fi
      return 0
    fi
  fi

  return 1
}

# Requires host to work.
if __hhs_has host; then

  # @function: Lookup DNS payload to determine the IP address.
  # @param $1 [Req] : The domain name to lookup.
  function __hhs_ip_lookup() {

    if [[ "$#" -le 0 || "$1" == "-h" || "$1" == "--help" ]]; then
      echo "usage: ${FUNCNAME[0]} <domain_name>"
      return 1
    else
      \host "${1}"
    fi

    return 0
  }

fi

# Requires dig to work.
if __hhs_has dig; then

  # @function: Resolve domain names associated with the specified IP.
  # @param $1 [Req] : The IP address to resolve.
  function __hhs_ip_resolve() {

    if [[ "$1" == "-h" || "$1" == "--help" || "$#" -ne 1 ]]; then
      echo "usage: ${FUNCNAME[0]} <IPv4_address>"
      return 1
    fi
    \dig +short -x "$1"

    return $?
  }

fi

# Requires netstat to work.
if __hhs_has netstat; then

  # @function: Check the state of local port(s).
  # @param $1 [Req] : The port number regex.
  # @param $2 [Opt] : The port state to match.
  function __hhs_port_check() {

    local states state port protocol ret_val

    states='CLOSED|LISTEN|SYN_SENT|SYN_RCVD|ESTABLISHED|CLOSE_WAIT|LAST_ACK|FIN_WAIT_1|FIN_WAIT_2|CLOSING|TIME_WAIT'
    port=${1:0:5}
    port=$(printf "%-.5s" "${port}")
    state=$(tr '[:lower:]' '[:upper:]' <<< "${2}")
    state="${state//\./}"
    protocol="${3//\./}"

    if [[ "$#" -le 0 || "$1" == "-h" || "$1" == "--help" ]]; then
      echo "usage: ${FUNCNAME[0]} <port_number> [port_state] [protocol]"
      echo ''
      echo '  Notes: '
      echo '    - Protocol: One of [tcp udp]'
      echo "    - States: One of [${states//|,, /}]"
      echo '    - Wildcards: Use dots (.) as a wildcard. E.g: 80.. will match 80[0-9][0-9]'
      return 1
    elif [[ -z "${state}" || "${state}" =~ ^(${states})$ ]] && [[ -z "${protocol}" ||  ${protocol} =~ ^(udp|tcp)$ ]]; then
      protocol="${protocol:-^(tcp|udp)}"
      echo -e "\n${YELLOW}Showing ports  Proto: [${protocol}] Number: [${port//\./*}] State: [${state:-*}] ${NC}"
      echo -e "\nProto Recv-Q Send-Q  Local Address          Foreign Address        State\n"
      \netstat -an \
        | __hhs_highlight "${protocol}[0-9]*" \
        | __hhs_highlight "[.:]${port} " \
        | __hhs_highlight "${state}"
      ret_val=$?
    else
      __hhs_errcho "${FUNCNAME[0]}" "Invalid state or protocol ($2 $3)!"
    fi

    echo ''

    return $ret_val
  }

fi
