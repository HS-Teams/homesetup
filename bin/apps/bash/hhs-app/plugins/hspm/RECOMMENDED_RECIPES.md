# Recommended HSPM Recipes

Use these recipes when installation needs more than a direct package-manager
command: an installer, prerequisite tooling, shell configuration, an external
repository, or service setup.  Plain package-manager wrappers are intentionally
omitted.

## Darwin

| Recipe | Purpose |
| --- | --- |
| `nvm` | Installs Node Version Manager through its upstream installer. |
| `node` | Installs Node.js through NVM. Requires the `nvm` recipe. |
| `qt` | Installs Qt and adds its tools to the HHS path configuration. |
| `rvm` | Imports RVM signing keys and installs RVM with Ruby. |
| `vue` | Installs the Vue CLI globally through NVM/npm. Requires the `nvm` recipe. |
| `xcode-select` | Installs Apple's Command Line Tools through the macOS system installer. |

## Linux

| Recipe | Purpose |
| --- | --- |
| `docker` | Configures Docker's official APT repository and installs Docker Engine. |
| `jenkins` | Configures Jenkins's official APT repository and installs the service and JRE. |
| `ollama` | Uses Ollama's upstream installer and manages its system service on removal. |
| `temurin@17` | Configures the Adoptium APT repository and installs Eclipse Temurin JDK 17. |
| `temurin@21` | Configures the Adoptium APT repository and installs Eclipse Temurin JDK 21. |

The `default` recipes and simple Homebrew wrappers, such as `jenv`, Darwin
`ollama`, and `colima`, are not recommended recipes.
