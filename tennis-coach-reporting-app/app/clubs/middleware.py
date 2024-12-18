from functools import wraps
from flask import request, current_app
from flask_login import current_user

def get_club_from_request():
    """Extract club from subdomain"""
    if 'localhost' in request.host:
        # For local testing, return first club or specific test club
        from app.models import TennisClub
        return TennisClub.query.first().subdomain
    host = request.host.split(':')[0]
    return host.split('.')[0]

def verify_club_access():
    """Middleware to verify user has access to requested club"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            subdomain = get_club_from_request()
            if not subdomain:
                return f(*args, **kwargs)
                
            if not current_user.tennis_club.subdomain == subdomain:
                return "Unauthorized", 403
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator