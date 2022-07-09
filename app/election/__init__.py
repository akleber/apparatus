from flask import Blueprint

bp = Blueprint("election", __name__)

from app.election import election_routes
