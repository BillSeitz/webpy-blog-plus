import web, datetime

#db = web.database(dbn='mysql', db='blog', user='justin')
from config import db

def posts():
    return db.select('entries', order='id DESC')

def post(id):
    try:
        return db.select('entries', where='id=$id', vars=locals())[0]
    except IndexError:
        return None

def post_create(title, text):
    db.insert('entries', title=title, content=text, posted_on=datetime.datetime.utcnow())

def post_delete(id):
    db.delete('entries', where="id=$id", vars=locals())

def post_update(id, title, text):
    db.update('entries', where="id=$id", vars=locals(),
        title=title, content=text)
        