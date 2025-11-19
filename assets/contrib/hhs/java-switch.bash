#!/usr/bin/env bash

#  Script: java-switch.bash
# Purpose: Seamless switch between installed JDK versions.
# Created: Mar 29, 2022
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs#homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2025, HomeSetup team

JDK_SEARCH_DIR=${JDK_SEARCH_DIR:-"/Library/Java/JavaVirtualMachines"}

read -r -d '' USAGE <<EOF
usage: sudo java-switch <jdk_version>
    Point /Library/Java/JavaVirtualMachines/Current to a specific JDK.
    Requires sudo privileges and an installed JDK under ${JDK_SEARCH_DIR}.

    options:
      (none)                         : Provide the desired JDK version as the sole argument.

    arguments:
      jdk_version                    : Major version to activate (e.g. 17, 21).

  Notes:
    - The script updates the 'Current' symlink after verifying the target exists.
    - Run with sudo to ensure permissions allow modifying the JDK directory.
EOF

RED="\033[31m"
GREEN="\033[32m"
BLUE="\033[34m"
NC="\033[m"

if [[ ! -d "${JDK_SEARCH_DIR}" && ! -L "${JDK_SEARCH_DIR}" ]]; then
    echo -e "${RED}Unable to find the JDK search dir: '${JDK_SEARCH_DIR}'${NC}" && exit 1
fi

if [[ $# -ne 1 ]]; then
    echo "${USAGE}" && exit 1
fi

if [ "${EUID}" -ne 0 ]; then
    echo -e "${RED}Please execute as root (sudo)${NC}"
    exit 127
fi

echo -e "${BLUE}[JDK] Checking for installed JDK versions at: '\033[34m${JDK_SEARCH_DIR}${NC}'..."
for jdk_ver in "${JDK_SEARCH_DIR}"/**.jdk; do

    jdk="$(basename "${jdk_ver}")"
    jdk_ver="${jdk%%\.*}"
    jdk_ver="${jdk_ver#*\-}"

    [[ "$jdk_ver" -eq "$1" ]] && TO_JDK="${jdk}"

    if [[ -n "${TO_JDK}" ]]; then
        echo -e "${BLUE}[JDK] Switching to JDK: '${GREEN}${TO_JDK}${NC}'"
        [[ -L "${JDK_SEARCH_DIR}/Current" ]] && sudo rm -f "${JDK_SEARCH_DIR}/Current"
        if [[ -d "${JDK_SEARCH_DIR}/${TO_JDK}" || -L "${JDK_SEARCH_DIR}/${TO_JDK}" ]]; then
            echo -n "${BLUE}[JDK] "
            sudo ln -sfv "${JDK_SEARCH_DIR}/${TO_JDK}" "${JDK_SEARCH_DIR}/Current"
            [[ -d "${JDK_SEARCH_DIR}/Current" || -L "${JDK_SEARCH_DIR}/Current" ]] && { echo -e "${NC}"; exit 0; }
        else
            echo -e "${RED}[JDK] Unable to find required JDK -> ${TO_JDK}${NC}" && exit 1
        fi
    fi

done

echo -e "${RED}[JDK] Unable to find required JDK -> ${1}${NC}" && exit 1
