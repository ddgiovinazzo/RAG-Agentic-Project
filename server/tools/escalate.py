import itertools

_counter = itertools.count(1)


def escalate(ticket_id, priority, reason):
    """Mock: escalate a ticket to a human queue. The trace row is the durable record."""
    return {
        "escalation_id": f"esc-{next(_counter)}",
        "ticket_id": ticket_id,
        "priority": priority,
        "status": "escalated",
    }
