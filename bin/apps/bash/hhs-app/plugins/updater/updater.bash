#!/usr/bin/env bash
#shellcheck disable=2181,2034,1090

#  Script: updater.bash
# Purpose: HomeSetup update manager
# Created: Oct 5, 2019
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs/homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2025, HomeSetup team

# Current plugin name
PLUGIN_NAME="updater"

# Current script version.
VERSION=0.9.0

# Namespace cleanup
UNSETS=(
  help version cleanup execute update_hhs stamp_next_update is_updated update_check do_update
)

[[ -s "${HHS_DIR}/bin/app-commons.bash" ]] && source "${HHS_DIR}/bin/app-commons.bash"

# Usage message
read -r -d '' USAGE <<EOF
usage: ${APP_NAME} ${PLUGIN_NAME} {check|update|stamp} [options]

 _   _           _       _
| | | |_ __   __| | __ _| |_ ___ _ __
| | | | '_ \ / _\` |/ _\` | __/ _ \ '__|
| |_| | |_) | (_| | (_| | ||  __/ |
 \___/| .__/ \__,_|\__,_|\__\___|_|
      |_|

  HomeSetup update manager.

    options:
      -h | --help                : Display this help message.
      -v | --version             : Display current plugin version.

    arguments:
      check                      : Fetch the last_update timestamp and report if HomeSetup needs to update.
      update                     : Check for updates and apply them.
      stamp                      : Stamp the next auto-update check for 7 days ahead.

    examples:
      Check whether updates are available:
        => ${APP_NAME} ${PLUGIN_NAME} check
      Run an update:
        => ${APP_NAME} ${PLUGIN_NAME} update

    exit status:
      (0) Success
      (1) Failure due to missing/wrong client input or similar issues
      (2) Failure due to program execution failures

  Notes:
    - Update checks compare the installed version with the repository .VERSION file.

EOF

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

  [[ -z "$1" || "$1" == "-h" || "$1" == "--help" ]] && usage 0
  [[ "$1" == "-v" || "$1" == "--version" ]] && version

  cmd="$1"
  shift
  args=("$@")

  \shopt -s nocasematch
  case "${cmd}" in
    check)
      update_check
    ;;
    update)
      update_hhs
    ;;
    stamp)
      stamp_next_update
    ;;
    *)
      usage 1 "Invalid ${PLUGIN_NAME} command: \"${cmd}\" !"
    ;;
  esac
  \shopt -u nocasematch

  quit 0
}

# @purpose: Check whether the repository version is greater than installed version.
is_updated() {
  IFS='.'
  read -r -a curr_versions <<<"${HHS_VERSION}"
  read -r -a repo_versions <<<"${repo_ver}"
  IFS="${OLDIFS}"
  for idx in "${!repo_versions[@]}"; do
    if [[ ${repo_versions[idx]} -gt ${curr_versions[idx]} ]]; then
      echo ''
      echo -e "${ORANGE}Updates Available: ${NC}"
      echo -e "  => Repository: ${GREEN}v${repo_ver}${NC}, Yours: ${RED}v${HHS_VERSION}${NC}"
      echo ''
      return 1
    fi
  done

  echo -e "${WHITE}Your version of ${GREEN}HomeSetup is up-to-date ${YELLOW}v${HHS_VERSION}${NC}"

  return 0
}

# shellcheck disable=SC2120
# @purpose: Check the current HomeSetup installation and look for updates.
update_hhs() {

  local repo_ver re ai_enabled
  local VERSION_URL='https://github.com/HS-Teams/homesetup/blob/master/.VERSION'

  if [[ -n "${HHS_VERSION}" ]]; then
    clear
    repo_ver="$(curl --silent --fail --connect-timeout 1 --max-time 1 "${VERSION_URL}")"
    re="[0-9]+\.[0-9]+\.[0-9]+"

    if [[ ${repo_ver} =~ $re ]]; then
      if ! is_updated "${repo_ver}"; then
        read -r -n 1 -sp "${YELLOW}Do you want to install the updates now (y/[n])? " ANS
        [[ -n "$ANS" ]] && echo "${ANS}${NC}"
        if [[ "${ANS}" =~ ^[yY]$ ]]; then
          pushd "${HHS_HOME}" &>/dev/null || quit 2
          ai_enabled=$(python3 -m pip show hspylib-askai &>/dev/null && echo '1')
          export GITHUB_ACTIONS="${ai_enabled:-0}"
          if do_update && "${HHS_HOME}/install.bash" -q -r; then
            echo -e "${GREEN}Successfully updated HomeSetup !${NC}"
            echo ''
            echo -e "${YELLOW}${POINTER_ICN}  The updated version will activate after restarting your terminal!${NC}"
            quit 0
          else
            quit 2 "${PLUGIN_NAME}: Failed to update HomeSetup !${NC}"
          fi
          popd &>/dev/null || quit 2
        fi
      fi
      stamp_next_update &>/dev/null
    else
      quit 2 "${PLUGIN_NAME}: Unable to fetch '.VERSION' ! ${repo_ver:-nada}"
    fi
  else
    quit 1 "${PLUGIN_NAME}: HHS_VERSION is undefined. HomeSetup installation is incomplete!"
  fi
  echo -e "${NC}"

  quit 0
}

do_update() {

  local stashed ret_val

  if [[ -n $(git status --porcelain) ]]; then
    git stash --all &>/dev/null || return 1
    stashed=1
  fi
  if git pull --rebase -Xtheirs &>/dev/null; then
    ret_val=0
  else
    ret_val=1
  fi
  [[ $stashed -eq 1 ]] && git stash pop &>/dev/null

  return $ret_val
}

# @purpose: Fetch the last_update timestamp and check if HomeSetup needs to be updated.
update_check() {

  if [[ $(date "+%s%S") -ge $(grep . "${HHS_DIR}"/.last_update) ]]; then
    update_hhs
    return $?
  fi

  stamp_next_update

  return 0
}

# @purpose: Stamp the next update timestamp
stamp_next_update() {

  # Stamp the next update check for next week
  if [[ "macOS" == "${HHS_MY_OS_RELEASE}" ]]; then
    \date -v+7d '+%s%S' 1>"${HHS_DIR}/.last_update" 2>/dev/null
  elif [[ "alpine" == "${MY_OS}" ]]; then
    \date -d "@$(( $(\date +%s) - 3 * 24 * 60 * 60 ))" '+%s%S' 1>"${HHS_DIR}/.last_update" 2>/dev/null
  else
    \date -d '+7 days' '+%s%S' 1>"${HHS_DIR}/.last_update" 2>/dev/null
  fi

  return 0
}
