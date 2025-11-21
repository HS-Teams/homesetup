#!/usr/bin/env zsh
# shellcheck disable=SC1117

#  Script: zsh_prompt.zsh
# Purpose: Shell prompt configuration file
# Created: Nov 21, 2025
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs/homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2025, HomeSetup team

# NOTICE:
# - Do not change this file. To customize your prompt edit the file ~/.prompt

# Initialize Starship prompt if it is set to.
if command -v 'starship' &>/dev/null && [[ ${HHS_USE_STARSHIP} -eq 1 ]]; then

  # @function: Set the terminal window title.
  function __hhs_set_win_title() {
    echo -ne "\033]0; ${TITLE} \007"
  }

  __hhs_log "INFO" "Starting starship prompt"

  if [[ ! -s "${STARSHIP_CONFIG}" ]]; then
    __hhs_log "DEBUG" "Copying default HomeSetup starship.toml config to -> ${STARSHIP_CONFIG}"
    if ! \cp "${HHS_STARSHIP_PRESETS_DIR}/hhs-starship.toml" \
      "${STARSHIP_CONFIG}" &>/dev/null; then
      __hhs_log "ERROR" "Unable to copy default starship config file into place!"
    fi
  fi

  # shellcheck disable=SC2034
  starship_precmd_user_func="__hhs_set_win_title"
  if eval "$(\starship init "${HHS_MY_SHELL}")"; then
    __hhs_log "INFO" "Starship successfully started!"
  else
    __hhs_log "ERROR" "Starship failed to start!"
  fi
else
  __hhs_log "WARN" "Starship prompt initialization was disabled !"
fi

# If Starship did not start, configure classic HomeSetup prompt.
if [[ -z "${STARSHIP_SESSION_KEY}" ]]; then
  __hhs_log "INFO" "Starting PowerLevel 10k prompt!"
  source "$(brew --prefix)/share/powerlevel10k/powerlevel10k.zsh-theme"
  [[ ! -f ~/.p10k.zsh ]] || source "${HOME}/.p10k.zsh"
fi

# ColorLS integration. Copy HomeSetup config files if they are not found.
if gem which colorls &>/dev/null; then
  colorls_dir="$(dirname "$(gem which colorls)")/yaml"
  hhs_colorls_dir="${HHS_HOME}/assets/colorls/hhs-preset"
  [[ -d "${colorls_dir}" ]] || \mkdir -p "${colorls_dir}"
  [[ -f "${colorls_dir}/dark_colors.yaml" ]] || \cp "${hhs_colorls_dir}/dark_colors.yaml" "${colorls_dir}"
  [[ -f "${colorls_dir}/light_colors.yaml" ]] || \cp "${hhs_colorls_dir}/light_colors.yaml" "${colorls_dir}"
  [[ -f "${colorls_dir}/file_aliases.yaml" ]] || \cp "${hhs_colorls_dir}/file_aliases.yaml" "${colorls_dir}"
  [[ -f "${colorls_dir}/files.yaml" ]] || \cp "${hhs_colorls_dir}/files.yaml" "${colorls_dir}"
  [[ -f "${colorls_dir}/folder_aliases.yaml" ]] || \cp "${hhs_colorls_dir}/folder_aliases.yaml" "${colorls_dir}"
  [[ -f "${colorls_dir}/folders.yaml" ]] || \cp "${hhs_colorls_dir}/folders.yaml" "${colorls_dir}"
  source "$(dirname "$(gem which colorls)")"/tab_complete.sh
fi
