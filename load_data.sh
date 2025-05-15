#!/bin/sh
cd "$(dirname "$0")"
python3 ./fake_data.py --db=postgresql://postgres:pass@localhost:1319/postgres --rows=10

