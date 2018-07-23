from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField,IntegerField, validators
from passlib.hash import sha256_crypt
from functools import wraps
from flask_qrcode import QRcode
from flask_mail import Mail, Message
import smtplib
import string, os,random

  

#new upload code starts
from flask_uploads import UploadSet, configure_uploads, IMAGES
#new upload code ends

app = Flask(__name__)
QRcode(app)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'ereceipt25@gmail.com'
app.config['MAIL_PASSWORD'] = 'receipt123'
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)


#new upload code starts
photos = UploadSet('photos', IMAGES)

app.config['UPLOADED_PHOTOS_DEST'] = 'static/img'
configure_uploads(app, photos)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST' and 'photo' in request.files:
        filename = photos.save(request.files['photo'])
        flash('Successfully Uploaded !', 'success')
        return redirect(url_for('advupload'))
    return redirect(url_for('advupload'))
#new upload code ends



mail = Mail(app)

# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'flaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# init MYSQL
mysql = MySQL(app)


#Admin
@app.route('/admin')
def admin():
    return render_template('admin.html')
#login Dash
@app.route('/login')
def login():
    return render_template('login_dashboard.html')

# Index
@app.route('/')
def index():
    return render_template('home.html')
   
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap 


#View Store
@app.route('/view_store')
def store():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get articles
    result = cur.execute("SELECT * FROM store")

    articles = cur.fetchall()

    if result > 0:
        return render_template('store.html', articles=articles)
    else:
        msg = 'No Stores Found'
        return render_template('store.html', msg=msg)
    # Close connection
    cur.close()

#Select Store
@app.route('/select_store')
def select_store():
    rand =''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
    print(rand)
    # Create cursor
    cur = mysql.connection.cursor()

    # Get articles
    result = cur.execute("SELECT * FROM store")

    articles = cur.fetchall()

    if result > 0:
        return render_template('select_store.html', articles=articles,rand=rand)
    else:
        msg = 'No Stores Found'
        return render_template('select_store.html', msg=msg)
    # Close connection
    cur.close()


#pos
@app.route('/pos/<string:sid>/<string:rand>',methods=['GET','POST'])
@is_logged_in

def pos(sid,rand):
    session['rand']=rand

    form = PosForm(request.form)
    if request.method == 'POST':
        # Get Form Fields
        name = request.form['name']
        qty = request.form['qty']
       
        # Create cursor
        cur = mysql.connection.cursor()
        result = cur.execute("SELECT name FROM product WHERE sid = %s", [sid])
        names = cur.fetchall()
        total = 0
        for row in names:
            # print(row['name'])
            # print(name)
            # print(result)
            # print(names)   
            if name == row['name']:
                cur1 = mysql.connection.cursor()
                cur1.execute("select price from product where name = %s",[name])
                prices = cur1.fetchall()
              
                for value in prices:
                    print(value['price'])
                    print(qty)
                    total = float(qty) * float(value['price'])
              
                cur.execute("insert into pos(sid,name,qty,total,uid)values(%s,%s,%s,%s,%s)",(sid,name,qty,total,rand))
                cur.execute("update pos inner join product on pos.name = product.name set pos.upc = product.upc")
                cur.execute("update pos inner join product on pos.name = product.name set pos.price = product.price")
                mysql.connection.commit()
                
                cur1.close()
                cur.close()

                return redirect(url_for('add_to_list',rand=rand))
            else:
                print('else')
        flash('Product not found in store', 'danger')
        return redirect(url_for('add_to_list',rand=rand))
       
    return render_template('pos.html',form=form)

@app.route('/add_to_list/<string:rand>')
def add_to_list(rand):
    session['rand']=rand

    # Create cursor
    cur = mysql.connection.cursor()
    cur2 = mysql.connection.cursor()

    result2 = cur2.execute("select sid,name,upc,qty,price,total from pos where uid = %s",[rand])
    articles2 = cur2.fetchall()
    totalprice=0
    for i in range(result2):
        totalprice+=float(articles2[i]['total'])
        print(totalprice)
    
    cur2.close()
     # Get articles
    result = cur.execute("SELECT sid,name,upc,qty,price,total from pos where uid = %s",[rand])

    articles = cur.fetchall()

    if result > 0:
        return render_template('add_to_list.html', articles=articles , totalprice=totalprice, rand=rand)
            
    else:
        msg = 'No Products in list'
        return render_template('add_to_list.html', msg=msg)
    # Close connection
    cur.close() 
   
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

@app.route('/bill/<string:rand>')
def bill(rand):
    cur = mysql.connection.cursor()
    cur1 = mysql.connection.cursor()
    cur2 = mysql.connection.cursor()
    cur3 = mysql.connection.cursor()

    cur3.execute("select temp from storedetails sd,store s where sd.stname = s.name")
    templates = cur3.fetchall()
    for row in templates:
        chosen = row['temp']    
    print(chosen)
    
    list_images = os.listdir("static/img")
    print(list_images)
    for images in list_images:
        print(images)
    print(images)


    cur.execute("SELECT sid from pos")
    names = cur.fetchall()
      
    result = cur1.execute("select s.sid,s.name,s.code from store s,pos p where s.sid = p.sid limit 1")
    articles = cur1.fetchall()
    print(result)
    result2 = cur2.execute("select sid,name,upc,qty,price,total from pos where uid = %s",[rand])
    articles2 = cur2.fetchall()
    print(result2)
    totalprice=0
    for i in range(result2):
        totalprice+=float(articles2[i]['total'])
        print(totalprice)
    
    if result > 0 and result2 > 0 :
        return render_template('bill.html', articles=articles,articles2=articles2,totalprice=totalprice,rand=rand,images=images,chosen=chosen)
    
    else:
        msg = 'No Bill Generated'
        return render_template('qrcode.html', msg=msg)
    
    # Close connection
    cur2.close()
    cur1.close()
    cur.close() 

    return render_template('bill.html')

@app.route('/qrcode/<string:rand>', methods=['GET', 'POST'])
def qrcode(rand):
    form = PosForm(request.form)
    if request.method == 'POST':
        print('fdsfsd')
        email = form.email.data
        print(rand)

        # Create cursor
        cur = mysql.connection.cursor()
        cur1 = mysql.connection.cursor()

        # Execute query
        cur.execute("update pos set email = %s where uid = %s",(email,rand))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        cur1.execute("select email from pos where uid = %s",[rand])
        mails=cur1.fetchall()
        for row in mails:
            a = row['email']
        print(a) 
        cur1.close()

        var ='http://127.0.0.1:5000/bill/'
        code = var+rand
        print(code)
        msg = Message('Thank You For Shopping', sender = 'ereceipt25@gmail.com', recipients =[a])
        msg.body = code
        mail.send(msg)
        flash('Mail sent', 'success')        

        return render_template('qrcode.html',rand=rand,form=form)
    return render_template('qrcode.html',rand=rand,form=form)

#payment
@app.route('/<string:rand>/payment')
def payment(rand):
    return render_template('payment.html',rand=rand)

# Delete Product pos
@app.route('/delete_pos_product/<string:name>/<string:rand>/', methods=['POST'])
@is_logged_in
def delete_pos_product(name,rand):
    # Create cursor
    cur = mysql.connection.cursor()

    # Execute
    cur.execute("DELETE FROM pos WHERE name = %s", [name])

    # Commit to DB
    mysql.connection.commit()

    #Close connection
    cur.close()

    flash('Product Deleted', 'success')
    # flash('Article Deleted', 'success')

    return redirect(url_for('add_to_list',rand=rand))


# Store Details
@app.route('/template', methods=['GET', 'POST'])
def template():
    form = StoredetailsForm(request.form)
    if request.method == 'POST': 
        if form.validate():
            stname = form.stname.data
            vdname = form.vdname.data
            adname = form.adname.data
            temp = form.temp.data  
            # Create Cursor
            cur = mysql.connection.cursor()

            # Execute
            cur.execute("INSERT INTO storedetails(stname, vdname, adname,temp) VALUES(%s, %s, %s, %s)",(stname, vdname, adname,temp))
            # Commit to DB
            mysql.connection.commit()

            #Close connection
            cur.close()
            flash('Store Details', 'success')

            return redirect(url_for('store_details'))

        return render_template('template.html', form=form)
    return render_template('template.html', form=form)


@app.route('/store_details')
def store_details():
     # Create cursor
     cur = mysql.connection.cursor()

     # Get articles
     result = cur.execute("SELECT stname,vdname,adname,temp FROM storedetails")

     articles = cur.fetchall()

     if result > 0:
         return render_template('store_details.html', articles=articles)
     else:
         msg = 'No Stores Found'
         return render_template('store_details.html', msg=msg)
     # Close connection
     cur.close()    

# create store
@app.route('/create_store', methods=['GET', 'POST'])
@is_logged_in
def create_store():
    form = StoreForm(request.form)
    if request.method == 'POST' and form.validate():
        sid = form.sid.data
        name = form.name.data
        code = form.code.data
        
        # Create Cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute("INSERT INTO store(sid, name, code) VALUES(%s, %s, %s)", (sid,name, code))

        # Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash('Store Created', 'success')

        return redirect(url_for('store_dash'))

    return render_template('add_store.html', form=form)

@app.route('/store_dash')
@is_logged_in
def store_dash():
     # Create cursor
     cur = mysql.connection.cursor()

     # Get articles
     result = cur.execute("SELECT sid,name,code FROM store")

     articles = cur.fetchall()

     if result > 0:
         return render_template('store.html', articles=articles)
     else:
         msg = 'No Stores Found'
         return render_template('store.html', msg=msg)
     # Close connection
     cur.close()



#product dashboard
@app.route('/product_dash/<string:sid>')
@is_logged_in
def product_dash(sid):
    #Create Cursor
    cur = mysql.connection.cursor()

     # Get articles
    result = cur.execute("SELECT * from product where sid = %s",[sid])

    articles = cur.fetchall()
    print(result)
    if result > 0:

      return render_template('product_dashboard.html', articles=articles)
    else:
        msg = 'No Products Found'
        return render_template('product_dashboard.html', msg=msg)
     # Close connection
    cur.close()

# Register Form Class
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    contact = StringField('Contact',[validators.Length(min=10, max=32)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')

# Store Creation Form
class StoreForm(Form):
    sid = StringField('Store ID',[validators.Length(min=1,max=5)])
    name = StringField('Store Name', [validators.Length(min=1, max=50)])
    code = StringField('Store Code', [validators.Length(min=1, max=10)])

class ProductForm(Form):
    sid = StringField('Store ID', [validators.Length(min=1,max=5)])
    name = StringField('Product Name', [validators.Length(min=1,max=50)])
    upc = StringField('upc', [validators.Length(min=1,max=50)])
    stock = StringField('stock', [validators.Length(min=1,max=50)])
    price = StringField('price', [validators.Length(min=1,max=50)])
    qty = StringField('qty', [validators.Length(min=1,max=50)])    


class PosForm(Form):
    sid = StringField('Store ID', [validators.Length(min=1,max=5)])
    name = StringField('Product Name', [validators.Length(min=1,max=50)])
    uid = StringField('User Code',[validators.Length(min=1,max=50)])
    upc = StringField('upc', [validators.Length(min=1,max=50)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    price = StringField('price', [validators.Length(min=1,max=50)])    
    total = StringField('total', [validators.Length(min=1,max=50)])    
    qty = StringField('Qty', [validators.Length(min=1,max=50)])


class StoredetailsForm(Form):
    stname = StringField('Store Name',[validators.Length(min=1,max=10)])
    vdname = StringField('Vendor Name', [validators.Length(min=1, max=50)])
    adname = StringField('Advertiser Name', [validators.Length(min=1, max=50)])
    temp = StringField('Template', [validators.Length(min=1, max=10)])
    redirect = StringField('Redirect URL', [validators.Length(min=10,max=150)])


    

# User Register Admin
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        contact = form.contact.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute query
        cur.execute("INSERT INTO users(name, email, username, contact, password) VALUES(%s, %s, %s, %s, %s)", (name, email, username, contact, password))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('You are now registered and can log in', 'success')

        return redirect(url_for('admin_login'))
    return render_template('register.html', form=form)


# login Admin
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['password']

            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid login'
                return render_template('admin_login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('admin_login.html', error=error)

    return render_template('admin_login.html')

# vendor login
@app.route('/vlogin', methods=['GET', 'POST'])
def vlogin():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Create cursor
        cur = mysql.connection.cursor()
    
        # Get user by username
        result = cur.execute("SELECT * FROM vendor WHERE username = %s", [username])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['password']

            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('vendor_dashboard'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')


# employee login
@app.route('/elogin', methods=['GET', 'POST'])
def elogin():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Create cursor
        cur = mysql.connection.cursor()
    
        # Get user by username
        result = cur.execute("SELECT * FROM employee WHERE username = %s", [username])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['password']

            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('employee_dashboard'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')

# advertiser login
@app.route('/alogin', methods=['GET', 'POST'])
def alogin():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Create cursor
        cur = mysql.connection.cursor()
    
        # Get user by username
        result = cur.execute("SELECT * FROM advertiser WHERE username = %s", [username])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['password']

            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('advupload'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')


@app.route('/employee_dashboard')
@is_logged_in
def employee_dashboard():
    return render_template('employee_dashboard.html')


@app.route('/adv/upload')
@is_logged_in
def advupload():
    # Create cursor
    cur = mysql.connection.cursor()
    cur1 = mysql.connection.cursor()

    # Get articles
    result = cur.execute("SELECT stname,vdname,temp FROM storedetails s,advertiser a where s.adname = a.name")
    print('B')

    articles = cur.fetchall()
    if result > 0:
        return render_template('advupload.html', articles=articles)
    else:
        msg = 'No Stores Assigned'
        return render_template('advupload.html', msg=msg)
    
    #Close connection   
    cur.close()
  
    return render_template('advupload.html')
    
# Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

#Admin Logout
@app.route('/admin_logout')
@is_logged_in
def admin_logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('admin_login'))

# Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    return render_template('dashboard.html')
 
#vendor 2nd page
@app.route('/vendor_dashboard')
@is_logged_in
def vendor_dashboard():
    return render_template('vendor_dashboard.html')

# Vendor Dashboard
@app.route('/vendor_dash')
@is_logged_in
def vendor_dash():
     # Create cursor
     cur = mysql.connection.cursor()

     # Get articles
     result = cur.execute("SELECT id,name,contact,email FROM vendor")

     articles = cur.fetchall()

     if result > 0:
         return render_template('dashboard.html', articles=articles)
     else:
         msg = 'No Articles Found'
         return render_template('dashboard.html', msg=msg)
     # Close connection
     cur.close()



# Employee Dashboard
@app.route('/employee_dash')
@is_logged_in
def employee_dash():
     # Create cursor
     cur = mysql.connection.cursor()

     # Get articles
     result = cur.execute("SELECT id,name,contact,email FROM employee")

     articles = cur.fetchall()

     if result > 0:
         return render_template('dashboard.html', articles=articles)
     else:
         msg = 'No Articles Found'
         return render_template('dashboard.html', msg=msg)
     # Close connection
     cur.close()

# Advertiser Dashboard
@app.route('/advertiser_dash')
@is_logged_in
def advertiser_dash():
     # Create cursor
     cur = mysql.connection.cursor()

     # Get articles
     result = cur.execute("SELECT id,name,contact,email FROM advertiser")

     articles = cur.fetchall()

     if result > 0:
         return render_template('vendor_dashboard.html', articles=articles)
     else:
         msg = 'No Advertisers Found'
         return render_template('vendor_dashboard.html', msg=msg)
     # Close connection
     cur.close()

# Article Form Class
class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])
    body = TextAreaField('Body', [validators.Length(min=30)])

# Add Vendor
@app.route('/add_vendor', methods=['GET', 'POST'])
@is_logged_in
def add_vendor():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        contact = form.contact.data

        password = sha256_crypt.encrypt(str(form.password.data))

        # Create Cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute("INSERT INTO vendor(name, email, username,contact, password) VALUES(%s, %s, %s, %s, %s)", (name, email, username, contact, password))

        # Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash('Vendor Created', 'success')

        return redirect(url_for('vendor_dash'))

    return render_template('add_vendor.html', form=form)

# Add Employee
@app.route('/add_employee', methods=['GET', 'POST'])
@is_logged_in
def add_employee():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        contact = form.contact.data

        password = sha256_crypt.encrypt(str(form.password.data))

        # Create Cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute("INSERT INTO employee(name, email, username,contact, password) VALUES(%s, %s, %s, %s, %s)", (name, email, username, contact, password))

        # Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash('Employee Created', 'success')

        return redirect(url_for('employee_dash'))

    return render_template('add_employee.html', form=form)


# Add Advertiser
@app.route('/add_advertiser', methods=['GET', 'POST'])
@is_logged_in
def add_advertiser():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        contact = form.contact.data

        password = sha256_crypt.encrypt(str(form.password.data))

        # Create Cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute("INSERT INTO advertiser(name, email, username,contact, password) VALUES(%s, %s, %s, %s, %s)", (name, email, username, contact, password))

        # Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash('Advertiser Created', 'success')

        return redirect(url_for('advertiser_dash'))

    return render_template('add_advertiser.html', form=form)   


# Add Article
@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        # Create Cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute("INSERT INTO articles(title, body, author) VALUES(%s, %s, %s)",(title, body, session['username']))

        # Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash('Article Created', 'success')

        return redirect(url_for('dashboard'))

    return render_template('add_article.html', form=form)

# Edit Advertiser
@app.route('/edit_advertiser/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_advertiser(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get article by id
    result = cur.execute("SELECT * FROM advertiser WHERE id = %s", [id])
    # result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()
    cur.close()
    # Get form
    form = RegisterForm(request.form)

    # Populate article form fields
    form.name.data = article['name']
    form.email.data = article['email']
    form.contact.data = article['contact']

    if request.method == 'POST':
        print('121324')
        if 1:
            print('dfhuidhfd') 
            name = request.form['name']
            email = request.form['email']
            contact = request.form['contact']
            # Create Cursor
            cur1 = mysql.connection.cursor()
            # app.logger.info(name)
            # Execute
            
            cur1.execute ("update advertiser set name=%s, contact=%s, email=%s WHERE id=%s", (name, contact, email, id))
            # Commit to DB
            mysql.connection.commit()

            #Close connection
            cur.close()
        

            flash('Advertiser Updated', 'success')

            return redirect(url_for('advertiser_dash'))
        return render_template('edit_article.html', form=form)
    return render_template('edit_article.html', form=form)


# Edit Article
@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get article by id
    result = cur.execute("SELECT * FROM vendor WHERE id = %s", [id])
    # result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()
    cur.close()
    # Get form
    form = RegisterForm(request.form)

    # Populate article form fields
    form.name.data = article['name']
    form.email.data = article['email']
    form.contact.data = article['contact']

    if request.method == 'POST' and form.validate():
        name = request.form['name']
        email = request.form['email']
        contact = request.form['contact']
        # Create Cursor
        cur = mysql.connection.cursor()
        # app.logger.info(name)
        # Execute
        cur.execute ("update vendor set name=%s, contact=%s, email=%s, WHERE id=%s", (name, contact, email, id))
        # Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash('Vendor Updated', 'success')

        return redirect(url_for('advertiser_dash'))

    return render_template('edit_article.html', form=form)

# Delete Advertiser
@app.route('/delete_advertiser/<string:id>', methods=['POST'])
@is_logged_in
def delete_advertiser(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Execute
    cur.execute("DELETE FROM advertiser WHERE id = %s", [id])

    # Commit to DB
    mysql.connection.commit()

    #Close connection
    cur.close()

    flash('Advertiser Deleted', 'success')
    # flash('Article Deleted', 'success')

    return redirect(url_for('advertiser_dash'))

# Delete Article
@app.route('/delete_product/<string:sid>/<string:name>', methods=['POST'])
@is_logged_in
def delete_product(sid,name):
    # Create cursor
    cur = mysql.connection.cursor()

    # Execute
    cur.execute("DELETE FROM product WHERE name = %s", [name])

    # Commit to DB
    mysql.connection.commit()

    #Close connection
    cur.close()

    flash('Product Deleted', 'success')
    # flash('Article Deleted', 'success')

    return redirect(url_for('product_dash',sid=sid))

if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)
