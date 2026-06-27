"""
Phase-1 Slice 1 tests — capture + style metrics + the personas API.

Unit tests (no infra): WhatsApp parsing + CMI language sensitivity.
Integration (needs docker postgres + redis, like test_pipeline): create a
persona, paste writing, read the measured style back.
"""
from __future__ import annotations

import uuid

from httpx import ASGITransport, AsyncClient

from app.core.auth import issue_dev_token
from app.tone import capture
from app.tone.features import message_features

_WA_EXPORT = """\
[2026/06/27, 11:45:30 PM] Abhishek: haan bhai isko aise karte hain
this part is a continued line
[2026/06/27, 11:45:40 PM] Rohan: ok cool got it
[2026/06/27, 11:46:00 PM] Abhishek: <Media omitted>
27/06/2026, 11:48 - Abhishek: latency thoda dekhna padega yaar
"""


def test_parse_whatsapp_keeps_only_author_and_joins_multiline():
    parsed = capture.parse_whatsapp(_WA_EXPORT)
    assert dict(capture.senders(parsed)) == {"Abhishek": 2, "Rohan": 1}

    mine = capture.author_messages(parsed, "Abhishek")
    # 2 real messages (the <Media omitted> line is dropped), multiline joined.
    assert len(mine) == 2
    assert "continued line" in mine[0]
    assert all("media omitted" not in m.lower() for m in mine)


def test_cmi_distinguishes_english_from_hinglish():
    english = message_features("please send me the report tomorrow morning").cmi
    # A genuinely alternating sentence (English clauses + Hindi clauses).
    hinglish = message_features("the deadline kal hai but main aaj finish karunga").cmi
    assert english < 0.1, f"pure English should be ~0 CMI, got {english}"
    assert hinglish > 0.3, f"code-mixed text should be clearly mixed, got {hinglish}"


async def test_persona_capture_end_to_end():
    # A fresh tenant minted straight from a dev token (JIT-provisioned on use).
    org_id, user_id = str(uuid.uuid4()), str(uuid.uuid4())
    email = f"abhi-{uuid.uuid4().hex[:8]}@example.test"  # unique per run (users.email is UNIQUE)
    token = issue_dev_token(user_id=user_id, org_id=org_id, email=email)
    headers = {"Authorization": f"Bearer {token}"}

    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # create persona
        r = await client.post("/personas", headers=headers, json={"name": "My voice"})
        assert r.status_code == 201, r.text
        persona_id = r.json()["persona_id"]

        # capture pasted writing (Hinglish, with a PII line that must be scrubbed)
        paste = (
            "haan bhai isko aise karte hain, ho jayega\n\n"
            "latency thoda dekhna padega yaar\n\n"
            "call me at +91 98765 43210 if urgent\n\n"
            "scene kya hai aaj ka, batao"
        )
        c = await client.post(
            f"/personas/{persona_id}/capture",
            headers=headers,
            json={"source_type": "paste", "text": paste, "build_capsule": False},
        )
        assert c.status_code == 200, c.text
        body = c.json()
        assert body["stored"] == 4
        assert body["total_tokens"] > 0       # the SUM must see the just-stored rows
        assert body["band"] == "warming_up"  # tiny sample → honest low confidence
        assert body["style"]["cmi"] > 0.1     # recognisably code-mixed, not pure English

        # read it back
        g = await client.get(f"/personas/{persona_id}", headers=headers)
        assert g.status_code == 200, g.text
        gb = g.json()
        assert gb["observations"] == 4
        assert gb["status"] == "warming_up"
        assert gb["style"]["cmi"] is not None
