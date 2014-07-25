import os, os.path
import random
import sqlite3
import string

import cherrypy

DB_STRING = "my.db"

class StringGenerator(object):
    @cherrypy.expose
    def index(self):
        return file('index.html')

class StringGeneratorWebService(object):
     exposed = True

     @cherrypy.tools.accept(media='text/plain')
     def GET(self):
         with sqlite3.connect(DB_STRING) as c:
             c.execute("SELECT value FROM user_string WHERE session_id=?",
                       [cherrypy.session.id])
             return c.fetchone()

     def POST(self, length=8):
         some_string = ''.join(random.sample(string.hexdigits, int(length)))
         with sqlite3.connect(DB_STRING) as c:
             c.execute("INSERT INTO user_string VALUES (?, ?)",
                       [cherrypy.session.id, some_string])
         return some_string

     def PUT(self, another_string):
         with sqlite3.connect(DB_STRING) as c:
             c.execute("UPDATE user_string SET value=? WHERE session_id=?",
                       [another_string, cherrypy.session.id])

     def DELETE(self):
         with sqlite3.connect(DB_STRING) as c:
             c.execute("DELETE FROM user_string WHERE session_id=?",
                       [cherrypy.session.id])

def setup_database():
     """
     Create the `user_string` table in the database
     on server startup
     """
     with sqlite3.connect(DB_STRING) as con:
         con.execute("CREATE TABLE user_string (session_id, value)")

def cleanup_database():
     """
     Destroy the `user_string` table from the database
     on server shutdown.
     """
     with sqlite3.connect(DB_STRING) as con:
         con.execute("DROP TABLE user_string")

if __name__ == '__main__':
     conf = {
         '/': {
             'tools.sessions.on': True,
             'tools.staticdir.root': os.path.abspath(os.getcwd())
         },
         '/generator': {
             'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
             'tools.response_headers.on': True,
             'tools.response_headers.headers': [('Content-Type', 'text/plain')],
         },
         '/static': {
             'tools.staticdir.on': True,
             'tools.staticdir.dir': './public'
         }
     }

     cherrypy.engine.subscribe('start', setup_database)
     cherrypy.engine.subscribe('stop', cleanup_database)

     webapp = StringGenerator()
     webapp.generator = StringGeneratorWebService()
     cherrypy.quickstart(webapp, '/', conf)