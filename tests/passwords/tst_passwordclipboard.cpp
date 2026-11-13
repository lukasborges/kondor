#include <QClipboard>
#include <QGuiApplication>
#include <QMimeData>
#include <QTest>

#include "passwords/passwordclipboard.h"

namespace {
const QString kSecretHint = QStringLiteral("x-kde-passwordManagerHint");
}

class TestPasswordClipboard : public QObject
{
    Q_OBJECT

private slots:
    void copyMarksPasswordSecret();
    void copyTextHasNoSecretHint();
    void copyTextIsNotCleared();
};

void TestPasswordClipboard::copyMarksPasswordSecret()
{
    PasswordClipboard clipboard;

    clipboard.copy(QStringLiteral("hunter2"));

    const QMimeData *data = QGuiApplication::clipboard()->mimeData();
    QCOMPARE(data->text(), QStringLiteral("hunter2"));
    QCOMPARE(data->data(kSecretHint), QByteArrayLiteral("secret"));
}

void TestPasswordClipboard::copyTextHasNoSecretHint()
{
    PasswordClipboard clipboard;

    clipboard.copyText(QStringLiteral("ana"));

    QVERIFY(!QGuiApplication::clipboard()->mimeData()->hasFormat(kSecretHint));
}

void TestPasswordClipboard::copyTextIsNotCleared()
{
    PasswordClipboard clipboard(nullptr, 20);
    clipboard.copy(QStringLiteral("hunter2"));

    clipboard.copyText(QStringLiteral("ana"));

    QTest::qWait(100);
    QCOMPARE(QGuiApplication::clipboard()->text(), QStringLiteral("ana"));
}

QTEST_MAIN(TestPasswordClipboard)
#include "tst_passwordclipboard.moc"
