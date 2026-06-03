from demo_add import add


def test_add_handles_positive_numbers():
    assert add(2, 3) == 5


def test_add_handles_negative_numbers():
    assert add(-2, -3) == -5
