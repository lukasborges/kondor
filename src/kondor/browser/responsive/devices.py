import re
from typing import NamedTuple

RESPONSIVE = "responsive"
MIN_SIZE = 200
MAX_SIZE = 4000
DEFAULT_SIZE = (393, 852)
SIZE_SEPARATOR = "x"
CHROME_VERSION = re.compile(r"Chrome/([\d.]+)")
FALLBACK_CHROME_VERSION = "140.0.0.0"
FALLBACK_DEVICE = "iphone-16"


class Device(NamedTuple):
    key: str
    name: str
    width: int
    height: int
    ratio: float
    template: str


IPHONE = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1"
)
IPAD = (
    "Mozilla/5.0 (iPad; CPU OS 18_5 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1"
)
MAC_SAFARI = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/18.5 Safari/605.1.15"
)
WINDOWS_CHROME = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/{chrome} Safari/537.36"
)
CAST_CHROME = (
    "Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/{chrome} Safari/537.36 CrKey/1.54.250320"
)


def android(version: int, model: str) -> str:
    return (
        f"Mozilla/5.0 (Linux; Android {version}; {model}) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/{chrome} Mobile Safari/537.36"
    )


FOLD = android(14, "Pixel 9 Pro Fold")

DEVICES = (
    Device("iphone-se", "iPhone SE", 375, 667, 2, IPHONE),
    Device("iphone-16", "iPhone 16", 393, 852, 3, IPHONE),
    Device("iphone-16-pro-max", "iPhone 16 Pro Max", 440, 956, 3, IPHONE),
    Device("pixel-9", "Pixel 9", 412, 924, 2.625, android(14, "Pixel 9")),
    Device("pixel-9-pro", "Pixel 9 Pro", 427, 952, 3, android(14, "Pixel 9 Pro")),
    Device("pixel-10", "Pixel 10", 412, 924, 2.625, android(16, "Pixel 10")),
    Device("galaxy-a55", "Samsung Galaxy A55", 360, 800, 2.25, android(14, "SM-A556B")),
    Device("ipad-mini", "iPad Mini", 768, 1024, 2, IPAD),
    Device("ipad-pro-13", "iPad Pro 13", 1032, 1376, 2, MAC_SAFARI),
    Device("surface-pro-10", "Surface Pro 10", 960, 1440, 2, WINDOWS_CHROME),
    Device(
        "pixel-9-pro-fold", "Pixel 9 Pro Fold", 412, 922, 2.625, android(14, "Pixel 9 Pro Fold")
    ),
    Device("galaxy-z-fold-6", "Galaxy Z Fold 6", 412, 968, 2.625, android(14, "SM-F956U")),
    Device("nest-hub-max", "Nest Hub Max", 1280, 800, 2, CAST_CHROME),
)


def device_for(key: str) -> Device | None:
    return next((device for device in DEVICES if device.key == key), None)


def device_list() -> list[dict[str, object]]:
    return [
        {
            "key": device.key,
            "name": device.name,
            "width": device.width,
            "height": device.height,
            "ratio": device.ratio,
        }
        for device in DEVICES
    ]


def chrome_version_of(profile_agent: str) -> str:
    found = CHROME_VERSION.search(profile_agent)
    return found.group(1) if found else FALLBACK_CHROME_VERSION


def mobile_agent(key: str, profile_agent: str) -> str:
    device = device_for(key)
    if device is None:
        return ""
    return device.template.replace("{chrome}", chrome_version_of(profile_agent))


def clamped(size: int) -> int:
    return max(MIN_SIZE, min(MAX_SIZE, size))


def format_size(width: int, height: int) -> str:
    return f"{width}{SIZE_SEPARATOR}{height}"


def parse_size(text: str) -> tuple[int, int] | None:
    width, _, height = text.partition(SIZE_SEPARATOR)
    if not (width.isdigit() and height.isdigit()):
        return None
    return clamped(int(width)), clamped(int(height))
