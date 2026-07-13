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

# Current hhs setup plug-in and settings schema versions.
VERSION="1.0.14"
SETTINGS_VERSION="1.0.13"

# Namespace cleanup
UNSETS=(
  help version cleanup execute DEFAULT_SETTINGS RE_PROPERTY SETTINGS_VERSION
)

# Usage message
read -r -d '' USAGE <<EOF
usage: ${APP_NAME} ${PLUGIN_NAME} [-restore | -apply <0|1>...] [options]

 ____       _
/ ___|  ___| |_ _   _ _ __
\___ \ / _ \ __| | | | '_ \\
 ___) |  __/ |_| |_| | |_) |
|____/ \___|\__|\__,_| .__/
                     |_|

  HomeSetup initialization setup v${VERSION}.

    options:
      -apply [<0|1>, ...]      : Apply setup values in file order; omitted values remain unchanged.
      -restore                 : Restore HomeSetup defaults.
      -h | --help              : Display this help message.
      -v | --version           : Display current plugin version.

    arguments:
      (none)                   : Launch interactive setup selection.

    examples:
      Restore default settings:
        => ${APP_NAME} ${PLUGIN_NAME} -restore
      Apply setup options from CLI:
        => ${APP_NAME} ${PLUGIN_NAME} -apply 1 0 1 1 0 0 1 1 1 1 0 0 0 1
      Review setup options interactively:
        => ${APP_NAME} ${PLUGIN_NAME}

    exit status:
      (0) Success
      (1) Failure due to missing/wrong client input or similar issues
      (2) Failure due to program execution failures

  Notes:
    - Settings are stored in homesetup.toml under the setup section.

EOF

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
  local apply_idx=0 apply_raw apply_value apply_values=() normalized_values=() setting

  if list_contains "${*}" "-restore"; then
    \cp -f "${HHS_HOME}/dotfiles/homesetup.toml" "${HHS_SETUP_FILE}"
    quit 0
  elif [[ ! -s "${HHS_SETUP_FILE}" ]]; then
    \cp -f "${HHS_HOME}/dotfiles/homesetup.toml" "${HHS_SETUP_FILE}"
  fi

  # Read all settings, but first, check the file version.
  file_ver="$(grep -E '@version:' "${HHS_SETUP_FILE}")"
  if [[ -z "${file_ver}" || "${file_ver#*: v}" != "${SETTINGS_VERSION}" ]]; then
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

  if [[ "${1}" == "-apply" ]]; then
    shift
    for apply_raw in "$@"; do
      apply_raw="${apply_raw//[/}"
      apply_raw="${apply_raw//]/}"
      apply_raw="${apply_raw//,/}"
      [[ -n "${apply_raw}" ]] && apply_values+=("${apply_raw}")
    done

    if [[ "${#apply_values[@]}" -gt "${#all_items[@]}" ]]; then
      quit 1 "Expected at most ${#all_items[@]} setup values, received ${#apply_values[@]}."
    fi

    for apply_value in "${apply_values[@]}"; do
      case "${apply_value}" in
        1|true|True|TRUE) normalized_values+=('true') ;;
        0|false|False|FALSE) normalized_values+=('false') ;;
        *) quit 1 "Invalid setup value: ${apply_value}. Use 0 or 1." ;;
      esac
    done

    for value in "${normalized_values[@]}"; do
      setting="${all_items[apply_idx]}"
      name="${setting%%=*}"
      if ! __hhs_toml_set "${HHS_SETUP_FILE}" "${name}=${value}" "setup"; then
        quit 2 "Unable to change setting: ${setting}!"
      fi
      ((apply_idx += 1))
    done
    quit 0 "${GREEN}HomeSetup settings (${#normalized_values[@]}) applied!${NC}"
  fi

  if [[ ${#} -gt 0 ]]; then
    quit 2 "Command not found: ${*}"
  fi

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
