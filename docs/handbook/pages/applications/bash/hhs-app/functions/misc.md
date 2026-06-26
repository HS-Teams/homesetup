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
      - [Built-Ins](built-ins.md)
      - [Misc](misc.md)
      - [Tests](tests.md)
      - [Web](web.md)
    - [Plugins](../../hhs-app.md#plug-ins)
      - [Ask](../plugins/ask.md)
      - [Firebase](../plugins/firebase.md)
      - [HSPM](../plugins/hspm.md)
      - [Services](../plugins/services.md)
      - [Settings](../plugins/settings.md)
      - [Setup](../plugins/setup.md)
      - [Starship](../plugins/starship.md)
      - [Taius](../plugins/taius.md)
      - [UI](../plugins/ui.md)
      - [Updater](../plugins/updater.md)

<!-- tocstop -->

## Miscellaneous

### "host-name"

```bash
usage: hhs host-name [new_hostname]
```

#### **Purpose**

Retrieve/Get/Set the current hostname.

#### **Returns**

**0** if the hostname was successfully changed/retrieved; **non-zero** otherwise.

#### **Parameters**

- $1 _Optional_ : The new hostname. If not provided, current hostname is retrieved.

#### **Examples**

`hhs host-name my.domain.hostname`

**Output**

N/A

`__hhs host-name`

**Output**

```bash
my.domain.hostname
```

------

### "shopts"

```bash
usage: __hhs shopts
```

#### **Purpose**

Set/Unset Shell Options.

#### **Returns**

**0** if the command was successful; **non-zero** otherwise.

#### **Examples**

`__hhs shopts`

**Output**

```bash
Terminal Options
Please check the desired terminal options:

   1      cdable_vars
   2       cdspell
   3       checkhash
   4       checkwinsize
   5       cmdhist
   6       compat31
   7       dotglob
   8       execfail
   9       expand_aliases
  10       extdebug

[Enter] Accept  [↑↓] Navigate  [Space] Mark  [I] Invert  [Esc] Quit  [1..34] Goto:
```
