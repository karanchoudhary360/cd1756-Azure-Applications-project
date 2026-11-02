    import os
from urllib.parse import quote_plus


class Config:
    """Application configuration loaded from environment variables."""

    SECRET_KEY = os.getenv("SECRET_KEY", "local-development-only-change-me")
    SESSION_TYPE = "filesystem"
    SESSION_PERMANENT = False

    BLOB_ACCOUNT = os.getenv("BLOB_ACCOUNT", "")
    BLOB_STORAGE_KEY = os.getenv("BLOB_STORAGE_KEY", "")
    BLOB_CONTAINER = os.getenv("BLOB_CONTAINER", "images")

    SQL_SERVER = os.getenv("SQL_SERVER", "")
    SQL_DATABASE = os.getenv("SQL_DATABASE", "")
    SQL_USER_NAME = os.getenv("SQL_USER_NAME", "")
    SQL_PASSWORD = os.getenv("SQL_PASSWORD", "")

    _odbc = quote_plus(
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER=tcp:{SQL_SERVER},1433;"
        f"DATABASE={SQL_DATABASE};"
        f"UID={SQL_USER_NAME};"
        f"PWD={SQL_PASSWORD};"
        "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
    )
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "SQLALCHEMY_DATABASE_URI", f"mssql+pyodbc:///?odbc_connect={_odbc}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    CLIENT_ID = os.getenv("CLIENT_ID", "")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET", "")
    AUTHORITY = os.getenv("AUTHORITY", "https://login.microsoftonline.com/common")
    REDIRECT_PATH = "/getAToken"
    SCOPE = ["User.Read"]
