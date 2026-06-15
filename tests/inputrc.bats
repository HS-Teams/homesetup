#!/usr/bin/env bats

#  Script: inputrc.bats
# Purpose: Readline inputrc configuration tests.
# Created: Jun 15, 2026
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs/homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2026, HomeSetup team

load test_helper
load_bats_libs

# TC - 1
@test "when-loading-inputrc-then-tab-should-use-standard-completion" {
  run bash --noprofile --norc -i -c "bind -f '${HHS_HOME}/dotfiles/inputrc'; bind -q complete; bind -q menu-complete"
  assert_success
  assert_output --partial 'complete can be invoked via "\C-i"'
  assert_output --partial 'menu-complete can be invoked via "\e[Z"'
}
