#!/usr/bin/env bash

#  Script: hhs-shell-utils.bash
# Created: Oct 5, 2019
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs/homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2025, HomeSetup team

# !NOTICE: Do not change this file. To customize your functions edit the file ~/.functions

# @function: Search for previously issued commands from history using filter.
# @param $1 [Req] : The case-insensitive filter to be used when listing.
function __hhs_history() {

  if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    echo "usage: ${FUNCNAME[0]} [regex_filter]"
    return 1
  fi
  echo ''
  if [[ "$#" -eq 0 ]]; then
    history | sort -k2 -k 1,1nr | uniq -f 1 | sort -n | __hhs_highlight -i "^ *[0-9]*  "
  else
    history | sort -k2 -k 1,1nr | uniq -f 1 | sort -n | __hhs_highlight -i "${*}"
  fi

  return $?
}

# inspiRED by https://superuser.com/questions/250227/how-do-i-see-what-my-most-used-linux-command-are
# @function: Display statistics about commands in history.
# @param $1 [Opt] : Limit to the top N commands.
function __hhs_hist_stats() {

  local top_n=${1:-10} width=${2:-30} i=1 cmd_name cmd_qty hist_output bar_len bar columns pad_len pad

  if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    echo "usage: ${FUNCNAME[0]} [top_N]"
    return 1
  fi

  hist_output="$(history | tr -s ' ' | cut -d ' ' -f6 | sort | uniq -c | sort -nr)"

  columns=$(tput cols)
  pad=$(printf '%0.1s' "."{1..41})
  pad_len=41
  max_size=$(echo "${hist_output}" | head -n 1 | awk '{print $1}')

  echo ' '
  echo "${YELLOW}Top ${top_n} used commands in history:"
  echo ' '

  hist_output="$(echo "${hist_output}" | head -n "${top_n}")"

  echo "${hist_output}" | while read -r line; do
    if [[ "${line}" =~ ^[[:space:]]*([0-9]+)[[:space:]]*([a-zA-Z0-9]+)$ ]]; then

      cmd_qty="${BASH_REMATCH[1]}"
      cmd_name="${BASH_REMATCH[2]}"
      cmd_name="${cmd_name:0:$columns}"

      bar_len=$(((cmd_qty * width) / max_size))
      [[ $bar_len -gt 0 && $bar_len -lt 2 ]] && bar_len=2

      if __hhs_has seq; then
        bar=$(printf '▄%.0s' $(seq 1 "${bar_len}"))
      elif __hhs_has jot; then
        bar=$(printf '▄%.0s' "$(jot - 1 "${bar_len}")")
      else
        __hhs_errcho "${FUNCNAME[0]}" "Neither seq nor jot is available."
        return 1
      fi

      printf "${WHITE}%3d: ${HHS_HIGHLIGHT_COLOR} " "${i}"
      printf "%s " "${cmd_name}"
      [[ "${#cmd_name}" -ge "${columns}" ]] && echo -en "${NC}" || echo -en "${NC}"
      printf '%*.*s' 0 $((pad_len - ${#cmd_name})) "${pad}"
      printf "${GREEN}%3d ${ORANGE}|%s\n" "${cmd_qty}" "${bar}"
      ((i += 1))
    fi
  done

  IFS="${OLDIFS}"
  echo "${NC}"

  return 0
}

# @function: Display the current dir (pwd) and remote repo url, if it applies.
# @param $1 [Req] : The command to get help.
function __hhs_where_am_i() {
  local pad_len=24 last_commit sha commit_msg repo_url branch_name metrics current_dir
  local os
  os="$(uname)"

  if [[ -n "$1" ]] && __hhs_has "$1"; then
    __hhs_has 'tldr' && tldr --list | grep -w "$1" && {
      tldr "$1"
    }
    __hhs help "$1" 2>/dev/null || __hhs_about "$1"
    return $?
  fi

  echo " "
  echo "${YELLOW}-=- You are here -=-${NC}"
  echo " "

  if [[ ${HHS_PYTHON_VENV_ACTIVE:-0} -eq 1 ]]; then
    printf "${WHITE}%${pad_len}s ${HHS_HIGHLIGHT_COLOR}%s %s\n${NC}" \
      "Virtual Environment:" "$(python -V 2>&1)" "=>${BLUE} ${HHS_VENV_PATH}"
  fi

  if [[ "$os" == "Darwin" ]]; then
    current_dir=$(pwd -P)
  else
    current_dir=$(pwd -LP)
  fi
  printf "${WHITE}%${pad_len}s ${HHS_HIGHLIGHT_COLOR}%s\n${NC}" "Current directory:" "${current_dir}"

  if __hhs_has git && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    repo_url="$(git remote -v | head -n 1 | awk '{print $2}')"
    printf "${WHITE}%${pad_len}s ${HHS_HIGHLIGHT_COLOR}%s\n${NC}" "Remote repository:" "${repo_url}"
    last_commit=$(git log --oneline -n 1)
    sha="$(echo "${last_commit}" | awk '{print $1}')"
    commit_msg="$(echo "${last_commit}" | cut -d' ' -f2-)"
    branch_name="$(git rev-parse --abbrev-ref HEAD)"
    printf "${WHITE}%${pad_len}s ${HHS_HIGHLIGHT_COLOR}%s %s\n${NC}" "Last commit sha:" "${sha}" "${commit_msg}"
    printf "${WHITE}%${pad_len}s ${HHS_HIGHLIGHT_COLOR}%s" "Branch:" " ${branch_name}"
    metrics=$(git diff --shortstat)
    [[ -n "${metrics}" ]] && echo -e " =>${BLUE}${metrics}${NC}"
    echo ""
  fi

  return 0
}

# @function: Select a shell from the existing shell list.
function __hhs_shell_select() {

  local ret_val=1 sel_shell mselect_file avail_shells=()

  if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    echo "usage: ${FUNCNAME[0]} "
  else
    read -d '' -r -a avail_shells <<<"$(grep '/.*' '/etc/shells')"
    if __hhs_has brew; then
      echo "${BLUE}Checking: HomeBrew's shells...${NC}"
      for next_sh in "${avail_shells[@]}"; do
        next_sh_app="$(basename "${next_sh}")"
        next_brew_sh="$(brew --prefix "${next_sh_app}" 2>/dev/null)"
        [[ -n "${next_brew_sh}" ]] && avail_shells+=("${next_brew_sh}/bin/${next_sh_app}")
      done
    fi
    mselect_file=$(mktemp)
    if __hhs_mselect "${mselect_file}" "Please select your default shell:" "${avail_shells[@]}"; then
      sel_shell=$(grep . "${mselect_file}")
      if [[ -n "${sel_shell}" && -f "${sel_shell}" ]]; then
        if \chsh -s "${sel_shell}"; then
          ret_val=0
          clear
          echo "${GREEN}Your default shell has changed to => '${sel_shell}'"
          echo "${ORANGE}Next time you open a terminal window you will use \"${sel_shell}\" as your default shell"
        else
          __hhs_errcho "${FUNCNAME[0]}" "Unable to change shell to ${sel_shell}. \n\n${YELLOW}${TIP_ICON} Tip: Try adding it to /etc/shells and try again!${NC}"
        fi
        [[ -f "${mselect_file}" ]] && \rm -f "${mselect_file}"
      fi
    fi
    echo -e "${NC}"
  fi

  return ${ret_val}
}

# @function: Display/Set/unset current Shell Options.
# @param $1 [Req] : Same as shopt, ref: https://ss64.com/bash/shopt.html
function __hhs_shopt() {

  local shell_options option enable color

  enable=$(tr '[:upper:]' '[:lower:]' <<<"${1}")
  option="${2}"

  if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    echo "usage: ${FUNCNAME[0]} [on|off] | [-pqsu] [-o] [optname ...]"
    echo ''
    echo '    Options:'
    echo '      off : Display all unset options.'
    echo '      on  : Display all set options.'
    echo '      -s  : Enable (set) each optname.'
    echo '      -u  : Disable (unset) each optname.'
    echo '      -p  : Display a list of all settable options, with an indication of whether or not each is set.'
    echo '            The output is displayed in a form that can be reused as input. (-p is the default action).'
    echo '      -q  : Suppresses normal output; the return status indicates whether the optname is set or unset.'
    echo "            If multiple optname arguments are given with '-q', the return status is zero if all optnames"
    echo '            are enabled; non-zero otherwise.'
    echo "      -o  : Restricts the values of optname to be those defined for the '-o' option to the set builtin."
    echo ''
    echo '  Notes:'
    echo '    If no option is provided, then, display all set & unset options.'
  elif [[ ${#} -eq 0 || ${enable} =~ on|off|-p ]]; then
    IFS=$'\n' read -r -d '' -a shell_options < <(\shopt | awk '{print $1"="$2}')
    IFS="${OLDIFS}"
    echo ' '
    echo "${YELLOW}Available shell ${enable:-on and off} options (${#shell_options[@]}):"
    echo ' '
    for option in "${shell_options[@]}"; do
      if [[ "${option#*=}" == 'on' ]] && [[ -z "${enable}" || "${enable}" =~ on|-p ]]; then
        echo -e "  ${WHITE}${ON_SWITCH_ICN}  ${GREEN} ON${BLUE}\t${option%%=*}"
      elif [[ "${option#*=}" == 'off' ]] && [[ -z "${enable}" || "${enable}" =~ off|-p ]]; then
        echo -e "  ${WHITE}${OFF_SWITCH_ICN}  ${RED} OFF${BLUE}\t${option%%=*}"
      fi
    done
    echo "${NC}"
    return 0
  elif [[ ${#} -ge 1 && ${enable} =~ -(s|u) ]]; then
    [[ -z "${option}" ]] && return 1
    if \shopt "${enable}" "${option}"; then
      read -r option enable < <(\shopt "${option}" | awk '{print $1, $2}')
      [[ 'off' == "${enable}" ]] && color="${RED}"
      __hhs_toml_set "${HHS_SHOPTS_FILE}" "${option}=${enable}" &&
        {
          echo -e "${WHITE}Shell option ${CYAN}${option}${WHITE} set to ${color:-${GREEN}}${enable} ${NC}"
          return 0
        }
    fi
  else
    \shopt "${@}" 2>/dev/null && return 0
    [[ "${enable}" == '-q' ]] && return 1
    __hhs_errcho "${FUNCNAME[0]}" "${enable}: invalid option"
  fi

  return 1
}

# @function: Display 'du' output formatted as a horizontal bar chart.
# @param $1 [Opt] : Directory path (default: current directory)
# @param $2 [Opt] : Number of top entries to display (default: 10)
function __hhs_du() {
  local dir="${1:-.}" i=1 top_n=${2:-10} width=${3:-30} max_size du_output columns pad_len pad bar_len bar path

  if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    echo "usage: ${FUNCNAME[0]} [path] [top_N]"
    return 1
  fi

  [[ ! -d "${dir}" ]] && {
    __hhs_errcho "${FUNCNAME[0]}" "Directory not found: \"${dir}\""
    return 1
  }

  if [[ "$(uname -s)" == "Darwin" ]]; then
    du_output="$(\du -hkd 1 "${dir}" 2>/dev/null | sort -rn | head -n "$((top_n + 1))")"
  else
    du_output="$(\du -hk --max-depth=1 "${dir}" 2>/dev/null | sort -rn | head -n "$((top_n + 1))")"
  fi

  columns=$(tput cols)
  pad_len=60
  pad=$(printf '%0.1s' "."{1..60})
  max_size=$(echo "${du_output}" | awk '{print $1}' | sort -n | awk '{
  a[NR]=$1
  } END {
    idx = int(NR * 0.9)
    if (idx < 1) idx = 1
    print a[idx]
  }')

  echo ' '
  echo "${YELLOW}Top ${top_n} disk usage at: ${BLUE}\"${dir//\./$(pwd)}\""
  echo ' '

  while read -r size path; do
    size=$(echo "${size}" | tr -d '[:space:]')
    [[ -z "${size}" || -z "${path}" || "${path}" == '.' || "${path}" == 'total' ]] && continue
    bar_len=$(((size * width) / max_size))
    [[ $bar_len -gt 0 && $bar_len -lt 2 ]] && bar_len=2

    if [[ $bar_len -gt 0 ]]; then
      if __hhs_has seq; then
        bar=$(printf '▄%.0s' $(seq 1 "${bar_len}"))
      elif __hhs_has jot; then
        bar=$(printf '▄%.0s' "$(jot - 1 "${bar_len}")")
      else
        __hhs_errcho "${FUNCNAME[0]}" "Neither seq nor jot is available."
        return 1
      fi
    fi

    path="${path//\.\//}"
    path="${path//\/\//\/}"
    path="${path:0:$columns}"

    printf "${WHITE}%3d: ${HHS_HIGHLIGHT_COLOR} " "${i}"
    printf "%s" "${path}"
    printf '%*.*s' 0 $((pad_len - ${#path})) "${pad}"
    [[ "${#path}" -ge "${columns}" ]] && echo -en "${NC}" || echo -en "${NC}"
    printf "${GREEN}%$((${#max_size} + 1))d KB ${ORANGE}|%s \n" " ${size}" "${bar}"
    ((i += 1))
  done <<<"${du_output}"

  echo ''
  echo "${WHITE}Total: ${ORANGE}$(\du -hc "${dir}" | grep total | cut -f1)"
  unset TOTAL

  echo "${NC}"
}
