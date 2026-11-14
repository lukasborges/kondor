from kondor.adblock.filters.filterengine import FilterEngine, ResourceKind
from pytests.adblock.enginecases import Request, blocked, engine_with

IMAGE = ResourceKind.IMAGE
LISTED_RULES = 2


def test_domain_anchor() -> None:
    engine = engine_with("||ads.example.com^")
    assert blocked(engine, Request("https://ads.example.com/x.js", "news.org"))
    assert blocked(engine, Request("https://sub.ads.example.com/x.js", "news.org"))
    assert not blocked(engine, Request("https://example.com/x.js", "news.org"))
    assert not blocked(engine, Request("https://notads.example.com/x.js", "news.org"))


def test_domain_with_path() -> None:
    engine = engine_with("||example.com/banners/*")
    assert blocked(engine, Request("https://example.com/banners/a.png", "x.org"))
    assert not blocked(engine, Request("https://example.com/other/a.png", "x.org"))


def test_exceptions_win() -> None:
    engine = engine_with("||tracker.net^", "@@||tracker.net^$domain=friendly.org")
    assert blocked(engine, Request("https://tracker.net/p.gif", "news.org"))
    assert not blocked(engine, Request("https://tracker.net/p.gif", "friendly.org"))


def test_third_party_option() -> None:
    engine = engine_with("||cdn.example.com^$third-party")
    assert blocked(engine, Request("https://cdn.example.com/a.js", "other.org"))
    assert not blocked(engine, Request("https://cdn.example.com/a.js", "www.example.com"))


def test_type_options() -> None:
    engine = engine_with("||img.example.com^$image")
    assert blocked(engine, Request("https://img.example.com/a.png", "x.org", IMAGE))
    script = Request("https://img.example.com/a.js", "x.org", ResourceKind.SCRIPT)
    assert not blocked(engine, script)


def test_substring_and_wildcard() -> None:
    engine = engine_with("/adserver/", "-banner-ad.", "/track*.gif?")
    assert blocked(engine, Request("https://a.org/img/top-banner-ad.png", "x.org", IMAGE))
    assert blocked(engine, Request("https://a.org/tracker1.gif?id=2", "x.org", IMAGE))
    assert not blocked(engine, Request("https://a.org/adserver/x.js", "x.org"))


def test_separator_caret() -> None:
    engine = engine_with("/ads^")
    assert blocked(engine, Request("https://a.org/ads?x=1", "x.org"))
    assert blocked(engine, Request("https://a.org/ads", "x.org"))
    assert not blocked(engine, Request("https://a.org/adsense", "x.org"))


def test_skipped_rules() -> None:
    engine = FilterEngine()
    assert not engine.add_rule("! comment")
    assert not engine.add_rule("[Adblock Plus 2.0]")
    assert not engine.add_rule("example.com##.ad")
    assert not engine.add_rule("||example.com^$unknownoption")
    assert not engine.add_rule("/ad[0-9]+/")
    assert engine.rule_count() == 0


def test_main_frame_never_blocked() -> None:
    engine = engine_with("||example.com^")
    page = Request("https://example.com/", "example.com", ResourceKind.MAIN_FRAME)
    assert not blocked(engine, page)


def test_add_list() -> None:
    engine = FilterEngine()
    engine.add_list(b"[Adblock Plus 2.0]\n! x\n||a.com^\r\n||b.com^$script\n##.x\n")
    assert engine.rule_count() == LISTED_RULES


def test_domain_option_includes_and_excludes_sites() -> None:
    engine = engine_with("||ads.net^$domain=news.org|~live.news.org")
    assert blocked(engine, Request("https://ads.net/a.js", "news.org"))
    assert blocked(engine, Request("https://ads.net/a.js", "m.news.org"))
    assert not blocked(engine, Request("https://ads.net/a.js", "live.news.org"))
    assert not blocked(engine, Request("https://ads.net/a.js", "other.org"))


def test_country_code_second_level_domain_is_first_party() -> None:
    engine = engine_with("||cdn.example.co.uk^$third-party")
    assert not blocked(engine, Request("https://cdn.example.co.uk/a.js", "www.example.co.uk"))
    assert blocked(engine, Request("https://cdn.example.co.uk/a.js", "www.other.co.uk"))


def test_end_anchor_requires_the_end_of_the_address() -> None:
    engine = engine_with("/banner.gif|")
    assert blocked(engine, Request("https://a.org/img/banner.gif", "x.org", IMAGE))
    assert not blocked(engine, Request("https://a.org/img/banner.gif?x=1", "x.org", IMAGE))
