py -m venv --upgrade-deps .venv
.venv\Scripts\python.exe -m pip install -U --disable-pip-version-check .[full]
.venv\Scripts\python.exe -m proxy_scraper_checker
