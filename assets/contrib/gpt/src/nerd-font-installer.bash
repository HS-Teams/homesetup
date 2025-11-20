#!/usr/bin/env bash

# Script Name: nerd-font-installer.bash
# Purpose: Install selected Nerd Font from the official repository
# Created Date: Oct 24, 2024
# Author: Hugo
# Required Packages: curl, unzip, fc-cache
# Powered by HomeSetup (https://github.com/yorevs/homesetup)
# GPT: [HHS-Script-Generator](https://chatgpt.com/g/g-ra0RVB9Jo-homesetup-script-generator)

# +------------------------------------------------------------------------------+
# | AIs CAN MAKE MISTAKES.                                                       |
# | For your safety, verify important information and code before executing it.  |
# |                                                                              |
# | This program comes with NO WARRANTY, to the extent permitted by law.         |
# +------------------------------------------------------------------------------+

{
  # https://semver.org/ ; major.minor.patch
  VERSION="1.0.0"

  # Usage message
  USAGE="usage: $(basename "$0") [-h|--help] [-v|--version] [-f|--font <font_name>]

  This script allows you to download and install a Nerd Font of your choice.

  Options:
    -h, --help            Display this help message and exit
    -v, --version         Print version information and exit
    -f, --font <name>     Install the first matching font by name (partial match)
    -d, --droid           Install HomeSetup provided nerd font

  Examples:
    $(basename "$0")
    $(basename "$0") -f 'Droid'
  "

  # Nerd font version
  NF_VERSION="v3.2.1"

  # HHS Nerd font version
  HHS_VERSION="v1.7.17"

  # Resources dir
  RESOURCE_DIR="$(dirname "${BASH_SOURCE[0]}")/resources"

  # @purpose: Display the usage/help message
  usage() {
      echo "$USAGE"
  }

  # @purpose: Display the version information
  version() {
      echo "$(basename "$0") version ${VERSION}"
      exit 0
  }

  # @purpose: Check if required packages are installed
  require_package() {
    if ! command -v "$1" &>/dev/null; then
      echo -e "\033[31mERROR:\033[m Package '$1' is not installed. Please install it and try again."
      exit 1
    fi
  }

  # @purpose: Validate that the font list CSV exists
  validate_font_list() {
    if [[ ! -f "$RESOURCE_DIR/nerd-font-list.csv" ]]; then
      echo -e "\033[31mERROR:\033[m Font list file not found: $RESOURCE_DIR/nerd-font-list.csv"
      exit 1
    fi
  }

  # @purpose: Calculate the maximum font name length
  get_max_font_length() {
    tail -n +2 "$RESOURCE_DIR/nerd-font-list.csv" | cut -d ';' -f 1 | awk '{ if (length > max) max = length } END { print max + 2 }'
  }

  # @purpose: Display available fonts in columns based on terminal width
  display_fonts_list() {
    local columns max_width
    columns=$(tput cols)  # Get terminal width
    max_width=$(get_max_font_length)  # Max font name length + 2 spaces

    # Adjust the number of columns to fit within the terminal width
    local num_columns=$(( (columns / (max_width + 5)) ))  # Extra padding between columns
    num_columns=$((num_columns > 0 ? num_columns : 1))

    # Extract font names from the CSV and print in columns
    tail -n +2 "$RESOURCE_DIR/nerd-font-list.csv" | cut -d ';' -f 1 |
    awk -v cols="$num_columns" -v width="$max_width" '
    {
      printf "\033[33m%-4d\033[m %-*s", NR, width, $0
      if (NR % cols == 0) print ""  # Newline after every full row
    }
    END { if (NR % cols != 0) print "" }  # Ensure proper formatting for partial rows
    '
  }

  # @purpose: Retrieve the selected font name from the CSV
  get_selected_font() {
    tail -n +2 "$RESOURCE_DIR/nerd-font-list.csv" | sed -n "${1}p" | cut -d ';' -f 1
  }

  # @purpose: Find a font by partial name
  find_font_by_name() {
    local name="$1"
    tail -n +2 "$RESOURCE_DIR/nerd-font-list.csv" | cut -d ';' -f 1 | grep -i -m 1 "$name"
  }

  # @purpose: Download and install the selected font
  install_font() {
    font_name="${1// /}"
    font_name="${font_name//NerdFont/}"
    font_url="${font_url:-https://github.com/ryanoasis/nerd-fonts/releases/download/${NF_VERSION}/${font_name// /%20}.zip}"
    font_zip="/tmp/${font_name// /_}.zip"
    target_dir="$HOME/.fonts/${font_name}"

    if [[ ! -f "${font_zip}" ]]; then
      # Download the font ZIP file
      echo -en "\033[34mDownloading\033[m \n  \033[33m${font_name}\033[m\n  from \033[36m'${font_url}'\033[m\n  into \033[36m'${target_dir}\033[m'..."
      if ! curl --fail -L -o "${font_zip}" "${font_url}" &>/dev/null || [[ ! -f "${font_zip}" ]]; then
        echo -e "\033[31m FAIL\033[m"
        echo -e "\033[31mERROR:\033[m Failed to download ${font_name}. Exiting."
        exit 1
      else
        echo -e "\033[32m OK\033[m"
      fi
    else
      echo -e "\033[34mUsing existing\033[m font ZIP file: \033[32m'${font_zip}'\033[m."
    fi

    echo -en "\033[34mExtracting\033[m \n  \033[33m${font_name}\033[m\n  into \033[36m'${target_dir}'\033[m..."

    # Extract the ZIP file, redirecting stdout to /dev/null
    if mkdir -p "${target_dir}" && unzip -o -q "${font_zip}" -d "${target_dir}" &>/dev/null; then
      # Check if the font files were extracted successfully
      if [[ ! -d "${target_dir}" || -z "$(ls -A "${target_dir}")" ]]; then
        echo -e "\033[31m FAIL\033[m"
        echo -e "\033[31mERROR:\033[m Failed to install ${font_name}. Exiting."
        exit 1
      else
        echo -e "\033[32m OK\033[m"
      fi
    else
      echo -e "\033[31mERROR:\033[m Failed to unzip '${font_zip}' into '${target_dir}'. Exiting."
      exit 1
    fi

    # for Mac users, we need to copy the fonts into ~/Library/Fonts/
    [[ "$(uname)" == "Darwin" ]] && \cp -rf "${target_dir}" "${HOME}/Library/Fonts/"

    echo -en "\033[34mCaching fonts\033[m..."

    # Refresh the font cache, redirecting stdout to /dev/null
    if fc-cache -f &>/dev/null; then
      echo -e "\033[32m OK\033[m\n"
      echo -e "\033[32mSUCCESS:\033[m \033[33m${font_name}\033[m installed successfully."
    else
      echo -e "\033[31m FAIL\033[m\n"
      echo -e "\033[31mFAILED:\033[m \033[33m${font_name}\033[m installed failed. Exiting."
      exit 1
    fi
  }

  # @purpose: Parse command-line arguments
  parse_args() {
    while [[ $# -gt 0 ]]; do
      case "$1" in
        -h|--help) usage; exit 0 ;;
        -v|--version) version; exit 0 ;;
        -f|--font) shift; quiet_font_name="$1" ;;
        -d|--droid) hhs_font="1" ;;
        *) echo -e "\033[31mERROR:\033[m Invalid option: $1" >&2; usage; exit 2 ;;
      esac
      shift
    done
  }

  # Ensure required packages are available
  require_package "curl"
  require_package "unzip"
  require_package "fc-cache"

  # Validate that the font list exists
  validate_font_list

  # Parse input arguments
  quiet_font_name=""
  hhs_font=""
  parse_args "$@"

  # If -f option is used, install the specified font directly
  if [[ -n "$quiet_font_name" ]]; then
    selected_font=$(find_font_by_name "$quiet_font_name")
    [[ -z "$selected_font" ]] && echo -e "\033[31mERROR:\033[m Font not found: '$quiet_font_name'!" && exit 1
  fi

  # If -d option is used, install the HomeSetup Droid font directly
  if [[ -n "$hhs_font" ]]; then
    selected_font="Droid-Sans-Mono-for-Powerline-Nerd-Font-Complete"
    font_url="https://github.com/yorevs/homesetup/releases/download/${HHS_VERSION}/${selected_font}.zip"
  fi

  if [[ -z "$selected_font" ]]; then
    # Display list of available fonts for user selection
    echo -e "\033[33mAvailable Nerd Fonts:\033[m\n"
    display_fonts_list

    echo ''  # Add a blank line before asking for user input

    # Ask user to select a font
    read -rp "Enter the number of the font you wish to install: " font_choice
    echo ''

    [[ -z "$font_choice" ]] && exit 1

    # Retrieve the selected font name
    selected_font=$(get_selected_font "$font_choice")

    if [[ -z "$selected_font" ]]; then
      echo -e "\033[31mERROR:\033[m Invalid font selection. Exiting."
      exit 1
    fi
  fi

  # Install the selected font
  [[ -n "$selected_font" ]] && install_font "$selected_font" && exit 0

  exit 1
}
