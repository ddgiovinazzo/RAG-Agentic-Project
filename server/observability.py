import time

from server.models import RunStep, db


def record_step(run_id, seq, kind, fn, *, tool_name=None, arguments=None, llm_messages=None):
    """Execute fn(), timing it, and persist the outcome as a RunStep.

    Never raises: an exception from fn() is captured as {"error": ...} so the
    agent loop can degrade gracefully while the failure stays in the log.
    """
    start = time.perf_counter()
    try:
        result = fn()
    except Exception as exc:  # noqa: BLE001 — every failure must reach the log
        result = {"error": str(exc)}
    latency_ms = int((time.perf_counter() - start) * 1000)
    stored = result if isinstance(result, dict) else {"value": result}
    step = RunStep(
        run_id=run_id,
        seq=seq,
        kind=kind,
        tool_name=tool_name,
        arguments=arguments,
        result=stored,
        llm_messages=llm_messages,
        latency_ms=latency_ms,
    )
    db.session.add(step)
    db.session.commit()
    return result
