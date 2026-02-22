# CLI tool for [RDGen](https://github.com/bryangerlach/rdgen)

Generate custom RustDesk clients via command interface instead of using web browser.

Help page:
```bash
usage: rdgen_cli.py [-h] -f FILE -s SERVER [--set-version SET_VERSION] [--set-platform SET_PLATFORM] [-v] [-p] [-d]

options:
  -h, --help                   show this help message and exit
  -f FILE, --file FILE         Input configuration file (JSON)
  -s SERVER, --server SERVER   Address of RDGen server. HTTP (:80) is the default scheme
  --set-version SET_VERSION    Override the 'version' key in the configuration JSON
  --set-platform SET_PLATFORM  Override the 'platform' key in the configuration JSON
  -v, --verbose                Increase output verbosity
  -p, --preserve-log           Preserve build status log
  -d, --disable-download       Disable automatic result download
```

# Usage (executable)

1. Download executable file from the [Releases](https://github.com/AlekseyLapunov/rdgen-cli/releases) page.
2. Obtain configuration JSON file. You can download the [template.json](https://raw.githubusercontent.com/AlekseyLapunov/rdgen-cli/refs/heads/main/template.json) from this repository or download it from RDGen web-page.
3. Open a terminal and run the executable with the flags specified in the help page above.

Example run:
```
chmod +x rdgen-cli-linux-x64

rdgen-cli-linux-x64 -f my_config.json -s https://rdgen.crayoneater.org
```

# Usage (python interpreter)

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

Example run:
```bash
cp template.json my_config.json

# ... making changes to my_config.json ...

python rdgen_cli.py -v -f my_config.json -s https://rdgen.crayoneater.org
```

# Kudos

Special thanks to [bryangerlach](https://github.com/bryangerlach) for creating the awesome [RDGen](https://github.com/bryangerlach/rdgen) service and contributing to this CLI tool in particular.

# Notice

Although you can specify custom port and basic authorization data in this tool, it won't work with vanilla [RDGen](https://github.com/bryangerlach/rdgen) as of now. But it should be easy to modify [RDGen](https://github.com/bryangerlach/rdgen) Actions pipelines to enable such functionality.
