import json
import os
import secrets

from flask import abort
current_path = os.path.dirname(os.path.realpath(__file__))



def load_config():
    with open(f'{current_path}/data/config.json', 'r') as f:
        config_data = (json.load(f))
    if config_data:
        db_key = config_data.get("dbselected", "")
        connection_strings = config_data.get("connection_string", "")
        if db_key and connection_strings and (db_key in connection_strings):
            db_uri = connection_strings[db_key]
            if db_uri[0:4] == "env:":
                config_data["db_uri"] = os.getenv(db_uri[4:])
            else:
                config_data["db_uri"] = db_uri
            
            config_data.pop("connection_string")
            return config_data

    abort(500, description="Ошибка конфигурации")



class Config:
    DEBUG = False
    SECRET_KEY = secrets.token_urlsafe()
    config = load_config()
    SQLALCHEMY_DATABASE_URI = config["db_uri"]
    SQLALCHEMY_TRACK_MODIFICATIONS = False
