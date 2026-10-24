from types import SimpleNamespace
from src.utils.inbox_localization import localize_message, translate_text


def test_saved_report_switch_preserves_source_and_numbers():
    msg = SimpleNamespace(subject="Daily Report — 29 Aug 2025", body="MEDICAL ROOM\nAli — out ~12d")
    original = (msg.subject, msg.body)
    arabic = localize_message(msg, language="ar", names={"Ali": "علي"})
    assert "التقرير اليومي" in arabic.subject
    assert "علي" in arabic.body and "12" in arabic.body
    assert not arabic.has_original_text
    english = localize_message(msg, language="en")
    assert (english.subject, english.body) == original
    assert (msg.subject, msg.body) == original


def test_offer_payload_hidden_in_both_languages_but_preserved():
    body = "Transfer fee: 20,000 EGP\nTRANSFER_OFFER|1|2|3|20000|500"
    msg = SimpleNamespace(subject="Offer Sent: Ali", body=body)
    for language in ("ar", "en"):
        result = localize_message(msg, language=language, names={"Ali": "علي"})
        assert "TRANSFER_OFFER" not in result.body
        assert "20,000" in result.body
    assert msg.body == body


def test_unknown_prose_remains_visible_with_notice():
    result = localize_message(SimpleNamespace(subject="Unexpected archive", body="Unreviewed narrative."), language="ar")
    assert result.has_original_text
    assert result.body == "Unreviewed narrative."
    assert localize_message(SimpleNamespace(subject="Expectation: Unknown Objective", body=""), language="ar").has_original_text


def test_parenthesized_template_and_decorated_heading():
    value, missing = translate_text("(Attempt 2/3; 1 attempt(s) left after this)\n⚽ MEDICAL ROOM")
    assert "Attempt" not in value and "MEDICAL" not in value
    assert "2" in value and "⚽" in value
    assert not missing
