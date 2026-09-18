_attempt = 0


def test_vm2_autoq_fresh_nomanual_0918():
    global _attempt
    _attempt += 1
    assert _attempt % 2 == 0, f"fresh no-manual AutoQ trigger attempt={_attempt}"
