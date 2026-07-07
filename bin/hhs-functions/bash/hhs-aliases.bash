#!/usr/bin/env bash
# shellcheck disable=SC1090

#  Script: hhs-aliases.bash
# Created: Oct 5, 2019
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs/homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2025, HomeSetup team

# !NOTICE: Do not change this file. To customize your functions edit the file ~/.functions

# @function: Manipulate custom aliases (add/remove/edit/list).
# @param $1 [Req] : The alias name.
# @param $2 [Opt] : The alias expression.
# @compatible: bash zsh
function __hhs_aliases() {

  HHS_ALIASES_FILE=${HHS_ALIASES_FILE:-$HHS_DIR/.aliases}

  local filter='.+' alias_name alias_expr pad pad_len all_aliases=() name expr tmp_file
  local col_offset=18 columns re

  touch "${HHS_ALIASES_FILE}"

  if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    echo "usage: ${FUNCNAME[0]} <alias> <alias_expr>"
    echo ''
    echo '    Options: '
    echo '      -l | --list    : List all custom aliases.'
    echo '      -e | --edit    : Open the aliases file for editing.'
    echo '      -r | --remove  : Remove an alias.'
    echo ''
    echo '  Notes: '
    echo '    - List all aliases    : When [alias_expr] is NOT provided. If [alias] is provided, filter results using it.'
    echo '    - Add/Set an alias    : When both [alias] and [alias_expr] are provided.'
    echo ''
    return 1
  else
    if [[ "$1" == '-e' || "$1" == "--edit" ]]; then
      __hhs_edit "${HHS_ALIASES_FILE}"
      return $?
    elif [[ "$1" == '-r' || "$1" == "--remove" ]] && [[ -n "$2" ]]; then
      alias_name="$2"
      # Remove one alias
      if grep -q "^alias ${alias_name}=.*$" "${HHS_ALIASES_FILE}"; then
        unalias "${alias_name}" &>/dev/null || true
        tmp_file="$(mktemp "${HHS_ALIASES_FILE}.XXXXXX")" || return 1
        awk -v alias_name="${alias_name}" \
          'index($0, "alias " alias_name "=") != 1 { print }' \
          "${HHS_ALIASES_FILE}" >"${tmp_file}"
        if mv "${tmp_file}" "${HHS_ALIASES_FILE}"; then
          echo -e "${YELLOW}Alias removed: ${WHITE}\"${alias_name}\"${NC}"
          return 0
        fi
        __hhs_errcho "${FUNCNAME[0]}" "Failed to remove alias: \"${alias_name}\""
      else
        __hhs_errcho "${FUNCNAME[0]}" "Alias not found: \"${alias_name}\""
        return 1
      fi
    elif [[ "$1" == '-l' || "$1" == "--list" ]] && [[ -z "$2" ]]; then
      alias_name="$2"
    else
      alias_name="$1"
    fi
    [[ $# -gt 0 ]] && shift

    # Remove duplicate items
    sort -u "${HHS_ALIASES_FILE}" -o "${HHS_ALIASES_FILE}"

    alias_expr="${*}"
    alias_expr="${alias_expr//$'\n'/ }"

    if [[ -z "${alias_expr}" || "$1" == '-l' || "$1" == "--list" ]]; then
      while IFS= read -r line; do all_aliases+=("$line"); done < <(grep -i -v '^#' "${HHS_ALIASES_FILE}")
      IFS="${OLDIFS}"
      if [[ ${#all_aliases[@]} -gt 0 ]]; then
        pad=$(printf '%0.1s' "."{1..60})
        pad_len=41
        [[ -n "${alias_name}" ]] && filter="${alias_name}"
        echo ' '
        echo "${YELLOW}Available custom aliases matching [${filter}]:"
        echo ' '
        columns="$(($(tput cols) - pad_len - col_offset))"
        IFS=$'\n'
        for next in "${all_aliases[@]}"; do
          re="^alias .+=.+"
          if [[ ${next} =~ ${re} ]]; then
            name=$(echo -en "${next}" | cut -d'=' -f1 | cut -d ' ' -f2)
            [[ ${name} =~ ${filter} ]] || continue
            expr=$(echo -en "${next}" | cut -d'=' -f2-)
            printf "%s" "${HHS_HIGHLIGHT_COLOR}${name//alias /}${NC}"
            printf '%*.*s' 0 $((pad_len - ${#name})) "${pad}"
            echo -en "${GREEN}  ${WHITE}${expr:0:${columns}}"
          else
            echo -en "${ORANGE}${next:0:${columns}}${NC}"
          fi
          [[ "${#expr}" -ge "${columns}" ]] && echo -n "..."
          echo -e "${NC}"
        done
        IFS="${OLDIFS}"
        echo -e "${NC}"
      else
        echo -e "${ORANGE}No aliases were found in \"${HHS_ALIASES_FILE}\" !${NC}"
      fi
    elif [[ -n "${alias_name}" && -n "${alias_expr}" ]]; then
      # Add/Set one alias
      tmp_file="$(mktemp "${HHS_ALIASES_FILE}.XXXXXX")" || return 1
      awk -v alias_name="${alias_name}" \
        'index($0, "alias " alias_name "=") != 1 && $0 !~ /^[[:space:]]*$/ { print }' \
        "${HHS_ALIASES_FILE}" >"${tmp_file}"
      mv "${tmp_file}" "${HHS_ALIASES_FILE}" || return 1
      echo "alias ${alias_name}='${alias_expr}'" >>"${HHS_ALIASES_FILE}"
      echo -e "${GREEN}Alias set: ${WHITE}\"${alias_name}\" is ${HHS_HIGHLIGHT_COLOR}'${alias_expr}'${NC}"
      source "${HHS_ALIASES_FILE}"
    fi
  fi

  return 0
}
