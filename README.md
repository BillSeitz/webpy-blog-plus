webpy-blog-plus
===============

Web.py blog app extended with various cookbook techniques.

Using SQLite-3.

See BillSeitz notes at http://webseitz.fluxent.com/wiki/ExtendingWebpyBlogAppWithCookbookFeatures

Before launching the code for the first time:
* copy "config_example.py" to "config.py" - and tweak SMTP values if you want to use that feature
* generate empty SQLite db from schema: "sqlite3 blog.db < schema.sql"
