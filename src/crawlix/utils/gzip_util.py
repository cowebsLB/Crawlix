from __future__ import annotations

import gzip


def gzip_bytes(data: bytes) -> bytes:
    return gzip.compress(data, compresslevel=6)


def gunzip_bytes(blob: bytes) -> bytes:
    return gzip.decompress(blob)
