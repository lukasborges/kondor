#pragma once

#include <QObject>
#include <QUrl>
#include <QtQmlIntegration/qqmlintegration.h>
#include <QQuickWebEngineProfile>

class QQmlEngine;
class QJSEngine;

class ProfileManager : public QObject
{
    Q_OBJECT
    QML_ELEMENT
    QML_SINGLETON

    Q_PROPERTY(QString homePage READ homePage CONSTANT)
    Q_PROPERTY(QString searchEngineUrl READ searchEngineUrl WRITE setSearchEngineUrl
                   NOTIFY searchEngineUrlChanged)

public:
    static ProfileManager *instance();
    static ProfileManager *create(QQmlEngine *engine, QJSEngine *jsEngine);

    // Perfil persistente (cookies, cache, histórico) usado pelas abas normais.
    Q_INVOKABLE QQuickWebEngineProfile *defaultProfile();
    // Perfil off-the-record novo, usado pelas abas privadas.
    Q_INVOKABLE QQuickWebEngineProfile *createPrivateProfile();

    // Transforma o texto digitado em URL: endereço, atalho de host ou busca.
    Q_INVOKABLE QUrl resolveAddress(const QString &text) const;

    QString homePage() const { return m_homePage; }
    QString searchEngineUrl() const { return m_searchEngineUrl; }
    void setSearchEngineUrl(const QString &url);

signals:
    void searchEngineUrlChanged();

private:
    explicit ProfileManager(QObject *parent = nullptr);
    void setupProfile(QQuickWebEngineProfile *profile);

    QString m_homePage = QStringLiteral("https://duckduckgo.com");
    QString m_searchEngineUrl = QStringLiteral("https://duckduckgo.com/?q=%1");
    QQuickWebEngineProfile *m_defaultProfile = nullptr;
};
