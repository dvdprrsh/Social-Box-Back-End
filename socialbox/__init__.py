from flask import Flask
from socialbox.config import Config
from flask_pymongo import PyMongo


app = Flask(__name__)
app.config.from_object(Config)

mongo = PyMongo(app)

from socialbox.routes import users, trips
