import re
from typing import NamedTuple

RESPONSIVE = "responsive"
MIN_SIZE = 200
MAX_SIZE = 4000
DEFAULT_SIZE = (393, 852)
SIZE_SEPARATOR = "x"
CHROME_VERSION = re.compile(r"Chrome/([\d.]+)")
FALLBACK_CHROME_VERSION = "140.0.0.0"
IOS_VERSION = "17_5"
IOS_SAFARI = "17.5"


class Device(NamedTuple):
    key: str
    name: str
    width: int
    height: int
    template: str


IPHONE = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS {ios} like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/{safari} Mobile/15E148 Safari/604.1"
)
IPAD = (
    "Mozilla/5.0 (iPad; CPU OS {ios} like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/{safari} Mobile/15E148 Safari/604.1"
)
ANDROID = (
    "Mozilla/5.0 (Linux; Android 14; {model}) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/{chrome} Mobile Safari/537.36"
)

DEVICES = (
    Device("iphone15", "iPhone 15", 393, 852, IPHONE),
    Device("pixel8", "Pixel 8", 412, 915, ANDROID.replace("{model}", "Pixel 8")),
    Device("galaxys24", "Galaxy S24", 360, 780, ANDROID.replace("{model}", "SM-S921B")),
    Device("ipadair", "iPad Air", 820, 1180, IPAD),
    Device("ipadpro", "iPad Pro 12.9″", 1024, 1366, IPAD),
)


def device_for(key: str) -> Device | None:
    return next((device for device in DEVICES if device.key == key), None)


def device_list() -> list[dict[str, object]]:
    return [{"key": d.key, "name": d.name, "width": d.width, "height": d.height} for d in DEVICES]


def chrome_version_of(profile_agent: str) -> str:
    found = CHROME_VERSION.search(profile_agent)
    return found.group(1) if found else FALLBACK_CHROME_VERSION


def mobile_agent(key: str, profile_agent: str) -> str:
    device = device_for(key)
    if device is None:
        return ""
    return device.template.format(
        ios=IOS_VERSION, safari=IOS_SAFARI, chrome=chrome_version_of(profile_agent)
    )


def clamped(size: int) -> int:
    return max(MIN_SIZE, min(MAX_SIZE, size))


def format_size(width: int, height: int) -> str:
    return f"{width}{SIZE_SEPARATOR}{height}"


def parse_size(text: str) -> tuple[int, int] | None:
    width, _, height = text.partition(SIZE_SEPARATOR)
    if not (width.isdigit() and height.isdigit()):
        return None
    return clamped(int(width)), clamped(int(height))
