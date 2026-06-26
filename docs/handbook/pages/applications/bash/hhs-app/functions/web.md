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

### "docsify"

```bash
usage: __hhs docsify
```

#### **Purpose**

Open a docsify version of the HomeSetup README.

#### **Returns**

**0** if the command was successfully executed; **non-zero** otherwise.

#### **Examples**

`__hhs docsify`

**Output**

```bash
Opening HomeSetup docsify README from: https://docsify-this.net/?basePath=https://raw.githubusercontent.com/yorevs/homesetup/master&sidebar=true
```

------

## Web

### "board"

```bash
usage: __hhs board
```

#### **Purpose**

Open the HomeSetup GitHub project board.

#### **Returns**

**0** if the command was successfully executed; **non-zero** otherwise.

#### **Examples**

`__hhs board`

**Output**

```bash
Opening HomeSetup board from: https://github.com/yorevs/homesetup/projects/1
```
