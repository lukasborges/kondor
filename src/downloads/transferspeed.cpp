#include "downloads/transferspeed.h"

namespace {
constexpr qint64 kMinimumSampleMs = 1000;
constexpr qreal kMillisecondsPerSecond = 1000.0;
}

void TransferSpeed::restart(qint64 receivedBytes)
{
    m_bytesPerSecond = 0.0;
    m_lastReceivedBytes = receivedBytes;
    m_timer.restart();
}

void TransferSpeed::update(qint64 receivedBytes)
{
    update(receivedBytes, m_timer.elapsed());
}

void TransferSpeed::update(qint64 receivedBytes, qint64 elapsedMs)
{
    if (elapsedMs < kMinimumSampleMs)
        return;
    m_bytesPerSecond = (receivedBytes - m_lastReceivedBytes) * kMillisecondsPerSecond / elapsedMs;
    m_lastReceivedBytes = receivedBytes;
    m_timer.restart();
}

void TransferSpeed::stop()
{
    m_bytesPerSecond = 0.0;
}

qreal TransferSpeed::bytesPerSecond() const
{
    return m_bytesPerSecond;
}
