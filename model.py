import web, datetime

#db = web.database(dbn='mysql', db='blog', user='justin')
from config import db

def posts():
    #return db.select('entries', order='id DESC')
    return db.query("SELECT e.*, u.user_name FROM entries e LEFT OUTER JOIN users u ON e.user_id = u.user_id ORDER by e.id DESC")

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

def user_email_matches(user_email):
    count = db.select('users',
        what = 'count(*) as count',
        where = 'user_email = $user_email',
        vars = {'user_email': user_email}
    )[0].count
    return count

def users_for_email(user_email):
    return db.select('users', where = 'user_email = $user_email', vars = {'user_email': user_email})

def user_emails_for_hash(hash_temp):
    return db.select('users', what = 'user_email', where='hash_temp = $hash_temp', vars = {'hash_temp': hash_temp})

def user_for_email_and_hash(user_email, hash_temp):
    return db.select('users', what = 'user_id', where='user_email = $user_email AND hash_temp = $hash_temp', vars = {'user_email': user_email, 'hash_temp': hash_temp})

def user_create(email, hashed, user_name):
    user_id = db.insert('users', seqname = 'users_user_id_seq', 
            user_email = email,
            user_password = hashed,
            user_name = user_name, 
            user_last_login = datetime.datetime.utcnow()
        )
    return user_id

def user_update_password(user_email, hashed):
	db.update('users', where='user_email = $user_email', hash_temp = None, user_password = hashed, vars = {'user_email': user_email, 'hashed': hashed})

def user_update_hash(email, hash_temp):
    db.update('users', where="user_email = $user_email", hash_temp = hash_temp, vars = {'user_email': email, 'hash_temp': hash_temp})
