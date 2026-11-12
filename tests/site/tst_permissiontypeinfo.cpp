#include <QGuiApplication>
#include <QQmlComponent>
#include <QQmlEngine>
#include <QQuickStyle>
#include <QTemporaryDir>
#include <QTest>
#include <QWebEnginePermission>
#include <QtWebEngineQuick/qtwebenginequickglobal.h>

using Type = QWebEnginePermission::PermissionType;

namespace {
struct Expectation
{
    const char *name;
    int type;
    const char *icon;
    const char *label;
    const char *sentence;
};

const int kUnknownType = 9999;

const Expectation kExpectations[] = {
    { "microphone", int(Type::MediaAudioCapture), "audio-input-microphone", "Microphone",
      "<b>site.example</b> wants to use your <b>microphone</b>." },
    { "camera", int(Type::MediaVideoCapture), "camera-web", "Camera",
      "<b>site.example</b> wants to use your <b>camera</b>." },
    { "cameraAndMicrophone", int(Type::MediaAudioVideoCapture), "camera-web",
      "Camera and Microphone",
      "<b>site.example</b> wants to use your <b>camera</b> and <b>microphone</b>." },
    { "screen", int(Type::DesktopVideoCapture), "video-display", "Screen",
      "<b>site.example</b> wants to share your <b>screen</b>." },
    { "screenAndMicrophone", int(Type::DesktopAudioVideoCapture), "video-display",
      "Screen and Microphone",
      "<b>site.example</b> wants to share your <b>screen</b> and <b>microphone</b>." },
    { "pointerLock", int(Type::MouseLock), "input-mouse", "Pointer Lock",
      "<b>site.example</b> wants to lock your <b>pointer</b>." },
    { "notifications", int(Type::Notifications), "preferences-desktop-notification",
      "Notifications", "<b>site.example</b> wants to show you <b>notifications</b>." },
    { "location", int(Type::Geolocation), "mark-location", "Location",
      "<b>site.example</b> wants to know your <b>location</b>." },
    { "clipboard", int(Type::ClipboardReadWrite), "edit-paste", "Clipboard",
      "<b>site.example</b> wants to read your <b>clipboard</b>." },
    { "localFonts", int(Type::LocalFontsAccess), "preferences-desktop-font", "Local Fonts",
      "<b>site.example</b> wants to use your <b>local fonts</b>." },
    { "unknown", kUnknownType, "security-high", "Permission",
      "<b>site.example</b> is requesting a <b>permission</b>." }
};
}

class TestPermissionTypeInfo : public QObject
{
    Q_OBJECT

private slots:
    void initTestCase();
    void everyTypeHasIconLabelAndSentence_data();
    void everyTypeHasIconLabelAndSentence();
    void hostComesFromTheOrigin();

private:
    QVariant call(const char *method, const QVariantList &arguments);
    QQmlEngine m_engine;
    QObject *m_info = nullptr;
};

void TestPermissionTypeInfo::initTestCase()
{
    m_engine.addImportPath(QStringLiteral(KONDOR_QML_IMPORT_DIR));
    QQmlComponent component(&m_engine,
                            QUrl::fromLocalFile(QStringLiteral(KONDOR_QML_DIR
                                                               "/site/PermissionTypeInfo.qml")));
    m_info = component.create();
    if (!m_info)
        qWarning() << component.errors();
    QVERIFY(m_info);
}

QVariant TestPermissionTypeInfo::call(const char *method, const QVariantList &arguments)
{
    QVariant result;
    const QVariant first = arguments.value(0);
    if (arguments.size() == 1)
        QMetaObject::invokeMethod(m_info, method, Q_RETURN_ARG(QVariant, result),
                                  Q_ARG(QVariant, first));
    else
        QMetaObject::invokeMethod(m_info, method, Q_RETURN_ARG(QVariant, result),
                                  Q_ARG(QVariant, first), Q_ARG(QVariant, arguments.value(1)));
    return result;
}

void TestPermissionTypeInfo::everyTypeHasIconLabelAndSentence_data()
{
    QTest::addColumn<int>("type");
    QTest::addColumn<QString>("icon");
    QTest::addColumn<QString>("label");
    QTest::addColumn<QString>("sentence");

    for (const Expectation &row : kExpectations)
        QTest::newRow(row.name) << row.type << QString::fromLatin1(row.icon)
                                << QString::fromLatin1(row.label)
                                << QString::fromLatin1(row.sentence);
}

void TestPermissionTypeInfo::everyTypeHasIconLabelAndSentence()
{
    QFETCH(int, type);
    QFETCH(QString, icon);
    QFETCH(QString, label);
    QFETCH(QString, sentence);

    QCOMPARE(call("iconFor", { type }).toString(), icon);
    QCOMPARE(call("labelFor", { type }).toString(), label);
    QCOMPARE(call("sentenceFor", { type, QStringLiteral("site.example") }).toString(), sentence);
}

void TestPermissionTypeInfo::hostComesFromTheOrigin()
{
    QCOMPARE(call("hostFor", { QStringLiteral("https://meet.jit.si/room") }).toString(),
             QStringLiteral("meet.jit.si"));
}

int main(int argc, char *argv[])
{
    QCoreApplication::setAttribute(Qt::AA_ShareOpenGLContexts);
    QtWebEngineQuick::initialize();

    QTemporaryDir home;
    if (!home.isValid())
        return 1;
    qputenv("XDG_DATA_HOME", home.path().toUtf8());
    qputenv("XDG_CONFIG_HOME", home.path().toUtf8());
    qputenv("XDG_CACHE_HOME", home.path().toUtf8());

    QGuiApplication app(argc, argv);
    QQuickStyle::setStyle(QStringLiteral("org.kde.desktop"));

    TestPermissionTypeInfo test;
    return QTest::qExec(&test, argc, argv);
}

#include "tst_permissiontypeinfo.moc"
