#pragma once

#include <QQmlComponent>
#include <QQmlEngine>
#include <QQuickItem>
#include <QQuickWindow>
#include <QTest>

#include "browser/profile/profilemanager.h"
#include "browser/tabs/tabmodel.h"
#include "../common/qmltesthelpers.h"
#include "core/settings/settings.h"
#include "extensions/catalog/extensioncatalog.h"
#include "extensions/extensionmanager.h"
#include "passwords/passwordstore.h"

inline QObject *pendingOf(QObject *parent)
{
    for (QObject *child : parent->children()) {
        if (child->property("searchEngine").isValid())
            return child;
        if (QObject *found = pendingOf(child))
            return found;
    }
    return nullptr;
}

inline void registerSettingsWindowTypes()
{
    static const bool typesRegistered = [] {
        qmlRegisterType<TabModel>("Kondor", 1, 0, "TabModel");
        registerSingleton<ProfileManager>("ProfileManager");
        registerSingleton<Settings>("Settings");
        registerSingleton<ExtensionManager>("ExtensionManager");
        registerSingleton<ExtensionCatalog>("ExtensionCatalog");
        registerSingleton<PasswordStore>("PasswordStore");
        return true;
    }();
    Q_UNUSED(typesRegistered)
}

inline void resetSettingsToTestDefaults()
{
    Settings *settings = Settings::instance();
    settings->setHomePage(QString());
    settings->setSearchEngine(QStringLiteral("duckduckgo"));
    settings->setCustomSearchUrl(QString());
    settings->setAskWhereToSave(false);
    settings->setStartupBehavior(QStringLiteral("homepage"));
    settings->setShowTopSites(true);
    settings->setClearDataOnExit(false);
    settings->setBlockThirdPartyCookies(false);
}

inline QQuickWindow *createSettingsWindow(QQmlEngine &engine)
{
    engine.addImportPath(QStringLiteral(KONDOR_QML_IMPORT_DIR));
    QQmlComponent component(&engine, QUrl::fromLocalFile(QStringLiteral(KONDOR_QML_DIR
                                                                       "/settings/SettingsWindow.qml")));
    auto *tabs = new TabModel;
    QObject *object = component.createWithInitialProperties(
        { { QStringLiteral("tabModel"), QVariant::fromValue(tabs) } });
    auto *window = qobject_cast<QQuickWindow *>(object);
    if (!window) {
        qWarning() << component.errors();
        delete object;
        delete tabs;
        return nullptr;
    }
    window->resize(860, 600);
    return window;
}

class SettingsWindowFixture
{
public:
    explicit SettingsWindowFixture(QQmlEngine &engine)
        : m_window(createSettingsWindow(engine))
    {
    }

    QQuickWindow *window() const { return m_window.data(); }
    QObject *pending() const { return pendingOf(m_window.data()); }
    bool isModified() const { return m_window->property("modified").toBool(); }

    void invoke(const char *method) { QMetaObject::invokeMethod(m_window.data(), method); }
    void showWindow() { invoke("showWindow"); }

    bool showExposed()
    {
        showWindow();
        return QTest::qWaitForWindowExposed(m_window.data());
    }

private:
    QScopedPointer<QQuickWindow> m_window;
};

inline const QList<QPair<QByteArray, QVariant>> &changedOptionPerPage()
{
    static const QList<QPair<QByteArray, QVariant>> options{
        { "homePage", QStringLiteral("https://kde.org") },
        { "searchEngine", QStringLiteral("google") },
        { "askWhereToSave", true },
        { "blockThirdPartyCookies", true },
        { "offerToSavePasswords", false },
        { "extensionsAutoUpdate", false },
        { "spellCheckEnabled", false },
    };
    return options;
}

inline void verifyOnlyPageReturnedToDefault(QObject *draft, int page)
{
    for (int i = 0; i < changedOptionPerPage().size(); ++i) {
        const auto &option = changedOptionPerPage().at(i);
        const QVariant defaultValue = Settings::instance()->defaultValue(QString::fromLatin1(option.first));
        QCOMPARE(draft->property(option.first.constData()), i == page ? defaultValue : option.second);
    }
}

int runTestSettingsApply(int argc, char *argv[]);
int runTestSettingsNavigation(int argc, char *argv[]);
