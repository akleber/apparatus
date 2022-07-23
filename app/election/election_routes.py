from app.election import bp, get_db
from app import qrcode
from flask import (
    render_template,
    current_app,
    abort,
    request,
    redirect,
    session,
    url_for,
    make_response,
    send_file,
)
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import InputRequired, Length
from datetime import datetime, timedelta


class VoteForm(FlaskForm):
    name = StringField("Name", validators=[InputRequired(), Length(max=50)])


@bp.route("/")
def index():
    return "index"


@bp.route("/<uuid:electionID>")
def election(electionID):
    # TODO deadline
    cur = get_db().execute(
        "SELECT * FROM election WHERE electionID = ? ",
        (str(electionID),),
    )
    rv = cur.fetchone()
    if not rv:
        current_app.logger.error(f"election: electionID unknown")
        return abort(404)
    election_data = dict(rv)

    if election_data["mode"] == 0:
        election_data["widget"] = "checkbox"
    else:
        election_data["widget"] = "radio"

    cur = get_db().execute(
        "SELECT * FROM election_options WHERE electionID = ? ORDER BY rank",
        (str(electionID),),
    )
    count_total = 0
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

        count_total = count_total + count
        a["count"] = count
        election_options.append(a)

        cur2 = get_db().execute(
            "SELECT name FROM election_vote WHERE optionID = ?",
            (a["optionID"],),
        )
        for row2 in cur2:
            names.add(row2[0])

    election_data["count_total"] = count_total

    names = list(names)
    names.sort()
    form = VoteForm()

    return render_template(
        "electionVote.html",
        election_data=election_data,
        election_options=election_options,
        names=names,
        form=form,
    )


@bp.route("/<uuid:electionID>/vote", methods=["POST"])
def vote(electionID):
    form = VoteForm()
    if not form.validate_on_submit():
        current_app.logger.error(f"vote: form validation failed")
        abort(400)

    votes = request.form.getlist("option")
    print(votes)
    for vote in votes:
        vote_data = {"name": form.name.data, "optionID": vote}

        sql = """INSERT INTO election_vote (optionID, name) 
                VALUES (:optionID, :name);"""
        get_db().execute(sql, vote_data)

    get_db().commit()

    response = make_response(
        redirect(url_for("election.election", electionID=electionID))
    )
    # TODO add "expires=datetime-object"
    response.set_cookie("voted", str(electionID))
    return response


@bp.route("/<uuid:electionID>/edit")
def edit(electionID):
    cur = get_db().execute(
        "SELECT * FROM election WHERE electionID = ? ",
        (str(electionID),),
    )
    rv = cur.fetchone()
    if not rv:
        current_app.logger.error(f"edit: electionID unknown")
        return abort(404)
    election_data = dict(rv)

    election_options = []
    cur = get_db().execute(
        "SELECT * FROM election_options WHERE electionID = ? ORDER BY rank",
        (str(electionID),),
    )
    for row in cur:
        a = dict(row)
        election_options.append(a)

    in_a_weeks = datetime.now() + timedelta(weeks=1)
    in_a_weeks = in_a_weeks.replace(hour=23, minute=59)
    deadline_str = in_a_weeks.strftime("%Y-%m-%dT%H:%M")
    election_data["deadline_str"] = deadline_str

    return render_template(
        "electionEdit.html",
        election_data=election_data,
        election_options=election_options,
    )


@bp.route("/<uuid:electionID>/qr", methods=["GET"])
def qr(electionID):
    url = url_for("election.election", electionID=electionID)
    return send_file(
        qrcode(request.url_root[:-1] + url, mode="raw"), mimetype="image/png"
    )
