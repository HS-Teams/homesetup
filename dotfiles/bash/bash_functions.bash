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

  # Collect source files recursively in lexical order without starting discovery subprocesses.
  function __hhs_collect_source_files__() {
    local source_path

    for source_path in "${1}"/*; do
      [[ -e "${source_path}" || -L "${source_path}" ]] || continue
      if [[ -d "${source_path}" && ! -L "${source_path}" ]]; then
        __hhs_collect_source_files__ "${source_path}"
      elif [[ -f "${source_path}" && "${source_path}" == *.bash ]]; then
        all+=("${source_path}")
      fi
    done
  }

  hhs_dotglob_enabled=0
  \shopt -q dotglob && hhs_dotglob_enabled=1
  \shopt -s dotglob

  # Load all function files.
  all=()
  __hhs_collect_source_files__ "${HHS_HOME}/bin/hhs-functions/bash"
  __hhs_log "DEBUG" "Loading (${#all[@]}) hhs-function files"
  for file in "${all[@]}"; do
    __hhs_log "DEBUG" "Loading ${file}"
    __hhs_source "${file}" || __hhs_log "ERROR" "Unable to source file: ${file}"
  done

  # Load all dev tools files.
  all=()
  __hhs_collect_source_files__ "${HHS_HOME}/bin/dev-tools/bash"
  __hhs_log "DEBUG" "Loading (${#all[@]}) dev-tools files"
  for file in "${all[@]}"; do
    __hhs_log "DEBUG" "Loading ${file}"
    __hhs_source "${file}" || __hhs_log "ERROR" "Unable to source file: ${file}"
  done

  [[ ${hhs_dotglob_enabled} -eq 1 ]] || \shopt -u dotglob
  unset hhs_dotglob_enabled source_path
  unset -f __hhs_collect_source_files__

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
      if [[ -r "${HHS_HOME}/bin/apps/bash/hhs-app/hhs.bash" ]]; then
        (
          HHS_APP_RUNTIME_REUSE=1
          source "${HHS_HOME}/bin/apps/bash/hhs-app/hhs.bash" "${@}"
        ) || return 1
      else
        hhs.bash "${@}" || return 1
      fi
    fi

    return 0
  }

fi
