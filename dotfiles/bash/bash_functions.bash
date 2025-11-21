#!/usr/bin/env bash
# shellcheck disable=SC1090

#  Script: bash_functions.bash
# Purpose: This file is used to define some shell tools
# Created: Aug 26, 2018
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs/homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2025, HomeSetup team

# !NOTICE: Do not change this file. To customize your functions edit the file ~/.functions

# Do not source this file multiple times.
if list_contains "${HHS_ACTIVE_DOTFILES}" "bash_functions"; then
  __hhs_log "DEBUG" "$0 was already loaded!"
else

  export HHS_ACTIVE_DOTFILES="${HHS_ACTIVE_DOTFILES} bash_functions"

  # Load all function files.
  all=()
  while IFS= read -r line; do all+=("$line"); done < <(find "${HHS_HOME}/bin/hhs-functions/bash" -type f -name "*.bash" | sort | uniq)
  __hhs_log "DEBUG" "Loading (${#all[@]}) hhs-function files"
  for file in "${all[@]}"; do
    __hhs_log "DEBUG" "Loading ${file}"
    __hhs_source "${file}" || __hhs_log "ERROR" "Unable to source file: ${file}"
  done

  # Load all dev tools files.
  while IFS= read -r line; do all+=("$line"); done < <(find "${HHS_HOME}/bin/dev-tools/bash" -type f -name "*.bash" | sort | uniq)
  __hhs_log "DEBUG" "Loading (${#all[@]}) dev-tools files"
  for file in "${all[@]}"; do
    __hhs_log "DEBUG" "Loading ${file}"
    __hhs_source "${file}" || __hhs_log "ERROR" "Unable to source file: ${file}"
  done

  # Unalias any hhs found because we need this name to use for HomeSetup
  unalias hhs &> /dev/null
  __hhs_has 'hhs' && __hhs_log "ERROR" "'hhs' is already defined: $(command -v 'hhs')"

  # @function: Wrapper to either invoke the hhs application or change to HHS_HOME or HHS_DIR.
  # @param $* [Opt] : All parameters are passed to hhs.bash.
  function __hhs() {

    if [[ -z "${1}" || "${1}" == 'home' ]]; then
      __hhs_change_dir "${HHS_HOME}" || return 1
    elif [[ "${1}" == 'dir' ]]; then
      __hhs_change_dir "${HHS_DIR}" || return 1
    else
      hhs.bash "${@}" || return 1
    fi

    return 0
  }

fi
