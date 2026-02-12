# CLI tool for [rdgen](https://github.com/bryangerlach/rdgen)

Generate custom RustDesk clients via command interface instead of using web browser.

# Usage

Install requirements:
```bash
python -m pip install -r requirements.txt
```
or (for externally-managed-environment)
```bash
# Debian-based:
apt install python3-requests

# RHEL-based:
dnf install python3-requests
```

Clone repository:
```bash
git clone --depth 1 https://github.com/AlekseyLapunov/rdgen-cli

cd rdgen-cli
```

Help page:
```bash
usage: rdgen_cli.py [-h] -f FILE -s SERVER [--set-version SET_VERSION] [--set-platform SET_PLATFORM] [-v] [-p] [-d]

options:
  -h, --help            show this help message and exit
  -f FILE, --file FILE  Input configuration file (JSON)
  -s SERVER, --server SERVER
                        Address of rdgen server. HTTP (:80) is the default scheme
  --set-version SET_VERSION
                        Override the 'version' key in the configuration JSON
  --set-platform SET_PLATFORM
                        Override the 'platform' key in the configuration JSON
  -v, --verbose         Increase output verbosity
  -p, --preserve-log    Preserve build status log
  -d, --disable-download
                        Disable automatic result download
```

Example:
```bash
cp template.json my_config.json

# ... making changes to my_config.json ...

python rdgen_cli.py -v -f my_config.json -s https://rdgen.crayoneater.org
```

# Notice

Although you can specify custom port and basic authorization data in this tool, it won't work with vanilla [rdgen](https://github.com/bryangerlach/rdgen) as of now. But it should be easy to modify [rdgen](https://github.com/bryangerlach/rdgen) Actions pipelines to enable such functionality.

# Versions

Tested with:
- Python: 3.11.2, 3.13.5;
- `requests`: 2.28.1, 2.32.5;
- OS: Debian 12 (Bookworm), Windows 11.
