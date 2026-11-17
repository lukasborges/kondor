import re

KONDOR = "kondor"
FIREFOX = "firefox"
CHROME = "chrome"
CUSTOM = "custom"
FIREFOX_VERSION = 140
FIREFOX_AGENT = (
    f"Mozilla/5.0 (X11; Linux x86_64; rv:{FIREFOX_VERSION}.0) "
    f"Gecko/20100101 Firefox/{FIREFOX_VERSION}.0"
)
KONDOR_TOKEN = re.compile(r" Kondor/[^ ]+")


def chrome_agent(profile_agent: str) -> str:
    return KONDOR_TOKEN.sub("", profile_agent)


def is_chrome_like(agent: str) -> bool:
    return "Chrome/" in agent and "Firefox/" not in agent and "Kondor/" not in agent


def choice_of(agent: str) -> str:
    if not agent:
        return KONDOR
    if agent == FIREFOX_AGENT:
        return FIREFOX
    return CHROME if is_chrome_like(agent) else CUSTOM


def agent_for_choice(choice: str, profile_agent: str) -> str:
    if choice == FIREFOX:
        return FIREFOX_AGENT
    return chrome_agent(profile_agent) if choice == CHROME else ""


def keeps_client_hints(agent: str) -> bool:
    return is_chrome_like(agent)
