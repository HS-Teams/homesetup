#!/usr/bin/env bash
# shellcheck disable=SC2034,SC1090

#  Script: hspm.bash
# Purpose: Manage your development tools using installation/uninstallation recipes.
# Created: Jan 06, 2020
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs#homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2025, HomeSetup team

# Current plugin name
PLUGIN_NAME="hspm"

# Current script version.
VERSION=1.0.0

# Namespace cleanup
UNSETS=(
  help version cleanup execute cleanup_recipes
  uninstall_recipe reinstall_recipe list_recipes install_recipe
  add_breadcrumb del_breadcrumb recover_packages
  _install_ _uninstall_ _depends_ _which_
)

# Usage message
read -r -d '' USAGE <<EOF
usage: ${APP_NAME} ${PLUGIN_NAME} {install|uninstall|reinstall|list|recover} [options]

 _   _ ____  ____  __  __
| | | / ___||  _ \|  \/  |
| |_| \___ \| |_) | |\/| |
|  _  |___) |  __/| |  | |
|_| |_|____/|_|   |_|  |_|

  HomeSetup package manager.

    options:
      -v | --version               : Display current program version.
      -h | --help                  : Display this help message.
      -e                           : (recover) Open the recovery file with the default editor.
      -i                           : (recover) Install all recovered packages instead of listing.
      -t                           : (recover) Use ${HHS_DEV_TOOLS} as the source for recovery.

    arguments:
      list                         : List all available OS-based installation recipes.
      install <package...>         : Install packages using matching recipes.
      uninstall <package...>       : Uninstall packages using matching recipes.
      reinstall <package...>       : Uninstall and install packages using matching recipes.
      recover                      : Recover packages previously installed by hspm.

    examples:
      Install a package recipe:
        => ${APP_NAME} ${PLUGIN_NAME} install fzf
      Recover and reinstall previous tools:
        => ${APP_NAME} ${PLUGIN_NAME} recover -i
      Inspect the recovery list without changes:
        => ${APP_NAME} ${PLUGIN_NAME} recover

    exit status:
      (0) Success
      (1) Failure due to missing/wrong client input or similar issues
      (2) Failure due to program execution failures

  Notes:
    - Package manager detection relies on common managers (brew, apt, yum, dnf, apk).

EOF

[[ -s "$HHS_DIR/bin/app-commons.bash" ]] && source "$HHS_DIR/bin/app-commons.bash"

# Flag to install all recovered packages,
RECOVER_INSTALL=

# Flag to recover HHS_DEV_TOOLS instead of breadcrumbs,
RECOVER_TOOLS=

# Hold all hspm recipes,
ALL_RECIPES=()

# Directory containing all hspm recipes,
RECIPES_DIR="${PLUGINS_DIR}/hspm/recipes"

# HSPM catalog file.
HSPM_CATALOG_FILE="${PLUGINS_DIR}/hspm/catalog.toml"

# File containing all installed/uninstalled packages
BREADCRUMB_FILE="${HHS_DIR}/.hspm"

# Known package managers
KNOWN_PCG_MANAGERS=('brew' 'apt-get' 'apt' 'yum' 'dnf' 'apk')

# Sudo command
SUDO=

# HSPM log file
LOGFILE="${HHS_LOG_DIR}/hspm.log"

# @purpose: HHS plugin required function
function help() {
  usage 0
}

# @purpose: HHS plugin required function
function version() {
  echo "${PLUGIN_NAME} v${VERSION}"
  exit 0
}

# @purpose: HHS plugin required function
function cleanup() {
  unset -f "${UNSETS[@]}"
  echo -n ''
}

# @purpose: HHS plugin required function
function execute() {

  local cmd args

  [[ -z "$1" || "$1" == "-h" || "$1" == "--help" ]] && usage 0
  [[ "$1" == "-v" || "$1" == "--version" ]] && version

  touch "${BREADCRUMB_FILE}" || quit 1 "Unable to access hspm file: ${BREADCRUMB_FILE}"

  if [[ -z "${HHS_MY_OS_PACKMAN}" ]]; then
    for pkg_man in "${KNOWN_PCG_MANAGERS[@]}"; do
      command -v "${pkg_man}" &> /dev/null && HHS_MY_OS_PACKMAN="${HHS_MY_OS_PACKMAN:-"${pkg_man}"}"
    done
    [[ -z "${OS_APP_MAN}" ]] && quit 1 "hspm.bash: no suitable tool found to install software on this machine. Tried: ${KNOWN_PCG_MANAGERS[*]}"
  fi

  cmd="$1"
  shift
  args=("$@")

  shopt -s nocasematch
  case "$cmd" in
    # Install the app
    install)
      [[ "${#}" -le 0 ]] && usage 1
      for next_recipe in "${@}"; do
        echo ''
        install_recipe "${next_recipe}"
      done
      echo ''
      ;;
    # Uninstall the app
    uninstall)
      [[ "${#}" -le 0 ]] && usage 1
      for next_recipe in "${@}"; do
        echo ''
        uninstall_recipe "${next_recipe}"
      done
      echo ''
      ;;
    # Reinstall the app
    reinstall)
      [[ "${#}" -le 0 ]] && usage 1
      for next_recipe in "${@}"; do
        echo ''
        reinstall_recipe "${next_recipe}"
      done
      echo ''
      ;;
    # Recover installed apps
    recover)
      [[ "$1" == "-e" || "$2" == "-e" || "$3" == "-e" ]] && __hhs_open "${BREADCRUMB_FILE}" && exit 0
      [[ "$1" == "-i" || "$2" == "-i" ]] && RECOVER_INSTALL=1
      [[ "$1" == "-t" || "$2" == "-t" ]] && RECOVER_TOOLS=1
      recover_packages
      ;;
    # List available apps
    list)
      list_recipes
      ;;
    *)
      usage 1 "Invalid ${PLUGIN_NAME} command: \"${cmd}\" !"
      ;;
  esac
  shopt -u nocasematch

  quit 0
}

# @purpose: Add a package to the breadcrumb file
function add_breadcrumb() {
  local package="${1}" os="${HHS_MY_OS_RELEASE}"
  grep -qxF "${os}:${package}" "${BREADCRUMB_FILE}" || echo "${os}:${package}" >> "${BREADCRUMB_FILE}"
}

# @purpose: Remove a package to the breadcrumb file
function del_breadcrumb() {
  local package="${1}" os="${HHS_MY_OS_RELEASE}"
  ised -e "/${os}:${package}/d" "${BREADCRUMB_FILE}"
}

# purpose: Unset all declared functions from the recipes
function cleanup_recipes() {
  unset -f _install_ _uninstall_ _depends_ _which_
}

# purpose: List all available hspm recipes
function list_recipes() {

  local index=0 recipe pad_len=20 pad os app all_packages=()

  pad=$(printf '%0.1s' "."{1..60})

  # shellcheck disable=SC2207
  ALL_RECIPES=($(find "${RECIPES_DIR}/${HHS_MY_OS}" -type f -name "*.recipe" | sort))

  if [[ ${#ALL_RECIPES[@]} -le 0 ]]; then
    index=$((index + 1))
    echo -e "${ORANGE}No recipes found matching OS='${HHS_MY_OS}'${NC}"
  fi

  IFS=$'\n' read -r -d '' -a all_packages < <(__hhs_toml_groups "${HSPM_CATALOG_FILE}")
  IFS="${OLDIFS}"

  echo -e "\n${YELLOW}Listing all available hspm '${HHS_MY_OS}' packages ... ${NC}\n"
  for package in "${all_packages[@]}"; do
    [[ "${package}" == 'default' ]] && continue
    recipe="${RECIPES_DIR}/${HHS_MY_OS}/${package}.recipe"
    [[ -s "${recipe}" ]] && printf '%3s + %s' "${index}" "${HHS_HIGHLIGHT_COLOR}${package} "
    [[ -s "${recipe}" ]] || printf '%3s - %s' "${index}" "${WHITE}${package} "
    printf '%*.*s' 0 $((pad_len - ${#package})) "${pad}"
    recipe_about="$(__hhs_toml_get "${HSPM_CATALOG_FILE}" 'about' "${package}")"
    echo -e "${GREEN} => ${WHITE}${recipe_about#*=}${NC}"
    ((index += 1))
  done
  echo -e "\n${YELLOW}Found (${#ALL_RECIPES[@]}) custom recipes."
  echo -e "Packages enlisted with '+' have a custom installation recipe${NC}\n"

  return 0
}

# purpose: Install the specified app using the installation recipe
function install_recipe() {

  local recipe package

  package="${1}"
  recipe="${RECIPES_DIR}/$(uname -s)/${package}.recipe"

  # Source the default recipe, so we can override only what we need
  source "${RECIPES_DIR}/${HHS_MY_OS}/default.recipe"
  package=$(basename "${recipe%\.*}")

  if [[ -f "${recipe}" ]]; then
    source "${recipe}"
    echo -e "${BLUE}Using recipe for \"${package}\""
  else
    echo -e "${YELLOW}Using [${HHS_MY_OS_PACKMAN}] default installation for \"${package}\"!"
  fi

  echo -e "${BLUE}Installing \"${package}\", please wait ..."

  if _depends_ && _install_ "${package}" 1>> "${LOGFILE}"; then
    echo -e "${GREEN}Installation successful => \"${package}\" ${NC}"
    add_breadcrumb "${package}"
    _which_ "${package}" || echo -e "${YELLOW}WARN: Package \"${package}\" did not provide a known binary!${NC}"
  else
    __hhs_errcho "${PLUGIN_NAME}" "Failed to install \"${package}\"! Please type __hhs logs hspm to find out details\n"
  fi
}

# purpose: Uninstall the specified app using the uninstallation recipe
function uninstall_recipe() {

  local recipe package

  package="${1}"
  recipe="${RECIPES_DIR}/$(uname -s)/${package}.recipe"

  # Source the default recipe, so we can override only what we need
  source "${RECIPES_DIR}/${HHS_MY_OS}/default.recipe"
  package=$(basename "${recipe%\.*}")

  if [[ -f "${recipe}" ]]; then
    source "${recipe}"
    echo -e "${BLUE}Using recipe for \"${package}\""
  else
    echo -e "${YELLOW}Using [${HHS_MY_OS_PACKMAN}] default uninstallation recipe for \"${package}\"!"
  fi

  echo -e "${BLUE}Uninstalling \"${package}\", please wait ..."

  if _uninstall_ "${package}" 1>> "${LOGFILE}"; then
    echo -e "${GREEN}Uninstallation successful => \"${package}\" ${NC}"
    del_breadcrumb "${package}"
    _which_ "${package}" && echo -e "${YELLOW}WARN: Package \"${package}\" is yet a known binary !${NC}"
  else
    __hhs_errcho "${PLUGIN_NAME}" "Failed to uninstall \"${package}\" ! Please type __hhs logs hspm to find out details\n"
  fi
}

# purpose: Reinstall the specified app using the uninstallation and installation recipes
function reinstall_recipe() {

  local package

  package="${1}"
  uninstall_recipe "${package}"
  install_recipe "${package}"
}

# @purpose: Install or list all packages previously installed by hspm.
function recover_packages() {

  local index=0 package pad_len=30 pkg pad all_packages=() os=${HHS_MY_OS_RELEASE}

  pad=$(printf '%0.1s' "."{1..80})

  if [[ -n "${RECOVER_INSTALL}" ]]; then
    echo -en "\n${YELLOW}Installing "
  else
    echo -en "\n${YELLOW}Listing "
  fi

  if [[ -z "${RECOVER_TOOLS}" ]]; then
    echo -e "recovered [${HHS_MY_OS}/${HHS_MY_OS_RELEASE}] packages ... "
    while read -r package; do
      all_packages+=("${package}")
    done < <(grep "^${os}:" "${BREADCRUMB_FILE}")
  else
    echo -e "development tools ... "
    # shellcheck disable=SC2206
    all_packages+=(${HHS_DEV_TOOLS[@]})
  fi
  echo "${NC}"

  if [[ -n "${RECOVER_INSTALL}" ]]; then
    for pkg in "${all_packages[@]}"; do
      package="${pkg#*:}"
      if ! command -v "${package}" &> /dev/null; then
        printf '%3s - %s' "${index}" "${BLUE}Installing package ${package} ${NC}"
        printf '%*.*s' 0 $((pad_len - ${#package})) "${pad}"
        if install_recipe "${package}" &> /dev/null; then
          echo -e " [   ${GREEN}OK${NC}   ]"
        else
          echo -e " [ ${RED}FAILED${NC} ]"
        fi
        index=$((index + 1))
      fi
    done
  else
    for pkg in "${all_packages[@]}"; do
      package="${pkg#*:}"
      printf '%3s - %s' "${index}" "${BLUE}${package} "
      printf '%*.*s' 0 $((pad_len - ${#package})) "${pad}"
      command -v "${package}" &> /dev/null && echo -e "${GREEN} INSTALLED${NC}" || echo -e "${RED} NOT INSTALLED${NC}"
      index=$((index + 1))
    done
  fi
  [[ $index -gt 0 ]] || echo "${YELLOW}No previously installed packages were found ${NC}"
  echo ''
}
