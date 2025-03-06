#!/usr/bin/env bats

#  Script: sanity-tests.bats
# Purpose: HomeSetup installation sanity tests.
# Created: Mar 02, 2020
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs/homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2025, HomeSetup team

load test_helper
load_bats_libs

# TC - 1
@test "after-installation-all-homesetup-folders-should-exist" {
  [[ \
    -d "${HHS_HOME}" \
    && -d "${HHS_DIR}" \
    && -d "${HHS_CACHE_DIR}" \
    && -d "${HHS_BACKUP_DIR}" \
    && -d "${HHS_LOG_DIR}" \
    && -d "${HHS_MOTD_DIR}" \
    && -d "${HHS_PROMPTS_DIR}" \
  ]]
}

# TC - 2
@test "after-installation-all-homesetup-dotfiles-should-exist" {

  declare -a missing=()

  for next in "${HHS_HOME}"/dotfiles/bash/*.bash; do
    dotfile="${HOME}/.$(basename "${next}")"
    dotfile="${dotfile%\.*}"
    [[ -L "${dotfile}" ]] || missing+=("${dotfile}")
  done

  [[ -f "${HOME}/.inputrc" ]] || missing+=("${HOME}/.inputrc")
  [[ -d "${HHS_DIR}/hunspell-dicts" ]] || missing+=("${HHS_DIR}/hunspell-dicts")
  [[ -f "${HHS_DIR}/.aliasdef" ]] || missing+=("${HHS_DIR}/.aliasdef")
  [[ -f "${HHS_DIR}/.homesetup.toml" ]] || missing+=("${HHS_DIR}/.homesetup.toml")
  [[ -f "${HHS_DIR}/shell-opts.toml" ]] || missing+=("${HHS_DIR}/shell-opts.toml")
  [[ -f "${HHS_DIR}/.aliases" ]] || missing+=("${HHS_DIR}/.aliases")
  [[ -f "${HHS_DIR}/.cmd_file" ]] || missing+=("${HHS_DIR}/.cmd_file")
  [[ -f "${HHS_DIR}/.colors" ]] || missing+=("${HHS_DIR}/.colors")
  [[ -f "${HHS_DIR}/.env" ]] || missing+=("${HHS_DIR}/.env")
  [[ -f "${HHS_DIR}/.functions" ]] || missing+=("${HHS_DIR}/.functions")
  [[ -f "${HHS_DIR}/.path" ]] || missing+=("${HHS_DIR}/.path")
  [[ -f "${HHS_DIR}/.profile" ]] || missing+=("${HHS_DIR}/.profile")
  [[ -f "${HHS_DIR}/.prompt" ]] || missing+=("${HHS_DIR}/.prompt")
  [[ -f "${HHS_DIR}/.saved_dirs" ]] || missing+=("${HHS_DIR}/.saved_dirs")
  [[ -f "${HHS_DIR}/.glow.yml" ]] || missing+=("${HHS_DIR}/.glow.yml")

  [[ ${#missing[@]} -eq 0 ]] || echo "Missing dotfiles: [${missing[*]}]"
  [[ ${#missing[@]} -eq 0 ]]
}

# TC - 3
@test "after-installation-all-homesetup-integrations-should-exist" {

  declare -a integrations=('starship' 'gtrash') missing=()

  for next in "${integrations[@]}"; do
    command -v "${next}" &>/dev/null || missing+=("${next}")
  done

  [[ -f "${HHS_BLESH_DIR}/out/ble.sh" ]] || missing+=("blesh")

  [[ ${#missing[@]} -eq 0 ]] || echo "Missing dotfiles: [${missing[*]}]"
  [[ ${#missing[@]} -eq 0 ]]
}

# TC - 4
@test "after-installation-all-homesetup-dotfiles-should-be-active" {
  run echo "$HHS_ACTIVE_DOTFILES"
  assert_output --partial "bashrc hhsrc bash_commons bash_env bash_colors bash_prompt bash_aliases bash_icons bash_functions"
}
