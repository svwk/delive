from flask import Flask

from delive.config import Config
from delive.models import db, migrate

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
migrate.init_app(app, db, f'{config.current_path}/migrations')

from delive.views import *
from delive.admin import *
