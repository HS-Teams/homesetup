#!/usr/bin/env bash

#  Script: hhs-profile-tools.bash
# Created: Oct 5, 2019
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs/homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2025, HomeSetup team

# !NOTICE: Do not change this file. To customize your functions edit the file ~/.functions

if [[ -d "${HOME}/.nvm" ]]; then

  # @function: Lazy load helper function to initialize NVM for the terminal.
  function __hhs_activate_nvm() {

    echo -en "Activating NVM app..."
    # NVM setup
    export NVM_DIR="${HOME}/.nvm"
    if [[ -s "$NVM_DIR/nvm.sh" ]] && __hhs_source "$NVM_DIR/nvm.sh"; then
      export PATH="$PATH:$NVM_DIR"
      if [[ -s "$NVM_DIR/bash_completion" ]]; then
        \ln -sf "$NVM_DIR/bash_completion" "${AUTO_CPL_D}/nvm-completion.bash"
      fi
      echo "${GREEN} OK${NC}" && return 0
    else
      __hhs_errcho "${FUNCNAME[0]}" "FAILED => NVM could not be started !"
    fi

    return 1
  }
fi

if [[ -d "${HOME}/.rvm" ]]; then

  # @function: Lazy load helper function to initialize RVM for the terminal.
  function __hhs_activate_rvm() {

    echo -en "Activating RVM app..."
    # RVM setup
    if [[ ! -d "${HOME}/.rvm" ]]; then
      __hhs_errcho "${FUNCNAME[0]}" "FAILED => Can't find RVM_HOME => \"${HOME}/.rvm\" !"
      return 1
    fi
    export RVM_DIR="${HOME}/.rvm"
    if [[ -s "$RVM_DIR/scripts/rvm" ]] && __hhs_source "$RVM_DIR/scripts/rvm"; then
      export PATH="$PATH:$RVM_DIR/bin"
      echo "${GREEN} OK${NC}" && return 0
    else
      __hhs_errcho "${FUNCNAME[0]}" "FAILED => RVM could not be started !"
    fi

    return 1
  }
fi

if __hhs_has jenv; then

  # @function: Lazy load helper function to initialize Jenv for the terminal.
  function __hhs_activate_jenv() {

    echo -en "Activating JENV app..."
    # JENV setup
    if eval "$(jenv init -)" &>/dev/null; then
      echo "${GREEN} OK${NC}" && return 0
    else
      __hhs_errcho "${FUNCNAME[0]}" "FAILED => JENV could not be started !" && return 1
    fi
  }
fi

if __hhs_has docker && __hhs_has colima && [[ -z "${HHS_HAS_DOCKER}" ]]; then

  # @function: Lazy load helper function to initialize Docker-Daemon for the terminal.
  function __hhs_activate_docker() {

    DK_LOC='/Applications/Docker.app'
    # Docker desktop daemon setup
    if [[ -f ${DK_LOC} ]]; then
      echo -en "Activating Docker desktop..."
      if open "${DK_LOC}" &>/dev/null; then
        echo "${GREEN} OK${NC}" && return 0
      fi
    # Docker and Colima setup
    elif __hhs_has 'colima' && __hhs_has 'docker'; then
      echo -en "Activating Colima + Docker..."
      if colima start &>/dev/null; then
        echo "${GREEN} OK${NC}" && return 0
      fi
    else
      __hhs_errcho "${FUNCNAME[0]}" "FAILED => Docker/Colima could not be started !"
    fi

    return 1
  }
fi
