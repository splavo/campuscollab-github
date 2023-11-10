from app import app
from models import db
# Only want to run web server if you run this file directly
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        app.run()