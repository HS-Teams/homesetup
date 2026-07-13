#!/usr/bin/env bash

#  Script: built-ins.bash
# Purpose: Contains HHS-App built-in functions.
# Created: Jan 06, 2020
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs#homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2025, HomeSetup team

# @purpose: List all HHS App Plug-ins and Functions.
# @param $1 [opt] : Instead of a formatted as a list, flat the commands for bash completion.
function list() {

  local args=("${@}") columns args count line

  if [[ "$1" == "help" ]]; then
    echo "usage: __hhs ${FUNCNAME[0]} [-flat] [-plugins] [-funcs] [-commands] [-aliases]" && quit 0
  fi

  # The complete command catalog is only needed for explicit discovery output.
  search_hhs_commands
  if [[ "${args[*]}" =~ -flat ]]; then
    args=("${args[@]/'-flat'/}")
    [[ ${#args[@]} -eq 1 || "${args[*]}" =~ -plugins ]] \
      && { for next in "${PLUGINS[@]}"; do echo -n "${next} "; done }
    [[ ${#args[@]} -eq 1 || "${args[*]}" =~ -funcs ]] \
      && { for next in "${HHS_APP_FUNCTIONS[@]}"; do echo -n "${next} "; done }
    [[ ${#args[@]} -eq 1 || "${args[*]}" =~ -commands ]] \
      && { for next in "${HHS_COMMANDS[@]}"; do echo -n "${next} "; done }
    [[ ${#args[@]} -eq 1 || "${args[*]}" =~ -aliases ]] \
      && { for next in "${HHS_ALIASES[@]}"; do echo -n "${next} "; done }
    quit 0
  else
    columns="$(tput cols)"
    count=$((${#PLUGINS[@]} > ${#HHS_APP_FUNCTIONS[@]} ? ${#PLUGINS[@]} : ${#HHS_APP_FUNCTIONS[@]}))
    count=$((${#count[@]} > ${#HHS_COMMANDS[@]} ? ${#count[@]} : ${#HHS_COMMANDS[@]}))
    echo -e "\n${YELLOW}HomeSetup application commands"
    if [[ ${#args[@]} -eq 0 || "${args[*]}" =~ -plugins ]]; then
      display_list "\n-=- HHS Plug-ins -=-\n" "${PLUGINS[@]}"
    fi
    if [[ ${#args[@]} -eq 0 || "${args[*]}" =~ -funcs ]]; then
      display_list "\n-=- HHS Functions -=-\n" "${HHS_APP_FUNCTIONS[@]}"
    fi
    if [[ ${#args[@]} -eq 0 || "${args[*]}" =~ -commands ]]; then
      display_list "\n-=- HHS Commands -=-\n" "${HHS_COMMANDS[@]}"
    fi
    if [[ ${#args[@]} -eq 0 || "${args[*]}" =~ -aliases ]]; then
      display_list -k "\n-=- HHS Aliases -=-\n" "${HHS_ALIASES[@]}"
    fi
  fi

  quit 0
}

# @purpose: Search for all __hhs_functions describing it's containing file name and line number.
function funcs() {

  local columns fn_name cache_file usage filter count matches=0

  usage="usage: __hhs ${FUNCNAME[0]} [regex_filter]"

  [[ "$1" == 'help' ]] && echo "${usage}" && quit 0

  cache_file="${HHS_CACHE_DIR}/hhs-funcs-${HHS_VERSION//./}.cache"

  filter=$*
  filter="${filter// /\|}"
  filter="${filter:-.*}"

  echo ' '
  echo "${YELLOW}-=- Available HomeSetup v${HHS_VERSION} functions matching [${filter}] -=-"

  if [[ ! -s "${cache_file}" ]]; then
    echo -en "${ORNGE}Please wait until we cache all HomeSetup v${HHS_VERSION} functions ...${NC}"
    search_hhs_functions \
      "${HHS_HOME}/dotfiles/bash" \
      "${HHS_HOME}/bin/hhs-functions/bash" \
      "${HHS_HOME}/bin/dev-tools/bash"
    printf "%s\n" "${HHS_FUNCTIONS[@]}" > "${cache_file}"
    echo -en '\033[2K'
    echo ''
  else
    echo ' '
    IFS=$'\n' read -r -d '' -a HHS_FUNCTIONS < <(grep . "${cache_file}")
    IFS="${OLDIFS}"
  fi

  columns="$(tput cols)"
  count="${#HHS_FUNCTIONS[@]}"
  for line in "${HHS_FUNCTIONS[@]}"; do
    fn_name=$(awk 'BEGIN { FS = "" } ; { print $2 }' <<< "${line}")
    fn_name=${fn_name%%:*}
    fn_name=$(trim <<< "${fn_name}")
    if [[ ${fn_name} =~ ${filter} ]]; then
      ((matches++))
      printf "${YELLOW}%${#count}d  ${HHS_HIGHLIGHT_COLOR}" "$((matches))"
      echo -en "${line:0:${columns}}${NC}"
      [[ "${#line}" -ge "${columns}" ]] && echo -n "..."
      echo -e "${NC}"
    fi
  done

  [[ $matches -eq 0 ]] && echo -e "${YELLOW}No functions found matching \"${filter}\"${NC}"

  quit 0
}

# @purpose: Retrieve HomeSetup logs.
# @param $1 [opt] : The hhs file to retrieve logs from.
# @param $2 [opt] : The log level to retrieve.
function logs() {

  local level logfile logs usage tail_opts
  local all_levels="ALL_LEVELS CRITICAL DEBUG ERROR FATAL FINE INFO OUT TRACE WARNING WARN SEVERE"

  usage="usage: __hhs ${FUNCNAME[0]} [-F] [hhs-log-file] [level]"
  [[ "${1}" =~ -h|--help ]] && quit 0 "${usage}"

  while [[ "$#" -gt 0 ]]; do
    case "$1" in
      -F|-f|-r) tail_opts="${tail_opts} $1"; shift ;;
      -q) tail_opts="${tail_opts} -q"; shift ;;
      -b|-c|-n) tail_opts="${tail_opts} $1 ${2:-log_lines}"; shift 2 ;;
      -h|--help) quit 0 "${usage}" ;;
      *) files+=("$1"); break ;;
    esac
  done

  tail_opts="${tail_opts} "
  [[ ! "$tail_opts" =~ (^|[[:space:]])-n([[:space:]]|$) ]] && tail_opts="${tail_opts} -n +1"
  level=$(echo "${1}" | tr '[:lower:]' '[:upper:]')

  if [[ -n "${level}" ]]; then
    if ! list_contains "${all_levels}" "${level}"; then
      logfile="${HHS_LOG_DIR}/${1//.log/}.log"
      if [[ ! -f "${logfile}" ]]; then
        logs=$(find "${HHS_LOG_DIR}" -type f -name '*.log' -exec basename {} \; | nl)
        __hhs_errcho "${APP_NAME}" "${WHITE}${POINTER_ICN} Log file not found: ${YELLOW}'${logfile}'."
        echo -e "${BLUE}\nAvailable log files: \n\n${CYAN}${logs}\n"
        quit 1
      fi
      level=$(echo "${2}" | tr '[:lower:]' '[:upper:]')
      if [[ -n "${level}" ]]; then
        if ! list_contains "${all_levels}" "${level}"; then
          quit 1 "Undefined log level: ${level}"
        fi
      fi
    else
      [[ -n $2 ]] && logfile="${HHS_LOG_DIR}/${2//.log/}.log"
      if [[ -n "${logfile}" && ! -f "${logfile}" ]]; then
        logs=$(find "${HHS_LOG_DIR}" -type f -name '*.log' -exec basename {} \; | nl)
        __hhs_errcho "${APP_NAME}" "${WHITE}${POINTER_ICN} Log file not found: ${YELLOW}'${logfile}'."
        echo -e "${BLUE}\nAvailable log files: \n\n${CYAN}${logs}\n"
        quit 1
      fi
    fi
  fi

  logfile=${logfile:="${HHS_LOG_FILE}"}
  re='-n [0-9]* -F'

  [[ ${tail_opts} =~ ${re} ]] && echo -en "\n${YELLOW}Tailing " || echo -en "\n${WHITE}Retrieving "
  echo -e "logs [${level:-ALL_LEVELS}] from ${logfile}:${NC}\n"

  if [[ -z "${level}" || "${level}" == 'ALL_LEVELS' ]]; then
    __hhs_tailor "${tail_opts}" "${logfile}"
  else
    tail ${tail_opts} "${logfile}" | awk -v level="${level}" 'toupper($3) == level' | __hhs_tailor
  fi

  quit $?
}

# @purpose: Display logs for a specified process over the last specified number of days.
# @param $1 [req] : The name of the process to filter logs for.
# @param $2 [req] : The number of days in the past to search for logs.
function sys-logs() {
    local process_name=$1 days=$2
    # Check if both arguments are provided
    if [ -z "$1" ] || [ -z "$2" ]; then
        echo "usage: __hhs ${FUNCNAME[0]} <process_name> <days>"
        return 1
    fi
    shift 2
    log show --predicate "process == \"${process_name}\"" --info --last "${days}"d "$@"
}


# @purpose: Fetch the ss64 manual from the web for the specified bash command.
# @param $1 [req] : The bash command to find out the manual.
function man() {

  local cmd="${1}" ss63_url

  ss63_url="https://ss64.com/${HHS_MY_SHELL}/${cmd}.html"

  if [[ $# -ne 1 || -z "${cmd}" ]]; then
    echo "usage: __hhs ${FUNCNAME[0]} <bash_command>"
  else
    echo -e "${ORANGE}Opening SS64 man page for '${cmd}': ${ss63_url}"
    sleep 2
    __hhs_open "${ss63_url}" && quit 0 ''
    quit 1 "Failed to open url: \"${ss63_url}\" !"
  fi

  quit 0
}

# @purpose: Attempt to display the help for the given command.
# @param $1 [Req] : The command to get help.
function help() {

  local cmd="${1}" help_msg
  if [[ -z "${cmd}" || "$1" == "-h" || "$1" == "--help" ]]; then
    echo "usage: ${FUNCNAME[0]} <command>"
    quit 1
  fi

  __hhs_has "${cmd}" || quit 1 "Command not found: '${cmd}'"

  help_msg="$(${cmd} --help 2>&1 | awk '/^[Uu]sage:/ {found=1} found')"
  if [[ -z "${help_msg}" ]]; then
    help_msg="$(${cmd} help 2>&1 | awk '/^[Uu]sage:/ {found=1} found')"
    if [[ -z "${help_msg}" ]]; then
      help_msg="$(${cmd} --0h012hux267844asu 2>&1 | awk '/^[Uu]sage:/ {found=1} found')"
      if [[ -z "${help_msg}" ]]; then
        quit 1 "Help not available for: '${cmd}'"
      fi
    fi
  fi

  echo -e "${YELLOW}Displaying help for: ${BLUE}'${cmd}'${NC}\n"
  echo -e "${help_msg}\n"

  quit 0
}

# @purpose: Clear HomeSetup logs, backups and caches and restore original HomeSetup files.
function reset() {

  local apply_idx=0 apply_raw apply_value colorls_dir file matched_file mchoose_file="" title
  local was_set=0 ret_val=0
  local -a all_files=() apply_values=() filtered_files=() matched_files=() selected_files=()

  all_files=(
    "${HHS_LOG_DIR}/*.log"
    "${HHS_BACKUP_DIR}/*.bak"
    "${HHS_CACHE_DIR}/*.*"
    "${HHS_DIR}/.aliasdef"
    "${HOME}/.inputrc"
    "${HHS_KEY_BINDINGS}"
    "${HHS_SETUP_FILE}"
    "${HHS_SHOPTS_FILE}"
    "${HHS_OLLAMA_HISTORY_FILE}"
    "${HHS_OLLAMA_PROMPT_FILE}"
  )

  __hhs_has 'colorls' && gem which colorls &>/dev/null && {
    colorls_dir="$(dirname "$(gem which colorls)")/yaml"
    if compgen -G "${colorls_dir}/*.yaml" &>/dev/null; then
      all_files+=("${colorls_dir}/*.yaml")
    else
      all_files+=("${HOME}/.config/colorls/*.yaml")
    fi
  }
  __hhs_has 'starship' && all_files+=("${STARSHIP_CONFIG}")

  for file in "${all_files[@]}"; do
    [[ -n "${file}" ]] && filtered_files+=("${file}")
  done
  all_files=("${filtered_files[@]}")

  case "${1:-}" in
    -h|--help|help)
      cat <<EOF
usage: __hhs reset [-apply <0|1>...] [options]

  Clear selected HomeSetup logs, backups, caches, and generated configuration files.

    options:
      -apply [<0|1>, ...]      : Apply reset selections in displayed order; omitted values default to 0.
      -list                    : List reset targets in apply order without opening the menu.
      -h | --help              : Display this help message.

    examples:
      Apply reset options from CLI:
        => __hhs reset -apply 1 0 1
      Review reset options interactively:
        => __hhs reset
EOF
      return 0
      ;;
    -list)
      [[ $# -eq 1 ]] || {
        echo "Unexpected reset arguments: ${*:2}" >&2
        return 1
      }
      printf '%s\n' "${all_files[@]}"
      return 0
      ;;
    -apply)
      shift
      for apply_raw in "$@"; do
        apply_raw="${apply_raw//[/}"
        apply_raw="${apply_raw//]/}"
        apply_raw="${apply_raw//,/}"
        [[ -n "${apply_raw}" ]] && apply_values+=("${apply_raw}")
      done

      if [[ "${#apply_values[@]}" -gt "${#all_files[@]}" ]]; then
        echo "Expected at most ${#all_files[@]} reset values, received ${#apply_values[@]}." >&2
        return 1
      fi

      for file in "${all_files[@]}"; do
        apply_value="${apply_values[apply_idx]:-0}"
        case "${apply_value}" in
          1|true|True|TRUE) selected_files+=("${file}") ;;
          0|false|False|FALSE) ;;
          *)
            echo "Invalid reset value: ${apply_value}. Use 0 or 1." >&2
            return 1
            ;;
        esac
        ((apply_idx += 1))
      done
      ;;
    "")
      title="${YELLOW}Attention! Mark what you want to delete  (${#all_files[@]})${NC}"
      mchoose_file=$(mktemp)
      if __hhs_mchoose "${mchoose_file}" "${title}" "${all_files[@]}"; then
        [[ $(wc -c < "${mchoose_file}") -le 1 ]] && return 1
        echo ' ' >> "${mchoose_file}"
        while read -r -d ' ' file; do
          [[ -n "${file}" ]] && selected_files+=("${file}")
        done < "${mchoose_file}"
        clear
      fi
      ;;
    *)
      echo "Unexpected reset arguments: $*" >&2
      return 1
      ;;
  esac

  if [[ ${#selected_files[@]} -gt 0 ]]; then
    echo -e "${YELLOW}Deleting selected files...${NC}\n"
    \shopt -q nullglob
    was_set=$?
    \shopt -s nullglob
    for file in "${selected_files[@]}"; do
      matched_files=()
      if [[ "${file}" == *[\*\?\[]* ]]; then
        while IFS= read -r matched_file; do
          if [[ "${matched_file}" == "${HHS_BACKGROUND_JOB_STDOUT_PATH:-}" || \
            "${matched_file}" == "${HHS_BACKGROUND_JOB_STDERR_PATH:-}" ]]; then
            continue
          fi
          matched_files+=("${matched_file}")
        done < <(compgen -G "${file}")
      elif [[ -e "${file}" || -L "${file}" ]]; then
        matched_files+=("${file}")
      fi
      echo -en "${HHS_HIGHLIGHT_COLOR}Deleting file ${WHITE}"
      echo -n "${file} $(printf '\056%.0s' {1..60})" | head -c 60
      if [[ ${#matched_files[@]} -gt 0 ]]; then
        if \rm -rfv -- "${matched_files[@]}" &> /dev/null; then
          echo -e "${GREEN} OK${NC}"
        else
          echo -e "${RED} FAILED${NC}"
          ret_val=1
        fi
      else
        echo -e "${YELLOW} SKIPPED${NC}"
      fi
    done
    echo ''
  fi
  [[ -f "${mchoose_file}" ]] && \rm -fv "${mchoose_file}" &> /dev/null
  (( was_set != 0 )) && \shopt -u nullglob
  echo -e "${YELLOW}Some changes will take effect after you 'reopen' your terminal!${NC}"

  return $ret_val

}
