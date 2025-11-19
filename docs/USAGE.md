<img src="https://iili.io/HvtxC1S.png" width="64" height="64" align="right" />

# HomeSetup Usage
>
> The ultimate Terminal experience

HomeSetup offers a comprehensive [User Handbook](handbook/handbook.md) that contains detailed documentation on all commands and examples of their usage. Additionally, there will soon be a _YouTube video series_ available that guides you through the installation, usage, configuration, and utilization of all the features and enhancements provided.

The User Handbook serves as a valuable resource for understanding and making the most of HomeSetup's capabilities, while the accompanying [YouTube]() and [asciinema](https://asciinema.org/~yorevs) videos provides a visual demonstration of its usage.

## Help template

All HomeSetup scripts and functions now emit help messages that follow a consistent, case-sensitive template. The same layout is shipped inside `templates/txt/help.txt` and powers `install.bash`, `hhs`, the plug-ins and the standalone utilities:

```
usage: ${APP_NAME} <arg_name> [options]
    # Optional: App. SYNOPSIS.
    # Optional: App. DESCRIPTION.

    options:
      -A | --A_long                     : TODO: Description about the option -A
      -B | --B_long  <ARG_1>            : TODO: Description about the option -B

    arguments:
      ARG_1   : TODO: Description about the argument

  Notes:
    - Optional: App. NOTES
```

Every CLI now documents its synopsis, options, arguments and notes using this structure, making it easier to skim command capabilities directly from the terminal.

## Table of contents

<!-- toc -->

- [1. Built-in dotfiles](#built-in-dotfiles)
- [2. Aliases](#aliases)
  - [2.1. Navigational](#navigational)
  - [2.2. General](#general)
  - [2.3. HomeSetup](#homesetup)
  - [2.4. External tools](#external-tools)
  - [2.5. OS Specific aliases](#os-specific-aliases)
    - [2.5.1. Linux](#linux)
    - [2.5.2. Darwin](#darwin)
  - [3.6. Handy terminal shortcuts](#handy-terminal-shortcuts)
  - [3.7. Python aliases](#python-aliases)
  - [3.8. Perl aliases](#perl-aliases)
  - [3.9. Git aliases](#git-aliases)
  - [3.10. Gradle aliases](#gradle-aliases)
  - [3.11. Docker aliases](#docker-aliases)
- [3. Functions](#functions)
  - [3.1. Standard tools](#standard-tools)
  - [3.2. Development tools](#development-tools)
- [4. Applications](#applications)
  - [4.1. Built-ins](#built-ins)
- [5. Alias Definitions](#alias-definitions)
- [6. HomeSetup application](#homesetup-application)
  - [6.1. HHS-Plug-ins](#hhs-plug-ins)
  - [6.2. HHS-Functions](#hhs-functions)
- [7. Auto completions](#auto-completions)
  - [7.1. Bash completions](#bash-completions)

## Built-in dotfiles

The following dotfiles will be available after installing HomeSetup:

| HHS Dotfile        | Description                |
|--------------------|----------------------------|
| ~/.bash_aliases    | HomeSetup built-in aliases |
| ~/.bash_colors     | Terminal color definitions |
| ~/.bash_commons    | Common HomeSetup functions |
| ~/.bash_completion | Bash completion functions  |
| ~/.bash_env        | Environment variables      |
| ~/.bash_functions  | Bash scripting functions   |
| ~/.bash_icons      | Predefined unicode icons   |
| ~/.bash_profile    | Login Bash resources       |
| ~/.bash_prompt     | Enhanced shell prompt      |
| ~/.bashrc          | Login Bash resources       |
| ~/.hhsrc           | HomeSetup resources        |

The following directories will be created in your **$HHS_DIR** folder:

- `$HHS_DIR/backup` # Includes all HomeSetup backup files.
- `$HHS_DIR/bin` # Includes all useful scripts provided by the project.
- `$HHS_DIR/cache` # Includes all HomeSetup cache files.
- `$HHS_DIR/log` # Includes all HomeSetup log files.

If the installation folder already exists, the install script will replace all files, taking care to back up the
important ones. To override or add customized configurations, you can create a custom file using the following:

| Custom Dotfile     | Description                             |
|--------------------|-----------------------------------------|
| ~/.aliases         | To customize your aliases               |
| ~/.colors          | To customize your colors                |
| ~/.env             | To customize your environment variables |
| ~/.functions       | To customize your functions             |
| ~/.path            | To customize your paths                 |
| ~/.profile         | To customize your profile               |
| ~/.prompt          | To customize your prompt                |
| ~/.homesetup.toml  | HomeSetup initialization file           |
| ~/.starship.toml   | Starship configuration file             |

## Aliases

HomeSetup will provide many useful aliases (shortcuts) to your terminal:

### Navigational

| ALIAS | Equivalent | Description                                                         |
|-------|------------|---------------------------------------------------------------------|
| ..    | cd ..      | Change-back to previous directory                                   |
| ...   | cd ...     | Change-back two previous directories                                |
| ....  | cd ....    | Change-back three previous directories                              |
| ..... | cd .....   | Change-back four previous directories                               |
| ~     | cd ~       | Change the current directory to HOME dir                            |
| \-    | cd -       | Change the current directory to the previous dir                    |
| ?     | pwd        | Display the current working dir and remote repository if it applies |

### General

| ALIAS     | Description                                                        |
|-----------|--------------------------------------------------------------------|
| q         | Shorthand for `exit 0' from terminal                               |
| sudo      | Enable aliases to be sudo’ed                                       |
| ls        | Always use color output for **ls**                                 |
| l         | List _all files_ colorized in long format                          |
| ld        | List _all directories_ colorized in long format                    |
| lf        | List _all files_ colorized in long format                          |
| ll        | List _all files_ colorized in long format, **including dotfiles**  |
| lll       | List _all **.dotfiles**_ colorized in long format                  |
| lld       | List _all **.dotfolders**_ colorized in long format                |
| grep      | Always enable colored **grep** output                              |
| fgrep     | Always enable colored **egrep** output                             |
| egrep     | Always enable colored **fgrep** output                             |
| cd        | Built-ins replacement for `cd'                                     |
| dirs      | Built-ins replacement for `dirs'                                   |
| help      | Built-ins replacement for `help'                                   |
| starship  | Starship replacement for `starship' binary                         |
| rm        | By default **rm** will prompt for confirmation and will be verbose |
| cp        | By default **cp** will prompt for confirmation and will be verbose |
| mv        | By default **mv** will prompt for confirmation and will be verbose |
| df        | Make **df** command output pretty and human readable format        |
| du        | Make **du** command output pretty and human readable format        |
| psg       | Make **ps** command output pretty and human readable format        |
| ifs       | Display current value of IFS                                       |
| open      | Use the assigned app to open a file                                |
| shopt     | Display/Set/unset current Shell Options                            |
| vi        | Use **vim** instead of **vi** if installed                         |
| more      | **more** will interpret escape sequences                           |
| less      | **less** will interpret escape sequences                           |
| mount     | Make `mount' command output pretty and human readable format       |
| week      | Date&Time - Display current **week number**                        |
| now       | Date&Time - Display current **date and time**                      |
| ts        | Date&Time - Display current **timestamp**                          |
| wget      | If **wget** is not available, use **curl** instead                 |
| ps1       | Make _PS1_ prompt active                                           |
| ps2       | Make _PS2_ prompt active (continuation prompt)                     |

### HomeSetup

| ALIAS          | Description                                            |
|----------------|--------------------------------------------------------|
| __hhs_reload   | Alias to reload HomeSetup                              |
| __hhs_clear    | Alias to clear and reset cursor attributes and **IFS** |
| __hhs_reset    | Alias to clear screen and reset the terminal           |
| __hhs_hspm     | Shortcut for `hhs hspm` plug-in                        |
| __hhs_hhu      | Shortcut for `hhs updater` plug-in                     |
| __hhs_starship | Shortcut for `hhs starship` plug-in                    |
| __hhs_setup    | Shortcut for `hhs setup` plug-in                       |
| __hhs_firebase | Shortcut for `hhs firebase` plug-in                    |
| __hhs_settings | Shortcut for `hhs settings` plug-in                    |
| __hhs_ask      | Shortcut for `hhs ask` plug-in                         |

### External tools

| ALIAS              | Description                                                                      |
|--------------------|----------------------------------------------------------------------------------|
| ask                | Shortcut for the HomeSetup AskAI application.                                    |
| jenv_set_java_home | Jenv - Set JAVA_HOME using jenv                                                  |
| cleanup-db         | Dropbox - Recursively delete Dropbox conflicted files from the current directory |
| encode             | Shortcut for base64 encode                                                       |

### OS Specific aliases

#### Linux

| ALIAS  | Description                     |
|--------|---------------------------------|
| cpu    | `top' shortcut ordered by CPU % |
| mem    | `top' shortcut ordered by MEM % |
| ised   | Same as sed -i'' -r             |
| esed   | Same as sed -r                  |
| decode | Shortcut for base64 decode      |
| apt    | Same as apt-get                 |

#### Darwin

| ALIAS          | Description                                                              |
|----------------|--------------------------------------------------------------------------|
| cpu            | `top' shortcut ordered by CPU %                                          |
| mem            | `top' shortcut ordered by MEM %                                          |
| ised           | Same as sed -i '' -E                                                     |
| esed           | Same as sed -E                                                           |
| decode         | Shortcut for **base64** decode                                           |
| cleanup-ds     | Delete all _.DS_store_ files recursively                                 |
| flush          | Flush Directory Service cache                                            |
| cleanup-reg    | Clean up LaunchServices to remove duplicates in the **"Open With"** menu |
| show-files     | Show hidden files in Finder                                              |
| hide-files     | Hide hidden files in Finder                                              |
| show-deskicons | Show all desktop icons                                                   |
| hide-deskicons | Hide all desktop icons                                                   |
| hd             | Canonical hex dump; some systems have this symlinked                     |
| md5sum         | If **md5sum** is not available, use **md5** instead`                     |
| sha1           | If **sha1** is not available, use **shasum** instead`                    |

### Handy Terminal Shortcuts

| ALIAS              | Description                          |
|--------------------|--------------------------------------|
| show-cursor        | Make terminal cursor visible         |
| hide-cursor        | Make terminal cursor invisible       |
| save-cursor-pos    | Save terminal cursor position        |
| restore-cursor-pos | Restore terminal cursor position     |
| enable-line-wrap   | Enable terminal line wrap            |
| disable-line-wrap  | Disable terminal line wrap           |
| enable-echo        | Enable terminal echo                 |
| disable-echo       | Disable terminal echo                |
| reset-cursor-attrs | Reset all terminal cursor attributes |
| save-screen        | Save the current terminal screen     |
| restore-screen     | Restore the saved terminal screen    |

### Python aliases

| ALIAS           | Description                         |
|-----------------|-------------------------------------|
| __hhs_urle      | URL-encode strings                  |
| __hhs_urld      | URL-decode strings                  |
| __hhs_uuid      | Generate a random UUID              |
| __hhs_tcalc     | Evaluate mathematical expressions   |
| __hhs_clitt     | Shortcut for hspylib-clitt module   |
| __hhs_vault     | Shortcut for hspylib-vault module   |
| __hhs_cfman     | Shortcut for hspylib-cfman module   |
| __hhs_kafman    | Shortcut for hspylib-kafman module  |

### Perl aliases

| ALIAS         | Description                            |
|---------------|----------------------------------------|
| clean_escapes | Remove escape (\EscXX) codes from text |
| clipboard     | Copy to clipboard **pbcopy required**  |

### Git aliases

| ALIAS                 | Description                             |
|-----------------------|-----------------------------------------|
| __hhs_git_status      | Git - Enhancement for **git status**    |
| __hhs_git_fetch       | Git - Shortcut for **git fetch**        |
| __hhs_git_history     | Git - Shortcut for **git log**          |
| __hhs_git_branch      | Git - Shortcut for **git branch**       |
| __hhs_git_diff        | Git - Shortcut for **git diff**         |
| __hhs_git_pull        | Git - Shortcut for **git pull**         |
| __hhs_git_log         | Git - Enhancement for **git log**       |
| __hhs_git_checkout    | Git - Shortcut for git **checkout**     |
| __hhs_git_add         | Git - Shortcut for git **add**          |
| __hhs_git_commit      | Git - Shortcut for git **commit**       |
| __hhs_git_amend       | Git - Shortcut for git **commit amend** |
| __hhs_git_pull_rebase | Git - Shortcut for git **pull rebase**  |
| __hhs_git_push        | Git - Shortcut for git **push**         |
| __hhs_git_show        | Git - Enhancement for **git diff-tree** |
| __hhs_git_difftool    | Git - Enhancement for **git difftool**  |

### Gradle aliases

| ALIAS                 | Description                                          |
|-----------------------|------------------------------------------------------|
| __hhs_gradle_build    | Gradle - Enhancement for **gradle build**            |
| __hhs_gradle_run      | Gradle - Enhancement for **gradle bootRun**          |
| __hhs_gradle_test     | Gradle - Shortcut for **gradle Test**                |
| __hhs_gradle_init     | Gradle - Shortcut for **gradle init**                |
| __hhs_gradle_quiet    | Gradle - Shortcut for **gradle -q**                  |
| __hhs_gradle_wrapper  | Gradle - Shortcut for **gradle wrapper**             |
| __hhs_gradle_projects | Gradle - Displays all available gradle projects      |
| __hhs_gradle_tasks    | Gradle - Displays all available gradle project tasks |

### Docker aliases

| ALIAS                     | Description                                  |
|---------------------------|----------------------------------------------|
| __hhs_docker_images       | Docker - Enhancement for docker images       |
| __hhs_docker_service      | Docker - Shortcut for docker service         |
| __hhs_docker_remove       | Docker - Shortcut for docker container rm    |
| __hhs_docker_remove_image | Docker - Shortcut for docker rmi             |
| __hhs_docker_ps           | Docker - Enhancement for docker ps           |
| __hhs_docker_top          | Docker - Enhancement for docker stats        |
| __hhs_docker_ls           | Docker - Enhancement for docker container ls |
| __hhs_docker_up           | Enhancement for `docker compose up           |
| __hhs_docker_down         | Shortcut for `docker compose stop            |

## Functions

HomeSetup provides many functions for the shell. All functions includes a help using the options -h or --help.

### Development tools

The complete handbook of development tools can be found on [functions handbook](handbook/pages/functions.md#development-tools)

| File                  | Function                     | Purpose                                                                             |
|-----------------------|------------------------------|-------------------------------------------------------------------------------------|
| hhs-docker-tools.bash | __hhs_docker_kill_all        | Stop, remove and remove dangling [active?] volumes of all docker containers.        |
|                       | __hhs_docker_count           | Count the number of active docker containers.                                       |
|                       | __hhs_docker_info            | Display information about the container.                                            |
|                       | __hhs_docker_exec            | Run a command or bash in a running container.                                       |
|                       | __hhs_docker_compose_exec    | This is the equivalent of docker exec, but for docker-compose.                      |
|                       | __hhs_docker_logs            | Fetch the logs of a container.                                                      |
|                       | __hhs_docker_remove_volumes  | Remove all docker volumes not referenced by any containers (dangling).              |
| hhs-git-tools.bash    | __hhs_git_branch_all         | Get the current branch name of all repositories from the base search path.          |
|                       | __hhs_git_status_all         | Get the status of current branch of all repositories from the base search path.     |
|                       | __hhs_git_branch_previous    | Checkout the previous branch in history (skips branch-to-same-branch changes ).     |
|                       | __hhs_git_show_file_diff     | Display a file diff comparing the version between the first and second commit IDs.  |
|                       | __hhs_git_show_file_contents | Display the contents of a file from specific commit ID.                             |
|                       | __hhs_git_show_changes       | List all changed files from a commit ID.                                            |
|                       | __hhs_git_pull_all           | Search and pull projects from the specified path using the given repository/branch. |
|                       | __hhs_git_branch_select      | Select and checkout a local or remote branch.                                       |
| hhs-gradle-tools.bash | __hhs_gradle                 | Prefer using the wrapper instead of the installed command itself.                   |

### Standard tools

The complete handbook of standard tools can be found on [functions handbook](handbook/pages/functions.md#standard-tools)

| File                   | Function               | Purpose                                                                                      |
|------------------------|------------------------|----------------------------------------------------------------------------------------------|
| hhs-aliases.bash       | __hhs_aliases          | Manipulate custom aliases (add/remove/edit/list).                                            |
| hhs-built-ins.bash     | __hhs_help             | Display a help for the given command.                                                        |
|                        | __hhs_where_am_i       | Display the current working dir and remote repository if it applies.                         |
|                        | __hhs_shopt            | Display/Set/unset current Shell Options.                                                     |
|                        | __hhs_random           | Generate a random number int the range \<min\> \<max\> (all limits included).                |
|                        | __hhs_open             | Open a file or URL with the default program.                                                 |
|                        | __hhs_edit             | Create and/or open a file using the default editor.                                          |
|                        | __hhs_about            | Display information about the given command.                                                 |
| hhs-clitt.bash         | __hhs_minput           | Provide a terminal form input with simple validation.                                        |
|                        | __hhs_mchoose          | Choose options from a list using a navigable menu.                                           |
|                        | __hhs_punch            | PUNCH-THE-CLOCK. This is a helper tool to aid with the timesheet.                            |
|                        | __hhs_mselect          | Select an option from a list using a navigable menu.                                         |
| hhs-command.bash       | __hhs_command          | Add/Remove/List/Execute saved bash commands.                                                 |
| hhs-dirs.bash          | __hhs_list_tree        | List all directories recursively (Nth level depth) as a tree.                                |
|                        | __hhs_save_dir         | Save one directory path for future __hhs_load.                                               |
|                        | __hhs_change_dir       | Change the current working directory to a specific Folder.                                   |
|                        | __hhs_load_dir         | Change the current working directory to pre-saved entry from __hhs_save.                     |
|                        | __hhs_godir            | Search and cd into the first match of the specified directory name.                          |
|                        | __hhs_mkcd             | Create all folders using a slash or dot notation path and immediately change into it.        |
|                        | __hhs_changeback_ndirs | Change back the current working directory by N directories.                                  |
|                        | __hhs_dirs             | Display the list of currently remembered directories.                                        |
| hhs-files.bash         | __hhs_ls_sorted        | List files sorted by the specified column.                                                   |
|                        | __hhs_del_tree         | Move files recursively to the Trash.                                                         |
| hhs-network.bash       | __hhs_ip_info          | Retrieve information about the specified IP.                                                 |
|                        | __hhs_ip_lookup        | Lookup DNS payload to determine the IP address.                                              |
|                        | __hhs_ip_resolve       | Resolve domain names associated with the specified IP.                                       |
|                        | __hhs_port_check       | Check the state of local port(s).                                                            |
|                        | __hhs_active_ifaces    | Display a list of active network interfaces.                                                 |
|                        | __hhs_ip               | Display the associated machine IP of the given kind.                                         |
| hhs-paths.bash         | __hhs_paths            | Manage your custom PATH entries.                                                             |
| hhs-profile-tools.bash | __hhs_activate_nvm     | Lazy load helper function to initialize NVM for the terminal.                                |
|                        | __hhs_activate_rvm     | Lazy load helper function to initialize RVM for the terminal.                                |
|                        | __hhs_activate_jenv    | Lazy load helper function to initialize Jenv for the terminal.                               |
|                        | __hhs_activate_docker  | Lazy load helper function to initialize Docker-Daemon for the terminal.                      |
| hhs-search.bash        | __hhs_search_file      | Search for files and links to files recursively.                                             |
|                        | __hhs_search_dir       | Search for directories and links to directories recursively.                                 |
|                        | __hhs_search_string    | Search in files for strings matching the specified criteria recursively.                     |
| hhs-security.bash      | __hhs_encrypt_file     | Encrypt file using GPG.                                                                      |
|                        | __hhs_decrypt_file     | Decrypt a GPG encrypted file.                                                                |
| hhs-shell-utils.bash   | __hhs_defs             | Display all alias definitions using filters.                                                 |
|                        | __hhs_shell_select     | Select a shell from the existing shell list.                                                 |
|                        | __hhs_history          | Search for previously issued commands from history using filters.                            |
|                        | __hhs_hist_stats       | Display statistics about commands in history.                                                |
|                        | __hhs_envs             | Display all environment variables using filters.                                             |
| hhs-sys-utils.bash     | __hhs_process_kill     | Kills ALL processes specified by name                                                        |
|                        | __hhs_sysinfo          | Display relevant system information.                                                         |
|                        | __hhs_partitions       | Exhibit a Human readable summary about all partitions.                                       |
|                        | __hhs_process_list     | Display a process list matching the process name/expression.                                 |
| hhs-taylor.bash        | __hhs_tailor           | Tail a log using customized colors and patterns.                                             |
| hhs-text.bash          | __hhs_highlight        | Highlight words from the piped stream.                                                       |
|                        | __hhs_json_print       | Pretty print (format) JSON string.                                                           |
|                        | __hhs_ascof            | Convert string into it's decimal ASCII presentation.                                         |
|                        | __hhs_utoh             | Convert unicode to hexadecimal.                                                              |
| hhs-toml.bash          | __hhs_toml_groups      | Print all toml file groups (tables).                                                         |
|                        | __hhs_toml_keys        | Print all toml file group keys (tables).                                                     |
|                        | __hhs_toml_get         | Get the key's value from a toml file.                                                        |
|                        | __hhs_toml_set         | Set the key's value from a toml file.                                                        |
| hhs-toolcheck.bash     | __hhs_toolcheck        | Check whether a tool is installed on the system.                                             |
|                        | __hhs_version          | Check the version of the app using the most common ways.                                     |
|                        | __hhs_tools            | Check whether a list of development tools are installed or not.                              |

### Dotfiles

HomeSetup include some basic helper functions:

| Dotfile              | Function               | Purpose                                                                        |
|----------------------|------------------------|--------------------------------------------------------------------------------|
| bash_commons.bash    | __hhs_errcho           | Echo a message in red color into stderr.                                       |
|                      | __hhs_is_reachable     | Check whether URL/URI is reachable on the network.                             |
|                      | __hhs_has              | Check if a command is available on the current shell context.                  |
|                      | __hhs_log              | Log to HomeSetup log file.                                                     |
|                      | __hhs_source           | Read/Execute commands from the filename argument in the current shell context. |
|                      | __hhs_alias            | Check if an alias does not exists and create it, otherwise ignore it.          |
| bash_prompt.bash     | __hhs_set_win_title    | Set the terminal window title.                                                 |
|                      | __hhs_git_prompt       | Check whether inside a git repository or not, and which branch is checked.     |

## Applications

HomeSetup includes a collection of useful applications that can be accessed directly from the shell. These applications
are also automatically added to your **$PATH** variable for easy execution.

For a comprehensive list and detailed information about the development tools available with HomeSetup, please refer
to the [Applications](handbook/pages/applications.md) section in the complete handbook.

### Built-ins

| Application      | Purpose                                                                                       |
|------------------|-----------------------------------------------------------------------------------------------|
| app-commons.bash | Commonly used bash code functions and variables that you may include it on your bash scripts. |
| check-ip.bash    | Validate and check information about a specified IP.                                          |
| fetch.bash       | Fetch REST APIs data easily.                                                                  |
| hhs.bash         | HomeSetup application.                                                                        |

### CLI help reference

| Command/Script | Synopsis | Highlights |
|----------------|----------|------------|
| `install.bash` | `usage: install.bash [options]` | `--local`, `--repair`, `--interactive`, `--prefix <path>`, `--homebrew`, `--quiet` describe every installation mode and are documented together with installer notes. |
| `uninstall.bash` | `usage: uninstall.bash [options]` | Presents interactive prompts and documents how backups are restored plus the optional `--help/--version` flags. |
| `hhs` | ``usage: hhs [options] {function \| plugin {task} <command>} [args...]`` | Explains the plugin/function tasks, the `--prefix` output helper and the recommended discovery commands (`hhs list`, `<plugin> help`). |
| `fetch.bash` | `usage: fetch [options] <method> <url>` | Details HTTP verbs, payload flags (`--body`, `--headers`, `--timeout`), JSON formatting and silent execution. |
| `docker-build.bash` | `usage: docker-build [options] <image_type...>` | Describes the multi-architecture buildx workflow plus the optional `--push` switch. |
| `check-ip.bash` | `usage: check-ip [options] <ip_address>` | Documents `--quiet`, `--info`, and how the command returns the validation result along with IP class/scope. |
| `hhs app plugins` | `usage: hhs <plugin> [options]` | Plugins such as `ask`, `starship`, `setup`, `taius`, `updater` and `hspm` all describe their supported tasks (e.g. `preset`, `recover`, `check/update/stamp`) plus shared `--help/--version` flags. |
| Utilities under `assets/contrib/gpt` | `usage: <tool> [options]` | The generated scripts (`media-converter`, `temperature-converter`, `iso-to-cron`, `cron-scheduler`, etc.) now call out their required options and guarded notes inside the standardized template. |

## Alias definitions

You have the flexibility to customize **most of the HomeSetup aliases** by editing the `~/.aliasdef` file. When you
initially install HomeSetup, this file will be automatically generated for you. However, future updates may require
you to update this file. We always keep a backup of this file, allowing you to preserve your customizations. Please
note that the backup process needs to be done manually in this case.

The original content and aliases are defined in the original [aliasdef](../dotfiles/aliasdef) file. If you remove your
`~/.aliasdef` file, the HomeSetup's original definitions file will be copied to your **$HHS_DIR** folder next time you
start you terminal.

## HomeSetup Application

HomeSetup is more than just a collection of scripts and functions to enhance your terminal experience. It also includes
an application framework and a variety of **plug-able scripts and functions** that can be seamlessly integrated into it.
To view a comprehensive list of all available functions and plug-ins, you can simply run the following command in your
terminal: `__hhs list`.

If you want to explore and check all the existing functions within HomeSetup, you can simply run the following command
in your terminal: `__hhs funcs`.

Those commands will provide you with an overview of all the functions and plug-ins that HomeSetup offers, allowing you
to explore and leverage their capabilities.

### HHS Plug-ins

| Plug-in  | Purpose                                                                  |
|----------|--------------------------------------------------------------------------|
| settings | Terminal settings manager.                                               |
| starship | Starship prompt manager.                                                 |
| setup    | HomeSetup initialization manager.                                        |
| updater  | Update manager for HomeSetup.                                            |
| firebase | Manager for HomeSetup Firebase integration.                              |
| hspm     | Manage your development tools using installation/uninstallation recipes. |

### HHS Functions

| Function    | Purpose                                                                                |
|-------------|----------------------------------------------------------------------------------------|
| docsify     | Open the HomeSetup **docsify** web page.                                               |
| board       | Open the HomeSetup GitHub project **board** for the current version.                   |
| list        | List all HHS App **Plug-ins** and **Functions**.                                       |
| funcs       | Search for all hhs **functions** describing it's containing file name and line number. |
| logs        | Retrieve latest HomeSetup load logs.                                                   |
| man         | Open manual for command.                                                               |
| reset       | Remove caches, logs and backup files.                                                  |
| host-name   | Retrieve/Get/Set the current hostname.                                                 |
| tests       | Execute all HomeSetup **automated tests**.                                             |
| color-tests | Execute all HomeSetup **terminal color tests**.                                        |

## Auto completions

In addition to the standard bash \<tab\> complete feature, HomeSetup introduces an enhanced completion functionality
accessed through **<shift+tab>**. This feature allows you to iterate over the available options provided by the
completion function, providing a more interactive experience.

By default, HomeSetup _does not load the completions_ during terminal startup to optimize performance. However, if you
wish to load the completions and utilize this enhanced feature, you can issue the following command in your terminal:
`__hhs_load_completions`

Executing this command will load the completions and enable the <shift+tab> complete functionality within HomeSetup.

### Bash completions

| File                           | Purpose                                           |
|--------------------------------|---------------------------------------------------|
| hhs-completion.bash            | Bash completion for HomeSetup.                    |
| brew-completion.bash           | Bash completion for Home Brew.                    |
| docker-completion.bash         | Bash completion file for core docker commands.    |
| docker-compose-completion.bash | Bash completion for docker-compose commands.      |
| docker-machine-completion.bash | Bash completion file for docker-machine commands. |
| git-completion.bash            | Bash/zsh completion support for core Git.         |
| gradle-completion.bash         | Bash and Zsh completion support for Gradle.       |
| helm-completion.bash           | Bash completion for helm.                         |
| kubectl-completion.bash        | Bash completion for kubectl.                      |
| pcf-completion.bash            | Bash completion for Cloud Foundry CLI.            |
