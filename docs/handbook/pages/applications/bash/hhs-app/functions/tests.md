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

## Tests

### "tests"

```bash
usage: __hhs tests
```

#### **Purpose**

Run all HomeSetup automated tests.

#### **Returns**

**0** if all tests ran successfully; **non-zero** otherwise.

#### **Examples**

`__hhs tests`

**Output**

```bash
[17:44:53] Running HomeSetup bats tests

  |-Bats : vBats 1.10.0
  |-Bash : vGNU bash, version 3.2.57(1)-release (x86_64-apple-darwin23)
  |-User : runner

[hhs-aliases.bats] Running tests 1 to 4

 √ PASS 1 when-invoking-with-help-option-then-should-print-usage-message
 √ PASS 2 when-adding-non-existent-valid-alias-then-should-add-it
 √ PASS 3 when-removing-an-invalid-alias-then-should-raise-an-error
 √ PASS 4 when-removing-an-existing-alias-then-should-remove-it
...
...
```

------

### "color-tests"

```bash
usage: __hhs color-tests
```

#### **Purpose**

Run all terminal color palette tests.

#### **Returns**

**0** if all color tests ran successfully; **non-zero** otherwise.

#### **Examples**

__hhs color-tests

**Output**

```bash
[17:53:59] Running HomeSetup color palette test

  |-Terminal : xterm-256color
  |-Terminal Program : Apple_Terminal

  BLACK     RED   GREEN  ORANGE    BLUE  PURPLE    CYAN    GRAY   WHITE  YELLOW  VIOLET

--- 16 Colors Low

C16-30 C16-31 C16-32 C16-33 C16-34 C16-35 C16-36 C16-37

--- 16 Colors High

C16-90 C16-91 C16-92 C16-93 C16-94 C16-95 C16-96 C16-97
...
...
```
