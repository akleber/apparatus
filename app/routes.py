from app import app, qrcode, get_db
from flask import request, send_file, url_for, render_template, redirect, make_response
import markdown


@app.route("/")
@app.route("/index")
def index():
    return "Hello, World!"


@app.route("/register/<tinylink>", methods=["GET", "POST"])
def register(tinylink):
    title = "AG Angebot Förderverein CUS Schuljahr 2021/22"
    user = {"username": "Miguel"}

    cur = get_db().execute('SELECT description FROM event WHERE eventID = 1')
    rv = cur.fetchall()
    cur.close()

    return render_template("register.html", title=title, user=user, description=markdown.markdown(rv[0][0]))


@app.route("/qr/<tinylink>", methods=["GET"])
def qr(tinylink):
    url = url_for("qr", tinylink=tinylink)
    return send_file(
        qrcode(request.url_root[:-1] + url, mode="raw"), mimetype="image/png"
    )


@app.route("/t/<tinylink>")
def t(tinylink):
    return redirect(url_for("register", tinylink=tinylink))


@app.route("/eventBanner/<eventID>/banner.jpg")
def eventBanner(eventID):
    cur = get_db().execute('SELECT bannerImage FROM event WHERE eventID = 1')
    image = cur.fetchone()
    response = make_response(image[0])
    response.headers.set('Content-Type', 'image/jpeg')
    return response
