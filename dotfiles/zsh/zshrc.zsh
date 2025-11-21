#!/usr/bin/env zsh
# shellcheck disable=SC1090

#  Script: zshrc.zsh
# Purpose: This is user specific file that gets loaded each time user creates a new non-login
#          shell. It simply loads the required HomeSetup dotfiles and set some required paths.
# Created: Nov 21, 2025
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs/homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2025, HomeSetup team

# If not running interactively or as a CI build, skip it.
[[ -z "${JOB_NAME}" && -z "${GITHUB_ACTIONS}" && -z "${PS1}" && -z "${PS2}" ]] && return

echo -e "\033[1;34m[${SHELL##*\/}] HomeSetup is starting...\033[m"

export HHS_ACTIVE_DOTFILES="${HHS_ACTIVE_DOTFILES} zshrc"

# Unset other used variables
unset -m 'HHS_*' '__hhs*'

# Unset all aliases before setting them again.
unalias -a

# Do not change this formatting, it is required to proper reset IFS to it's defaults
# The Internal Field Separator (IFS). The default value is <space><tab><newline>
export OLDIFS="${IFS}"

export PYTHON3="${PYTHON3:-python3}"

# The following variables are not inside the bash_env because we need them in the early load process.
export HHS_MY_OS="${HHS_MY_OS:-$(uname -s)}"
export HHS_MY_SHELL="${SHELL##*/}"

# Detect if HomeSetup was installed using an installation prefix.
export HHS_PREFIX_FILE="${HOME}/.hhs-prefix"

if [[ -s "${HHS_PREFIX_FILE}" ]]; then
  prefix="$(grep -m 1 . "${HHS_PREFIX_FILE}")"
  [[ -n "${prefix}" && -d "${prefix}" ]] && export HHS_PREFIX="${prefix}"
else
  unset HHS_PREFIX
fi

# Defined by the installation.
export HHS_HOME="${HHS_PREFIX:-${HOME}/HomeSetup}"
export HHS_DIR="${HOME}"/.config/hhs
export HHS_VERSION="$(< "${HHS_HOME}"/.VERSION)"
export HHS_SHOPTS_FILE="${HHS_DIR}"/shell-opts.toml
export HHS_BACKUP_DIR="${HHS_DIR}"/backup
export HHS_CACHE_DIR="${HHS_DIR}"/cache
export HHS_LOG_DIR="${HHS_DIR}"/log
export HHS_LOG_FILE="${HHS_LOG_DIR}"/hhsrc.log
export HHS_MOTD_DIR="${HHS_DIR}"/motd
export HHS_PROMPTS_DIR="${HHS_DIR}"/askai/prompts
export HHS_SETUP_FILE="${HHS_DIR}"/.homesetup.toml
export HHS_VENV_PATH="${HHS_DIR}"/venv
export HHS_ALIASDEF="${HHS_DIR}"/.aliasdef

# if the log directory is not found, we have to create it.
[[ -d "${HHS_LOG_DIR}" ]] || mkdir -p "${HHS_LOG_DIR}"

# if the cache directory is not found, we have to create it.
[[ -d "${HHS_CACHE_DIR}" ]] || mkdir -p "${HHS_CACHE_DIR}"

# if the motd directory is not found, we have to create it.
[[ -d "${HHS_MOTD_DIR}" ]] || mkdir -p "${HHS_MOTD_DIR}"

# if the prompts directory is not found, we have to create it.
[[ -d "${HHS_PROMPTS_DIR}" ]] || mkdir -p "${HHS_PROMPTS_DIR}"

# Set path so it includes user's private bin if it exists.
[[ -d "${HOME}/bin" ]] && export PATH="${PATH}:${HOME}/bin"

# Set path so it includes user's private bin if it exists.
[[ -d "${HOME}/.local/bin" ]] && export PATH="${PATH}:${HOME}/.local/bin"

# Set path so it includes `$HHS_DIR/bin` if it exists.
[[ -d "${HHS_DIR}/bin" ]] && export PATH="${PATH}:${HHS_DIR}/bin"

# Set path so it includes `bats-core` if it exists.
[[ -d "${HHS_HOME}/tests/bats/bats-core/bin" ]] && export PATH="${PATH}:${HHS_HOME}/tests/bats/bats-core/bin"

# Load all dotfiles following the order.
# Notice that the order here is important, do not reorder it.
DOTFILES=(
  'bash_aliases'
  'bash_colors'
  'bash_env'
  'zsh_functions'
  'bash_icons'
  'zsh_prompt'
)

# Custom dotfiles comes after the default one, so they can be overriden.
# Notice that the order here is important, do not reorder it.
CUSTOM_DOTFILES=(
   'env'
   'colors'
   'prompt'
   'aliases'
   'aliasdef'
   'functions'
)

# Re-create the HomeSetup log file.
started="$(${PYTHON3:-python3} -c 'import time; print(int(time.time() * 1000))')"
echo -e "HomeSetup is starting: $(date)\n" >"${HHS_LOG_FILE}"

# Source the bash common functions. Logs are available below here.
source "${HHS_HOME}/dotfiles/bash/bash_commons.bash"

# Initialization setup (homesetup.toml).
if [[ ! -s "${HHS_SETUP_FILE}" ]]; then
  __hhs_log "WARN" "HomeSetup initialization file '${HHS_SETUP_FILE}' was not found. Using defaults."
  \cp "${HHS_HOME}/dotfiles/homesetup.toml" "${HHS_SETUP_FILE}"
fi
re='^([a-zA-Z0-9_.]+) *= *(.*)'
while read -r pref; do
  if [[ ${pref} =~ ${re} ]]; then
    key="${match[1]}"
    val="${match[2]}"
    case "${(U)val}" in
      TRUE)  val=1 ;;
      FALSE) val="" ;;
    esac
    val="${val//[\"\']/}"
    typeset -g "${(U)key}"="${val}"
  fi
done <"${HHS_SETUP_FILE}"

# -----------------------------------------------------------------------------------
# Settings (homesetup.toml) are available as environment variables from this point

# Add custom paths to the system `$PATH`.
if [[ -f "${HHS_DIR}/.path" ]]; then
  __hhs_log "DEBUG" "Adding custom system PATH's"
  all="$(grep . "${HHS_DIR}/.path" | grep -v -e '^$')"
  for f_path in ${all}; do
    [[ -n "${f_path}" ]] && PATH="${f_path}:${PATH}"
  done
fi

# ZSH missing paths
brew_path="/opt/homebrew/bin"
ruby_path="$(ruby -e 'puts Gem.bindir')"
PATH="${brew_path:h}:${ruby_path}:${PATH}"
# Remove PATH duplicates.
PATH=$(awk -F: '{for (i=1;i<=NF;i++) { if ( !x[$i]++ ) printf("%s:",$i); }}' <<<"${PATH}")
export PATH

# Auto-suggestions and syntax-highlighting
source "$(brew --prefix)/share/zsh-autosuggestions/zsh-autosuggestions.zsh"
source "$(brew --prefix)/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh"

# Shell options
setopt share_history
setopt hist_expire_dups_first
setopt hist_ignore_dups
setopt hist_verify
setopt auto_cd

# Alias definitions
if ! [[ -s "${HHS_ALIASDEF}" ]]; then
  __hhs_log "WARN" "'.aliasdef' file was copied because it was not found at: ${HHS_DIR}"
  \cp "${HHS_HOME}/dotfiles/aliasdef" "${HHS_ALIASDEF}"
fi

# -----------------------------------------------------------------------------------
# Initialize HomeSetup key bindings.
bindkey '^[[A' history-search-backward
bindkey '^[[B' history-search-forward

# -----------------------------------------------------------------------------------
# Activate HomeSetup Python venv.
if [[ ${HHS_PYTHON_VENV_ENABLED} -eq 1 ]]; then
  __hhs_log "DEBUG" "Activating python virtual environment"
  if source "${HHS_VENV_PATH}"/bin/activate; then
    __hhs_log "INFO" "HomeSetup Python venv has been activated: ${HHS_VENV_PATH}"
    export HHS_PYTHON_VENV_ACTIVE=1
  else
    __hhs_log "ERROR" "Unable to activate HomeSetup Python venv!"
  fi
else
  __hhs_log "WARN" "HomeSetup Python venv auto-activation was disabled !"
fi

# -----------------------------------------------------------------------------------
# Set/Unset the shell options
if [[ ${HHS_LOAD_SHELL_OPTIONS} -eq 1 ]]; then
  if [[ ! -s "${HHS_SHOPTS_FILE}" ]]; then
    \shopt | awk '{print $1" = "$2}' >"${HHS_SHOPTS_FILE}" ||
       __hhs_log "ERROR" "Unable to create the Shell Options file !"
  fi
  re_key_pair="^([a-zA-Z0-9]*) *= *([Oo][Nn]|[Oo][Ff][Ff])$"
  while read -r line; do
    if [[ ${line} =~ ${re_key_pair} ]]; then
      option="${BASH_REMATCH[1]}"
      state="${BASH_REMATCH[2]}"
      if [[ "${state}" == 'on' ]]; then
        \shopt -s "${option}" &>/dev/null || __hhs_log "WARN" "Unable to SET shell option: ${option}"
      elif [[ "${state}" == 'off' ]]; then
        \shopt -u "${option}" &>/dev/null || __hhs_log "WARN" "Unable to UNSET shell option: ${option}"
      fi
    fi
  done <"${HHS_SHOPTS_FILE}"
  __hhs_log "INFO" "Shell options are set !"
fi

# -----------------------------------------------------------------------------------
# Load dotfiles

# Load all HomeSetup dotfiles.
__hhs_log "INFO" "Loading HomeSetup dotfiles"
for file in "${DOTFILES[@]}"; do
  f_path="${HOME}/.${file}"
  if [[ -s "${f_path}" ]]; then
    __hhs_log "DEBUG" "Loading dotfile: ${f_path}"
    source "${f_path}"
  else
    __hhs_log "WARN" "Skipped dotfile :: Not found -> ${f_path}"
  fi
done

# Zoxide integration
if command -v &>/dev/null 'zoxide'; then
  eval "$(zoxide init zsh)"
else
  echo "WARN" "Zoxide was not enabled !"
fi

# Load all Custom dotfiles:
#   source -> ~/.hhs/.env can be used to extend/override .bash_env
#   source -> ~/.hhs/.colors can be used to extend/override .bash_colors
#   source -> ~/.hhs/.prompt can be used to extend/override .bash_prompt
#   source -> ~/.hhs/.aliases can be used to extend/override .bash_aliases
#   source -> ~/.hhs/.aliasdef can be used to customize your alias definitions
#   source -> ~/.hhs/.functions can be used to extend/override .bash_functions
for file in "${CUSTOM_DOTFILES[@]}"; do
  f_path="${HHS_DIR}/.${file}"
  if [[ -s "${f_path}" ]]; then
    __hhs_log "INFO" "Loading custom dotfile: ${f_path}"
    __hhs_source "${f_path}"
  else
    __hhs_log "WARN" "Skipped custom dotfile :: Not found -> ${f_path}"
  fi
done

# Restore the last used directory
if [[ ${HHS_RESTORE_LAST_DIR} -eq 1 && -s "${HHS_DIR}/.last_dirs" ]]; then
  last_dir="$(grep -m 1 . "${HHS_DIR}/.last_dirs")"
  \cd "${last_dir}" 2> /dev/null || {
    __hhs_log "WARN" "Unable to enter last directory: '${last_dir}' because it was not found !"
    \cd "${HOME}" || true
  }
fi


# -----------------------------------------------------------------------------------
# Workaround to fix missing __hhs_functions

# Print HomeSetup MOTDs.
echo -e "\033[H\033[J"
echo -en "${ORANGE}[${HHS_MY_OS}-${HHS_MY_OS_RELEASE}/${HHS_MY_SHELL}] ${WHITE}${HAND_PEACE_ICN}  "
echo -e "${GREEN}Welcome ${USER:-user} to HomeSetup ${BLUE}v${HHS_VERSION}${NC}\n"

alias cd='\cd'
alias ..='cd ..'
alias ...='cd ../../'
alias ....='cd ../../../'
alias .....='cd ../../../../'
alias \?='\pwd'
alias dirs='\dirs'
alias du='\du'
alias open='\open'
alias shopt='\shopt'
alias hhs='__hhs'
alias gta='git add'

# -----------------------------------------------------------------------------------
# Finalization

finished="$(${PYTHON3:-python3} -c 'import time; print(int(time.time() * 1000))')"
diff_time=$((finished - started))
diff_time_sec=$((diff_time/1000))
diff_time_ms=$((diff_time-(diff_time_sec*1000)))

__hhs_log "INFO" "HomeSetup initialization completed in ${diff_time_sec}s ${diff_time_ms}ms" >>"${HHS_LOG_FILE}"
echo '' >>"${HHS_LOG_FILE}"

unset started finished diff_time diff_time_sec diff_time_ms state option line file all
unset f_path tmp_file re_key_pair prefs cpl bnd pref re motd all app_name last_dir re
