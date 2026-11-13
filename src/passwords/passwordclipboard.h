#pragma once

#include <QObject>
#include <QString>
#include <QTimer>

class PasswordClipboard : public QObject
{
    Q_OBJECT

public:
    explicit PasswordClipboard(QObject *parent = nullptr, int clearAfterMs = 30 * 1000);

    void copy(const QString &secret);
    void copyText(const QString &text);

private:
    void clearIfStillHolding();

    QTimer m_timer;
    QString m_secret;
};
