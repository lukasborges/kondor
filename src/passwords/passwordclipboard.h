#pragma once

#include <QObject>
#include <QString>
#include <QTimer>

class PasswordClipboard : public QObject
{
    Q_OBJECT

public:
    explicit PasswordClipboard(QObject *parent = nullptr);

    void copy(const QString &secret);

private:
    void clearIfStillHolding();

    QTimer m_timer;
    QString m_secret;
};
