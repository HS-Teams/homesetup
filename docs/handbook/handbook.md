<img src="https://iili.io/HvtxC1S.png" width="64" height="64" align="right" />

# HomeSetup Developer Handbook
>
> Introduction

**Thank You** for using HomeSetup. This handbook contains a collection of instructions intended to provide ready
reference for your new terminal features. We will cover all related aliases, applications and functions, as well as
environment variables, configuration files and more.

## Table of contents

<!-- toc -->

- [Environment variables](#environment-variables)
- [Aliases](#aliases)
  - [Alias Definitions](#alias-definitions)
  - [Categories](#categories)
- [Functions](#functions)
- [Applications](#applications)
- [Templates](#templates)

<!-- tocstop -->

## Environment Variables

Your new terminal uses a bunch of environment variables, that will be extended by HomeSetup using the
[bash_envs.bash](../../dotfiles/bash/bash_env.bash).

You can override or add additional variables by adding entries to your installed **~/.env** file. When you first
install HomeSetup this file will be created automatically for you, so you just need to edit it.

> **All HomeSetup variable are prefixed with HHS_**

| VARIABLE                 | Description                                                                                       |
|--------------------------|---------------------------------------------------------------------------------------------------|
| HHS_ACTIVE_DOTFILES      | Dotfiles that are actually active and the load order.                                             |
| HHS_ALIASES_FILE         | File containing your alias exports.                                                               |
| HHS_BACKUP_DIR           | Directory containing all HomeSetup backup files                                                   |
| HHS_BASH_COMPLETIONS     | Bash-completions that are actually active.                                                        |
| HHS_CACHE_DIR            | Directory containing all HomeSetup cache files                                                    |
| HHS_CMD_FILE             | This file holds the saved commands issued by __hhs_command function.                              |
| HHS_DEV_TOOLS            | Tools that HomeSetup will keep an eye on, to check is they are installed or not.                  |
| HHS_DIR                  | This is where HomeSetup stores it's configuration files.                                          |
| HHS_ENV_FILE             | File containing your environment exports.                                                         |
| HHS_EXPORT_SETTINGS      | Whether to export system settings (Setman) or not.                                                |
| HHS_FIREBASE_CONFIG_FILE | File used to store your Firebase integration configurations.                                      |
| HHS_FIREBASE_CREDS_FILE  | File containing your Firebase credentials, used for authentication.                               |
| HHS_GITHUB_URL           | HomeSetup Github URL                                                                              |
| HHS_ASKAI_URL            | HomeSetup AskAI Github URL                                                                        |
| HHS_HAS_DOCKER           | Whether docker is installed and active.                                                           |
| HHS_AI_ENABLED           | Whether AskAI is enabled for HomeSetup.                                                           |
| HHS_HIGHLIGHT_COLOR      | Color to be used to highlight text on some functions.                                             |
| HHS_HOME                 | HomeSetup installation directory.                                                                 |
| HHS_LOAD_COMPLETIONS     | Whether to load bash completions at startup.                                                      |
| HHS_LOAD_SHELL_OPTIONS   | Whether to setr/unset shell options at startup.                                                   |
| HHS_LOG_DIR              | Directory containing all HomeSetup function logs.                                                 |
| HHS_LOG_FILE             | File containing all HomeSetup load logs.                                                          |
| HHS_MY_OS                | Your OS name.                                                                                     |
| HHS_MY_OS_PACKMAN        | Your OS package manager application.                                                              |
| HHS_MY_OS_RELEASE        | Your OR release name.                                                                             |
| HHS_MY_SHELL             | Your login shell base name.                                                                       |
| HHS_NO_AUTO_UPDATE       | Whether HomeSetuop auto-update is enabled or not.                                                 |
| HHS_PATHS_FILE           | This file holds the additional PATH's to be added to your shell and used by __hhs_paths function. |
| HHS_PREFIX_FILE          | This is the HomeSetup installation prefix. Useful for multi-user installation.                    |
| HHS_PUNCH_FILE           | This file holds the saved punches issued by __hhs_punch function.                                 |
| HHS_RESTORE_LAST_DIR     | Whether to restore last user directory at startup or not.                                         |
| HHS_SAVED_DIRS_FILE      | This file holds the saved directories issued by __hhs_save_dir function.                          |
| HHS_SETMAN_CONFIG_FILE   | File that holds Setman configurations.                                                            |
| HHS_SETMAN_DB_FILE       | File containing all Setman settings.                                                              |
| HHS_SETUP_FILE           | File that holds HomeSetup initialization settings.                                                |
| HHS_SET_LOCALES          | Whether to set current locale or not.                                                             |
| HHS_SHOPTS_FILE          | File containing all shell options.                                                                |
| HHS_STARSHIP_PRESETS_DIR | Directory containing all HomeSet-Starship presets.                                                |
| HHS_STREAMLIT_UI_PORT    | Port used by the HomeSetup Streamlit UI. Defaults to 18501.                                      |
| HHS_USE_STARSHIP         | Whether to use Starship prompt or not.                                                            |
| HHS_VAULT_FILE           | This file holds the user vault, used to store secure information.                                 |
| HHS_VAULT_USER           | This is the user that hhs vault plugin will use to store your vault data.                         |
| HHS_VERSION              | Currently installed HomeSetup version.                                                            |

## Aliases

HomeSetup defines some [aliases](../USAGE.md#aliases) that can be used to ease common tasks and commands. We provide many functions tha are
also aliased, but those can be customised using the installed **~/.aliasdef** file. You can customize most of HomeSetup
aliases by editing this file.

When you first install HomeSetup, the file will be automatically generated for you. Further updates may require this
file to be updated. We always keep a backup of this file, so, you can preserve your customizations, but this process has
to be manual. The original content is defined on the original [aliasdef](../../dotfiles/aliasdef) file.

### Alias Definitions

Here is where you feel yourself home. You can override our default aliases by changing your installed **~/.aliasdef** file.
When you first install HomeSetup this file will be created automatically for you, so you just need to customise it the
what you desire.

If you want to add more aliases, you can edit the file **~/.aliases**. HomeSetup will always load this file after the defaults, so whatever you write in this file, will prevail over the default.

**Notice that** Sometimes we need to update this file when we add/change some functions. We will always keep a backup of this file prior to
changing it, so you can always get what you have inside it and move to the new file.

### Categories

We group our aliases using the following categories:

- [Navigational](../USAGE.md#navigational)
- [General](../USAGE.md#general)
- [HomeSetup](../USAGE.md#homesetup)
- [External tools](../USAGE.md#external-tools)
- [OS Specific aliases](../USAGE.md#os-specific-aliases)
- [Handy Terminal Shortcuts](../USAGE.md#handy-terminal-shortcuts)
- [Python aliases](../USAGE.md#python-aliases)
- [Perl aliases](../USAGE.md#perl-aliases)
- [Git aliases](../USAGE.md#git-aliases)
- [Gradle aliases](../USAGE.md#gradle-aliases)
- [Docker aliases](../USAGE.md#docker-aliases)

## Functions

HomeSetup defines a bunch of [functions](../USAGE.md#functions) to help with the daily tasks such as "punch the clock",
calculations with time, search and cd into directories, save most used directories, aliases and commands, git stuff and more.
They can also be aliased using the **~/.aliasdef** file. We also define some default values for them (that you can also change later).

You can override or add additional variables by adding entries to your installed **~/.functions** file. When you first
install HomeSetup this file will be created automatically for you, so you just need to edit it.

**All HomeSetup functions are prefixed with `__hhs_`**

Functions are grouped into two categories:

- [Standard tools](../USAGE.md#standard-tools)
- [Development tools](../USAGE.md#development-tools)

Checkout the full handbook of [functions here](pages/functions.md).

## Applications

In addition to aliases and functions, HomeSetup also puts available some applications with different purposes, such as
IP information verification, fetch REST services, and more:

- [Bash applications](../USAGE.md#applications)

Checkout the complete handbook of [applications here](pages/applications.md).

## Templates

Currently HomeSetup offers a handful of templates, that helps you code or configure your git like we do. The following
are provided with the latest version:

- [Bash templates](../../templates/bash)
  - [app.bash](../../templates/bash/app.bash) : Create bash applications using our style.
- [Git templates](../../templates/git)
  - [commits](../../templates/git/commits) : HomeSetup commit messages format.
  - [gitconfig](../../templates/git/gitconfig) : .gitconfig file template.
  - [gitignore](../../templates/git/gitignore) : .gitignore file template.
  - [commit-msg](../../templates/git/hooks/commit-msg) : Git hook to make sure your commit message is following our format.
  - [prepare-commit-msg](../../templates/git/hooks/prepare-commit-msg) : Make sure no one commits on master.
- [Text templates](../../templates/txt)
  - [help.txt](../../templates/txt/help.txt) : Template used to create HomeSetup help messages.
  - [man.txt](../../templates/txt/man.txt) : Template used to create bash man pages.

**Do you have a nicer template ? Send it to us !**
