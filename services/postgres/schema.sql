SET max_parallel_maintenance_workers TO 80;
SET maintenance_work_mem TO '16 GB';

CREATE TABLE users (
    id_users BIGINT PRIMARY KEY,
    username TEXT UNIQUE,
    password TEXT
);

CREATE TABLE user_urls (
    id_users BIGINT PRIMARY KEY,
    url TEXT UNIQUE,
    FOREIGN KEY (id_users) REFERENCES users(id_users)
);

CREATE TABLE tweets (
    id_tweets BIGINT PRIMARY KEY,
    id_users BIGINT,
    created_at TIMESTAMP,
    text TEXT,
    a tsvector,
    FOREIGN KEY (id_users) REFERENCES users(id_users)
);

CREATE EXTENSION IF NOT EXISTS RUM;

CREATE TRIGGER tsvectorupdate
BEFORE UPDATE OR INSERT ON tweets
FOR EACH ROW
EXECUTE PROCEDURE tsvector_update_trigger('a', 'pg_catalog.english', 'text');

/*
-- optional indexes for production performance
ALTER TABLE users SET (parallel_workers = 80);
ALTER TABLE user_urls SET (parallel_workers = 80);
ALTER TABLE tweets SET (parallel_workers = 80);

CREATE INDEX credentials1 ON users(username text_pattern_ops);
CREATE INDEX credentials2 ON users(password text_pattern_ops);
CREATE INDEX username   ON users(id_users, username text_pattern_ops);
CREATE INDEX tweet_time ON tweets(created_at);
CREATE INDEX tweet_text ON tweets USING rum(a rum_tsvector_ops);
*/

