import pytest

from kondor.browser.responsive import devices

PROFILE_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/140.0.1.2 Kondor/0.1 Safari/537.36"
)


def test_iphone_agent_is_ios_safari() -> None:
    agent = devices.mobile_agent("iphone-16", PROFILE_AGENT)
    assert "iPhone" in agent
    assert "Safari/604.1" in agent
    assert "Chrome" not in agent


def test_android_agents_use_the_chromium_version_of_the_profile() -> None:
    agent = devices.mobile_agent("pixel-9", PROFILE_AGENT)
    assert "Chrome/140.0.1.2 Mobile" in agent
    assert "Pixel 9" in agent


def test_responsive_has_no_agent() -> None:
    assert devices.mobile_agent(devices.RESPONSIVE, PROFILE_AGENT) == ""


def test_device_list_is_chromes_default_list() -> None:
    assert [device["name"] for device in devices.device_list()] == [
        "iPhone SE",
        "iPhone 16",
        "iPhone 16 Pro Max",
        "Pixel 9",
        "Pixel 9 Pro",
        "Pixel 10",
        "Samsung Galaxy A55",
        "iPad Mini",
        "iPad Pro 13",
        "Surface Pro 10",
        "Pixel 9 Pro Fold",
        "Galaxy Z Fold 6",
        "Nest Hub Max",
    ]


def test_device_list_carries_the_default_ratio() -> None:
    ratios = {device["key"]: device["ratio"] for device in devices.device_list()}
    assert (ratios["pixel-9"], ratios["iphone-16"], ratios["galaxy-a55"]) == (2.625, 3, 2.25)


def test_pixel_10_runs_android_16() -> None:
    assert "Android 16; Pixel 10" in devices.mobile_agent("pixel-10", PROFILE_AGENT)


def test_ipad_pro_13_sends_the_macos_safari_agent() -> None:
    assert "Macintosh" in devices.mobile_agent("ipad-pro-13", PROFILE_AGENT)


@pytest.mark.parametrize(
    ("text", "size"),
    [("393x852", (393, 852)), ("10x9000", (200, 4000)), ("bad", None), ("1x", None)],
)
def test_parse_size_clamps_and_rejects_garbage(text: str, size: tuple[int, int] | None) -> None:
    assert devices.parse_size(text) == size
