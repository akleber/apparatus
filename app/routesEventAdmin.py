from app import app, get_db
from flask import (
    render_template,
    send_from_directory,
    abort,
)
from datetime import datetime
from pyexcel_xlsx import save_data
from collections import OrderedDict


@app.route("/eventAdmin/<eventID>", methods=["GET"])
def eventAdmin(eventID):
    cur = get_db().execute(
        "SELECT title, description FROM event WHERE eventID = ?", (eventID,)
    )
    rv = cur.fetchone()
    if not rv:
        return abort(404)

    event_data = {}
    event_data["eventID"] = eventID
    event_data["title"] = rv[0]

    return render_template("eventAdmin.html", event_data=event_data)


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
