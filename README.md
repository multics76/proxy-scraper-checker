# proxy-scraper-checker

[![CI](https://github.com/multics76/proxy-scraper-checker/actions/workflows/ci.yml/badge.svg)](https://github.com/multics76/proxy-scraper-checker/actions/workflows/ci.yml)

![Screenshot](screenshot.png)

HTTP, SOCKS4, SOCKS5 proxies scraper and checker.

- Asynchronous.
- Uses regex to find proxies of format `protocol://username:password@ip:port` on a web page or in a local file, allowing proxies to be extracted even from json without code changes.
- It is possible to specify the URL to which to send a request to check the proxy.
- Supports saving to plain text or json.
- Can sort proxies by speed.
- Supports determining the geolocation of the proxy exit node.
- Can determine if the proxy is anonymous.

You can get proxies obtained using this script in [multics76/proxy-list](https://github.com/multics76/proxy-list).

## Installation and usage

### Pre-compiled binary

This is the easiest way, but it is only available for x64 Windows, macOS and Linux. Just download the archive for your OS from <https://nightly.link/multics76/proxy-scraper-checker/workflows/ci/main?preview>, unzip it, edit `config.toml` and run the executable.

If Windows Defender detects an executable file as a virus, please read [this](https://github.com/Nuitka/Nuitka/issues/2495#issuecomment-1762836583).

### Running from source code

#### Desktop

- Install [Python](https://python.org/downloads). The minimum version required is 3.8. The recommended version is 3.11, because 3.12 may not install some libraries in the absence of a C compiler.
- Download and unpack [the archive with the program](https://github.com/multics76/proxy-scraper-checker/archive/refs/heads/main.zip).
- Edit `config.toml` to your preference.
- Run the script that installs dependencies and starts `proxy-scraper-checker`:
  - On Windows run `start.cmd`
  - On Unix-like operating systems run `start.sh`

#### Termux

To use `proxy-scraper-checker` in Termux, knowledge of the Unix command-line interface is required.

- Download Termux from [F-Droid](https://f-droid.org/en/packages/com.termux/). [Don't download it from Google Play](https://github.com/termux/termux-app#google-play-store-deprecated).
- Run the following command (it will automatically update Termux packages, install Python, and download and install `proxy-scraper-checker`):
  ```bash
  bash <(curl -fsSL 'https://raw.githubusercontent.com/multics76/proxy-scraper-checker/main/install-termux.sh')
  ```
- Edit `~/proxy-scraper-checker/config.toml` to your preference using a text editor (vim/nano).
- To run `proxy-scraper-checker` use the following command:
  ```bash
  cd ~/proxy-scraper-checker && sh start-termux.sh
  ```

## Something else?

All other info is available in `config.toml` file.

## License

[MIT](LICENSE)
