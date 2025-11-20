#!/usr/bin/env bash

#  Script: firebase.bash
# Purpose: Manager for HomeSetup Firebase integration
# Created: Jan 06, 2020
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs#homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2025, HomeSetup team

# Current plugin name
PLUGIN_NAME="firebase"

# Namespace cleanup
UNSETS=(
  help version cleanup execute args action db_alias dotfiles
)

# @purpose: HHS plugin required function
function help() {
  python3 -m ${PLUGIN_NAME} -h
  exit $?
}

# @purpose: HHS plugin required function
function version() {
  python3 -m ${PLUGIN_NAME} -v
  exit $?
}

# @purpose: HHS plugin required function
function cleanup() {
  unset -f "${UNSETS[@]}"
  echo -n ''
}

# @purpose: HHS plugin required function
function execute() {

  local args action db_alias dotfiles=()

  __hhs_is_venv || quit 1 "Not available when HomeSetup python venv is not active!"

  # shellcheck disable=SC2206
  args=(${@})
  action="${args[0]}"
  db_alias="${args[1]}"

  # Find all dotfiles
  dotfiles=()
  IFS=''
  while read -r dotfile; do
    [[ "$(basename "${dotfile}")" == .last_update ]] && continue
    is_text_file=$(file -bL --mime "${dotfile}" | grep -v 'binary')
    [[ -s "${dotfile}" && -n ${is_text_file} ]] && dotfiles+=("${dotfile}")
  done < <(find "${HHS_DIR}" -maxdepth 1 -type f -name ".*")
  IFS="${OLDIFS}"
  [[ ${#dotfiles[@]} -eq 0 ]] && quit 2 "Unable to find any dotfile to upload!"

  echo ''
  pushd "${HHS_DIR}" &>/dev/null || quit 2

  if [[ 'upload' == "${action}" ]]; then
    python3 -m firebase upload dotfiles."${db_alias}" "${dotfiles[@]}"
  elif [[ 'download' == "${action}" ]]; then
    python3 -m firebase download dotfiles."${db_alias}"
  elif [[ 'setup' == "${action}" ]]; then
    python3 -m firebase setup
  else
    python3 -m firebase "${args[@]}"
  fi
  ret_val=$?

  popd &>/dev/null || quit 2
  echo -e "${NC}"

    [[ ${ret_val} -eq 0 ]] && quit 0 || quit 2
  }
