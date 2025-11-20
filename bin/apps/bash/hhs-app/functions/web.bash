#!/usr/bin/env bash

#  Script: web.bash
# Purpose: Contains HHS-App web based functions.
# Created: Nov 29, 2023
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs#homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2025, HomeSetup team


# @purpose: Open the HomeSetup GitHub page.
function github() {

  local page_url="${HHS_GITHUB_URL}"

  echo -e "${BLUE}${GLOBE_ICN} Opening HomeSetup github page from: ${page_url}${ELLIPSIS_ICN}${NC}"
  __hhs_open "${page_url}" && sleep 2 && quit 0

  quit 2 "Failed to open url: \"${page_url}\" !"
}

# @purpose: Open the HomeSetup GitHub project board.
function board() {

  local page_url="${HHS_GITHUB_URL}/projects/1"

  echo -e "${BLUE}${GLOBE_ICN} Opening HomeSetup board from: ${page_url}${ELLIPSIS_ICN}${NC}"
  __hhs_open "${page_url}" && sleep 2 && quit 0

  quit 2 "Failed to open url: \"${page_url}\" !"
}

# @purpose: Open the HomeSetup GitHub sponsors page.
function sponsor() {

  local page_url="https://github.com/sponsors/yorevs"

  echo -e "${BLUE}${GLOBE_ICN} Opening HomeSetup sponsors page from: ${page_url}${ELLIPSIS_ICN}${NC}"
  __hhs_open "${page_url}" && sleep 2 && quit 0

  quit 2 "Failed to open url: \"${page_url}\" !"
}

# @purpose: Open GitHub docs of the HomeSetup.
function docs() {

  local page_url='https://hs-teams.github.io/homesetup/'

  echo -e "${BLUE}${GLOBE_ICN} Opening HomeSetup docs from: ${page_url}${ELLIPSIS_ICN}${NC}"
  __hhs_open "${page_url}" && sleep 2 && quit 0

  quit 2 "Failed to open url: \"${page_url}\" !"
}
