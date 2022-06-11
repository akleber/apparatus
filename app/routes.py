from app import app, qrcode, get_db
from flask import request, send_file, url_for, render_template, redirect, make_response
import markdown


@app.route("/")
@app.route("/index")
def index():
    return "Hello, World!"


@app.route("/register/<tinylink>", methods=["GET", "POST"])
def register(tinylink):
    user = {"username": "Miguel"}

    cur = get_db().execute("SELECT title, description FROM event WHERE eventID = 1")
    rv = cur.fetchone()
    if rv:
        title = rv[0]
        description = rv[1]
        return render_template(
            "register.html",
            title=title,
            user=user,
            description=markdown.markdown(description),
        )


@app.route("/qr/<tinylink>", methods=["GET"])
def qr(tinylink):
    url = url_for("qr", tinylink=tinylink)
    return send_file(
        qrcode(request.url_root[:-1] + url, mode="raw"), mimetype="image/png"
    )


@app.route("/t/<tinylink>")
def t(tinylink):
    return redirect(url_for("register", tinylink=tinylink))


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
