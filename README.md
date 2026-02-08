# CLI tool for [rdgen](https://github.com/bryangerlach/rdgen)

Generate custom RustDesk clients via command interface instead of using web browser.

# Usage

Install requirements:
```bash
$ python -m pip install -r requirements.txt
```

Clone repository:
```bash
$ git clone --depth 1 https://github.com/AlekseyLapunov/rdgen-cli
```

Help page:
```bash
$ python rdgen_cli.py --help
usage: rdgen_cli.py [-h] -f FILE -s SERVER [-v] [-p] [-d]

options:
  -h, --help            show this help message and exit
  -f, --file FILE       Input configuration file (JSON)
  -s, --server SERVER   Address of rdgen server. HTTP (:80) is the default scheme
  -v, --verbose         Increase output verbosity
  -p, --preserve-log    Preserve build status log
  -d, --disable-download
                        Disable automatic result download
```

Example:
```bash
$ cp template.json my_config.json

# ... making changes to my_config.json ...

$ python rdgen_cli.py -v -f my_config.json -s https://rdgen.crayoneater.org
```

# Notice

Although you can specify **custom port** and **basic authorization data** in this tool, it won't work with vanilla [rdgen](https://github.com/bryangerlach/rdgen) as of now. But it should be easy to modify [rdgen](https://github.com/bryangerlach/rdgen) Actions pipelines to enable such functionality.

# Versions

Tested with:
- Python: 3.13.5
- `requests`: 2.32.5
