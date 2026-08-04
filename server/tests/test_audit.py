from datetime import datetime, timezone

import pytest

from server.auth import bcrypt
from server.models import Conversation, Message, Run, RunStep, User, db


def _seed_user(email):
    user = User(
        email=email,
        password_hash=bcrypt.generate_password_hash("password123").decode("utf-8"),
    )
    db.session.add(user)
    db.session.commit()
    return user


def _seed_run(
    user,
    *,
    status="completed",
    goal="test goal",
    latency=3000,
    tokens=(100, 10),
    tool="search_knowledge",
    created_at=None,
):
    conv = Conversation(user_id=user.id, title=f"conv of {user.email}")
    db.session.add(conv)
    db.session.commit()
    msg = Message(conversation_id=conv.id, role="user", content=goal)
    db.session.add(msg)
    db.session.commit()
    run = Run(
        conversation_id=conv.id,
        user_message_id=msg.id,
        status=status,
        model="llama3.1:8b",
        total_latency_ms=latency,
    )
    db.session.add(run)
    db.session.commit()
    if created_at is not None:
        run.created_at = created_at
        db.session.commit()
    db.session.add_all(
        [
            RunStep(
                run_id=run.id, seq=1, kind="llm_call", result={},
                latency_ms=latency - 500 if latency else None,
                prompt_tokens=tokens[0], completion_tokens=tokens[1],
            ),
            RunStep(
                run_id=run.id, seq=2, kind="tool_call", tool_name=tool,
                arguments={}, result={}, latency_ms=500,
            ),
        ]
    )
    db.session.commit()
    return run


@pytest.fixture
def me(app, auth_headers):
    return User.query.filter_by(email="me@test.com").one()


def test_list_runs_scoped_to_own_user(client, auth_headers, me):
    other = _seed_user("other@test.com")
    mine = _seed_run(me, goal="my goal")
    _seed_run(other, goal="their goal")

    body = client.get("/api/runs", headers=auth_headers).get_json()
    assert body["total"] == 1
    row = body["runs"][0]
    assert row["id"] == mine.id
    assert row["goal"] == "my goal"
    assert row["step_count"] == 2
    assert row["prompt_tokens"] == 100
    assert row["completion_tokens"] == 10
    assert "user_email" not in row

    # user_email param is silently ignored for non-admins
    body = client.get(
        "/api/runs?user_email=other@test.com", headers=auth_headers
    ).get_json()
    assert body["total"] == 1
    assert body["runs"][0]["id"] == mine.id


def test_list_runs_admin_sees_all_and_filters_by_email(client, admin_headers, auth_headers, me):
    other = _seed_user("other@test.com")
    _seed_run(me)
    _seed_run(other)

    body = client.get("/api/runs", headers=admin_headers).get_json()
    assert body["total"] == 2
    assert {r["user_email"] for r in body["runs"]} == {"me@test.com", "other@test.com"}

    body = client.get(
        "/api/runs?user_email=OTHER@test.com", headers=admin_headers
    ).get_json()
    assert body["total"] == 1
    assert body["runs"][0]["user_email"] == "other@test.com"


def test_list_runs_filters_and_pagination(client, auth_headers, me):
    _seed_run(me, status="completed", created_at=datetime(2026, 8, 1, 12, tzinfo=timezone.utc))
    _seed_run(me, status="failed", created_at=datetime(2026, 8, 2, 12, tzinfo=timezone.utc))
    _seed_run(me, status="completed", created_at=datetime(2026, 8, 3, 12, tzinfo=timezone.utc))

    body = client.get("/api/runs?status=completed", headers=auth_headers).get_json()
    assert body["total"] == 2

    body = client.get(
        "/api/runs?date_from=2026-08-02&date_to=2026-08-02", headers=auth_headers
    ).get_json()
    assert body["total"] == 1
    assert body["runs"][0]["status"] == "failed"

    body = client.get("/api/runs?per_page=2&page=2", headers=auth_headers).get_json()
    assert body["total"] == 3
    assert len(body["runs"]) == 1
    # newest first: page 2 holds the oldest run
    assert body["runs"][0]["created_at"].startswith("2026-08-01")
