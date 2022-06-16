from flask import Flask, g
from flask_qrcode import QRcode
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail
import sqlite3


DATABASE = "apparatus.db"

app = Flask(__name__)

mail = Mail(app)

# https://marcoagner.github.io/Flask-QRcode/
qrcode = QRcode(app)

# https://flask-limiter.readthedocs.io/en/stable/
limiter = Limiter(app, key_func=get_remote_address)


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


from app import routes
from app import routesEventAdmin
