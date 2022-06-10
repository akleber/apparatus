from flask import Flask, g
from flask_qrcode import QRcode
import sqlite3


DATABASE = 'apparatus.db'

app = Flask(__name__)

# https://marcoagner.github.io/Flask-QRcode/
qrcode = QRcode(app)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

from app import routes
