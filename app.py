"""
Flask Employee Manager

Creates the Flask app, configures session cookie security, enables CSRF
protection, registers route Blueprints, and starts the local development server.
"""

from flask import Flask
from flask_wtf.csrf import CSRFProtect

from config import FLASK_DEBUG, FLASK_SECRET_KEY
from routes.auth_routes import auth_bp
from routes.employee_routes import employee_bp
from routes.payraise_routes import payraise_bp

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

csrf = CSRFProtect(app)

app.register_blueprint(auth_bp)
app.register_blueprint(employee_bp)
app.register_blueprint(payraise_bp)

if __name__ == "__main__":
    app.run(debug=FLASK_DEBUG)
