from app.election import bp


@bp.route("/")
def index():
    return "election"
