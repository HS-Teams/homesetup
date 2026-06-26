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

### Command tool

#### __hhs_command

```bash
usage: __hhs_command [options [cmd_alias] <cmd_expression>] | [cmd_index]

    Options:
      [cmd_index]   : Execute the command specified by the command index.
      -e | --edit   : Edit the commands file.
      -a | --add    : Store a command.
      -r | --remove : Remove a command.
      -l | --list   : List all stored commands.

  Notes:
    MSelect default : When no arguments is provided, a menu with options will be displayed.
```

##### **Purpose**:

Add/Remove/List/Execute saved bash commands.

##### **Returns**:

**0** if the command executed successfully; **non-zero** otherwise.

##### **Parameters**:

  - $1 _Optional_ : The command index or alias.
  - $2..$N _Conditional_ : The command expression. This is required when alias is provided.

##### **Examples:**

`__hhs_command -a test ls -la`

**Output**

```bash
Command saved: "TEST" as ls -la
```

`__hhs_command -l`

**Output**

```bash
Available commands (1):

(001) Command TEST.......................  'ls -la'
```

`__hhs_command test`

**Output**

```bash
#> ls -la
   rwxr-xr-x   37   hjunior   staff      1 KiB   Tue Dec 26 17:31:35 2023    ./
   rwx------    9   hjunior   staff    288 B     Thu Dec 21 19:06:11 2023    ../
   rwxr-xr-x   14   hjunior   staff    448 B     Fri Dec 22 19:10:05 2023    backup/
   rwxr-xr-x   18   hjunior   staff    576 B     Fri Dec 22 18:56:47 2023    bin/
   rwxr-xr-x    3   hjunior   staff     96 B     Tue Dec 26 16:39:48 2023    cache/
   rwxr-xr-x    5   hjunior   staff    160 B     Tue Dec 26 15:21:18 2023    log/
   rwxr-xr-x    3   hjunior   staff     96 B     Mon Dec 18 15:24:45 2023    motd/
...
...
```

`__hhs_command -r test`

**Output**

```bash
Command "TEST" removed!
```
