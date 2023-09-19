from app import app
from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy(app)






class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    email = db.Column(db.String)
    google_id = db.Column(db.String)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable = True)
    posts = db.relationship('Post', backref='user', lazy=True)

    def __init__(self, name, email, google_id, school_id, posts):
        self.name = name
        self.email = email
        self.google_id = google_id
        self.school_id = school_id
        self.posts = posts

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
    code = db.Column(db.String(50))

    def __init__(self, name, members, code):
        self.name = name
        self.members = members
        self.code = code


if __name__ == '__main__':
    db.create_all()
    