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


def get_event_data_verify_admin(adminToken: uuid, eventID: uuid) -> dict:
    print("get_event_data")
    cur = get_db().execute("SELECT * FROM event WHERE eventID = ?", (str(eventID),))
    rv = cur.fetchone()
    if not rv:
        print("404")
        abort(404)
    event_data = dict(rv)
    if event_data['adminToken'] != str(adminToken):
        abort(401)
    
    return event_data


@app.route("/eventAdmin/<uuid:adminToken>/<uuid:eventID>", methods=["GET"])
def eventAdmin(adminToken, eventID):
    event_data = get_event_data_verify_admin(adminToken, eventID)

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
    return render_template("eventEdit.html", event_data=event_data, add=True)


@app.route("/eventAdmin/<uuid:adminToken>/<uuid:eventID>/edit", methods=["GET"])
def eventAdmin_event_edit(adminToken, eventID):
    event_data = get_event_data_verify_admin(adminToken, eventID)

    if event_data['adminToken'] != str(adminToken):
        return abort(401)

    return render_template("eventEdit.html", event_data=event_data, add=False)


@app.route("/eventAdmin/<uuid:adminToken>/<uuid:eventID>/save", methods=["POST"])
def eventAdmin_event_save(adminToken, eventID):
    now = datetime.utcnow()

    blob = None
    if "bannerImage" in request.files:
        file = request.files["bannerImage"]
        if file.filename != "":
            blob = file.stream.read()

    cur = get_db().execute(
        "SELECT * FROM event WHERE eventID = ?",
        (str(eventID),),
    )
    rv = cur.fetchone()
    if rv:
        # update event
        event_data = dict(rv)
        if event_data['adminToken'] != str(adminToken):
            abort(401)

        sql_data = {
            "eventID": str(eventID),
            "active": request.form.get("active", "0"),
            "title": request.form.get("title"),
            "description": request.form.get("description"),
            "lastChangedDate": now.isoformat(" "),
        }
        sql = """UPDATE event SET active = :active, title = :title, description = :description, lastChangedDate = :lastChangedDate 
                 WHERE eventID = :eventID;"""

        if blob:
            sql_image = """UPDATE event SET bannerImage = ? WHERE eventID = ?;"""
            get_db().execute(sql_image, (memoryview(blob), str(eventID)))

    else:
        # add event
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
            "adminToken": str(uuid.uuid4()),
            "bannerImage": blob,
        }
        sql = """INSERT INTO event (eventID, tinylink, active, title, description, creator, creationDate, lastChangedDate, adminToken, bannerImage) 
                 VALUES (:eventID, :tinylink, :active, :title, :description, :creator, :creationDate, :lastChangedDate, :adminToken, :bannerImage);"""

    get_db().execute(sql, sql_data)
    get_db().commit()

    return redirect(url_for("eventAdmin", adminToken=adminToken, eventID=eventID))


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


@app.route("/eventAdmin/<uuid:adminToken>/<uuid:eventID>/activity/add", methods=["GET"])
def eventAdmin_activity_add(adminToken, eventID):
    event_data = get_event_data_verify_admin(adminToken, eventID)

    activity_data = {"activityID": str(uuid.uuid4()), "title": "", "description": ""}
    return render_template(
        "activityEdit.html", event_data=event_data, activity_data=activity_data
    )


@app.route(
    "/eventAdmin/<uuid:adminToken>/<uuid:eventID>/activity/edit/<uuid:activityID>", methods=["GET"]
)
def eventAdmin_activity_edit(adminToken, eventID, activityID):
    event_data = get_event_data_verify_admin(adminToken, eventID)

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

    return render_template(
        "activityEdit.html", event_data=event_data, activity_data=activity_data
    )


@app.route(
    "/eventAdmin/<uuid:adminToken>/<uuid:eventID>/activity/save/<uuid:activityID>", methods=["POST"]
)
def eventAdmin_activity_save(adminToken, eventID, activityID):
    event_data = get_event_data_verify_admin(adminToken, eventID)
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

    return redirect(url_for("eventAdmin", adminToken=adminToken, eventID=eventID))


@app.route(
    "/eventAdmin/<uuid:adminToken>/<uuid:eventID>/activity/delete/<uuid:activityID>", methods=["GET"]
)
def eventAdmin_activity_delete(adminToken, eventID, activityID):
    event_data = get_event_data_verify_admin(adminToken, eventID)

    get_db().execute(
        "DELETE FROM activity WHERE activityID = ? and eventID = ?",
        (str(activityID), str(eventID)),
    )
    get_db().commit()

    return redirect(url_for("eventAdmin", adminToken=adminToken, eventID=eventID))


@app.route("/eventAdmin/<uuid:adminToken>/<uuid:eventID>/attendees/xlsx")
def eventAdmin_attendees_xlsx(adminToken, eventID):
    event_data = get_event_data_verify_admin(adminToken, eventID)

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


@app.route("/eventAdmin/<uuid:adminToken>/<uuid:eventID>/activity/docx", methods=["GET"])
def eventAdmin_activity_docx(adminToken, eventID):
    event_data = get_event_data_verify_admin(adminToken, eventID)

    cur = get_db().execute(
        "SELECT title, description FROM activity WHERE eventID = ?", (str(eventID),)
    )

    document = Document()
    document.add_heading(event_data['title'], 0)

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
