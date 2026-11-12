#pragma once

#include <QList>
#include <QStringList>
#include <QUrl>
#include <QVariantMap>
#include <QtWebEngineCore/qwebenginecontextmenurequest.h>

#include "core/settings.h"

using Request = QWebEngineContextMenuRequest;

namespace {
const QString kSeparator = QStringLiteral("-");

QVariantMap link()
{
    return { { QStringLiteral("linkUrl"), QUrl(QStringLiteral("https://link.example/")) } };
}

QVariantMap image()
{
    return { { QStringLiteral("mediaType"), int(Request::MediaTypeImage) } };
}

QVariantMap video()
{
    const int flags = Request::MediaCanToggleControls | Request::MediaControls;
    return { { QStringLiteral("mediaType"), int(Request::MediaTypeVideo) },
             { QStringLiteral("mediaFlags"), flags } };
}

QVariantMap selection()
{
    return { { QStringLiteral("selectedText"), QStringLiteral("some words") } };
}

QVariantMap misspelledField()
{
    return { { QStringLiteral("isContentEditable"), true },
             { QStringLiteral("misspelledWord"), QStringLiteral("helo") },
             { QStringLiteral("spellCheckerSuggestions"), QStringList{ QStringLiteral("hello") } },
             { QStringLiteral("editFlags"), int(Request::CanPaste) } };
}

QVariantMap withLinkAndImage()
{
    QVariantMap request = link();
    request.insert(image());
    return request;
}

struct Case
{
    const char *name;
    QVariantMap request;
    QStringList items;
};

const QStringList kInspect{ kSeparator, QStringLiteral("Inspect Element") };
const QStringList kLinkItems{ QStringLiteral("Open Link in New Tab"),
                              QStringLiteral("Open Link in New Private Tab"), kSeparator,
                              QStringLiteral("Copy Link Address"),
                              QStringLiteral("Save Link As…") };
const QStringList kImageItems{ QStringLiteral("Open Image in New Tab"),
                               QStringLiteral("Save Image As…"), QStringLiteral("Copy Image"),
                               QStringLiteral("Copy Image Address") };

const QList<Case> kCases = {
    { "link", link(), kLinkItems + kInspect },
    { "image", image(), kImageItems + kInspect },
    { "linkAndImage", withLinkAndImage(), kLinkItems + QStringList{ kSeparator } + kImageItems + kInspect },
    { "videoWithControls", video(),
      QStringList{ QStringLiteral("Save Media As…"), QStringLiteral("Copy Media Address"),
                   kSeparator, QStringLiteral("Show Controls"), QStringLiteral("Loop") } + kInspect },
    { "selection", selection(), QStringList{ QStringLiteral("Copy"), QStringLiteral("%SEARCH%") } + kInspect },
    { "misspelledField", misspelledField(),
      QStringList{ QStringLiteral("hello"), kSeparator, QStringLiteral("Undo"),
                   QStringLiteral("Redo"), kSeparator, QStringLiteral("Cut"),
                   QStringLiteral("Copy"), QStringLiteral("Paste"),
                   QStringLiteral("Paste as Plain Text"), QStringLiteral("Select All") } + kInspect },
    { "nothing", {}, QStringList{ QStringLiteral("Back"), QStringLiteral("Forward"),
                                  QStringLiteral("Reload"), kSeparator,
                                  QStringLiteral("View Page Source") } + kInspect }
};

QString searchItem()
{
    const QString engine = Settings::instance()->searchEngineName();
    if (engine.isEmpty())
        return QStringLiteral("Search for “some words”");
    return QStringLiteral("Search %1 for “some words”").arg(engine);
}
}
