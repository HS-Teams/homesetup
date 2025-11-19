#!/usr/bin/env bash
# shellcheck disable=2181,2034

#  Script: setup.bash
# Purpose: Contains all HHS initialization functions
# Created: Nov 06, 2023
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs#homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2025, HomeSetup team

# Current plugin name
PLUGIN_NAME="setup"

UNSETS=(
  help version cleanup execute DEFAULT_SETTINGS RE_PROPERTY
)

# Current hhs setup version
VERSION="1.0.13"

# Usage message
USAGE="$(cat <<EOF
usage: ${APP_NAME} ${PLUGIN_NAME} [options]
    Configure or restore HomeSetup initialization settings (v${VERSION}).
    Presents a multi-select menu for toggling startup features.

    options:
      -h | --help                    : Display this help message and exit.
      -v | --version                 : Print the setup plugin version.
      -restore                       : Restore the default homesetup.toml file.

    arguments:
      (none)                         : Selections are made interactively via menus.

  Notes:
    - When invoked without options a picker lets you toggle each startup feature.
    - Restoring overwrites the existing homesetup.toml with the template version.
EOF
)"

# Regex to match a setting.
RE_PROPERTY="^([a-zA-Z0-9_.]+) *= *(.*)"

[[ -s "${HHS_DIR}/bin/app-commons.bash" ]] && source "${HHS_DIR}/bin/app-commons.bash"

# @purpose: HHS plugin required function
function help() {
  usage 0
}

# @purpose: HHS plugin required function
function version() {
  echo "HomeSetup ${PLUGIN_NAME} plugin v${VERSION}"
  quit 0
}

# @purpose: HHS plugin required function
function cleanup() {
  unset -f "${UNSETS[@]}"
  echo -n ''
}

# @purpose: HHS plugin required function
function execute() {

  local file_ver name title value minput_file sel_settings all_items=()

  if list_contains "${*}" "-restore"; then
    \cp -f "${HHS_HOME}/dotfiles/homesetup.toml" "${HHS_SETUP_FILE}"
    quit 0
  elif [[ ! -s "${HHS_SETUP_FILE}" ]]; then
    \cp -f "${HHS_HOME}/dotfiles/homesetup.toml" "${HHS_SETUP_FILE}"
  fi

  if [[ ${#} -gt 0 ]]; then
    quit 2 "Command not found: ${*}"
  fi

  # Read all settings, but first, check the file version.
  file_ver="$(grep -E '@version:' "${HHS_SETUP_FILE}")"
  if [[ -z "${file_ver}" || "${file_ver#*: v}" != "${VERSION}" ]]; then
    \cp -f "${HHS_HOME}/dotfiles/homesetup.toml" "${HHS_SETUP_FILE}"
    echo "${YELLOW}HomeSetup settings required updating and have been overwritten by the new one.${NC}"
    sleep 2
  fi

  while read -r setting; do
    name="${setting%%=*}"
    value="${setting#*=}"
    value="${value//true/True}"
    value="${value//false/False}"
    all_items+=("${name}=${value}")
  done < <(__hhs_toml_get_all "${HHS_SETUP_FILE}" "setup")

  title="${BLUE}HomeSetup Initialization Settings${ORANGE} ${GREEN}v${VERSION}\n"
  title+="${ORANGE}Please mark the preferred startup settings:"
  mchoose_file=$(mktemp)

  if __hhs_mchoose "${mchoose_file}" "${title}" "${all_items[@]}"; then
    read -r -d '' -a sel_settings < <(grep . "${mchoose_file}")
    for setting in "${all_items[@]}"; do
      name="${setting%%=*}"
      if list_contains "${sel_settings[*]}" "${name}"; then
        value='true'
      else
        value='false'
      fi
      if ! __hhs_toml_set "${HHS_SETUP_FILE}" "${name}=${value}" "setup"; then
        quit 2 "Unable to change setting: ${setting}!"
      fi
    done
    quit 0 "${GREEN}HomeSetup settings (${#sel_settings[@]}) saved!${NC}"
  else
    quit 0 "${YELLOW}HomeSetup settings (${#all_items[@]}) unchanged!${NC}"
  fi
}
