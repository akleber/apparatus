from flask import Flask, g
from flask_qrcode import QRcode
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail
import sqlite3
import os
from pathlib import Path

from importlib_metadata import version


DATABASE = "apparatus.db"

app = Flask(__name__)

app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER")
app.config["MAIL_PORT"] = os.getenv("MAIL_PORT")
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER")
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_SUPPRESS_SEND"] = False
app.config["MAIL_DEBUG"] = False
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")

version = "dev"
version_file = Path("VERSION")
if version_file.is_file():
    with open(version_file, "r") as f:
        version = f.read().strip()
app.logger.info(f"Found version {version}")
app.config["VERSION"] = version

mail = Mail(app)

# https://marcoagner.github.io/Flask-QRcode/
qrcode = QRcode(app)

# https://flask-limiter.readthedocs.io/en/stable/
limiter = Limiter(app, key_func=get_remote_address)

app.logger.warning(f"Python SQLite module version: {sqlite3.version}, SQLite library version: {sqlite3.sqlite_version}")


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)

    db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


from app import routes
from app import routesEventAdmin
