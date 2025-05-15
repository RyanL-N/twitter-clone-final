# services/postgres/Dockerfile
FROM postgis/postgis:latest

# 1. Install build tools + matching PG headers (v17)
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      less \
      make \
      vim \
      git \
      gcc \
      postgresql-server-dev-17 \
 && rm -rf /var/lib/apt/lists/*

# 2. Clone, build & install RUM extension
RUN cd /tmp \
 && git clone https://github.com/postgrespro/rum \
 && cd rum \
 && make USE_PGXS=1 \
 && make USE_PGXS=1 install

# 3. Prepare data directory
WORKDIR /tmp/postgres
RUN mkdir /data && chown postgres /data

# 4. Copy your schema into the init directory
COPY schema.sql /docker-entrypoint-initdb.d/01.sql

