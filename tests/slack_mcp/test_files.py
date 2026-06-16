"""Tests for slack_mcp.files — temp-file helpers."""

import os

from slack_mcp.files import write_temp


def test_write_temp_saves_bytes_and_returns_path():
    path = write_temp(b"\x89PNG", "image/png")
    try:
        assert os.path.isfile(path)
        with open(path, "rb") as f:
            assert f.read() == b"\x89PNG"
    finally:
        os.unlink(path)
