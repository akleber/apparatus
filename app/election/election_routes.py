from app.election import bp, get_db


@bp.route("/")
def index():
    db = get_db()

    return "election"
