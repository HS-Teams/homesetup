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

# @function: Display statistics about commands in history (aligned + dotted padding)
# @param $1 [Opt] : Limit to the top N commands.
function __hhs_hist_stats() {
  local top_n=${1:-10} width=${2:-30} i=1
  local cmd_name cmd_qty hist_output bar_len bar columns pad_len pad max_size

  if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    echo "usage: ${FUNCNAME[0]} [top_N]"
    return 0
  fi

  # Generic parser – handles user/date/timestamped history formats
  hist_output="$(
    history |
      sed -E 's/^\[[^]]*\][[:space:]]*//' |             # remove [user,date,...]
      sed -E 's/^[[:space:]]*[0-9]+\**[[:space:]]*//' | # remove numeric ids
      awk '{
        for (i=1; i<=NF; i++) {
          t=$i
          if (t ~ /^[0-9]{4}-[0-9]{2}-[0-9]{2}$/) continue
          if (t ~ /^[0-9]{2}:[0-9]{2}:[0-9]{2}$/) continue
          if (t ~ /^([0-9]{4}-[0-9]{2}-[0-9]{2})[T ]([0-9]{2}:[0-9]{2}:[0-9]{2})$/) continue
          if (t ~ /^[0-9]{1,4}$/) continue
          if (t ~ /^[[:punct:]]+$/) continue
          if (t ~ /^[[:alnum:]_.\/:+-]+$/) { CMD[t]++; break }
        }
      }
      END { for (c in CMD) print CMD[c], c }' |
      sort -nr
  )"

  [[ -z "${hist_output}" ]] && {
    __hhs_errcho "${FUNCNAME[0]}" "No valid command tokens found in history."
    return 1
  }

  columns=80
  pad_len=$((columns / 2))
  pad=$(printf '%0.1s' "."{1..80})

  max_size=$(echo "${hist_output}" | head -n 1 | awk '{print $1}')
  [[ -z "${max_size}" || "${max_size}" -le 0 ]] && max_size=1

  echo ''
  echo "${YELLOW}Top ${top_n} used commands in history:${NC}"
  echo ''

  while read -r cmd_qty cmd_name; do
    [[ -z "${cmd_qty}" || -z "${cmd_name}" ]] && continue

    bar_len=$(((cmd_qty * width) / max_size))
    ((bar_len < 1)) && bar_len=1

    if __hhs_has seq; then
      bar=$(printf '▄%.0s' $(seq 1 "${bar_len}"))
    elif __hhs_has jot; then
      bar=$(printf '▄%.0s' "$(jot - 1 "${bar_len}")")
    else
      __hhs_errcho "${FUNCNAME[0]}" "Neither seq nor jot is available."
      return 1
    fi

    # Trim overly long names
    [[ ${#cmd_name} -gt $((columns - 20)) ]] && cmd_name="${cmd_name:0:$((columns - 20))}…"

    # Command label + dotted pad + count + bar
    printf "${WHITE}%3d: ${HHS_HIGHLIGHT_COLOR} %s" "${i}" "${cmd_name}"
    printf '%*.*s' 0 $((pad_len - ${#cmd_name})) "${pad}"
    printf "${GREEN}%4d ${ORANGE}|%s${NC}\n" "${cmd_qty}" "${bar}"

    ((i += 1))
  done < <(echo "${hist_output}" | head -n "${top_n}")

  echo ''
  echo "${NC}"
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
      __hhs_toml_set "${HHS_SHOPTS_FILE}" "${option}=${enable}" && {
        echo -e "${WHITE}Shell option ${CYAN}${option}${WHITE} set to ${color:-${GREEN}}${enable} ${NC}"
        return 0
      }
    fi
  else
    \shopt "${@}" 2>/dev/null && return 0
    [[ "${enable}" == '-q' ]] && return 1
    __hhs_errcho "${FUNCNAME[0]}" "${enable}: invalid shell option"
  fi

  return 1
}

# @function: Display 'du' output formatted as a horizontal bar chart (auto unit scaling).
# @param $1 [Opt] : Directory path (default: current directory)
# @param $2 [Opt] : Number of top entries to display (default: 10)
# @param $3 [Opt] : Chart bar width scaling factor (default: 30)
function __hhs_du() {
  local dir="${1:-.}"
  local top_n=${2:-10}
  local width=${3:-30}
  local i=1 du_output columns pad_len pad max_val bar_len bar path entry_count
  local size_human size_kib

  if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    echo "usage: ${FUNCNAME[0]} [path] [top_N] [width]"
    return 0
  fi

  [[ ! -d "${dir}" ]] && {
    __hhs_errcho "${FUNCNAME[0]}" "Directory not found: \"${dir}\""
    return 1
  }

  # Collect du output (human readable)
  if [[ "$(uname -s)" == "Darwin" ]]; then
    du_output="$(\du -hd 1 "${dir}" 2>/dev/null | grep -v 'total' | sort -hr)"
  else
    du_output="$(\du -h --max-depth=1 "${dir}" 2>/dev/null | grep -v 'total' | sort -hr)"
  fi

  entry_count=$(echo "${du_output}" | wc -l | tr -d '[:space:]')
  [[ "${entry_count}" -eq 0 ]] && {
    __hhs_errcho "${FUNCNAME[0]}" "No usable entries found in: \"${dir}\""
    return 1
  }

  du_output=$(echo "${du_output}" | head -n "${top_n}")

  columns=80
  pad_len=$((columns / 2))
  pad=$(printf '%0.1s' "."{1..80})

  # Compute max size in KiB for bar scaling
  max_val=$(echo "${du_output}" | awk '
  function to_kib(v) {
    unit=tolower(substr(v, length(v)))
    val=substr(v, 1, length(v)-1)
    if (unit=="g") return int(val*1024*1024)
    if (unit=="m") return int(val*1024)
    if (unit=="k") return int(val)
    if (unit=="b") return int(val/1024)
    return int(v)
  }
  {print to_kib($1)}' | sort -n | tail -1)
  [[ -z "${max_val}" || "${max_val}" -le 0 ]] && max_val=1

  echo ''
  echo "${YELLOW}Top ${top_n} disk usage at: ${BLUE}\"${dir//\./$(pwd)}\"${NC}"
  echo ''

  while read -r size_human path; do
    [[ -z "${size_human}" || -z "${path}" ]] && continue

    # Convert to KiB for scaling
    size_kib=$(awk -v v="${size_human}" '
      function to_kib(x) {
        unit=tolower(substr(x, length(x)))
        val=substr(x, 1, length(x)-1)
        if (unit=="g") return int(val*1024*1024)
        if (unit=="m") return int(val*1024)
        if (unit=="k") return int(val)
        if (unit=="b") return int(val/1024)
        return int(x)
      }
      BEGIN { print to_kib(v) }')

    # Normalize path
    [[ "${path}" == '.' ]] && continue

    path="${path//\.\//}"
    path="${path//\/\//\/}"


    bar_len=$(((size_kib * width) / max_val))
    ((bar_len < 1)) && bar_len=1

    if __hhs_has seq; then
      bar=$(printf '▄%.0s' $(seq 1 "${bar_len}"))
    elif __hhs_has jot; then
      bar=$(printf '▄%.0s' "$(jot - 1 "${bar_len}")")
    else
      __hhs_errcho "${FUNCNAME[0]}" "Neither seq nor jot is available."
      return 1
    fi

    # Safe truncation for narrow terminals
    local max_label_width=$((columns - 30))
    ((max_label_width < 10)) && max_label_width=10
    [[ ${#path} -gt ${max_label_width} ]] && path="${path:0:${max_label_width}}…"

    printf "${WHITE}%3d: ${HHS_HIGHLIGHT_COLOR} " "${i}"
    printf "%s" "${path}"
    printf '%*.*s' 0 $((pad_len - ${#path})) "${pad}"
    printf "${GREEN}%8s ${ORANGE}|%s${NC}\n" "${size_human}" "${bar}"

    ((i += 1))
  done <<<"${du_output}"

  echo ''
  echo "${WHITE}Total: ${ORANGE}$(\du -sh "${dir}" 2>/dev/null | awk '{print $1}')${NC}"
  echo ''
}
