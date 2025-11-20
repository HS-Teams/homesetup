#!/usr/bin/env bash

# Script Name: temperature-converter.bash
# Purpose: Convert temperatures between Celsius, Fahrenheit, and Kelvin
# Created Date: Aug 23, 2024
# Author: Hugo
# Required Packages: None
# Powered by [HomeSetup](https://github.com/yorevs/homesetup)
# GPT: [HHS-Script-Generator](https://chatgpt.com/g/g-ra0RVB9Jo-homesetup-script-generator)

# +------------------------------------------------------------------------------+
# | AIs CAN MAKE MISTAKES.                                                       |
# | For your safety, verify important information and code before executing it.  |
# |                                                                              |
# | This program comes with NO WARRANTY, to the extent permitted by law.         |
# +------------------------------------------------------------------------------+

# https://semver.org/ ; major.minor.patch
VERSION="1.0.0"  # https://semver.org/ ; major.minor.patch

USAGE="usage: $(basename "$0") -t <temperature> -f <C|F|K> -o <C|F|K>
Convert temperatures between Celsius, Fahrenheit, and Kelvin.

Options:
  -t, --temperature   Temperature value to convert
  -f, --from          Current scale of the temperature (C, F, or K)
  -o, --to            Desired scale to convert to (C, F, or K)
  -h, --help          Display this help message and exit
  -v, --version       Print version information and exit

Examples:
  $(basename "$0") -t 100 -f C -o F    # Convert 100°C to °F
  $(basename "$0") -t 212 -f F -o K    # Convert 212°F to K
"

# @purpose: Display help message and exit
usage() {
  echo "$USAGE"
  exit 2
}

# @purpose: Print version information and exit
version() {
  echo "$(basename "$0") version $VERSION"
  exit 0
}

# @purpose: Parse command line arguments
parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      -t|--temperature)
        temperature="$2"
        shift 2
        ;;
      -f|--from)
        from="$2"
        shift 2
        ;;
      -o|--to)
        to="$2"
        shift 2
        ;;
      -h|--help)
        usage
        ;;
      -v|--version)
        version
        ;;
      *)
        echo -e "\033[31mERROR\033[m: Invalid option '$1'"
        usage
        ;;
    esac
  done
}

# @purpose: Convert temperatures between scales
convert_temperature() {
  if [[ "${from}" == "C" && "${to}" == "F" ]]; then
    echo "scale=2; (${temperature} * 9/5) + 32" | bc | xargs printf "%.2f"
  elif [[ "${from}" == "C" && "${to}" == "K" ]]; then
    echo "scale=2; ${temperature} + 273.15" | bc | xargs printf "%.2f"
  elif [[ "${from}" == "F" && "${to}" == "C" ]]; then
    echo "scale=2; (${temperature} - 32) * 5/9" | bc | xargs printf "%.2f"
  elif [[ "${from}" == "F" && "${to}" == "K" ]]; then
    echo "scale=2; (${temperature} - 32) * 5/9 + 273.15" | bc | xargs printf "%.2f"
  elif [[ "${from}" == "K" && "${to}" == "C" ]]; then
    echo "scale=2; ${temperature} - 273.15" | bc | xargs printf "%.2f"
  elif [[ "${from}" == "K" && "${to}" == "F" ]]; then
    echo "scale=2; (${temperature} - 273.15) * 9/5 + 32" | bc | xargs printf "%.2f"
  else
    echo -e "\033[31mERROR\033[m: Invalid conversion request"
    exit 1
  fi
}

# Main script execution
parse_args "$@"

if [[ -z "${temperature}" || -z "${from}" || -z "${to}" ]]; then
  echo -e "\033[31mERROR\033[m: Missing required arguments"
  usage
fi

convert_temperature
