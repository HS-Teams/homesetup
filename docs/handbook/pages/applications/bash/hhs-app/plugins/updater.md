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

## Updater

### "help"

#### **Purpose**

HomeSetup update manager.

#### **Returns**

**0** if the command was successfully executed; **non-zero** otherwise.

#### **Parameters**

N/A

#### **Examples**

`__hhs updater help`

**Output**

```bash
usage: updater updater [option] {check,update,stamp}

 _   _           _       _
| | | |_ __   __| | __ _| |_ ___ _ __
| | | | '_ \ / _` |/ _` | __/ _ \ '__|
| |_| | |_) | (_| | (_| | ||  __/ |
 \___/| .__/ \__,_|\__,_|\__\___|_|
      |_|

  HomeSetup update manager.

    arguments:
      check             : Fetch the last_update timestamp and check if HomeSetup needs to be updated.
      update            : Check for HomeSetup updates.
      stamp             : Stamp the next auto-update check for 7 days ahead.
```

------

### "check"

#### **Purpose**

Fetch the last_update timestamp and check if HomeSetup needs to be updated.

#### **Returns**

**0** if the command was successfully executed; **non-zero** otherwise.

#### **Parameters**

N/A

#### **Examples**

`__hhs updater execute check`

**Output**

N/A

------

### "check"

#### **Purpose**

Check for HomeSetup updates.

#### **Returns**

**0** if the command was successfully executed; **non-zero** otherwise.

#### **Parameters**

N/A

#### **Examples**

`__hhs updater execute update`

**Output**

```bash
Your version of HomeSetup is not up-to-date:
  => Repository: v1.6.19, Yours: v1.6.19

Would you like to update it now (y/[n])?
```

------

### "stamp"

#### **Purpose**

Stamp the next auto-update check for 7 days ahead.

#### **Returns**

**0** if the command was successfully executed; **non-zero** otherwise.

#### **Parameters**

N/A

#### **Examples**

`__hhs updater execute stamp`

**Output**

N/A
