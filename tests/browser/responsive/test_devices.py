import pytest

from kondor.browser.responsive import devices

PROFILE_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/140.0.1.2 Kondor/0.1 Safari/537.36"
)


def test_iphone_agent_is_ios_safari() -> None:
    agent = devices.mobile_agent("iphone15", PROFILE_AGENT)
    assert "iPhone" in agent
    assert "Safari/604.1" in agent
    assert "Chrome" not in agent


def test_android_agents_use_the_chromium_version_of_the_profile() -> None:
    agent = devices.mobile_agent("pixel8", PROFILE_AGENT)
    assert "Chrome/140.0.1.2 Mobile" in agent
    assert "Pixel 8" in agent


def test_responsive_has_no_agent() -> None:
    assert devices.mobile_agent(devices.RESPONSIVE, PROFILE_AGENT) == ""


def test_device_list_holds_the_five_devices() -> None:
    assert [device["name"] for device in devices.device_list()] == [
        "iPhone 15",
        "Pixel 8",
        "Galaxy S24",
        "iPad Air",
        "iPad Pro 12.9″",
    ]


@pytest.mark.parametrize(
    ("text", "size"),
    [("393x852", (393, 852)), ("10x9000", (200, 4000)), ("bad", None), ("1x", None)],
)
def test_parse_size_clamps_and_rejects_garbage(text: str, size: tuple[int, int] | None) -> None:
    assert devices.parse_size(text) == size
