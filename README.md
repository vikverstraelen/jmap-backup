# jmap-backup

[![PyPI](https://img.shields.io/pypi/v/jmap-backup.svg)](https://pypi.org/project/jmap-backup/)
[![Changelog](https://img.shields.io/github/v/release/vikverstraelen/jmap-backup?include_prereleases&label=changelog)](https://github.com/vikverstraelen/jmap-backup/releases)
[![Tests](https://github.com/vikverstraelen/jmap-backup/actions/workflows/test.yml/badge.svg)](https://github.com/vikverstraelen/jmap-backup/actions/workflows/test.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/vikverstraelen/jmap-backup/blob/master/LICENSE)

A CLI tool to backup a mailbox using the JMAP protocol

## Installation

Install this tool using `pip`:
```bash
pip install jmap-backup
```
## Usage

For help, run:
```bash
jmap-backup --help
```
You can also use:
```bash
python -m jmap_backup --help
```
## Development

To contribute to this tool, first checkout the code. Then create a new virtual environment:
```bash
cd jmap-backup
python -m venv venv
source venv/bin/activate
```
Now install the dependencies and test dependencies:
```bash
pip install -e '.[test]'
```
To run the tests:
```bash
python -m pytest
```
