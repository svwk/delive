from flask import Flask

from delive.config import Config
from delive.models import db, migrate

app = Flask(__name__)
app.config.from_object(Config)
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SERVER_NAME='svs-delive.herokuapp.com',
    SESSION_COOKIE_DOMAIN='https://svs-delive.herokuapp.com'
)


db.init_app(app)
migrate.init_app(app, db, f'{config.current_path}/migrations')

from delive.views import *
from delive.admin import *
