"""POST /api/detect"""
import base64, io, os, logging
from flask import Blueprint, request, jsonify
from flask_login import current_user
from PIL import Image

from models.database import db, ScanHistory
from utils.model import run_inference, make_thumbnail, get_image_dimensions
from utils.description import get_description

detect_bp = Blueprint("detect", __name__)
logger    = logging.getLogger(__name__)

ALLOWED_MIME = {"image/jpeg","image/png","image/webp","image/jpg"}
MAX_BYTES    = int(os.environ.get("MAX_CONTENT_LENGTH_MB", 10)) * 1024 * 1024


@detect_bp.route("/detect", methods=["POST"])
def detect():
    if "image" not in request.files:
        return jsonify({"error": "No image field"}), 400
    file = request.files["image"]
    if not file.filename:
        return jsonify({"error": "Empty filename"}), 400

    image_bytes = file.read()
    if len(image_bytes) > MAX_BYTES:
        return jsonify({"error": f"File too large (max {MAX_BYTES//1024//1024} MB)"}), 413

    try:
        img = Image.open(io.BytesIO(image_bytes)); img.verify()
    except Exception:
        return jsonify({"error": "Invalid or corrupt image"}), 400

    mime = file.content_type or "image/jpeg"
    if mime not in ALLOWED_MIME:
        return jsonify({"error": f"Unsupported type: {mime}"}), 415

    # 1. Inference
    try:
        result = run_inference(image_bytes)
    except Exception as e:
        logger.error("Inference error: %s", e)
        return jsonify({"error": "Detection failed"}), 500

    label      = result["label"]
    confidence = result["confidence"]
    raw_score  = result.get("raw_score")

    # 2. Description (hardcoded pool)
    desc_data   = get_description(label)
    description = desc_data["description"]
    signals     = desc_data["signals"]

    # 3. Thumbnail
    try:
        thumb = make_thumbnail(image_bytes, 240)
        thumbnail_b64 = "data:image/jpeg;base64," + base64.b64encode(thumb).decode()
    except Exception:
        thumbnail_b64 = None

    # 4. Save to DB if authenticated
    scan_id = None
    if current_user.is_authenticated:
        try:
            w, h = get_image_dimensions(image_bytes)
            entry = ScanHistory(
                user_id       = current_user.id,
                file_name     = file.filename,
                file_size_kb  = round(len(image_bytes)/1024, 1),
                image_width   = w,
                image_height  = h,
                label         = label,
                confidence    = float(confidence),
                raw_score     = raw_score,
                description   = description,
                signals       = signals,
                thumbnail_b64 = thumbnail_b64,
            )
            db.session.add(entry)
            db.session.commit()
            scan_id = entry.id
        except Exception as e:
            logger.error("DB save failed: %s", e)
            db.session.rollback()

    return jsonify({
        "id"         : scan_id,
        "label"      : label,
        "confidence" : confidence,
        "raw_score"  : raw_score,
        "description": description,
        "signals"    : signals,
        "thumbnail"  : thumbnail_b64,
        "file_name"  : file.filename,
        "saved"      : scan_id is not None,
    })
