from app.services.classifier import is_newsletter, guess_category, priority


def test_newsletter_detection():
    assert is_newsletter("<mailto:unsubscribe@example.com>", None)
    assert is_newsletter(None, "Click here to unsubscribe")


def test_category_and_priority():
    category = guess_category("Rechnung", "Bitte Zahlung", False)
    assert category == "finance"
    score, reason = priority("Frist morgen?", "Rechnung", False)
    assert score > 20
    assert reason
