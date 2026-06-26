<img src="https://iili.io/HvtxC1S.png" width="64" height="64" align="right" />

# HomeSetup Developer Handbook
>
> Applications handbook

## Table of contents

<!-- toc -->

- [Bash Applications](../../applications.md)
  - [Check-IP](check-ip.md#check-ip)
  - [Fetch](fetch.md#fetch)
  - [HHS-App](hhs-app.md#homesetup-application)
    - [Functions](hhs-app.md#functions)
      - [Built-Ins](hhs-app/functions/built-ins.md)
      - [Misc](hhs-app/functions/misc.md)
      - [Tests](hhs-app/functions/tests.md)
      - [Web](hhs-app/functions/web.md)
    - [Plugins](hhs-app.md#plug-ins)
      - [Firebase](hhs-app/plugins/firebase.md)
      - [HSPM](hhs-app/plugins/hspm.md)
      - [Services](hhs-app/plugins/services.md)
      - [Settings](hhs-app/plugins/settings.md)
      - [Setup](hhs-app/plugins/setup.md)
      - [Starship](hhs-app/plugins/starship.md)
      - [Taius](hhs-app/plugins/taius.md)
      - [UI](hhs-app/plugins/ui.md)
      - [Updater](hhs-app/plugins/updater.md)

<!-- tocstop -->

## Check-IP

```bash
usage: check-ip.bash <ip_address> [options]
    Validate an IPv4 address and display class, scope, and optional details.

    options:
      -q | --quiet            : Validate only; skip scope/class details.
      -i | --info             : Fetch additional information from the web.
      -h | --help             : Display this help message.
      -v | --version          : Display current program version.
```

### **Purpose**

Validate and check information about a provided IP address.

### **Returns**

**0** if the IP is valid; **non-zero** otherwise.

### **Parameters**

- $1 _Required_ : The IP address.

### **Examples:**

`check-ip.bash 192.168.0.10`

**Output**

```bash
Valid IP: 192.168.0.10, Class: C, Scope: Private
```

`check-ip.bash -i 192.158.100.10`

**Output**

```bash
Valid IP: 192.158.100.10, Class: C, Scope: Public
{
    "status": "success",
    "country": "United States",
    "countryCode": "US",
    "region": "OR",
    "regionName": "Oregon",
    "city": "Beaverton",
    "zip": "97077",
    "lat": 45.4991,
    "lon": -122.823,
    "timezone": "America/Los_Angeles",
    "isp": "Tektronix",
    "org": "Tektronix, Inc",
    "as": "",
    "query": "192.158.100.10"
}
```
