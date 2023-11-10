from app import app
from flask_sqlalchemy import SQLAlchemy
import json
from datetime import datetime

db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.String, primary_key = True)
    email = db.Column(db.String)
    name = db.Column(db.String)
    posts = db.relationship('Post', backref='user', lazy=True)

    def __init__(self, id, name, email, posts):
        self.id = id
        self.email = email
        self.name = name
        self.posts = posts

class Post(db.Model):
    __tablename__ = 'post'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    author_name = db.Column(db.String)
    description = db.Column(db.String(500))
    author_id = db.Column(db.String, db.ForeignKey('user.id'), nullable = True) # nullable just for production

    def __init__(self, title, author_name, description, author_id):
        self.title = title
        self.author_name = author_name
        self.description = description
        self.author_id = author_id

class Message(db.Model):
    __tablename__ = 'message'
    id = db.Column(db.Integer, primary_key = True)
    sender_id = db.Column(db.String, db.ForeignKey('user.id')) # Google ID
    chat_room_id = db.Column(db.Integer, db.ForeignKey('chat_room.id'))
    body = db.Column(db.String(800))
    timestamp = db.Column(db.DateTime, default = datetime.utcnow)

    def __init__(self, sender_id, chat_room_id, body, timestamp):
        self.sender_id = sender_id
        self.chat_room_id = chat_room_id
        self.body = body
        self.timestamp = timestamp

class ChatRoom(db.Model):
    __tablename__ = 'chat_room'
    id = db.Column(db.Integer, primary_key = True)
    user1_id = db.Column(db.String, db.ForeignKey('user.id'))
    user2_id = db.Column(db.String, db.ForeignKey('user.id'))

    def __init__(self, user1_id, user2_id):
        self.user1_id = user1_id
        self.user2_id = user2_id
            

if __name__ == '__main__':
    db.create_all()
    db.session.commit()
    