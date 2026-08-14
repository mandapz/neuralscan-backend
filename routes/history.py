from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models.database import db, ScanHistory

history_bp = Blueprint("history", __name__)

@history_bp.route("", methods=["GET"])
@login_required
def list_history():
    page     = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)
    p = (ScanHistory.query.filter_by(user_id=current_user.id)
         .order_by(ScanHistory.scanned_at.desc())
         .paginate(page=page, per_page=per_page, error_out=False))
    return jsonify({"items": [s.to_dict() for s in p.items],
                    "total": p.total, "page": page, "pages": p.pages, "per_page": per_page})

@history_bp.route("/stats", methods=["GET"])
@login_required
def stats():
    scans = ScanHistory.query.filter_by(user_id=current_user.id).all()
    total = len(scans)
    ai    = sum(1 for s in scans if s.label == "AI")
    return jsonify({"total": total, "ai_count": ai, "real_count": total - ai,
                    "avg_confidence": round(sum(s.confidence for s in scans)/total,1) if total else None})

@history_bp.route("/<int:scan_id>", methods=["GET"])
@login_required
def get_scan(scan_id):
    return jsonify(ScanHistory.query.filter_by(id=scan_id, user_id=current_user.id).first_or_404().to_dict())

@history_bp.route("/<int:scan_id>", methods=["DELETE"])
@login_required
def delete_scan(scan_id):
    s = ScanHistory.query.filter_by(id=scan_id, user_id=current_user.id).first_or_404()
    db.session.delete(s); db.session.commit()
    return jsonify({"deleted": True, "id": scan_id})

@history_bp.route("", methods=["DELETE"])
@login_required
def clear_history():
    deleted = ScanHistory.query.filter_by(user_id=current_user.id).delete(synchronize_session=False)
    db.session.commit()
    return jsonify({"deleted": deleted})
