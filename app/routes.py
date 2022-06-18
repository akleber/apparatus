from app import app, get_db, limiter, mail, babel
from app.fieldDescriptions import get_field_description
from flask import (
    url_for,
    render_template,
    redirect,
    make_response,
    abort,
    request,
    g,
    current_app,
)
import markdown
import uuid
from threading import Thread
from flask_mail import Message
import time
from flask_babel import _


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(subject, recipients, text_body, html_body):
    # todo fix mail
    # return

    msg = Message(subject, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    Thread(target=send_async_email, args=(app, msg)).start()


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


@babel.localeselector
def get_locale():
    # return request.accept_languages.best_match(app.config['LANGUAGES'])
    return "de"


@app.route("/")
@app.route("/index")
def index():
    return render_template("index.html")


@app.route("/event/<eventID>/view", methods=["GET"])
def eventView(eventID):
    cur = get_db().execute(
        "SELECT title, description FROM event WHERE eventID = ?", (eventID,)
    )
    rv = cur.fetchone()
    if not rv:
        return abort(404)

    event_data = {}
    event_data["eventID"] = eventID
    event_data["title"] = rv[0]
    event_data["description"] = markdown.markdown(rv[1])

    activity_data = []
    cur = get_db().execute(
        "SELECT activityID, title FROM activity WHERE eventID = ?", (eventID,)
    )
    for data in cur:
        a = {"activityID": data[0], "title": data[1]}
        activity_data.append(a)

    return render_template(
        "register.html", event_data=event_data, activity_data=activity_data
    )


@app.route("/event/<eventID>/register", methods=["POST"])
def register(eventID):
    user_data = {
        "firstName": request.form.get("firstName"),
        "familyName": request.form.get("familyName"),
        "mail": request.form.get("mail"),
        "mailVerificationToken": str(uuid.uuid4()),
        "gdprToken": str(uuid.uuid4()),
    }
    sql = """INSERT INTO user (firstName, familyName, mail, mailVerificationToken, gdprToken) 
             VALUES (:firstName, :familyName, :mail, :mailVerificationToken, :gdprToken) RETURNING userID;"""
    cur = get_db().execute(sql, user_data)
    userID = cur.lastrowid

    activities = request.form.getlist("activity")
    attendee_data = {
        "userID": userID,
        "klasse": request.form.get("klasse", ""),
        "ganztag": request.form.get("ganztag", ""),
        "telefonnummer": request.form.get("telefonnummer", ""),
        "foevMitgliedsname": request.form.get("foevMitgliedsname", ""),
        "beideAGs": request.form.get("beideAGs", ""),
        "primaryActivityChoice": activities[0] if len(activities) >= 1 else "",
        "secondaryActivityChoice": activities[1] if len(activities) == 2 else "",
    }
    sql = """INSERT INTO attendee (userID, klasse, ganztag, telefonnummer, 
             foevMitgliedsname, beideAGs, primaryActivityChoice, secondaryActivityChoice) 
             VALUES (:userID, :klasse, :ganztag, :telefonnummer, :foevMitgliedsname,
             :beideAGs, :primaryActivityChoice, :secondaryActivityChoice);"""
    cur = get_db().execute(sql, attendee_data)
    get_db().commit()

    # get event title
    cur = get_db().execute(
        "SELECT title FROM event WHERE eventID = ?",
        (eventID,),
    )
    rv = cur.fetchone()
    if not rv:
        return abort(404)
    title = rv[0]

    event_data = {"eventID": eventID, "title": title}

    subject = f"Anmeldebestätigung für '{title}'"
    send_email(
        subject,
        recipients=[user_data["mail"]],
        text_body=render_template(
            "email_registered.txt", user_data=user_data, event_data=event_data
        ),
        html_body=None,
    )

    return render_template(
        "registered.html", user_data=user_data, event_data=event_data
    )


@app.route("/eventAdd")
def eventAdd():
    return "event add"


@app.route("/activityAbout/<activityID>", methods=["GET"])
def activityAbout(activityID):
    cur = get_db().execute(
        "SELECT eventID, title, description FROM activity WHERE activityID = ?",
        (activityID,),
    )
    rv = cur.fetchone()
    if not rv:
        return abort(404)

    event_data = {}
    event_data["eventID"] = rv[0]

    activity_data = []
    a = {"title": rv[1], "description": markdown.markdown(rv[2])}
    activity_data.append(a)

    return render_template(
        "activityAbout.html", event_data=event_data, activity_data=activity_data
    )


@app.route("/gdpr/<gdprToken>")
def gdpr(gdprToken):
    cur = get_db().execute("SELECT * FROM gdprView WHERE gdprToken = ?", (gdprToken,))
    rv = cur.fetchone()
    if not rv:
        return abort(404)
    gdpr_data = dict(rv)
    print(gdpr_data)

    gdpr_data_desc = {}
    for key, value in gdpr_data.items():
        gdpr_data_desc[get_field_description(key)] = value

    event_data = {"eventID": 1}

    return render_template("gdpr.html", gdpr_data=gdpr_data_desc, event_data=event_data)


@app.route("/t/<tinylink>")
@limiter.limit("10/minute")
def t(tinylink):
    cur = get_db().execute("SELECT eventID FROM event WHERE tinylink = ?", (tinylink,))
    rv = cur.fetchone()
    if not rv:
        return abort(404)

    return redirect(url_for("eventView", eventID=rv[0]))


# todo: int -> uuid
@app.route("/event/<int:eventID>/banner.jpg")
def eventBanner(eventID):
    cur = get_db().execute(
        "SELECT bannerImage FROM event WHERE eventID = ?", (eventID,)
    )
    rv = cur.fetchone()
    if not rv:
        return app.send_static_file("banner-fallback.jpg")

    image = rv[0]
    response = make_response(image)
    response.headers.set("Content-Type", "image/jpeg")
    return response
