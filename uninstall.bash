#!/usr/bin/env bash
# shellcheck disable=SC1117,SC1090

#  Script: uninstall.bash
# Purpose: Uninstall HomeSetup
# Created: Dec 21, 2018
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs/homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2025, HomeSetup team

# This script name.
APP_NAME="${0##*/}"

# Help message to be displayed by the script.
USAGE="
usage: $APP_NAME
"

# Define the USER and HOME
USER="${SUDO_USER:-${USER}}"
[[ -z "${SUDO_USER}" ]] && HOME=${HOME:-~/}
[[ -n "${SUDO_USER}" ]] && HOME=$(getent passwd "${SUDO_USER}" | cut -d: -f6)
SHELL="${SHELL:/bin/bash}"

# Import pre-defined Bash Colors.
[[ -f "${HOME}/.bash_colors" ]] && source "${HOME}/.bash_colors"

UNSETS=(
  'quit' 'usage' 'uninstall_dotfiles' 'uninstall_dotfiles'
)

# HomeSetup installation prefix file
HHS_PREFIX_FILE="${HOME}/.hhs-prefix"

# Define the user HomeSetup installation prefix
HHS_PREFIX="$([[ -f "${HHS_PREFIX_FILE}" ]] && grep . "${HHS_PREFIX_FILE}")"

# Define the HomeSetup directory
HHS_HOME=${HHS_PREFIX:-${HOME}/HomeSetup}

# Define the HomeSetup files (.hhs) location
HHS_DIR="${HOME}/.hhs"

# HSPyLib python modules to uninstall
PYTHON_MODULES=(
  'hspylib'
  'hspylib-clitt'
  'hspylib-setman'
  'hspylib-vault'
  'hspylib-firebase'
  'hspylib-datasource'
  'hspylib-askai'
)

# Shell type
SHELL_TYPE="${SHELL##*/}"

# Dotfiles source location
DOTFILES_DIR="${HHS_HOME}/dotfiles/${SHELL_TYPE}"

# Backup prefix
ORIG_PREFIX="orig"

# Flag indicating HHS_DIR removal
REMOVE_HHS_DIR=

# Flag indicating HSPyLib removal
REMOVE_HSPYLIB=

# Flag indicating HomeSetup project removal
REMOVE_PRJ_DIR=

# .dotfiles we will handle
ALL_DOTFILES=()

# Uninstallation type
UNINSTALL_TYPE='normal'

# Find all dotfiles used by HomeSetup according to the current shell type.
IFS=''
while read -r dotfile; do
  ALL_DOTFILES+=("${dotfile}")
done < <(find "${DOTFILES_DIR}" -maxdepth 1 -name "*.${SHELL_TYPE}" -exec basename {} \;)
IFS="${OLDIFS}"

# Purpose: Quit the program and exhibits an exit message if specified
# @param $1 [Req] : The exit return code. 0 = SUCCESS, 1 = FAILURE, * = ERROR ${RED}.
# @param $2 [Opt] : The exit message to be displayed.
quit() {

  # Unset all declared functions
  unset -f "${UNSETS[*]}"
  exit_code=${1:-0}
  shift
  [[ ${exit_code} -ne 0 && ${#} -ge 1 ]] && echo -en "${RED}${APP_NAME}: " 1>&2
  [[ ${#} -ge 1 ]] && echo -e "${*} ${NC}" 1>&2
  [[ ${#} -gt 0 ]] && echo ''
  exit "${exit_code}"
}

# Usage message
# @param $1 [Req] : The exit return code. 0 = SUCCESS, 1 = FAILURE
usage() {
  quit "$1" "$USAGE"
}

check_installation() {

  if [[ -n "${HHS_HOME}" && -d "${HHS_HOME}" ]]; then

    echo -e "${ORANGE}"
    [[ -z ${QUIET} ]] && read -rn 1 -p \
      "Delete HomeSetup project (${HHS_HOME}) dir y/[n] ? " REMOVE_PRJ_DIR
    [[ -n "${REMOVE_PRJ_DIR}" ]] && echo ''
    [[ -z ${QUIET} ]] && read -rn 1 -p \
      "Delete HomeSetup config (${HHS_DIR}) files y/[n] ? " REMOVE_HHS_DIR
    [[ -n "${REMOVE_HHS_DIR}" ]] && echo ''
    [[ -z ${QUIET} ]] && read -rn 1 -p \
      "Uninstall HomeSetup python packages(${PYTHON_MODULES[*]}) y/[n] ? " REMOVE_HSPYLIB
    [[ -n "${REMOVE_HSPYLIB}" ]] && echo ''

    [[ "${REMOVE_PRJ_DIR}" =~ ^[yY]$ ]] && UNINSTALL_TYPE+=' +hhs-prj'
    [[ "${REMOVE_HHS_DIR}" =~ ^[yY]$ ]] && UNINSTALL_TYPE+=' +hhs-dir'
    [[ "${REMOVE_HSPYLIB}" =~ ^[yY]$ ]] && UNINSTALL_TYPE+=' +lib-dir'

    echo -e "${NC}"
    echo -e "${WHITE}### ${GREEN}HomeSetup© ${WHITE}Removal Settings ###${NC}"
    echo -e "${BLUE}"
    echo -e "  Uninstall Type: ${UNINSTALL_TYPE}"
    echo -e "     Install Dir: ${HHS_HOME}"
    echo -e "  Install Prefix: ${HHS_PREFIX}"
    echo -e "        Dotfiles: ${ALL_DOTFILES[*]}"
    echo -e "${NC}"

    echo -e "${YELLOW}"
    read -rn 1 -p "HomeSetup will be completely removed and all backups restored. Continue y/[n] ?" ANS
    echo -e "${NC}"
    [[ -n "$ANS" ]] && echo ''
    if [[ "$ANS" =~ ^[yY]$ ]]; then
      uninstall_dotfiles
    else
      quit 1 "Uninstallation cancelled !"
    fi
  else
    quit 2 "Installation files were not found or removed !"
  fi
}

# Remove dotfiles
uninstall_dotfiles() {

  cd "${HOME}" || cd ..

  # Remove installed HomeSetup dotfiles
  echo -e "\n${BLUE}Removing installed HomeSetup dotfiles ...${NC}"
  for next in ${ALL_DOTFILES[*]}; do
    dotfile="${HOME}/.${next//\.${SHELL_TYPE}/}"
    [[ -f "${dotfile}" ]] && \rm -fv "${dotfile:?}"
  done

  # Removing HomeSetup folders
  [[ -n "${REMOVE_PRJ_DIR}" && -d "${HHS_HOME}" ]] && \rm -rfv "${HHS_HOME:?}"
  [[ -L "${HHS_DIR}/bin" ]] && \rm -rfv "${HHS_DIR:?}/bin"

  # Remove HomeSetup .hhs folder
  [[ -n "${REMOVE_HHS_DIR}" ]] && echo ''
  if [[ "${REMOVE_HHS_DIR}" =~ ^[yY]$ ]]; then
    [[ -d "${HHS_DIR}" ]] && \rm -rfv "${HHS_DIR:?}" &> /dev/null
  fi

  # Restore original dotfiles
  if [[ -d "${HHS_DIR}" ]]; then
    echo -e "\n${BLUE}Restoring original dotfiles ...${NC}"
    BACKUPS=("$(find "${HHS_DIR}" -iname "*.${ORIG_PREFIX}")")
    for next in ${BACKUPS[*]}; do
      [[ -f "${next}" ]] && \cp -v "${next}" "${HOME}/$(basename "${next%.*}")"
    done
  fi

  # Uninstall HomeSetup python library
  if [[ "${REMOVE_HSPYLIB}" =~ ^[yY]$ ]]; then
    PIP=$(command -v pip3 2>/dev/null)
    # HsPyLib-Vault
    echo -e "\n${BLUE}Removing HomeSetup Vault${NC}"
    ${PIP} uninstall -y hspylib-vault &> /dev/null \
      || echo -e "${RED}# Unable to uninstall HomeSetup vault !\n${NC}"
    # HsPyLib-Firebase
    echo -e "\n${BLUE}Removing HomeSetup Firebase${NC}"
    ${PIP} uninstall -y hspylib-firebase &> /dev/null \
      || echo -e "${RED}# Unable to uninstall HomeSetup firebase !\n${NC}"
    # HsPyLib-Clitt
    echo -e "\n${BLUE}Removing HomeSetup Clitt${NC}"
    ${PIP} uninstall -y hspylib-clitt &> /dev/null \
      || echo -e "${RED}# Unable to uninstall HomeSetup clitt !\n${NC}"
    # HsPyLib-Datasource
    echo -e "\n${BLUE}Removing HomeSetup Datasource${NC}"
    ${PIP} uninstall -y hspylib-datasource &> /dev/null \
      || echo -e "${RED}# Unable to uninstall HomeSetup datasource !\n${NC}"
    # HsPyLib-Setman
    echo -e "\n${BLUE}Removing HomeSetup HsPyLib-Setman${NC}"
    ${PIP} uninstall -y hspylib-setman &> /dev/null \
      || echo -e "${RED}# Unable to uninstall HomeSetup HsPyLib-Setman !\n${NC}"
    # HsPyLib-AskAi
    echo -e "\n${BLUE}Removing HomeSetup HsPyLib-AskAi${NC}"
    ${PIP} uninstall -y hspylib-askai &> /dev/null \
      || echo -e "${RED}# Unable to uninstall HomeSetup HsPyLib-AskAi !\n${NC}"
    # HsPyLib-Core
    echo -e "\n${BLUE}Removing HomeSetup HsPyLib-Core${NC}"
    ${PIP} uninstall -y hspylib &> /dev/null \
      || echo -e "${RED}# Unable to uninstall HomeSetup HsPyLib-Core !\n${NC}"
  fi

  # Remove Starship. Locate and delete the binary
  command -v 'starship' &>/dev/null && \rm -fv "$(command -v 'starship')"

  # Restoring prompts
  export PS1='\[\h:\W \u \$ '
  export PS2="$PS1"

  # Removing HomeSetup folder
  [[ -d "${HHS_HOME}" ]] && quit 2 "Failed to uninstall HomeSetup !"

  # Unset aliases and envs
  echo "Unsetting aliases and variables ..."
  unalias -a
  unset "${!HHS_@}"

  echo 'HomeSetup has been successfully uninstalled !'
  echo ''
  echo '* Your old PS1 (prompt) and aliases will be restored next time you open the terminal.'
  echo "* Your temporary PS1 => '$PS1'"
  echo ''
}

check_installation

echo '!!! HomeSetup will be gone after you open a new terminal !!!'
