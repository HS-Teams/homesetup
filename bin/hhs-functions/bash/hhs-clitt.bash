#!/usr/bin/env bash

#  Script: hhs-clitt.bash
# Created: May 26, 2023
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs/homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2025, HomeSetup team

# !NOTICE: Do not change this file. To customize your functions edit the file ~/.functions

# @function: Choose options from a list using a navigable menu.
# @param $1 [Req] : The response file.
# @param $2 [Req] : The render title.
# @param $3 [Req] : The array of items.
# @compatible: bash zsh
function __hhs_mchoose() {

  if [[ $# -eq 0 || "$1" == "-h" || "$1" == "--help" ]]; then
    echo "usage: ${FUNCNAME[0]} [options] <output_file> <title> <items...>"
    echo ''
    echo '    Options: '
    echo '      -c  : All options are initially checked instead of unchecked.'
    echo ''
    echo '    Arguments: '
    echo '      output_file : The output file where the result will be stored.'
    echo '            title : The text to be displayed before rendering the items.'
    echo '            items : The items to be displayed for selecting.'
    echo ''
    echo '    Examples: '
    echo '      Choose numbers from 1 to 20 (start with all options checked):'
    echo "        => ${FUNCNAME[0]} /tmp/out.txt 'Mark the desired options' {1..20} && cat /tmp/out.txt"
    echo '      Choose numbers from 1 to 20 (start with all options unchecked):'
    echo "        => ${FUNCNAME[0]} -c /tmp/out.txt 'Mark the desired options' {1..20} && cat /tmp/out.txt"
    echo ''
    echo '  Notes: '
    echo '    - A temporary file is suggested to used with this command: $ mktemp.'
    echo '    - The outfile must not exist or it be an empty file.'
    echo '    - To initialize items individually, provide items on form: name=[True|False].'
    return 1
  fi

  local outfile title all_options all_items=() all_checks=() len all_options_str all_checks_str ret_val checked=False

  [[ '-c' = "${1}" ]] && shift && checked='True'

  outfile="${1}"
  title="${2:-Please mark the desired choices}"
  shift 2
  all_options=("${@}")
  len=${#all_options[@]}

  if [[ ${len} -le 1 ]]; then
    __hhs_errcho "${FUNCNAME[0]}" "Invalid number of items: \"${len}\""
    return 1
  fi

  echo '' >"${outfile}"

  if __hhs_is_venv; then

    re_prop='^([a-zA-Z0-9_]*)=(.*)$'
    for option in "${all_options[@]}"; do
      if [[ ${option} =~ ${re_prop} ]]; then
        all_items+=("${BASH_REMATCH[1]}")
        all_checks+=("${BASH_REMATCH[2]}")
      else
        all_items+=("${option}")
        all_checks+=("${checked}")
      fi
    done

    printf -v all_options_str '%s,' "${all_items[@]}"
    all_options_str="${all_options_str%,}"
    all_options_str="${all_options_str//,/\",\"}"
    printf -v all_checks_str '%s,' "${all_checks[@]}"
    all_checks_str="${all_checks_str%,}"
    all_checks_str="${all_checks_str//on/True}"
    all_checks_str="${all_checks_str//off/False}"

    python3 -c "
from clitt.core.tui.mchoose.mchoose import mchoose
from clitt.core.tui.tui_preferences import TUIPreferences

if __name__ == \"__main__\":
  items = [\"${all_options_str}\"]
  checks = [${all_checks_str}]
  ret = mchoose(items, checks, \"${title}\", \"${outfile}\")
  exit(1 if ret is None else 0)
"
    ret_val=$?

  else
    __hhs_classic_mchoose "${outfile}" "${title}" "${all_options[@]}"
  fi

  return $ret_val
}

# @function: Select an option from a list using a navigable menu.
# @param $1 [Req] : The response file.
# @param $2 [Req] : The render title.
# @param $3 [Req] : The array of items.
# @compatible: bash zsh
function __hhs_mselect() {

  local outfile all_options=() all_options_str len

  if [[ $# -lt 3 || "$1" == "-h" || "$1" == "--help" ]]; then
    echo "usage: ${FUNCNAME[0]} <output_file> <title> <items...>"
    echo ''
    echo '    Arguments: '
    echo '      output_file : The output file where the result will be stored.'
    echo '            title : The text to be displayed before rendering the items.'
    echo '            items : The items to be displayed for selecting.'
    echo ''
    echo '    Examples: '
    echo '      Select a number from 1 to 100:'
    echo "        => ${FUNCNAME[0]} /tmp/out.txt 'Please select one option' {1..100} && cat /tmp/out.txt"
    echo ''
    echo '  Notes: '
    echo '    - If only one option is available, mselect will select it and return.'
    echo '    - A temporary file is suggested to used with this command: $ mktemp.'
    echo '    - The outfile must not exist or it be an empty file.'
    return 1
  fi

  outfile="${1}"
  title="${2:-Please selected the desired option}"
  shift 2
  all_options=("${@}")
  len=${#all_options[@]}

  [[ "${len}" -le 1 ]] && echo "${all_options[0]}" >"${outfile}" && return 0

  echo '' >"${outfile}"

  if __hhs_is_venv; then

    printf -v all_options_str '%s,' "${all_options[@]}"
    all_options_str="${all_options_str%,}"

    python3 -c """
from clitt.core.tui.mselect.mselect import mselect
from clitt.core.tui.tui_preferences import TUIPreferences

if __name__ == \"__main__\":
  it = [\"${all_options_str//,/\",\"}\"]
  ret = mselect(it, \"${title}\", \"${outfile}\")
  exit(1 if ret is None else 0)
"""

  else
    __hhs_classic_mselect "${outfile}" "${title}" "${all_options[@]}"
  fi

  return $?
}

# @function: Provide a terminal form input with simple validation.
# @param $1 [Req] : The response file.
# @param $2 [Req] : The render title.
# @param $3 [Req] : The form fields.
# @compatible: bash zsh
function __hhs_minput() {

  local outfile title all_fields=() len

  __hhs_is_venv || { __hhs_errcho "Not available when HomeSetup python venv is not active!"; return 1; }

  if [[ $# -lt 3 || "$1" == "-h" || "$1" == "--help" ]]; then
    echo "usage: ${FUNCNAME[0]} <output_file> <title> <form_fields...>"
    echo ''
    echo '    Arguments: '
    echo '      output_file : The output file where the results will be stored.'
    echo '            title : The text to be displayed before rendering the items.'
    echo '           fields : A list of form fields: Label|Mode|Type|Min/Max len|Perm|Value'
    echo ''
    echo '    Fields: '
    echo '      Field tokens (in-order): '
    echo '              <Label> => The field label. Consisting only of alphanumeric characters and under‐scores.'
    echo '               [Mode] => The input mode. One of {[text]|password|checkbox|select|masked}.'
    echo '               [Type] => The input type. One of {letters|numbers|words|masked|[anything]}.'
    echo '        [Min/Max len] => The minimum and maximum length of characters allowed. Defaults to [0/30].'
    echo '               [Perm] => The field permissions. One of {r|[rw]}. Where \"r\" for Read Only ; \"rw\" for Read & Write.'
    echo ''
    echo '    Examples: '
    echo '      Form with 4 fields (Name,Age,Password,Role,Accept Conditions): '
    echo "        => ${FUNCNAME[0]} /tmp/out.txt 'Please fill the form below:'     'Name|||5/30|rw|'     'Age|masked|masked|1/3|| ;###'     'Password|password||5|rw|'     'Role|select||4/5|rw|Admin;<User>;Guest'     'Locked||||r|locked value'     'Accept Conditions|checkbox||||' && cat /tmp/out.txt "
    echo ''
    echo '  Notes: '
    echo '    - Optional fields will assume a default value if they are not specified.'
    echo '    - A temporary file is suggested to used with this command: $ mktemp.'
    return 1
  fi

  outfile="${1}"
  title="${2:-Please fill all fields of the form below}"
  shift 2

  all_fields=("${@}")
  len=${#all_fields[*]}

  if [[ ${len} -lt 1 ]]; then
    __hhs_errcho "${FUNCNAME[0]}" "Invalid number of fields: \"${len}\""
    return 1
  fi

  echo '' >"${outfile}"

  printf -v all_fields_str '%s,' "${all_fields[@]}"
  all_fields_str="${all_fields_str%,}"

  python3 -c """
from clitt.core.tui.minput.input_validator import InputValidator
from clitt.core.tui.minput.minput import MenuInput, minput

if __name__ == \"__main__\":
  it = [\"${all_fields_str//,/\",\"}\"]
  form_fields = MenuInput.builder() \
    .from_tokenized(it) \
    .build()
  ret=minput(form_fields, \"${title}\", \"${outfile}\")
  exit(1 if ret is None else 0)
"""

  return $?
}

# @function: PUNCH-THE-CLOCK. This is a helper tool to aid with the timesheet.
# @param $1 [Con] : The week list punches from.
# @compatible: bash zsh
function __hhs_punch() {

  __hhs_is_venv || { __hhs_errcho "${FUNCNAME[0]}" "Not available when HomeSetup python venv is not active!"; return 1; }

  if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    echo "usage: ${FUNCNAME[0]} [options] <args>"
    echo ''
    echo '    Options: '
    echo '      -l | --list       : List all registered punches.'
    echo '      -e | --edit       : Edit current punch file.'
    echo '      -r | --reset      : Reset punches for the current week and save the previous one.'
    echo '      -w | --week <num> : Report (list) all punches of specified week using the pattern: week-N.punch.'
    echo ''
    echo '  Notes: '
    echo '    When no arguments are provided it will !!PUNCH THE CLOCK!!.'
    return 1
  else
    if [[ "-l" == "${1}" || "--list" == "${1}" ]]; then
      python3 -m clitt widgets punch list
    elif [[ "-e" == "${1}" || "--edit" == "${1}" ]]; then
      python3 -m clitt widgets punch edit
    elif [[ "-r" == "${1}" || "--reset" == "${1}" ]]; then
      python3 -m clitt widgets punch reset
    elif [[ "-w" == "${1}" || "--week" == "${1}" ]]; then
      python3 -m clitt widgets punch week "${2}"
    else
      python3 -m clitt widgets punch
    fi
  fi

  return $?
}
