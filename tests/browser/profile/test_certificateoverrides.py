from PySide6.QtCore import QObject

from kondor.browser.profile.certificateoverrides import CertificateOverrides


def test_marks_hosts_case_insensitively_per_profile() -> None:
    overrides, first, second = CertificateOverrides(), QObject(), QObject()
    overrides.mark(first, "KDE.org")
    assert overrides.is_overridden(first, "kde.org")
    assert overrides.is_overridden(first, "KDE.ORG")
    assert not overrides.is_overridden(second, "kde.org")


def test_ignores_missing_profile_and_empty_host() -> None:
    overrides, profile = CertificateOverrides(), QObject()
    overrides.mark(None, "kde.org")
    overrides.mark(profile, "")
    assert not overrides.is_overridden(None, "kde.org")
    assert not overrides.is_overridden(profile, "")


def test_forget_drops_the_profile() -> None:
    overrides, profile = CertificateOverrides(), QObject()
    overrides.mark(profile, "kde.org")
    overrides.forget(profile)
    assert not overrides.is_overridden(profile, "kde.org")
