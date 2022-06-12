from app import app, qrcode, get_db
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


@app.route("/eventView/<tinylink>", methods=["GET"])
def eventView(tinylink):
    cur = get_db().execute("SELECT eventID FROM event WHERE tinyurl = ?", (tinylink,))
    rv = cur.fetchone()
    if not rv:
        return abort(404)

    eventID = rv[0]
    cur = get_db().execute(
        "SELECT title, description FROM event WHERE eventID = ?", (eventID,)
    )
    rv = cur.fetchone()
    if rv:
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


@app.route("/register/<eventID>", methods=["POST"])
def register(eventID):
    return "registered: " + str(request.form)


@app.route("/activityAbout/<activityID>", methods=["GET"])
def activityAbout(activityID):
    return "activityAbout"


@app.route("/qr/<tinylink>", methods=["GET"])
def qr(tinylink):
    url = url_for("qr", tinylink=tinylink)
    return send_file(
        qrcode(request.url_root[:-1] + url, mode="raw"), mimetype="image/png"
    )


@app.route("/t/<tinylink>")
def t(tinylink):
    return redirect(url_for("eventView", tinylink=tinylink))


# todo: int -> uuid
@app.route("/eventBanner/<int:eventID>/banner.jpg")
def eventBanner(eventID):
    cur = get_db().execute(
        "SELECT bannerImage FROM event WHERE eventID = ?", (eventID,)
    )
    rv = cur.fetchone()
    if rv:
        image = rv[0]
        response = make_response(image)
        response.headers.set("Content-Type", "image/jpeg")
        return response
    else:
        return app.send_static_file("banner-fallback.jpg")
