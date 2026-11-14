from PySide6.QtCore import QByteArray, QDataStream, QIODevice


def qmap_order(key: str) -> bytes:
    return key.encode("utf-16-be", errors="surrogatepass")


def map_to_bytes(logins: dict[str, str]) -> bytes:
    data = QByteArray()
    stream = QDataStream(data, QIODevice.OpenModeFlag.WriteOnly)
    stream.writeUInt32(len(logins))
    for key in sorted(logins, key=qmap_order):
        stream.writeQString(key)
        stream.writeQString(logins[key])
    return bytes(data.data())


def read_pairs(stream: QDataStream, count: int) -> dict[str, str]:
    logins: dict[str, str] = {}
    for _ in range(count):
        key, value = stream.readQString(), stream.readQString()
        if stream.status() != QDataStream.Status.Ok:
            break
        logins[key] = value
    return logins


def map_from_bytes(data: bytes) -> dict[str, str]:
    buffer = QByteArray(data)
    stream = QDataStream(buffer)
    logins = read_pairs(stream, stream.readUInt32())
    return logins if stream.status() == QDataStream.Status.Ok else {}
