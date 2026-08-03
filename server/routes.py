from flask import Blueprint, current_app, g, jsonify, request

from server.agent import resume_run, run_agent
from server.auth import require_auth
from server.models import Conversation, Message, Run, RunStep, db

api_bp = Blueprint("api", __name__, url_prefix="/api")


def _serialize_steps(run, include_messages=False):
    steps = RunStep.query.filter_by(run_id=run.id).order_by(RunStep.seq).all()
    out = []
    for s in steps:
        item = {
            "seq": s.seq,
            "kind": s.kind,
            "tool_name": s.tool_name,
            "arguments": s.arguments,
            "result": s.result,
            "latency_ms": s.latency_ms,
        }
        if include_messages:
            item["llm_messages"] = s.llm_messages
        out.append(item)
    return out


def _owned_run(run_id):
    return (
        Run.query.join(Conversation, Run.conversation_id == Conversation.id)
        .filter(Run.id == run_id, Conversation.user_id == g.user.id)
        .first()
    )


@api_bp.get("/conversations")
@require_auth
def list_conversations():
    convs = Conversation.query.filter_by(user_id=g.user.id).order_by(Conversation.id).all()
    return jsonify(
        [{"id": c.id, "title": c.title, "created_at": c.created_at.isoformat()} for c in convs]
    )


@api_bp.post("/conversations")
@require_auth
def create_conversation():
    data = request.get_json(silent=True) or {}
    conv = Conversation(user_id=g.user.id, title=data.get("title") or "New conversation")
    db.session.add(conv)
    db.session.commit()
    return jsonify({"id": conv.id, "title": conv.title}), 201


@api_bp.post("/conversations/<int:conv_id>/messages")
@require_auth
def send_message(conv_id):
    conv = Conversation.query.filter_by(id=conv_id, user_id=g.user.id).first()
    if conv is None:
        return jsonify({"error": "conversation not found"}), 404
    goal = ((request.get_json(silent=True) or {}).get("content") or "").strip()
    if not goal:
        return jsonify({"error": "content is required"}), 400

    user_msg = Message(conversation_id=conv.id, role="user", content=goal)
    db.session.add(user_msg)
    db.session.flush()
    run = Run(
        conversation_id=conv.id,
        user_message_id=user_msg.id,
        model=current_app.config["AGENT_MODEL"],
    )
    db.session.add(run)
    db.session.commit()

    outcome = run_agent(run, goal)
    return jsonify({**outcome, "trace": _serialize_steps(run)})


@api_bp.post("/runs/<int:run_id>/confirm")
@require_auth
def confirm_run(run_id):
    run = _owned_run(run_id)
    if run is None:
        return jsonify({"error": "run not found"}), 404
    data = request.get_json(silent=True) or {}
    if "approved" not in data:
        return jsonify({"error": "approved (true/false) is required"}), 400
    if run.status != "needs_confirmation":
        return jsonify({"error": f"run is not awaiting confirmation (status: {run.status})"}), 409

    outcome = resume_run(run, bool(data["approved"]))
    return jsonify({**outcome, "trace": _serialize_steps(run)})


@api_bp.get("/runs/<int:run_id>")
@require_auth
def get_run(run_id):
    run = _owned_run(run_id)
    if run is None:
        return jsonify({"error": "run not found"}), 404
    return jsonify(
        {
            "id": run.id,
            "status": run.status,
            "model": run.model,
            "total_latency_ms": run.total_latency_ms,
            "created_at": run.created_at.isoformat(),
            "steps": _serialize_steps(run, include_messages=True),
        }
    )
