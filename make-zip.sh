#!/usr/bin/env bash
# Builds the U3 upload package with the files at the archive root (no folder prefix).
set -euo pipefail
cd "$(dirname "$0")"
rm -f txn-screener-u3-py.zip
zip -q txn-screener-u3-py.zip handler.py screener.py requirements.txt
unzip -l txn-screener-u3-py.zip
