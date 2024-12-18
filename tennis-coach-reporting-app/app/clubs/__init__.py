from flask import Blueprint

club_management = Blueprint('club_management', __name__)

from app.clubs import routes