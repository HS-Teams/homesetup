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

# TC - 2
@test "when-loading-hhs-bindings-then-tab-should-use-standard-completion" {
  run bash --noprofile --norc -i -c "bind -f '${HHS_HOME}/dotfiles/hhs-bindings'; bind -q complete; bind -q menu-complete"
  assert_success
  assert_output --partial 'complete can be invoked via "\C-i"'
  assert_output --partial 'menu-complete can be invoked via "\e[Z"'
}

# TC - 3
@test "when-ssh-config-is-missing-then-ssh-completion-should-not-print-errors" {
  run bash --noprofile --norc -c "HOME='${BATS_TEST_TMPDIR}' source '${HHS_HOME}/bin/completions/bash/ssh-completion.bash'; COMP_WORDS=(ssh h); __ssh_complete"
  assert_success
  assert_output ''
}

# TC - 4
@test "when-bash-completion-library-is-missing-then-gtrash-fallback-should-not-print-errors" {
  run bash --noprofile --norc -c "source '${HHS_HOME}/bin/completions/bash/gtrash-completion.bash'; COMP_WORDS=(gtrash); COMP_CWORD=0; __gtrash_init_completion -n =:; printf '%s:%s:%s' \"\${cur}\" \"\${prev}\" \"\${cword}\""
  assert_success
  assert_output 'gtrash::0'
}
