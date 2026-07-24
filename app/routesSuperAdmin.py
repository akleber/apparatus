from flask import abort, redirect, render_template, url_for

from app import app, get_db


def ensureSuperAdmin(superAdminToken):
    if superAdminToken != app.config["SUPER_ADMIN_SECRET"]:
        app.logger.error("superAdmin: secret wrong")
        abort(404)


def ensureEventID(eventID):
    cur = get_db().execute(
        "SELECT title FROM event WHERE eventID = ?",
        (str(eventID),),
    )
    rv = cur.fetchone()
    if not rv:
        app.logger.error(f"eventID {eventID} unknown")
        return abort(404)


@app.route("/superAdmin/<superAdminToken>", methods=["GET"])
def superAdmin(superAdminToken):
    ensureSuperAdmin(superAdminToken)

    events_data = []
    cur = get_db().execute("SELECT * FROM event ORDER BY creationDate DESC")
    for row in cur:
        events_data.append(dict(row))

    return render_template(
        "superAdmin.html", events_data=events_data, superAdminToken=superAdminToken
    )


@app.route("/superAdmin/<superAdminToken>/<uuid:eventID>/delete", methods=["GET"])
def superAdminDeleteEvent(superAdminToken, eventID):
    ensureSuperAdmin(superAdminToken)
    ensureEventID(eventID)

    activity_data = []
    cur = get_db().execute("SELECT * FROM activity WHERE eventID = ?", (str(eventID),))
    for row in cur:
        activity_data.append(dict(row))

    attendee_data = []
    for a in activity_data:
        cur = get_db().execute(
            "SELECT * FROM attendee WHERE primaryActivityChoice = ? OR secondaryActivityChoice = ?",
            (str(a["activityID"]), str(a["activityID"])),
        )
        for row in cur:
            attendee_data.append(dict(row))

    for at in attendee_data:
        get_db().execute("DELETE FROM user WHERE userID = ?", (str(at["userID"]),))

    for a in activity_data:
        get_db().execute(
            "DELETE FROM attendee WHERE primaryActivityChoice = ? OR secondaryActivityChoice = ?",
            (str(a["activityID"]), str(a["activityID"])),
        )

    get_db().execute("DELETE FROM activity WHERE eventID = ?", (str(eventID),))

    # We do not delete the creator user here. Due to a bug we can have duplicated userID in events.
    # Users can be cleared through the maintenance.
    # cur = get_db().execute(
    #     "SELECT creator FROM event WHERE eventID = ?", (str(eventID),)
    # )
    # rv = cur.fetchone()
    # creator = rv["creator"]
    # get_db().execute("DELETE FROM user WHERE userID = ?", (str(creator),))

    get_db().execute("DELETE FROM event WHERE eventID = ?", (str(eventID),))

    get_db().commit()

    return redirect(url_for("superAdmin", superAdminToken=superAdminToken))


@app.route("/superAdmin/<superAdminToken>/maintenance", methods=["GET"])
def superAdminMaintenance(superAdminToken):
    ensureSuperAdmin(superAdminToken)

    users_data = []
    delete_candidates = []

    cur = get_db().execute("SELECT userID FROM user")
    for row in cur:
        user = dict(row)
        users_data.append(user["userID"])

    for u in users_data:
        cur = get_db().execute(
            "SELECT attendeeID FROM attendee WHERE userID = ?", (str(u),)
        )
        rv = cur.fetchone()
        if not rv:
            delete_candidates.append(u)

    revised_delete_candidates = []
    for c in delete_candidates:
        cur = get_db().execute("SELECT title FROM event WHERE creator = ?", (c,))
        rv = cur.fetchone()
        if not rv:
            revised_delete_candidates.append(c)

    for rc in revised_delete_candidates:
        get_db().execute("DELETE FROM user WHERE userID = ?", (rc,))

    get_db().commit()

    return redirect(url_for("superAdmin", superAdminToken=superAdminToken))
