#include "core/defaultbookmarks.h"

#include <QtGlobal>

const QList<DefaultBookmark> kDefaultBookmarks = {
    {"KDE", "https://kde.org/", {}},
    {"Planet KDE", "https://planet.kde.org/", {}},
    {"Qt Docs", "https://doc.qt.io/", {}},
    {QT_TRANSLATE_NOOP("DefaultBookmarks", "News"), nullptr,
     {
         {"LWN.net", "https://lwn.net/", {}},
         {"Phoronix", "https://www.phoronix.com/", {}},
         {"9to5Linux", "https://9to5linux.com/", {}},
         {"OMG! Ubuntu", "https://www.omgubuntu.co.uk/", {}},
         {"GamingOnLinux", "https://www.gamingonlinux.com/", {}},
         {"DistroWatch", "https://distrowatch.com/", {}},
     }},
    {QT_TRANSLATE_NOOP("DefaultBookmarks", "Development"), nullptr,
     {
         {"KDE Developer", "https://develop.kde.org/", {}},
         {"KDE Human Interface Guidelines", "https://develop.kde.org/hig/", {}},
         {"KDE Invent", "https://invent.kde.org/", {}},
         {"freedesktop.org", "https://www.freedesktop.org/", {}},
         {"The Linux Kernel Archives", "https://www.kernel.org/", {}},
         {"Kondor Browser on GitHub", "https://github.com/lukasborges/kondor", {}},
     }},
    {QT_TRANSLATE_NOOP("DefaultBookmarks", "Linux"), nullptr,
     {
         {"Fedora Project", "https://fedoraproject.org/", {}},
         {"Fedora Docs", "https://docs.fedoraproject.org/", {}},
         {"ArchWiki", "https://wiki.archlinux.org/", {}},
         {"Flathub", "https://flathub.org/", {}},
         {"KDE Applications", "https://apps.kde.org/", {}},
         {"KDE UserBase", "https://userbase.kde.org/", {}},
         {"KDE Discuss", "https://discuss.kde.org/", {}},
     }},
};
