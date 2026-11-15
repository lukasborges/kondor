import struct

from kondor.passwords.wallet.walletmap import map_from_bytes, map_to_bytes

NULL_STRING_LENGTH = 0xFFFFFFFF


def qstring_bytes(text: str) -> bytes:
    encoded = text.encode("utf-16-be")
    return struct.pack(">I", len(encoded)) + encoded


def test_writes_the_qdatastream_bytes() -> None:
    expected = bytes.fromhex("00000001" "00000006" "0061006e006e" "00000004" "00700077")
    assert map_to_bytes({"ann": "pw"}) == expected


def test_orders_keys_like_qmap() -> None:
    logins = {"b": "1", "a": "2", "\U0001f600": "3", "￿": "4"}
    expected = struct.pack(">I", 4) + b"".join(
        qstring_bytes(key) + qstring_bytes(logins[key]) for key in ("a", "b", "\U0001f600", "￿")
    )
    assert map_to_bytes(logins) == expected


def test_round_trips() -> None:
    logins = {"ann": "from C++ é😀", "Bob": "", "": "x"}
    assert map_from_bytes(map_to_bytes(logins)) == logins


def test_reads_empty_bytes_as_empty() -> None:
    assert map_from_bytes(b"") == {}


def test_reads_truncated_bytes_as_empty() -> None:
    assert map_from_bytes(map_to_bytes({"ann": "pw"})[:-1]) == {}
    assert map_from_bytes(struct.pack(">I", NULL_STRING_LENGTH - 1)) == {}


def test_reads_null_strings_as_empty() -> None:
    null_string = struct.pack(">I", NULL_STRING_LENGTH)
    pairs = null_string + qstring_bytes("pw") + qstring_bytes("bo") + null_string
    data = struct.pack(">I", 2) + pairs
    assert map_from_bytes(data) == {"": "pw", "bo": ""}
