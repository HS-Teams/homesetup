#!/usr/bin/env bash
# shellcheck disable=SC2155

#  Script: bash_env.bash
# Purpose: This file is used to configure shell environment variables
# Created: Aug 26, 2018
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs/homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2025, HomeSetup team

# !NOTICE: Do not change this file. To customize your environment variables edit the file ~/.env

# Do not source this file multiple times
if list_contains "${HHS_ACTIVE_DOTFILES}" "bash_env"; then
  __hhs_log "DEBUG" "$0 was already loaded!"
else

  export HHS_ACTIVE_DOTFILES="${HHS_ACTIVE_DOTFILES} bash_env"

  # ----------------------------------------------------------------------------
  # System folders
  export TEMP="${TEMP:-${TMPDIR:-$(dirname "$(mktemp)")}}"
  export TRASH="${TRASH:-${HOME}/.Trash}"

  # Preferred editor
  if [[ -z "${EDITOR}" ]]; then
    __hhs_has "nvim" && export EDITOR="nvim"
  elif [[ -z "${EDITOR}" ]]; then
    __hhs_has "vim" && export EDITOR="vim"
  else
    __hhs_has "vi" && export EDITOR="${EDITOR:-vi}"
  fi

  # ----------------------------------------------------------------------------
  # Home Sweet Home

  # Java
  if [[ -z "${JAVA_HOME}" ]] && __hhs_has java; then
    export JAVA_HOME=${JAVA_HOME:-"/Library/Java/JavaVirtualMachines/Current/Contents/Home"}
    export JDK_HOME="${JDK_HOME:-$JAVA_HOME}"
  fi

  # Python
  [[ -z "${PYTHON_HOME}" && -d "/Library/Python/Current" ]] \
    && export PYTHON_HOME=${PYTHON_HOME:-"/Library/Python/Current"}

  # ----------------------------------------------------------------------------
  # OS Release

  # Darwin
  if [[ "Darwin" == "$(uname -s)" ]]; then
    # Hide the annoying warning about zsh
    export BASH_SILENCE_DEPRECATION_WARNING=${BASH_SILENCE_DEPRECATION_WARNING:-1}
    # OS Release - Darwin
    export HHS_MY_OS_RELEASE="$(sw_vers -productName)"
    export HHS_MY_OS_PACKMAN='brew'
    if command -v xcode-select &> /dev/null; then
      export XCODE_HOME=$(xcode-select -p)
      if [[ -d "${XCODE_HOME}/Platforms/MacOSX.platform/Developer/SDKs/MacOSX.sdk" ]]; then
        export MACOS_SDK="${XCODE_HOME}/Platforms/MacOSX.platform/Developer/SDKs/MacOSX.sdk"
      elif [[ -d "${XCODE_HOME}/SDKs/MacOSX" ]]; then
        export MACOS_SDK="${XCODE_HOME}/SDKs/MacOSX"
      fi
    fi
  # Linux
  else
    HHS_MY_OS_RELEASE="$(grep '^ID=' '/etc/os-release' 2> /dev/null)"
    HHS_MY_OS_RELEASE="${HHS_MY_OS_RELEASE#*=}"
    export HHS_MY_OS_RELEASE="${HHS_MY_OS_RELEASE//\"/}"
    if command -v 'apt-get' &> /dev/null; then
      export HHS_MY_OS_PACKMAN='apt-get'
    elif command -v 'dnf' &> /dev/null; then
      export HHS_MY_OS_PACKMAN='dnf'
    elif command -v 'apt' &> /dev/null; then
      export HHS_MY_OS_PACKMAN='apt'
    elif command -v 'apk' &> /dev/null; then
      export HHS_MY_OS_PACKMAN='apk'
    elif command -v 'pacman' &> /dev/null; then
      export HHS_MY_OS_PACKMAN='pacman'
    else
      export HHS_MY_OS_PACKMAN=''
      __hhs_log "WARN" "Unable to find a proper package manager"
    fi
  fi

  # ----------------------------------------------------------------------------
  # Bash History

  # History control ( ignore duplicates and spaces ).
  export HISTCONTROL=${HISTCONTROL:-"ignoreboth:erasedups"}
  # Ignored history commands
  export HISTIGNORE="?:??:exit:pwd:clear"
  # Max. history size.
  export HISTSIZE=2000
  # Max. history file size.
  export HISTFILESIZE=2000
  # Setting history format: Index [<User>, <Date> <Time>] command
  export HISTTIMEFORMAT="[${USER}, %F %T]  "
  # Bash history file.
  export HISTFILE="${HOME}/.bash_history"
  # Do not share history between concurrent Bash sessions do speedup initialization.
  unset PROMPT_COMMAND

  # ----------------------------------------------------------------------------
  # HomeSetup variables

  export HHS_GITHUB_URL='https://github.com/HS-Teams/homesetup'
  export HHS_ASKAI_URL='https://github.com/HS-Teams/askai'
  export HHS_HAS_DOCKER=$(__hhs_has docker && docker info &> /dev/null && echo '1')
  export HHS_AI_ENABLED=$(__hhs_has_module hspylib-askai &>/dev/null && echo '1')

  # ----------------------------------------------------------------------------
  # Module configs

  export HHS_ALIASES_FILE="${HHS_DIR}/.aliases"
  export HHS_CMD_FILE="${HHS_DIR}/.cmd_file"
  export HHS_ENV_FILE="${HHS_DIR}/.env"
  export HHS_FIREBASE_CONFIG_FILE="${HHS_DIR}/firebase.properties"
  export HHS_FIREBASE_CREDS_FILE="${HHS_DIR}/{project_id}-firebase-credentials.json"
  export HHS_PATHS_FILE="${HHS_DIR}/.path"
  export HHS_PUNCH_FILE="${HHS_DIR}/.punches"
  export HHS_SAVED_DIRS_FILE="${HHS_DIR}/.saved_dirs"
  export HHS_DIRS_FILE="${HHS_DIR}/.dirs"
  export HHS_SETMAN_CONFIG_FILE="${HHS_DIR}/setman.properties"
  export HHS_SETMAN_DB_FILE="${HHS_DIR}/setman.db"
  export HHS_VAULT_FILE="${HHS_DIR}/.vault"
  export HHS_VAULT_USER="${USER}"

  # ----------------------------------------------------------------------------
  # Directories

  [[ -z "${GIT_REPOS}" && -d "${HOME}"/GIT-Repository ]] && export GIT_REPOS="${HOME}"/GIT-Repository
  [[ -d "${HOME}"/Desktop ]] && export DESKTOP="${HOME}/Desktop"
  [[ -d "${HOME}"/Documents ]] && export DOCUMENTS="${HOME}/Documents"
  [[ -d "${HOME}"/Downloads ]] && export DOWNLOADS="${HOME}/Downloads"
  [[ -d "${HOME}"/Dropbox ]] && export DROPBOX="${HOME}/Dropbox"
  [[ -d "${HOME}"/Workspace ]] && export WORKSPACE="${HOME}/Workspace"
  [[ -d "${HOME}"/Music ]] && export MUSIC="${HOME}/Music"
  [[ -d "${HOME}"/Pictures ]] && export PICTURES="${HOME}/Pictures"

  # ----------------------------------------------------------------------------
  # Integrations

  # Ollama-AI
  if __hhs_has 'ollama'; then
    export HHS_OLLAMA_HISTORY_FILE="${HHS_OLLAMA_HISTORY_FILE:-${HHS_DIR}/.ollama_history}"
  fi

  # Hunspell
  if __hhs_has 'hunspell'; then
    export DICPATH="${HHS_DIR}/hunspell-dicts"
    export DICTIONARY="en_US,es_ES,pt_BR,fr_FR"
  fi

  # Glow
  if __hhs_has 'glow'; then
    [[ -s "${HHS_DIR}/.glow.yml" ]] || \cp "${HHS_HOME}/dotfiles/glow.yml" "${HHS_DIR}/.glow.yml"
  fi

  # Starship variables
  export STARSHIP_CONFIG="${STARSHIP_CONFIG=${HHS_DIR}/.starship.toml}"
  export STARSHIP_CACHE="${STARSHIP_CACHE=${HHS_CACHE_DIR}}"
  export HHS_STARSHIP_PRESETS_DIR="${HHS_HOME}/bin/apps/bash/hhs-app/plugins/starship/hhs-presets"

  # FZF variables
  if __hhs_has 'fzf'; then
    if __hhs_has 'bat'; then
      export FZF_DEFAULT_OPTS="--preview 'bat --color=always {}'"
    else
      export FZF_DEFAULT_OPTS="--preview 'cat --color=always {}'"
    fi
    if __hhs_has 'fd'; then
      export FZF_DEFAULT_COMMAND="fd --hidden --strip-cwd-prefix --exclude .git"
      export FZF_CTRL_COMMAND="${FZF_DEFAULT_COMMAND}"
      export FZF_ALT_C_COMMAND="fd --type=d --hidden --strip-cwd-prefix --exclude .git"
      _fzf_compgen_path() {
        fd --hidden --exclude .git . "$1"
      }
      _fzf_compgen_dir() {
        fd --type=d --hidden --exclude .git . "$1"
      }
    else
      export FZF_DEFAULT_COMMAND="find "
    fi
  fi

  # ----------------------------------------------------------------------------
  # Development tools. To override it please export HHS_DEV_TOOLS variable at ${HHS_ENV_FILE}
  DEVELOPER_TOOLS=(
    'git' 'hexdump' 'nvim' 'tree' 'pcregrep' 'gpg' 'base64' 'rsync'
    'java' 'ruby' 'gem' 'python3' 'pip3' 'node' 'npm'
    'gcc' 'make' 'gradle'
    'jq' 'sqlite3' 'gawk' 'hunspell'
    'bat' 'fd' 'nvim' 'delta' 'tldr' 'zoxide' 'glow' 'btop'
    'colorls' 'fzf' 'starship' 'gtrash' 'atuin' 'ollama'

  )

  [[ "Darwin" == "${HHS_MY_OS}" ]] && DEVELOPER_TOOLS+=('brew' 'xcode-select')

  export HHS_DEV_TOOLS="${HHS_DEV_TOOLS:-"${DEVELOPER_TOOLS[@]}"}"

fi
