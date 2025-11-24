#!/usr/bin/env bash
# shellcheck disable=SC2206

#  Script: hhs-taylor.bash
# Created: Oct 5, 2019
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs/homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2025, HomeSetup team

# !NOTICE: Do not change this file. To customize your functions edit the file ~/.functions

# @function: Tail a log using customized colors and patterns.
# @param $1 [Req] : The log file name.
function __hhs_tailor() {

  local file sed_flag all_args args last_idx file stream

  HHS_TAILOR_LEVEL_INFO_RE="INFO|OUT"
  HHS_TAILOR_LEVEL_INFO_COLOR=${HHS_TAILOR_LEVEL_INFO_COLOR:="${GREEN}"}
  HHS_TAILOR_LEVEL_DEBUG_RE="DEBUG|FINE|TRACE"
  HHS_TAILOR_LEVEL_DEBUG_COLOR=${HHS_TAILOR_LEVEL_DEBUG_COLOR:="${WHITE}"}
  HHS_TAILOR_LEVEL_WARN_RE="WARN[ING]*"
  HHS_TAILOR_LEVEL_WARN_COLOR=${HHS_TAILOR_LEVEL_WARN_COLOR:="${YELLOW}"}
  HHS_TAILOR_LEVEL_ERR_RE="CRITICAL|SEV[ERE]*|FATAL|ERR[OR]*"
  HHS_TAILOR_LEVEL_ERROR_COLOR=${HHS_TAILOR_LEVEL_ERROR_COLOR:="${RED}"}
  HHS_TAILOR_THREAD_NAME_RE=" *[-a-zA-Z0-9_ =]+ *"
  HHS_TAILOR_THREAD_NAME_COLOR=${HHS_TAILOR_THREAD_NAME_COLOR:="${PURPLE}"}
  HHS_TAILOR_FQDN_RE=" [a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+ ?"
  HHS_TAILOR_FQDN_COLOR=${HHS_TAILOR_FQDN_COLOR:="${CYAN}"}
  HHS_TAILOR_DATE_FMT_RE="([0-9]{1,4}[-/]?){3}[T ]([0-9]{1,2}[-:]?){2,3}((\.[0-9]+([+-][0-9]{1,2}[-:][0-9]{1,2}|Z))|([,.][0-9]+))?"
  HHS_TAILOR_DATE_FMT_COLOR=${HHS_TAILOR_DATE_FMT_COLOR:="${VIOLET}"}
  HHS_TAILOR_URI_RE="(((https?|ftp|file):\/)|(\/?[a-zA-Z0-9]+))\/[-A-Za-z0-9\+&@#/%?=~_|!:,.;]*\.*[-A-Za-z0-9\+&@#/%=~_|]"
  HHS_TAILOR_URI_COLOR=${HHS_TAILOR_URI_COLOR:="${BLUE}"}

  if [[ "$(uname -s)" == "Darwin" ]]; then
    sed_flag="-E"
  else
    sed_flag="-r"
  fi

  if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    echo "usage: ${FUNCNAME[0]} [-F | -f | -r] [-q] [-b # | -c # | -n #] <file>"
    echo ''
    echo '  Notes: '
    echo '    - filename: If not provided, /dev/stdin will be used instead.'
    return 1
  else

    if [[ $# -gt 0 ]]; then
      all_args=(${*})
      args=${all_args[*]::${#all_args[@]} - 1}
      last_idx=$((${#all_args[@]} - 1))
      file=${all_args[last_idx]}
    fi

    file=${file:-/dev/stdin}

    if [[ "${file}" == '/dev/stdin' ]]; then
      while read -r stream; do
        echo "${stream}" | sed ${sed_flag} \
          -e "s/\[(${HHS_TAILOR_THREAD_NAME_RE})\]/\[${HHS_TAILOR_THREAD_NAME_COLOR}\1${NC}\]/g" \
          -e "s/(${HHS_TAILOR_FQDN_RE})/${HHS_TAILOR_FQDN_COLOR}\1${NC}/g" \
          -e "s/(${HHS_TAILOR_LEVEL_INFO_RE})/${HHS_TAILOR_LEVEL_INFO_COLOR}\1${NC}/g" \
          -e "s/(${HHS_TAILOR_LEVEL_DEBUG_RE})/${HHS_TAILOR_LEVEL_DEBUG_COLOR}\1${NC}/g" \
          -e "s/(${HHS_TAILOR_LEVEL_WARN_RE})/${HHS_TAILOR_LEVEL_WARN_COLOR}\1${NC}/g" \
          -e "s/(${HHS_TAILOR_LEVEL_ERR_RE})/${HHS_TAILOR_LEVEL_ERROR_COLOR}\1${NC}/g" \
          -e "s/(${HHS_TAILOR_DATE_FMT_RE})/${HHS_TAILOR_DATE_FMT_COLOR}\1${NC}/g" \
          -e "s/(${HHS_TAILOR_URI_RE})/${HHS_TAILOR_URI_COLOR}\1${NC}/g"
      done <"${file}"
    else
      [[ -f "${file}" ]] && touch "${file}"
      [[ ${#args[@]} -le 1 && -z ${args[0]} ]] && unset -f args
      # shellcheck disable=SC2068
      tail ${args[@]} "${file}" | sed ${sed_flag} \
        -e "s/\[(${HHS_TAILOR_THREAD_NAME_RE})\]/\[${HHS_TAILOR_THREAD_NAME_COLOR}\1${NC}\]/g" \
        -e "s/(${HHS_TAILOR_LEVEL_INFO_RE})/${HHS_TAILOR_LEVEL_INFO_COLOR}\1${NC}/g" \
        -e "s/(${HHS_TAILOR_FQDN_RE})/${HHS_TAILOR_FQDN_COLOR}\1${NC}/g" \
        -e "s/(${HHS_TAILOR_LEVEL_DEBUG_RE})/${HHS_TAILOR_LEVEL_DEBUG_COLOR}\1${NC}/g" \
        -e "s/(${HHS_TAILOR_LEVEL_WARN_RE})/${HHS_TAILOR_LEVEL_WARN_COLOR}\1${NC}/g" \
        -e "s/(${HHS_TAILOR_LEVEL_ERR_RE})/${HHS_TAILOR_LEVEL_ERROR_COLOR}\1${NC}/g" \
        -e "s/(${HHS_TAILOR_DATE_FMT_RE})/${HHS_TAILOR_DATE_FMT_COLOR}\1${NC}/g" \
        -e "s/(${HHS_TAILOR_URI_RE})/${HHS_TAILOR_URI_COLOR}\1${NC}/g"
    fi

  fi

  return $?
}
