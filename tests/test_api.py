import pytest  # noqa
import swmming.api.wrappers as swio


def test_import():
    assert swio._platform == "Linux"
    assert swio._lib is not None


def test_get_version():
    assert swio.get_version().startswith("52")
