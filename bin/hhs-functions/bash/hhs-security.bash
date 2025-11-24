#!/usr/bin/env bash

#  Script: hhs-security.bash
# Created: Oct 5, 2019
#  Author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
#  Mailto: taius.hhs@gmail.com
#    Site: https://github.com/yorevs/homesetup
# License: Please refer to <https://opensource.org/licenses/MIT>
#
# Copyright (c) 2025, HomeSetup team

# !NOTICE: Do not change this file. To customize your functions edit the file ~/.functions

if __hhs_has 'gpg' && __hhs_has 'base64'; then

  # @function: Encrypt file using GPG.
  # @param $1 [Req] : The file to encrypt.
  # @param $2 [Req] : The passphrase used to encrypt the file.
  # @param $3 [Opt] : If provided, keeps the decrypted file, delete it otherwise.
  function __hhs_encrypt_file() {

    local file="${1}" passwd="${2}" keep_file="${3}"

    if [[ "$#" -lt 2 || "$1" == "-h" || "$1" == "--help" ]]; then
      echo "usage: ${FUNCNAME[0]} <filename> <passphrase> [--keep]"
      return 1
    else
      if [[ ! -f "${file}" ]]; then
        __hhs_errcho "${FUNCNAME[0]}" "File not found: \"${file}\" !"
      elif [[ -z "${passwd}" ]]; then
        __hhs_errcho "${FUNCNAME[0]}" "Passphrase can't be blank !"
      elif gpg --yes --batch --passphrase="${passwd}" -c "${file}" &>/dev/null; then
        if encode -i "${file}.gpg" -o "${file}"; then
          [[ ${keep_file} =~ --[kK][eE]{2}[pP] ]] || rm -f "${file}.gpg" &>/dev/null
          echo -e "${GREEN}File \"${file}\" has been encrypted !${NC}"
          return 0
        fi
      else
        __hhs_errcho "${FUNCNAME[0]}" "Unable to encrypt file: \"$1\" ${NC}"
      fi
    fi

    return 1
  }

  # @function: Decrypt a GPG encrypted file.
  # @param $1 [Req] : The file to decrypt.
  # @param $2 [Req] : The passphrase used to decrypt the file.
  # @param $3 [Opt] : If provided, keeps the encrypted file, delete it otherwise.
  function __hhs_decrypt_file() {

    local file="${1}" passwd="${2}" keep_file="${3}"

    if [[ "$#" -lt 2 || "$1" == "-h" || "$1" == "--help" ]]; then
      echo "usage: ${FUNCNAME[0]} <filename> <passphrase> [--keep]"
      return 1
    else
      if [[ ! -f "${file}" ]]; then
        __hhs_errcho "${FUNCNAME[0]}" "File not found: \"${file}\" !"
      elif [[ -z "${passwd}" ]]; then
        __hhs_errcho "${FUNCNAME[0]}" "Passphrase can't be blank !"
      elif decode -i "${file}" -o "${file}.gpg"; then
        if gpg --yes --batch --passphrase="${passwd}" "${file}.gpg" &>/dev/null; then
          [[ ${keep_file} =~ --[kK][eE]{2}[pP]keep ]] || rm -f "${file}.gpg" &>/dev/null
          echo -e "${GREEN}File \"${file}\" has been decrypted !${NC}"
          return 0
        fi
      else
        __hhs_errcho "${FUNCNAME[0]}" "Unable to decrypt file: \"${file}\""
      fi
    fi

    return 1
  }

fi

# @purpose: Generate a strong password using SHA-256
# @param $1 [Req] : Password length (default 15)
# @param $2 [Req] : Password type (1..4 default 4)
function __hhs_pwgen() {
  local i hash_str charset index=0 length=15 type=4 password rand_index num_letters num_symbols
  local letters="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
  local numbers="0123456789"
  local alphanum="${letters}${numbers}"
  local symbols="!@#\$%^&*()-_=+[]{}<>?/"

  local usage="
usage: ${FUNCNAME[0]} [-l <password_length>] [-t <password_type>]

    Options:
      -l, --length <number>     : Length of the password → default is 15
      -t, --type <1|2|3|4>      : Password type:
                                   1 - Letters (A-Z, a-z)
                                   2 - Numbers (0-9)
                                   3 - Alphanumeric (A-Z, a-z, 0-9)
                                   4 - Strong. Mixed with 70% letters/numbers and 30% symbols → default
      -h, --help                : Show this help message and exit"

  while [[ $# -gt 0 ]]; do
    case "$1" in
    -l | --length)
      shift
      length="${1}"
      ;;
    -t | --type)
      shift
      type="${1}"
      ;;
    -h | --help) quit 0 "${usage}" ;;
    *) quit 1 "Unknown option: $1 \n${usage}" ;;
    esac
    shift
  done

  if [[ -z "${length}" || -z "${type}" ]]; then
    __hhs_errcho "${FUNCNAME[0]}" "Missing required arguments. \n${usage}"
    return 1
  elif ! [[ "${length}" =~ ^[0-9]+$ ]]; then
    __hhs_errcho "${FUNCNAME[0]}" "Password length must be a positive integer. \n${usage}"
    return 1
  elif ! [[ "${type}" =~ ^[1-4]$ ]]; then
    __hhs_errcho "${FUNCNAME[0]}" "Password type must be between [1..4]. \n${usage}"
    return 1
  fi

  # Generate a SHA-256 hash string from random data
  hash_str=$(date +%s%N | shasum -a 256 | awk '{print $1}')

  case "${type}" in
    1) charset="${letters}" ;;
    2) charset="${numbers}" ;;
    3) charset="${alphanum}" ;;
    4)
      num_letters=$((length * 70 / 100))    # 70% letters/numbers
      num_symbols=$((length - num_letters)) # 30% symbols

      # Generate 70% alphanumeric characters
      for ((i = 0; i < num_letters; i++)); do
        rand_index=$((16#${hash_str:index:2} % ${#alphanum}))
        password+="${alphanum:1:1}"
        ((index += 2))
      done

      # Generate 30% symbols
      for ((i = 0; i < num_symbols; i++)); do
        rand_index=$((16#${hash_str:index:2} % ${#symbols}))
        password+="${symbols:rand_index:1}"
        ((index += 2))
      done

      # Shuffle the password to mix letters and symbols
      password=$(echo "${password}" |
        awk 'BEGIN{srand()} {for(i=1;i<=length($0);i++) a[i]=substr($0,i,1);} END{for(i=length($0);i>0;i--) {j=int(rand()*i)+1; printf "%s", a[j]; a[j]=a[i];}}')
      ;;
    *)
      __hhs_errcho "${FUNCNAME[0]}" "Invalid password type. Use -h for help."
      return 1
      ;;
  esac

  if [[ -z "${password}" ]]; then
    # Convert hash_str to usable characters
    for ((i = 0; i < length; i++)); do
      index=$((16#${hash_str:i:2} % ${#charset}))
      password+="${charset:index:1}"
    done
  fi

  if [[ -n "${password}" ]]; then
    echo -n "${password}" | __hhs_clipboard
    echo -e "${GREEN}Password copied to the clipboard!${NC}"
    return 0
  fi
echo '5'
  return 1
}
