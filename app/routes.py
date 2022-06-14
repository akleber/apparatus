import tempfile
from app import app, qrcode, get_db, limiter
from flask import (
    request,
    send_file,
    url_for,
    render_template,
    redirect,
    make_response,
    abort,
    send_from_directory,
)
from pyexcel_xlsx import save_data
from collections import OrderedDict
from datetime import datetime
import markdown
import uuid


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
    sql = """INSERT INTO user (firstName, familyName, mail, mailVerificationToken, dsgvoToken) 
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
    # fix typo telefonummer
    sql = """INSERT INTO attendee (userID, klasse, ganztag, telefonummer, 
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

    event_data = {"eventID": eventID, "title": rv[0]}

    return render_template(
        "registered.html", event_data=event_data, user_data=user_data
    )


@app.route("/eventAdmin/<eventID>/attendees/xlsx")
def eventAdmin_attendees_xlsx(eventID):
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    tempfolder = app.root_path + "/temp"
    filename = f"event_export_{timestamp}.xlsx"

    data = OrderedDict()
    data.update({"Sheet 1": [[1, 2, 3], [4, 5, 6]]})
    data.update({"Sheet 2": [["row 1", "row 2", "row 3"]]})
    save_data(tempfolder + "/" + filename, data)

    return send_from_directory(
        tempfolder, filename, as_attachment=True, cache_timeout=0
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


@app.route("/gdpr/<gdprData>")
def gdpr(gdprData):
    return "GDPR data"


@app.route("/qr/<eventID>", methods=["GET"])
def qr(eventID):
    cur = get_db().execute("SELECT tinyurl FROM event WHERE eventID = ?", (eventID,))
    rv = cur.fetchone()
    if not rv:
        return abort(404)

    url = url_for("t", tinylink=rv[0])
    return send_file(
        qrcode(request.url_root[:-1] + url, mode="raw"), mimetype="image/png"
    )


@app.route("/t/<tinylink>")
@limiter.limit("10/minute")
def t(tinylink):
    cur = get_db().execute("SELECT eventID FROM event WHERE tinyurl = ?", (tinylink,))
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
