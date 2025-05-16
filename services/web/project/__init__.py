import os
from flask import (
    Flask, jsonify, send_from_directory, request,
    render_template, make_response, redirect, url_for
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import sqlalchemy
import datetime
import re

app = Flask(__name__)

engine = sqlalchemy.create_engine(
    "postgresql://postgres:pass@postgres:5432",
    connect_args={'application_name': '__init__.py'}
)
connection = engine.connect()


def are_creds_good(user, pw):
    sql = sqlalchemy.sql.text("""
        SELECT id_users FROM users
        WHERE username ILIKE :user AND password ILIKE :pw;
    """)
    res = connection.execute(sql, {'user': user, 'pw': pw})
    return res.first() is not None


def root_tweets(page):
    sql = sqlalchemy.sql.text("""
        SELECT id_users, created_at, text FROM tweets
        ORDER BY created_at DESC
        LIMIT 20 OFFSET :offset;
    """)
    res = connection.execute(sql, {'offset': page * 20})
    tweets = []
    for tweet in res.fetchall():
        id_user, time, text = tweet
        username = connection.execute(
            sqlalchemy.sql.text("SELECT username FROM users WHERE id_users=:id"),
            {'id': id_user}
        ).fetchone()[0]
        tweets.append({'username': username, 'text': text, 'time': time})
    return tweets


def unique_username(name):
    sql = sqlalchemy.sql.text("SELECT username FROM users WHERE username ILIKE :user;")
    res = connection.execute(sql, {'user': name})
    return res.first() is None


def add_user(username, pw):
    sql = sqlalchemy.sql.text("SELECT id_users FROM users ORDER BY id_users DESC LIMIT 1;")
    new_id = connection.execute(sql).first()[0] + 1
    sql = sqlalchemy.sql.text("""
        INSERT INTO users (id_users, username, password)
        VALUES (:id, :username, :pw);
    """)
    connection.execute(sql, {'id': new_id, 'username': username, 'pw': pw})


def add_tweet(username, tweet):
    cid = connection.execute(
        sqlalchemy.sql.text("SELECT id_tweets FROM tweets ORDER BY id_tweets DESC LIMIT 1")
    ).first()[0] + 1

    uid = connection.execute(
        sqlalchemy.sql.text("SELECT id_users FROM users WHERE username ILIKE :username"),
        {'username': username}
    ).first()[0]

    sql = sqlalchemy.sql.text("""
        INSERT INTO tweets (id_tweets, id_users, created_at, text)
        VALUES (:cid, :uid, :time, :text);
    """)
    connection.execute(sql, {
        'cid': cid, 'uid': uid, 'time': datetime.datetime.now(), 'text': tweet
    })


def highlight(term, text):
    return re.sub('(?i)' + re.escape(term), '<mark>' + term + '</mark>', text)


def search_tweets(term, page):
    sql_term = re.sub(' +', ' | ', re.escape(term))
    sql = sqlalchemy.sql.text("""
        SELECT id_users, created_at, text, a <=> to_tsquery('english', :term) AS rank
        FROM tweets
        WHERE a @@ to_tsquery('english', :term)
        ORDER BY a <=> to_tsquery('english', :term)
        LIMIT 20 OFFSET :offset;
    """)
    res = connection.execute(sql, {'offset': page * 20, 'term': sql_term})
    tweets = []
    for tweet in res.fetchall():
        id_user, time, text = tweet[0], tweet[1], tweet[2]
        username = connection.execute(
            sqlalchemy.sql.text("SELECT username FROM users WHERE id_users=:id"),
            {'id': id_user}
        ).fetchone()[0]
        tweets.append({
            'username': username,
            'text': highlight(term, text),
            'time': time
        })
    return tweets


@app.route("/", methods=["GET", "POST"])
def root():
    good_credentials = request.cookies.get('loggedIn') == 'true'
    page = int(request.args.get('page', 0))
    tweets = root_tweets(page)
    return render_template('root.html', logged_in=good_credentials, tweets=tweets, page=page)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.cookies.get('loggedIn') == 'true':
        return redirect(url_for('root', logged_in=True, page=0))

    username = request.form.get("username")
    password = request.form.get("password")
    if username is None:
        return render_template('login.html', bad_credentials=False)

    if not are_creds_good(username, password):
        return render_template('login.html', bad_credentials=True)

    response = redirect(url_for('root', logged_in=True, page=0))
    response.set_cookie('username', username)
    response.set_cookie('password', password)
    response.set_cookie('loggedIn', 'true')
    return response


@app.route("/logout", methods=["GET", "POST"])
def logout():
    response = redirect('/')
    response.set_cookie('username', '', max_age=0)
    response.set_cookie('password', '', max_age=0)
    response.set_cookie('loggedIn', '', max_age=0)
    return response


@app.route("/create_account", methods=["GET", "POST"])
def create_account():
    if request.cookies.get('loggedIn') == 'true':
        return redirect(url_for('root', logged_in=True, page=0))

    username = request.form.get("username")
    pw1 = request.form.get("pw1")
    pw2 = request.form.get("pw2")

    if username is None:
        return render_template('create_account.html', bad_user=None, bad_pw=None)
    if not unique_username(username):
        return render_template('create_account.html', bad_user=True, bad_pw=None)
    if pw1 != pw2:
        return render_template('create_account.html', bad_user=False, bad_pw=True)

    add_user(username, pw1)
    response = redirect(url_for('root', logged_in=True, page=0))
    response.set_cookie('username', username)
    response.set_cookie('password', pw1)
    response.set_cookie('loggedIn', 'true')
    return response


@app.route("/create_tweet", methods=["GET", "POST"])
def create_tweet():
    if request.cookies.get('loggedIn') != 'true':
        return redirect(url_for('root', logged_in=False, page=0))

    if request.form.get("tweet") is None:
        return render_template('create_tweet.html', logged_in=True)

    tweet = request.form.get("tweet")
    username = request.cookies.get('username')
    add_tweet(username, tweet)
    return redirect(url_for('root', logged_in=True, page=0))


@app.route("/search", methods=["GET", "POST"])
def search():
    search_term = request.args.get('search_term')
    if not search_term:
        return render_template('search.html', searched=False)

    page = int(request.args.get('page', 0))
    tweets = search_tweets(search_term, page)
    return render_template(
        'search.html',
        searched=True,
        tweets=tweets,
        page=page,
        search_term=search_term
    )

