from datetime import datetime
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy

# shared SQLAlchemy instance
# imported and initialized by the application factory (app.py)
db = SQLAlchemy()


class User(UserMixin, db.Model):
    """Simple user model for authentication.

    Each user is associated with exactly one ``client_slug``.  There is an
    optional ``is_admin`` flag that allows the creation of other users via the
    web interface.
    """

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    client_slug = db.Column(db.String(100), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password: str):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username} ({self.client_slug})>"
