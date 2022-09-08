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


eventAttendees_view = """
DROP VIEW IF EXISTS "main"."eventAttendees";
CREATE VIEW "eventAttendees" AS SELECT e.eventID, u.firstName, u.familyName, u.mail, u.mailVerificationToken,at.klasse,group_concat(a.title, "|") as AGs,at.attendeeID
FROM event as e
INNER JOIN activity a ON a.eventID = e.eventID
INNER JOIN attendee at ON a.activityID = at.primaryActivityChoice OR a.activityID = at.secondaryActivityChoice
INNER JOIN user u ON at.userID = u.userID
GROUP BY u.firstName, u.familyName
"""

eventAttendeesXlsx_view = """
DROP VIEW IF EXISTS "main"."eventAttendeesXlsx";
CREATE VIEW "eventAttendeesXlsx" AS SELECT e.eventID, u.firstName, u.familyName, u.mail, u.mailVerificationToken,at.klasse,at.geschlecht,at.ganztag,at.telefonnummer,at.foevMitgliedsname,at.beideAGs,a.title as AG
FROM event as e
INNER JOIN activity a ON a.eventID = e.eventID
INNER JOIN attendee at ON a.activityID = at.primaryActivityChoice OR a.activityID = at.secondaryActivityChoice
INNER JOIN user u ON at.userID = u.userID
"""

gdprView = """
DROP VIEW IF EXISTS "main"."gdprView";
CREATE VIEW gdprView AS
SELECT user.firstName , user.familyName , user.mail, user.mailVerificationToken , user.gdprToken, 
attendee.klasse, attendee.geschlecht, attendee.ganztag, attendee.telefonnummer, attendee.foevMitgliedsname , attendee.beideAGs,
a1.title AS title1, a2.title as title2
FROM user 
JOIN attendee ON user.userID = attendee.userID 
LEFT OUTER JOIN activity a1 ON attendee.primaryActivityChoice = a1.activityID
LEFT OUTER JOIN activity a2 ON attendee.secondaryActivityChoice = a2.activityID
"""

with app.app_context():
    get_db().executescript(eventAttendees_view)
    get_db().executescript(eventAttendeesXlsx_view)
    get_db().executescript(gdprView)
    get_db().commit()
app.logger.info(f"updated sql views")

from app.election import bp as election_bp

app.register_blueprint(election_bp, url_prefix="/election")


from app import routes
from app import routesEventAdmin
