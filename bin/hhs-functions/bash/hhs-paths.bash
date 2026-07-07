#!/usr/bin/env bash

# Script: hhs-paths.bash
# Created: Oct 5, 2019
# Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
# Mailto: taius.hhs@gmail.com
# Site: https://github.com/yorevs/homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2025, HomeSetup team
#
# !NOTICE: Do not change this file. To customize your functions edit the file ~/.function

# @function: Manage your custom PATH entries.
# @param $1..$N [Opt]: Flags and path inputs (see `--help` for options).
function __hhs_paths() {
  local OPTIND opt

  # Flags
  local add_path=""
  local remove_path=""
  local truncate=0
  local edit=0
  local clean=0
  local quiet=0
  local show_help=0

  # Display & formatting
  local path path_raw custom private path_dir tmp_file
  local columns truncate_col max_path_len=0 truncated=0
  local line_title pad_len PAD_CHAR="."
  local pad_space ellipsis="…"
  local visible_path type_prefix=""

  # Files and dirs
  HHS_PATHS_FILE=${HHS_PATHS_FILE:-${HHS_DIR}/.path}
  PATHS_D="/etc/paths.d"
  PVT_PATHS_D="/private/etc/paths"
  TRUNC_LEN=66

  # Parse options
  while getopts ":a:r:ectqh" opt; do
    case "${opt}" in
      a) add_path="${OPTARG}" ;;
      r) remove_path="${OPTARG}" ;;
      e) edit=1 ;;
      c) clean=1 ;;
      t) truncate=1 ;;
      q) quiet=1 ;;
      h) show_help=1 ;;
      \?) __hhs_errcho "${FUNCNAME[0]}" "Invalid option: -${OPTARG}"; return 1 ;;
      :) __hhs_errcho "${FUNCNAME[0]}" "Missing argument for -${OPTARG}"; return 1 ;;
    esac
  done
  shift $((OPTIND - 1))

  # Help
  if [[ "${show_help}" -eq 1 ]]; then
    echo "usage: ${FUNCNAME[0]} [options] <args>"
    echo ''
    echo '    Options: '
    echo '      -a <path> : Add the specified <path> to PATH.'
    echo '      -r <path> : Remove the specified <path> from PATH.'
    echo '      -e        : Edit the HHS_PATHS_FILE.'
    echo '      -c        : Clear non-existing paths from the PATH file.'
    echo '      -t        : Enable truncation mode.'
    echo '      -q        : Quiet mode.'
    echo '      -h        : Show this help message.'
    echo ''
    echo '  Notes: '
    echo '    - If no arguments are provided, it lists all PATH entries.'
    return 0
  fi

  # Deduplicate
  [[ -f "${HHS_PATHS_FILE}" ]] && sort -u "${HHS_PATHS_FILE}" -o "${HHS_PATHS_FILE}"

  # Edit
  if [[ "${edit}" -eq 1 ]]; then
    __hhs_edit "${HHS_PATHS_FILE}"
    return 0
  fi

  # Add
  if [[ -n "${add_path}" ]]; then
    if [[ ! -d "${add_path}" ]]; then
      __hhs_errcho "${FUNCNAME[0]}" "Path \"${add_path}\" does not exist"
      return 1
    fi
    grep -qxF "${add_path}" "${HHS_PATHS_FILE}" && return 0
    tmp_file="$(mktemp "${HHS_PATHS_FILE}.XXXXXX")" || return 1
    grep -vxF -- "${add_path}" "${HHS_PATHS_FILE}" >"${tmp_file}" || true
    mv "${tmp_file}" "${HHS_PATHS_FILE}" || return 1
    echo "${add_path}" >>"${HHS_PATHS_FILE}"
    export PATH="${add_path}:${PATH}"
    [[ "${quiet}" -eq 0 ]] && echo "${GREEN}Path added: ${WHITE}\"${add_path}\"${NC}"
    return 0
  fi

  # Remove
  if [[ -n "${remove_path}" ]]; then
    if grep -qxF "${remove_path}" "${HHS_PATHS_FILE}"; then
      tmp_file="$(mktemp "${HHS_PATHS_FILE}.XXXXXX")" || return 1
      grep -vxF -- "${remove_path}" "${HHS_PATHS_FILE}" >"${tmp_file}" || true
      if mv "${tmp_file}" "${HHS_PATHS_FILE}"; then
        export PATH="${PATH//${remove_path}:/}"
        [[ "${quiet}" -eq 0 ]] && echo "${YELLOW}Path removed: ${WHITE}\"${remove_path}\"${NC}"
      fi
    else
      __hhs_errcho "${FUNCNAME[0]}" "Path \"${remove_path}\" is not in the PATH file"
      return 1
    fi
    return 0
  fi

  # Listing / Clean mode
  [[ -f "${HHS_PATHS_FILE}" ]] || touch "${HHS_PATHS_FILE}"

  if [[ -t 1 ]]; then
    columns=$(tput cols)
  fi
  columns=${columns:-80}
  truncate_col=$((columns - 50))

  # First pass: find longest raw path (assume 2-char prefix)
  for path_raw in ${PATH//:/ }; do
    [[ ${#path_raw} -gt ${max_path_len} ]] && max_path_len=${#path_raw}
  done

  # Auto-truncate if terminal is too narrow
  if (( max_path_len + 50 > columns )); then
    truncate=1
    truncated=1
  fi

  # Truncation mode
  if (( truncate )); then
    max_path_len=$TRUNC_LEN
    truncate_col=$TRUNC_LEN
    pad_len=$TRUNC_LEN
    truncated=1
  else
    pad_len=$((max_path_len + 2))
  fi

  # Header
  line_title="${YELLOW}Listing all PATH entries"
  [[ "${truncated}" -eq 1 ]] && line_title+=" (truncated paths)"
  line_title+=":${NC}"

  echo ''
  echo -e "${line_title}"
  echo ''

  for path_raw in ${PATH//:/ }; do
    path="${path_raw}"

    # Determine prefix icon
    if [[ -L "${path_raw}" ]]; then
      type_prefix=" "
    elif [[ -d "${path_raw}" ]]; then
      type_prefix=" "
    else
      type_prefix=" "
    fi

    visible_path="${path}"

    # Truncate and add ellipsis
    if (( truncate )) && [[ ${#visible_path} -gt truncate_col ]]; then
      visible_path="${visible_path:0:$((truncate_col - 1))}${ellipsis}"
    fi

    # Padding is based on full visible string (icon + path + ellipsis)
    printf -v pad_space '%*s' $((pad_len - ${#visible_path})) ''
    echo -en "${WHITE}${type_prefix}${HHS_HIGHLIGHT_COLOR}${visible_path}${pad_space// /${PAD_CHAR}}"

    # Existence marker
    if [[ -d "${path_raw}" ]]; then
      echo -en "${GREEN} ${CHECK_ICN}  ${WHITE}"
    else
      if [[ "${clean}" -eq 1 ]]; then
        tmp_file="$(mktemp "${HHS_PATHS_FILE}.XXXXXX")" || return 1
        grep -vxF -- "${path_raw}" "${HHS_PATHS_FILE}" >"${tmp_file}" || true
        mv "${tmp_file}" "${HHS_PATHS_FILE}" || return 1
        export PATH="${PATH//${path_raw}:/}"
        echo -en "${RED} ${CROSS_ICN}  "
      else
        echo -en "${ORANGE} ${CROSS_ICN}  "
      fi
    fi

    # Path classification
    custom=""
    private=""
    path_dir=""
    [[ -f "${HHS_PATHS_FILE}" ]] && custom="$(grep -Fx -- "${path_raw}" "${HHS_PATHS_FILE}")"
    [[ -d "${PVT_PATHS_D}" ]] && private="$(find "${PVT_PATHS_D}" -type f -exec cat {} \; | grep -Fx -- "${path_raw}")"
    [[ -d "${PATHS_D}" ]] && path_dir="$(find "${PATHS_D}" -type f -exec cat {} \; | grep -Fx -- "${path_raw}")"

    if [[ -n "${custom}" ]]; then
      echo -n "${BLUE}Custom path"
    elif [[ -n "${path_dir}" ]]; then
      echo -n "${VIOLET}Private system path (${PATHS_D})"
    elif [[ -n "${private}" ]]; then
      echo -n "${VIOLET}General system path (${PVT_PATHS_D})"
    else
      echo -n "${WHITE}Shell export"
    fi
    echo -e "${NC}"

  done

  echo -e "${NC}"
  return 0
}
