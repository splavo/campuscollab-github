from app import app
from sqlalchemy import func, or_, and_
from models import db, User, Post, Message, ChatRoom
from flask import Flask, Blueprint, url_for, redirect, current_app, request, session, render_template, abort

import datetime
import os
from flask_session import Session
import requests
import google.auth.transport.requests
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
from authlib.integrations.flask_client import OAuth
import pathlib
from datetime import datetime


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



def get_or_create_chat_room(user1, user2):
    room = db.session.query(ChatRoom).filter(ChatRoom.user1_id == user1, ChatRoom.user2_id == user2).first()
    print(room)
    if room is None:
        room = ChatRoom(user1, user2)
        db.session.add(room)
        db.session.commit()
    return room




def get_user_chat_rooms(user_id):
    # Query all messages for a specific user, group by chat_room_id
    result = (
        db.session.query(
            ChatRoom.id.label("chat_room_id")
        )
        .select_from(Message)
        .join(ChatRoom, or_(
            and_(Message.sender_id == user_id, ChatRoom.user1_id == user_id),
            and_(Message.sender_id == user_id, ChatRoom.user2_id == user_id),
            and_(Message.chat_room_id == ChatRoom.id, ChatRoom.user1_id == user_id),
            and_(Message.chat_room_id == ChatRoom.id, ChatRoom.user2_id == user_id)
        ))
        .group_by(ChatRoom.id)
        .all()
    )

    # Extract the chat room IDs from the result
    chat_rooms = [row.chat_room_id for row in result]


    return chat_rooms


def get_messages_for_chat_room(chat_room_id):
    # Assuming your Message model has a 'timestamp' field for sorting
    messages = Message.query.filter_by(chat_room_id=chat_room_id).order_by(Message.timestamp).all()
    for message in messages:
        print(message.sender_id, message.chat_room_id)
    return messages

    


# ------ Main Routes ------
@app.route('/view-profile')
def view_profile():
    return render_template('view-profile.html')

@app.route('/chat/<int:chat_room_id>', methods = ['GET', 'POST'])
def chat(chat_room_id):
    
    
    if request.method == 'POST':
        new_message = Message(session['user_id'], chat_room_id, request.form['body'], datetime.utcnow())
        db.session.add(new_message)
        db.session.commit()

        return redirect(url_for('chat', chat_room_id=chat_room_id))
    
    else:

        chat_room_ids = get_user_chat_rooms(session['user_id'])
        messages = get_messages_for_chat_room(chat_room_id)
        names = {}
        for message in messages:
            names[message.sender_id] = User.query.filter_by(id = message.sender_id).first().name
        
        
        current_chat_room = chat_room_id
        print(messages)
        
    return render_template('chat.html', chat_room_ids=chat_room_ids, messages=messages, current_chat_room=current_chat_room, names = names)

@app.route('/collaborate/<int:post_id>', methods=['GET', 'POST'])
def collaborate(post_id):
    
    # Fetch post with post id
    post = Post.query.filter_by(id=post_id).first()

    if request.method == 'POST':

        chat_room = get_or_create_chat_room(session['user_id'], post.author_id)

        # Create new message
        sender_id = session['user_id']
        
        body = request.form['body']
        timestamp = datetime.utcnow()
        new_message = Message(sender_id, chat_room.id, body, timestamp)

        db.session.add(new_message)
        db.session.add(chat_room)
        db.session.commit()

        
        return redirect(url_for('chat', chat_room_id=chat_room.id))
    
    else:
        return render_template('collaborate.html', post=post)

@app.route('/post-idea', methods=['GET', 'POST'])
def post_idea(): # Fix after
    if request.method == 'POST':
        title = request.form['title']
        author_name = request.form['author_name']
        description = request.form['description']
        print(session['user_id'])
        new_post = Post(title, author_name, description, session['user_id'])
        print(new_post)
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
        if "user_id" not in session:  #authorization required
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
    session["user_id"] = id_info.get("sub")  #defing the results to show on the page
    session["name"] = id_info.get("name")
    session["email"] = id_info.get("email")
    session['picture'] = id_info.get('picture')

    # If the user doesnt exist
    if db.session.query(User).filter(User.id == session["user_id"]).count() == 0:

        # Create user
        new_user = User(session["user_id"], session["email"], session["name"],[])
        db.session.add(new_user)
        db.session.commit()

    # Else query the user and set user_id session variabele
    else:
        user = User.query.filter_by(id = session["user_id"]).first()
        session['user_id'] = user.id

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