""" Basic blog using webpy 0.3 """
import web
import model
import config

### Define urls """
urls = (
    '/', 'Posts',
    '/post/(\d+)', 'Post',
    '/create', 'Create',
    '/post/(\d+)/delete', 'Delete',
    '/post/(\d+)/update', 'Update',
    '/login_fake/(.+)', 'LoginFake',
    '/logout', 'LogOut',
)

app = web.application(urls, globals())

### Define session
"""
TO-DO: session is defined this way as a workaround --should add handler when web.config.debug = False
"""
if web.config.get('_session') is None: # from http://webpy.org/cookbook/session_with_reloader
    session = web.session.Session(app, web.session.DiskStore('sessions'))
    web.config._session = session
else:
    session = web.config._session

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

def user_name():
	if not session.has_key('user_name'):
		session.user_name = None
	return session.user_name

### Define template base and pass some globals
render = web.template.render('templates', base='base', globals={'csrf_token': csrf_token, 'datestr': web.datestr, 'user_name': user_name})

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

### Class Create - renders form to create new entry and handles POST request to add it the database
class Create:

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

### Class Delete - handles POST request to delete entry by id
class Delete:

    @csrf_protected # Verify this is not CSRF, or fail
    def POST(self, id):
        model.post_delete(int(id))
        raise web.seeother('/')

### Class Update - renders form to edit entries by id and handles POST request to update entry in database
class Update:

    def GET(self, id):
        post = model.post(int(id))
        form = Create.form()
        form.fill(post)
        return render.post_update(post, form)

    @csrf_protected # Verify this is not CSRF, or fail
    def POST(self, id):
        form = Create.form()
        post = model.post(int(id))
        if not form.validates():
            return render.edit(post, form)
        model.post_update(int(id), form.d.title, form.d.content)
        raise web.seeother('/')

class LoginFake:

	def GET(self, name):
		session.user_name = name
		return "Hello, %s!" % (session.user_name)
		
class LogOut:

	def GET(self):
		session.user_name = None
		return "Now I think you are %s" % (session.user_name)
		
### If module is called directly, run development server
if __name__ == '__main__':
    app.run()
