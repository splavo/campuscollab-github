import os
from authlib.integrations.flask_client import OAuth
from datetime import timedelta
from flask import Flask, Blueprint, url_for, redirect, current_app, request, session, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('landing-page.html')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/view-profile')
def view_profile():
    return render_template('login.html')

@app.route('/collaborate')
def collaborate():
    return render_template('collaborate.html')

@app.route('/post-idea')
def post_idea():
    return render_template('post-idea.html')

@app.route('/about')
def about():
    return render_template('about.html')


# Only want to run web server if you run this file directly
if __name__ == '__main__':
    app.run(debug=True)

# ------------------------------------------------------------------------------------------------
# Configuration
# GOOGLE_CLIENT_ID = '861825727338-cuod7108nr4e2cc59edvukagh6veo8uv.apps.googleusercontent.com'
# GOOGLE_CLIENT_SECRET = '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'
# GOOGLE_DISCOVERY_URL = (
#     "https://accounts.google.com/.well-known/openid-configuration"
    
# )

# oauth = OAuth(app)


# app.config['SESSION_COOKIE_NAME'] = 'google-login-session'
# app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=5)
# app.secret_key = "secret-key"

