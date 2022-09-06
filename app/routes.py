from app import app, get_db, limiter, utils, EVENT_DB
from app.fieldDescriptions import get_field_description
from flask import (
    url_for,
    render_template,
    redirect,
    make_response,
    abort,
    request,
    g,
    send_file,
)
import markdown
import uuid
import time
import io
import sqlite3
import tempfile
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, RadioField, EmailField, TelField
from wtforms.validators import InputRequired, Length, Email


class RegisterForm(FlaskForm):
    firstName = StringField(
        "Vorname Kind", validators=[InputRequired(), Length(max=50)]
    )
    familyName = StringField(
        "Nachname Kind", validators=[InputRequired(), Length(max=50)]
    )
    mail = EmailField("E-Mail Adresse", validators=[InputRequired(), Email()])
    klasse = StringField("Klasse", validators=[InputRequired(), Length(max=3)])
    telefonnummer = TelField("Telefonnummer", validators=[InputRequired()])
    ganztag = RadioField(
        "Ganztag",
        default=0,
        choices=[(0, "keine Teilnahme"), (1, "bis 14:30 Uhr"), (2, "bis 17:00 Uhr")],
        validators=[InputRequired()],
    )
    foevMitgliedsname = StringField("Name des Mitglieds", validators=[Length(max=50)])
    beideAGs = BooleanField("beideAGs")
    geschlecht = RadioField(
        "Geschlecht",
        default=None,
        choices=[(0, "Männlich"), (1, "Weiblich"), (2, "Divers")],
        validators=[InputRequired()],
    )


# Request time logging. Uncomment the decorators
# @app.before_request
def logging_before():
    # Store the start time for the request
    g.start_time = time.perf_counter()


# @app.after_request
def logging_after(response):
    # Get total time in milliseconds
    total_time = time.perf_counter() - g.start_time
    time_in_ms = int(total_time * 1000)
    # Log the time taken for the endpoint
    app.logger.info(
        "%s ms %s %s %s", time_in_ms, request.method, request.path, dict(request.args)
    )
    return response


@app.route("/")
@app.route("/index")
def index():
    return render_template("index.html")


@app.route("/event/<uuid:eventID>/view", methods=["GET"])
def eventView(eventID):
    cur = get_db().execute(
        "SELECT title, description FROM event WHERE eventID = ? and active = 1",
        (str(eventID),),
    )
    rv = cur.fetchone()
    if not rv:
        app.logger.error(f"eventView: eventID unknown")
        return abort(404)

    event_data = {}
    event_data["eventID"] = str(eventID)
    event_data["title"] = rv[0]
    event_data["description"] = markdown.markdown(rv[1])

    activity_data = []
    cur = get_db().execute(
        "SELECT activityID, title FROM activity WHERE eventID = ? and active = 1 ORDER BY title",
        (str(eventID),),
    )
    for data in cur:
        a = {"activityID": data[0], "title": data[1]}
        activity_data.append(a)

    form = RegisterForm()

    utils.stats_event(f"view-{str(eventID)}")

    return render_template(
        "register.html", event_data=event_data, activity_data=activity_data, form=form
    )


@app.route("/event/<uuid:eventID>/register", methods=["POST"])
def register(eventID):
    form = RegisterForm()
    if not form.validate_on_submit():
        app.logger.error(f"register: form validation failed")
        abort(400)

    userID, user_data = utils.add_user(
        form.firstName.data,
        form.familyName.data,
        form.mail.data,
    )

    activities = request.form.getlist("activity")
    attendee_data = {
        "attendeeID": str(uuid.uuid4()),
        "userID": userID,
        "klasse": form.klasse.data,
        "ganztag": form.ganztag.data,
        "geschlecht": form.geschlecht.data,
        "telefonnummer": form.telefonnummer.data,
        "foevMitgliedsname": form.foevMitgliedsname.data,
        "beideAGs": form.beideAGs.data,
        "primaryActivityChoice": activities[0] if len(activities) >= 1 else "",
        "secondaryActivityChoice": activities[1] if len(activities) == 2 else "",
    }
    sql = """INSERT INTO attendee (attendeeID, userID, klasse, ganztag, geschlecht, telefonnummer, 
             foevMitgliedsname, beideAGs, primaryActivityChoice, secondaryActivityChoice) 
             VALUES (:attendeeID, :userID, :klasse, :ganztag, :geschlecht, :telefonnummer, :foevMitgliedsname,
             :beideAGs, :primaryActivityChoice, :secondaryActivityChoice);"""
    get_db().execute(sql, attendee_data)
    get_db().commit()

    # get event title
    cur = get_db().execute(
        "SELECT eventID, title, legal FROM event WHERE eventID = ?",
        (str(eventID),),
    )
    rv = cur.fetchone()
    if not rv:
        app.logger.error(f"register: eventID unknown")
        return abort(404)
    event_data = dict(rv)

    legal_plain = utils.strip_markdown(event_data["legal"])
    legal_filename = f"AGB_{ event_data['title'].replace(' ', '_') }.txt"

    subject = f"Anmeldebestätigung für '{event_data['title']}'"
    utils.send_email(
        subject,
        recipients=[user_data["mail"]],
        text_body=render_template(
            "email_registered.txt",
            user_data=user_data,
            event_data=event_data,
            attendee_data=attendee_data,
        ),
        html_body=None,
        att_filename=legal_filename,
        att_mime="text/plain",
        att_content=legal_plain,
    )

    return render_template(
        "registered.html", user_data=user_data, event_data=event_data
    )


@app.route("/event/<uuid:eventID>/deregister/<uuid:attendeeID>")
def deregister(eventID, attendeeID):
    cur = get_db().execute(
        "SELECT * FROM event WHERE eventID = ? and active = 1",
        (str(eventID),),
    )
    rv = cur.fetchone()
    if not rv:
        app.logger.error(f"deregister: eventID unknown or inactive")
        return abort(404)
    event_data = dict(rv)

    cur = get_db().execute(
        "SELECT userID FROM attendee WHERE attendeeID = ?", (str(attendeeID),)
    )
    rv = cur.fetchone()
    if not rv:
        app.logger.error(f"deregister: attendeeID unknown")
        return abort(404)

    get_db().execute(
        "DELETE FROM user WHERE userID = ?",
        (str(rv[0]),),
    )
    get_db().execute(
        "DELETE FROM attendee WHERE attendeeID = ?",
        (str(attendeeID),),
    )
    get_db().commit()

    return render_template("deregistered.html", event_data=event_data)


@app.route("/event/<uuid:eventID>/legal")
def legal(eventID):
    cur = get_db().execute("SELECT * FROM event WHERE eventID = ?", (str(eventID),))
    rv = cur.fetchone()
    if not rv:
        app.logger.error(f"legal: eventID unknown")
        return abort(404)

    event_data = dict(rv)
    if event_data["legal"]:
        event_data["legal"] = markdown.markdown(event_data["legal"])

    return render_template("legal.html", event_data=event_data)


@app.route("/event/<uuid:eventID>/legal/download")
def legal_download(eventID):
    cur = get_db().execute(
        "SELECT title, legal FROM event WHERE eventID = ?", (str(eventID),)
    )
    rv = cur.fetchone()
    if not rv:
        app.logger.error(f"legal_download: eventID unknown")
        return abort(404)

    event_data = dict(rv)
    timestamp = datetime.utcnow().strftime("%d.%m.%Y")

    legal_plain = utils.strip_markdown(event_data["legal"])
    legal_txt = f"{legal_plain}\n\nHeruntergeladen am {timestamp}\n"
    legal_filename = f"AGB_{ event_data['title'].replace(' ', '_') }.txt"

    f = io.BytesIO(legal_txt.encode("utf-8"))

    return send_file(
        f, as_attachment=True, download_name=legal_filename, cache_timeout=0
    )


@app.route("/event/<uuid:eventID>/banner.jpg")
def eventBanner(eventID):
    cur = get_db().execute(
        "SELECT bannerImage FROM event WHERE eventID = ?", (str(eventID),)
    )
    rv = cur.fetchone()
    if not rv:
        return app.send_static_file("banner-fallback.jpg")

    image = rv[0]
    if not image:
        return ("", 204)

    response = make_response(image)
    response.headers.set("Content-Type", "image/jpeg")
    return response


@app.route("/activityAbout/<activityID>", methods=["GET"])
def activityAbout(activityID):
    cur = get_db().execute(
        "SELECT eventID, title, description FROM activity WHERE activityID = ?",
        (activityID,),
    )
    rv = cur.fetchone()
    if not rv:
        app.logger.error(f"activityAbout: activityID unknown")
        return abort(404)

    event_data = {}
    event_data["eventID"] = rv[0]

    activity_data = []
    a = {"title": rv[1], "description": markdown.markdown(rv[2])}
    activity_data.append(a)

    return render_template(
        "activityAbout.html", event_data=event_data, activity_data=activity_data
    )


@app.route("/verifyMail/<mailVerificationToken>")
def verifyMail(mailVerificationToken):
    sql = "SELECT firstName FROM user WHERE mailVerificationToken = ?"
    cur = get_db().execute(sql, (mailVerificationToken,))
    rv = cur.fetchone()
    if rv:
        user_data = dict(rv)
        sql = "UPDATE user SET mailVerificationToken = '' WHERE mailVerificationToken = ?;"
        get_db().execute(sql, (mailVerificationToken,))
        get_db().commit()
        return render_template("mailVerified.html", user_data=user_data)
    else:
        return "E-Mail Verifizierungstoken unbekannt oder E-Mail Adresse bereits verifiziert"


@app.route("/gdpr/<gdprToken>")
def gdpr(gdprToken):
    cur = get_db().execute("SELECT * FROM gdprView WHERE gdprToken = ?", (gdprToken,))
    rv = cur.fetchone()
    if not rv:
        app.logger.error(f"gdpr: gdprToken unknown")
        return abort(404)
    gdpr_data = dict(rv)

    gdpr_data_desc = {}
    for key, value in gdpr_data.items():
        gdpr_data_desc[get_field_description(key)] = value

    return render_template("gdpr.html", gdpr_data=gdpr_data_desc)


# for statistics purposes we distinguish between q qr code link and a tinylink
@app.route("/t/<tinylink>")
@limiter.limit("10/minute")
def t(tinylink):
    cur = get_db().execute("SELECT eventID FROM event WHERE tinylink = ?", (tinylink,))
    rv = cur.fetchone()
    if not rv:
        app.logger.error(f"t: tinylink unknown")
        return abort(404)

    utils.stats_event(f"t-{tinylink}")
    return redirect(url_for("eventView", eventID=rv[0]))


# see above
@app.route("/q/<tinylink>")
@limiter.limit("10/minute")
def q(tinylink):
    cur = get_db().execute("SELECT eventID FROM event WHERE tinylink = ?", (tinylink,))
    rv = cur.fetchone()
    if not rv:
        app.logger.error(f"q: tinylink unknown")
        return abort(404)

    utils.stats_event(f"q-{tinylink}")
    return redirect(url_for("eventView", eventID=rv[0]))


@app.route("/backup/<backup_secret>")
def backup(backup_secret):
    if backup_secret != app.config["BACKUP_SECRET"]:
        app.logger.error(f"backup: secret wrong")
        abort(404)

    backup_filename = "backup_event.db"

    con = sqlite3.connect(EVENT_DB)
    bck = sqlite3.connect(backup_filename)
    with bck:
        con.backup(bck)
    bck.close()
    con.close()

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    download_name = f"event_{timestamp}.db"

    return send_file(
        path_or_file=f"../{backup_filename}",
        mimetype="application/octet-stream",
        as_attachment=True,
        download_name=download_name,
    )
