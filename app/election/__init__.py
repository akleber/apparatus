from flask import Blueprint, g
import sqlite3


ELECTION_DB = "election.db"

bp = Blueprint("election", __name__)


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(ELECTION_DB)
    db.row_factory = sqlite3.Row
    return db


from app.election import election_routes
