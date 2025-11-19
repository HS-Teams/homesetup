#!/usr/bin/env bash

#  Script: multi-user-install.bash
# Purpose: Install HomeSetup for multiple users.
# Created: Apr 2, 2023
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs#homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2025, HomeSetup team

RED="\033[31m"
GREEN="\033[32m"
BLUE="\033[34m"
NC="\033[m"

HHS_GITHUB_URL='https://github.com/yorevs/homesetup'

HHS_GROUP="${HHS_GROUP:-homesetup}"

INSTALL_DIR="${1:-/var/lib/homesetup}"

HHS_USERS=("${@:2}")

read -r -d '' USAGE <<EOF
usage: multi-user-install <install_dir> <username...>
    Install HomeSetup under a shared directory for multiple users.
    Creates a common group and adjusts permissions for collaborators.

    options:
      (none)                         : Script behavior is fully driven by arguments.

    arguments:
      install_dir                    : Destination for the shared HomeSetup checkout.
      username...                    : One or more system accounts to enroll in the group.

  Notes:
    - Must be executed as root so the group and permissions can be updated.
    - Uses the HHS_GROUP environment variable when provided (defaults to 'homesetup').
EOF

if [[ $# -le 1 || ${#HHS_USERS[@]} -eq 0 ]]; then
    echo "${USAGE}" && exit 1
fi

if [ "${EUID}" -ne 0 ]; then
    echo -e "${RED}Please execute as root (sudo)${NC}"
    exit 127
fi

# Add the HomeSetup group
if [[ -z $(getent group "${HHS_GROUP}") ]]; then
  echo -e "${BLUE}==> Adding HomeSetup group${NC}"
  groupadd "${HHS_GROUP}"
fi

# Clone/Pull the repository
if [[ -d "${INSTALL_DIR}" ]]; then
  pushd "${INSTALL_DIR}" &>/dev/null || exit 1
  echo -e "${BLUE}==> Pulling HomeSetup project${NC}"
  git pull &>/dev/null
  popd &>/dev/null || exit 1
else
  echo -e "${BLUE}==> Cloning HomeSetup project${NC}"
  git clone "${HHS_GITHUB_URL}.git" "${INSTALL_DIR}" &>/dev/null
fi

# Change the group of HomeSetup files
echo -e "${BLUE}==> Changing the group of HomeSetup files${NC}"
chgrp -R "${HHS_GROUP}" "${INSTALL_DIR}"

# Change the group of /temp dir
echo -e "${BLUE}==> Changing the group of /temp dir${NC}"
chgrp -R "${HHS_GROUP}" "${TEMP}"

# Give read permissions to HomeSetup group
echo -e "${BLUE}==> Giving read permissions to '${HHS_GROUP}' group${NC}"
chmod g+r -R "${INSTALL_DIR}"

# Give read permissions to HomeSetup group
echo -e "${BLUE}==> Giving read permissions to '${HHS_GROUP}' group${NC}"
chmod g+r -R "${TEMP}"

# Add users to the HomeSetup group
for usr in "${HHS_USERS[@]}"; do
  echo -e "${BLUE}==> Adding '${usr}' to '${HHS_GROUP}' group${NC}"
  usermod -a -G "${HHS_GROUP}" "${usr}"
done

echo -e "${GREEN}Installation succeeded !${NC}"
