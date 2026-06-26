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

## Services

### "help"

#### **Purpose**

Display the service management plug-in help.

#### **Returns**

**0** if the command was successfully executed; **non-zero** otherwise.

#### **Parameters**

N/A

#### **Examples**

`__hhs services help`

**Output**

```bash
usage: __hhs services <operation> [service_name] [options]

  HomeSetup services v1.0.1.

    options:
      -h | --help               : Display this help message.
      -v | --version            : Display current plugin version.

    arguments:
      operation                 : start | stop | restart | status.
      service_name              : Target service (required except when listing all statuses).

    examples:
      Check status for all services:
        => __hhs services status
      Restart a specific service:
        => __hhs services restart sshd

  Notes:
    - Commands adapt to the current OS service manager (brew, rc-service, systemctl).
```

------

### "status"

#### **Purpose**

List service statuses for the current operating system. The implementation uses `brew services` on macOS,
`rc-service` on Alpine, and `systemctl` on Debian, Fedora, and CentOS compatible systems. The HomeSetup UI service is
also added to the list based on the Streamlit UI port status.

#### **Returns**

**0** if statuses are listed; **non-zero** otherwise.

#### **Parameters**

- $1 _Optional_ : Service name filter.

#### **Examples**

`__hhs services execute status`

**Output**

```bash
Fetching services statuses...

  Service             Status
------------------------------
  1: atuin...........  Down
  2: homesetup-ui....  Up
```

------

### "start", "stop", and "restart"

#### **Purpose**

Manage one service using the service manager detected for the current operating system.

#### **Returns**

**0** if the service operation succeeds; **non-zero** otherwise.

#### **Parameters**

- $1 _Required_ : Operation, one of `start`, `stop`, or `restart`.
- $2 _Required_ : Service name.

#### **Examples**

`__hhs services execute restart sshd`

**Output**

```bash
Restart service "sshd"... OK
```
