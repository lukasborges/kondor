import pytest

from kondor.site.identity import useragents

PROFILE_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/140.0.0.0 Kondor/0.1 Safari/537.36"
)


def test_chrome_agent_drops_the_kondor_token() -> None:
    assert "Kondor" not in useragents.chrome_agent(PROFILE_AGENT)
    assert "Chrome/140.0.0.0 Safari/537.36" in useragents.chrome_agent(PROFILE_AGENT)


@pytest.mark.parametrize(
    ("agent", "choice"),
    [
        ("", useragents.KONDOR),
        (useragents.FIREFOX_AGENT, useragents.FIREFOX),
        (useragents.chrome_agent(PROFILE_AGENT), useragents.CHROME),
        ("MyBrowser/1.0", useragents.CUSTOM),
    ],
)
def test_choice_is_read_from_the_stored_text(agent: str, choice: str) -> None:
    assert useragents.choice_of(agent) == choice


def test_only_chrome_keeps_client_hints() -> None:
    assert useragents.keeps_client_hints(useragents.chrome_agent(PROFILE_AGENT))
    assert not useragents.keeps_client_hints(useragents.FIREFOX_AGENT)
    assert not useragents.keeps_client_hints("MyBrowser/1.0")


def test_kondor_choice_stores_no_value() -> None:
    assert useragents.agent_for_choice(useragents.KONDOR, PROFILE_AGENT) == ""
