from cpb_outreach.enrich.verify_email import syntax_ok, verify_email


def test_syntax_ok():
    assert syntax_ok("coach@example.k12.tx.us")
    assert not syntax_ok("not-an-email")


def test_verify_email_invalid():
    ok, reason = verify_email("bad")
    assert not ok
    assert reason == "invalid_syntax"
