from app.election import bp, get_db
from flask import render_template, current_app, abort


@bp.route("/")
def index():
    return "index"


@bp.route("/<uuid:electionID>")
def vote(electionID):
    # TODO deadline
    cur = get_db().execute(
        "SELECT * FROM election WHERE electionID = ? ",
        (str(electionID),),
    )
    rv = cur.fetchone()
    if not rv:
        current_app.logger.error(f"vote: electionID unknown")
        return abort(404)
    election_data = dict(rv)

    cur = get_db().execute(
        "SELECT * FROM election_options WHERE electionID = ? ORDER BY rank",
        (str(electionID),),
    )
    names = set()
    election_options = []
    for row in cur:
        a = dict(row)

        cur2 = get_db().execute(
            "SELECT optionID, COUNT(optionID) FROM election_vote WHERE optionID = ? GROUP BY optionID",
            (a["optionID"],),
        )
        count = 0
        rv2 = cur2.fetchone()
        if rv2:
            count = rv2[1]

        a["count"] = count
        election_options.append(a)

        cur2 = get_db().execute(
            "SELECT name FROM election_vote WHERE optionID = ?",
            (a["optionID"],),
        )
        for row2 in cur2:
            names.add(row2[0])

    return render_template(
        "electionVote.html",
        election_data=election_data,
        election_options=election_options,
        names=names,
    )
