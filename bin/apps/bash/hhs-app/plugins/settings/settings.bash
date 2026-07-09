#!/usr/bin/env bash

#  Script: settings.bash
# Created: Jul 18, 2023
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs/homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2025, HomeSetup team

# Current plugin name
PLUGIN_NAME="settings"

# Current python module name
MODULE_NAME="setman"

# Namespace cleanup
UNSETS=(
  help version cleanup execute
)

# @purpose: HHS plugin required function
function help() {
  local ret_val

  python3 -m "${MODULE_NAME}" -h
  ret_val=$?
  printf '\nHomeSetup wrapper options:\n'
  printf '  truncate -f, truncate --force  Remove all settings without interactive confirmation.\n'

  exit "${ret_val}"
}

# @purpose: HHS plugin required function
function version() {
  python3 -m "${MODULE_NAME}" -v
  exit $?
}

# @purpose: HHS plugin required function
function cleanup() {
  unset -f "${UNSETS[@]}"
  echo -n ''
}

# shellcheck disable=SC1090,SC2206
# @purpose: HHS plugin required function
function execute() {

  local args env_file ret_val=0 num arg_n force operation_index has_filter idx

  __hhs_is_venv || quit 1 "Not available when HomeSetup python venv is not active!"

  args=()
  arg_n=${#}

  if [[ "${#}" -eq 0 ]]; then
    python3 -m "${MODULE_NAME}" -h
  # Hook the setman source command
  elif [[ $1 == 'source' ]]; then
    __hhs_has direnv && env_file='.envrc'
    shift
    while getopts ":f:n:" opt; do
      case "${opt}" in
      f)
        env_file="${OPTARG}"
        ;;
      n)
        args+=("-n" "${OPTARG}")
        ;;
      *)
        quit 1 "Invalid argument: ${opt}"
        ;;
      esac
    done
    env_file=${env_file:-"settings-export-$(date +'%Y%m%d%H%M%S')"}
    if [[ $((arg_n%2)) -eq 0 ]]; then
      quit 1 "Invalid settings syntax: ${*}"
    elif python3 -m "${MODULE_NAME}" source -f "${env_file}" "${args[@]}"; then
      # Remove duplicate entries
      sort | uniq -o "${env_file}"{,}
      # Check if env_file is not empty and count the exported settings
      if [[ -f "${env_file}" && -n "${env_file}" ]]; then
        num=$(wc -l "${env_file}" | sed -e 's/^[ \t]*\([0-9]*\) *\/*.*/\1/')
        if [[ $num -gt 0 ]]; then
          echo -e "${GREEN}Exported (${num}) settings. To source them type:${NC}"
          echo ">> ${BLUE}source ${env_file}${NC}"
        else
          echo -e "${YELLOW}No settings found!${NC}"
          \rm -f  "${env_file}"
        fi
      fi
    else
      quit 1 "Settings command failed: ${*}"
    fi
  # Execute the setman python app normally
  else
    force=0
    args=()
    while [[ "${#}" -gt 0 ]]; do
      case "${1}" in
      -f | --force)
        force=1
        ;;
      *)
        args+=("${1}")
        ;;
      esac
      shift
    done

    if [[ "${force}" -eq 1 ]]; then
      operation_index=-1
      has_filter=0
      for idx in "${!args[@]}"; do
        case "${args[$idx]}" in
        truncate)
          operation_index="${idx}"
          ;;
        -n | --name | -t | --type)
          has_filter=1
          ;;
        esac
      done
      [[ "${operation_index}" -ge 0 ]] || quit 1 "Force option is only supported with truncate."
      [[ "${has_filter}" -eq 1 ]] || args+=("-n" "*")
    fi

    python3 -m "${MODULE_NAME}" "${args[@]}"
  fi
  ret_val=$?
  echo -e "${NC}"

  quit ${ret_val}
}
