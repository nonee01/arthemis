import importlib
import sys
import pathlib

from arthemis import main as am


def test_origin_no_los():
    assert am.check_los(0, 0) is False


def test_behind_moon_los():
    # Spacecraft located just beyond the Moon on the +X axis
    assert am.check_los(380000, 0, moon_x=375000) is True


def test_off_axis_no_los():
    # Off-axis trajectory should not be blocked
    assert am.check_los(200000, 50000, moon_x=375000) is False
