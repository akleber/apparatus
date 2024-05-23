from flask import Flask, g
from flask_qrcode import QRcode
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail
import sqlite3
import os
from pathlib import Path


EVENT_DB = "event.db"

app = Flask(__name__)

app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER")
app.config["MAIL_PORT"] = os.getenv("MAIL_PORT")
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER")
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_SUPPRESS_SEND"] = False
app.config["MAIL_DEBUG"] = False
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["BACKUP_SECRET"] = os.getenv("BACKUP_SECRET")
app.config["STATS_SECRET"] = os.getenv("STATS_SECRET")

app.config["WTF_CSRF_TIME_LIMIT"] = 21600  # 6h


version = "dev"
version_file = Path("VERSION")
if version_file.is_file():
    with open(version_file, "r") as f:
        version = f.read().strip()
app.logger.info(f"Found version {version}")
app.config["VERSION"] = version

app.jinja_options["keep_trailing_newline"] = True

mail = Mail(app)

# https://marcoagner.github.io/Flask-QRcode/
qrcode = QRcode(app)

# https://flask-limiter.readthedocs.io/en/stable/
limiter = Limiter(app, key_func=get_remote_address)

app.logger.warning(
    f"Python SQLite module version: {sqlite3.version}, SQLite library version: {sqlite3.sqlite_version}"
)


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(EVENT_DB)
    db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


with app.app_context():
    cur = get_db().execute("SELECT name FROM sqlite_schema WHERE type = 'table' AND name NOT LIKE 'sqlite_%'")
    rv = cur.fetchone()
    if not rv:
        app.logger.warn("found empty db, loading schema and demo data")
        with open("event-schema.sql") as f:
            schema = f.read()
        get_db().executescript(schema)

        with open("event-demo.sql") as f:
            schema = f.read()
        get_db().executescript(schema)

        get_db().commit()

from app.election import bp as election_bp

app.register_blueprint(election_bp, url_prefix="/election")


from app import routes
from app import routesEventAdmin
