import os
from authlib.integrations.flask_client import OAuth
from datetime import timedelta
from flask import Flask, Blueprint, url_for, redirect, current_app, request, session, render_template, abort
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
import requests
# from authlib.integrations.flask_client import OAuth
import google.auth.transport.requests
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
import pathlib
from pip._vendor import cachecontrol
from os import environ as env
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

app.secret_key = "secret-key"  #it is necessary to set a password when dealing with OAuth 2.0
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"  #this is to set our environment to https because OAuth 2.0 only supports https environments

GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')  #enter your client id you got from Google console
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")  #set the path to where the .json file you got Google console is
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI')

ENV = os.environ.get('ENV')
if ENV=='dev':
    app.debug=True
    uri = "http://localhost:5000/callback"

else:
    app.debug=False
    uri = "https://campuscollab-test-96c4f0d44031.herokuapp.com/callback"

flow = Flow.from_client_secrets_file(  #Flow is OAuth 2.0 a class that stores all the information on how we want to authorize our users
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],  #here we are specifing what do we get after the authorization
    redirect_uri=uri  #and the redirect URI is the point where the user will end up after the authorization
)



oauth = OAuth(app)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI')

Session(app)


print(ENV)

if ENV=='dev':
    app.debug=True
     

else:
    app.debug=False
    

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    email = db.Column(db.String)
    google_id = db.Column(db.String)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable = True)
    skills = db.Column(db.String)
    experience = db.Column(db.String)
    posts = db.relationship('Post', backref='user', lazy=True)

    def __init__(self, name, email, google_id, school, skills, experience):
        self.name = name
        self.email = email
        self.google_id = google_id
        self.school = school
        self.skills = skills
        self.experience = experience

class Post(db.Model):
    __tablename__ = 'post'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    author_name = db.Column(db.String)
    description = db.Column(db.String(500))
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = True)

    def __init__(self, title, author_name, description, author_id):
        self.title = title
        self.author_name = author_name
        self.description = description
        self.author_id = author_id

class School(db.Model):
    __tablename__ = 'school'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    members = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = True)

    def __init__(self, name, members):
        self.name = name
        self.members = members
    

# @app.route('/view-profile')
# def view_profile():
#     return render_template('login.html')

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
    print(id_info)
    session["google_id"] = id_info.get("sub")  #defing the results to show on the page
    session["name"] = id_info.get("name")
    session["email"] = id_info.get("email")
    
    print(session)

    

    # Add to database
    
    if db.session.query(User).filter(User.email == session["email"]).count() == 0:
            data = User(session["name"], session["email"], session["google_id"], 12345, 'skills', 'experience')
            db.session.add(data)
            db.session.commit()
            
    else:
        user = User.query.filter_by(email = session["email"]).first()
        print(user)
                

    return redirect("/home")  #the final page where the authorized users will end up

@app.route('/home')
@login_required
def home():
    posts = db.session.query(Post).all()
    return render_template('home.html', posts = posts)


@app.route("/logout")  #the logout page and function
def logout():
    session.clear()
    return redirect("/")


@app.route("/")  #the home page where the login button will be located
def index():
    return render_template('landing-page.html')

# Only want to run web server if you run this file directly
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        app.run()
