<img src="https://iili.io/HvtxC1S.png" width="64" height="64" align="right" />

# HomeSetup

> The ultimate Terminal experience

[![Terminal](https://badgen.net/badge/icon/terminal?icon=terminal&label)](https://github.com/yorevs/homesetup)
[![License](https://badgen.net/badge/license/MIT/gray)](LICENSE.md)
[![Release](https://badgen.net/badge/release/v1.8.28/gray)](docs/CHANGELOG.md#unreleased)
[![Gitter](https://badgen.net/badge/icon/gitter?icon=gitter&label)](https://gitter.im/yorevs-homesetup/community?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)
[![Donate](https://badgen.net/badge/paypal/donate/yellow)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=J5CDEFLF6M3H4)
[![Build](https://github.com/yorevs/homesetup/actions/workflows/build-and-test.yml/badge.svg)](https://github.com/yorevs/homesetup/actions/workflows/build-and-test.yml)

<img src="https://iili.io/JinJpTu.png" width="100%" height="100%" />

---

Are you passionate about the terminal and CLI? If so, you've come to the right place, especially if you're a command line enthusiast. Terminal dotfiles are well-known for improving productivity and streamlining everyday tasks. While there are numerous frameworks available to assist with this, many of them come with a steep learning curve and are primarily targeted towards individuals with strong programming skills. Additionally, these frameworks often employ esoteric syntax, requiring an additional effort to fully utilize their features.

Wouldn't it be fantastic if we could effortlessly upload and download our configurations, dotfiles, packages, and customizations to the cloud? This is where HomeSetup comes in. It provides a solution that simplifies the process, allowing you to leverage the power of the cloud seamlessly.

With **HomeSetup**, you can enhance your terminal experience, boost productivity, and customize your shell to suit your preferences all without the complexities often associated with other frameworks. HomeSetup was specifically developed to enhance the command line experience for users. Its primary objective is to provide useful and user-friendly features that expedite daily tasks, such as time tracking, string and file searching, directory navigation, and seamless integration with popular tools like Git, Gradle, Docker, and more.

> **THIS IS NOT JUST A DOTFILES FRAMEWORK**

<img src="https://iili.io/dbXcC6g.gif">

- See the [Showcase](docs/SHOWCASE.md) page to see some HomeSetup demos.
- For the full documentation, access the [HomeSetup usage manual](docs/USAGE.md).

**🔥 HOT** AI is here ! **HomeSetup** has integrated AI with RAG capabilities.

<img src="https://iili.io/dy2Ga6u.gif">

## Key Features

- Automated setup for commonly used configurations, ensuring a hassle-free initial setup.
- A wide range of functions to simplify terminal configuration and streamline daily tasks.
- A visually appealing prompt with a monospaced font that supports [Font-Awesome](https://fontawesome.com/) icons (requires a [Nerd font](https://www.nerdfonts.com/)).
- Highly customizable **aliases**, **paths**, **environment variables** and more.
- A **universal package manager** helper that facilitates the installation of applications using recipes, catering to various package managers _beyond normal package managers_.
- Ability to upload custom dotfiles on [Firebase](https://firebase.google.com/) and easily download them across different environments.
- Offers a short learning curve and provides a comprehensive [User's Handbook](docs/handbook/handbook.md) for reference.
- All code is licensed under The [MIT License](https://opensource.org/license/mit/), granting users the freedom to modify and use it as desired.
- Tab completion with Shift key (using menu-complete) to cycle through options conveniently.
- Intuitive visual input methods for selecting, choosing, and form data within scripts.
- Utilizes a Python virtual environment to avoid interfering with your installation.
- Supports Linux and macOS, expanding its compatibility to a wider range of operating systems.
- Can be tried on a [Docker](https://hub.docker.com/repository/docker/yorevs/hhs-fedora/general) container beforehand, ensuring a **risk-free trial**.

## Integrations

HomeSetup offers seamless integration with a variety of tools to enhance productivity and customization:

- **[Starship](https://starship.rs/):** Elevate your terminal experience with this highly customizable prompt.
- **[ColorLS](https://github.com/athityakumar/colorls):** Add colorized and feature-rich directory listings for improved readability.
- **[FZF](https://www.redhat.com/sysadmin/fzf-linux-fuzzy-finder):** Enjoy the power of fuzzy search for rapid navigation and command-line operations.
- **[Bat](https://github.com/sharkdp/bat):** A cat(1) clone with syntax highlighting and Git integration.
- **[FD](https://github.com/sharkdp/fd):** A simple, fast and user-friendly alternative to 'find'.
- **[GTrash](https://github.com/umlx5h/gtrash):** Manage file deletion effortlessly with this trash-cli alternative.
- **[NeoVim](https://neovim.io/):** A hyper-extensible, modern rewrite of Vim, offering improved performance and enhanced plugins for developers and power users.
- **[Sdiff](https://man7.org/linux/man-pages/man1/sdiff.1.html) + [Colordiff](https://www.colordiff.org/):** Compare and colorize file differences directly in your terminal, providing an intuitive way to track changes between files.
- **[Ble-sh](https://github.com/akinomyoga/ble.sh):** Bash Line Editor―a line editor written in pure Bash with syntax highlighting, auto suggestions, vim modes, etc. for Bash interactive sessions.
- **[Atuin](https://github.com/atuinsh/atuin):** Magical shell history.
- **[Delta](https://github.com/dandavison/delta):** A syntax-highlighting pager for git, diff, grep, and blame output.
- **[Zoxide](https://github.com/ajeetdsouza/zoxide):** A smarter cd command. Supports all major shells.
- **[TLDR](https://github.com/tldr-pages/tldr):** Collaborative cheatsheets for console commands.

## Catalina moved from bash to zsh

Starting with the _Catalina_ version of macOS, the default shell has been switched to **Zsh**. Nonetheless, you retain the flexibility to change the default shell back to bash. To accomplish this, you can utilize the following command:

```bash
sudo chsh -s /bin/bash
```

If Apple removes **Bash** from future _macOS_ releases, you can rely on Homebrew's version. The path to the shell may differ. For example:

```bash
brew install bash
sudo chsh -s /usr/local/bin/bash
```

If Homebrew is used, determine the correct Bash path by running:

```bash
brew --prefix bash
```

For terminals like **iTerm2**, you can configure the interpreter path in your _profile settings_. Set the login shell to the desired **Bash** path (e.g., the one provided by Homebrew). After updating the interpreter path, restart the terminal to apply changes.

## Installation

### Operating Systems

- Darwin (macOS)
  - High Sierra and higher
- Linux
  - Ubuntu 16 and higher
  - CentOS 7 and higher
  - Fedora 31 and higher
  - Alpine (jenkins-agent)

> While it's possible to install HomeSetup on **other Linux** distributions and it might work, it's important to note that **there are no guarantees** of its _full functionality or compatibility_.

### Supported Shells

- **Bash**: Everything from 3.2.57(1) and higher.
- **Zsh**: Zsh is planned but not supported yet.

### Terminal configuration

To visualize the Font-Awesome unicode icons, you'll need a compatible nerd font. We recommend using the font we provide with the installation:

[Droid font](assets/fonts/Droid-Sans-Mono-for-Powerline-Nerd-Font-Complete.otf).

**Linux users**: Some terminals already support icons, but if not, you can manually install the font.

**Mac users**: We suggest using one of the terminal profiles listed below to ensure optimal icon display.

You can execute the following commands to install it even before installing HomeSetup:

```bash
curl -L https://github.com/yorevs/homesetup/releases/download/v1.8.14/Droid-Sans-Mono-for-Powerline-Nerd-Font-Complete.zip -o ${TEMP}/Droid-Sans-Mono.zip && unzip -o ${TEMP}/Droid-Sans-Mono.zip -d ${HOME}/.fonts/DroidSan-MonoforPowerlineNerdFontComplete && fc-cache -f
```

**Mac users**: There is one additional step:

```bash
cp -f ${HOME}/.fonts/DroidSan-MonoforPowerlineNerdFontComplete/*.otf ${HOME}/Library/Fonts  && fc-cache -f
```

After HomeSetup installation, the Nerd font will be available at: `${HHS_HOME}/assets/fonts`

#### Terminal App (Darwin)

[HomeSetup Terminal](assets/term-configs/HomeSetup.terminal)

#### iTerm2 App (Darwin)

[HomeSetup iTerm2](assets/term-configs/HomeSetup-iTerm2.json)

#### WezTerm (Linux/Darwin)

[HomeSetup WezTerm](assets/term-configs/HomeSetup-WezTerm.lua)


When your terminal is set, then you should see something like this:

[Welcome](https://iili.io/JuxHulR.png)

### Try-it first

<img src="https://iili.io/dydwcjR.gif">

Running HomeSetup in a Docker container offers a convenient and isolated environment for testing purposes, ensuring
that your machine remains unaffected during the evaluation process. Use one of the following docker images:

#### amd64

```bash
docker run --rm -it yorevs/hhs-centos:amd64-latest
docker run --rm -it yorevs/hhs-ubuntu:amd64-latest
docker run --rm -it yorevs/hhs-fedora:amd64-latest
docker run --rm -it yorevs/hhs-alpine:amd64-latest
```

#### arm64

```bash
docker run --rm -it yorevs/hhs-centos:arm64-latest
docker run --rm -it yorevs/hhs-ubuntu:arm64-latest
docker run --rm -it yorevs/hhs-fedora:arm64-latest
```

> Alpine is not available for **arm64** architecture.

### Remote installation

This is the recommended installation method. You can install HomeSetup directly from GitHub by executing one of the
following commands:

```bash
curl -o- https://raw.githubusercontent.com/yorevs/homesetup/master/install.bash | bash
```

or

```bash
wget -qO- https://raw.githubusercontent.com/yorevs/homesetup/master/install.bash | bash
```

### Local installation

Clone the HomeSetup repository:

```bash
git clone https://github.com/yorevs/homesetup.git ~/HomeSetup
```

And then install all dotfiles using the following command:

**To install all files at once**

```bash
cd ~/HomeSetup && ./install.bash
```

or

**To install one by one**

```bash
cd ~/HomeSetup && ./install.bash -i
```

Your existing dotfiles (such as .bashrc, .bash_profile, etc.) will be backed up with the **'.orig'** suffix and stored in the **~/.hhs/backup** folder. This ensures that your original dotfiles are safely preserved during the installation process.

Once the installation is completed successfully, you should see the following welcome message:

<img src="https://iili.io/24Lgi1s.jpg">

### Firebase setup

HomeSetup provides the capability to utilize your Firebase account for uploading and downloading your custom files (dotfiles file synchronization) to your _Real-time Database_. To utilize this feature, you must first configure your Google Firebase account. Please check the [Firebase Setup](docs/FIREBASE_SETUP.md) document for instructions.

<img src="https://iili.io/dbXM29a.gif">

### Starship Setup

HomeSetup, now, bundles starship prompt. It's has an out-of-the-box configuration. For a full list of features and configurations please checkout the [Starship](https://starship.rs/) website. Please check the [Starship Plugin](docs/handbook/pages/applications/bash/hhs-app/plugins/starship.md) document for mode details about HomeSetup / Starship integration.

<img src="https://iili.io/24QCWuf.gif">

### Other integrations

#### ColorLS

HomeSetup, now, integrates the new modern **ls** command [ColorLS](https://github.com/athityakumar/colorls). HomeSetup will not install it, but once you have installed it, it will be used instead of the built-in **ls**.

Please check the [ColorLS Setup](docs/COLOR_LS_SETUP.md) document for more instructions on how to set up ColorLS.

#### FZF

HomeSetup, now, integrates the modern [fuzzy-finder](https://github.com/junegunn/fzf). HomeSetup
will not install it, but once you have installed it, it will be used. We have set the common configurations like the key bindings (Ctrl+T \[find\] and Ctrl+R \[history\]) and auto-completions. Is also integrates with [bat](https://github.com/sharkdp/bat) (extended 'cat') and [fd](https://github.com/sharkdp/fd) (extended 'find').

Please check the [FZF Docs](https://github.com/junegunn/fzf#examples) for more usage examples.

#### Ble-sh

HomeSetup integrates the advanced Bash line editor [ble.sh](https://github.com/akinomyoga/ble.sh). While HomeSetup will not install ble.sh automatically, it supports its usage once you have it installed. Common configurations such as syntax highlighting, auto-suggestions, and Vim modes are set up for enhanced Bash interactive sessions.

Ble.sh extends your shell with powerful features for better command-line editing. To benefit from these, install ble.sh following its instructions and source its initialization script in your Bash profile:

Refer to the [ble.sh](https://github.com/akinomyoga/ble.sh) documentation for detailed configuration options and additional features.

#### Atuin

HomeSetup integrates [Atuin](https://github.com/atuinsh/atuin) for magical shell history sessions. While HomeSetup does not install Atuin automatically, once installed, it will be utilized seamlessly within your shell environment.

We assume a standard Atuin configuration for optimal history management, which includes session tracking, search capabilities, and synchronization across devices. HomeSetup's configuration files are set up to work with Atuin out of the box, capturing shell commands and history efficiently.

Please refer to [Atuin's](https://github.com/atuinsh/atuin) documentation for detailed setup instructions, advanced configuration options, and usage examples.

#### Delta

HomeSetup integrates [Delta](https://github.com/dandavison/delta), a syntax-highlighting pager for git, diff, grep, and blame outputs. After installing Delta, HomeSetup configures your git settings to use Delta as the default pager and adjusts related environment variables to enhance the output of diff, grep, and blame commands with syntax highlighting.

To enable it for your git installation, add the following to your `~/.gitconfig`:

```ini
[core]
  pager = delta

[diff]
  tool = delta

[interactive]
  diffFilter = delta --color-only

[merge]
  conflictstyle = zdiff3

[delta]
  navigate = true
  side-by-side = true
```

This configuration sets Delta as the default pager and enables side-by-side diffs, line numbers, and other decorations. For additional configuration options and usage examples, refer to the [Delta Docs](https://github.com/dandavison/delta#usage).

#### Zoxide

HomeSetup integrates the powerful [Zoxide](https://github.com/ajeetdsouza/zoxide) to provide a smarter `cd` command across all major shells. While HomeSetup does not install Zoxide, it configures the environment for seamless use once Zoxide is installed.

The integration sets up necessary environment variables and aliases for rapid directory navigation. After installing Zoxide, simply restart your shell or source your profile to enable the new configurations.

HomeSetup integrates it's built-in **\_\_hhs_change_dir** with the zoxide `z` command. Once installed, `cd` command automatically leverages `z`. The `z` command will also work.

Please refer to the [Zoxide Docs](https://github.com/ajeetdsouza/zoxide) for more information and advanced usage examples.

#### TLDR

HomeSetup integrates with [TLDR](https://github.com/tldr-pages/tldr), providing community-driven cheatsheets for console commands. While HomeSetup does not install TLDR, once it is installed, the system supports its use. Common configurations such as setting up aliases, automatic updates, and managing cache paths can be customized in your shell configuration.

HomeSetup integrates it's built-in **\_\_hhs_where_am_i** (? command) with the `tldr` command. Once installed, `?` command automatically leverages `tldr`. The `tldr` command will also work.

Examples:

```bash
? grep
? fzf
```

Refer to the [TLDR Documentation](https://github.com/tldr-pages/tldr#readme) for more details on usage and customization.

#### AskAI

HomeSetup now integrates with the AskAI application. You can ask questions about the terminal or any aspect of the HomeSetup project. You can also request assistance in building commands and using HomeSetup easily. You just need to ask!

It's required that you own accounts on GoogleSearch API (for searching the web), DeepL (for translations), and OpenAI. For that is required that you provide the following Api Keys:

1. GOOGLE_API_KEY
2. OPENAI_API_KEY
3. DEEPL_API_KEY

For more information about getting the ApiKeys, please check: [AskAI](https://github.com/yorevs/askai).

## Uninstallation

If you choose to uninstall HomeSetup and restore your old dotfiles, you can do so by issuing the following command in a shell:

`# HomeSetup $ ./uninstall.bash`

The uninstaller will remove all files and folders associated with HomeSetup. The only folder that will remain is the **$HHS_DIR** (~/.hhs typically), whereas your configurations were stored. After a successful uninstallation, it is safe to delete this folder if you no longer need it, **HOWEVER ALL CUSTOM DOTFILES WILL BE GONE**.

## Support

> Your support and contributions are greatly appreciated in helping us improve and enhance HomeSetup. Together, we can make it even better!

You can support HomeSetup by [donating](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=J5CDEFLF6M3H4) or contributing code. Feel free to contact me for further details. When making code contributions, please make sure to review our [guidelines](docs/CONTRIBUTING.md) and adhere to our [code of conduct](docs/CODE_OF_CONDUCT.md).

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/yorevs)

You can also sponsor it by using our [GitHub Sponsors](https://github.com/sponsors/yorevs) page.

This project is already supported by:

<a href="https://www.jetbrains.com/community/opensource/?utm_campaign=opensource&utm_content=approved&utm_medium=email&utm_source=newsletter&utm_term=jblogo#support">
  <img src="https://resources.jetbrains.com/storage/products/company/brand/logos/jb_beam.png" width="120" height="120">
</a>

Thank you <3 !!

## Final notes

HomeSetup is designed to automatically fetch updates **every 7 days** from the time of installation. However, if you want to manually ensure that your HomeSetup is up to date, you can run one of the following command in your terminal:

`hhs updater execute update`

or just

`hhu`

This will install the latest version of HomeSetup, keeping your setup current and incorporating any new features and improvements. Keeping HomeSetup updated is essential to benefit from the latest enhancements and bug fixes. If you have any questions or encounter any issues during the update process, feel free to reach out for assistance.

## Known Issues

- [In-Progress] We are aware that there is a problems when using python@3.12 and we are already working on a fix.

## Contacts

- Documentation: [API](docs/handbook/handbook.md)
- License: [MIT](LICENSE.md)
- Issue tracker: [ISSUES](https://github.com/yorevs/homesetup/issues)
- Official chat: [GITTER](https://gitter.im/yorevs-homesetup/community)
- Maintainer: [REDDIT](https://www.reddit.com/user/yorevs)
- Mailto: [HomeSetup](mailto:taius.hhs@gmail.com)

Enjoy!
