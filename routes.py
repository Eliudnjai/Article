from flask import Flask,url_for,render_template,request,redirect,flash,logging,session
from app import app
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps


from app import app

def is_logged_in(f):
    @wraps(f)
    def wrap(*args,**kwargs):
        if 'logged_in'in session:
            return f(*args,**kwargs)
        else:
            return redirect(url_for('login'))
    return wrap



#config db
app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='root'
app.config['MYSQL_PASSWORD']='Eliud0715'
app.config['MYSQL_DB']='myflaskapp'
app.config['MYSQL_CURSORCLASS']='DictCursor'

app.secret_key='Eliud09774674828487483743874387438748347834'
#intialize sql
mysql=MySQL(app)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

#passing the articles
@app.route('/articles')
@is_logged_in
def articles(): 
    #connect to database
    cur=mysql.connection.cursor()

    #execute
    results=cur.execute("SELECT * FROM articles")

    #fetchall
    articles=cur.fetchall()

    if results > 0:
        return render_template('articles.html',articles=articles)
    else:
        msg='Articles not found'
        return render_template('articles.html',msg=msg)
    
    #close connection
    cur.close()

#passing the id
@app.route('/article/<string:id>')
@is_logged_in
def route(id):
    
    #create cursor
    cur=mysql.connection.cursor()

    result=cur.execute('SELECT * FROM articles WHERE id=%s',[id])

    article=cur.fetchone()
    
    return render_template('article.html',article=article)



#create a form
class RegisterForm(Form):
    name=StringField('Name',[validators.Length(min=1,max=20)])
    email=StringField('Email',[validators.Length(min=5,max=50)])
    username=StringField('Username',[validators.Length(min=5,max=20)])
    password=PasswordField('Password',[
        validators.DataRequired(),
        validators.EqualTo('confirm',message='passwords do not match')
    ])
    confirm=PasswordField('Confirm password')

#create register route
@app.route('/register',methods=['GET','POST'])
def register():
    form=RegisterForm(request.form)
    if request.method=='POST' and form.validate():
        name=form.name.data
        email=form.email.data
        username=form.username.data
        password=sha256_crypt.encrypt(str(form.password.data))

        #creat a cursor
        cur=mysql.connection.cursor()

        cur.execute("INSERT INTO users(name,email,username,password)VALUES(%s,%s,%s,%s)",(name,email,username,password))
        #commit
        mysql.connection.commit()

        #close connection
        cur.close()

        flash('you are now registered ','success')

        return redirect(url_for('login'))

    
    return render_template('register.html',form=form)
    
#user login
@app.route('/login',methods=["POST","GET"])
def login():
    if request.method=='POST':
        #get form fields
        username=request.form['username']
        password_candidate=request.form['password']

        #create a cursor
        cur=mysql.connection.cursor()
        #get the user from the database
        result=cur.execute("SELECT * FROM users WHERE username=%s",[username])
        #if statement
        if result > 0:
            data=cur.fetchone()
            password=data['password']
    
            #compare passwords using sha256
            if sha256_crypt.verify(password_candidate,password):
                #passed and session
                session['logged_in']=True
                session['username']=username

                return redirect(url_for('dashboard'))
                #first error return error invalid login and close conn.
            else:
                error='invalid login'
                return render_template('login.html',error=error)

            cur.close()
            #return error user not found then return login.html
        else:
            error='user not found'
            return render_template('login.html',error=error)

    return render_template('login.html')

#check if user logged in by using decorators:
def is_logged_in(f):
    @wraps(f)
    def wrap(*args,**kwargs):
        if 'logged_in'in session:
            return f(*args,**kwargs)
        else:
            return redirect(url_for('login'))
    return wrap


@app.route('/logout')
@is_logged_in
def logout():
    #clear session
    session.clear()
    return redirect(url_for('login'))
 

 
@app.route('/dashboard')
@is_logged_in
def dashboard():
    
    #create a cursor
    cur=mysql.connection.cursor()

    #get the articles
    result=cur.execute("SELECT * from articles")

    articles=cur.fetchall()

    #if statement
    if result > 0:
        return render_template('dashboard.html',articles=articles)
    else:
        msg='No Articles Found'
        return render_template('dashboard.html',msg=msg)  

    #close cur
    cur.close()

#articles form class
class articleForm(Form):
    title=StringField('Title',[validators.Length(min=1,max=200)])
    body=TextAreaField('Body',[validators.Length(min=5)])

#create route for add articles
@app.route('/add_articles',methods=['GET','POST'])
@is_logged_in
def add_articles():
    form=articleForm(request.form)

    if request.method=='POST' and form.validate():
        title=form.title.data
        body=form.body.data

        #create cursor
        cur=mysql.connection.cursor()

        #excute
        cur.execute("INSERT INTO articles(title,body,author)VALUES(%s,%s,%s)",(title,body,session["username"]))

        #commit
        mysql.connection.commit()

        #close the connection.
        cur.close()

        #redirect
        flash('Article created','success')

        return redirect(url_for('dashboard'))
    return render_template('add_articles.html',form=form)

#Edit Article.
@app.route('/edit_article/<string:id>',methods=['POST','GET'])
@is_logged_in
def edit_article(id):
    #create a cursor
    cur=mysql.connection.cursor()

    #execute the query getting article by id.
    result=cur.execute("SELECT * FROM articles WHERE id=%s",[id])

    articles=cur.fetchone()

    #get the form
    form=articleForm(request.form)
    

    #populate the fields
    form.title.data=articles['title']
    form.body.data=articles['body']

    if request.method=='POST' and form.validate():
        title=request.form['title']
        body=request.form['body']
        #create a cursor
        cur=mysql.connection.cursor()

        cur.execute("UPDATE articles SET title=%s,body=%s WHERE id=%s",(title,body,id))

        #commit 
        mysql.connection.commit()

        #close
        cur.close()

        flash('Article updated','success')

        return redirect(url_for('dashboard'))
    return render_template('edit_articles.html',form=form)


#delete article
@app.route('/delete_article/<string:id>',methods=['POST'])
@is_logged_in
def delete_article(id):
    
    #create a cursor
    cur=mysql.connection.cursor()

    #execute
    cur.execute("DELETE FROM articles where id=%s",[id])

    #commit
    mysql.connection.commit()

    #close
    cur.close()

    flash('Article delete','success')

    return redirect(url_for('dashboard'))




    
    



        
        

    
      
    


    



    

