"""
Columbia W4111 Intro to databases
Example webserver
To run locally
    python server.py
Go to http://localhost:8111 in your browser
A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, session, flash, url_for
from flask_table import Table, Col, LinkCol

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)



# XXX: The Database URI should be in the format of:
#
#     postgresql://USER:PASSWORD@<IP_OF_POSTGRE_SQL_SERVER>/<DB_NAME>
#
# For example, if you had username ewu2493, password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://ewu2493:foobar@<IP_OF_POSTGRE_SQL_SERVER>/postgres"
#
# For your convenience, we already set it to the class database

# Use the DB credentials you received by e-mail
DB_USER = "xy2378"
DB_PASSWORD = "0r30ys9i"

DB_SERVER = "w4111.cisxo09blonu.us-east-1.rds.amazonaws.com"

DATABASEURI = "postgresql://"+DB_USER+":"+DB_PASSWORD+"@"+DB_SERVER+"/w4111"


#
# This line creates a database engine that knows how to connect to the URI above
#
engine = create_engine(DATABASEURI)


# Here we create a test table and insert some values in it
#engine.execute("""DROP TABLE IF EXISTS test;""")
#engine.execute("""CREATE TABLE IF NOT EXISTS test (
  #id serial,
  #name text
#);""")
#engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")



@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request
  The variable g is globally accessible
  """
  try:
    g.conn = engine.connect()
  except:
    print("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to e.g., localhost:8111/foobar/ with POST or GET then you could use
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
#
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/')
def index():
    if 'eid' in session:
        eid = session['eid']

        # retrieve the name of the user for greeting message

        #storing sql query as a string variable protexts against sql injections (I think)
        #qname = "SELECT name FROM Users WHERE uid = %s;"
        #cursor = g.conn.execute(qname, (uid,))
        cursor = g.conn.execute("SELECT username FROM users "
                               "WHERE eid = %s", (eid,))
        name = cursor.next()[0]
        cursor.close()

        #information table
        cursor = g.conn.execute("SELECT * FROM employee_have_job WHERE eid = %s;", (session['eid'],))
        results = []
        for result in cursor:
            results.append({'eid':result['eid'],
                'name':result['name'],
                'class_year':result['class_year'],
                'major':result['major'],
                'university':result['university'],
                'education':result['education_level'],
                'linkedin':result['linkedin'],
                'job ID':result['jid'],
                'industry':result['industry'],
                'job Title':result['job_title'],
                'salary':result['salary'],
                'type':result['type'],
                'company':result['company_name']})
        cursor.close()
        table = Basicinformation(results)
        table.border = True

        return render_template('dashboard.html', table=table, name=name)
    else:
        return render_template('login.html')

##################################################################################
# login page
###################################################################################
@app.route('/login', methods=['POST'])
def login():
    USERNAME = str(request.form['username'])
    PASSWORD = str(request.form['password'])

    # check if there is matched user record in the db
    if 'eid' not in session:
        try:
            cursor = g.conn.execute("SELECT eid FROM Users "
                                   "WHERE username = %s AND "
                                  "password = %s;", (USERNAME, PASSWORD))
            session['eid'] = cursor.next()[0]
            cursor.close()
        except:
            flash('username/password not matched!')
    return index()



##################################################################################
# logout page
##################################################################################
@app.route('/logout')
def logout():
    # remove the username from the session if it's there
    session.pop('eid', None)
    return redirect(url_for('index'))



##################################################################################
# create a new user
##################################################################################
@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')

    # fetch sign-up info, all fields cannot be null.
    USERNAME = str(request.form['username'])
    PASSWORD = str(request.form['password'])
    if not (USERNAME and PASSWORD):
        flash('Data cannot be null.')
        return redirect(url_for('signup'))
    cursor = g.conn.execute("SELECT MAX(eid) FROM users;")
    curuid = cursor.next()[0] + 1
    cursor.close()
    try:
        g.conn.execute("INSERT INTO Users(eid, username,password) VALUES"
                        "(%s, %s, %s);", (curuid, USERNAME, PASSWORD))
    except:
        flash('Cannot create User.')
        return redirect(url_for('signup'))
    flash('User successfully created.')
    return redirect(url_for('index'))

#
# This is an example of a different path.  You can see it at
#
#     localhost:8111/another
#
# notice that the functio name is another() rather than index()
# the functions for each app.route needs to have different names
#
##################################################################################
# Use Flask_table module to generate html table for Tracking Account
# (third-party library)
##################################################################################
class Basicinformation(Table):
    eid = Col('eid', show=False)
    name = Col('name')
    class_year = Col('class_year')
    major = Col('major')
    university = Col('university')
    education_level = Col('education_level')
    linkedin = Col('linkedin')
    jid = Col('jid')
    industry = Col('industry')
    job_title = Col('job_title')
    salary = Col('salary')
    type = Col('type')
    company_name = Col('company_name')
    # Called edit_trackingaccount() when the link is clicked.
    edit = LinkCol('Edit', 'edit_information', url_kwargs=dict(eid='eid'))
    # Called delete_trackingaccount() when the link is clicked.
    delete = LinkCol('Delete', 'delete_information', url_kwargs=dict(eid='eid'))


##################################################################################
# add new employee
##################################################################################
@app.route('/add_information', methods=['POST', 'GET'])
def add_information():
    if request.method == 'GET':
        return render_template("add_information.html")
    eid = request.form['eid']
    name = request.form['name']
    class_year = request.form['class_year']
    major = request.form['major']
    university = request.form['university']
    education_level = request.form['education_level']
    linkedin = request.form['linkedin']
    jid = request.form['jid']
    industry = request.form['industry']
    job_title = request.form['job_title']
    salary = request.form['salary']
    type = request.form['type']
    company_name = request.form['company_name']
    if not eid or not name or not jid or not company_name:
        flash('Data should not be null.')
        return redirect(url_for('add_information'))

    # create new record in db
    print (eid, name, class_year, major, university, education_level, linkedin, jid, industry, job_title, salary, type, company_name)
    cmd = 'INSERT INTO employee_have_job VALUES (:eid1, :name1, :class1, :major1, :university1, :education_level1, :linkedin1, :jid1, :industry1, :job_title1, :salary1, :type1, :company_name1)'
    g.conn.execute(text(cmd),eid1=eid, name1=name, class1=class_year, major1=major, university1=university, education_level1=education_level, linkedin1=linkedin, jid1=jid, industry1=industry, job_title1=job_title, salary1=salary, type1=type, company_name1=company_name)
    return redirect(url_for('add_information'))


##################################################################################
# edit a tracking account
##################################################################################
@app.route('/edit_information/<int:eid>', methods=['GET', 'POST'])
def edit_information(eid):
    if request.method == 'GET':
        info = "SELECT * FROM employee_have_job WHERE eid = %s;"
        cursor = g.conn.execute(info, (eid,))
        record = cursor.next()
        cursor.close()
        return render_template("edit_information.html",
            eid = record['eid'],
            name = record['name'],
            class_year = record['class_year'],
            major = record['major'],
            university = record['university'],
            education_level = record['education_level'],
            linkedin = record['linkedin'],
            jid = record['jid'],
            industry = record['industry'],
            job_title = record['job_title'],
            salary = record['salary'],
            type = record['type'],
            company_name = record['company_name'])
    name = request.form['name']
    class_year = request.form['class_year']
    major = request.form['major']
    university = request.form['university']
    education_level = request.form['education_level']
    linkedin = request.form['linkedin']
    jid = request.form['jid']
    industry = request.form['industry']
    job_title = request.form['job_title']
    salary = request.form['salary']
    type = request.form['type']
    company_name = request.form['company_name']
    if not eid or not name or not class_year or not major or not university or not education_level or not jid or not industry or not job_title or not company_name or not type:
        flash('Data should not be null.')
        return redirect('/edit_information/{eid}'.format(eid=eid))
    cmd = 'UPDATE employee_have_job SET name=%s, class_year=%s, major=%s, university=%s,education_level=%s, linkedin=%s,jid=%s,industry=%s,job_title=%s,type=%s,company_name=%s, WHERE eid=%s;'
    g.conn.execute(cmd, (name,class_year,major,university,education_level,linkedin, jid, industry, job_title, type, company_name,eid))
    return redirect('/')


##################################################################################
# delete infomation
##################################################################################
@app.route('/delete_information/<int:aid>', methods=['GET', 'POST'])
def delete_information(eid):
    if request.method == 'GET':
        return render_template("delete_information.html", eid=eid)

    #eid = str(request.form['eid'])
    #cmd="DELETE FROM employee_have_job WHERE eid = %s;"
    g.conn.execute("DELETE FROM employee_have_job WHERE eid = %s;", (eid,))
    return redirect("/")

if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using
        python server.py
    Show the help text using
        python server.py --help
    """

    HOST, PORT = host, port
    print ("running on %s:%d" % (HOST, PORT))
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

  app.secret_key = 'supersupersupersecretkey'
  run()