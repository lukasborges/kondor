#include "extensionsuiharness.h"

class TestExtensionDialogs : public QObject
{
    Q_OBJECT

private slots:
    void initTestCase();
    void cleanup();
    void configureDialogWritesValuesOnAccept();
    void restoreDefaultsStaysPending();
    void installDialogShowsPendingInstall();
    void closingTheInstallDialogDropsThePendingInstall();
    void notAnExtensionShowsOnlyTheError();

private:
    QObject *openDialog(const char *qml);

    QTemporaryDir m_work;
    QQmlEngine m_engine;
    QScopedPointer<QObject> m_window;
};

void TestExtensionDialogs::initTestCase()
{
    QVERIFY(m_work.isValid());
}

void TestExtensionDialogs::cleanup()
{
    m_window.reset();
    removeEveryExtension();
}

QObject *TestExtensionDialogs::openDialog(const char *qml)
{
    m_window.reset(createInWindow(&m_engine, qml));
    return m_window ? childObject(m_window.data(), "dialog") : nullptr;
}

void TestExtensionDialogs::configureDialogWritesValuesOnAccept()
{
    QVERIFY(installSample(m_work.path()));
    QObject *dialog = openDialog(settingsDialogQml);
    QVERIFY(dialog);
    QMetaObject::invokeMethod(dialog, "openFor", Q_ARG(QVariant, QStringLiteral("sample")));
    QCOMPARE(dialog->property("values").toMap().value(QStringLiteral("greeting")).toString(), QStringLiteral("hello"));
    QCOMPARE(dialog->property("schema").toList().size(), 4);

    QMetaObject::invokeMethod(dialog, "setValue", Q_ARG(QVariant, QStringLiteral("greeting")),
                              Q_ARG(QVariant, QStringLiteral("ola")));
    dialog->setProperty("privateAllowed", true);
    QCOMPARE(settingValue(QStringLiteral("greeting")), QStringLiteral("hello"));
    QMetaObject::invokeMethod(dialog, "accept");
    QCOMPARE(settingValue(QStringLiteral("greeting")), QStringLiteral("ola"));
    ExtensionManager *manager = ExtensionManager::instance();
    QVERIFY(manager->data(manager->index(0), ExtensionManager::PrivateAllowedRole).toBool());
}

void TestExtensionDialogs::restoreDefaultsStaysPending()
{
    QVERIFY(installSample(m_work.path()));
    applySettings(QStringLiteral("sample"), {{QStringLiteral("greeting"), QStringLiteral("ola")}});
    QObject *dialog = openDialog(settingsDialogQml);
    QVERIFY(dialog);
    QMetaObject::invokeMethod(dialog, "openFor", Q_ARG(QVariant, QStringLiteral("sample")));
    QMetaObject::invokeMethod(dialog, "restoreDefaults");
    QCOMPARE(dialog->property("values").toMap().value(QStringLiteral("greeting")).toString(), QStringLiteral("hello"));
    QCOMPARE(settingValue(QStringLiteral("greeting")), QStringLiteral("ola"));
}

void TestExtensionDialogs::installDialogShowsPendingInstall()
{
    QObject *dialog = openDialog(installDialogQml);
    QVERIFY(dialog);
    QVERIFY(!dialog->property("visible").toBool());

    ExtensionManager::instance()->inspectFile(samplePackage(m_work.path()));
    QVERIFY(dialog->property("isValid").toBool());
    QTRY_VERIFY(dialog->property("visible").toBool());
    QVERIFY(!dialog->property("replacing").toBool());
}

void TestExtensionDialogs::closingTheInstallDialogDropsThePendingInstall()
{
    QObject *dialog = openDialog(installDialogQml);
    QVERIFY(dialog);
    ExtensionManager::instance()->inspectFile(samplePackage(m_work.path()));
    QTRY_VERIFY(dialog->property("visible").toBool());

    QMetaObject::invokeMethod(dialog, "close");
    QTRY_VERIFY(ExtensionManager::instance()->pendingInstall().isEmpty());
}

void TestExtensionDialogs::notAnExtensionShowsOnlyTheError()
{
    QObject *dialog = openDialog(installDialogQml);
    QVERIFY(dialog);
    const QString notZip = m_work.path() + QStringLiteral("/bad.kondorext");
    QVERIFY(writeFile(notZip, "nope"));
    ExtensionManager::instance()->inspectFile(notZip);
    QVERIFY(!dialog->property("isValid").toBool());
    QVERIFY(dialog->property("hasInfo").toBool());
    QTRY_VERIFY(dialog->property("visible").toBool());
    ExtensionManager::instance()->cancelInstall();
}

int runTestExtensionDialogs(int argc, char *argv[])
{
    TestExtensionDialogs test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_extensiondialogs.moc"
