from app.services.unsubscribe import parse_list_unsubscribe


def test_parse_list_unsubscribe():
    header = "<mailto:unsubscribe@example.com>, <https://example.com/unsub>"
    links = parse_list_unsubscribe(header)
    assert "mailto:unsubscribe@example.com" in links.mailto
    assert "https://example.com/unsub" in links.urls
