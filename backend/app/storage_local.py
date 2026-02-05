from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO
from uuid import uuid4


@dataclass(frozen=True)
class StoredObject:
    backend: str
    key: str
    size_bytes: int
    sha256_hex: str


class LocalFileStorage:
    backend = "local"

    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save(self, stream: BinaryIO, *, original_filename: str, first_chunk: bytes = b"") -> StoredObject:
        _, ext = os.path.splitext(original_filename or "")
        ext = (ext[:10] if ext else "")  # guard weirdly long extensions
        key = f"{uuid4().hex}{ext}"
        dest = self.base_dir / key

        sha = hashlib.sha256()
        size = 0

        with open(dest, "wb") as out:
            if first_chunk:
                out.write(first_chunk)
                sha.update(first_chunk)
                size += len(first_chunk)

            while True:
                chunk = stream.read(1024 * 1024)  # 1MB
                if not chunk:
                    break
                out.write(chunk)
                sha.update(chunk)
                size += len(chunk)

        return StoredObject(self.backend, key, size, sha.hexdigest())

    def open(self, key: str) -> BinaryIO:
        return open(self.base_dir / key, "rb")
