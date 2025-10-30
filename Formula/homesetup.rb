class Homesetup < Formula
  desc "HomeSetup - The ultimate Terminal experience"
  homepage "https://github.com/HS-Teams/homebrew-homesetup"
  url "https://github.com/HS-Teams/homebrew-homesetup.git",
      tag: "v1.8.28"
  license "MIT"

  depends_on xcode: ["12.0", :build]
  depends_on :macos

  depends_on "bash"
  depends_on "git"
  depends_on "rsync"
  depends_on "vim"
  depends_on "make"
  depends_on "gcc"
  depends_on "tree"
  depends_on "pcre2"
  depends_on "gpg"
  depends_on "base64"
  depends_on "ruby"
  depends_on "gawk"
  depends_on "python@3.11"
  depends_on "jq"
  depends_on "hunspell"
  depends_on "ffmpeg"
  depends_on "portaudio"

  uses_from_macos "ruby"
  uses_from_macos "curl"
  uses_from_macos "perl"
  uses_from_macos "libmagic"
  uses_from_macos "sqlite3"

  def python3
    "python3.11"
  end

  def install
    py3ver = Language::Python.major_minor_version python3
    ENV["PYTHONPATH"] = site_packages = prefix/Language::Python.site_packages(python3)
    ENV["PYTHON"] = python3
    prefix.install Dir["*"]
    prefix.install Dir[".*"].reject { |f| [".", ".."].include?(File.basename(f)) }
  end

  def caveats
    <<~EOS
      Welcome to HomeSetup - The ultimate Terminal experience !"

      To enable HomeSetup for your user, type:
        $ #{prefix}/install.bash -r -b -p #{prefix}
      To uninstall, type:
        $ #{prefix}/uninstall.bash
    EOS
  end

  test do
    output = shell_output("#{prefix}/bin/apps/bash/hhs-app/hhs.bash --version")
    assert_match "hhs v1.1.0 built on HomeSetup v1.8.28", output
  end
end
