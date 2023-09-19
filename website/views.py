from app import app
from models import db, User, Post, School
from flask import Flask, Blueprint, url_for, redirect, current_app, request, session, render_template, abort
import os
from flask_session import Session
import requests
import google.auth.transport.requests
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
from authlib.integrations.flask_client import OAuth
import pathlib


GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')  #enter your client id you got from Google console
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")  #set the path to where the .json file you got Google console is
# app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

Session(app)

ENV = os.environ.get('ENV')
if ENV=='dev':
    app.debug=True
    uri = "http://localhost:5000/callback"

else:
    app.debug=False
    uri = "https://campuscollab-test-96c4f0d44031.herokuapp.com/callback"

flow = Flow.from_client_secrets_file(  #Flow is OAuth 2.0 a class that stores all the information on how we want to authorize our users
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/user.organization.read", "openid"],  #here we are specifing what do we get after the authorization
    redirect_uri=uri  #and the redirect URI is the point where the user will end up after the authorization
)

oauth = OAuth(app)

# @app.route('/')
# def index():
#     return 'hello'

@app.route('/view-profile')
def view_profile():
    return render_template('view-profile.html')

@app.route('/edit-profile', methods=['GET','POST'])
def edit_profile():
    if request.method == 'POST':
        name = request.form['name']
        school = request.form['school']
        major = request.form['major']
        
        
        user = User.query.filter_by(email=session['email']).first()
        user.name = name
        # user.school = school
        user.major = major
        session['name'] = name
        
        school_now = School.query.filter_by(name=school).first()
        school_id = school_now.id
        
        user.school_id = school_id
        db.session.commit()
        return redirect('/view-profile')
    else:
        schools = School.query.all()
        return render_template('edit-profile.html', schools = schools)

@app.route('/collaborate/<int:post_id>', methods=['GET', 'POST'])
def collaborate(post_id):
    # Fetch post with id and get author email, then pass it into template
    post = Post.query.filter_by(id=post_id).first()
    return render_template('collaborate.html', post=post)

@app.route('/post-idea', methods=['GET', 'POST'])
def post_idea(): # Fix after
    if request.method == 'POST':
        title = request.form['title']
        author_name = request.form['author_name']
        description = request.form['description']
        author_id = 1
        new_post = Post(title, author_name, description, author_id)
        db.session.add(new_post)
        db.session.commit()
        return redirect('/home')
    else:
        return render_template('post-idea.html')

@app.route('/about')
def about():
    return render_template('about.html')

def login_required(function):  #a function to check if the user is authorized or not
    def wrapper(*args, **kwargs):
        if "google_id" not in session:  #authorization required
            return redirect('/login')
        else:
            return function()

    return wrapper

@app.route("/login")  #the page where the user can login
def login():
    authorization_url, state = flow.authorization_url()  #asking the flow class for the authorization (login) url
    # session["state"] = state
    return redirect(authorization_url)


@app.route("/callback")  #this is the page that will handle the callback process meaning process after the authorization
def callback():
    flow.fetch_token(authorization_response=request.url)
    # if not session["state"] == request.args["state"]:
    #     abort(500)  #state does not match!

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID
    )
    print('id_info: ', id_info)
    session["google_id"] = id_info.get("sub")  #defing the results to show on the page
    session["name"] = id_info.get("name")
    session["email"] = id_info.get("email")
    session['picture'] = id_info.get('picture')
    
        
    
    # Add to database
    if db.session.query(User).filter(User.email == session["email"]).count() == 0:
            data = User(session["name"], session["email"], session["google_id"], 1)
            
            db.session.add(data)
            db.session.commit()
            user = User.query.filter_by(email = session["email"]).first()
            session['user_id'] = user.id
    else:
        user = User.query.filter_by(email = session["email"]).first()
        session['user_id'] = user.id
        # session['school_name'] = user.school_id
        print(user)

    # Check for & store school
    school_code = id_info.get('hd')
    if school_code == None:
        session['school_code'] = None
    else:
        session['school_code'] = school_code

    

    if db.session.query(School).filter(School.code == school_code).count() == 0:
        if school_code == 'wfu.edu':
            session['school_name'] = 'Wake Forest University' # Hardcoded school name - find directory/make later
            new_school = School(session['school_name'], user.id, session['school_code'])
            db.session.add(new_school)
            db.session.commit()
    else:
        school = School.query.filter_by(code = school_code).first()
        session['school_name'] = school.name
        print('session[\'school_name\']: ', session['school_name'])
    
    return redirect("/home")  #the final page where the authorized users will end up

@app.route('/home')
@login_required
def home():
    posts = db.session.query(Post).all()
    schools = db.session.query(School).all()
    print(schools)
    return render_template('home.html', posts = posts, schools = schools)


@app.route("/logout")  #the logout page and function
def logout():
    session.clear()
    return redirect("/")


@app.route("/")  #the home page where the login button will be located
def index():
    return render_template('landing-page.html')