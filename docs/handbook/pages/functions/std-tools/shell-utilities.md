<img src="https://iili.io/HvtxC1S.png" width="64" height="64" align="right" />

# HomeSetup Developer Handbook
>
> Standard-Tools

## Table of contents

<!-- toc -->

- [Standard Tools](../../functions.md#standard-tools)
  - [Aliases Related](aliases-related.md#aliases-related-functions)
  - [Built-ins](built-ins.md#built-ins-functions)
  - [CLI Terminal Tools](clitt.md#cli-terminal-tools)
  - [Command Tool](command-tool.md#command-tool)
  - [Directory Related](directory-related.md#directory-related-functions)
  - [File Related](file-related.md#file-related-functions)
  - [Network Related](network-related.md#network-related-functions)
  - [Paths Tool](paths-tool.md#paths-tool)
  - [Profile Related](profile-related.md#profile-related-functions)
  - [Search Related](search-related.md#search-related-functions)
  - [Security Related](security-related.md#security-related-functions)
  - [Shell Utilities](shell-utilities.md#shell-utilities)
  - [System Utilities](system-utilities.md#system-utilities)
  - [Taylor Tool](taylor-tool.md#taylor-tool)
  - [Text Utilities](text-utilities.md#text-utilities)
  - [TOML Utilities](toml-utilities.md#toml-utilities)
  - [Toolchecks](toolchecks.md#tool-checks-functions)
- [Development Tools](../../functions.md#development-tools)
  - [Gradle](../dev-tools/gradle-tools.md#gradle-functions)
  - [Docker](../dev-tools/docker-tools.md#docker-functions)
  - [Git](../dev-tools/git-tools.md#git-functions)

<!-- tocstop -->


### Shell utilities

#### __hhs_history

```bash
usage: __hhs_history [regex_filter]
```

##### **Purpose**

Search for previously issued commands from history using filter.

##### **Returns**

**0** on success; **non-zero** otherwise.

##### **Parameters**

  - $1 _Optional_ : The case-insensitive filter to be used when listing.

##### **Examples**

`hist`

**Output**

```bash
    1  [hjunior, 2023-12-28 14:16:07]  __hhs_history -h
    2  [hjunior, 2023-12-28 14:17:29]  about hl
    3  [hjunior, 2023-12-28 14:17:50]  hist
    4  [hjunior, 2023-12-28 14:18:05]  hist stats
    5  [hjunior, 2023-12-28 14:18:10]  __hhs_hist_stats
    6  [hjunior, 2023-12-28 14:19:14]  hist
...
...
```

#### __hhs_hist_stats

```bash
usage: __hhs_hist_stats [top_N]
```

##### **Purpose**

Display statistics about commands in history.

##### **Returns**

**0** on success; **non-zero** otherwise.

##### **Parameters**

  - $1 _Optional_ : Limit to the top N commands.

##### **Examples**

`__hhs_hist_stats 10`

**Output**

```bash
  1:  git ........................... 050 |▄▄▄▄▄▄▄▄▄▄
  2:  gwb ........................... 030 |▄▄▄▄▄▄
  3:  about ......................... 025 |▄▄▄▄▄
  4:  cat ........................... 015 |▄▄▄
  5:  hhs ........................... 010 |▄▄
  6:  hist .......................... 010 |▄▄
  7:  history ....................... 005 |▄
  8:  man ........................... 005 |▄
  9:  grep .......................... 003 |
 10:  more .......................... 001 |
```

------

#### __hhs_envs

```bash
usage: __hhs_envs [options] [regex_filters]

    Options:
      -a, --add <NAME=VALUE>    Add or edit a custom environment variable.
      -e, --edit                Edit current HHS_ENV_FILE.
      -r, --del <NAME>          Delete a custom environment variable.
      --reveal                  Show secret values (not masked).
      -h, --help                Show this help message.
```

##### **Purpose**

Display and manage custom environment variables using filters.

##### **Returns**

**0** on success; **non-zero** otherwise.

##### **Parameters**

  - $1 _Optional_ : The operation flag, filter, or reveal option.
  - $2 _Optional_ : The environment variable name for add/delete operations.
  - $3 _Optional_ : The environment variable value for add operations.

##### **Examples**

`__hhs_envs hhs`

**Output**

```bash
Listing all exported environment variables matching [ hhs ]:

HHS_ACTIVE_DOTFILES ..................... => bashrc hhsrc bash_commons bash_env bash_colors bash_prompt bash_aliases bash_icons bash_functions
HHS_ALIASES_FILE ........................ => /Users/hjunior/.config/hhs/.aliases
HHS_BACKUP_DIR .......................... => /Users/hjunior/.config/hhs/backup
HHS_CACHE_DIR ........................... => /Users/hjunior/.config/hhs/cache
HHS_CMD_FILE ............................ => /Users/hjunior/.config/hhs/.cmd_file
HHS_DEV_TOOLS ........................... => git hexdump vim tree pcregrep gpg base64 shfmt shellcheck pylint docker sqlite3 perl groovy java ruby python3 gcc make mvn gradl...
HHS_DIR ................................. => /Users/hjunior/.config/hhs
HHS_ENV_FILE ............................ => /Users/hjunior/.config/hhs/.env
...
...
```

------

#### ____hhs_defs

```bash
usage: __hhs_defs [regex_filter]
```

##### **Purpose**

Display all alias definitions using filters.

##### **Returns**

**0** on success; **non-zero** otherwise.

##### **Parameters**

  - $1 _Optional_ : If -e is present, edit the .aliasdef file, otherwise a case-insensitive filter to be used when listing.

##### **Examples**

`__hhs_defs gw`

**Output**

```bash
Listing all alias definitions matching [gw]:

gw ........................ defined as => __hhs_gradle
gwb ....................... defined as => __hhs_gradle_build
gwi ....................... defined as => __hhs_gradle_init
gwp ....................... defined as => __hhs_gradle_projects
gwq ....................... defined as => __hhs_gradle_quiet
gwr ....................... defined as => __hhs_gradle_run
gwt ....................... defined as => __hhs_gradle_tasks
gwtt ...................... defined as => __hhs_gradle_test
gww ....................... defined as => __hhs_gradle_wrapper
```

------

#### __hhs_shell_select

```bash
usage: __hhs_shell_select
```

##### **Purpose**

Select a shell from the existing shell list.

##### **Returns**

**0** on success; **non-zero** otherwise.

##### **Parameters**

N/A

##### **Examples**

`__hhs_shell_select`

**Output**

```bash
Please select your default shell:

  1    /bin/bash
  2     /bin/csh
  3     /bin/dash
  4     /bin/ksh
  5     /bin/sh
  6     /bin/tcsh
  7     /bin/zsh
  8     /usr/local/bin/bash

[Enter] Select  [↑↓] Navigate  [Esc] Quit  [1..8] Goto:
```
