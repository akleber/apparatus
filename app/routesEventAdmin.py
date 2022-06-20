from app import app, get_db, qrcode
from flask import render_template, abort, url_for, send_file, request, redirect
from datetime import datetime
from pyexcel_xlsx import save_data
from collections import OrderedDict
from docx import Document
from htmldocx import HtmlToDocx
import markdown
from io import BytesIO
import sqlite3
import uuid
from datetime import datetime


@app.route("/eventAdmin/<eventID>", methods=["GET"])
def eventAdmin(eventID):
    cur = get_db().execute(
        "SELECT eventID, title, tinylink FROM event WHERE eventID = ?", (eventID,)
    )
    rv = cur.fetchone()
    if not rv:
        return abort(404)
    event_data = dict(rv)

    activity_data = []
    cur = get_db().execute("SELECT * FROM activity WHERE eventID = ?", (eventID,))
    for row in cur:
        activity_data.append(dict(row))

    return render_template(
        "eventAdmin.html", event_data=event_data, activity_data=activity_data
    )


@app.route("/eventAdmin/<eventID>/qr", methods=["GET"])
def qr(eventID):
    cur = get_db().execute("SELECT tinylink FROM event WHERE eventID = ?", (eventID,))
    rv = cur.fetchone()
    if not rv:
        return abort(404)

    url = url_for("t", tinylink=rv["tinylink"])
    return send_file(
        qrcode(request.url_root[:-1] + url, mode="raw"), mimetype="image/png"
    )


@app.route("/eventAdmin/<eventID>/activity/add", methods=["GET"])
def eventAdmin_activity_add(eventID):
    event_data = {"eventID": eventID}
    activity_data = {"activityID": str(uuid.uuid4()), "title": "", "description": ""}
    return render_template(
        "activityEdit.html", event_data=event_data, activity_data=activity_data
    )


@app.route("/eventAdmin/<eventID>/activity/edit/<activityID>", methods=["GET"])
def eventAdmin_activity_edit(eventID, activityID):
    event_data = {"eventID": eventID}

    cur = get_db().execute("SELECT * FROM activity WHERE activityID = ?", (activityID,))
    rv = cur.fetchone()
    if not rv:
        return abort(404)
    activity_data = dict(rv)

    print(activity_data)

    return render_template(
        "activityEdit.html", event_data=event_data, activity_data=activity_data
    )


@app.route("/eventAdmin/<eventID>/activity/save/<activityID>", methods=["POST"])
def eventAdmin_activity_save(eventID, activityID):
    cur = get_db().execute(
        "SELECT * FROM activity WHERE activityID = ? and eventID = ?",
        (activityID, eventID),
    )
    rv = cur.fetchone()
    if rv:
        print("update event")
    else:
        print("add event")
        now = datetime.utcnow()

        user_data = {
            "activityID": request.form.get("activityID"),
            "eventID": request.form.get("eventID"),
            "active": request.form.get("active"),
            "title": request.form.get("title"),
            "descriptions": request.form.get("descriptions"),
            "seats": request.form.get("seats"),
            "creationDate": now.isoformat(" "),
            "lastChangedDate": now.isoformat(" "),
        }
        sql = """INSERT INTO activity (activityID, eventID, active, title, description, seats, creationDate, lastChangedDate) 
                 VALUES (:activityID, :eventID, :active, :title, :descriptions, :seats, :creationDate, :lastChangedDate);"""

    cur = get_db().execute(sql, user_data)

    return redirect(url_for("eventAdmin", eventID=eventID))


@app.route("/eventAdmin/<eventID>/attendees/xlsx")
def eventAdmin_attendees_xlsx(eventID):
    excel_rows = []
    cur = get_db().execute("SELECT * FROM eventAttendees WHERE eventID = ?", (eventID,))

    excel_col_names = []
    for col_name in cur.description:
        excel_col_names.append(col_name[0])
    excel_rows.append(excel_col_names)

    for row in cur:
        excel_rows.append(list(row))

    data = OrderedDict()
    data.update({"Sheet 1": excel_rows})
    # data.update({"Sheet 2": [["row 1", "row 2", "row 3"]]})

    io = BytesIO()
    save_data(io, data)
    io.seek(0)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"event_export_{timestamp}.xlsx"

    return send_file(io, as_attachment=True, download_name=filename, cache_timeout=0)


@app.route("/eventAdmin/<eventID>/activity/docx", methods=["GET"])
def eventAdmin_activity_docx(eventID):
    cur = get_db().execute("SELECT title FROM event WHERE eventID = ?", (eventID,))
    rv = cur.fetchone()
    if not rv:
        return abort(404)
    eventTitle = rv["title"]

    cur = get_db().execute(
        "SELECT title, description FROM activity WHERE eventID = ?", (eventID,)
    )

    document = Document()
    document.add_heading(eventTitle, 0)

    new_parser = HtmlToDocx()

    for activity in cur:
        document.add_heading(activity["title"], level=1)

        md = activity["description"]
        html = markdown.markdown(md)

        new_parser.add_html_to_document(html, document)

    file = BytesIO()
    document.save(file)
    file.seek(0)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"activity_export_{timestamp}.docx"

    return send_file(file, as_attachment=True, download_name=filename, cache_timeout=0)
