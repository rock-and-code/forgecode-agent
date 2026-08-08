from __future__ import annotations

from forgecode_agent.ledger import RunLedger


def test_append_defensively_copies_event_data() -> None:
    ledger = RunLedger(run_id="mutation-test")
    payload = {"nested": {"items": ["original"]}}

    event = ledger.append("payload_recorded", payload)
    payload["nested"]["items"].append("mutated")

    assert event.data == {"nested": {"items": ["original"]}}
    assert ledger.events[0].data == {"nested": {"items": ["original"]}}
