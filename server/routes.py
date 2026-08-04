from datetime import date
from flask import Blueprint, current_app, g, jsonify, request
from sqlalchemy import func

from server.agent import resume_run, run_agent
from server.auth import require_auth
from server.models import Conversation, Message, PendingAction, Run, RunStep, User, db

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


def _parse_iso_date(value):
    try:
        return date.fromisoformat(value) if value else None
    except ValueError:
        return None


def _filtered_runs_query():
    """(Run, Conversation, User) rows with audit filters applied, scoped by role."""
    q = (
        db.session.query(Run, Conversation, User)
        .join(Conversation, Run.conversation_id == Conversation.id)
        .join(User, Conversation.user_id == User.id)
    )
    if g.is_admin:
        email = (request.args.get("user_email") or "").strip().lower()
        if email:
            q = q.filter(func.lower(User.email) == email)
    else:
        q = q.filter(Conversation.user_id == g.user.id)
    status = request.args.get("status")
    if status:
        q = q.filter(Run.status == status)
    conv_id = request.args.get("conversation_id", type=int)
    if conv_id:
        q = q.filter(Run.conversation_id == conv_id)
    date_from = _parse_iso_date(request.args.get("date_from"))
    if date_from:
        q = q.filter(func.date(Run.created_at) >= date_from.isoformat())
    date_to = _parse_iso_date(request.args.get("date_to"))
    if date_to:
        q = q.filter(func.date(Run.created_at) <= date_to.isoformat())
    return q


@api_bp.get("/runs")
@require_auth
def list_runs():
    q = _filtered_runs_query()
    page = max(request.args.get("page", 1, type=int), 1)
    per_page = min(max(request.args.get("per_page", 20, type=int), 1), 100)
    total = q.count()
    rows = (
        q.order_by(Run.created_at.desc(), Run.id.desc())
        .limit(per_page)
        .offset((page - 1) * per_page)
        .all()
    )
    run_ids = [run.id for run, _, _ in rows]
    step_aggs = {}
    goals = {}
    if run_ids:
        for run_id, count, pt, ct in (
            db.session.query(
                RunStep.run_id,
                func.count(RunStep.id),
                func.coalesce(func.sum(RunStep.prompt_tokens), 0),
                func.coalesce(func.sum(RunStep.completion_tokens), 0),
            )
            .filter(RunStep.run_id.in_(run_ids))
            .group_by(RunStep.run_id)
        ):
            step_aggs[run_id] = (count, pt, ct)
        goals = dict(
            db.session.query(Message.id, Message.content).filter(
                Message.id.in_([run.user_message_id for run, _, _ in rows])
            )
        )
    runs = []
    for run, conv, user in rows:
        count, pt, ct = step_aggs.get(run.id, (0, 0, 0))
        item = {
            "id": run.id,
            "status": run.status,
            "goal": (goals.get(run.user_message_id) or "")[:80],
            "conversation_id": conv.id,
            "conversation_title": conv.title,
            "model": run.model,
            "step_count": count,
            "total_latency_ms": run.total_latency_ms,
            "prompt_tokens": pt,
            "completion_tokens": ct,
            "created_at": run.created_at.isoformat(),
        }
        if g.is_admin:
            item["user_email"] = user.email
        runs.append(item)
    return jsonify({"runs": runs, "total": total, "page": page, "per_page": per_page})


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


@api_bp.get("/conversations/<int:conv_id>/messages")
@require_auth
def get_conversation_messages(conv_id):
    conv = Conversation.query.filter_by(id=conv_id, user_id=g.user.id).first()
    if conv is None:
        return jsonify({"error": "conversation not found"}), 404
    messages = Message.query.filter_by(conversation_id=conv.id).order_by(Message.id).all()
    runs = Run.query.filter_by(conversation_id=conv.id).order_by(Run.id).all()
    return jsonify(
        {
            "messages": [
                {
                    "id": m.id,
                    "role": m.role,
                    "content": m.content,
                    "created_at": m.created_at.isoformat(),
                }
                for m in messages
            ],
            "runs": [
                {"id": r.id, "user_message_id": r.user_message_id, "status": r.status}
                for r in runs
            ],
        }
    )


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
    if not isinstance(data["approved"], bool):
        return jsonify({"error": "approved must be a boolean"}), 400
    if run.status != "needs_confirmation":
        return jsonify({"error": f"run is not awaiting confirmation (status: {run.status})"}), 409

    outcome = resume_run(run, data["approved"])
    return jsonify({**outcome, "trace": _serialize_steps(run)})


@api_bp.get("/runs/<int:run_id>")
@require_auth
def get_run(run_id):
    run = _owned_run(run_id)
    if run is None:
        return jsonify({"error": "run not found"}), 404
    body = {
        "id": run.id,
        "status": run.status,
        "model": run.model,
        "total_latency_ms": run.total_latency_ms,
        "created_at": run.created_at.isoformat(),
        "steps": _serialize_steps(run, include_messages=True),
    }
    pending = PendingAction.query.filter_by(run_id=run.id, status="pending").first()
    if pending is not None:
        body["pending_action"] = {
            "id": pending.id,
            "tool": pending.tool_name,
            "arguments": pending.arguments,
        }
    return jsonify(body)
