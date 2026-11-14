from dataclasses import dataclass, field

from PySide6.QtCore import QJsonDocument, QUrl


@dataclass
class SingleInstanceMessage:
    urls: list[QUrl] = field(default_factory=list)
    private_mode: bool = False
    new_window: bool = False
    activation_token: bytes = b""


def encode_urls(urls: list[QUrl]) -> list[str]:
    return [bytes(url.toEncoded()).decode("utf-8") for url in urls]


def decode_urls(values: list[object]) -> list[QUrl]:
    urls = [QUrl.fromEncoded(str(value).encode("utf-8")) for value in values]
    return [url for url in urls if url.isValid() and not url.isEmpty()]


def to_json_line(message: SingleInstanceMessage) -> bytes:
    document = QJsonDocument.fromVariant(
        {
            "urls": encode_urls(message.urls),
            "private": message.private_mode,
            "newWindow": message.new_window,
            "activationToken": message.activation_token.decode("utf-8"),
        }
    )
    return bytes(document.toJson(QJsonDocument.JsonFormat.Compact)) + b"\n"


def from_object(data: dict[str, object]) -> SingleInstanceMessage:
    urls = data.get("urls")
    token = data.get("activationToken")
    return SingleInstanceMessage(
        urls=decode_urls(urls if isinstance(urls, list) else []),
        private_mode=data.get("private") is True,
        new_window=data.get("newWindow") is True,
        activation_token=token.encode("utf-8") if isinstance(token, str) else b"",
    )


def from_json_line(line: bytes) -> SingleInstanceMessage:
    document = QJsonDocument.fromJson(line.strip())
    if not document.isObject():
        return SingleInstanceMessage()
    return from_object(document.object())
