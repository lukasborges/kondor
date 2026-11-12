#pragma once

#include <QQmlComponent>
#include <QQmlEngine>
#include <QSqlQuery>
#include <QTest>
#include <QVariantList>
#include <QVariantMap>
#include <memory>

#include "bookmarks/bookmarkmanager.h"
#include "browser/faviconstore.h"
#include "browser/profilemanager.h"
#include "common/qmltesthelpers.h"
#include "core/database.h"
#include "core/settings.h"
#include "history/historymanager.h"

class SeededBookmarkFolder
{
public:
    explicit SeededBookmarkFolder(qint64 id) : m_id(id) {}
    ~SeededBookmarkFolder() { BookmarkManager::instance()->remove(m_id); }

private:
    qint64 m_id;
};

class AddressSuggestionsFixture : public QObject
{
protected:
    void registerSuggestionTypes()
    {
        QVERIFY2(Database::instance()->isValid(), "the test database must open");
        registerSingleton<ProfileManager>("ProfileManager");
        registerSingleton<HistoryManager>("HistoryManager");
        registerSingleton<BookmarkManager>("BookmarkManager");
        registerSingleton<FaviconStore>("FaviconStore");
        registerSingleton<Settings>("Settings");
    }

    void clearHistory()
    {
        QSqlQuery clear(Database::instance()->handle());
        QVERIFY(clear.exec(QStringLiteral("DELETE FROM history")));
    }

    QObject *createPopup()
    {
        m_engine.addImportPath(QStringLiteral(KONDOR_QML_IMPORT_DIR));
        QQmlComponent component(&m_engine, QUrl::fromLocalFile(QStringLiteral(
            KONDOR_QML_DIR "/browser/AddressSuggestions.qml")));
        QObject *popup = component.create();
        if (!popup)
            qWarning() << component.errors();
        return popup;
    }

    std::unique_ptr<QObject> popupTyping(const QString &text)
    {
        std::unique_ptr<QObject> popup(createPopup());
        if (!popup) {
            QTest::qFail("the popup must load", __FILE__, __LINE__);
            return popup;
        }
        popup->setProperty("text", text);
        return popup;
    }

    void addHistory(const QString &url, const QString &title, qint64 visitedAt)
    {
        QSqlQuery insert(Database::instance()->handle());
        insert.prepare(QStringLiteral(
            "INSERT INTO history (url, title, visited_at) VALUES (?, ?, ?)"));
        insert.addBindValue(url);
        insert.addBindValue(title);
        insert.addBindValue(visitedAt);
        QVERIFY(insert.exec());
    }

    qint64 addPlasmaBookmark()
    {
        BookmarkManager *bookmarks = BookmarkManager::instance();
        const qint64 folder = bookmarks->addFolder(QStringLiteral("Address suggestions test"),
                                                   bookmarks->otherFolderId());
        const qint64 bookmark = bookmarks->addBookmark(
            QUrl(QStringLiteral("https://kde.org/hig/")), QStringLiteral("Plasma HIG"), folder);
        if (bookmark <= 0)
            QTest::qFail("bookmark was not added", __FILE__, __LINE__);
        return folder;
    }

    void addPlasmaHistory()
    {
        const qint64 now = 1000000;
        addHistory(QStringLiteral("https://kde.org/"), QStringLiteral("KDE Community"), now - 3000);
        addHistory(QStringLiteral("https://kde.org/"), QStringLiteral("KDE Community"), now - 2000);
        addHistory(QStringLiteral("https://plasma.kde.org/"), QStringLiteral("KDE Plasma"),
                   now - 1000);
    }

    static QVariantList rowsOf(QObject *popup) { return popup->property("rows").toList(); }

    static QString fieldOf(const QVariantList &rows, int row, const char *key)
    {
        return rows.at(row).toMap().value(QString::fromLatin1(key)).toString();
    }

    static bool hasRowWithIcon(const QVariantList &rows, const char *iconName)
    {
        for (const QVariant &row : rows) {
            if (row.toMap().value(QStringLiteral("iconName")).toString()
                    == QLatin1String(iconName)) {
                return true;
            }
        }
        return false;
    }

    static bool hasRowWithIconAndLabel(const QVariantList &rows, const char *iconName,
                                       const char *label)
    {
        for (const QVariant &row : rows) {
            const QVariantMap entry = row.toMap();
            if (entry.value(QStringLiteral("iconName")).toString() == QLatin1String(iconName)
                    && entry.value(QStringLiteral("label")).toString() == QLatin1String(label)) {
                return true;
            }
        }
        return false;
    }

    QQmlEngine m_engine;
};
