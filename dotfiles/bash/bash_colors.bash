#!/usr/bin/env bash
# shellcheck disable=SC1117

#  Script: bash_colors.bash
# Purpose: This file is used to configure shell colors
# Created: Aug 26, 2018
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs/homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2025, HomeSetup team

# !NOTICE: Do not change this file. To customize your bash colors edit the file ~/.colors
# inspiRED by: https://github.com/mathiasbynens/dotfiles
# improved with: https://misc.flogisoft.com/bash/tip_colors_and_formatting

# Do not source this file multiple times
if list_contains "${HHS_ACTIVE_DOTFILES}" "bash_colors"; then
  __hhs_log "DEBUG" "${0} was already loaded!"
else

  export HHS_ACTIVE_DOTFILES="${HHS_ACTIVE_DOTFILES} bash_colors"

  # Detect which `ls` flavor is in use
  # LS_Colors builder: https://geoff.greer.fm/lscolors/
  # Items:
  #   di: Directory      bd: Block special
  #   ln: Link           cd: Char special
  #   so: Socket         su: Exe setuid
  #   pi: Pipe           sg: Exe setgid
  #   ex: Executable     tw: Dir. write others(sticky)
  #                      ow: Dir. write others(no-sticky)

  if ls --color &> /dev/null; then # GNU `ls`
    export COLOR_FLAG="--color"
    export LS_COLORS='di=1;34:ln=1;36:so=35:pi=33:ex=1;32:bd=34;46:cd=34;43:su=30;41:sg=30;46:tw=30;42:ow=30;43'
  else # macOS `ls`
    export COLOR_FLAG="-G"
    export CLICOLOR=1
    export LSCOLORS='ExGxfxdxCxegedabagacad'
  fi

  color_cache_term="${TERM//[^a-zA-Z0-9_.-]/_}"
  color_cache_file="${HHS_CACHE_DIR}/terminal-colors-v1-${color_cache_term:-unknown}.bash"
  color_cache_loaded=0

  if [[ -s "${color_cache_file}" ]] && __hhs_source "${color_cache_file}"; then
    color_cache_loaded=1
  fi

  if [[ ${color_cache_loaded} -ne 1 ]]; then
    if tput setaf 1 &>/dev/null; then
      # Solarized colors, taken from http://git.io/solarized-colors.
      NC=$(tput sgr0)
      BLACK=$(tput setaf 0)
      RED=$(tput setaf 124)
      GREEN=$(tput setaf 64)
      ORANGE=$(tput setaf 166)
      BLUE=$(tput setaf 33)
      PURPLE=$(tput setaf 61)
      CYAN=$(tput setaf 37)
      GRAY=$(tput setaf 235)
      WHITE=$(tput setaf 15)
      YELLOW=$(tput setaf 136)
      VIOLET=$(tput setaf 125)
      STRIKE=
      __hhs_log "DEBUG" "Bash colors loaded using 'tput'"
    else
      # VT100 ANSI colors, taken from https://misc.flogisoft.com/bash/tip_colors_and_formatting
      NC='\033[0;0;0m'
      BLACK='\033[0;30m'
      RED='\033[0;31m'
      GREEN='\033[0;32m'
      BLUE='\033[0;34m'
      PURPLE='\033[0;35m'
      CYAN='\033[0;36m'
      ORANGE='\033[38;5;202m'
      GRAY='\033[38;5;8m'
      WHITE='\033[0;97m'
      YELLOW='\033[0;93m'
      VIOLET='\033[0;95m'
      STRIKE='\033[9m'
      __hhs_log "DEBUG" "Bash colors loaded using 'Esc['"
    fi

    color_cache_tmp="${color_cache_file}.${BASHPID:-$$}.tmp"
    (
      umask 077
      for color_name in NC BLACK RED GREEN ORANGE BLUE PURPLE CYAN GRAY WHITE YELLOW VIOLET STRIKE; do
        printf 'export %s=%q\n' "${color_name}" "${!color_name}"
      done >"${color_cache_tmp}"
    ) && \mv -f "${color_cache_tmp}" "${color_cache_file}"
    \rm -f "${color_cache_tmp}"
  fi

  export NC BLACK RED GREEN ORANGE BLUE PURPLE CYAN GRAY WHITE YELLOW VIOLET STRIKE
  unset color_cache_file color_cache_loaded color_cache_term color_cache_tmp color_name

  # Color used to highlight text: Default is CYAN
  export HHS_HIGHLIGHT_COLOR=${HHS_HIGHLIGHT_COLOR:-${CYAN}}

fi
