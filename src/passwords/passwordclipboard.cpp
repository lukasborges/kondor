#include "passwords/passwordclipboard.h"

#include <QClipboard>
#include <QGuiApplication>
#include <QMimeData>

PasswordClipboard::PasswordClipboard(QObject *parent, int clearAfterMs)
    : QObject(parent)
{
    m_timer.setSingleShot(true);
    m_timer.setInterval(clearAfterMs);
    connect(&m_timer, &QTimer::timeout, this, &PasswordClipboard::clearIfStillHolding);
}

void PasswordClipboard::copy(const QString &secret)
{
    auto *data = new QMimeData;
    data->setText(secret);
    data->setData(QStringLiteral("x-kde-passwordManagerHint"), QByteArrayLiteral("secret"));
    QGuiApplication::clipboard()->setMimeData(data);
    m_secret = secret;
    m_timer.start();
}

void PasswordClipboard::copyText(const QString &text)
{
    QGuiApplication::clipboard()->setText(text);
}

void PasswordClipboard::clearIfStillHolding()
{
    QClipboard *clipboard = QGuiApplication::clipboard();
    if (!m_secret.isEmpty() && clipboard->text() == m_secret)
        clipboard->clear();
    m_secret.clear();
}
