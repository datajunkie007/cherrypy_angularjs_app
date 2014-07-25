import cherrypy 
import MySQLdb 
import os, os.path
import random
import string
from lib import html_table_lib as HTML
import ast


 
def connect(thread_index): 
    # Create a connection and store it in the current thread 
    cherrypy.thread_data.db = MySQLdb.connect('mysqlhost.com', 'user', 'user', 'db') 
 
# Tell CherryPy to call "connect" for each thread, when it starts up 
cherrypy.engine.subscribe('start_thread', connect)

# utility function for ordering status
def orderfunc(subdict):
    key, value = subdict
    if key in ['env_id', 'overall_status']:
        return 1
    else:
        return value['STATUS_ORDER']

def get_env_status(rows):
    table_data = []
    header=['ID','Env Name','DB Type','Db Name','Release Version','Install Type','File Name','File Size','Status','Install Date','SVN Version']

    for row in rows:
        table_data.append(row)
    htmlcode = HTML.table(table_data,header_row=header)
    return htmlcode


def get_idrp_status_table(statusrows):
    t = HTML.Table(header_row=['Job Name', 'Status', "Description"])
    op = ast.literal_eval(statusrows)
    sorted_status = sorted(op.items(), key=orderfunc)
    start_category = "pipeline"
    cat_col1 = HTML.TableCell(start_category.title(), bgcolor='Cornsilk',style="font-weight:bold;")
    cat_col2 = HTML.TableCell("", bgcolor='Cornsilk')
    cat_col3 = HTML.TableCell("", bgcolor='Cornsilk')
    t.rows.append([cat_col1, cat_col2, cat_col3])
    for status in sorted_status:
        if status not in ('env_id', 'overall_status'):
            try:
                job_name = status[0]
                status_detail = ast.literal_eval(str(status[1]))
                status_code = status_detail['status']
                description = status_detail['status_description']
                category = status_detail['STATUS_CATEGORY']
                colored_cell = HTML.TableCell(' ', bgcolor=status_code)
                if start_category == category:
                    t.rows.append([job_name, colored_cell, description])
                else:
                    start_category = category
                    cat_col1 = HTML.TableCell(start_category.title(), bgcolor='Cornsilk',style="font-weight:bold;")
                    t.rows.append([cat_col1, cat_col2, cat_col3])
                    t.rows.append([job_name, colored_cell, description])
            except Exception:
                pass    
    htmlcode = str(t)
    #print htmlcode
    return htmlcode

 
class DRPStatusDashboard(object):
    @cherrypy.expose
    def generate(self, length=8):
        some_string = ''.join(random.sample(string.hexdigits, int(length)))
        cherrypy.session['mystring'] = some_string
        return some_string

    @cherrypy.expose
    def idrp_status(self):
        # Sample page that displays the number of records in "table" 
        # Open a cursor, using the DB connection for the current thread 
        c = cherrypy.thread_data.db.cursor() 
        c.execute('select status_text from status_cache order by id desc limit 1') 
        rows = c.fetchone()
        c.close() 
        status_data =  rows[0]
        status_dict = ast.literal_eval(status_data)
        env_id = status_dict['env_id']
        overall_status = status_dict['overall_status']
        htmltext = "<html><body><h3>Env:%s<p>Status:%s</h3><p>" % (env_id,overall_status)
        htmltext = htmltext +  get_idrp_status_table(rows[0])
        htmltext = htmltext  + "</body></html>"
        return htmltext

    
    @cherrypy.expose
    def index(self): 
        # Sample page that displays the number of records in "table" 
        # Open a cursor, using the DB connection for the current thread 
        c = cherrypy.thread_data.db.cursor() 
        c.execute('select * from iad_schema_metadata') 
        rows = c.fetchall()
        c.close() 
        htmlcode =  "<html><body><h3>Env:%s<p>Host:%s</h3><p>" % ('VDE','myhost.com')
        htmlcode = htmlcode + "<p><h3><a href=\"/idrp_status\">Status</a></h3>"
        htmlcode = htmlcode + get_env_status(rows)
        htmlcode = htmlcode  + "</body></html>"
        return htmlcode



if __name__ == '__main__':
     conf = {
         '/': {
             'tools.sessions.on': True,
             'tools.staticdir.root': os.path.abspath(os.getcwd())
         },
         '/static': {
             'tools.staticdir.on': True,
             'tools.staticdir.dir': './public'
         }
     }
     cherrypy.quickstart(DRPStatusDashboard(), '/', conf) 
