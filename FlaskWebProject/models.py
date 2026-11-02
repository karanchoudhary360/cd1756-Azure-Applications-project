from datetime import datetime
import secrets

from azure.storage.blob import BlockBlobService
from flask import flash
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from FlaskWebProject import app, db, login


def _blob_service():
    return BlockBlobService(
        account_name=app.config["BLOB_ACCOUNT"],
        account_key=app.config["BLOB_STORAGE_KEY"],
    )


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    def __repr__(self):
        return f"<User {self.username}>"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


@login.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Post(db.Model):
    __tablename__ = "posts"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    author = db.Column(db.String(75), nullable=False)
    body = db.Column(db.String(800), nullable=False)
    image_path = db.Column(db.String(100))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    def __repr__(self):
        return f"<Post {self.title}>"

    def save_changes(self, form, file, user_id, new=False):
        self.title = form.title.data.strip()
        self.author = form.author.data.strip()
        self.body = form.body.data.strip()
        self.user_id = user_id

        if file and file.filename:
            original_name = secure_filename(file.filename)
            extension = original_name.rsplit(".", 1)[-1].lower()
            new_name = f"{secrets.token_hex(16)}.{extension}"
            old_name = self.image_path
            try:
                service = _blob_service()
                service.create_blob_from_stream(app.config["BLOB_CONTAINER"], new_name, file)
                self.image_path = new_name
                if old_name:
                    service.delete_blob(app.config["BLOB_CONTAINER"], old_name)
            except Exception:
                db.session.rollback()
                app.logger.exception("Blob upload failed")
                flash("The image could not be uploaded. Please try again.", "danger")
                raise

        if new:
            db.session.add(self)
        db.session.commit()
