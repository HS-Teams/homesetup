#!/usr/bin/env bash
# shellcheck disable=SC1117,SC1090

#  Script: install.bash
# Purpose: Install and configure HomeSetup
# Created: Aug 26, 2018
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs/homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2025, HomeSetup team

{

  # This script name
  APP_NAME="${0##*/}"

  # HomeSetup Installation version
  VERSION="1.8.25"

  # Help message to be displayed by the script
  USAGE="
usage: $APP_NAME [OPTIONS] <args>

  -l | --local          : Local installation (default). Replaces existing dotfiles.
  -r | --repair         : Repair the current installation.
  -i | --interactive    : Interactive installation of all scripts in the user HomeSetup directory.
  -p | --prefix         : HomeSetup installation prefix. Defaults to user's HOME directory '~/HomeSetup'.
  -b | --homebrew       : Homebrew-based installation. Skips dependency checks.
  -q | --quiet          : Non-interactive mode using all defaults.
"

  # Installation log file
  INSTALL_LOG="${HOME}/install-hhs.log"

  # Define USER and HOME variables
  if [[ -n "${SUDO_USER}" ]]; then
    USER="${SUDO_USER}"
    HOME="$(eval echo ~"${SUDO_USER}")"
    has sudo && SUDO=sudo
  else
    USER="${USER:-$(whoami)}"
    HOME="${HOME:-$(eval echo ~"${USER}")}"
    [[ -n "${GITHUB_ACTIONS}" ]] && SUDO=sudo
  fi

  [[ -z "${USER}" || -z "${HOME}" ]] && quit 1 "Unable to determine USER/HOME -> ${USER}/${HOME}"

  # Functions to be unset after quit
  UNSETS=(
    quit usage has check_current_shell check_inst_method install_dotfiles clone_repository check_required_tools
    activate_dotfiles compatibility_check install_packages configure_python install_hspylib ensure_brew
    copy_file create_directory install_homesetup abort_install check_prefix configure_starship install_brew
    install_tools query_askai_install create_destination_dirs configure_askai_rag configure_blesh create_venv
  )

  # Awesome icons
  STAR_ICN='\xef\x80\x85'       # 
  HAND_PEACE_ICN='\xef\x89\x9b' # 
  POINTER_ICN='\xef\x90\xb2'    # 
  SUCCESS_ICN='\xef\x98\xab'    # 
  FAIL_ICN='\xef\x91\xa7'       # 
  AI_ICN='\xef\x89\xa0'         # 

  # VT-100 Terminal colors
  ORANGE='\033[38;5;202m'
  WHITE='\033[97m'
  BLUE='\033[34m'
  CYAN='\033[36m'
  GREEN='\033[32m'
  YELLOW='\033[33m'
  RED='\033[31m'
  MAGENTA='\033[35m'
  NC='\033[m'

  touch "${INSTALL_LOG}"
  [[ -f "${INSTALL_LOG}" ]] || quit 1 "Unable initialize installation logs -> ${INSTALL_LOG}"
  [[ -f "${INSTALL_LOG}" ]] && echo -e "${ORANGE}Installation logs can be accessed here: ${BLUE}${INSTALL_LOG}${NC}"

  # HomeSetup GitHub repository URL
  GITHUB_URL='https://github.com/yorevs/homesetup.git'

  # HomeSetup GitHub issues URL
  ISSUES_URL="https://github.com/yorevs/homesetup/issues"

  # Define the user HomeSetup installation prefix
  PREFIX=

  # HomeSetup installation prefix file
  PREFIX_FILE="${HOME}/.hhs-prefix"

  # Option to allow install to be interactive or not
  OPT='all'

  # HomeSetup installation method
  METHOD=

  # Whether to install it without prompts
  QUIET=

  # Whether the script is running from a stream
  STREAMED="$([[ -t 0 ]] || echo 'Yes')"

  # Whether being installed by HomeBrew
  HOMEBREW_INSTALLING=

  # Whether to install the AskAI functionalities or not
  INSTALL_AI="${GITHUB_ACTIONS:-}"

  # Streamed installation is disabled by default
  [[ -n "${STREAMED}" && -z "${GITHUB_ACTIONS}" ]] && unset INSTALL_AI

  # Shell type
  SHELL_TYPE="${SHELL##*/}"

  # All .dotfiles we will manage
  ALL_DOTFILES=()

  # Supported shell types. For now, only bash is supported
  SUPP_SHELL_TYPES=('bash')

  # Timestamp used to backup files
  TIMESTAMP=$(date "+%s%S")

  # Python executable
  PYTHON3="${PYTHON3:-$(command -v python3.11)}"

  # Pip executable
  PIP3="${PIP3:-${PYTHON3} -m pip}"

  # Virtual environment Python
  VENV_PYTHON3=

  # Virtual environment Pip
  VENV_PIP3=

  # HSPyLib python modules to install
  PYTHON_MODULES=(
    'hspylib'
    'hspylib-datasource'
    'hspylib-clitt'
    'hspylib-setman'
    'hspylib-vault'
    'hspylib-firebase'
  )

  # User's operating system
  MY_OS=$(uname -s)

  # OS Application manager. Defined later on the installation process
  OS_APP_MAN=

  # HomeBrew prefix
  BREW=

  # OS type. Defined later on the installation process
  OS_TYPE=

  # HomeSetup application dependencies
  DEPENDENCIES=(
    'git' 'curl' 'ruby' 'rsync' 'mkdir' 'vim' 'gawk' 'make'
  )

  # Missing HomeSetup dependencies
  MISSING_DEPS=()

  if [[ "${MY_OS}" == "Darwin" ]]; then
    MY_OS_NAME=$(sw_vers -productName)
    GROUP=${GROUP:-staff}
  elif [[ "${MY_OS}" == "Linux" ]]; then
    MY_OS_NAME="$(grep '^ID=' '/etc/os-release' 2>/dev/null)"
    MY_OS_NAME="${MY_OS_NAME#*=}"
    GROUP=${GROUP:-${USER}}
  fi

  # Purpose: Quit the program and exhibits an exit message if specified
  # @param $1 [Req] : The exit return code. 0 = SUCCESS, 1 = FAILURE, * = ERROR ${RED}.
  # @param $2 [Opt] : The exit message to be displayed.
  quit() {

    log_count=15
    unset -f "${UNSETS[*]}"
    exit_code=${1:-0}
    last_log_lines="  Last (${log_count}) log lines:\n$(tail -n ${log_count} "${INSTALL_LOG}" |
      sed '/^[[:space:]]*$/d; s/^/  => /' | nl)"
    shift
    [[ ${exit_code} -ne 0 && ${#} -ge 1 ]] && echo -en "${RED}${APP_NAME}: " 1>&2
    [[ ${#} -ge 1 ]] && echo -e "${*} \n${last_log_lines}${NC}" 1>&2
    [[ ${#} -gt 0 ]] && echo ''
    # Move the installation log to logs folder
    [[ -f "${INSTALL_LOG}" && -d "${HHS_LOG_DIR}" ]] &&
      cp -f "${INSTALL_LOG}" "${HHS_LOG_DIR}/install.log"
    exit "${exit_code}"
  }

  # Usage message
  usage() {
    quit 2 "${USAGE}"
  }

  # @function: Check if a command exists
  # @param $1 [Req] : The command to check
  has() {
    type "${1}" >>"${INSTALL_LOG}" 2>&1
  }

  # @function: Create a directory and check for write permissions
  # @Param $1 [Req] : The directory name
  create_directory() {

    local dir="${1}"

    # If directory is not there yet, create it.
    if [[ ! -d "${dir}" && ! -L "${dir}" ]]; then
      echo -en "\n${WHITE}Creating: ${BLUE}\"${dir}\"${WHITE} directory... "
      if mkdir -p "${dir}"; then
        echo -e "${GREEN}OK${NC}"
      else
        echo -e " ${RED}FAILED${NC}"
        quit 2 "Unable to create directory ${dir}!"
      fi
    else
      echo -en "\n${WHITE}Skipping: ${YELLOW}\"${dir}\"${WHITE} was not created because destination exists. ${NC}"
    fi
    # Trying to write at the created directory to validate write permissions.
    if ! touch "${dir}/tmpfile" >>"${INSTALL_LOG}" 2>&1 ||
      ! rm -f "${dir:?}/tmpfile" >>"${INSTALL_LOG}" 2>&1; then
      quit 2 "Not enough permissions to write to \"${dir}\" directory!"
    fi
  }

  # @function: Copy file from source to destination.
  # @Param $1 [Req] : The source file/dir.
  # @Param $2 [Req] : The destination file/dir.
  copy_file() {

    local src_file="${1}" dest_file="${2}"

    echo ''
    if [[ -f "${dest_file}" || -d "${dest_file}" ]]; then
      echo -e "${WHITE}Skipping: ${YELLOW}${dest_file} file/dir was not copied because destination exists. ${NC}"
    else
      echo -en "${WHITE}Copying: ${BLUE} ${src_file} -> ${dest_file}... "
      \rsync --archive "${src_file}" "${dest_file}" >>"${INSTALL_LOG}" 2>&1
      \chown "${USER}":"${GROUP}" "${dest_file}" >>"${INSTALL_LOG}" 2>&1
      [[ -f "${dest_file}" ]] && echo -e "${GREEN}OK${NC}"
      [[ -f "${dest_file}" ]] || quit 1 " ${RED}FAILED${NC}"
    fi
  }

  # @function: Link file from source to destination.
  # @Param $1 [Req] : The source file/dir.
  # @Param $2 [Req] : The destination file/dir.
  link_file() {

    local src_file="${1}" dest_file="${2}"

    echo ''
    if [[ -s "${dest_file}" && ! -L "${dest_file}" ]]; then
      echo -e "${WHITE}Backing up: ${YELLOW}${dest_file} file/dir was not copied because destination exists. ${NC}"
      mv "${dest_file}" "${HHS_BACKUP_DIR}/$(basename "${dest_file}".orig)"
    fi
    echo -en "${WHITE}Linking: ${BLUE}"
    echo -en "$(\ln -sfv "${src_file}" "${dest_file}")...${NC}"
    [[ -L "${dest_file}" ]] && echo -e " ${GREEN}OK${NC}"
    [[ -L "${dest_file}" ]] || quit 1 " ${RED}FAILED${NC}"
  }

  # shellcheck disable=SC2199,SC2076
  # Check current active User shell type.
  check_current_shell() {

    if [[ ! " ${SUPP_SHELL_TYPES[@]} " =~ " ${SHELL##*/} " ]]; then
      quit 2 "Your current shell is not supported: \"${SHELL}\""
    fi
  }

  # shellcheck disable=SC1091
  # Check which installation method should be used
  check_inst_method() {

    # Loop through the command line options
    while test -n "$1"; do
      case "$1" in
      -l | --local)
        METHOD='local'
        ;;
      -r | --repair)
        METHOD='repair'
        ;;
      -i | --interactive)
        OPT=''
        ;;
      -p | --prefix)
        PREFIX="${2}"
        shift
        ;;
      -b | --homebrew)
        HOMEBREW_INSTALLING=1
        ;;
      -q | --quiet)
        QUIET=1
        ;;
      *)
        quit 2 "Invalid option: \"$1\""
        ;;
      esac
      shift
    done

    # Installation prefix
    [[ -d "${PREFIX}" ]] || unset PREFIX
    PREFIX="${PREFIX:-$([[ -s "${PREFIX_FILE}" ]] && \grep . "${PREFIX_FILE}")}"

    # Installation destination
    INSTALL_DIR="${PREFIX:-${HOME}/HomeSetup}"
    INSTALL_DIR="${INSTALL_DIR/#~/${HOME}}"

    # README link for HomeSetup
    README="${INSTALL_DIR}/README.MD"

    # Configuration files location
    HHS_DIR="${HOME}/.config/hhs"

    # Binaries location
    HHS_BIN_DIR="${HHS_DIR}/bin"

    # MOTD location
    HHS_MOTD_DIR="${HHS_DIR}/motd"

    # Backup location
    HHS_BACKUP_DIR="${HHS_DIR}/backup"

    # Logs directory
    HHS_LOG_DIR="${HHS_DIR}/log"

    # Shell options file
    HHS_SHOPTS_FILE="${HHS_DIR}/shell-opts.toml"

    # Ble Bash plug installation path.
    HHS_BLESH_DIR="${HHS_DIR}/ble-sh"

    # HomeSetup virtual environment path.
    HHS_VENV_PATH="${HHS_DIR}/venv"

    # Hunspell dictionaries location.
    HUNSPELL_DIR="${HHS_DIR}/hunspell-dicts"

    # NeoVim configuration files location.
    NEOVIM_DIR="${HHS_DIR}/nvim"

    # Fonts destination location
    if [[ "Darwin" == "${MY_OS}" ]]; then
      FONTS_DIR="${HOME}/Library/Fonts"
    elif [[ "Linux" == "${MY_OS}" ]]; then
      FONTS_DIR="${HOME}/.local/share/fonts"
    fi

    # Dotfiles source location
    DOTFILES_SRC="${INSTALL_DIR}/dotfiles/${SHELL_TYPE}"

    # Applications source location
    APPS_DIR="${INSTALL_DIR}/bin/apps"

    # Auto-completions source location
    COMPLETIONS_DIR="${INSTALL_DIR}/bin/completions"

    # Key-Bindings source location
    BINDINGS_DIR="${INSTALL_DIR}/bin/key-bindings"

    # Check if the user passed help or version options
    [[ "$1" == '-h' || "$1" == '--help' ]] && quit 0 "${USAGE}"
    [[ "$1" == '-v' || "$1" == '--version' ]] && quit 0 "HomeSetup v${VERSION}"
    [[ -z "${USER}" || -z "${GROUP}" ]] && quit 1 "Unable to detect USER:GROUP => [${USER}:${GROUP}]"
    [[ -z "${HOME}" || -z "${SHELL}" ]] && quit 1 "Unable to detect HOME/SHELL => [${HOME}:${SHELL}]"

    echo -e "\n${GREEN}HomeSetup© v${VERSION} installation ${NC}"

    # Check the installation method
    if [[ -z "${METHOD}" ]]; then
      if [[ -d "${INSTALL_DIR}" || -f "${INSTALL_DIR}/.VERSION" ]]; then
        METHOD='local'
      elif [[ -n "${STREAMED}" ]]; then
        METHOD='remote'
      elif [[ ! -f "${PREFIX_FILE}" && ! -d "${HHS_DIR}" && ! -d "${INSTALL_DIR}" ]]; then
        METHOD='fresh'
      else
        METHOD='repair'
      fi
    fi
  }

  # Prompt the user for AskAI installation
  query_askai_install() {
    if ${PIP3} show hspylib-askai >>"${INSTALL_LOG}" 2>&1; then
      INSTALL_AI='Yes'
    elif [[ -z "${INSTALL_AI}" && -z "${STREAMED}" && -z "${GITHUB_ACTIONS}" && -z "${HOMEBREW_INSTALLING}" ]]; then
      echo -e "${ORANGE}"
      read -rn 1 -p 'Would you like to install HomeSetup AI capabilities (y/[n])? ' ANS
      echo -e "${NC}" && [[ -n "${ANS}" ]] && echo ''
      if [[ "${ANS}" =~ ^[yY]$ ]]; then
        INSTALL_AI='Yes'
      fi
      unset ANS
    fi
  }

  # Create all HomeSetup destination directories
  create_destination_dirs() {
    # Create HomeSetup .hhs directory
    create_directory "${HHS_DIR}"
    # Create HomeSetup bin directory
    create_directory "${HHS_BIN_DIR}"
    # Create HomeSetup motd directory
    create_directory "${HHS_MOTD_DIR}"
    # Create HomeSetup backup directory
    create_directory "${HHS_BACKUP_DIR}"
    # Create HomeSetup logs directory
    create_directory "${HHS_LOG_DIR}"
    # Create fonts destination directory
    create_directory "${FONTS_DIR}"
    # Create hunspell dictionaries destination directory
    create_directory "${HUNSPELL_DIR}"
    # Create neovim configurations files destination directory
    create_directory "${NEOVIM_DIR}"
  }

  # Check HomeSetup required tools
  check_required_tools() {

    [[ -n "${INSTALL_AI}" ]] && PYTHON_MODULES+=('hspylib-askai')

    # macOS
    if [[ "${MY_OS}" == "Darwin" ]]; then
      OS_TYPE='macOS'
      OS_APP_MAN='brew'
      DEPENDENCIES+=('sudo' 'xcode-select')
      [[ -n "${INSTALL_AI}" ]] &&
        DEPENDENCIES+=('ffmpeg' 'portaudio' 'libmagic')
      install="${SUDO} brew install -f"
      check_pkg="brew list "
    # Debian: Ubuntu
    elif has 'apt'; then
      OS_TYPE='Debian'
      OS_APP_MAN='apt'
      DEPENDENCIES+=('sudo' 'file' 'build-essential' 'python3' 'python3-pip')
      [[ -n "${INSTALL_AI}" ]] &&
        DEPENDENCIES+=('ffmpeg' 'python3-pyaudio' 'portaudio19-dev' 'libasound-dev' 'libmagic-dev')
      install="${SUDO} apt install -y"
      check_pkg="apt list --installed | grep"
    # RedHat: Fedora, CentOS
    elif has 'yum'; then
      OS_TYPE='RedHat'
      OS_APP_MAN='yum'
      DEPENDENCIES+=('sudo' 'file' 'make' 'automake' 'gcc' 'gcc-c++' 'kernel-devel' 'python3' 'python3-pip')
      [[ -n "${INSTALL_AI}" ]] &&
        DEPENDENCIES+=('ffmpeg' 'python3-pyaudio' 'portaudio-devel' 'redhat-rpm-config' 'libmagic-dev')
      install="${SUDO} yum install -y"
      check_pkg="yum list installed | grep"
    # Alpine: Busybox
    elif has 'apk'; then
      OS_TYPE='Alpine'
      OS_APP_MAN='apk'
      DEPENDENCIES+=('file' 'python3' 'pip3')
      unset INSTALL_AI # AskAI is not tested on Alpine
      install="apk add --no-cache"
      check_pkg="apk list | grep"
    # ArchLinux
    elif has 'pacman'; then
      OS_TYPE='ArchLinux'
      OS_APP_MAN='pacman'
      DEPENDENCIES+=('sudo' 'file' 'python3' 'python3-pip')
      unset INSTALL_AI # AskAI is not tested on ArchLinux
      install="${SUDO} pacman -Sy"
      check_pkg="pacman -Q | grep"
    else
      quit 1 "Unable to find package manager for $(uname -s)"
    fi

    echo -e "\nUsing ${YELLOW}\"${OS_APP_MAN}\"${NC} application manager!\n"
    pad=$(printf '%0.1s' "."{1..60})
    pad_len=20

    if [[ -n "${HOMEBREW_INSTALLING}" ]]; then
      echo -e "${BLUE}[${OS_TYPE}] ${WHITE}Using ${GREEN}HomeBrew${WHITE} dependency management ...${NC}"
    else
      echo -e "${BLUE}[${OS_TYPE}] ${WHITE}Checking required tools using ${YELLOW}'${check_pkg}'${WHITE} ...${NC}\n"
      for tool_name in "${DEPENDENCIES[@]}"; do
        echo -en "${BLUE}[${OS_TYPE}] ${WHITE}Checking: ${YELLOW}${tool_name} ...${NC}"
        printf '%*.*s' 0 $((pad_len - ${#tool_name})) "${pad}"
        if has "${tool_name}" || ${check_pkg} "${tool_name}" >>"${INSTALL_LOG}" 2>&1; then
          echo -e " ${GREEN}${SUCCESS_ICN} INSTALLED${NC}"
        else
          echo -e " ${RED}${FAIL_ICN} NOT INSTALLED${NC}"
          MISSING_DEPS+=("${tool_name}")
        fi
      done
    fi

    # Install packages using the default package manager
    install_packages "${install}" "${check_pkg}" "${MISSING_DEPS[@]}"
    ensure_brew
  }

  # shellcheck disable=SC2206
  # Install missing required tools.
  install_packages() {

    local install="${1}" check_pkg="${2}" tools pkgs use_sudo=

    shift 2
    tools=(${@})
    pkgs="${tools[*]}"
    pkgs="${pkgs// /\\n  |-}"

    if [[ ${#tools[@]} -gt 0 ]]; then
      # 1st Attempt to install packages without sudo.
      echo -e "${BLUE}[${OS_TYPE}] ${WHITE}Installing required packages using: ${YELLOW}\"${install}\"${NC}"
      echo -e "  |-${pkgs}"
      for tool_name in "${tools[@]}"; do
        echo -en "${BLUE}[${OS_TYPE}] ${WHITE}Installing: ${YELLOW}${tool_name}${NC}..."
        if [[ -z "${use_sudo}" ]] && ${install} "${tool_name}" >>"${INSTALL_LOG}" 2>&1; then
          printf '%*.*s' 0 $((pad_len - ${#tool_name})) "${pad}"
          echo -e " ${GREEN}${SUCCESS_ICN} OK${NC}"
        else
          [[ -z "${use_sudo}" ]] && echo -e " ${RED}${FAIL_ICN} FAILED${NC}"
          # 2nd Attempt to install packages using sudo.
          has 'sudo' || quit 2 "Failed to install dependencies. 'sudo' is not available"
          [[ -z "${use_sudo}" && -n "${SUDO}" ]] && echo -e "\n${ORANGE}Retrying with 'sudo'. You may be prompted for password.${NC}\n"
          install="${SUDO} ${install}"
          use_sudo=1
          echo -en "${BLUE}[${OS_TYPE}] ${WHITE}Installing: ${YELLOW}${tool_name}${NC}..."
          if ${install} "${tool_name}" >>"${INSTALL_LOG}" 2>&1; then
            printf '%*.*s' 0 $((pad_len - ${#tool_name})) "${pad}"
            echo -e " ${GREEN}${SUCCESS_ICN} OK${NC}"
          else
            echo -e " ${RED}${FAIL_ICN} FAILED${NC}"
            MISSING_DEPS+=("${tool_name}")
            quit 2 "Failed to install dependencies. Please manually install the missing tools and try again."
          fi
        fi
      done
    fi
  }

  # Make sure HomeBrew is installed. In the future will use HomeBrew as the default HHS package manager.
  ensure_brew() {

    if [[ ${OS_TYPE} == macOS ]]; then
      echo ''
      if [[ -z "${HOMEBREW_INSTALLING}" ]] && ! has 'brew'; then
        echo -en "${YELLOW}HomeBrew is not installed!${NC}"
        install_brew || quit 2 "### Failed to install HomeBrew !"
      else
        echo -e "${BLUE}[${OS_TYPE}] ${WHITE}HomeBrew is already installed -> ${GREEN}$(brew --prefix) ${NC}"
      fi
    elif [[ ${OS_TYPE} =~ Debian|RedHat ]]; then
      echo -e "${BLUE}[${OS_TYPE}] ${YELLOW}Skipping brew installation (not enforced)."
    else
      echo -e "${BLUE}[${OS_TYPE}] ${YELLOW}Skipping brew installation (not supported OS)."
    fi
  }

  # Install HomeBrew
  install_brew() {

    echo -e "${BLUE}[${OS_TYPE}] Attempting to install HomeBrew [${OS_TYPE}]... "
    if ${SUDO} curl -fsSL https://raw.githubusercontent.com/HomeBrew/install/HEAD/install.sh | bash >>"${INSTALL_LOG}" 2>&1; then
      echo -e "${GREEN}OK${NC}"
      if [[ "${MY_OS}" == "Linux" ]]; then
        [[ -d ~/.linuxbrew ]] && eval "$(~/.linuxbrew/bin/brew shellenv)"
        [[ -d /home/linuxbrew/.linuxbrew ]] && eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
        ${SUDO} eval "$("$(brew --prefix)"/bin/brew shellenv)"
      fi
      BREW="$(brew --prefix)/bin/brew"
      if command -v brew >>"${INSTALL_LOG}" 2>&1; then
        echo -e "\n${GREEN}@@@ Successfully installed HomeBrew -> ${BREW}${NC}"
      else
        quit 2 "### Could not find HomeBrew installation !"
      fi
    else
      echo -e "${RED}FAILED${NC}"
      quit 2 "### Failed to install HomeBrew !"
    fi
  }

  # Install HomeSetup.
  install_homesetup() {

    echo -e "HomeSetup installation started: $(date)\n" >"${INSTALL_LOG}"
    echo ''
    echo -e "${WHITE}Using ${YELLOW}\"${METHOD}\"${NC} installation method!"

    # Select the installation method and call the underlying functions
    case "${METHOD}" in
    remote | repair | fresh)
      query_askai_install
      check_required_tools
      create_destination_dirs
      clone_repository
      install_dotfiles
      compatibility_check
      configure_starship
      configure_gtrash
      configure_blesh
      configure_python
      install_hspylib
      configure_askai_rag
      ;;
    local)
      create_destination_dirs
      install_dotfiles
      compatibility_check
      configure_askai_rag
      ;;
    *)
      quit 2 "Installation method \"${METHOD}\" is not valid!"
      ;;
    esac

    # Finish installation and activate HomeSetup.
    activate_dotfiles
  }

  # Clone the repository and install dotfiles.
  clone_repository() {

    echo -e "${NC}"

    if [[ ! -d "${INSTALL_DIR}" ]]; then
      echo -en "${BLUE}[${OS_TYPE}] ${WHITE}Cloning HomeSetup from ${BLUE}${GITHUB_URL}${WHITE} into ${GREEN}${INSTALL_DIR}... ${NC}"
      if git clone "${GITHUB_URL}" "${INSTALL_DIR}" >>"${INSTALL_LOG}" 2>&1; then
        echo -e "${GREEN}OK${NC}"
      else
        echo -e "${RED}FAILED${NC}"
        quit 2 "Unable to clone HomeSetup repository !"
      fi
    fi

    [[ -s "${INSTALL_DIR}" && -f "${INSTALL_DIR}/.VERSION" ]] || quit 2 "Unable to find HomeSetup source files at: \"${INSTALL_DIR}\"!"
  }

  # Install all dotfiles.
  install_dotfiles() {

    [[ -z ${STREAMED} ]] && is_streamed='No'
    [[ -z ${INSTALL_AI} ]] && is_askai='No'
    [[ -z ${HOMEBREW_INSTALLING} ]] && is_brew='No'
    [[ -z ${GITHUB_ACTIONS} ]] && is_gha='No'

    echo ''
    echo -e "${WHITE}### ${GREEN}HomeSetup© ${WHITE}Installation Settings ###${NC}"
    echo -e ""
    echo -e "${WHITE}          Shell: ${YELLOW}${MY_OS}-${MY_OS_NAME}/${SHELL_TYPE}"
    echo -e "${WHITE}   Install Type: ${YELLOW}${METHOD}"
    echo -e "${WHITE}         Source: ${YELLOW}${INSTALL_DIR}"
    echo -e "${WHITE}         Prefix: ${YELLOW}${PREFIX:-${PREFIX}}"
    echo -e "${WHITE} Configurations: ${YELLOW}${HHS_DIR}"
    echo -e "${WHITE}  PyPi Packages: ${YELLOW}${PYTHON_MODULES[*]}"
    echo -e "${WHITE}     User/Group: ${YELLOW}${USER}:${GROUP}"
    echo -e "${WHITE}      Enable AI: ${YELLOW}${is_askai:=Yes}"
    echo -e "${WHITE}       Streamed: ${YELLOW}${is_streamed:=Yes}"
    echo -e "${WHITE}       HomeBrew: ${YELLOW}${is_brew:=Yes}"
    echo -e "${WHITE} GitHub Actions: ${YELLOW}${is_gha:=Yes}"
    echo -e "${NC}"

    if [[ "${METHOD}" == 'fresh' && -z "${QUIET}" && -z "${STREAMED}" && -z "${HOMEBREW_INSTALLING}" ]]; then
      echo -e "${ORANGE}"
      if [[ -z "${ANS}" ]]; then
        read -rn 1 -p 'Your current .dotfiles will be replaced and your old files backed up. Continue (y/[n])? ' ANS
      fi
      echo -e "${NC}" && [[ -n "${ANS}" ]] && echo ''
      if [[ ! "${ANS}" =~ ^[yY]$ ]]; then
        echo "Installation aborted!" >>"${INSTALL_LOG}" 2>&1
        echo ">> ANS=${ANS}  QUIET=${QUIET}  METHOD=${METHOD}  STREAM=${STREAMED}" >>"${INSTALL_LOG}"
        quit 1 "Installation aborted!"
      fi
      echo -e "${BLUE}[${METHOD}]${WHITE} Installing HomeSetup... ${NC}"
    else
      echo -e "${BLUE}[${METHOD}]${WHITE} Installing HomeSetup quietly... ${NC}"
    fi

    # Create user dotfiles files.
    [[ -s "${HHS_DIR}/.aliases" ]] || touch "${HHS_DIR}/.aliases"
    [[ -s "${HHS_DIR}/.colors" ]] || touch "${HHS_DIR}/.colors"
    [[ -s "${HHS_DIR}/.env" ]] || touch "${HHS_DIR}/.env"
    [[ -s "${HHS_DIR}/.functions" ]] || touch "${HHS_DIR}/.functions"
    [[ -s "${HHS_DIR}/.profile" ]] || touch "${HHS_DIR}/.profile"
    [[ -s "${HHS_DIR}/.prompt" ]] || touch "${HHS_DIR}/.prompt"
    [[ -s "${HHS_DIR}/.cmd_file" ]] || touch "${HHS_DIR}/.cmd_file"
    [[ -s "${HHS_DIR}/.path" ]] || touch "${HHS_DIR}/.path"
    [[ -s "${HHS_DIR}/.saved_dirs" ]] || touch "${HHS_DIR}/.saved_dirs"

    # Create aliasdef, inputrc, glow.yml, and homesetup.toml
    copy_file "${INSTALL_DIR}/dotfiles/aliasdef" "${HHS_DIR}/.aliasdef"
    copy_file "${INSTALL_DIR}/dotfiles/homesetup.toml" "${HHS_DIR}/.homesetup.toml"
    copy_file "${INSTALL_DIR}/dotfiles/glow.yml" "${HHS_DIR}/.glow.yml"
    copy_file "${INSTALL_DIR}/dotfiles/inputrc" "${HOME}/.inputrc"

    # HomeSetup key bindings
    copy_file "${INSTALL_DIR}/dotfiles/hhs-bindings" "${HHS_DIR}/.hhs-bindings"

    # Find all dotfiles used by HomeSetup according to the current shell type
    while read -r dotfile; do
      ALL_DOTFILES+=("${dotfile}")
    done < <(find "${DOTFILES_SRC}" -maxdepth 1 -type f -name "*.${SHELL_TYPE}" -exec basename {} \;)

    pushd "${DOTFILES_SRC}" >>"${INSTALL_LOG}" 2>&1 || quit 1 "Unable to enter dotfiles directory: \"${DOTFILES_SRC}\" !"

    echo ">>> Linked dotfiles:" >>"${INSTALL_LOG}"
    # If `all' option is used, copy all files
    if [[ "$OPT" == 'all' ]]; then
      # Link all dotfiles
      for next in "${ALL_DOTFILES[@]}"; do
        dotfile="${HOME}/.${next//\.${SHELL_TYPE}/}"
        link_file "${DOTFILES_SRC}/${next}" "${dotfile}"
        echo "${next} -> ${DOTFILES_SRC}/${next}" >>"${INSTALL_LOG}"
      done
    # If `all' option is NOT used, prompt for confirmation
    else
      # Link all dotfiles
      for next in "${ALL_DOTFILES[@]}"; do
        dotfile="${HOME}/.${next//\.${SHELL_TYPE}/}"
        echo ''
        [[ -z ${QUIET} && -z "${STREAMED}" ]] && read -rn 1 -sp "Link ${dotfile} (y/[n])? " ANS
        [[ ! "${ANS}" =~ ^[yY]$ ]] && continue
        echo ''
        link_file "${DOTFILES_SRC}/${next}" "${dotfile}"
        echo "${next} -> ${DOTFILES_SRC}/${next}" >>"${INSTALL_LOG}"
      done
    fi

    # Remove old apps
    echo -en "\n${WHITE}Removing old links... ${BLUE}"
    echo ">>> Removed old links:" >>"${INSTALL_LOG}"
    if find "${HHS_BIN_DIR}" -maxdepth 1 -type l -delete -print >>"${INSTALL_LOG}" 2>&1; then
      echo -e "${GREEN}OK${NC}"
    else
      quit 2 "Unable to remove old app links from \"${HHS_BIN_DIR}\" directory !"
    fi

    # Link apps into place
    echo -en "\n${WHITE}Linking apps from ${BLUE}${APPS_DIR} to ${HHS_BIN_DIR}..."
    echo ">>> Linked apps:" >>"${INSTALL_LOG}"
    if find "${APPS_DIR}" -maxdepth 3 -type f -iname "**.${SHELL_TYPE}" \
      -print \
      -exec ln -sfv {} "${HHS_BIN_DIR}" \; \
      -exec chmod +x {} \; >>"${INSTALL_LOG}" 2>&1; then
      echo -e " ${GREEN}OK${NC}"
    else
      quit 2 "Unable to link apps into \"${HHS_BIN_DIR}\" directory !"
    fi

    # Link auto-completes into place
    echo -en "\n${WHITE}Linking auto-completes from ${BLUE}${COMPLETIONS_DIR} to ${HHS_BIN_DIR}... "
    echo ">>> Linked auto-completes:" >>"${INSTALL_LOG}"
    if find "${COMPLETIONS_DIR}" -maxdepth 2 -type f -iname "**-completion.${SHELL_TYPE}" \
      -print \
      -exec ln -sfv {} "${HHS_BIN_DIR}" \; \
      -exec chmod +x {} \; >>"${INSTALL_LOG}" 2>&1; then
      echo -e " ${GREEN}OK${NC}"
    else
      quit 2 "Unable to link auto-completes into bin (${HHS_BIN_DIR}) directory !"
    fi

    # Link key-bindings into place
    echo -en "\n${WHITE}Linking key-bindings from ${BLUE}${BINDINGS_DIR} to ${HHS_BIN_DIR}... "
    echo ">>> Linked key-bindings:" >>"${INSTALL_LOG}"
    if find "${BINDINGS_DIR}" -maxdepth 2 -type f -iname "**-key-bindings.${SHELL_TYPE}" \
      -print \
      -exec ln -sfv {} "${HHS_BIN_DIR}" \; \
      -exec chmod +x {} \; >>"${INSTALL_LOG}" 2>&1; then
      echo -e " ${GREEN}OK${NC}"
    else
      quit 2 "Unable to link key-bindings into bin (${HHS_BIN_DIR}) directory !"
    fi

    # Copy HomeSetup fonts into place
    echo -en "\n${WHITE}Copying HomeSetup fonts into ${BLUE}${FONTS_DIR}... "
    echo ">>> Copied HomeSetup fonts" >>"${INSTALL_LOG}"
    [[ -d "${FONTS_DIR}" ]] || quit 2 "Unable to locate fonts (${FONTS_DIR}) directory !"
    if find "${INSTALL_DIR}"/assets/fonts -maxdepth 1 -type f \( -iname "*.otf" -o -iname "*.ttf" \) \
      -print \
      -exec rsync --archive {} "${FONTS_DIR}" \; \
      -exec chown "${USER}":"${GROUP}" {} \; >>"${INSTALL_LOG}" 2>&1; then
      echo -e "${GREEN}OK${NC}"
    else
      quit 2 "Unable to copy HHS fonts into fonts (${FONTS_DIR}) directory !"
    fi

    # Copy hunspell dictionaries
    echo -en "\n${WHITE}Copying Hunspell dictionaries into ${BLUE}\"${HUNSPELL_DIR}\"... "
    echo ">>> Copied Hunspell dictionaries" >>"${INSTALL_LOG}"
    [[ -d "${HUNSPELL_DIR}" ]] || quit 2 "Unable to locate hunspell (${HUNSPELL_DIR}) directory !"
    if find "${INSTALL_DIR}"/assets/hunspell-dicts -maxdepth 1 -type f \( -iname "*.aff" -o -iname "*.dic" \) \
      -print \
      -exec rsync --archive {} "${HUNSPELL_DIR}" \; \
      -exec chown "${USER}":"${GROUP}" {} \; >>"${INSTALL_LOG}" 2>&1; then
      echo -e "${GREEN}OK${NC}"
    else
      quit 2 "Unable to extract Hunspell files into dictionaries(${HUNSPELL_DIR}) directory !"
    fi

    # Copy NeoVim integration configs
    echo -en "\n${WHITE}Copying NeoVim integration configs and plugins into ${BLUE}\"${NEOVIM_DIR}\"... "
    if cp -Rf "${INSTALL_DIR}"/assets/nvim "${NEOVIM_DIR}"; then
      echo -e "${GREEN}OK${NC}"
    else
      quit 2 "Unable to copy NeoVim configuration files into (${NEOVIM_DIR}) directory !"
    fi

    # -----------------------------------------------------------------------------------
    # Set default HomeSetup terminal options
    case "${SHELL_TYPE}" in
    bash)
      # Creating the shell-opts file
      echo -en "\n${WHITE}Creating the Shell Options file ${BLUE}${HHS_SHOPTS_FILE}... "
      \shopt | awk '{print $1" = "$2}' >"${HHS_SHOPTS_FILE}" || quit 2 "Unable to create the Shell Options file !"
      echo -e "${GREEN}OK${NC}"
      ;;
    esac

    # Copy MOTDs file into place
    [[ -d "${HHS_MOTD_DIR}" ]] || create_directory "${HHS_MOTD_DIR}"
    cp "${INSTALL_DIR}"/.MOTD "${HHS_MOTD_DIR}"/000-hhs-motd >>"${INSTALL_LOG}" 2>&1

    # Cleanup old files (older than 30 days)
    echo -en "\n${WHITE}Cleaning up old cache and log files... "
    if find "${HHS_DIR?}/cache" "${HHS_LOG_DIR?}" -type f -mtime +30 -exec rm -f {} \; 2>/dev/null; then
      echo -e "${GREEN}OK${NC}"
    else
      echo -e "${YELLOW}SKIPPED${NC}"
    fi

    \popd >>"${INSTALL_LOG}" 2>&1 || quit 1 "Unable to leave dotfiles directory !"
  }

  # Configure python and HomeSetup python library
  configure_python() {

    echo -en "\n${WHITE}Configuring Python... "

    [[ -z "${PYTHON3}" || -z "${PIP3}" ]] &&
      quit 2 "Python and Pip >= 3.10 <= 3.12 are required to use HomeSetup. <None> has been found!"
    python_version=$("${PYTHON3}" --version 2>&1 | awk '{print $2}')
    [[ ! "${python_version}" =~ ^3\.1[012] ]] &&
      quit 2 "Python and Pip >= 3.10 <= 3.12 are required to use HomeSetup! Found: ${python_version}"

    echo -e "${GREEN}OK${NC}"
    create_venv
  }

  # Create HomeSetup virtual environment
  create_venv() {

    python3_str="${BLUE}[$(basename "${PYTHON3}")]"
    if [[ ! -d "${HHS_VENV_PATH}" ]]; then
      echo -en "\n${python3_str} ${WHITE}Creating virtual environment... "
      if
        ${PIP3} install --upgrade --break-system-packages "virtualenv" >>"${INSTALL_LOG}" 2>&1 &&
          ${PYTHON3} -m virtualenv "${HHS_VENV_PATH}" >>"${INSTALL_LOG}" 2>&1
      then
        echo -e "${GREEN}OK${NC}"
        echo -e "\n${python3_str} ${WHITE}Virtual environment created -> ${CYAN}'${HHS_VENV_PATH}'."
      else
        echo -e "${RED}FAILED${NC}"
        quit 2 "Unable to create virtual environment!"
      fi
    else
      echo -e "\n${python3_str} ${WHITE}Virtual environment already exists -> ${CYAN} '${HHS_VENV_PATH}'."
    fi

    # Activate the virtual environment
    echo -en "\n${python3_str} ${WHITE}Activating virtual environment... ${NC}"
    if source "${HHS_VENV_PATH}"/bin/activate && [[ -n "${VIRTUAL_ENV}" ]]; then
      echo -e "${GREEN}OK${NC}"
      echo -e "\n${python3_str} ${WHITE}Virtual environment activated: ${CYAN}${VENV_PYTHON3}${NC}"
    else
      echo -e "${RED}FAILED${NC}"
      quit 2 "Unable to activate virtual environment!"
    fi

    # Python executable from venv
    VENV_PYTHON3="${VIRTUAL_ENV}/bin/$(basename "${PYTHON3}")"
    # Pip executable from venv
    VENV_PIP3="${VENV_PYTHON3} -m pip"
  }

  # Install HomeSetup python libraries
  install_hspylib() {

    python3_str="${BLUE}[$(basename "${VENV_PYTHON3}")]"
    python_version="$(${VENV_PYTHON3} -V)"
    pip_version="$(${VENV_PIP3} -V | \cut -d ' ' -f1,2)"
    echo -e "\n${python3_str} ${WHITE}Using ${YELLOW}${python_version}${WHITE} and ${YELLOW}P${pip_version:1} ${WHITE}from ${BLUE}\"${VIRTUAL_ENV}\" ${NC}"
    echo -e "\n${python3_str} ${WHITE}Installing HSPyLib packages... \n"
    pkgs=$(mktemp)
    printf "%s\n" "${PYTHON_MODULES[@]}" >"${pkgs}"
    printf "${python3_str} ${WHITE}Module: ${YELLOW}%s${NC}\n" "${PYTHON_MODULES[@]}"
    if
      ${VENV_PIP3} install --upgrade --break-system-packages --ignore-installed -r "${pkgs}" >>"${INSTALL_LOG}" 2>&1 ||
        ${VENV_PIP3} install --upgrade --ignore-installed -r "${pkgs}" >>"${INSTALL_LOG}" 2>&1
    then
      rm -f "$(mktemp)"
      echo "Installed HSPyLib python modules:" >>"${INSTALL_LOG}"
      ${VENV_PIP3} freeze | grep hspylib >>"${INSTALL_LOG}"
      echo -e "\n${python3_str} Installed ${BLUE}HSPyLib${NC} python modules:"
      ${VENV_PIP3} freeze | grep hspylib | sed 's/^/  |-/'
    else
      quit 2 "${RED}FAILED${NC} Unable to install PyPi packages!"
    fi
  }

  # Configure AskAI HomeSetup/RAG documents
  configure_askai_rag() {

    python3_str="${BLUE}[$(basename "${VENV_PYTHON3}")]"
    if [[ -n "${INSTALL_AI}" ]]; then
      # Copy HomeSetup AskAI prompts into place.
      echo -en "\n${python3_str} ${WHITE}Copying HomeSetup RAG docs... "
      echo ">>> Copied HomeSetup RAG docs" >>"${INSTALL_LOG}"
      copy_code="
      from askai.core.component.rag_provider import RAGProvider
      if __name__ == '__main__':
        RAGProvider.copy_rag('${INSTALL_DIR}/docs', 'homesetup-docs')
        RAGProvider.copy_rag('${INSTALL_DIR}/README.md', 'homesetup-docs/README.md')
      "
      export OPENAI_API_KEY="${OPENAI_API_KEY:-your openai api key}"
      export GOOGLE_API_KEY="${GOOGLE_API_KEY:-your google api key}"
      export DEEPL_API_KEY="${DEEPL_API_KEY:-your deepl api key}"
      # Dedent the python code above, 6 spaces for now
      if ${VENV_PYTHON3} -c "${copy_code//      /}" >>"${INSTALL_LOG}" 2>&1; then
        echo -e "${GREEN}OK${NC}"
        echo -en "\n${WHITE}Checking AI capabilities... ${CYAN}"
        # TODO: Uncomment when device checks are implemented
        # ${VENV_PYTHON3} -m askai -r rag  "What is HomeSetup?" 2>&1
        echo -e "${GREEN}OK${NC}"
      else
        quit 2 "Unable to copy HomeSetup docs into AskAI RAG directory !"
      fi
    fi
  }

  # Check for backward HomeSetup backward compatibility
  compatibility_check() {

    echo -e "\n${WHITE}Checking HomeSetup backward compatibility... ${BLUE}"

    # Cleaning up old dotfiles links
    [[ -d "${HHS_BIN_DIR}" ]] && rm -f "${HHS_BIN_DIR:?}/*.*"

    # .profile Needs to be renamed, so, we guarantee that no dead lock occurs
    if [[ -f "${HOME}/.profile" ]]; then
      mv -f "${HOME}/.profile" "${HHS_BACKUP_DIR}/profile.orig"
      echo ''
      echo -e "\n${YELLOW}Your old ${HOME}/.profile had to be renamed to ${HHS_BACKUP_DIR}/profile.orig "
      echo -e "This is to avoid invoking dotfiles multiple times. If you are sure that your .profile don't source either"
      echo -e ".bash_profile or .bashrc, then, you can rename it back to .profile: "
      echo -e "$ mv ${HHS_BACKUP_DIR}/profile.orig ${HOME}/.profile"
      echo -e "${NC}"
    fi

    # Moving old hhs files into the proper directory
    [[ -f "${HOME}/.cmd_file" ]] && mv -f "${HOME}/.cmd_file" "${HHS_DIR}/.cmd_file"
    [[ -f "${HOME}/.saved_dir" ]] && mv -f "${HOME}/.saved_dir" "${HHS_DIR}/.saved_dirs"
    [[ -f "${HOME}/.punches" ]] && mv -f "${HOME}/.punches" "${HHS_DIR}/.punches"
    [[ -f "${HOME}/.firebase" ]] && mv -f "${HOME}/.firebase" "${HHS_DIR}/.firebase"

    # From hspylib integration on
    [[ -f "${HOME}/.aliases" ]] && mv -f "${HOME}/.aliases" "${HHS_DIR}/.aliases"
    [[ -f "${HOME}/.aliasdef" ]] && mv -f "${HOME}/.aliasdef" "${HHS_DIR}/.aliasdef"
    [[ -f "${HOME}/.colors" ]] && mv -f "${HOME}/.colors" "${HHS_DIR}/.colors"
    [[ -f "${HOME}/.env" ]] && mv -f "${HOME}/.env" "${HHS_DIR}/.env"
    [[ -f "${HOME}/.functions" ]] && mv -f "${HOME}/.functions" "${HHS_DIR}/.functions"
    [[ -f "${HOME}/.profile" ]] && mv -f "${HOME}/.profile" "${HHS_DIR}/.profile"
    [[ -f "${HOME}/.prompt" ]] && mv -f "${HOME}/.prompt" "${HHS_DIR}/.prompt"

    # Removing the old ${HOME}/bin folder
    if [[ -L "${HOME}/bin" ]]; then
      rm -rfv "${HOME:?}/bin"
      echo -e "\n${YELLOW}Your old ${HOME}/bin link had to be removed. ${NC}"
    fi

    # .bash_aliasdef was renamed to .aliasdef and it is only copied if it does not exist. #9c592e0
    if [[ -L "${HOME}/.bash_aliasdef" ]]; then
      rm -f "${HOME:?}/.bash_aliasdef"
      echo -e "\n${YELLOW}Your old ${HOME}/.bash_aliasdef link had to be removed. ${NC}"
    fi

    # .inputrc Needs to be updated, so, we need to replace it
    if [[ -f "${HOME}/.inputrc" ]]; then
      mv -f "${HOME}/.inputrc" "${HHS_BACKUP_DIR}/inputrc-${TIMESTAMP}.bak"
      copy_file "${INSTALL_DIR}/dotfiles/inputrc" "${HOME}/.inputrc"
      echo -e "\n${YELLOW}Your old ${HOME}/.inputrc had to be replaced by a newer version. Your old file it located at ${HHS_BACKUP_DIR}/inputrc-${TIMESTAMP}.bak ${NC}"
    fi

    # .aliasdef Needs to be updated, so, we need to replace it
    if [[ -f "${HOME}/.aliasdef" ]]; then
      mv -f "${HOME}/.aliasdef" "${HHS_BACKUP_DIR}/aliasdef-${TIMESTAMP}.bak"
      copy_file "${INSTALL_DIR}/dotfiles/aliasdef" "${HHS_DIR}/.aliasdef"
      echo -e "\n${YELLOW}Your old .aliasdef had to be replaced by a newer version. Your old file it located at ${HHS_BACKUP_DIR}/aliasdef-${TIMESTAMP}.bak ${NC}"
    fi

    if [[ -f "${HHS_DIR}/.homesetup.toml" ]]; then
      # Check if the homesetup.toml is outdated
      user_version=$(grep -o '^# @version: v[0-9]*\.[0-9]*\.[0-9]*' "${HHS_DIR}/.homesetup.toml" | sed 's/# @version: v//')
      hhs_version=$(grep -o '^# @version: v[0-9]*\.[0-9]*\.[0-9]*' "${INSTALL_DIR}/dotfiles/homesetup.toml" | sed 's/# @version: v//')
      user_num=$(echo "${user_version}" | awk -F. '{ printf "%d%02d%03d", $1, $2, $3 }')
      hhs_num=$(echo "${hhs_version}" | awk -F. '{ printf "%d%02d%03d", $1, $2, $3 }')
      if [[ "${hhs_num}" -gt "${user_num}" ]]; then
        mv -f "$HHS_DIR/.homesetup.toml" "${HHS_BACKUP_DIR}/homesetup-${TIMESTAMP}.toml.bak"
        copy_file "${INSTALL_DIR}/dotfiles/homesetup.toml" "${HHS_DIR}/.homesetup.toml"
        echo -e "\n${YELLOW}Your old .homesetup.toml had to be replaced by a newer version. Your old file it located at ${HHS_BACKUP_DIR}/homesetup-${TIMESTAMP}.toml.bak ${NC}"
      fi
    fi

    # Moving .path file to .hhs
    if [[ -f "${HOME}/.path" ]]; then
      mv -f "${HOME}/.path" "${HHS_DIR}/.path"
      echo -e "\n${YELLOW}Moved file ${HOME}/.path into ${HHS_DIR}/.path"
    fi

    # .bash_completions was renamed to .bash_completion. #e6ce231
    [[ -L "${HOME}/.bash_completions" ]] && rm -f "${HOME}/.bash_completions"
    # .bash_completion was deleted.
    [[ -L "${HOME}/.bash_completion" ]] && rm -f "${HOME}/.bash_completion"

    # Removing the old python lib directories and links
    [[ -d "${INSTALL_DIR}/bin/apps/bash/hhs-app/lib" ]] &&
      rm -rfv "${INSTALL_DIR:?}/bin/apps/bash/hhs-app/lib"
    [[ -L "${INSTALL_DIR:?}/bin/apps/bash/hhs-app/plugins/firebase/lib" ]] &&
      rm -rfv "${INSTALL_DIR:?}/bin/apps/bash/hhs-app/plugins/firebase/lib"
    [[ -L "${INSTALL_DIR}/bin/apps/bash/hhs-app/plugins/vault/lib" ]] &&
      rm -rfv "${INSTALL_DIR:?}/bin/apps/bash/hhs-app/plugins/vault/lib"

    # Moving orig and bak files to backup folder
    find "${HHS_DIR}" -maxdepth 1 \
      -type f \( -name '*.bak' -o -name '*.orig' \) \
      -print -exec mv {} "${HHS_BACKUP_DIR}" \;

    # .tailor Needs to be updated, so, we need to replace it
    if [[ -f "${HHS_DIR}/.tailor" ]]; then
      mv -f "${HHS_DIR}/.tailor" "${HHS_BACKUP_DIR}/tailor-${TIMESTAMP}.bak"
      echo -e "\n${YELLOW}Your old .tailor had to be replaced by a newer version. Your old file it located at ${HHS_BACKUP_DIR}/tailor-${TIMESTAMP}.bak ${NC}"
    fi

    # Old $HHS_DIR/starship.toml changed to $HHS_DIR/.starship.toml
    if [[ -f "${HHS_DIR}/starship.toml" ]]; then
      mv -f "${HHS_DIR}/starship.toml" "${HHS_BACKUP_DIR}/starship.toml-${TIMESTAMP}.bak"
      echo -e "\n${YELLOW}Your old starship.toml had to be replaced by a newer version. Your old file it located at ${HHS_BACKUP_DIR}/starship.toml-${TIMESTAMP}.bak ${NC}"
    fi

    # Old hhs-init file changed to homesetup.toml
    if [[ -f "${HHS_DIR}/.hhs-init" ]]; then
      rm -f "${HHS_DIR:?}/.hhs-init"
      echo -e "\n${YELLOW}Your old .hhs-init renamed to .homesetup.toml and the old file was deleted.${NC}"
    fi

    # Init submodules case it's not there yet
    if [[ ! -s "${INSTALL_DIR}/tests/bats/bats-core/bin/bats" ]]; then
      pushd "${INSTALL_DIR}" >>"${INSTALL_LOG}" 2>&1 || quit 1 "Unable to enter homesetup directory \"${INSTALL_DIR}\" !"
      echo -en "\n${WHITE}Pulling ${GREEN}bats ${WHITE} submodules... "
      if git submodule update --init >>"${INSTALL_LOG}" 2>&1; then
        echo -e "${GREEN}OK${NC}"
      else
        echo -e "${RED}FAILED${NC}"
        echo -e "${YELLOW}Bats test will not be available${NC}"
      fi
      popd >>"${INSTALL_LOG}" 2>&1 || quit 1 "Unable to leave homesetup directory \"${INSTALL_DIR}\" !"
    fi

    # From HomeSetup 1.7+, we changed the HomeSetup config dir from $HOME/.hhs to $HOME/.config/hhs to match
    # common the standard
    if [[ -d "${HOME}/.hhs" ]] && \rsync --archive "${HOME}/.hhs" "${HOME}/.config"; then
      echo -e "\n${YELLOW}Your old ~/.hhs folder was moved to ~/.config/hhs !${NC}"
      rm -rf "${HOME:?}/.hhs" >>"${INSTALL_LOG}" 2>&1 || echo -e \
        "${RED}Unable to delete the old .hhs directory. It was moved to ~/.config. Feel free to wipe it out!${NC}"
    fi
  }

  # Install Starship prompt
  configure_starship() {
    if ! command -v starship >>"${INSTALL_LOG}" 2>&1; then
      echo -en "\n${WHITE}Installing Starship prompt... "
      if \curl -sSL "https://starship.rs/install.sh" 1>"${HHS_DIR}/install_starship.sh" &&
        \chmod a+x "${HHS_DIR}"/install_starship.sh &&
        "${HHS_DIR}"/install_starship.sh -y -b "${HHS_BIN_DIR}" >>"${INSTALL_LOG}" 2>&1; then
        echo -e "${GREEN}OK${NC}"
      else
        echo -e "${RED}FAILED${NC}"
        echo -e "${YELLOW}Starship prompt will not be available${NC}"
      fi
    fi
  }

  # Install GTrash application
  configure_gtrash() {
    if ! command -v gtrash >>"${INSTALL_LOG}" 2>&1; then
      arch=$(uname -m)
      arch="${arch//aarch64/arm64}"
      echo -en "\n${WHITE}Installing ${BLUE}GTrash${NC} app... "
      if
        curl -sSL "https://github.com/umlx5h/gtrash/releases/latest/download/gtrash_$(uname -s)_${arch}.tar.gz" | tar xz &&
          chmod a+x ./gtrash &&
          mv ./gtrash "${HHS_DIR}/bin/gtrash"
      then
        echo -e "${GREEN}OK${NC}"
      else
        echo -e "${RED}FAILED${NC}"
        echo -e "${YELLOW}GTrash will not be available${NC}"
      fi
    fi
  }

  # Install ble.sh plug-in
  configure_blesh() {

    ble_repo="https://github.com/akinomyoga/ble.sh.git"
    echo -en "\n${WHITE}Installing ${BLUE}Blesh${NC} plug-in... "
    [[ -d "${HHS_BLESH_DIR}" ]] && rm -rfv "${HHS_BLESH_DIR:?}" >>"${INSTALL_LOG}" 2>&1
    if
      git clone --recursive --depth 1 --shallow-submodules "${ble_repo}" "${HHS_BLESH_DIR}" >>"${INSTALL_LOG}" 2>&1 &&
        make -C "${HHS_BLESH_DIR}" >>"${INSTALL_LOG}" 2>&1
    then
      echo -e "${GREEN}OK${NC}"
    else
      echo -e "${RED}FAILED${NC}"
      echo -e "${YELLOW}Ble-sh will not be available${NC}"
    fi
  }

  # Check installation prefix
  check_prefix() {

    # Create the prefix file to be used
    [[ -n "${PREFIX}" ]] && echo "${PREFIX}" >"${PREFIX_FILE}"
    # Delete the useless prefix file
    [[ -z "${PREFIX}" && -f "${PREFIX_FILE}" ]] && rm -f "${PREFIX_FILE}"
  }

  # Reload the terminal and apply installed files.
  activate_dotfiles() {

    JOB_NAME='HomeSetup restart!' PYTHON3="${VENV_PYTHON3}" source "${HOME}/.bashrc"
    PYTHON3="${PYTHON3:-$(command -v python3.11)}"
    PIP3="${PIP3:-${PYTHON3} -m pip}"

    # Set the auto-update timestamp.
    if [[ "${OS_TYPE}" == "macOS" ]]; then
      date -v+7d '+%s%S' 1>"${HHS_DIR}/.last_update" 2>>"${INSTALL_LOG}"
    elif [[ "${OS_TYPE}" == "Alpine" ]]; then
      date -d "@$(($(date +%s) - 3 * 24 * 60 * 60))" '+%s%S' 1>"${HHS_DIR}/.last_update" 2>>"${INSTALL_LOG}"
    elif [[ "${OS_TYPE}" =~ Debian|RedHat ]]; then
      date -d '+7 days' '+%s%S' 1>"${HHS_DIR}/.last_update" 2>>"${INSTALL_LOG}"
    else
      date '+%s' 1>"${HHS_DIR}/.last_update" 2>>"${INSTALL_LOG}"
    fi

    echo ''
    echo -e "${GREEN}${POINTER_ICN} Done installing HomeSetup v$(cat "${INSTALL_DIR}/.VERSION") !"
    echo -e "${CYAN}"
    echo "____    __    ____  _______  __        ______   ______   .___  ___.  _______ "
    echo "\   \  /  \  /   / |   ____||  |      /      | /  __  \  |   \/   | |   ____|"
    echo " \   \/    \/   /  |  |__   |  |     |  ,----'|  |  |  | |  \  /  | |  |__   "
    echo "  \            /   |   __|  |  |     |  |     |  |  |  | |  |\/|  | |   __|  "
    echo "   \    /\    /    |  |____ |  \`----.|  \`----.|  \`--'  | |  |  |  | |  |____ "
    echo "    \__/  \__/     |_______||_______| \______| \______/  |__|  |__| |_______|"
    echo ''
    echo -e "${MAGENTA}${HAND_PEACE_ICN} The ultimate Terminal experience !"
    ${PIP3} show hspylib-askai >>"${INSTALL_LOG}" 2>&1 &&
      echo -en "${AI_ICN} Empowered with ${GREEN}$(${PYTHON3} -m askai -v)"
    echo ''
    echo -e "${YELLOW}${STAR_ICN} To reload your dotfiles, type: ${WHITE}source ${HOME}/.bashrc"
    echo -e "${YELLOW}${STAR_ICN} To configure your HomeSetup initialization: ${WHITE}hhs setup"
    echo -e "${YELLOW}${STAR_ICN} To check for updates, type: ${WHITE}hhu update"
    echo -e "${YELLOW}${STAR_ICN} To learn more about your new Terminal, type: ${WHITE}cat ${README}"
    echo -e "${YELLOW}${STAR_ICN} For details about the installation, type: ${WHITE}hhs logs install"
    echo -e "${YELLOW}${STAR_ICN} Report issues at: ${WHITE}${ISSUES_URL}"
    echo -e "${NC}"

    echo -e "HomeSetup installation finished: $(date)" >>"${INSTALL_LOG}"
  }

  # shellcheck disable=SC2317
  abort_install() {
    echo ''
    echo "Installation aborted:  ANS=${ANS}  QUIET=${QUIET}  METHOD=${METHOD}" >>"${INSTALL_LOG}" 2>&1
    quit 2 'Installation aborted !'
  }

  trap abort_install SIGINT
  trap abort_install SIGABRT

  [[ "${1}" == "-h" || "${1}" == "--help" ]] && usage

  check_current_shell
  check_inst_method "$@"
  check_prefix
  install_homesetup
  quit 0
}
