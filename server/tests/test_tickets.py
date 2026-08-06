from server.models import Ticket, db
from server.tools.ticket_tools import create_ticket, list_tickets, update_ticket, delete_ticket

def test_ticket_crud_routes(client, auth_headers):
    # 1. Create a ticket via POST /api/tickets
    res = client.post(
        "/api/tickets",
        headers=auth_headers,
        json={
            "title": "Broken Monitor",
            "description": "External display stays black on USB-C",
            "priority": "high",
            "category": "IT",
        },
    )
    assert res.status_code == 201
    data = res.get_json()
    assert data["title"] == "Broken Monitor"
    assert data["priority"] == "high"
    assert data["status"] == "open"
    ticket_id = data["id"]

    # 2. List tickets via GET /api/tickets
    res = client.get("/api/tickets", headers=auth_headers)
    assert res.status_code == 200
    tickets = res.get_json()
    assert len(tickets) >= 1
    assert any(t["id"] == ticket_id for t in tickets)

    # 3. Filter tickets by status
    res = client.get("/api/tickets?status=open", headers=auth_headers)
    assert res.status_code == 200
    assert len(res.get_json()) >= 1

    # 4. Update ticket via PATCH /api/tickets/<id>
    res = client.patch(
        f"/api/tickets/{ticket_id}",
        headers=auth_headers,
        json={"status": "resolved", "priority": "low"},
    )
    assert res.status_code == 200
    updated = res.get_json()
    assert updated["status"] == "resolved"
    assert updated["priority"] == "low"

    # 5. Delete ticket via DELETE /api/tickets/<id>
    res = client.delete(f"/api/tickets/{ticket_id}", headers=auth_headers)
    assert res.status_code == 200
    assert res.get_json()["success"] is True

    # Verify deleted
    res = client.get("/api/tickets", headers=auth_headers)
    assert not any(t["id"] == ticket_id for t in res.get_json())
