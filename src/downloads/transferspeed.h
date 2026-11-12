#pragma once

#include <QElapsedTimer>
#include <QtTypes>

class TransferSpeed
{
public:
    void restart(qint64 receivedBytes);
    void update(qint64 receivedBytes);
    void update(qint64 receivedBytes, qint64 elapsedMs);
    void stop();
    qreal bytesPerSecond() const;

private:
    QElapsedTimer m_timer;
    qint64 m_lastReceivedBytes = 0;
    qreal m_bytesPerSecond = 0.0;
};
