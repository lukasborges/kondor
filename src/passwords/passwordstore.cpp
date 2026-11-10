#include "passwordstore.h"

#include <KWallet>

#include <QClipboard>
#include <QGuiApplication>
#include <QMap>

namespace {
const QString kFolder = QStringLiteral("Kondor");
constexpr int kClipboardClearMs = 30 * 1000;
}

PasswordStore *PasswordStore::instance()
{
    static PasswordStore *store = new PasswordStore;
    return store;
}

PasswordStore *PasswordStore::create(QQmlEngine *engine, QJSEngine *jsEngine)
{
    Q_UNUSED(engine)
    Q_UNUSED(jsEngine)
    return instance();
}

PasswordStore::PasswordStore(QObject *parent)
    : QObject(parent)
{
    m_clipboardTimer.setSingleShot(true);
    m_clipboardTimer.setInterval(kClipboardClearMs);
    connect(&m_clipboardTimer, &QTimer::timeout, this, &PasswordStore::clearClipboardIfStillHolds);
}

QString PasswordStore::originOf(const QUrl &url)
{
    const QString scheme = url.scheme().toLower();
    if ((scheme != QLatin1String("http") && scheme != QLatin1String("https")) || url.host().isEmpty())
        return {};
    QString origin = scheme + QLatin1String("://") + url.host(QUrl::FullyEncoded).toLower();
    const int port = url.port();
    const bool defaultPort = port == -1 || (scheme == QLatin1String("http") && port == 80)
        || (scheme == QLatin1String("https") && port == 443);
    if (!defaultPort)
        origin += QLatin1Char(':') + QString::number(port);
    return origin;
}

QString PasswordStore::originFromInput(const QString &text)
{
    QString input = text.trimmed();
    if (input.isEmpty())
        return {};
    if (!input.contains(QLatin1String("://")))
        input.prepend(QLatin1String("https://"));
    const QString origin = originOf(QUrl(input));
    return canSaveFor(origin) ? origin : QString();
}

bool PasswordStore::contains(const QString &origin, const QString &username) const
{
    return usernames(origin).contains(username);
}

QString PasswordStore::hostOfOrigin(const QString &origin)
{
    return QUrl(origin).host();
}

bool PasswordStore::canSaveFor(const QString &origin)
{
    const QUrl url(origin);
    const QString host = url.host(QUrl::FullyEncoded).toLower();
    if (url.scheme() == QLatin1String("https"))
        return !host.isEmpty();
    return url.scheme() == QLatin1String("http")
        && (host == QLatin1String("localhost") || host.endsWith(QLatin1String(".localhost")));
}

QString PasswordStore::state() const
{
    switch (m_state) {
    case State::Closed:
        return QStringLiteral("closed");
    case State::Opening:
        return QStringLiteral("opening");
    case State::Open:
        return QStringLiteral("open");
    case State::Unavailable:
        break;
    }
    return QStringLiteral("unavailable");
}

void PasswordStore::setState(State state)
{
    if (m_state == state)
        return;
    m_state = state;
    emit stateChanged();
    emit changed();
}

void PasswordStore::ensureOpen()
{
    if (m_state != State::Closed)
        return;
    // Tests and agent runs must never reach the session wallet.
    if (qEnvironmentVariableIntValue("KONDOR_NO_KWALLET") != 0) {
        setState(State::Unavailable);
        return;
    }
    setState(State::Opening);
    m_wallet = KWallet::Wallet::openWallet(KWallet::Wallet::NetworkWallet(), 0,
                                           KWallet::Wallet::Asynchronous);
    if (!m_wallet) {
        setState(State::Unavailable);
        return;
    }
    connect(m_wallet, &KWallet::Wallet::walletOpened, this, &PasswordStore::onWalletOpened);
    connect(m_wallet, &KWallet::Wallet::walletClosed, this, [this] {
        // Closed from outside (KWalletManager, timeout): reopen on next use.
        closeWallet();
        m_usernames.clear();
        setState(State::Closed);
    });
}

void PasswordStore::closeWallet()
{
    if (!m_wallet)
        return;
    m_wallet->disconnect(this);
    m_wallet->deleteLater();
    m_wallet = nullptr;
}

void PasswordStore::retry()
{
    if (m_state == State::Opening || m_state == State::Open)
        return;
    closeWallet();
    m_state = State::Closed;
    ensureOpen();
}

void PasswordStore::onWalletOpened(bool success)
{
    if (!success || !m_wallet || !m_wallet->isOpen()) {
        closeWallet();
        setState(State::Unavailable);
        return;
    }
    if (!m_wallet->hasFolder(kFolder) && !m_wallet->createFolder(kFolder)) {
        closeWallet();
        setState(State::Unavailable);
        return;
    }
    m_wallet->setFolder(kFolder);
    reloadUsernames();
    setState(State::Open);
    emit changed();
}

void PasswordStore::reloadUsernames()
{
    m_usernames.clear();
    if (!m_wallet || !m_wallet->isOpen())
        return;
    m_wallet->setFolder(kFolder);
    const QStringList origins = m_wallet->entryList();
    for (const QString &origin : origins) {
        QMap<QString, QString> map;
        if (m_wallet->readMap(origin, map) != 0)
            continue;
        QStringList names = map.keys();
        names.sort(Qt::CaseInsensitive);
        if (!names.isEmpty())
            m_usernames.insert(origin, names);
    }
}

QVariantList PasswordStore::entries() const
{
    QVariantList list;
    for (auto it = m_usernames.cbegin(); it != m_usernames.cend(); ++it) {
        for (const QString &name : it.value()) {
            list.append(QVariantMap{
                {QStringLiteral("origin"), it.key()},
                {QStringLiteral("host"), hostOfOrigin(it.key())},
                {QStringLiteral("username"), name},
            });
        }
    }
    return list;
}

QStringList PasswordStore::usernames(const QString &origin) const
{
    return m_usernames.value(origin);
}

QString PasswordStore::password(const QString &origin, const QString &username) const
{
    if (!isOpen() || !m_wallet->isOpen())
        return {};
    m_wallet->setFolder(kFolder);
    QMap<QString, QString> map;
    if (m_wallet->readMap(origin, map) != 0)
        return {};
    return map.value(username);
}

QVariantList PasswordStore::credentialsFor(const QString &origin) const
{
    QVariantList list;
    if (!isOpen() || !m_wallet->isOpen() || !m_usernames.contains(origin))
        return list;
    m_wallet->setFolder(kFolder);
    QMap<QString, QString> map;
    if (m_wallet->readMap(origin, map) != 0)
        return list;
    for (auto it = map.cbegin(); it != map.cend(); ++it) {
        list.append(QVariantMap{
            {QStringLiteral("username"), it.key()},
            {QStringLiteral("password"), it.value()},
        });
    }
    return list;
}

bool PasswordStore::save(const QString &origin, const QString &username, const QString &password)
{
    if (!isOpen() || !m_wallet->isOpen() || origin.isEmpty())
        return false;
    m_wallet->setFolder(kFolder);
    QMap<QString, QString> map;
    m_wallet->readMap(origin, map);
    map.insert(username, password);
    if (m_wallet->writeMap(origin, map) != 0)
        return false;
    reloadUsernames();
    emit changed();
    return true;
}

void PasswordStore::remove(const QString &origin, const QString &username)
{
    if (!isOpen() || !m_wallet->isOpen())
        return;
    m_wallet->setFolder(kFolder);
    QMap<QString, QString> map;
    if (m_wallet->readMap(origin, map) != 0 || !map.contains(username))
        return;
    map.remove(username);
    if (map.isEmpty())
        m_wallet->removeEntry(origin);
    else
        m_wallet->writeMap(origin, map);
    reloadUsernames();
    emit changed();
}

void PasswordStore::copyPassword(const QString &origin, const QString &username)
{
    const QString secret = password(origin, username);
    if (secret.isEmpty())
        return;
    QGuiApplication::clipboard()->setText(secret);
    m_copiedPassword = secret;
    m_clipboardTimer.start();
}

void PasswordStore::clearClipboardIfStillHolds()
{
    QClipboard *clipboard = QGuiApplication::clipboard();
    if (!m_copiedPassword.isEmpty() && clipboard->text() == m_copiedPassword)
        clipboard->clear();
    m_copiedPassword.clear();
}
