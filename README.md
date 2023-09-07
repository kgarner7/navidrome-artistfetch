# Navidrome Artist Image Fetcher

This tool is designed to query a Navidrome instance for all artists, and manually fetch the details
of each to populate artist profile pictures and biographies (if they exist).

## Requirements

Supports Python >= 3.9. This requires two Python package, `requests`, and `python-dateutil` (for Python 3.9). To install everything, you can do `pip install -r requirements.txt`

## Usage

```
usage: Artist Fetch [-h] [-u USERNAME] [-p PASSWORD] [-f] [-d DAYS_SINCE] server

Tool to query Navidrome and fetch artist images

positional arguments:
  server                The base url to your server (e.g. https://music.example.com)

options:
  -h, --help            show this help message and exit
  -u USERNAME, --username USERNAME
                        The username you want to authenticate as. If not provided, you will be prompted in console
  -p PASSWORD, --password PASSWORD
                        The password you want to authenticate as. If not provided, you will be prompted in console. Caution: If set, your password may be saved in your shell's history
  -f, --force           If true, try and fetch artist images even if the last fetch time was recent
  -d DAYS_SINCE, --days-since DAYS_SINCE
                        How many days until external info is considered 'stale' and will be refetched
```

Personally, I would recommend just doing `python main.py $YOUR_SERVER_URL -u $USERNAME` and then letting
the script prompt you for the password.
