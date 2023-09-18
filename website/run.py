from core import app

# Only want to run web server if you run this file directly
if __name__ == '__main__':
    with app.app_context():
        app.run()