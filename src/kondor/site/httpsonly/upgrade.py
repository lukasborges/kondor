import ipaddress

from PySide6.QtCore import QUrl

HTTP_DEFAULT_PORT = 80


def is_ip_address(host: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address | None:
    try:
        return ipaddress.ip_address(host.strip("[]"))
    except ValueError:
        return None


def is_local_host(host: str) -> bool:
    if host == "localhost" or host.endswith(".localhost") or "." not in host:
        return True
    address = is_ip_address(host)
    return address is not None and (address.is_loopback or address.is_private)


def is_upgradable(url: QUrl, allowed_hosts: set[str]) -> bool:
    host = url.host().lower()
    if url.scheme().lower() != "http" or not host:
        return False
    return host not in allowed_hosts and not is_local_host(host)


def secure_version_of(url: QUrl) -> QUrl:
    secure = QUrl(url)
    secure.setScheme("https")
    if secure.port() == HTTP_DEFAULT_PORT:
        secure.setPort(-1)
    return secure
