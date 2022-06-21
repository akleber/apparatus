from app import app, get_db, qrcode, utils
from flask import render_template, abort, url_for, send_file, request, redirect
from datetime import datetime
from pyexcel_xlsx import save_data
from collections import OrderedDict
from docx import Document
from htmldocx import HtmlToDocx
import markdown
from io import BytesIO
import uuid
from datetime import datetime
import shortuuid


@app.route("/eventAdmin/<uuid:eventID>", methods=["GET"])
def eventAdmin(eventID):
    cur = get_db().execute("SELECT * FROM event WHERE eventID = ?", (str(eventID),))
    rv = cur.fetchone()
    if not rv:
        return abort(404)
    event_data = dict(rv)

    activity_data = []
    cur = get_db().execute("SELECT * FROM activity WHERE eventID = ?", (str(eventID),))
    for row in cur:
        activity_data.append(dict(row))

    return render_template(
        "eventAdmin.html", event_data=event_data, activity_data=activity_data
    )


@app.route("/eventAdmin/add", methods=["GET"])
def eventAdmin_event_add():
    event_data = {"eventID": str(uuid.uuid4()), "title": "", "description": ""}
    return render_template("eventEdit.html", event_data=event_data)


@app.route("/eventAdmin/<uuid:eventID>/edit", methods=["GET"])
def eventAdmin_event_edit(eventID):
    cur = get_db().execute(
        "SELECT * FROM event WHERE eventID = ?",
        (str(eventID),),
    )
    rv = cur.fetchone()
    if not rv:
        return abort(404)
    event_data = dict(rv)

    return render_template("eventEdit.html", event_data=event_data)


@app.route("/eventAdmin/<uuid:eventID>/save", methods=["POST"])
def eventAdmin_event_save(eventID):
    now = datetime.utcnow()

    cur = get_db().execute(
        "SELECT * FROM event WHERE eventID = ?",
        (str(eventID),),
    )
    rv = cur.fetchone()
    if rv:
        # update event
        user_data = {
            "eventID": str(eventID),
            "active": request.form.get("active", "0"),
            "title": request.form.get("title"),
            "description": request.form.get("description"),
            "lastChangedDate": now.isoformat(" "),
        }
        sql = """UPDATE event SET active = :active, title = :title, description = :description, lastChangedDate = :lastChangedDate 
                 WHERE eventID = :eventID;"""

    else:
        # add event
        # TODO finish event Add (missing user)
        userID, user_data = utils.add_user(
            request.form.get("firstName"),
            request.form.get("familyName"),
            request.form.get("mail"),
        )

        tinylink = shortuuid.uuid()[:10]

        sql_data = {
            "eventID": str(eventID),
            "tinylink": tinylink,
            "active": request.form.get("active", "0"),
            "title": request.form.get("title"),
            "description": request.form.get("description"),
            "creator": userID,
            "creationDate": now.isoformat(" "),
            "lastChangedDate": now.isoformat(" "),
            "adminToken": uuid.uuid4(),
        }
        sql = """INSERT INTO event (eventID, tinylink, active, title, description, creator, creationDate, lastChangedDate, adminToken) 
                 VALUES (:eventID, :tinylink, :active, :title, :description, :creator, :creationDate, :lastChangedDate, :adminToken);"""

    get_db().execute(sql, sql_data)
    get_db().commit()

    return redirect(url_for("eventAdmin", eventID=eventID))


@app.route("/eventAdmin/<uuid:eventID>/qr", methods=["GET"])
def qr(eventID):
    cur = get_db().execute(
        "SELECT tinylink FROM event WHERE eventID = ?", (str(eventID),)
    )
    rv = cur.fetchone()
    if not rv:
        return abort(404)

    url = url_for("t", tinylink=rv["tinylink"])
    return send_file(
        qrcode(request.url_root[:-1] + url, mode="raw"), mimetype="image/png"
    )


@app.route("/eventAdmin/<uuid:eventID>/activity/add", methods=["GET"])
def eventAdmin_activity_add(eventID):
    event_data = {"eventID": str(eventID)}
    activity_data = {"activityID": str(uuid.uuid4()), "title": "", "description": ""}
    return render_template(
        "activityEdit.html", event_data=event_data, activity_data=activity_data
    )


@app.route(
    "/eventAdmin/<uuid:eventID>/activity/edit/<uuid:activityID>", methods=["GET"]
)
def eventAdmin_activity_edit(eventID, activityID):
    event_data = {"eventID": str(eventID)}

    cur = get_db().execute(
        "SELECT * FROM activity WHERE eventID = ? AND activityID = ?",
        (
            str(eventID),
            str(activityID),
        ),
    )
    rv = cur.fetchone()
    if not rv:
        return abort(404)
    activity_data = dict(rv)

    print(activity_data)

    return render_template(
        "activityEdit.html", event_data=event_data, activity_data=activity_data
    )


@app.route(
    "/eventAdmin/<uuid:eventID>/activity/save/<uuid:activityID>", methods=["POST"]
)
def eventAdmin_activity_save(eventID, activityID):
    now = datetime.utcnow()

    cur = get_db().execute(
        "SELECT * FROM activity WHERE activityID = ? and eventID = ?",
        (str(activityID), str(eventID)),
    )
    rv = cur.fetchone()
    if rv:
        user_data = {
            "activityID": str(activityID),
            "eventID": str(eventID),
            "active": request.form.get("active", "0"),
            "title": request.form.get("title"),
            "description": request.form.get("description"),
            "seats": request.form.get("seats", ""),
            "lastChangedDate": now.isoformat(" "),
        }
        sql = """UPDATE activity SET active = :active, title = :title, description = :description, seats = :seats, lastChangedDate = :lastChangedDate 
                 WHERE eventID = :eventID AND activityID = :activityID;"""

    else:
        user_data = {
            "activityID": str(activityID),
            "eventID": str(eventID),
            "active": request.form.get("active", "0"),
            "title": request.form.get("title"),
            "description": request.form.get("description"),
            "seats": request.form.get("seats", ""),
            "creationDate": now.isoformat(" "),
            "lastChangedDate": now.isoformat(" "),
        }
        sql = """INSERT INTO activity (activityID, eventID, active, title, description, seats, creationDate, lastChangedDate) 
                 VALUES (:activityID, :eventID, :active, :title, :description, :seats, :creationDate, :lastChangedDate);"""

    get_db().execute(sql, user_data)
    get_db().commit()

    return redirect(url_for("eventAdmin", eventID=eventID))


@app.route(
    "/eventAdmin/<uuid:eventID>/activity/delete/<uuid:activityID>", methods=["GET"]
)
def eventAdmin_activity_delete(eventID, activityID):
    get_db().execute(
        "DELETE FROM activity WHERE activityID = ? and eventID = ?",
        (str(activityID), str(eventID)),
    )
    get_db().commit()

    return redirect(url_for("eventAdmin", eventID=eventID))


@app.route("/eventAdmin/<uuid:eventID>/attendees/xlsx")
def eventAdmin_attendees_xlsx(eventID):
    excel_rows = []
    cur = get_db().execute(
        "SELECT * FROM eventAttendees WHERE eventID = ?", (str(eventID),)
    )

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


@app.route("/eventAdmin/<uuid:eventID>/activity/docx", methods=["GET"])
def eventAdmin_activity_docx(eventID):
    cur = get_db().execute("SELECT title FROM event WHERE eventID = ?", (str(eventID),))
    rv = cur.fetchone()
    if not rv:
        return abort(404)
    eventTitle = rv["title"]

    cur = get_db().execute(
        "SELECT title, description FROM activity WHERE eventID = ?", (str(eventID),)
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
