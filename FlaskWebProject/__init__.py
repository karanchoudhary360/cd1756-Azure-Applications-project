"""Flask application package."""
import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Flask
from flask_login import LoginManager
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy

from config import Config

app = Flask(__name__)
app.config.from_object(Config)

log_level = getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO)
app.logger.setLevel(log_level)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")

# Console logging is displayed by Azure App Service Log Stream.
if not any(getattr(handler, "_cms_console", False) for handler in app.logger.handlers):
    console_handler = logging.StreamHandler()
    console_handler._cms_console = True
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    app.logger.addHandler(console_handler)

# A local rotating log is useful when the project is run outside Azure.
if not app.debug and not app.testing:
    file_handler = RotatingFileHandler("cms.log", maxBytes=1_000_000, backupCount=3)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    app.logger.addHandler(file_handler)

Session(app)
db = SQLAlchemy(app)
login = LoginManager(app)
login.login_view = "login"
login.login_message_category = "info"

from FlaskWebProject import views  # noqa: E402,F401
