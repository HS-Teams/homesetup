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

## Starship

### "help"

#### **Purpose**

HomeSetup starship integration setup.

#### **Returns**

**0** if the command was successfully executed; **non-zero** otherwise.

#### **Parameters**

- $1 _Optional_ : The starship command to be executed.

#### **Examples**

`__hhs starship help`

**Output**

```bash
usage: __hhs starship [command]

 ____  _                 _     _
/ ___|| |_ __ _ _ __ ___| |__ (_)_ __
\___ \| __/ _` | '__/ __| '_ \| | '_ \
 ___) | || (_| | |  \__ \ | | | | |_) |
|____/ \__\__,_|_|  |___/_| |_|_| .__/
                                |_|

  HomeSetup starship integration setup.
  Visit the Starship website at: https://starship.rs/

    commands:
      edit                  : Edit your starship configuration file (default command).
      restore               : Restore HomeSetup defaults.
      preset <preset_name>  : Configure your starship to a preset.

    presets:
      no-runtime-versions   : This preset hides the version of language runtimes. If you work in containers or
                              virtualized environments, this one is for you!
      bracketed-segments    : This preset changes the format of all the built-in modules to show their segment in
                              brackets instead of using the default Starship wording ('via', 'on', etc.).
      plain-text-symbols    : This preset changes the symbols for each module into plain text. Great if you don't have
                              access to Unicode.
      no-empty-icons        : This preset does not show icons if the toolset is not found.
      tokyo-night           : This preset is inspired by tokyo-night-vscode-theme.
      no-nerd-font          : This preset changes the symbols for several modules so that no Nerd Font symbols are used
                              anywhere in the prompt.
      pastel-powerline      : This preset is inspired by M365Princess (opens new window). It also shows how path
                              substitution works in starship.
      pure-preset           : This preset emulates the look and behavior of Pure.
      nerd-font-symbols     : This preset changes the symbols for each module to use Nerd Font symbols.

    note:
      - If no command is passed, the default editor will open the starship configuration file.
```

------

### "edit"

#### **Purpose**

Edit your starship configuration file.

#### **Returns**

**0** if the command was successfully executed; **non-zero** otherwise.

#### **Parameters**

N/A

#### **Examples**

`__hhs starship` or `__hhs starship execute edit`

**Output**

N/A

------

### "restore"

#### **Purpose**

Restore the default HomeSetup starship configuration file.

#### **Returns**

**0** if the command was successfully executed; **non-zero** otherwise.

#### **Parameters**

N/A

#### **Examples**

`__hhs starship execute restore`

**Output**

```bash
Restoring HomeSetup starship configuration...
Your starship prompt changed to HomeSetup defaults!
```

------

### "preset"

#### **Purpose**

Change you starship configuration to a preset.

#### **Returns**

**0** if the command was successfully executed; **non-zero** otherwise.

#### **Parameters**

- $1 _Optional_ : If set, specifies the preset to use.

#### **Examples**

`__hhs starship execute preset 'no-nerd-font'`

**Output**

```bash
Setting starship preset "no-nerd-font"...
Your starship prompt changed to preset: no-nerd-font !
```
