# proxy-scraper-checker

[![CI](https://github.com/multics76/proxy-scraper-checker/actions/workflows/ci.yml/badge.svg)](https://github.com/mutlics76/proxy-scraper-checker/actions/workflows/ci.yml)

![Screenshot](screenshot.png)

HTTP, SOCKS4, SOCKS5 proxies scraper and checker.

- Asynchronous.
- Uses regex to search for proxies (ip:port format) on a web page, allowing proxies to be extracted even from json without making changes to the code.
- It is possible to specify the URL to which to send a request to check the proxy.
- Can sort proxies by speed.
- Supports determining the geolocation of the proxy exit node.
- Can determine if the proxy is anonymous.

You can get proxies obtained using this script in [monosans/proxy-list](https://github.com/multics76/proxy-list).

## Installation and usage

### Desktop

- Download and unpack [the archive with the program](https://github.com/multics76/proxy-scraper-checker/archive/refs/heads/main.zip).
- Edit `config.ini` to your preference.
- Install [Python](https://python.org/downloads) (minimum required version is 3.7).
- Run the script that installs dependencies and starts `proxy-scraper-checker`:
  - On Windows run `start.cmd`
  - On Unix-like operating systems run `start.sh`

### Termux

To use `proxy-scraper-checker` in Termux, knowledge of the Unix command-line interface is required.

- Download Termux from [F-Droid](https://f-droid.org/en/packages/com.termux/). [Don't download it from Google Play](https://github.com/termux/termux-app#google-play-store-deprecated).
- Run the following command (it will automatically update Termux packages, install Python, and download and install `proxy-scraper-checker`):
  ```bash
  bash <(curl -fsSL 'https://raw.githubusercontent.com/multics76/proxy-scraper-checker/main/install-termux.sh')
  ```
- Edit `~/proxy-scraper-checker/config.ini` to your preference using a text editor (vim/nano).
- To run `proxy-scraper-checker` use the following command:
  ```bash
  cd ~/proxy-scraper-checker && sh start-termux.sh
  ```

## Checking local proxy lists

To check the local proxy lists, start the Python HTTP server on your local machine by running the `python -m http.server --bind localhost` command in the folder with the proxy lists. After that, add links to the appropriate files in `config.ini`.

## Folders description

When the script finishes running, the following folders will be created (this behavior can be changed in the config):

- `proxies` - proxies with any anonymity level.
- `proxies_anonymous` - anonymous proxies.
- `proxies_geolocation` - same as `proxies`, but includes exit-node's geolocation.
- `proxies_geolocation_anonymous` - same as `proxies_anonymous`, but includes exit-node's geolocation.

Geolocation format is `ip:port|Country|Region|City`.

## License

[MIT](LICENSE)
