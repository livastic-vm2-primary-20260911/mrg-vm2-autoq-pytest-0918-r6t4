_attempt = 0


def test_vm2_autoq_fresh_nomanual_0918():
    global _attempt
    _attempt += 1
    assert _attempt % 2 == 1, f"fresh no-manual main calibration attempt={_attempt}"
