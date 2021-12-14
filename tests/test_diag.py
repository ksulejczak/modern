from mode.diag import Diag


def test_set_flag() -> None:
    diag = Diag()

    diag.set_flag("abc")

    assert diag.has_flag("abc") is True


def test_double_set_flag() -> None:
    diag = Diag()

    diag.set_flag("abc")
    diag.set_flag("abc")

    assert diag.has_flag("abc") is True


def test_unset_flag() -> None:
    diag = Diag()
    diag.set_flag("abc")

    diag.unset_flag("abc")

    assert diag.has_flag("abc") is False


def test_has_flag() -> None:
    diag = Diag()

    assert diag.has_flag("abc") is False

    diag.set_flag("abc")

    assert diag.has_flag("abc") is True


def test_get_flags() -> None:
    diag = Diag()
    diag.set_flag("flag1")
    diag.set_flag("flag2")

    all_flags = diag.get_flags()

    assert all_flags == {"flag1", "flag2"}
