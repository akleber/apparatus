from app import app, qrcode
from flask import request, send_file, url_for


@app.route('/')
@app.route('/index')
def index():
    return "Hello, World!"

@app.route("/qr/<tinylink>", methods=["GET"])
def qr(tinylink):
    url = url_for('qr', tinylink=tinylink)
    return send_file(qrcode(request.url_root[:-1] + url, mode="raw"), mimetype="image/png")
