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

    ## We are looking for user entries that are not referenced anywhere and remove them

    # get all users
    cur = get_db().execute("SELECT userID FROM user")
    delete_candidates = []
    for row in cur:
        user = dict(row)
        delete_candidates.append(user["userID"])

    # filter users that are referenced in attendee
    delete_candidates_filtered_1 = []
    for u in delete_candidates:
        cur = get_db().execute("SELECT attendeeID FROM attendee WHERE userID = ?", (u,))
        rv = cur.fetchone()
        if not rv:
            delete_candidates_filtered_1.append(u)

    # filter users that are creator users
    delete_candidates_filtered_2 = []
    for c in delete_candidates_filtered_1:
        cur = get_db().execute("SELECT title FROM event WHERE creator = ?", (c,))
        rv = cur.fetchone()
        if not rv:
            delete_candidates_filtered_2.append(c)

    # remove remaining users
    for rc in delete_candidates_filtered_2:
        get_db().execute("DELETE FROM user WHERE userID = ?", (rc,))

    get_db().commit()

    ## Due to omission/bug the user 1 might not be validated. Lets fix that
    cur = get_db().execute(
        "SELECT mailVerificationToken FROM user WHERE userID = 1 AND mailVerificationToken IS NULL"
    )
    rv = cur.fetchone()
    if rv:
        get_db().execute(
            "UPDATE user SET mailVerificationToken = 'cfa82b3d-4649-4c23-8aa8-af56a9bddcb9' WHERE userID = 1"
        )
        get_db().commit()

    return redirect(url_for("superAdmin", superAdminToken=superAdminToken))
