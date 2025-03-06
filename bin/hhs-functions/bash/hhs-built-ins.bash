#!/usr/bin/env bash

#  Script: hhs-built-ins.bash
# Created: Oct 6, 2019
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs/homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2025, HomeSetup team

# !NOTICE: Do not change this file. To customize your functions edit the file ~/.functions

# @function: Generate a random number int the range <min> <max> (all limits included).
# @param $1 [Req] : The minimum range of the number.
# @param $2 [Req] : The maximum range of the number.
function __hhs_random() {

  if [[ $# -ne 2 ]]; then
    echo "usage: ${FUNCNAME[0]} <min> <max>"
    return 1
  else
    echo "$((RANDOM % ($2 - $1 + 1) + $1))"
  fi

  return 0
}

# @function: Open a file or URL with the default program.
# @param $1 [Req] : The url or filename to open.
function __hhs_open() {

  local filename="$1"

  if __hhs_has open && \open "${filename}"; then
    return $?
  elif __hhs_has xdg-open && \xdg-open "${filename}"; then
    return $?
  elif __hhs_has vim && \vim "${filename}"; then
    return $?
  elif __hhs_has vi && \vi "${filename}"; then
    return $?
  else
    __hhs_errcho "${FUNCNAME[0]}" "Unable to open \"${filename}\". No suitable application found !"
  fi

  return 1
}

# @function: Create and/or open a file using the default editor.
# @param $1 [Req] : The file path.
function __hhs_edit() {

  local filename="$1" editor="${EDITOR:-vi}"

  if [[ $# -le 0 || "$1" == "-h" || "$1" == "--help" ]]; then
    echo "usage: ${FUNCNAME[0]} <file_path>"
    return 1
  else
    [[ -s "${filename}" ]] || touch "${filename}" > /dev/null 2>&1
    [[ -s "${filename}" ]] || __hhs_errcho "${FUNCNAME[0]}" "Unable to create file \"${filename}\""

    if [[ -n "${editor}" ]] && __hhs_has "${editor}" && ${editor} "${filename}"; then
      return $?
    elif __hhs_has gedit && \gedit "${filename}"; then
      return $?
    elif __hhs_has emacs && \emacs "${filename}"; then
      return $?
    elif __hhs_has vim && \vim "${filename}"; then
      return $?
    elif __hhs_has vi && \vi "${filename}"; then
      return $?
    elif __hhs_has cat && \cat > "${filename}"; then
      return $?
    else
      __hhs_errcho "${FUNCNAME[0]}" "Unable to find a suitable editor for the file \"${filename}\" !"
    fi
  fi

  return 1
}

# shellcheck disable=SC2030,SC2031
# @function: Display information about the given command.
# @param $1 [Req] : The command to check.
function __hhs_about() {

  local cmd type_ret=() re_alias re_function re_command recurse="${2}"
  re_alias="(.*) is aliased to \`(.*)'"
  re_function="(.*) is a function"
  re_command="(.*) is (.*)"

  if [[ $# -eq 0 || "$1" == "-h" || "$1" == "--help" ]]; then
    echo "usage: ${FUNCNAME[0]} <command>"
    return 1
  elif [[ ${recurse} -gt 5 ]] || [[ ${recurse} =~ [^0-9]+ ]]; then
    return 1
  else
    [[ ${recurse} -eq 0 ]] && echo ''
    cmd=${1}
    IFS=$'\n'
    read -r -d '' -a type_ret < <(type "${cmd}" 2> /dev/null)
    IFS="${OLDIFS}"
    if [[ ${#type_ret[@]} -gt 0 ]]; then
      if [[ ${type_ret[0]} =~ ${re_alias} ]]; then
        printf "${GREEN}%14s${BLUE} %s${WHITE} => %s ${NC}\n" "Aliased:" "${BASH_REMATCH[1]}" "${BASH_REMATCH[2]}"
        # To avoid unalias the command, we do that in another subshell
        (
          IFS=$'\n'
          if [[ "${BASH_REMATCH[2]}" == *"__hhs_"* ]]; then
            ((recurse += 1))
            __hhs_about "${BASH_REMATCH[2]}" "${recurse}"
          else
            while unalias "${cmd}" 2> /dev/null; do
              ((recurse += 1))
              __hhs_about "${cmd}" "${recurse}"
            done
          fi
          IFS="${OLDIFS}"
        )
      elif [[ ${type_ret[0]} =~ ${re_function} ]]; then
        printf "${GREEN}%14s${BLUE} %s${WHITE} => \n" "Function:" "${BASH_REMATCH[1]}"
        printf "%s\n" "${type_ret[@]:2}" | nl
      elif [[ ${type_ret[0]} =~ ${re_command} ]]; then
        printf "${GREEN}%14s${BLUE} %s${WHITE} => %s ${NC}\n" "Command:" "${BASH_REMATCH[1]}" "${BASH_REMATCH[2]}"
        brew_cmd="$(brew --prefix "${cmd}" 2>/dev/null)"
        [[ -n "${brew_cmd}" ]] && printf "${GREEN}%14s${BLUE} %s${WHITE} => %s\n" "Brew:" "prefix" "${brew_cmd}"
      fi
    fi
    [[ ${recurse} -eq 0 ]] && echo -e "${NC}"
  fi

  return 0
}

# @function: Display all alias definitions using filter.
# @param $1 [Opt] : If -e is present, edit the .aliasdef file, otherwise a case-insensitive filter to be used when listing.
function __hhs_defs() {

  local pad pad_len filter name value columns ret_val=0 next

  HHS_ALIASDEF_FILE="${HHS_DIR}/.aliasdef"

  if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    echo "usage: ${FUNCNAME[0]} [regex_filters]"
    return 1
  else
    if [[ "$1" == '-e' ]]; then
      __hhs_edit "${HHS_ALIASDEF_FILE}"
      ret_val=$?
    else
      pad=$(printf '%0.1s' "."{1..30})
      pad_len=26
      columns="$(($(tput cols) - pad_len - 10))"
      filter="$*"
      filter=${filter// /\|}
      [[ -z "${filter}" ]] && filter=".*"
      echo -e "\n${YELLOW}Listing all alias definitions matching [${filter}]:\n"
      IFS=$'\n'
      for next in $(grep -i '^ *__hhs_alias' "${HHS_ALIASDEF_FILE}" | sed 's/^ *//g' | sort | uniq); do
        name=${next%%=*}
        name="$(trim <<< "${name}" | awk '{print $2}')"
        value=${next#*=}
        value=${value//[\'\"]/}
        if [[ ${name} =~ ${filter} ]]; then
          echo -en "${HHS_HIGHLIGHT_COLOR}${name//__hhs_alias/}${NC} "
          printf '%*.*s' 0 $((pad_len - ${#name})) "${pad}"
          echo -en "${GREEN} defined as => ${NC}"
          echo -n "${value:0:${columns}}"
          [[ ${#value} -ge ${columns} ]] && echo -n "..."
          echo "${NC}"
        fi
      done
      IFS="${OLDIFS}"
      echo ' '
    fi
  fi

  return ${ret_val}
}

# @function: Display all environment variables using filter.
# @param $1 [Opt] : If -e is present, edit the env file, otherwise a case-insensitive filter to be used when listing.
function __hhs_envs() {

  local pad pad_len filter name value ret_val=0 columns col_offset=8 env_var

  HHS_ENV_FILE=${HHS_ENV_FILE:-$HHS_DIR/.env}

  touch "${HHS_ENV_FILE}"

  if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    echo "usage: ${FUNCNAME[0]} [options] [regex_filters]"
    echo ''
    echo '    Options: '
    echo '      -e : Edit current HHS_ENV_FILE.'
    return 1
  else
    if [[ "$1" == '-e' ]]; then
      __hhs_edit "${HHS_ENV_FILE}"
      ret_val=$?
    else
      pad=$(printf '%0.1s' "."{1..60})
      pad_len=40
      columns="$(($(tput cols) - pad_len - col_offset))"
      filter="$*"
      filter=${filter// /\|}
      [[ -z "${filter}" ]] && filter=".*"
      echo ' '
      echo -e "${YELLOW}Listing all exported environment variables matching [ ${filter} ]:${NC}"
      echo ' '
      IFS=$'\n'
      \shopt -s nocasematch
      for env_var in $(env | sort); do
        if [[ $env_var =~ ^([a-zA-Z0-9_]+)=(.*) ]]; then
          name=${BASH_REMATCH[1]}
          value=${BASH_REMATCH[2]}
          if [[ ${name} =~ ${filter} ]]; then
            echo -en "${HHS_HIGHLIGHT_COLOR}${name}${NC} "
            printf '%*.*s' 0 $((pad_len - ${#name})) "${pad}"
            echo -en " ${GREEN}=> ${NC}${value:0:${columns}}"
            [[ ${#value} -ge ${columns} ]] && echo -n "..."
            echo -e "${NC}"
          fi
        fi
      done
      IFS="${OLDIFS}"
      \shopt -u nocasematch
      echo ' '
    fi
  fi

  return ${ret_val}
}

# @function: Activate/Deactivate the HomeSetup python venv.
function __hhs_venv() {

  local ret_val=1 enable="${1}" active

  if [[ '-h' == "${enable}" || '--help' == "${enable}" ]]; then
    echo "usage: ${FUNCNAME[0]} [-a|-d|-t]"
    echo ''
    echo '    Options: '
    echo '      -a | --activate     : Makes the venv active.'
    echo '      -d | --deactivate   : Makes the venv inactive.'
    echo '      -t | --toggle       : Toggles the venv between active/inactive.'
    echo ''
    echo '  Notes: '
    echo '    - if no option is specified, it will check whether it is active/inactive.'
    return 1
  fi

  active="$(__hhs_is_venv && echo -e "${GREEN}Active")"
  active="${active:-${RED}Inactive}"

  [[ -z "${enable}" ]] && { echo -e "${WHITE}Virtual environment is ${active} ${YELLOW}[$(python3 -V)] -> $(command -v python3)."; return 0; }

  if [[ "${enable}" =~ -d|-t ]] && declare -F deactivate &> /dev/null; then
    deactivate && \
      { echo -e "${WHITE}Virtual environment ${RED}deactivated ${YELLOW}[$(python3 -V)] -> $(command -v python3)."; ret_val=0; }
  elif [[ "${enable}" =~ -a|-t ]] && ! declare -F deactivate &> /dev/null; then
    source "${HHS_VENV_PATH}"/bin/activate &> /dev/null && \
      { echo "${WHITE}Virtual environment ${GREEN}activated ${YELLOW}[$(python3 -V)] -> $(command -v python3)."; ret_val=0; }
  else
    echo -e "${WHITE}Virtual environment is ${active} ${YELLOW}[$(python3 -V)] -> $(command -v python3)."
  fi

  echo -e "${NC}"
  # shellcheck disable=SC2155
  export HHS_PYTHON_VENV_ACTIVE="$(__hhs_is_venv && echo '1')"
  setting="hhs_python_venv_enabled"
  [[ ${HHS_PYTHON_VENV_ACTIVE} -eq 1 ]] && value='true' || value='false'

  if ! __hhs_toml_set "${HHS_SETUP_FILE}" "${setting}=${value}" "setup"; then
    __hhs_errcho "${FUNCNAME[0]}" "Unable to change setting: ${setting}!"
    return 1
  fi

  __hhs_restart__

  return $ret_val
}
