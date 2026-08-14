import secrets, hashlib
from datetime import datetime, timezone, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id                    = db.Column(db.Integer, primary_key=True)
    username              = db.Column(db.String(32), unique=True, nullable=False, index=True)
    email                 = db.Column(db.String(256), unique=True, nullable=False, index=True)
    password_hash         = db.Column(db.String(256), nullable=False)
    created_at            = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_login            = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    reset_token_hash      = db.Column(db.String(64), nullable=True, index=True)
    reset_token_expires   = db.Column(db.DateTime, nullable=True)
    scans = db.relationship(
        "ScanHistory",
        back_populates="user",
        lazy="dynamic",
        cascade="all, delete-orphan"
    )

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    def generate_reset_token(self, expires_in_minutes=30):
        raw_token = secrets.token_urlsafe(32)
        self.reset_token_hash = hashlib.sha256(
            raw_token.encode()
        ).hexdigest()

        self.reset_token_expires = (
            datetime.now(timezone.utc).replace(microsecond=0)
            + timedelta(minutes=expires_in_minutes)
        )

        return raw_token

    def verify_reset_token(self, raw_token):
        if not self.reset_token_hash or not self.reset_token_expires:
            return False

        if datetime.now(timezone.utc) > self.reset_token_expires.replace(
            tzinfo=timezone.utc
        ):
            return False

        return (
            hashlib.sha256(raw_token.encode()).hexdigest()
            == self.reset_token_hash
        )

    def clear_reset_token(self):
        self.reset_token_hash = None
        self.reset_token_expires = None

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "name": self.username
        }


class ScanHistory(db.Model):
    __tablename__ = "scan_history"

    id            = db.Column(db.Integer, primary_key=True)
    user_id       = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True,
        index=True
    )
    file_name     = db.Column(db.String(256), nullable=True)
    file_size_kb  = db.Column(db.Float, nullable=True)
    image_width   = db.Column(db.Integer, nullable=True)
    image_height  = db.Column(db.Integer, nullable=True)
    label         = db.Column(db.String(16), nullable=False)
    confidence    = db.Column(db.Float, nullable=False)
    raw_score     = db.Column(db.Float, nullable=True)
    description   = db.Column(db.Text, nullable=True)
    signals       = db.Column(db.JSON, nullable=True)
    thumbnail_b64 = db.Column(db.Text, nullable=True)
    scanned_at    = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        index=True
    )

    user = db.relationship(
        "User",
        back_populates="scans"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "file_name": self.file_name,
            "file_size_kb": self.file_size_kb,
            "image_width": self.image_width,
            "image_height": self.image_height,
            "label": self.label,
            "confidence": round(self.confidence, 1),
            "description": self.description,
            "signals": self.signals or [],
            "thumbnail": self.thumbnail_b64,
            "scanned_at": (
                self.scanned_at.isoformat()
                if self.scanned_at
                else None
            ),
        }