from typing import NamedTuple

from PySide6.QtCore import QT_TRANSLATE_NOOP

CONTEXT = "DefaultBookmarks"


class DefaultBookmark(NamedTuple):
    title: str
    url: str | None
    children: tuple["DefaultBookmark", ...] = ()

    def is_folder(self) -> bool:
        return self.url is None


def folder(title: str, children: tuple[DefaultBookmark, ...]) -> DefaultBookmark:
    return DefaultBookmark(title, None, children)


NEWS = (
    DefaultBookmark("LWN.net", "https://lwn.net/"),
    DefaultBookmark("Phoronix", "https://www.phoronix.com/"),
    DefaultBookmark("9to5Linux", "https://9to5linux.com/"),
    DefaultBookmark("OMG! Ubuntu", "https://www.omgubuntu.co.uk/"),
    DefaultBookmark("GamingOnLinux", "https://www.gamingonlinux.com/"),
    DefaultBookmark("DistroWatch", "https://distrowatch.com/"),
)

DEVELOPMENT = (
    DefaultBookmark("KDE Developer", "https://develop.kde.org/"),
    DefaultBookmark("KDE Human Interface Guidelines", "https://develop.kde.org/hig/"),
    DefaultBookmark("KDE Invent", "https://invent.kde.org/"),
    DefaultBookmark("freedesktop.org", "https://www.freedesktop.org/"),
    DefaultBookmark("The Linux Kernel Archives", "https://www.kernel.org/"),
    DefaultBookmark("Kondor Browser on GitHub", "https://github.com/lukasborges/kondor-browser"),
)

LINUX = (
    DefaultBookmark("Fedora Project", "https://fedoraproject.org/"),
    DefaultBookmark("Fedora Docs", "https://docs.fedoraproject.org/"),
    DefaultBookmark("ArchWiki", "https://wiki.archlinux.org/"),
    DefaultBookmark("Flathub", "https://flathub.org/"),
    DefaultBookmark("KDE Applications", "https://apps.kde.org/"),
    DefaultBookmark("KDE UserBase", "https://userbase.kde.org/"),
    DefaultBookmark("KDE Discuss", "https://discuss.kde.org/"),
)

DEFAULT_BOOKMARKS = (
    DefaultBookmark("KDE", "https://kde.org/"),
    DefaultBookmark("Planet KDE", "https://planet.kde.org/"),
    DefaultBookmark("Qt Docs", "https://doc.qt.io/"),
    folder(QT_TRANSLATE_NOOP("DefaultBookmarks", "News"), NEWS),
    folder(QT_TRANSLATE_NOOP("DefaultBookmarks", "Development"), DEVELOPMENT),
    folder(QT_TRANSLATE_NOOP("DefaultBookmarks", "Linux"), LINUX),
)
