#include "passwords/passwordclipboard.h"

#include <QClipboard>
#include <QGuiApplication>

namespace {
constexpr int kClearAfterMs = 30 * 1000;
}

PasswordClipboard::PasswordClipboard(QObject *parent)
    : QObject(parent)
{
    m_timer.setSingleShot(true);
    m_timer.setInterval(kClearAfterMs);
    connect(&m_timer, &QTimer::timeout, this, &PasswordClipboard::clearIfStillHolding);
}

void PasswordClipboard::copy(const QString &secret)
{
    QGuiApplication::clipboard()->setText(secret);
    m_secret = secret;
    m_timer.start();
}

void PasswordClipboard::clearIfStillHolding()
{
    QClipboard *clipboard = QGuiApplication::clipboard();
    if (!m_secret.isEmpty() && clipboard->text() == m_secret)
        clipboard->clear();
    m_secret.clear();
}
