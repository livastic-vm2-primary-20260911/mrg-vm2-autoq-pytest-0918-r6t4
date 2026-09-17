_attempt = 0


def test_vm2_new_flaky_autoq_r6t4():
    global _attempt
    _attempt += 1
    assert _attempt % 2 == 0, f"controlled flaky trigger attempt={_attempt}"
