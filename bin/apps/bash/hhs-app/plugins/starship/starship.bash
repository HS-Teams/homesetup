#!/usr/bin/env bash
# shellcheck disable=2181,2199,2076,2034

#  Script: built-ins.bash
# Purpose: Contains all starship manipulation functions
# Created: Wed 22, 2023
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs#homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2025, HomeSetup team

# Current plugin name
PLUGIN_NAME="starship"

# Current hhs starship version
VERSION="1.1.0"

# Namespace cleanup
UNSETS=(
  help version cleanup execute add_hhs_presets
  current_starship_preset record_starship_preset
)

# All Starship presets
STARSHIP_PRESETS=(
  'no-nerd-font'
  'bracketed-segments'
  'plain-text-symbols'
  'no-runtime-versions'
  'no-empty-icons'
  'pure-preset'
  'tokyo-night'
  'pastel-powerline'
  'nerd-font-symbols'
)

# Usage message
read -r -d '' USAGE <<EOF
usage: ${APP_NAME} ${PLUGIN_NAME} [command] [options]

 ____  _                 _     _
/ ___|| |_ __ _ _ __ ___| |__ (_)_ __
\___ \| __/ _\` | '__/ __| '_ \| | '_ \\
 ___) | || (_| | |  \__ \ | | | | |_) |
|____/ \__\__,_|_|  |___/_| |_|_|_| .__/
                                |_|

  HomeSetup starship integration setup.
  Visit the Starship website at: https://starship.rs/

    options:
      -h | --help                : Display this help message.
      -v | --version             : Display current plugin version.

    commands:
      edit                       : Edit your starship configuration file (default command).
      restore                    : Restore HomeSetup defaults.
      preset <-q | preset_name>       : Configure of query your current starship to a preset.

    presets:
      no-runtime-versions        : Hide language runtime versions.
      bracketed-segments         : Show modules in brackets instead of wording.
      plain-text-symbols         : Use plain-text symbols for modules.
      no-empty-icons             : Omit icons when toolsets are unavailable.
      tokyo-night                : Inspired by tokyo-night-vscode-theme.
      no-nerd-font               : Avoid Nerd Font symbols anywhere in the prompt.
      pastel-powerline           : Inspired by M365Princess, demonstrates path substitution.
      pure-preset                : Emulates the look and behavior of Pure.
      nerd-font-symbols          : Use Nerd Font symbols for each module.

    examples:
      Restore the default prompt:
        => ${APP_NAME} ${PLUGIN_NAME} restore
      Apply a preset interactively:
        => ${APP_NAME} ${PLUGIN_NAME} preset

    exit status:
      (0) Success
      (1) Failure due to missing/wrong client input or similar issues
      (2) Failure due to program execution failures

  Notes:
    - If no command is passed, the default editor opens the starship configuration file.

EOF

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

  local preset_val mselect_file title preset query_status

  [[ -z "$1" || "$1" == "-h" || "$1" == "--help" ]] && usage 0
  [[ "$1" == "-v" || "$1" == "--version" ]] && version

  if __hhs_has starship; then

    [[ $# -eq 0 ]] || { list_contains "$@" "edit" && __hhs_open "${STARSHIP_CONFIG}" && quit 0; }
    [[ $# -eq 0 ]] || { list_contains "$@" "configs" && configs; }

    if list_contains "${*}" "restore"; then
      echo -e "${GREEN}Restoring HomeSetup starship configuration...${NC}"
      if \cp "${HHS_STARSHIP_PRESETS_DIR}/hhs-starship.toml" "${STARSHIP_CONFIG}" &> /dev/null; then
        quit 0 "${GREEN}Your starship prompt changed to HomeSetup defaults!${NC}"
      else
        quit 1 "Unable to restore HomeSetup starship preset"
      fi
    elif list_contains "${*}" "preset"; then
      preset_val="$2"
      if [[ "${preset_val}" == "-q" ]]; then
        preset_val="$(current_starship_preset)"
        query_status=$?
        if [[ ${query_status} -eq 1 ]]; then
          quit 1 "Unable to read starship configuration file: ${STARSHIP_CONFIG}"
        elif [[ ${query_status} -eq 2 ]]; then
          quit 1 "Starship preset information not found in: ${STARSHIP_CONFIG}"
        fi
        printf '%s\n' "${preset_val}"
        quit 0
      fi
      add_hhs_presets
      [[ -n "${preset_val}" && "${2}" == hhs-* ]] && preset_val="${preset_val//.toml}.toml"
      if [[ -z ${preset_val} ]]; then
        mselect_file=$(mktemp)
        title="Please select one Starship preset (${#STARSHIP_PRESETS[@]})"
        if __hhs_mselect "${mselect_file}" "${title}${NC}" "${STARSHIP_PRESETS[@]}"; then
          preset_val=$(grep . "${mselect_file}")
        fi
      fi
      if [[ -n "${preset_val}" ]] && ! list_contains "${STARSHIP_PRESETS[*]}" "${preset_val}"; then
        __hhs_errcho "${PLUGIN_NAME}" \
          "Starship preset not found: \033[9m'${preset_val}'\033[m!\n${STARSHIP_PRESETS[*]}"
        echo -e "${YELLOW}${TIP_ICON} Tip: Please choose one valid Starship preset: ${BLUE}"
        for preset in "${STARSHIP_PRESETS[@]}"; do echo "  |-${preset}" | nl; done
        quit 1
      fi
      if [[ -n "${preset_val}" ]]; then
        echo -e "${GREEN}Setting starship preset \"${preset_val}\"...${NC}"
        if [[ "${preset_val}" == *'hhs-'* ]] \
          && \cp "${HHS_STARSHIP_PRESETS_DIR}/${preset_val}" "${STARSHIP_CONFIG}"; then
          quit 0 "${GREEN}Your starship prompt changed to HomeSetup preset: ${preset_val} !${NC}"
        elif starship preset "${preset_val}" -o "${STARSHIP_CONFIG}" &> /dev/null \
          && record_starship_preset "${preset_val}"; then
          quit 0 "${GREEN}Your starship prompt changed to preset: ${preset_val} !${NC}"
        else
          quit 1 "Unable to set starship preset: ${preset_val} "
        fi
      fi
    else
      quit 1 "Command not found: ${*} "
    fi

  else
    echo -e "${ORANGE}Starship is not installed. You can install it by:"
    echo -e "${CYAN}$ curl -sS https://starship.rs/install.sh${NC}"
  fi
}


# @purpose: Print the current preset recorded in the Starship configuration file.
function current_starship_preset() {
  local preset_name

  [[ -r "${STARSHIP_CONFIG:-}" ]] || return 1
  preset_name="$(
    awk '/^# Preset:[[:space:]]*/ {
      sub(/^# Preset:[[:space:]]*/, "")
      print
      exit
    }' "${STARSHIP_CONFIG}"
  )"
  if [[ -z "${preset_name}" ]]; then
    preset_name="$(
      awk '/^# Profile:[[:space:]]*/ {
        sub(/^# Profile:[[:space:]]*/, "")
        print
        exit
      }' "${STARSHIP_CONFIG}"
    )"
    [[ "${preset_name}" == hhs-* && "${preset_name}" != *.toml ]] \
      && preset_name="${preset_name}.toml"
  fi
  [[ -n "${preset_name}" ]] || return 2
  printf '%s\n' "${preset_name}"
}


# @purpose: Record a generated preset in the Starship configuration file.
function record_starship_preset() {
  local preset_name="$1"

  [[ -n "${preset_name}" && -f "${STARSHIP_CONFIG:-}" ]] || return 1
  printf '\n# Preset: %s\n' "${preset_name}" >> "${STARSHIP_CONFIG}"
}


# @purpose: Opens the Starship configuration page
configs() {
  local page_url="https://starship.rs/config/"

  echo -e "${BLUE}${GLOBE_ICN} Opening Starship config page from: ${page_url}${ELLIPSIS_ICN}${NC}"
  __hhs_open "${page_url}" && sleep 2 && quit 0

  quit 1 "Failed to open url: \"${page_url}\" !"
}


# @purpose: Add HomeSetup presets.
add_hhs_presets() {

  local hhs_presets

  IFS=$'\n' read -r -d '' -a hhs_presets < <(
    find "${HHS_STARSHIP_PRESETS_DIR}" -type f -name "hhs-*.toml" -exec basename {} \;
  )
  IFS="${OLDIFS}"
  STARSHIP_PRESETS+=("${hhs_presets[@]}")
}
