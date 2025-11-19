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

UNSETS=(
  help version cleanup execute add_hhs_preset
)

# Current hhs starship version
VERSION="1.0.1"

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
USAGE="$(cat <<EOF
usage: ${APP_NAME} ${PLUGIN_NAME} [options] {edit|restore|preset <name>|configs}
    Manage your Starship prompt from HomeSetup.
    Apply curated presets or quickly edit the configuration file.

    options:
      -h | --help                    : Display this help message and exit.
      -v | --version                 : Print the starship plugin version.

    arguments:
      edit                           : Open the starship configuration file in the default editor.
      restore                        : Restore the HomeSetup default preset.
      preset <preset_name>           : Apply one of the bundled or upstream presets.
      configs                        : Open the official Starship configuration reference.

  Notes:
    - When no command is supplied the script defaults to 'edit'.
    - Run '${APP_NAME} ${PLUGIN_NAME} preset' with no name to pick from the curated list interactively.
EOF
)"

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

# @purpose: Opens the Starship configuration page
function configs() {
  local page_url="https://starship.rs/config/"

  echo -e "${BLUE}${GLOBE_ICN} Opening Starship config page from: ${page_url}${ELLIPSIS_ICN}${NC}"
  __hhs_open "${page_url}" && sleep 2 && quit 0

  quit 1 "Failed to open url: \"${page_url}\" !"
}


# @purpose: Add HomeSetup presets.
function add_hhs_presets() {

  local hhs_presets

  IFS=$'\n' read -r -d '' -a hhs_presets < <(find "${HHS_STARSHIP_PRESETS_DIR}" -type f -name "hhs-*.toml" -exec basename {} \;)
  IFS="${OLDIFS}"
  STARSHIP_PRESETS+=("${hhs_presets[@]}")
}

# @purpose: HHS plugin required function
function execute() {

  local preset_val mselect_file title preset

  if __hhs_has starship; then

    [[ $# -eq 0 ]] || { list_contains "$@" "edit" && __hhs_open "${STARSHIP_CONFIG}" && quit 0; }
    [[ $# -eq 0 ]] || { list_contains "$@" "configs" && configs; }
    list_contains "${*}" "help" && usage 0
    list_contains "${*}" "version" && version

    if list_contains "${*}" "restore"; then
      echo -e "${GREEN}Restoring HomeSetup starship configuration...${NC}"
      if \cp "${HHS_STARSHIP_PRESETS_DIR}/hhs-starship.toml" "${STARSHIP_CONFIG}" &> /dev/null; then
        quit 0 "${GREEN}Your starship prompt changed to HomeSetup defaults!${NC}"
      else
        quit 1 "Unable to restore HomeSetup starship preset"
      fi
    elif list_contains "${*}" "preset"; then
      add_hhs_presets
      preset_val="$2"
      [[ -n "${preset_val}" && "${2}" == hhs-* ]] && preset_val="${preset_val//.toml}.toml"
      if [[ -z ${preset_val} ]]; then
        mselect_file=$(mktemp)
        title="Please select one Starship preset (${#STARSHIP_PRESETS[@]})"
        if __hhs_mselect "${mselect_file}" "${title}${NC}" "${STARSHIP_PRESETS[@]}"; then
          preset_val=$(grep . "${mselect_file}")
        fi
      fi
      if [[ -n "${preset_val}" ]] && ! list_contains "${STARSHIP_PRESETS[*]}" "${preset_val}"; then
        __hhs_errcho "${PLUGIN_NAME}" "Starship preset not found: \033[9m'${preset_val}'\033[m!\n${STARSHIP_PRESETS[*]}"
        echo -e "${YELLOW}${TIP_ICON} Tip: Please choose one valid Starship preset: ${BLUE}"
        for preset in "${STARSHIP_PRESETS[@]}"; do echo "  |-${preset}" | nl; done
        quit 1
      fi
      if [[ -n "${preset_val}" ]]; then
        echo -e "${GREEN}Setting starship preset \"${preset_val}\"...${NC}"
        if [[ "${preset_val}" == *'hhs-'* ]] && \cp "${HHS_STARSHIP_PRESETS_DIR}/${preset_val}" "${STARSHIP_CONFIG}"; then
          quit 0 "${GREEN}Your starship prompt changed to HomeSetup preset: ${preset_val} !${NC}"
        elif bash -c "starship preset \"${preset_val}\" -o ${STARSHIP_CONFIG}" &> /dev/null; then
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
