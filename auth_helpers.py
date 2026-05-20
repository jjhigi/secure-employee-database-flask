"""
Authentication Helper Functions

Provides shared access-control helpers used by route Blueprints.
"""

from flask import abort, session

from routes.auth_routes import require_login


def require_level(allowed):
    """Require that the current user has one of the allowed security levels."""
    guard = require_login()
    if guard:
        return guard

    if session.get("SecurityLevel") not in allowed:
        # If the level is not allowed, pretend the page does not exist.
        return abort(404)

    return None
