#!/usr/bin/env bash
# shellcheck disable=SC2009,SC1090

#  Script: hhs-sys-utils.bash
# Created: Oct 5, 2019
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs/homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2025, HomeSetup team

# !NOTICE: Do not change this file. To customize your functions edit the file ~/.functions

# @function: Display relevant system information.
function __hhs_sysinfo() {
  local username containers if_name if_ip all_ips all_users=() OLDIFS

  if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    echo "usage: ${FUNCNAME[0]}"
    return 1
  fi

  username=$(whoami)
  echo ""
  echo -e "${ORANGE}-=- System Information -=-"
  echo ""
  echo -e "${GREEN}User:${HHS_HIGHLIGHT_COLOR}"
  echo -e "${WHITE}  Username..... : ${HHS_HIGHLIGHT_COLOR}${username}"
  echo -e "${WHITE}  Group........ : ${HHS_HIGHLIGHT_COLOR}$(groups "${username}" | awk '{print $1}')"
  echo -e "${WHITE}  UID.......... : ${HHS_HIGHLIGHT_COLOR}$(id -u "${username}")"
  echo -e "${WHITE}  GID.......... : ${HHS_HIGHLIGHT_COLOR}$(id -g "${username}")"
  echo ""
  echo -e "${GREEN}System:${HHS_HIGHLIGHT_COLOR}"
  echo -e "${WHITE}  OS........... :${HHS_HIGHLIGHT_COLOR} ${HHS_MY_OS:-$(uname)} $(uname -pmr)"
  if __hhs_has sw_vers; then
    echo -e "${WHITE}  Software..... :${HHS_HIGHLIGHT_COLOR} $(sw_vers | awk '{print $2" "$3}' | tr '\n' ' '):: $(__hhs_get_codename)"
  fi
  if __hhs_has uptime; then
    echo -e "${WHITE}  Up-Time...... :${HHS_HIGHLIGHT_COLOR} $(uptime | cut -d ',' -f1)"
  fi
  if __hhs_has ps; then
    echo -e "${WHITE}  MEM Usage.... :${HHS_HIGHLIGHT_COLOR} ~$(ps -A -o %mem | awk '{s+=$1} END {print s "%"}')"
    echo -e "${WHITE}  CPU Usage.... :${HHS_HIGHLIGHT_COLOR} ~$(ps -A -o %cpu | awk '{s+=$1} END {print s "%"}')"
  fi

  if __hhs_has __hhs_ip; then
    echo ""
    echo -e "${GREEN}Network:"
    OLDIFS=$IFS
    IFS=$'\n'
    all_ips=$(__hhs_ip | sort)
    printf "${WHITE}  Hostname..... : ${HHS_HIGHLIGHT_COLOR}%s\n" "$(hostname)"
    for next in ${all_ips}; do
      if_name="${next%%:*}"
      if_ip="${next##*:}"
      printf "${WHITE}  %-13s :${HHS_HIGHLIGHT_COLOR}%s\n" "IP-${if_name// /.}" "${if_ip}"
    done
    IFS=$OLDIFS
  fi

  OLDIFS=$IFS
  IFS=$'\n'
  while IFS= read -r line; do all_users+=("$line"); done < <(who -H)
  if [[ ${#all_users[@]} -gt 0 ]]; then
    echo -e "\n${GREEN}Currently Logged in Users:${WHITE}"
    for next in "${all_users[@]}"; do
      echo "  ${next} ${HHS_HIGHLIGHT_COLOR}"
    done
  fi
  IFS=$OLDIFS

  echo ""
  echo -e "${GREEN}Storage:${WHITE}"
  printf "  %-15s %-7s %-7s %-7s %-5s\n" "Disk" "Size" "Used" "Free" "Cap${HHS_HIGHLIGHT_COLOR}"
  if [[ "$(uname)" == "Darwin" ]]; then
    df -h | grep "^/dev/disk" | awk '{printf("  %-15s %-7s %-7s %-7s %-5s\n", $1, $2, $3, $4, $5)}'
  else
    df -h | grep -E "^/dev/|^.*fs" | awk '{printf("  %-15s %-7s %-7s %-7s %-5s\n", $1, $2, $3, $4, $5)}'
  fi

  if __hhs_has docker && __hhs_has __hhs_docker_ps; then
    OLDIFS=$IFS
    IFS=$'\n'
    read -r -d '' -a containers < <(__hhs_docker_ps -a && printf '\0')
    if [[ ${#containers[@]} -gt 0 && $(__hhs_docker_count) -ge 1 ]]; then
      echo -e "\n${GREEN}Online Docker Containers:${WHITE}"
      for next in "${containers[@]}"; do
        echo "  ${next} ${HHS_HIGHLIGHT_COLOR}"
      done
    fi
    IFS=$OLDIFS
  fi

  echo "${NC}"
  return 0
}

# @function: Display a process list matching the process name/expression.
# @param $1 [Req] : The process name to check.
# @param $2 [Opt] : Whether to kill all found processes.
# @compatible: bash zsh
function __hhs_process_list() {

  local all_pids=() uid pid ppid cmd force=0 quiet=0 kill_flag=0 pad divider gflags='-E'

  if [[ $# -lt 1 || "$1" == "-h" || "$1" == "--help" ]]; then
    echo "usage: ${FUNCNAME[0]} [options] <process_name>"
    echo ''
    echo '    Options: '
    echo '        -k, --kill        : When specified, attempts to kill the processes it finds'
    echo '        -i, --ignore-case : Make case insensitive search'
    echo '        -w, --words       : Match full words only'
    echo '        -f, --force       : Do not prompt when killing processes'
    echo '        -q, --quiet       : Make the operation less talkative'
    echo ''
    return 1
  else
    while [[ -n "$1" ]]; do
      case "$1" in
      -w | --words)
        gflags="${gflags//E/Fw}"
        ;;
      -i | --ignore-case)
        gflags="${gflags}i"
        ;;
      -f | --force)
        force=1
        ;;
      -q | --quiet)
        quiet=1
        ;;
      -k | --kill)
        kill_flag=1
        ;;
      *)
        [[ ! "$1" =~ ^-[wifq] ]] && break
        ;;
      esac
      shift
    done

    IFS=$'\n'
    while IFS= read -r line; do all_pids+=("$line"); done < <(ps -axco uid,pid,ppid,comm | grep "${gflags}" "${1:-.}")
    IFS="${OLDIFS}"

    if [[ ${#all_pids[@]} -gt 0 ]]; then
      pad="$(printf '%0.1s' " "{1..40})"
      divider="$(printf '%0.1s' "-"{1..92})"
      echo ''
      [[ $quiet -ne 1 ]] && printf "${WHITE}%5s\t%5s\t%5s\t%-40s %s\n" "UID" "PID" "PPID" "COMMAND" "ACTIVE ?"
      [[ $quiet -ne 1 ]] && printf "%-154s\n\n" "${divider}"
      for next in "${all_pids[@]}"; do
        uid=$(awk '{ print $1 }' <<<"${next}")
        pid=$(awk '{ print $2 }' <<<"${next}")
        ppid=$(awk '{ print $3 }' <<<"${next}")
        cmd=$(awk '{for(i=4;i<=NF;i++) printf $i" "; print ""}' <<<"${next}")
        [[ "${#cmd}" -ge 37 ]] && cmd="${cmd:0:37}..."
        printf "${HHS_HIGHLIGHT_COLOR}%5s\t%5s\t%5s\t%s" "${uid}" "${pid}" "${ppid}" "${cmd}"
        printf '%*.*s' 0 $((40 - ${#cmd})) "${pad}"
        if [[ -n "${pid}" && $kill_flag -eq 1 ]]; then
          tput sc
          if [[ $force -ne 1 ]]; then
            read -r -n 1 -p "${YELLOW} Kill this process y/[n]? " ANS
          fi
          if [[ -n "${force}" || "$ANS" == "y" || "$ANS" == "Y" ]]; then
            tput rc
            if kill -9 "${pid}" &>/dev/null; then
              echo -en "${GREEN}=> Killed \"${pid}\" with SIGKILL(-9)\033[K"
            else
              echo -en "${ORANGE}=> Skipped \"${pid}\" inactive process\033[K"
            fi
          fi
          if [[ -n "$ANS" || -n "${force}" ]]; then echo -e "${NC}"; fi
        else
          # Check for ghost processes
          if ps -p "${pid}" &>/dev/null; then
            echo -e "${GREEN} ${CHECK_ICN}  active process"
          else
            echo -e "${RED} ${CROSS_ICN}  ghost process"
          fi
        fi
      done
    else
      echo -e "\n${ORANGE}No active PIDs for process named: \"$1\""
    fi
  fi

  echo -e "${NC}"

  return 0
}

# @function: Kills ALL processes specified by name
# @param $1 [Req] : The process name to kill
function __hhs_process_kill() {

  local ret_val=1 force_flag=

  if [[ "$#" -lt 1 || "$1" == "-h" || "$1" == "--help" ]]; then
    echo "usage: ${FUNCNAME[0]} [options] <process_name>"
    echo ''
    echo '    Options: '
    echo '        -f | --force : Do not prompt for confirmation when killing a process'
    return 1
  fi

  if [[ "$1" == "-f" || "$1" == "--force" ]]; then
    shift
    force_flag='-f'
  fi

  for nproc in "${@}"; do
    __hhs_process_list -q -k ${force_flag} "${nproc}"
    ret_val=$?
    echo -e "\033[3A" # Move up 3 lines to beautify the output
  done
  echo -e '\n'

  return ${ret_val}
}

# @function: Exhibit a Human readable summary about all partitions.
function __hhs_partitions() {

  local all_parts=() str_text mounted size used avail cap

  if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    echo "usage: ${FUNCNAME[0]} "
    return 1
  else
    IFS=$'\n'
    while IFS= read -r line; do all_parts+=("$line"); done < <(df -H | tail -n +2)
    IFS="${OLDIFS}"
    echo "${WHITE}"
    printf '%-4s\t%-5s\t%-4s\t%-8s\t%-s\n' 'Size' 'Avail' 'Used' 'Capacity' 'Mounted-ON'
    echo -e "----------------------------------------------------------------${HHS_HIGHLIGHT_COLOR}"
    for next in "${all_parts[@]}"; do
      str_text=${next:16}
      size="$(awk '{ print $1 }' <<<"${str_text}")"
      avail="$(awk '{ print $3 }' <<<"${str_text}")"
      used="$(awk '{ print $2 }' <<<"${str_text}")"
      cap="$(awk '{ print $4 }' <<<"${str_text}")"
      [[ "Darwin" == "${HHS_MY_OS}" ]] && mounted="$(awk '{ print $8 }' <<<"${str_text}")"
      [[ "Linux" == "${HHS_MY_OS}" ]] && mounted="$(awk '{ print $5 }' <<<"${str_text}")"
      printf '%-4s\t%-5s\t%-4s\t%-8s\t%-s\n' "${size:0:4}" "${avail:0:4}" "${used:0:4}" "${cap:0:4}" "${mounted:0:40}"
    done
    echo "${NC}"
  fi

  return 0
}

# @function: Provide information about the OS.
function __hhs_os_info() {

  local os_info=() linux_os_release='/etc/os-release'

  echo ''
  IFS=$'\n'
  code_name=$(__hhs_get_codename)
  if [[ "${HHS_MY_OS}" == "Darwin" ]]; then
    while IFS= read -r line; do os_info+=("$line"); done < <(sw_vers | awk '{print $2}')
    echo "${HHS_HIGHLIGHT_COLOR}    Type: ${WHITE}Darwin"
    echo "${HHS_HIGHLIGHT_COLOR}    Name: ${WHITE}${os_info[0]}"
    echo "${HHS_HIGHLIGHT_COLOR} Version: ${WHITE}${os_info[1]}"
    echo "${HHS_HIGHLIGHT_COLOR}Codename: ${WHITE}${code_name:-N/D}"
    echo "${HHS_HIGHLIGHT_COLOR}Home URL: ${WHITE}https://www.apple.com/support"
    echo "${NC}"
    return 0
  elif [[ "${HHS_MY_OS}" == "Linux" ]]; then
    if [[ -f "${linux_os_release}" ]] && source "${linux_os_release}"; then
      echo "${HHS_HIGHLIGHT_COLOR}    Type: ${WHITE}Linux"
      echo "${HHS_HIGHLIGHT_COLOR}    Name: ${WHITE}${ID:-N/D}"
      echo "${HHS_HIGHLIGHT_COLOR} Version: ${WHITE}${VERSION:-${VERSION_ID:-N/D}}"
      echo "${HHS_HIGHLIGHT_COLOR}Codename: ${WHITE}${VERSION_CODENAME:-${PRETTY_NAME:-N/D}}"
      echo "${HHS_HIGHLIGHT_COLOR}Home URL: ${WHITE}${HOME_URL:-N/D}"
      echo "${NC}"
      return 0
    else
      echo "${YELLOW}Could not find a valid os-release file in '/etc' folder !${NC}"
    fi
  else
    echo "${YELLOW}Unknown OS!${NC}"
  fi
  IFS="${OLDIFS}"

  return 1
}

# @function: Get the OS Codename.
function __hhs_get_codename() {

  if [[ "${HHS_MY_OS}" == "Darwin" ]]; then
    # Using Standard macOS software agreement.
    local line re_codename='.*SOFTWARE LICENSE AGREEMENT FOR ([a-zA-Z ]+).*'
    local os_info_file="/System/Library/CoreServices/Setup Assistant.app/Contents/Resources/en.lproj/OSXSoftwareLicense.rtf"

    line=$(grep -E "${re_codename}" "${os_info_file}")
    if [[ ${line} =~ ${re_codename} ]]; then
      echo "${BASH_REMATCH[1]//macOS /}"
      return 0
    fi
  elif [[ "${HHS_MY_OS}" == "Linux" ]]; then
    # Using /etc/os-release for a generic solution
    source /etc/os-release
    # Fallback if VERSION_CODENAME is empty
    [[ -z "${VERSION_CODENAME}" && -z "${PRETTY_NAME}" ]] && return 1
    echo "${VERSION_CODENAME:-$PRETTY_NAME}"
    return 0
  fi

  return 1
}
