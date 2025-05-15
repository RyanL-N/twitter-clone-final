import argparse
import sqlalchemy
from tqdm import tqdm
import random
import string
import time
from essential_generators import DocumentGenerator
import datetime

parser = argparse.ArgumentParser()
parser.add_argument('--db', required=True) 
parser.add_argument('--rows', default=100)
args = parser.parse_args()

engine = sqlalchemy.create_engine(args.db, connect_args={
    'application_name': 'fake_data.py',
    })
connection = engine.connect()

gen=DocumentGenerator()

def generate_users(n):
    for i in tqdm(range(n), desc="Generate Users"):
        username = str(i)
        id_user=i
        password = gen.word()
        sql = sqlalchemy.sql.text("""
            INSERT INTO users (username, password, id_users) VALUES (:user, :pw, :id);
        """)
        try:
            res = connection.execute(sql, {
                'user': username,
                'pw': password,
                'id': id_user
                })
        except sqlalchemy.exc.IntegrityError as e:
            print("user",i,"FAIL",e)

def generate_urls(n):
    for i in tqdm(range(n), desc="Generate URLs"):
        url = gen.url() + str(i)
        id_user = i
        sql = sqlalchemy.sql.text("""
            INSERT INTO user_urls (id_users, url) VALUES (:id, :url);
        """)
        try:
            res = connection.execute(sql, {'id':id_user,'url': url})
        except sqlalchemy.exc.IntegrityError as e:
            print("url",i,"FAIL",e)

def generate_messages(n):
    sql = sqlalchemy.sql.text("""
        SELECT id_users FROM users;
    """)
    res = connection.execute(sql)
    ids = [tup[0] for tup in res.fetchall()]

    for i in tqdm(range(n), desc="Generate Messages"):
        id_tweets = i
        id_users = random.choice(ids)
        text = gen.sentence()
        time = datetime.datetime.now() 
        sql = sqlalchemy.sql.text("""
        INSERT INTO tweets (id_tweets, id_users, created_at, text) VALUES (:id_tweets, :id_users, :created_at, :text);
        """)
        try:
            res = connection.execute(sql, {
                'id_tweets': id_tweets,
                'id_users': id_users,
                'created_at': time,
                'text': text
                })
        except sqlalchemy.exc.IntegrityError as e:
            print("message",i,"FAIL",e)


start_time = time.time()

generate_users(int(args.rows))
generate_urls(int(args.rows))
generate_messages(10 * int(args.rows))

end_time = time.time()

runtime = end_time - start_time

print('runtime =', runtime)

connection.close()
