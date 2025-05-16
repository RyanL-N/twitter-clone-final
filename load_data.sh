#!/usr/bin/env bash
set -euo pipefail

# go to this script’s directory
cd "$(dirname "$0")"

# adjust if your host/port differ
DBURL="postgresql://postgres:pass@localhost:1319/postgres"
ROWS=1000000
TWEET_MULTIPLIER=10

echo "1/4: Generating users.csv…"
python3 - <<PYCODE
import csv
from essential_generators import DocumentGenerator
rows = $ROWS
gen = DocumentGenerator()
with open('users.csv', 'w', newline='') as f:
    w = csv.writer(f)
    for i in range(rows):
        w.writerow([str(i), gen.word(), i])
PYCODE

echo "2/4: Generating urls.csv…"
python3 - <<PYCODE
import csv
from essential_generators import DocumentGenerator
rows = $ROWS
gen = DocumentGenerator()
with open('urls.csv', 'w', newline='') as f:
    w = csv.writer(f)
    for i in range(rows):
        w.writerow([i, gen.url() + str(i)])
PYCODE

echo "3/4: Generating tweets.csv…"
python3 - <<PYCODE
import csv, random, datetime
from essential_generators import DocumentGenerator
rows = $ROWS
mult = $TWEET_MULTIPLIER
gen = DocumentGenerator()
with open('tweets.csv', 'w', newline='') as f:
    w = csv.writer(f)
    for i in range(rows * mult):
        w.writerow([
            i,
            random.randrange(rows),
            datetime.datetime.now().isoformat(sep=' '),
            gen.sentence()
        ])
PYCODE

echo "4/4: Bulk-loading into Postgres…"
psql "$DBURL" <<SQL
\copy users      (username,password,id_users)          FROM 'users.csv' CSV
\copy user_urls  (id_users,url)                        FROM 'urls.csv'  CSV
\copy tweets     (id_tweets,id_users,created_at,text)  FROM 'tweets.csv' CSV
SQL

echo "✅ Done!"

