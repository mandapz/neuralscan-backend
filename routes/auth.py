import os, re, logging, requests
from datetime import datetime, timezone

from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from models.database import db, User

auth_bp = Blueprint("auth", __name__)
logger  = logging.getLogger(__name__)

USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]{3,32}$")
EMAIL_RE    = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

RESEND_API_URL = "https://api.resend.com/emails"


def _find_user_by_identifier(identifier):
    """identifier can be a username or an email — either works to log in."""
    identifier = (identifier or "").strip()
    return User.query.filter(
        (db.func.lower(User.username) == identifier.lower()) |
        (db.func.lower(User.email) == identifier.lower())
    ).first()


def _send_email(to_email, subject, body):
    """Sends via the Resend HTTPS API if configured; otherwise logs the
    message so it's still visible during local development. Configure
    RESEND_API_KEY and RESEND_FROM in .env to actually deliver emails
    in production.

    Uses an HTTPS API instead of raw SMTP because most PaaS providers
    (Railway included) block outbound SMTP ports (25/465/587) on
    non-enterprise plans to prevent abuse — HTTPS traffic isn't affected.
    """
    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        logger.warning("RESEND_API_KEY not configured — email not sent. Would have sent to %s:\n%s", to_email, body)
        return

    sender = os.environ.get("RESEND_FROM", "onboarding@resend.dev")

    try:
        resp = requests.post(
            RESEND_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "from": sender,
                "to": [to_email],
                "subject": subject,
                "text": body,
            },
            timeout=10,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        detail = getattr(e.response, "text", "")
        logger.error("Failed to send email to %s: %s %s", to_email, e, detail)


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    email    = (data.get("email") or "").strip()
    password = data.get("password") or ""

    if not USERNAME_RE.match(username):
        return jsonify({"error": "Username harus 3-32 karakter, hanya huruf/angka/underscore"}), 400
    if not EMAIL_RE.match(email):
        return jsonify({"error": "Format email tidak valid"}), 400
    if len(password) < 8:
        return jsonify({"error": "Password minimal 8 karakter"}), 400

    if _find_user_by_identifier(username) or User.query.filter(db.func.lower(User.email) == email.lower()).first():
        return jsonify({"error": "Username atau email sudah terdaftar"}), 409

    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    login_user(user, remember=True)
    return jsonify({"user": user.to_dict()}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    identifier = data.get("identifier") or data.get("username") or data.get("email") or ""
    password   = data.get("password") or ""

    user = _find_user_by_identifier(identifier)
    if not user or not user.check_password(password):
        return jsonify({"error": "Username/email atau password salah"}), 401

    user.last_login = datetime.now(timezone.utc)
    db.session.commit()
    login_user(user, remember=True)
    return jsonify({"user": user.to_dict()})


@auth_bp.route("/me")
def me():
    if current_user.is_authenticated:
        return jsonify({"authenticated": True, "user": current_user.to_dict()})
    return jsonify({"authenticated": False, "user": None}), 200


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return jsonify({"ok": True})


@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    data  = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip()

    # Always return the same generic message, whether or not the email
    # exists — so this endpoint can't be used to check who has an account.
    generic = {"message": "Jika email terdaftar, tautan reset password telah dikirim."}

    if EMAIL_RE.match(email):
        user = User.query.filter(db.func.lower(User.email) == email.lower()).first()
        if user:
            raw_token = user.generate_reset_token()
            db.session.commit()
            frontend = os.environ.get("FRONTEND_URL", "http://localhost:3000")
            reset_link = f"{frontend}/reset-password?token={raw_token}&email={user.email}"
            _send_email(
                user.email,
                "Reset Password NeuralScan",
                f"Halo {user.username},\n\n"
                f"Klik tautan berikut untuk mengatur ulang password kamu (berlaku 30 menit):\n{reset_link}\n\n"
                f"Kalau kamu tidak meminta ini, abaikan saja email ini.",
            )
    return jsonify(generic)


@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    data     = request.get_json(silent=True) or {}
    token    = data.get("token") or ""
    email    = (data.get("email") or "").strip()
    password = data.get("password") or ""

    if len(password) < 8:
        return jsonify({"error": "Password minimal 8 karakter"}), 400

    user = User.query.filter(db.func.lower(User.email) == email.lower()).first() if email else None
    if not user or not user.verify_reset_token(token):
        return jsonify({"error": "Tautan reset tidak valid atau sudah kedaluwarsa"}), 400

    user.set_password(password)
    user.clear_reset_token()
    db.session.commit()
    return jsonify({"message": "Password berhasil diubah. Silakan masuk dengan password baru."})