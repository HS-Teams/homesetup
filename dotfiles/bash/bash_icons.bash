#!/usr/bin/env bash
# shellcheck disable=SC1090,SC2034

#  Script: bash_icons.bash
# Purpose: This file is used to hold all terminal icon definitions
# Created: Nov 28, 2023
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs/homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2025, HomeSetup team

# !NOTICE: Do not change this file. To customize your icons edit the file ~/.env

# Do not source this file multiple times
if list_contains "${HHS_ACTIVE_DOTFILES}" "bash_icons"; then
  __hhs_log "DEBUG" "$0 was already loaded!"
else

  export HHS_ACTIVE_DOTFILES="${HHS_ACTIVE_DOTFILES} bash_icons"

  # Droid Icons
  ALERT_ICN="\xef\x91\xae"  # 
  ALIAS_ICN="\xef\x81\xa1"  # 
  CHECK_ICN="\xef\x81\x98"  # 
  CROSS_ICN="\xef\x81\x97"  # 
  ELLIPSIS_ICN="\xe2\x80\xa6"  # …
  ERROR_ICN="\xe2\x9c\x98"  # ✘
  FAIL_ICN="\xef\x91\xa7"  # 
  FUNC_ICN="\xef\x84\xa1"  # 
  GLOBE_ICN="\xef\x82\xac" # 
  HAND_PEACE_ICN='\xef\x89\x9b'  # 
  HELP_ICN="\xef\x81\x99"  # 
  OFF_SWITCH_ICN="\xef\x88\x84"  # 
  ON_SWITCH_ICN="\xef\x88\x85"  # 
  UNMARKED_ICN="\xef\x98\xb0"  # 
  MARKED_ICN="\xef\x98\xb4"  # 
  PASS_ICN="\xef\x98\xac"  # 
  PLUG_IN_ICN="\xef\x84\xae"  # 
  POINTER_ICN='\xef\x90\xb2'  # 
  SKIP_ICN="\xef\x91\xa8"  # 
  STAR_ICN="\xef\x80\x85"  # 
  SUCCESS_ICN="\xef\x98\xab"  # 
  TIP_ICON="\xef\x90\x80"  # 
  WARN_ICON="\xef\x81\xb1"  # 
  FOLDER_ICON="\xef\x84\x94"  # 
  UNKNOWN_ICON="\xef\x8a\x9c" # 
  LINK_ICON="\xef\x92\x82"  # 
  FOLDER_LINK_ICON="\xef\x92\x82"  # 
fi
