from flask import Flask, render_template, url_for, flash, redirect, request
from forms import RegistrationForm, LoginForm
from pymysql.cursors import DictCursor
from datetime import datetime
import pymysql.cursors

app = Flask(__name__)
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
db = pymysql.connect(host='localhost', user='newuser', password='password123', database='customer', cursorclass=DictCursor)
cursor = db.cursor()
now = datetime.now()

#variables and dictionaries
loginstate = False
adminstate = False
adminbox = 'n'
session = {
            'ID':'',
            'name':'',
            'email':'',
            'password':''}
result = {
            'AID':'',
            'UID':'',
            'name':'',
            'email':'',
            'password':'',
}

#index and default page
@app.route("/")
@app.route("/index")
def index():
    global loginstate
    global session
    udisplay = ''
    #get username from dictionary
    if loginstate == True:
        udisplay = session['name']
    return render_template('index.html',loginstate=loginstate, userdisplay=udisplay)
    

#about page
@app.route("/about")
def about():
    global loginstate
    return render_template('about.html', title='About',loginstate=loginstate)

#shop page
@app.route("/shop",methods=["GET","POST"])
def shop():
    global loginstate
    global session
    global cursor
    if loginstate:
        print(loginstate)
    else:
        flash('please login to gain access to table booking', 'danger')
    sql = "SELECT * FROM shop"
    cursor.execute(sql)
    shoplist=cursor.fetchall()
    #Booking submission
    #Variables:
    #bshopid-shop id
    #buserid-user id
    #btime-booking time
    if request.method == "POST":
        try:
            bshopid = request.form.get("bsid")
            bdate = request.form.get("bdate")
            bmonth = request.form.get("bmonth")
            btime = request.form.get("btime")
            buserid = session['ID']
        except:
            flash('Error,please re-submit', 'danger')
            return render_template('shop.html', title='Shop list', shoplist=shoplist, loginstate=loginstate)
        sql = "SELECT SID FROM shop WHERE SID=(%s)"
        cursor.execute(sql,(bshopid))
        result = cursor.fetchone()
        #validate shop id
        try:result['SID']
        except: 
            flash('Invalid Shop ID', 'danger')
            return render_template('shop.html', title='Shop list', shoplist=shoplist, loginstate=loginstate)
        #time verification
        #bdate,bmonth are user input
        #day, month system input
        day = now.strftime("%d")
        month = now.strftime("%m")
        year = now.strftime("%Y")

        #remove leading 0
        month = month.lstrip("0")
        day = day.lstrip("0")

        #date verification
        print(month,bmonth)
        if month > bmonth:
            flash('Invalid month', 'danger')
            return render_template('shop.html', title='Shop list', shoplist=shoplist, loginstate=loginstate)

        #if the booking is within this month
        if month == bmonth:
            if day > bdate:
                flash('Invalid date', 'danger')
                return render_template('shop.html', title='Shop list', shoplist=shoplist, loginstate=loginstate)
            try:
                sql = "INSERT INTO booking (UID,SID,Time,date,month,year) VALUES (%s,%s,%s,%s,%s,%s)"
                cursor.execute(sql,(buserid,bshopid,btime,bdate,bmonth,year))
                db.commit()
                flash('Order complete!', 'success')
                return render_template('index.html')
            except:
                flash('Order failed, please resubmit', 'danger')
                return render_template('shop.html', title='Shop list', shoplist=shoplist, loginstate=loginstate)

        #if the booking is made after this month
        try:
            sql = "INSERT INTO booking (UID,SID,Time,date,month,year) VALUES (%s,%s,%s,%s,%s,%s)"
            cursor.execute(sql,(buserid,bshopid,btime,bdate,bmonth,year))
            db.commit()
            flash('Order complete!', 'success')
            return render_template('index.html')
        except:
            flash('Order failed, please resubmit', 'danger')
            return render_template('shop.html', title='Shop list', shoplist=shoplist, loginstate=loginstate)
    return render_template('shop.html', title='Shop list', shoplist=shoplist, loginstate=loginstate)

#account registration
@app.route("/register", methods=['GET', 'POST'])
def register():
    global cursor
    form = RegistrationForm()
    if request.method == "POST" and form.validate_on_submit():
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        #check if email already used in system
        sql = "SELECT * FROM users WHERE email=(%s)"
        cursor.execute(sql,(email))
        emailcheck = cursor.fetchone()
        #if email is not present
        if emailcheck == None:
            sql = "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)"
            cursor.execute(sql,(username, email, password))
            db.commit()
            flash(f'Account created for {form.username.data}!', 'success')
            return redirect(url_for('index'))
        #if email already used
        else:
            flash(f'Email already registered!', 'danger')
    return render_template('register.html', title='Register',form=form ,loginstate=loginstate)

@app.route("/login", methods=['GET', 'POST'])
def login():
    global session
    global loginstate
    global adminstate
    global result
    form = LoginForm()
    if form.validate_on_submit():
        #clearing previous users's detials
        session = {
            'ID':'',
            'name':'',
            'email':'',
            'password':''}
        #resetting checkbox initial state
        adminbox = 'n'

        email = request.form["email"]
        password = request.form["password"]
        #admin checkbox check
        try:
            adminbox = request.form["admin"]
        #non admin login
        except:
            adminbox = 'n'
        if adminbox == 'y':
            sql = "SELECT * FROM admin WHERE email=(%s)"
            cursor.execute(sql,(email))
            result = cursor.fetchone()

            try:
                session['ID'] = result['AID']
                session['name'] = result['username']
                session['email'] = result['email']
                session['password'] = result['password']
            except :
                adminbox = 'n'
            #successful admin login
            if password == session['password']:
                loginstate = True
                adminstate = True
                flash('You have been logged in as administrator!', 'success')
                return redirect(url_for('admin',session=session))
            #failed admin login
            else:
                session.pop('ID',None)
                session.pop('name',None)
                session.pop('email',None)
                session.pop('password',None)
                loginstate = False
                flash('Failed to log in as administrator!', 'danger')
                return redirect(url_for('login'))
        if adminbox == 'n':        
            sql = "SELECT * FROM users WHERE email=(%s)"
            cursor.execute(sql,(email))
            result = cursor.fetchone()
            
            try:
                session['ID'] = result['UID']
                session['name'] = result['username']
                session['email'] = result['email']
                session['password'] = result['password']
            except:
                flash('Login Unsuccessful. Please check username and password', 'danger')
                return render_template('login.html', title='Login',form=form ,loginstate=loginstate)
            try:
                if password == session['password']:
                    loginstate = True
                    flash('You have been logged in!', 'success')
                    print(loginstate)
                    return redirect(url_for('index',loginstate=loginstate))
                else:
                    session.pop('ID',None)
                    session.pop('name',None)
                    session.pop('email',None)
                    session.pop('password',None)
                    loginstate = False
                    flash('Login Unsuccessful. Please check username and password', 'danger')
                    return render_template('login.html', title='Login',form=form,loginstate=loginstate),
            except:
                flash('Login Unsuccessful. Please check username and password', 'danger')            
    return render_template('login.html', title='Login',form=form,loginstate=loginstate)

@app.route("/logout", )
def logout():
    global session
    global loginstate
    global adminstate
    if loginstate == True:
        session.pop('ID',None)
        session.pop('name',None)
        session.pop('email',None)
        session.pop('password',None)
        loginstate = False
        adminstate = False
        flash('Logout successful.', 'success')
    else:
        flash('You are currently not logged in.', 'danger')
    return render_template('index.html',loginstate=loginstate)

@app.route("/account", methods=["GET"])
def account():
    global session
    global loginstate
    global adminstate
    global cursor
    if adminstate == True:
        flash('Please use admin for all details.', 'danger')
        return redirect(url_for('admin',loginstate=loginstate))
    #Determine if user is logged in
    if loginstate == True:
        login = "true"
        UID= session['ID']
        sql = "SELECT UID, username, email FROM users WHERE UID=(%s)"
        cursor.execute(sql,(UID))
        account=cursor.fetchone()
        sql = "SELECT * FROM booking WHERE UID=(%s)"
        cursor.execute(sql,(UID))
        bookinglist=cursor.fetchall()
    #If user is not logged in
    else:
        login = "false"
        flash('You are currently not logged in, please login to access personal detials', 'danger')
        return redirect(url_for('index'))
    return render_template('account.html',bookinglist=bookinglist, account=account, loginstate=loginstate, login=login)

    #default template

@app.route("/admin",)
def admin():
    global session
    global loginstate
    global adminstate
    if loginstate == True and adminstate == True:
        return render_template('admin.html',loginstate=loginstate)
    else:
        flash('Please login as admin before proceding', 'danger')
    return render_template('index.html',loginstate=loginstate)

@app.route("/adminaddshop",methods=["GET","POST"])
def adminaddshop():
    global cursor
    global loginstate
    if request.method == "POST":
        try:   
            shopn = request.form.get("shopn")
            shopw = request.form.get("shopw")
            sql = "INSERT INTO shop (Shopname, Shopwebsite) VALUES (%s, %s)"
            cursor.execute(sql,(shopn,shopw))
            db.commit()
            flash('Shop added successfully', 'success')
            return render_template('adminaddshop.html',loginstate=loginstate)
        except:
            flash('Please re-enter data', 'danger')
            return render_template('adminaddshop.html',loginstate=loginstate)
    return render_template('adminaddshop.html',loginstate=loginstate)

@app.route("/adminview")
def adminview():
    global loginstate
    sql = "SELECT * FROM users"
    cursor.execute(sql)
    userlist=cursor.fetchall()
    sql = "SELECT * FROM shop"
    cursor.execute(sql)
    shoplist=cursor.fetchall()
    return render_template('adminview.html',userlist=userlist,shoplist=shoplist,loginstate=loginstate)

@app.route("/bookingview")
def bookingview():
    global loginstate
    sql = "SELECT * FROM booking"
    cursor.execute(sql)
    bookinglist=cursor.fetchall()
    return render_template('bookingview.html',bookinglist=bookinglist,loginstate=loginstate)


@app.route("/home")
def home():
    global adminstate
    return render_template('home.html')
        
if __name__ == '__main__':
    app.run(debug=True)