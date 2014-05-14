""" 
Basic blog using webpy 0.3 
Heavily modified by BillSeitz:
 * renamed classes and models and templates
 * add config.py to isolate configuration settings
 * add authentication features
"""
import web
from web import form
import model
from config import *
from datetime import datetime
from time import sleep

### Define urls
urls = (
    '/', 'Posts',
    '/post/(\d+)', 'Post',
    '/create', 'Post_Create',
    '/post/(\d+)/delete', 'Post_Delete',
    '/post/(\d+)/update', 'Post_Update',
    '/login', 'login',
    '/logout', 'logout',
    '/password_reset', 'password_reset',
    '/password_reset_submit/(.+)', 'password_reset_submit',
    '/register', 'register',
)

app = web.application(urls, globals())

if web.config.get('_session') is None: # from http://webpy.org/cookbook/session_with_reloader
    session = web.session.Session(app, web.session.DiskStore('sessions'))
    web.config._session = session
else:
    session = web.config._session

""" functions used in templates """
### Cross-site request forgery protection
def csrf_token():
    if not session.has_key('csrf_token'):
        from uuid import uuid4
        session.csrf_token=uuid4().hex
    return session.csrf_token

def csrf_protected(f):
    def decorated(*args,**kwargs):
        inp = web.input()
        if not (inp.has_key('csrf_token') and inp.csrf_token==session['csrf_token']):
            raise web.HTTPError(
                "400 Bad request",
                {'content-type':'text/html'},
                """Cross-site request forgery (CSRF) attempt (or stale browser form).
<a href="">Back to the form</a>.""") # Provide a link back to the form
        return f(*args,**kwargs)
    return decorated

def datestr(posted_on):
    datetime_obj = datetime.strptime(posted_on,'%Y-%m-%d %H:%M:%S.%f')
    return web.datestr(datetime_obj)
    
def user_name():
    if not session.has_key('user_name'):
        session.user_name = None
    return session.user_name

### Define template base and pass some globals
render = web.template.render('templates', base='base', globals={'context': session, 'csrf_token': csrf_token, 'datestr': datestr, 'user_name': user_name})
render_email = web.template.render('templates/', globals={'context': session, 'csrf_token': csrf_token, 'datestr': datestr, 'user_name': user_name})

### Class Posts - renders main page with list of entries, and links to post new ones.
class Posts:

    def GET(self):
        """ Show page """
        posts = model.posts()
        return render.index(posts)

### Class Post - renders singular entry
class Post:

    def GET(self, id):
        """ View single post """
        post = model.post(int(id))
        return render.post(post)

### Class Post_Create - renders form to create new entry and handles POST request to add it the database
class Post_Create:

    form = web.form.Form(
        web.form.Textbox('title', web.form.notnull, 
            size=30,
            description="Post title:"),
        web.form.Textarea('content', web.form.notnull, 
            rows=30, cols=80,
            description="Post content:"),
        web.form.Button('Post entry'),
    )

    def GET(self):
        form = self.form()
        return render.post_create(form)
        
    @csrf_protected # Verify this is not CSRF, or fail
    def POST(self):
        form = self.form()
        if not form.validates():
            return render.new(form)
        model.post_create(form.d.title, form.d.content)
        raise web.seeother('/')

### Class Post_Delete - handles POST request to delete entry by id
class Post_Delete:

    @csrf_protected # Verify this is not CSRF, or fail
    def POST(self, id):
        model.post_delete(int(id))
        raise web.seeother('/')

### Class Post_Update - renders form to edit entries by id and handles POST request to update entry in database
class Post_Update:

    def GET(self, id):
        post = model.post(int(id))
        form = Post_Create.form()
        form.fill(post)
        return render.post_update(post, form)

    @csrf_protected # Verify this is not CSRF, or fail
    def POST(self, id):
        form = Post_Create.form()
        post = model.post(int(id))
        if not form.validates():
            return render.edit(post, form)
        model.post_update(int(id), form.d.title, form.d.content)
        raise web.seeother('/')


""" --------------- users, registration/login/etc --------------"""

class login:
    def GET(self): #login form
        # do $:f.render() in the template
        f = login_form()
        msg = None
        if session.has_key("auth_error"):
            msg = session.auth_error
        return render.login(f, msg)
    @csrf_protected # Verify this is not csrf, or fail
    def POST(self): 
        # artificial delay (to slow down brute force attacks)
        sleep(forced_delay)
        i = web.input()
        user_email = i.get('user_email', '').strip()
        password = i.get('password', '').strip()
        user = user_authenticate(user_email, password)
        if not user:
            session.auth_error = 'fail'
            web.seeother('/login')
            return 
        elif user.user_status == 'suspended':
            session.auth_error = 'suspended'
            web.seeother('/login')
            return
        else:
            #login(user)
            if session.has_key('auth_error'):
                del session['auth_error']
            session.user_name = user.user_name
            session.user_id = user.user_id
        next = session.get('next', '/')
        try:
            del session['next']
        except KeyError:
            pass
        web.seeother(next)
        return

class logout:
    def GET(self):
        #import pdb; pdb.set_trace()
        try:
            web.debug(str(dict(session)))
            del session['user_name']
            del session['user_id']
        except KeyError:
            pass
        web.seeother('/')

class password_reset: # trigger reset-request
    def GET(self): #login form
        # do $:f.render() in the template
        f = password_reset_form()
        msg = None
        if session.has_key("auth_error"):
            msg = session.auth_error
        return render.password_reset(f, msg)
    @csrf_protected # Verify this is not csrf, or fail
    def POST(self): 
        i = web.input()
        user_email = i.get('user_email', '').strip()
        if not user_exists(user_email):
            session.auth_error = 'fail'
            web.seeother('/password_reset')
            return 
        else:
            if session.has_key('auth_error'):
                del session['auth_error']
            hash_temp = user_hash_set(user_email) # set users.hash_temp in db
            # send email
            msg_subject = "Reset your password"
            msg_body = render_email.user_email_password_reset(hash_temp)['__body__']
            headers = {'Content-Type':'text/html;charset=utf-8'}
            web.sendmail(web.config.smtp_username, user_email, msg_subject, msg_body, headers=headers)         
        next = session.get('next', '/')
        try:
            del session['next']
        except KeyError:
            pass
        web.seeother(next)
        return

class password_reset_submit: # do actual reset
    def GET(self, hash_temp): # form for new password
        # check that hash exists, if so generate form
        user_emails = model.user_emails_for_hash(hash_temp)
        if bool(user_emails):
            user_email = list(user_emails)[0]["user_email"]
            msg = None
        else:
            user_email = None
            msg = 'fail'
        web.debug(user_email)
        f = password_reset_submit_form()
        return render.password_reset_submit(f, user_email, hash_temp, msg)
    @csrf_protected # Verify this is not csrf, or fail
    def POST(self, hash_temp): # set the new password, clear the hash
        i = web.input()
        user_email = i.get('user_email', '').strip()
        password = i.get('password', '').strip()
        # check that hash/email match
        users = model.user_for_email_and_hash(user_email, hash_temp)
        if not bool(users):
            web.seeother('password_reset')
        # set new password, clear hash_temp
        hashed = hashBcrypt(password)
        model.user_update_password(user_email, hashed)
        web.seeother('/login')

class register:
    def GET(self, msg = None):
        # do $:f.render() in the template
        f = register_form()
        return render.register(f, msg)
    @csrf_protected # Verify this is not csrf, or fail
    def POST(self, msg = None):
        f = register_form()
        if not f.validates():
            return render.register(f, msg)
        else:
            try:
                user_id = user_create(f.d.user_email.strip(), f.d.user_name.strip(), f.d.password.strip())
                session.user_name = f.d.user_name.strip()
                session.user_id = user_id
                web.seeother('/') # should really capture 
            except AuthError:
                web.seeother('/register?msg=CreateUserFailed')

class AuthError(Exception): pass

def user_authenticate(login, password):
    """
    Validates the user's credentials. If are valid, returns
    a user object (minus the password hash).
    """
    login = login.strip()
    password = password.strip()        
    user = model.users_for_email(login)
    if not bool(user):
        return None
    user = list(user)[0]
    if user.user_status == 'deleted':
        return None
    if not password_check(password, user.user_password):
        return None
        
    del user['user_password']
    return user

def user_hash_set(email): # set a 1-time-use user hash field for whatever use (mainly MemberResetsPassword)
    import uuid
    hash_temp = str(uuid.uuid4())
    model.user_update_hash(email, hash_temp)
    return hash_temp

def user_exists(email):
    """
    Return True if a user with that email already exists.
    """
    return model.user_email_matches(email) > 0

def password_check(password, stored_passw):
    """
    Returns a boolean of whether the password was correct.
    """
    from cryptacular.bcrypt import BCRYPTPasswordManager
    manager = BCRYPTPasswordManager()
    return manager.check(stored_passw, password)

def hashBcrypt(password, salt='', n=12):
    import cryptacular.bcrypt
    from cryptacular.bcrypt import BCRYPTPasswordManager
    manager = BCRYPTPasswordManager()
    hashed = manager.encode(password)
    return hashed

def user_create(email, user_name, password=None):
    """
    Create a new user and returns its id.
    If password is None, it will marks the user as having no password
    (check_password() for this user will never return True).
    """
    #email = email.strip()
    if user_exists(email):
        raise AuthError, 'user exist'
    if not password:
        raise AuthError, 'UNUSABLE_PASSWORD' # BillS insert dubiously
        hashed = UNUSABLE_PASSWORD
    else:
        #password = password.strip()
        if len(password) < password_minlen:
            raise AuthError, 'bad password'
        hashed = hashBcrypt(password)    
    user_id = model.user_create(email, hashed, user_name) 
    return user_id

"""
------------ forms for users, register, login, etc. ----------
"""
vpass = form.regexp(r".{3,20}$", 'must be between 3 and 20 characters')
vemail = form.regexp(r".*@.*", "must be a valid email address")

register_form = form.Form(
    form.Textbox("user_email", vemail, description="E-Mail"),
    form.Textbox("user_name", description="User Name"),
    form.Password("password", vpass, description="Password"),
    form.Password("password2", description="Repeat password"),
    form.Button("Register", type="submit"),
    validators = [
        form.Validator("Passwords didn't match", lambda i: i.password == i.password2)]
    )

login_form = form.Form(
    form.Textbox("user_email", vemail, description="E-Mail"),
    form.Password("password", vpass, description="Password"),
    form.Button("Log In", type="submit"),
    )

password_reset_form = form.Form(
    form.Textbox("user_email", vemail, description="E-Mail"),
    form.Button("Send a password-reset email", type="submit"),
    )

password_reset_submit_form = form.Form(
    form.Password("password", vpass, description="New password"),
    form.Password("password2", vpass, description="Repeat new password"),
    form.Button("Reset my password", type="submit"),
    validators = [
        form.Validator("Passwords didn't match", lambda i: i.password == i.password2)]
    )

### If module is called directly, run development server
if __name__ == '__main__':
    app.run()
