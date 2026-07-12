#!/usr/bin/env bash
# shellcheck disable=SC1117

#  Script: bash_prompt.bash
# Purpose: Shell prompt configuration file
# Created: Aug 26, 2018
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs/homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2025, HomeSetup team

# NOTICE:
# - Do not change this file. To customize your prompt edit the file ~/.prompt
# - inspiRED by: https://github.com/mathiasbynens/dotfiles
# - Heavily inspiRED by @necolas’s prompt: https://github.com/necolas/dotfiles
# - Improved with: http://ezprompt.net
# - If you are using Starship, you have to edit the ${STARSHIP_CONFIG} file

# Do not source this file multiple times
if list_contains "${HHS_ACTIVE_DOTFILES}" "bash_prompt"; then
  __hhs_log "DEBUG" "$0 was already loaded!"
else

  export HHS_ACTIVE_DOTFILES="${HHS_ACTIVE_DOTFILES} bash_prompt"

  # @function: Retrieve the current git branch if inside a git repository.
  function __hhs_git_prompt() {

    local st_flag='' branch_name=''

    if git rev-parse --is-inside-work-tree &>/dev/null; then

      # check if the current directory is in .git before running git checks.
      if [[ "$(git rev-parse --is-inside-git-dir 2>/dev/null)" == 'false' ]]; then

        # Ensure the index is up to date.
        git update-index --really-refresh -q &>/dev/null

        # Check for uncommitted changes in the index.
        if ! git diff --quiet --ignore-submodules --cached; then
          st_flag+='+'
        fi

        # Check for un-staged changes.
        if ! git diff-files --quiet --ignore-submodules --; then
          st_flag+='!'
        fi

        # Check for untracked files.
        if [[ -n "$(git ls-files --others --exclude-standard)" ]]; then
          st_flag+='?'
        fi

        # Check for stashed files.
        if git rev-parse --verify refs/stash &>/dev/null; then
          st_flag+='$'
        fi

        # Get the short symbolic ref. If HEAD isn’t a symbolic ref, get the short SHA for the latest commit
        # Otherwise, just give up.
        branch_name="$(git symbolic-ref --quiet --short HEAD 2>/dev/null || git rev-parse --short HEAD 2>/dev/null || echo '(unknown)')"

        [[ -n "${st_flag}" ]] && st_flag=" [${st_flag}]"

        echo -e "${1}${branch_name}${2}${st_flag}"
      else
        return
      fi

    fi
  }

  if [[ ${COLORTERM} == gnome-* && ${TERM} == xterm ]] && infocmp gnome-256color >/dev/null 2>&1; then
    export TERM='gnome-256color'
  elif infocmp xterm-256color >/dev/null 2>&1; then
    export TERM='xterm-256color'
  fi

  # Prompt colors
  PROMPT_COLOR="\[${HHS_PROMPT_COLOR:-$WHITE}\]"
  ALERT_COLOR="\[${RED}\]"
  NET_COLOR="\[${YELLOW}\]"
  OK_COLOR="\[${GREEN}\]"
  DIR_COLOR="\[${ORANGE}\]"
  GIT_COLOR="\[${CYAN}\]"
  HOST_COLOR="\[${PURPLE}\]"

  # Prompt icons
  MACOS_ICN="\357\205\271"
  LINUX_ICN="\357\214\232"
  UBUNTU_ICN="\357\214\233"
  CENTOS_ICN="\357\214\204"
  FEDORA_ICN="\357\214\213"

  USER_ICN="\357\220\225"
  ROOT_ICN="\357\222\234"
  AT_ICN="\357\207\272"
  NET_ICN="\357\203\250"
  FOLDER_ICN="\357\201\273"
  GIT_ICN="\357\204\246"
  PROMPT_ICN="\357\232\262"

  # Icons to be displayed. Check https://fontawesome.com/cheatsheet?from=io for details.
  # Use __hhs_utoh <4digit-hex> to find out the octal value of the icon.

  MY_OS="$(uname -s)"

  case "${MY_OS}" in
  Darwin)
    MY_OS_ICN="${MACOS_ICN}"
    ;;
  Linux)
    # Most of linux distros have this file to detect the releases.
    OS_RELEASE="$(grep '^ID=' '/etc/os-release' 2>/dev/null)"
    OS_RELEASE="${OS_RELEASE#*=}"   # Extracting ID=
    OS_RELEASE="${OS_RELEASE//\"/}" # Removing leading quotes
    case "${OS_RELEASE}" in
    ubuntu)
      MY_OS_ICN="${UBUNTU_ICN}"
      ;;
    centos)
      MY_OS_ICN="${CENTOS_ICN}"
      ;;
    fedora)
      MY_OS_ICN="${FEDORA_ICN}"
      ;;
    *)
      MY_OS_ICN="${LINUX_ICN}"
      ;;
    esac
    ;;
  *)
    MY_OS_ICN="${LINUX_ICN}"
    ;;
  esac

  # Set the terminal title and prompt.
  # Check ${HHS_HOME}/docs/devel/bash-prompt-codes.md for more details.

  # Initialize Starship prompt if it is set to.
  if __hhs_has "starship" && [[ ${HHS_USE_STARSHIP} -eq 1 ]]; then

    # @function: Set the terminal window title.
    function __hhs_set_win_title() {
      echo -ne "\033]0; ${TITLE} \007"
    }

    __hhs_log "INFO" "Starting starship prompt"

    if [[ ! -s "${STARSHIP_CONFIG}" ]]; then
      __hhs_log "DEBUG" "Copying default HomeSetup starship.toml config to -> ${STARSHIP_CONFIG}"
      if ! \cp "${HHS_STARSHIP_PRESETS_DIR}/hhs-starship.toml" \
        "${STARSHIP_CONFIG}" &>/dev/null; then
        __hhs_log "ERROR" "Unable to copy default starship config file into place!"
      fi
    fi

    # shellcheck disable=SC2034
    starship_precmd_user_func="__hhs_set_win_title"
    if eval "$(\starship init "${HHS_MY_SHELL}")"; then
      __hhs_log "INFO" "Starship successfully started!"
    else
      __hhs_log "ERROR" "Starship failed to start!"
    fi
  else
    __hhs_log "WARN" "Starship prompt initialization was disabled !"
  fi

  # If Starship did not start, configure classic HomeSetup prompt.
  if [[ -z "${STARSHIP_SESSION_KEY}" ]]; then

    # Terminal title.
    TITLE="HomeSetup-v${HHS_VERSION}"
    ESCAPED_TITLE="\[\e]2;${TITLE}\a\]"

    # The history number of this command.
    HIST_STYLE="${PROMPT_COLOR}${MY_OS_ICN} (\!)"

    # Logged username. Highlight when logged in as root.
    if [[ "${USER}" == "root" ]]; then
      USER_STYLE="${PROMPT_COLOR} ${ROOT_ICN}${ALERT_COLOR} \u"
    else
      USER_STYLE="${PROMPT_COLOR} ${USER_ICN}${OK_COLOR} \u"
    fi

    # The hostname. Highlight when connected via SSH.
    if [[ -n "${SSH_TTY}" ]]; then
      HOST_STYLE="${PROMPT_COLOR} ${NET_ICN}${NET_COLOR} \H"
    else
      HOST_STYLE="${PROMPT_COLOR} ${AT_ICN}${HOST_COLOR} \h"
    fi

    # Working directory base path.
    PATH_STYLE="${PROMPT_COLOR} ${FOLDER_ICN} ${DIR_COLOR} \W"

    # Git repository details.
    # Check if the current directory is a Git repository.
    GIT_STYLE="${PROMPT_COLOR}\$(__hhs_git_prompt \" ${GIT_ICN} ${GIT_COLOR}\")"

    # User prompt format.
    PROMPT="${PROMPT_COLOR}${ESCAPED_TITLE} ${PROMPT_ICN} "

      # PS1 Style: Color and icons (default).
    PS1_STYLE=$"${HIST_STYLE}${USER_STYLE}${HOST_STYLE}${PATH_STYLE}${GIT_STYLE}${PROMPT}"

    # PS2 Style: Continuation prompt.
    PS2_STYLE=$'... '

    export PS1=${HHS_CUSTOM_PS1:-$PS1_STYLE}
    export PS2=${HHS_CUSTOM_PS2:-$PS2_STYLE}
  fi

  # ColorLS integration. Cache the Ruby library path because resolving it starts Ruby.
  colorls_root=''
  colorls_cache_file="${HHS_CACHE_DIR}/colorls-root-v1.path"
  if __hhs_has colorls; then
    if [[ -s "${colorls_cache_file}" ]]; then
      IFS= read -r colorls_root <"${colorls_cache_file}"
      [[ -s "${colorls_root}/tab_complete.sh" ]] || colorls_root=''
    fi
    if [[ -z "${colorls_root}" ]] && __hhs_has gem; then
      colorls_library="$(gem which colorls 2>/dev/null)"
      if [[ -s "${colorls_library}" ]]; then
        colorls_root="${colorls_library%/*}"
        printf '%s\n' "${colorls_root}" >"${colorls_cache_file}"
      fi
    fi
  fi

  if [[ -n "${colorls_root}" ]]; then
    colorls_dir="${colorls_root}/yaml"
    hhs_colorls_dir="${HHS_HOME}/assets/colorls/hhs-preset"
    [[ -d "${colorls_dir}" ]] || \mkdir -p "${colorls_dir}"
    [[ -f "${colorls_dir}/dark_colors.yaml" ]] || \cp "${hhs_colorls_dir}/dark_colors.yaml" "${colorls_dir}"
    [[ -f "${colorls_dir}/light_colors.yaml" ]] || \cp "${hhs_colorls_dir}/light_colors.yaml" "${colorls_dir}"
    [[ -f "${colorls_dir}/file_aliases.yaml" ]] || \cp "${hhs_colorls_dir}/file_aliases.yaml" "${colorls_dir}"
    [[ -f "${colorls_dir}/files.yaml" ]] || \cp "${hhs_colorls_dir}/files.yaml" "${colorls_dir}"
    [[ -f "${colorls_dir}/folder_aliases.yaml" ]] || \cp "${hhs_colorls_dir}/folder_aliases.yaml" "${colorls_dir}"
    [[ -f "${colorls_dir}/folders.yaml" ]] || \cp "${hhs_colorls_dir}/folders.yaml" "${colorls_dir}"
    __hhs_source "${colorls_root}/tab_complete.sh"
  fi
  unset colorls_cache_file colorls_dir colorls_library colorls_root hhs_colorls_dir

fi
