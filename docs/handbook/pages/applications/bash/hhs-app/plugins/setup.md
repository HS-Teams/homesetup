<img src="https://iili.io/HvtxC1S.png" width="64" height="64" align="right" />

# HomeSetup Developer Handbook
>
> Applications handbook

## Table of contents

<!-- toc -->

- [Bash Applications](../../../../applications.md)
  - [Check-IP](../../check-ip.md#check-ip)
  - [Fetch](../../fetch.md#fetch)
  - [HHS-App](../../hhs-app.md#homesetup-application)
    - [Functions](../../hhs-app.md#functions)
      - [Built-Ins](../functions/built-ins.md)
      - [Misc](../functions/misc.md)
      - [Tests](../functions/tests.md)
      - [Web](../functions/web.md)
    - [Plugins](../../hhs-app.md#plug-ins)
      - [Ask](ask.md)
      - [Firebase](firebase.md)
      - [HSPM](hspm.md)
      - [Services](services.md)
      - [Settings](settings.md)
      - [Setup](setup.md)
      - [Starship](starship.md)
      - [Taius](taius.md)
      - [UI](ui.md)
      - [Updater](updater.md)

<!-- tocstop -->

## Setup

### "help"

#### **Purpose**

HomeSetup initialization setup.

#### **Returns**

**0** if the command was successfully executed; **non-zero** otherwise.

#### **Parameters**

- $1 _Optional_ : If specified, restore HomeSetup defaults.

#### **Examples**

`__hhs setup help`

**Output**

```bash
usage: __hhs setup [-restore | -apply <0|1>...] [options]

 ____       _
/ ___|  ___| |_ _   _ _ __
\___ \ / _ \ __| | | | '_ \
 ___) |  __/ |_| |_| | |_) |
|____/ \___|\__|\__,_| .__/
                     |_|

  HomeSetup initialization setup.

    options:
      -apply [<0|1>, ...] : Apply setup values in file order; omitted values remain unchanged.
      -restore            : Restore the HomeSetup defaults.
```

`__hhs setup`

```bash
HomeSetup Initialization Settings
Please check the desired startup settings:

  1      hhs_set_locales
  2       hhs_export_settings
  3       hhs_restore_last_dir
  4       hhs_use_starship
  5       hhs_load_shell_options
  6       homebrew_no_auto_update
  7       hhs_no_auto_update
  8       hhs_load_completions

[Enter] Accept  [↑↓] Navigate  [Space] Mark  [I] Invert  [Esc] Quit  [1..8] Goto:
```
