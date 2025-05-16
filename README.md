#Final Project
[![Tests](https://github.com/RyanL-N/twitter-clone-final/actions/workflows/web-service.yml/badge.svg)](https://github.com/RyanL-N/twitter-clone-final/actions/workflows/web-service.yml)


## What this repo does
Basic Twitter clone to demo nginx, flask, and postgres. \
1 million users world wide! \
10 million rows!

## Build instructions
1. Download all files from repository.\
2. Create the file .env.prod file in the root. It should contain:
```
FLASK_APP=project/__init__.py
FLASK_DEBUG=1
DATABASE_URL=postgresql://postgres:pass@localhost:5432
SQL_HOST=postgres
SQL_PORT=5432
DATABASE=postgres
APP_FOLDER=/home/app/web
PGUSER=postgres
PGPASS=pass
```
\
3. Create the file .env.prod.db in the root. It should contain:
```
POSTGRES_USER=postgres
POSTGRES_PASSWORD=pass
POSTGRES_DB=postgres
```
\
4. Run: 
```
$ docker compose -f docker-compose.prod.yml up -d --build
$ sh load_data.sh

```
load_data.sh can be modified to create more fake data. It will create 10x more tweets than there are users.

