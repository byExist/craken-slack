"""Local-file helpers for the download flow."""

import mimetypes
import os
import tempfile


def write_temp(data: bytes, content_type: str) -> str:
    """Write binary ``data`` to a uniquely-named temp file; return its path.

    The extension is derived from ``content_type`` so image readers and other
    tools can recognize the file. The file persists until the OS cleans its
    temp dir; copy it if you need to keep it.
    """
    ext = mimetypes.guess_extension((content_type or "").split(";")[0].strip()) or ""
    fd, path = tempfile.mkstemp(suffix=ext)
    with os.fdopen(fd, "wb") as f:
        f.write(data)
    return path
