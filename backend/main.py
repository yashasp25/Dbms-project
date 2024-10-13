from flask import Flask,redirect,render_template,flash,request,session
from flask.globals import request
from flask.helpers import url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from flask_login import UserMixin
from flask_login import login_required,logout_user,login_user,login_manager,LoginManager,current_user
from werkzeug.security import generate_password_hash,check_password_hash
import json
from flask_mail import Mail
from functools import wraps
import re

#my app initialization
local_server = True
app = Flask(__name__)
app.secret_key="yashasp"



with open('config.json','r') as e:
    params=json.load(e)["params"]


#set login manager(for getting unique user access)
login_manager=LoginManager(app)
login_manager.login_view='login'

#actual connection initi sqlalkemy object
# app.config['SQLALCHEMY_DATABASE_URI']='mysql://username:password@localhost/datbasename'
app.config['SQLALCHEMY_DATABASE_URI']='mysql://root:@localhost/bedslot'
db=SQLAlchemy(app)#telling what all

#to keep track of user

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id)) or Hospitaluser.query.get(int(user_id))


#test model
class Test(db.Model):
    id=db.Column(db.Integer(),primary_key=True)
    name=db.Column(db.String(40))

#model
class User(UserMixin,db.Model):
    id=db.Column(db.Integer,primary_key=True)
    srfid=db.Column(db.String(20),unique=True)
    email=db.Column(db.String(20))
    dob=db.Column(db.String(1000))

#model
class Hospitaluser(UserMixin,db.Model):  # This maps your model to the 'hospitaluser' table in the database
    id=db.Column(db.Integer,primary_key=True)
    code=db.Column(db.String(20))
    email=db.Column(db.String(200))
    password=db.Column(db.String(1000))
    def get_id(self):
        return str(self.id)

class Hospitaldata(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    code=db.Column(db.String(20),unique=True)
    hname=db.Column(db.String(100))
    normalbeds=db.Column(db.Integer)
    hicubeds=db.Column(db.Integer)
    icubeds=db.Column(db.Integer)
    vbeds=db.Column(db.Integer)

class Trig(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    code=db.Column(db.String(20))
    normalbeds=db.Column(db.Integer)
    hicubeds=db.Column(db.Integer)
    icubeds=db.Column(db.Integer)
    vbeds=db.Column(db.Integer)
    querys=db.Column(db.String(20))
    date=db.Column(db.String(20))

class Booking(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    srfid=db.Column(db.String(20),unique=True)
    bedtype=db.Column(db.String(40))
    code=db.Column(db.String(20))
    spo2=db.Column(db.Integer)
    pname=db.Column(db.String(40))
    pphone=db.Column(db.Integer)
    paddress=db.Column(db.String(40))

# Email validation function
def is_valid_email(email):
    regex = r'^\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    if re.match(regex, email):
        return True
    else:
        return False

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/trigers")
def trigers():
    query=Trig.query.all()
    return render_template("trigers.html",query=query)

@app.route("/signup", methods=['POST', 'GET'])
def signup():
    if request.method == "POST":
        srfid = request.form.get('srf')
        email = request.form.get('email')
        dob = request.form.get('dob')

        if not is_valid_email(email):
            flash("Invalid email address", "warning")
            return render_template("usersignup.html")

        encpassword = generate_password_hash(dob)
        user = User.query.filter_by(srfid=srfid).first()
        emailUser = User.query.filter_by(email=email).first()
        
        if user or emailUser:
            flash("Email or SRF ID already exists", "warning")
            return render_template("usersignup.html")
        
        # Creating a new user instance
        new_user = User(srfid=srfid, email=email, dob=encpassword)
        # Adding the new user to the database session
        db.session.add(new_user)
        # Committing the transaction to the database
        db.session.commit()
        
        # Direct access without login page
        user1 = User.query.filter_by(srfid=srfid).first()
        if user1 and check_password_hash(user1.dob, dob):
            login_user(user1)
            flash("SignIn Success", 'success')
            return render_template('index.html')

    return render_template('usersignup.html')

@app.route("/login",methods=['POST','GET'])
def login():
    if request.method=="POST":
        srfid=request.form.get('srf')
        dob=request.form.get('dob')
        user=User.query.filter_by(srfid=srfid).first()

        if user and check_password_hash(user.dob,dob):
            login_user(user)
            flash("Login Success","info")
            return render_template("index.html")
        else:
            flash("Invalid Credentials","danger")
            return render_template("userlogin.html")

    return render_template('userlogin.html')

#hospital login
@app.route("/hospitallogin",methods=['POST','GET'])
def hospitallogin():
    if request.method=="POST":
        email=request.form.get('email')
        password=request.form.get('password')
        user=Hospitaluser.query.filter_by(email=email).first()
        if not is_valid_email(email):
            flash("Invalid email address", "warning")
            return render_template("hospitallogin.html")

        if user and check_password_hash(user.password,password):
            login_user(user)
            flash("Login Success","info")
            return redirect('/addhospitalinfo')
        else:
            flash("Invalid Credentials","danger")
            return render_template("hospitallogin.html")

    return render_template('hospitallogin.html')


#admin login
@app.route("/admin",methods=['POST','GET'])
def admin():
    if request.method=="POST":
        username=request.form.get('username')
        password=request.form.get('password')
        if (username==params['user'] and password==params['password']):
            session['user']=username
            flash("Login success","info")
            return render_template("addHosUser.html")
        else:
            flash("Invalid Credentials","danger")

    return render_template('admin.html')

#this session makes- can only be accesed when admin is logged in
@app.route("/addhospitalUser",methods=['POST','GET'])
def hospitalUser():
    if('user' in session and session['user']==params['user']):
        if request.method=="POST":
            code=request.form.get('code')
            email=request.form.get('email')
            password=request.form.get('password')
            code=code.upper()
            encpassword=generate_password_hash(password)
            if not is_valid_email(email):
                flash("Invalid email address", "warning")
                return render_template("addHosUser.html")
            # code=Hospitaluser.query.filter_by(code=code).first()
            emailUser=Hospitaluser.query.filter_by(email=email).first()
            if emailUser:
                flash("Email already exist","Warning")

        # Creating a new user instance
            new_hos_user = Hospitaluser(code=code, email=email, password=encpassword)
            # Adding the new user to the database session
            db.session.add(new_hos_user)
            # Committing the transaction to the database
            db.session.commit()
#sending data to email   #First argument=(subject) 2nd argument=(sender)
            flash("Data sent and inserted succesfully","warning")
            return render_template("addHosUser.html")
    else:
        flash("Login and try Again","warning")
        return redirect('/admin')


#logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logout Successfull","info")
    return redirect(url_for('login'))


#testing connection
@app.route("/test")
def test():
    em=current_user.email
    print(em)
    try:
        a=Test.query.all()
        print(a)
        return 'Mydatabase is connected'
    except Exception as e:
        print(e)
        return 'My database is not connected'
    
@app.route("/logoutadmin")
def logoutadmin():
    session.pop('user')
    flash("You are logged out admin","primary")
    return redirect('/admin')

@app.route("/addhospitalinfo", methods=['POST', 'GET'])
# @login_required
def addhospitalinfo():
    email = current_user.email
    posts = Hospitaluser.query.filter_by(email=email).first()

    if posts is None:
        flash("User data not found", "danger")
        return redirect("/hospitallogin")  # Redirect to login page or handle as appropriate

    code = posts.code
    postsdata = Hospitaldata.query.filter_by(code=code).first()

    if request.method == "POST":
        code = request.form.get('code')
        hname = request.form.get('hname')
        nbed = request.form.get('normalbeds')
        hbed = request.form.get('hicubeds')
        ibed = request.form.get('icubeds')
        vbed = request.form.get('vbeds')
        code = code.upper()
        
        huser = Hospitaluser.query.filter_by(code=code).first()
        hduser = Hospitaldata.query.filter_by(code=code).first()
        
        if hduser:
            flash("Data is already present, you can update", "primary")
            return render_template("hospitaldata.html")
        
        if huser:
            new_hos_data = Hospitaldata(code=code, hname=hname, normalbeds=nbed, hicubeds=hbed, icubeds=ibed, vbeds=vbed)
            db.session.add(new_hos_data)
            db.session.commit()
            flash("Data is added", "primary")
            return redirect("/addhospitalinfo")
        else:
            flash("Hospital code doesn't exist", "warning")
    
    return render_template("hospitaldata.html", postsdata=postsdata)


@app.route("/hedit/<string:id>", methods=['POST', 'GET'])
@login_required
def hedit(id):
    posts=Hospitaldata.query.filter_by(id=id).first()
    if request.method == "POST":
        hname = request.form.get('hname')
        nbed = request.form.get('normalbeds')
        hbed = request.form.get('hicubeds')
        ibed = request.form.get('icubeds')
        vbed = request.form.get('vbeds')
        hospital = Hospitaldata.query.filter_by(id=id).first()
        if hospital:
            hospital.hname = hname
            hospital.normalbeds = nbed
            hospital.hicubeds = hbed
            hospital.icubeds = ibed
            hospital.vbeds = vbed
            db.session.commit()
            flash('Hospital data updated successfully', 'success')
            return redirect('/addhospitalinfo')
    return render_template("hedit.html",posts=posts)

@app.route("/hdelete/<string:id>", methods=['POST', 'GET'])
@login_required
def hdelete(id):
    post = Hospitaldata.query.filter_by(id=id).first()
    if post:
        db.session.delete(post)
        db.session.commit()
        flash('Hospital data deleted successfully', 'success')
        return redirect('/addhospitalinfo')
    else:
        flash('Hospital data not found', 'error')
        return redirect('/addhospitalinfo')

@app.route("/pdetails",methods=['GET'])
@login_required
def pdetails():
    code=current_user.srfid
    print(code)
    data=Booking.query.filter_by(srfid=code).first()
    return render_template("details.html",data=data)

#slotbooking
@app.route("/slotbooking",methods=['POST','GET'])
@login_required
def slotbooking():
    query1=Hospitaldata.query.all()
    query=Hospitaldata.query.all()
    if request.method=="POST":
        
        srfid=request.form.get('srfid')
        bedtype=request.form.get('bedtype')
        code=request.form.get('code')
        spo2=request.form.get('spo2')
        pname=request.form.get('pname')
        pphone=request.form.get('pphone')
        paddress=request.form.get('paddress')  
        check2=Hospitaldata.query.filter_by(code=code).first()
        checkpatient=Booking.query.filter_by(srfid=srfid).first()
        if checkpatient:
            flash("already srfid is registered ","warning")
            return render_template("booking.html",query=query,query1=query1)
        
        if not check2:
            flash("Hospital Code not exist","warning")
            return render_template("booking.html",query=query,query1=query1)

        
        dbb=Hospitaldata.query.filter_by(code=code).all()      
        bedtype=bedtype
        if bedtype=="Normalbed":       
            for d in dbb:
                seat=d.normalbeds
                print(seat)
                ar=Hospitaldata.query.filter_by(code=code).first()
                ar.normalbeds=seat-1
                db.session.commit()
                
            
        elif bedtype=="HICUbed":      
            for d in dbb:
                seat=d.hicubeds
                print(seat)
                ar=Hospitaldata.query.filter_by(code=code).first()
                ar.hicubeds=seat-1
                db.session.commit()

        elif bedtype=="ICUbed":     
            for d in dbb:
                seat=d.icubeds
                print(seat)
                ar=Hospitaldata.query.filter_by(code=code).first()
                ar.icubeds=seat-1
                db.session.commit()

        elif bedtype=="Ventilatorbed": 
            for d in dbb:
                seat=d.vbeds
                ar=Hospitaldata.query.filter_by(code=code).first()
                ar.vbeds=seat-1
                db.session.commit()
        else:
            pass

        check=Hospitaldata.query.filter_by(code=code).first()
        if check!=None:
            if(seat>0 and check):
                res=Booking(srfid=srfid,bedtype=bedtype,code=code,spo2=spo2,pname=pname,pphone=pphone,paddress=paddress)
                db.session.add(res)
                db.session.commit()
                flash("Slot is Booked kindly Visit Hospital for Further Procedure","success")
                # return render_template("booking.html",query=query,query1=query1)
            else:
                flash("Something Went Wrong","danger")
                # return render_template("booking.html",query=query,query1=query1)
        else:
            flash("Give the proper hospital Code","info")
            # return render_template("booking.html",query=query,query1=query1)
            
    
    return render_template("booking.html",query=query,query1=query1)

    
if __name__ == '__main__':
    app.run(debug=True)