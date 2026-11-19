import hashlib
from pathlib import Path

CHUNK_BYTES = 1 << 20


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(CHUNK_BYTES):
            digest.update(chunk)
    return digest.hexdigest()


def matches_hash(path: Path, expected: str) -> bool:
    return path.is_file() and sha256_of(path) == expected.lower()
