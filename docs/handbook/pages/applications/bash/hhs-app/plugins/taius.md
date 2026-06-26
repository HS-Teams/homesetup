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

## Taius

### "help"

#### **Purpose**

Display the HomeSetup Taius AskAI integration help.

#### **Returns**

**0** if the command was successfully executed; **non-zero** otherwise.

#### **Parameters**

N/A

#### **Examples**

`__hhs taius help`

**Output**

```bash
usage: __hhs taius <question> [options]

  HomeSetup AskAI integration.

    options:
      -h | --help              : Display this help message.
      -v | --version           : Display current plugin version.

    arguments:
      question                 : The question to ask Taius about HomeSetup.

    examples:
      Ask for usage guidance:
        => __hhs taius "How do I update HomeSetup?"

  Notes:
    - Requires the HomeSetup Python virtual environment and AskAI installation.
```

------

### "question"

#### **Purpose**

Ask Taius a question about HomeSetup through the AskAI RAG integration.

#### **Returns**

**0** if AskAI is executed; **non-zero** otherwise.

#### **Parameters**

- $1..$N _Required_ : Question text.

#### **Examples**

`__hhs taius execute "How do I launch the UI?"`

**Output**

N/A
