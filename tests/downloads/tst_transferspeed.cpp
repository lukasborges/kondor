#include "downloads/transferspeed.h"

#include <QtTest>

class TstTransferSpeed : public QObject
{
    Q_OBJECT

private slots:
    void reportsBytesPerSecondAfterOneSecond();
    void keepsSpeedWithinOneSecond();
    void stopResetsSpeed();
};

void TstTransferSpeed::reportsBytesPerSecondAfterOneSecond()
{
    TransferSpeed speed;
    speed.restart(0);
    speed.update(4000, 2000);
    QCOMPARE(speed.bytesPerSecond(), 2000.0);
}

void TstTransferSpeed::keepsSpeedWithinOneSecond()
{
    TransferSpeed speed;
    speed.restart(0);
    speed.update(1000, 1000);
    speed.update(9000, 999);
    QCOMPARE(speed.bytesPerSecond(), 1000.0);
}

void TstTransferSpeed::stopResetsSpeed()
{
    TransferSpeed speed;
    speed.restart(0);
    speed.update(1000, 1000);
    speed.stop();
    QCOMPARE(speed.bytesPerSecond(), 0.0);
}

QTEST_APPLESS_MAIN(TstTransferSpeed)

#include "tst_transferspeed.moc"
