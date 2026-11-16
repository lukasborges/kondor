import secrets
import string
from collections.abc import Mapping
from dataclasses import dataclass

LOWERCASE = string.ascii_lowercase
UPPERCASE = string.ascii_uppercase
DIGITS = string.digits
SYMBOLS = "!#$%&*+-.=?@_"
DEFAULT_LENGTH = 20
MIN_LENGTH = 8
MAX_LENGTH = 64


@dataclass(frozen=True)
class PasswordRules:
    length: int = DEFAULT_LENGTH
    use_symbols: bool = True


def clamped_length(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return DEFAULT_LENGTH
    return max(MIN_LENGTH, min(MAX_LENGTH, int(value)))


def rules_from(values: Mapping[str, object]) -> PasswordRules:
    return PasswordRules(
        length=clamped_length(values.get("length")),
        use_symbols=values.get("useSymbols") is not False,
    )


def classes_in_use(rules: PasswordRules) -> list[str]:
    classes = [LOWERCASE, UPPERCASE, DIGITS]
    return [*classes, SYMBOLS] if rules.use_symbols else classes


def draw(rules: PasswordRules, alphabet: str) -> str:
    return "".join(secrets.choice(alphabet) for _ in range(rules.length))


def holds_every_class(password: str, classes: list[str]) -> bool:
    return all(any(char in group for char in password) for group in classes)


def generate_password(rules: PasswordRules) -> str:
    classes = classes_in_use(rules)
    alphabet = "".join(classes)
    password = draw(rules, alphabet)
    while not holds_every_class(password, classes):
        password = draw(rules, alphabet)
    return password
