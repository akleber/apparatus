from app import app, qrcode, get_db, limiter
from flask import (
    request,
    send_file,
    url_for,
    render_template,
    redirect,
    make_response,
    abort,
)
import markdown


@app.route("/")
@app.route("/index")
def index():
    return "Hello, World!"


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
    return "registered: " + str(request.form)


@app.route("/activityAbout/<activityID>", methods=["GET"])
def activityAbout(activityID):
    return "activityAbout"


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
