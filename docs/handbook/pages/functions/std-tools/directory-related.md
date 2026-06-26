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

### Directory related functions

#### __hhs_change_dir

```bash
usage: __hhs_change_dir [-L|-P] [dirname]

    Options:
      -L    : Follow symbolic links.
      -P    : Don't follow symbolic links.

  Notes:
    - dirname: The directory to change. If not provided, default is the user's home directory
```

##### **Purpose**

##### **Returns**

**0** if the directory is changed; **non-zero** otherwise.

##### **Parameters**

  - $1 _Optional_ : [-L|-P] whether to follow (-L) or not (-P) symbolic links.
  - $2 _Optional_ : The directory to change. If not provided, default DIR is the value of the HOME variable.

##### **Examples**

`__hhs_change_dir /tmp && pwd`

```bash
/tmp
```

------

#### __hhs_changeback_ndirs

```bash
usage: __hhs_changeback_ndirs [amount]
```

##### **Purpose**

Change back the current working directory by N directories.

##### **Returns**

**0** if directory is changed; **non-zero** otherwise.

##### **Parameters**

  - $1 _Optional_ : The amount of directories to change backwards. If not provided, default is one.

##### **Examples**

`cd $HOME && .. && pwd`

**Output**

```bash
Changed current directory: "/Users"
/Users
```

`cd $HOME && .. 2 && pwd`

**Output**

```bash
Changed directory backwards by 2 time(s) and landed at: "/"
/
```

------

#### __hhs_dirs

```bash
usage: __hhs_dirs
```

##### **Purpose**

Display the list of currently remembered directories.

##### **Returns**

**0** if directory is changed; **non-zero** otherwise.

##### **Parameters**

  - $N _Optional_ : If any parameter is used, the default dirs command is invoked instead.

##### **Examples**

`__hhs_dirs`

**Output**

```bash
Please choose one directory to change into (6) found:

  1    /
  2     /Users/hjunior
  3     /Users/hjunior/.config/hhs
  4     /Users/hjunior/GIT-Repository/GitHub/hspylib
  5     /Users/hjunior/HomeSetup
  6     /tmp

[Enter] Select  [↑↓] Navigate  [Esc] Quit  [1..6] Goto:
```

------

#### __hhs_list_tree

```bash
usage: __hhs_list_tree [dir] [max_depth]
```

##### **Purpose**

List contents of directories in a tree-like format.

##### **Returns**

**0** on success ; **non-zero** otherwise.

##### **Parameters**

  - $N _Optional_ : The directory to list from.
  - $N _Optional_ : The max level depth to walk into.

##### **Examples**

`__hhs_list_tree . 5`

**Output**

```bash
.
├── LICENSE.md
├── README.md
├── _config.yml
├── assets
│   ├── HomeSetup.terminal
│    ├── colorls
│    │    ├── hhs-preset
│    │    │    ├── dark_colors.yaml
│    │    │    ├── file_aliases.yaml
│    │    │    ├── files.yaml
│    │    │    ├── folder_aliases.yaml
...
...
```

------

#### __hhs_save_dir

```bash
usage: __hhs_save_dir -e | [-r] <dir_alias> | <path> <dir_alias>

Options:
    -e : Edit the saved dirs file.
    -r : Remove saved dir.
    -c : Cleanup directory paths that does not exist.
```

##### **Purpose**

Save one directory path for future __hhs_load.

##### **Returns**

**0** if the save was successful; **non-zero** otherwise.

##### **Parameters**

  - $1 _Required_ : The directory path to save or the alias to be removed.
  - $2 _Required_ : The alias to name the saved path.

##### **Examples**

`__hhs_save_dir . dot`

**Output**

```bash
Directory "/Users/hjunior/HomeSetup" saved as DOT
```

`__hhs_save_dir -r dot`

**Output**

```bash
Directory aliased as "DOT" was removed!
```

------

#### __hhs_load_dir

```bash
usage: __hhs_load_dir [-l] | [dir_alias]

Options:
    [dir_alias] : The alias to load the path from.
             -l : If provided, list all saved dirs instead.

  Notes:
    MSelect default : If no arguments is provided, a menu with options will be displayed.
```

##### **Purpose**

Change the current working directory to pre-saved entry from __hhs_save.

##### **Returns**

**0** if the load was successful; **non-zero** otherwise.

##### **Parameters**

  - $1 _Optional_ : The alias to load the path from.
  - $2 _Optional_ : If provided, list all saved dirs instead.

##### **Examples**

`__hhs_load_dir dot`

**Output**

```bash
Directory changed to: "/Users/hjunior/HomeSetup"
```

`__hhs_load_dir -l`

**Output**

```bash
Available directories (3) saved:

AKS......................................  '/tmp'
HOM......................................  '/Users/hjunior'
DOT......................................  '/Users/hjunior/HomeSetup'
```

------

#### __hhs_godir

```bash
usage: __hhs_godir [search_path] <dir_name>
```

##### **Purpose**

Search and cd into the first match of the specified directory name.

##### **Returns**

**0** if directory is changed; **non-zero** otherwise.

##### **Parameters**

  - $1 _Optional_ : The base search path.
  - $2 _Required_ : The directory name to search and cd into.

##### **Examples**

`__hhs_godir /usr/bin`

**Output**

```bash
Directory changed to: "/usr/bin"
```

------

#### __hhs_mkcd

```bash
usage: __hhs_mkcd <dirtree | package>

E.g:. __hhs_mkcd dir1/dir2/dir3 (dirtree)
E.g:. __hhs_mkcd dir1.dir2.dir3 (FQDN)
```

##### **Purpose**

Create all folders using a slash or dot notation path and immediately change into it.

##### **Returns**

**0** on success; **non-zero** otherwise.

##### **Parameters**

  - $1 _Required_ : The directory tree or the package name

##### **Examples**

`__hhs_mkcd dir1/dir2/dir3`

**Output**

```bash
   Directories created: ./dir1/dir2/dir3
  Directory changed to: /tmp/dir1/dir2/dir3
```

`__hhs_mkcd br.edu.hhs`

**Output**

```bash
   Directories created: ./br/edu/hhs
  Directory changed to: /tmp/br/edu/hhs
```
