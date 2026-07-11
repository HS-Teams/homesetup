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
VERSION=1.0.4

# Namespace cleanup
UNSETS=(
  help version cleanup execute cleanup_recipes hspm_recipe_path set_hspm_host_os
  list_recipe_commands hspm_catalog_description
  uninstall_recipe reinstall_recipe list_recipes install_recipe
  add_breadcrumb del_breadcrumb recover_packages sync_packages user_installed_packages
  _install_ _uninstall_ _depends_ _which_ _catalog_ _temurin_version_
)

# Usage message
read -r -d '' USAGE <<EOF
usage: ${APP_NAME} ${PLUGIN_NAME} {install|uninstall|reinstall|list|recover|sync} [options]

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
      -t                           : (recover) Use \${HHS_DEV_TOOLS} as the source for recovery.

    arguments:
      list                         : List all available OS-based installation recipes.
      install <package...>         : Install packages using matching recipes.
      uninstall <package...>       : Uninstall packages using matching recipes.
      reinstall <package...>       : Uninstall and install packages using matching recipes.
      recover                      : Recover packages previously installed by hspm.
      sync                         : Add user-installed package manager packages to the recovery file.

    examples:
      Install a package recipe:
        => ${APP_NAME} ${PLUGIN_NAME} install fzf
      Recover and reinstall previous tools:
        => ${APP_NAME} ${PLUGIN_NAME} recover -i
      Inspect the recovery list without changes:
        => ${APP_NAME} ${PLUGIN_NAME} recover
      Sync user-installed packages into the recovery list:
        => ${APP_NAME} ${PLUGIN_NAME} sync

    exit status:
      (0) Success
      (1) Failure due to missing/wrong client input or similar issues
      (2) Failure due to program execution failures

  Notes:
    - Package manager detection relies on common managers (brew, apt, yum, dnf, apk, pacman).

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
KNOWN_PCG_MANAGERS=('brew' 'apt-get' 'apt' 'yum' 'dnf' 'apk' 'pacman')

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

# @purpose: Select recipes using the operating system executing HSPM.
function set_hspm_host_os() {
  HHS_MY_OS="$(uname -s)"
  export HHS_MY_OS
}

# @purpose: HHS plugin required function
function execute() {

  local cmd args exit_code=0

  [[ -z "$1" || "$1" == "-h" || "$1" == "--help" ]] && usage 0
  [[ "$1" == "-v" || "$1" == "--version" ]] && version

  # Always use the operating system of the host running HSPM. This avoids a
  # stale or SSH-forwarded HHS_MY_OS selecting recipes for another platform.
  set_hspm_host_os

  touch "${BREADCRUMB_FILE}" || quit 1 "Unable to access hspm file: ${BREADCRUMB_FILE}"

  if [[ -z "${HHS_MY_OS_PACKMAN}" ]]; then
    for pkg_man in "${KNOWN_PCG_MANAGERS[@]}"; do
      command -v "${pkg_man}" &> /dev/null && HHS_MY_OS_PACKMAN="${HHS_MY_OS_PACKMAN:-"${pkg_man}"}"
    done
    [[ -z "${HHS_MY_OS_PACKMAN}" ]] && quit 1 \
      "hspm.bash: no suitable tool found to install software on this machine. Tried: ${KNOWN_PCG_MANAGERS[*]}"
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
        install_recipe "${next_recipe}" || exit_code=2
      done
      echo ''
      ;;
    # Uninstall the app
    uninstall)
      [[ "${#}" -le 0 ]] && usage 1
      for next_recipe in "${@}"; do
        echo ''
        uninstall_recipe "${next_recipe}" || exit_code=2
      done
      echo ''
      ;;
    # Reinstall the app
    reinstall)
      [[ "${#}" -le 0 ]] && usage 1
      for next_recipe in "${@}"; do
        echo ''
        reinstall_recipe "${next_recipe}" || exit_code=2
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
    # Sync user-installed package-manager packages into recovery
    sync)
      sync_packages || exit_code=2
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

  quit "${exit_code}"
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

# @purpose: List packages installed explicitly by the user for the active package manager.
function user_installed_packages() {

  case "${HHS_MY_OS_PACKMAN}" in
    brew)
      brew list --formula --installed-on-request
      ;;
    apt | apt-get)
      command -v apt-mark &> /dev/null || {
        echo "apt-mark is required to list manually installed packages." >&2
        return 1
      }
      apt-mark showmanual
      ;;
    dnf | yum)
      "${HHS_MY_OS_PACKMAN}" repoquery --userinstalled --qf '%{name}'
      ;;
    apk)
      apk info --manual
      ;;
    pacman)
      pacman -Qqe
      ;;
    *)
      echo "Unsupported package manager: ${HHS_MY_OS_PACKMAN:-none}" >&2
      return 1
      ;;
  esac
}

# @purpose: Add package-manager user installs absent from the HSPM recovery file.
function sync_packages() {

  local package package_list added_count=0 os=${HHS_MY_OS_RELEASE}

  if ! package_list="$(user_installed_packages)"; then
    __hhs_errcho "${PLUGIN_NAME}" "Unable to list user-installed packages from ${HHS_MY_OS_PACKMAN}."
    return 1
  fi

  while IFS= read -r package; do
    [[ -n "${package}" ]] || continue
    grep -qxF "${os}:${package}" "${BREADCRUMB_FILE}" && continue
    add_breadcrumb "${package}"
    added_count=$((added_count + 1))
  done < <(printf '%s\n' "${package_list}" | LC_ALL=C sort -u)

  if [[ ${added_count} -gt 0 ]]; then
    echo -e "${GREEN}Synchronized ${added_count} user-installed package(s) from ${HHS_MY_OS_PACKMAN}.${NC}"
  else
    echo -e "${YELLOW}HSPM already tracks all user-installed ${HHS_MY_OS_PACKMAN} packages.${NC}"
  fi
}

# purpose: Unset all declared functions from the recipes
function cleanup_recipes() {
  unset -f _install_ _uninstall_ _depends_ _which_ _catalog_ _temurin_version_
}

# @purpose: Return the OS-specific recipe file for a package command.
function hspm_recipe_path() {

  local package="${1}" recipe_name

  recipe_name="${package%%@*}"
  printf '%s/%s.recipe\n' "${RECIPES_DIR}/${HHS_MY_OS}" "${recipe_name}"
}

# @purpose: Print command names supplied by one HSPM recipe file.
function list_recipe_commands() {

  local recipe="${1}" recipe_name

  cleanup_recipes
  # shellcheck disable=SC1090
  source "${recipe}"
  if declare -F _catalog_ >/dev/null; then
    _catalog_
  else
    recipe_name="$(basename "${recipe%.recipe}")"
    printf '%s\n' "${recipe_name}"
  fi
  cleanup_recipes
}

# @purpose: Return the catalog description associated with a recipe command.
function hspm_catalog_description() {

  local package="${1}" base_package description

  description="$(
    __hhs_toml_get "${HSPM_CATALOG_FILE}" 'about' "${package}" || true
  )"
  if [[ -z "${description}" ]]; then
    base_package="${package%%@*}"
    description="$(
      __hhs_toml_get "${HSPM_CATALOG_FILE}" 'about' "${base_package}" || true
    )"
  fi
  description="${description#*=}"
  [[ -n "${description}" ]] || description='No description available.'
  printf '%s' "${description}"
}

# @purpose: List all available recipes for the current operating system.
function list_recipes() {

  local index=0 recipe package description pad_len=20 pad recipe_dir

  pad=$(printf '%0.1s' "."{1..60})
  set_hspm_host_os
  recipe_dir="${RECIPES_DIR}/${HHS_MY_OS}"

  ALL_RECIPES=()
  if [[ ! -d "${recipe_dir}" ]]; then
    echo -e "${ORANGE}No recipes found matching OS='${HHS_MY_OS}'${NC}"
    return 0
  fi
  while IFS= read -r recipe; do
    [[ "${recipe##*/}" == 'default.recipe' ]] && continue
    ALL_RECIPES+=("${recipe}")
  done < <(find "${recipe_dir}" -maxdepth 1 -type f -name "*.recipe" -print | sort)

  if [[ ${#ALL_RECIPES[@]} -le 0 ]]; then
    echo -e "${ORANGE}No recipes found matching OS='${HHS_MY_OS}'${NC}"
    return 0
  fi

  echo -e "\n${YELLOW}Listing all available hspm '${HHS_MY_OS}' packages ... ${NC}\n"
  for recipe in "${ALL_RECIPES[@]}"; do
    while IFS= read -r package; do
      [[ -n "${package}" ]] || continue
      description="$(hspm_catalog_description "${package}")"
      printf '%3s + %s' "${index}" "${HHS_HIGHLIGHT_COLOR}${package} "
      printf '%*.*s' 0 $((pad_len - ${#package})) "${pad}"
      echo -e "${GREEN} => ${WHITE}${description}${NC}"
      ((index += 1))
    done < <(list_recipe_commands "${recipe}")
  done
  echo -e "\n${YELLOW}Found (${#ALL_RECIPES[@]}) custom recipes."
  echo -e "Catalog descriptions are read from ${HSPM_CATALOG_FILE}${NC}\n"

  return 0
}

# purpose: Install the specified app using the installation recipe
function install_recipe() {

  local recipe package

  package="${1}"
  recipe="$(hspm_recipe_path "${package}")"

  # Source the default recipe, so we can override only what we need
  source "${RECIPES_DIR}/${HHS_MY_OS}/default.recipe"

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
    return 0
  else
    __hhs_errcho "${PLUGIN_NAME}" "Failed to install \"${package}\"! Please type __hhs logs hspm to find out details\n"
    return 2
  fi
}

# purpose: Uninstall the specified app using the uninstallation recipe
function uninstall_recipe() {

  local recipe package

  package="${1}"
  recipe="$(hspm_recipe_path "${package}")"

  # Source the default recipe, so we can override only what we need
  source "${RECIPES_DIR}/${HHS_MY_OS}/default.recipe"

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
    return 0
  else
    __hhs_errcho "${PLUGIN_NAME}" "Failed to uninstall \"${package}\" ! Please type __hhs logs hspm to find out details\n"
    return 2
  fi
}

# purpose: Reinstall the specified app using the uninstallation and installation recipes
function reinstall_recipe() {

  local package exit_code=0

  package="${1}"
  uninstall_recipe "${package}" || exit_code=2
  install_recipe "${package}" || exit_code=2
  return "${exit_code}"
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
