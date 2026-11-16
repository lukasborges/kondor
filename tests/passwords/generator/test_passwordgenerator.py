import pytest

from kondor.passwords import passwordgenerator as generator
from kondor.passwords.passwordgenerator import PasswordRules, generate_password, rules_from


def test_default_length_is_twenty() -> None:
    assert len(generate_password(PasswordRules())) == generator.DEFAULT_LENGTH


@pytest.mark.parametrize("length", [8, 33, 64])
def test_returns_the_requested_length(length: int) -> None:
    assert len(generate_password(PasswordRules(length=length))) == length


def test_holds_every_character_class() -> None:
    for _ in range(50):
        password = generate_password(PasswordRules(length=8))
        for group in (
            generator.LOWERCASE,
            generator.UPPERCASE,
            generator.DIGITS,
            generator.SYMBOLS,
        ):
            assert any(char in group for char in password)


def test_holds_no_symbol_when_symbols_are_off() -> None:
    password = generate_password(PasswordRules(length=64, use_symbols=False))
    assert not any(char in generator.SYMBOLS for char in password)


def test_rules_clamp_the_length() -> None:
    assert rules_from({"length": 3}).length == generator.MIN_LENGTH
    assert rules_from({"length": 500}).length == generator.MAX_LENGTH


def test_rules_default_a_missing_or_non_numeric_length() -> None:
    assert rules_from({}).length == generator.DEFAULT_LENGTH
    assert rules_from({"length": "abc"}).length == generator.DEFAULT_LENGTH


def test_rules_read_the_symbols_flag() -> None:
    assert rules_from({"useSymbols": False}).use_symbols is False
    assert rules_from({}).use_symbols is True
