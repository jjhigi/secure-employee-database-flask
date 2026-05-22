"""
Authentication Helper Functions

Provides shared access-control helpers used by route Blueprints.
"""

from flask import abort, session

from routes.auth_routes import require_login


def require_level(allowed_levels):
    """
    Require a logged-in user with one of the allowed security levels.

    Unauthorized users receive the app's existing 404 behavior so protected
    pages are not exposed through permission error details.
    """
    guard = require_login()
    if guard:
        return guard

    if session.get("SecurityLevel") not in allowed_levels:
        return abort(404)

    return None
