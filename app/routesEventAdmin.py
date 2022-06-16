from app import app, get_db, qrcode
from flask import (
    render_template,
    abort,
    url_for,
    send_file,
    request,
)
from datetime import datetime
from pyexcel_xlsx import save_data
from collections import OrderedDict
from docx import Document
from htmldocx import HtmlToDocx
import markdown
from io import BytesIO


@app.route("/eventAdmin/<eventID>", methods=["GET"])
def eventAdmin(eventID):
    cur = get_db().execute(
        "SELECT title, tinyurl FROM event WHERE eventID = ?", (eventID,)
    )
    rv = cur.fetchone()
    if not rv:
        return abort(404)

    event_data = {}
    event_data["eventID"] = eventID
    event_data["title"] = rv[0]
    event_data["tinyurl"] = rv[1]

    return render_template("eventAdmin.html", event_data=event_data)


@app.route("/eventAdmin/<eventID>/attendees/xlsx")
def eventAdmin_attendees_xlsx(eventID):
    data = OrderedDict()
    data.update({"Sheet 1": [[1, 2, 3], [4, 5, 6]]})
    data.update({"Sheet 2": [["row 1", "row 2", "row 3"]]})

    io = BytesIO()
    save_data(io, data)
    io.seek(0)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"event_export_{timestamp}.xlsx"

    return send_file(io, as_attachment=True, download_name=filename, cache_timeout=0)


@app.route("/eventAdmin/<eventID>/qr", methods=["GET"])
def qr(eventID):
    cur = get_db().execute("SELECT tinyurl FROM event WHERE eventID = ?", (eventID,))
    rv = cur.fetchone()
    if not rv:
        return abort(404)

    url = url_for("t", tinylink=rv[0])
    return send_file(
        qrcode(request.url_root[:-1] + url, mode="raw"), mimetype="image/png"
    )


@app.route("/eventAdmin/<eventID>/activity/docx", methods=["GET"])
def eventAdmin_activity_docx(eventID):
    cur = get_db().execute("SELECT title FROM event WHERE eventID = ?", (eventID,))
    rv = cur.fetchone()
    if not rv:
        return abort(404)

    eventTitle = rv[0]

    cur = get_db().execute(
        "SELECT title, description FROM activity WHERE eventID = ?", (eventID,)
    )

    document = Document()
    document.add_heading(eventTitle, 0)

    new_parser = HtmlToDocx()

    for a in cur:
        document.add_heading(a[0], level=1)

        md = a[1]
        html = markdown.markdown(md)

        new_parser.add_html_to_document(html, document)
        # p = document.add_paragraph(a[1])

    file = BytesIO()
    document.save(file)
    file.seek(0)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"activity_export_{timestamp}.docx"

    return send_file(file, as_attachment=True, download_name=filename, cache_timeout=0)
