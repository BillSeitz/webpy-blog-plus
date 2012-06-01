""" Basic blog using webpy 0.3 """
import web
import model

### Define urls """
urls = (
    '/', 'Index',
    '/view/(\d+)', 'View',
    '/new', 'New',
    '/delete/(\d+)', 'Delete',
    '/edit/(\d+)', 'Edit',
)

### Define session
"""
TO-DO: session is defined this way as a workaround --should add handler when web.config.debug = False
"""
if web.config.get('_session') is None: # from http://webpy.org/cookbook/session_with_reloader
    session = web.session.Session(app, web.session.DiskStore('sessions'))
    web.config._session = session
else:
    session = web.config._session

### Define template base and pass some globals
render = web.template.render('templates', base='base', globals={'csrf_token':csrf_token, 'datestr': web.datestr})


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

### Class Index - renders main page with list of entries, and links to post new ones.
class Index:

    def GET(self):
        """ Show page """
        posts = model.get_posts()
        return render.index(posts)

### Class View - renders singular entry
class View:

    def GET(self, id):
        """ View single post """
        post = model.get_post(int(id))
        return render.view(post)

### Class New - renders form to create new entry and handles POST request to add it the database
class New:

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
        return render.new(form)
        
    @csrf_protected # Verify this is not CSRF, or fail
    def POST(self):
        form = self.form()
        if not form.validates():
            return render.new(form)
        model.new_post(form.d.title, form.d.content)
        raise web.seeother('/')

### Class Delete - handles POST request to delete entry by id
class Delete:

    @csrf_protected # Verify this is not CSRF, or fail
    def POST(self, id):
        model.del_post(int(id))
        raise web.seeother('/')

### Class Edit - renders form to edit entries by id and handles POST request to update entry in database
class Edit:

    def GET(self, id):
        post = model.get_post(int(id))
        form = New.form()
        form.fill(post)
        return render.edit(post, form)

    @csrf_protected # Verify this is not CSRF, or fail
    def POST(self, id):
        form = New.form()
        post = model.get_post(int(id))
        if not form.validates():
            return render.edit(post, form)
        model.update_post(int(id), form.d.title, form.d.content)
        raise web.seeother('/')

### If module is called directly, run development server
if __name__ == '__main__':
    app = web.application(urls, globals())
    app.run()