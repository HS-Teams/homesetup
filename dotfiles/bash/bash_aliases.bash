#!/usr/bin/env bash
# shellcheck disable=2035,2139

#  Script: bash_aliases.bash
# Purpose: This file is used to configure some useful shell aliases
# Created: Aug 26, 2018
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs/homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2025, HomeSetup team

# !NOTICE: Do not change this file. To customize your aliases edit the file ~/.aliases
# inspiRED by: https://github.com/mathiasbynens/dotfiles

# Do not source this file multiple times
if list_contains "${HHS_ACTIVE_DOTFILES}" "bash_aliases"; then
  __hhs_log "DEBUG" "$0 was already loaded!"
else

  export HHS_ACTIVE_DOTFILES="${HHS_ACTIVE_DOTFILES} bash_aliases"

  # -----------------------------------------------------------------------------------
  # @category: Navigational

  # @alias: Change-back to previous directory
  alias ..='__hhs_changeback_ndirs'
  # @alias: Change-back two previous directories
  alias ...='.. 2'
  # @alias: Change-back three previous directories
  alias ....='.. 3'
  # @alias: Change-back four previous directories
  alias .....='.. 4'
  # @alias: Change the current directory to HOME dir
  alias ~='cd ~'
  # @alias: Change the current directory to the previous dir
  alias -- -='cd -'
  # @alias: Display the current working dir and remote repository if it applies
  alias \?='__hhs_where_am_i'

  # -----------------------------------------------------------------------------------
  # @category: General

  # @alias: Shorthand for `exit 0' from terminal
  alias q="exit 0"
  # @alias: Enable aliases to be sudo’ed
  alias sudo='sudo '

  if __hhs_has 'colorls'; then
    # @alias: Use colorls instead or built-in `ls'
    alias ls='\colorls --dark --group-directories-first --git-status'
    # @alias: [colorls] List all files colorized in long format
    alias l='ls --long'
    # @alias: [colorls] List all directories in long format
    alias ld='l --dirs'
    # @alias: [colorls] List all files in long format
    alias lf='l --files'
    # @alias: [colorls] List all files and folders colorized in long format, including dot files
    alias ll='l --all'
    # @alias: [colorls] List all .dotfiles colorized in long format
    alias lll='lf --all'
    # @alias: [colorls] List all .dotfolders colorized in long format
    alias lld='ld --all'
  else
    # @alias: Always use color output for `ls'
    alias ls='\ls ${COLOR_FLAG}'
    # @alias: List all files colorized in long format
    alias l='ls -lhF'
    # @alias: List all directories colorized in long format
    alias ld='ls -d -lah */ 2> /dev/null'
    # @alias: List all files colorized in long format
    alias lf='ls -lahd ??* | grep --color=never "^-"'
    # @alias: List all files and folders colorized in long format, including dot files
    alias ll='ls -lahF'
    # @alias: List all .dotfiles colorized in long format
    alias lll='ls -lahd .??* 2> /dev/null | grep --color=never "^-"'
    # @alias: List all .dotfolders colorized in long format
    alias lld='ls -d -lah .??*/ 2> /dev/null'
  fi

  if __hhs_has 'delta'; then
    # @alias: Replacement for diff using colors and split panels using delta
    alias diff='delta'
  elif __hhs_has 'sdiff' && __hhs_has 'colordiff'; then
    # @alias: Replacement for diff using colors and split panels using sdiff + colordiff
    alias diff='sdiff --diff-program=colordiff'
  fi

  # @alias: Always enable colored `grep` output
  # Note: `GREP_OPTIONS="--color=auto"` is deprecated, hence the alias usage.
  alias grep='\grep --color=auto'
  # @alias: Always enable colored `fgrep` output
  alias fgrep='\fgrep --color=auto'
  # @alias: Always enable colored `egrep` output
  alias egrep='\egrep --color=auto'

  # @alias: Built-ins replacement for `cd'
  alias cd='__hhs_change_dir'
  # @alias: Built-ins replacement for `dirs'
  alias dirs='__hhs_dirs'
  # @alias: Built-ins replacement for `cat'
  __hhs_has "bat" && alias cat='bat --paging=never --style=header,grid'
  # @alias: Built-ins replacement for `help'
  alias help='__hhs help'
  # @alias: Starship replacement for `starship' binary
  alias starship='__hhs_starship'
  # @alias: Shortcut for `gtrash put' binary
  alias del='gtrash put'
  # @alias: By default `rm' will prompt for confirmation and will be verbose
  alias rm='\rm -iv'
  # @alias: By default `cp' will prompt for confirmation and will be verbose
  alias cp='\cp -iv'
  # @alias: By default `mv' will prompt for confirmation and will be verbose
  alias mv='\mv -iv'
  # @alias: Make `df' command output pretty and human readable format
  alias df='\df -H'
  # @alias: Make `ps' command output pretty and human readable format
  alias psg='\ps aux | \grep -v grep | \grep -i -e VSZ -e'
  # @alias: Make `du' command output pretty and human readable format
  alias du='__hhs_du'
  # @alias: Use the assigned app to open a file
  alias open="__hhs_open"
  # @alias: Display/Set/unset current Shell Options
  alias shopt="__hhs_shopt"

  if __hhs_has nvim; then
    # @alias: Use `nvim' instead of `vi' if installed
    alias vi='nvim'
  elif __hhs_has "vim"; then
    # @alias: Use `vim' instead of `vi' if installed
    alias vi='vim'
  fi

  # @alias: `more' will interpret escape sequences
  __hhs_has "more" && alias more='\more -r'
  # @alias: `less' will interpret escape sequences
  __hhs_has "less" && alias less='\less -r'
  # @alias: Make `mount' command output pretty and human readable format
  alias mount='\mount | column -t'

  # @alias: Date&Time - Display current week number
  alias week='\date +%V'
  # @alias: Date&Time - Display current date and time
  alias now='\date +"(Week:%V) %Y-%m-%d %T %Z"'
  # @alias: Date&Time - Display current timestamp
  alias ts='\date "+%s"'

  # @alias: If `wget' is not available, use `curl' instead
  __hhs_has "wget" || alias wget='\curl -O'

  # @alias: Make PS1 prompt active
  alias ps1='export PS1=$PS1_STYLE'
  # @alias: Make PS2 prompt active (continuation prompt)
  alias ps2='export PS1=$PS2_STYLE'

  # @alias: Jenv - Set JAVA_HOME using jenv
  __hhs_has "jenv" && alias jenv_set_java_home='export JAVA_HOME="${HOME}/.jenv/versions/`jenv version-name`"'

  # @alias: Dropbox - Recursively delete Dropbox conflicted files from the current directory
  [[ -d "${DROPBOX}" ]] && alias cleanup-db="find . -name *\ \(*conflicted* -exec rm -v {} \;"

  # @alias: Shortcut for base64 encode
  __hhs_has "base64" && alias encode="base64"

  # -----------------------------------------------------------------------------------
  # @category: OS Specific aliases

  # Linux boxes have a different syntax for some commands, so we create the alias to match the correct OS.
  case "${HHS_MY_OS}" in

  Linux)
    # @alias: `top' shortcut ordered by CPU%
    alias cpu='\top -o %CPU'
    # @alias: `top' shortcut ordered by MEM%
    alias mem='\top -o %MEM'
    # @alias: Shortcut for base64 decode
    __hhs_has "base64" && alias decode='base64 -d'
    # @alias: Shortcut for base64 decode
    __hhs_has "apt-get" && alias apt='apt-get'
    ;;

  Darwin)
    # @alias: `top' shortcut ordered by CPU%
    alias cpu='\top -o cpu'
    # @alias: `top' shortcut ordered by MEM%
    alias mem='\top -o rsize'
    # @alias: Shortcut for base64 decode
    __hhs_has "base64" && alias decode='base64 -D'
    # @alias: Delete all .DS_store files recursively
    alias cleanup-ds="find . -type f -name '*.DS_Store' -ls -delete"
    # @alias: Flush Directory Service cache
    __hhs_has "dscacheutil" && alias flush="dscacheutil -flushcache && killall -HUP mDNSResponder"
    # @alias: Clean up LaunchServices to remove duplicates in the "Open With" menu
    alias cleanup-reg="/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -kill -r -domain local -domain system -domain user && killall Finder"
    # @alias: Show hidden files in Finder
    alias show-files="defaults write com.apple.finder AppleShowAllFiles -bool true && killall Finder"
    # @alias: Hide hidden files in Finder
    alias hide-files="defaults write com.apple.finder AppleShowAllFiles -bool false && killall Finder"
    # @alias: Show all desktop icons
    alias show-deskicons="defaults write com.apple.finder CreateDesktop -bool true && killall Finder"
    # @alias: Hide all desktop icons
    alias hide-deskicons="defaults write com.apple.finder CreateDesktop -bool false && killall Finder"
    if __hhs_has "hexdump"; then
      # @alias: Display current value of IFS
      alias ifs='echo -en "${IFS}" | hexdump -C'
      # @alias: Canonical hex dump; some systems have this symlinked
      __hhs_has "hd" || alias hd='hexdump -C'
    fi
    # @alias: If `md5sum' is not available, use `md5' instead`
    __hhs_has "md5sum" || alias md5sum='md5'
    # @alias: If `sha1' is not available, use `shasum' instead`
    __hhs_has "sha1" || alias sha1='shasum'
    ;;
  esac

  # -----------------------------------------------------------------------------------
  # @category: Handy Terminal Shortcuts

  case "${HHS_MY_SHELL}" in

  bash)
    # @alias: Make terminal cursor visible (Bash)
    alias show-cursor='tput cnorm'
    # @alias: Make terminal cursor invisible (Bash)
    alias hide-cursor='tput civis'
    # @alias: Save terminal cursor position (Bash)
    alias save-cursor-pos='tput sc'
    # @alias: Restore terminal cursor position (Bash)
    alias restore-cursor-pos='tput rc'
    # @alias: Enable terminal line wrap (Bash)
    alias enable-line-wrap='tput smam'
    # @alias: Disable terminal line wrap (Bash)
    alias disable-line-wrap='tput rmam'
    # @alias: Enable terminal echo (Bash)
    alias enable-echo='stty echo -raw'
    # @alias: Disable terminal echo (Bash)
    alias disable-echo='stty raw -echo min 0'
    # @alias: Reset all terminal cursor attributes (Bash)
    alias reset-cursor-attrs='show-cursor; enable-line-wrap; enable-echo'
    # @alias: Save the current terminal screen
    alias save-screen='tput smcup'
    # @alias: Load the saved terminal screen
    alias restore-screen='tput rmcup'
    ;;
  esac

  # -----------------------------------------------------------------------------------
  # @category: Python & HomeSetup aliases

  # @alias: Evaluate mathematical expressions
  alias __hhs_calc='python3 -c "import sys, math; print(eval(\"\".join(sys.argv[1:])))"'
  # @alias: URL-encode strings
  alias __hhs_urle='python3 -c "import sys; from urllib import parse as ul; print(ul.quote(\" \".join(sys.argv[1:])))"'
  # @alias: URL-decode strings
  alias __hhs_urld='python3 -c "import sys; from urllib import parse as ul; print(ul.unquote(\" \".join(sys.argv[1:])))"'
  # @alias: Generate a UUID
  alias __hhs_uuid='python3 -c "import uuid as ul; print(ul.uuid4())"'

  # @alias: Reload HomeSetup
  alias __hhs_reload='__hhs_clear; exec ${HHS_MY_SHELL} -l'
  # @alias: Clear and reset all cursor attributes and IFS
  alias __hhs_clear='reset-cursor-attrs; echo -en "\033[2J\033[H${NC}"; export IFS="${OLDIFS}"'
  # @alias: Clear the screen and reset the terminal
  alias __hhs_reset="__hhs_clear; \reset"
  # @alias: Shortcut for hhs hspm plug-in
  alias __hhs_hspm='__hhs hspm execute'
  # @alias: Shortcut for hhs updater plug-in
  alias __hhs_hhu='__hhs updater execute'
  # @alias: Shortcut for hhs starship plug-in
  alias __hhs_starship='__hhs starship execute'
  # @alias: Shortcut for hhs setup plug-in
  alias __hhs_setup='__hhs setup execute'
  # @alias: Shortcut for hhs service plug-in
  alias __hhs_services='__hhs services execute'
  # @alias: Shortcut for hhs ask plug-in (offline ollama AI)
  alias __hhs_ask="__hhs ask execute"

  # The following aliases requires HomeSetup python venv to be active
  if __hhs_is_venv; then
    # @alias: Shortcut for hspylib-clitt module
    alias __hhs_clitt="__hhs_ensure_venv '__hhs_clitt' && python3 -m clitt"
    # @alias: Shortcut for the HomeSetup TimeCalc widget
    alias __hhs_tcalc="__hhs_ensure_venv '__hhs_tcalc' && __hhs_clitt widgets TimeCalc"
    # @alias: Shortcut for hspylib-vault module
    alias __hhs_vault="__hhs_ensure_venv '__hhs_vault' && python3 -m vault"
    # @alias: Shortcut for hspylib-cfman module
    alias __hhs_cfman="__hhs_ensure_venv '__hhs_cfman' && python3 -m cfman"
    # @alias: Shortcut for hspylib-kafman module
    alias __hhs_kafman="__hhs_ensure_venv '__hhs_kafman' && python3 -m kafman"
    # @alias: Shortcut for hhs firebase plug-in
    alias __hhs_firebase="__hhs_ensure_venv '__hhs_firebase' && __hhs firebase execute"
    # @alias: Shortcut for hhs settings plug-in
    alias __hhs_settings="__hhs_ensure_venv '__hhs_settings' && __hhs settings execute"

    if [[ ${HHS_AI_ENABLED} -eq 1 ]] && __hhs_has_module 'hspylib-askai'; then
      # @alias: Shortcut for the AskAI python module
      alias taius="__hhs_ensure_venv 'taius' && python3 -m askai"
    fi
  fi

  # @alias: Remove escape (\EscXX) codes from text
  alias clean_escapes="__hhs_clean_escapes"
  # @alias: Copy to clipboard removing any escape sequences
  alias clipboard="__hhs_clean_escapes | __hhs_clipboard"

  # -----------------------------------------------------------------------------------
  # @category: Git aliases

  # @alias: Git - Enhancement for `git status'
  alias __hhs_git_status='git status && gl -n 1'
  # @alias: Git - Shortcut for `git fetch'
  alias __hhs_git_fetch='git fetch -p'
  # @alias: Git - Shortcut for `git log'
  alias __hhs_git_history='git log -p'
  # @alias: Git - Shortcut for `git branch'
  alias __hhs_git_branch='git branch'
  # @alias: Git - Shortcut for `git diff'
  alias __hhs_git_diff='git diff'
  # @alias: Git - Shortcut for `git pull'
  alias __hhs_git_pull='git pull'
  # @alias: Git - Enhancement for `git log'
  alias __hhs_git_log='git log --oneline --graph --decorate --pretty=format:"%C(blue)%h%C(red)%d %C(yellow)(%cr) %C(cyan)<%ce> %C(white)\"%s\"%Creset"'
  # @alias: Git - Shortcut for `git checkout'
  alias __hhs_git_checkout='git checkout'
  # @alias: Git - Shortcut for `git commit'
  alias __hhs_git_commit='git commit -m'
  # @alias: Git - Shortcut for `git commit amend'
  alias __hhs_git_amend='git commit --amend --no-edit'
  # @alias: Git - Shortcut for `git pull rebase'
  alias __hhs_git_pull_rebase='git pull --rebase --autostash --all --verbose --no-recurse-submodules'
  # @alias: Git - Shortcut for `git push'
  alias __hhs_git_push='git push origin HEAD'
  # @alias: Git - Enhancement for `git diff-tree'
  alias __hhs_git_show='git diff-tree --no-commit-id --name-status -r'
  # @alias: Git - Enhancement for `git difftool'
  alias __hhs_git_difftool='git difftool -t opendiff'

  # -----------------------------------------------------------------------------------
  # @category: Gradle aliases

  if __hhs_has "gradle"; then

    # @alias: Gradle - Enhancement for `gradle build'
    alias __hhs_gradle_build='gw clean build'
    # @alias: Gradle - Enhancement for `gradle bootRun'
    alias __hhs_gradle_run='gw bootRun -x Test'
    # @alias: Gradle - Shortcut for `gradle Test'
    alias __hhs_gradle_test='gw Test'
    # @alias: Gradle - Shortcut for `gradle init'
    alias __hhs_gradle_init='gw init'
    # @alias: Gradle - Shortcut for `gradle -q'
    alias __hhs_gradle_quiet='gw -q'
    # @alias: Gradle - Shortcut for `gradle wrapper'
    alias __hhs_gradle_wrapper='gw wrapper --gradle-version'
    # @alias: Gradle -  Displays all available gradle projects
    alias __hhs_gradle_projects='gw -q projects'
    # @alias: Gradle - Displays all available gradle project tasks
    alias __hhs_gradle_tasks='gw -q :tasks --all'
  fi

  # -----------------------------------------------------------------------------------
  # @category: Docker aliases

  # inspiRED by https://hackernoon.com/handy-docker-aliases-4bd85089a3b8
  if [[ -n "${HHS_HAS_DOCKER}" ]]; then

    # @alias: Docker - Enhancement for `docker images'
    alias __hhs_docker_images='docker images | hl "(REPOSITORY|TAG|IMAGE ID|CREATED|SIZE|$)"'
    # @alias: Docker - Shortcut for `docker service'
    alias __hhs_docker_service='docker service'
    # @alias: Docker - Shortcut for `docker container rm'
    alias __hhs_docker_remove='docker container rm'
    # @alias: Docker - Shortcut for `docker rmi'
    alias __hhs_docker_remove_image='docker rmi'
    # @alias: Docker - Enhancement for `docker ps'
    alias __hhs_docker_ps='docker ps -a --format "table {{.ID}}\t{{.Names}}\t{{.Image}}\t{{.Ports}}\t{{.Status}}"'
    # @alias: Docker - Enhancement for `docker stats'
    alias __hhs_docker_top='docker stats --format "table {{.Container}}\t{{.Name}}\t{{.CPUPerc}}\t{{.NetIO}}\t{{.BlockIO}}"'
    # @alias: Docker - Enhancement for `docker container ls'
    alias __hhs_docker_ls='docker container ls -a'
    # @alias: Docker - Enhancement for `docker compose up'
    alias __hhs_docker_up='docker-compose up --force-recreate --build --remove-orphans --detach'
    # @alias: Docker - Shortcut for `docker compose stop'
    alias __hhs_docker_down='docker-compose stop'
  fi

fi
