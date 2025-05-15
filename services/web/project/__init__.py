import os
from flask import (
    Flask,
    jsonify,
    send_from_directory,
    request,
    render_template,
    make_response,
    redirect,
    url_for
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import sqlalchemy
import datetime
import re

app = Flask(__name__)

engine = sqlalchemy.create_engine("postgresql://postgres:pass@postgres:5432", connect_args={'application_name': '__init__.py'})
connection = engine.connect()


def are_creds_good(user, pw):
    # look into db and find
    sql = sqlalchemy.sql.text("""
        SELECT id_users FROM users
        WHERE username ILIKE :user
        and password ILIKE :pw;
            """)
    res = connection.execute(sql, {
        'user': user,
        'pw': pw
    })

    if res.first() is None:
        return False
    else:
        return True


def root_tweets(page):
    sql = sqlalchemy.sql.text("""
        SELECT id_users, created_at, text from tweets
        ORDER BY created_at DESC
        LIMIT 20 OFFSET :offset;
            """)

    res = connection.execute(sql, {'offset': (page) * 20})
    tweets = []
    for tweet in res.fetchall():
        id_user = tweet[0]
        time = tweet[1]
        text = tweet[2]
        sql = sqlalchemy.sql.text("""
            SELECT username from users
            WHERE id_users=:id;
                """)
        username = connection.execute(sql, {'id': id_user}).fetchone()[0]
        tweets.append({
            'username': username,
            'text': text,
            'time': time
        })
    return tweets


def unique_username(name):
    sql = sqlalchemy.sql.text("""
        SELECT username from users
        WHERE username ILIKE :user;
            """)
    res = connection.execute(sql, {'user': name})

    if res.first() is None:
        return True
    else:
        return False


def add_user(username, pw):
    sql = sqlalchemy.sql.text("""SELECT id_users from users ORDER BY id_users DESC LIMIT 1;""")
    new_id = connection.execute(sql).first()[0] + 1

    sql = sqlalchemy.sql.text("""
        INSERT INTO users (id_users, username, password)
        VALUES (:id, :username, :pw);
            """)
    res = connection.execute(sql, {
        'id': new_id,
        'username': username,
        'pw': pw
    })
    return res


def add_tweet(username, tweet):
    sql = sqlalchemy.sql.text("""SELECT id_tweets from tweets ORDER BY id_tweets DESC LIMIT 1""")
    cid = connection.execute(sql).first()[0] + 1

    sql = sqlalchemy.sql.text("""
        SELECT id_users from users
        WHERE username ILIKE :username;
            """)
    uid = connection.execute(sql, {'username': username}).first()[0]

    sql = sqlalchemy.sql.text("""
        INSERT INTO tweets (id_tweets, id_users, created_at, text)
        VALUES (:cid, :uid, :time, :text);
            """)
    time = datetime.datetime.now()
    res = connection.execute(sql, {
        'cid': cid,
        'uid': uid,
        'time': time,
        'text': tweet
    })
    return res


def highlight(term, text):
    return re.sub('(?i)' + term, '<mark>' + term + '</mark>', text)


def search_tweets(term, page):
    sql_term = re.sub(' +', ' | ', term)
    sql = sqlalchemy.sql.text("""
        SELECT id_users, created_at, text, a <=> to_tsquery('english', :term) as rank
        FROM tweets
        WHERE a @@ to_tsquery('english', :term)
        ORDER BY a <=> to_tsquery('english', :term)
        LIMIT 20 OFFSET :offset;
            """)

    res = connection.execute(sql, {
        'offset': (page) * 20,
        'term': sql_term
    })
    tweets = []
    for tweet in res.fetchall():
        id_user = tweet[0]
        time = tweet[1]
        text = highlight(term, tweet[2])
        sql = sqlalchemy.sql.text("""
            SELECT username from users
            WHERE id_users=:id;
                """)
        username = connection.execute(sql, {'id': id_user}).fetchone()[0]
        tweets.append({
            'username': username,
            'text': text,
            'time': time
        })
    return tweets


@app.route("/", methods=["GET", "POST"])
def root():
    # check if logged in
    if request.cookies.get('loggedIn') == 'true':
        good_credentials = True
    else:
        good_credentials = False

    page = int(request.args.get('page', 0))
    tweets = root_tweets(page)

    return render_template('root.html', logged_in=good_credentials, tweets=tweets, page=page)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.cookies.get('loggedIn') == 'true':
        return redirect(url_for('root', bad_credentials=False, logged_in=True, tweets=root_tweets(0), page=0))

    username = request.form.get("username")
    password = request.form.get("password")
    good_credentials = are_creds_good(username, password)

    if username is None:
        return render_template('login.html', bad_credentials=False)
    else:
        if not good_credentials:
            return render_template('login.html', bad_credentials=True)
        else:
            response = redirect(url_for('root', bad_credentials=False, logged_in=True, tweets=root_tweets(0), page=0))
            response.set_cookie('username', username)
            response.set_cookie('password', password)
            response.set_cookie('loggedIn', 'true')
            return response

    return render_template('login.html')


@app.route("/logout", methods=["GET", "POST"])
def logout():
    response = redirect('/')
    # response.CookieJar.clear()
    response.set_cookie('username', max_age=0)
    response.set_cookie('password', max_age=0)
    response.set_cookie('loggedIn', max_age=0)
    return response


@app.route("/create_account", methods=["GET", "POST"])
def create_account():
    if request.cookies.get('loggedIn') == 'true':
        return redirect(url_for('root', bad_credentials=False, logged_in=True, tweets=root_tweets(0), page=0))

    username = request.form.get("username")
    pw1 = request.form.get("pw1")
    pw2 = request.form.get("pw2")
    unique = unique_username(username)
    if username is None:
        return render_template('create_account.html', bad_user=None, bad_pw=None)
    elif unique is False:
        return render_template('create_account.html', bad_user=True, bad_pw=None)
    elif pw1 != pw2:
        return render_template('create_account.html', bad_user=False, bad_pw=True)
    else:
        add_user(username, pw1)
        response = redirect(url_for('root', bad_credentials=False, logged_in=True, tweets=root_tweets(0), page=0))
        response.set_cookie('username', username)
        response.set_cookie('password', pw1)
        response.set_cookie('loggedIn', 'true')
        return response


@app.route("/create_tweet", methods=["GET", "POST"])
def create_tweet():
    if request.cookies.get('loggedIn') == 'true':
        good_credentials = True
    else:
        good_credentials = False
        return redirect(url_for('root', bad_credentials=True, logged_in=False, tweets=root_tweets(0), page=0))

    if request.form.get("tweet") is None:
        return render_template('create_tweet.html', logged_in=good_credentials)

    tweet = request.form.get("tweet")
    username = request.cookies.get('username')

    add_tweet(username, tweet)
    # add to database
    response = redirect(url_for('root', bad_credentials=False, logged_in=True, tweets=root_tweets(0), page=0))
    return response


@app.route("/search", methods=["GET", "POST"])
def search():
    search_term = request.args.get('search_term')

    if search_term is None:
        return render_template('search.html', searched=False)
    else:
        page = int(request.args.get('page', 0))
        tweets = search_tweets(search_term, page)
        return render_template('search.html', searched=True, tweets=tweets, page=page)
