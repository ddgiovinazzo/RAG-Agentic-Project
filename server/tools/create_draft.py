import itertools

_counter = itertools.count(1)


def create_draft(ticket_id, reply_text):
    """Mock: 'send' a draft reply for a ticket. The trace row is the durable record."""
    return {"draft_id": f"draft-{next(_counter)}", "ticket_id": ticket_id, "status": "sent"}
