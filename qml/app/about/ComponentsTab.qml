import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

ScrollView {
    id: root
    contentWidth: availableWidth
    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

    signal linkActivated(string url)

    readonly property var components: [
        {
            name: "Qt",
            version: AboutInfo.qtRuntimeVersion,
            description: qsTr("Using %1 (built against %2)")
                         .arg(AboutInfo.qtRuntimeVersion)
                         .arg(AboutInfo.qtBuildVersion),
            link: "https://www.qt.io/"
        },
        {
            name: "Qt WebEngine",
            version: AboutInfo.webEngineVersion,
            description: qsTr("Chromium %1").arg(AboutInfo.chromiumVersion),
            link: "https://doc.qt.io/qt-6/qtwebengine-index.html"
        },
        {
            name: "Kirigami",
            version: "",
            description: qsTr("KDE user interface framework, used for the Breeze look"),
            link: "https://develop.kde.org/frameworks/kirigami/"
        },
        {
            name: qsTr("Windowing System"),
            version: "",
            description: AboutInfo.windowingSystem,
            link: ""
        },
        {
            name: qsTr("Operating System"),
            version: "",
            description: AboutInfo.operatingSystem,
            link: ""
        }
    ]

    ColumnLayout {
        width: root.availableWidth
        spacing: Kirigami.Units.largeSpacing

        Repeater {
            model: root.components

            delegate: ColumnLayout {
                required property var modelData
                spacing: 0

                Label {
                    font.bold: true
                    text: modelData.version.length > 0
                          ? "%1 %2".arg(modelData.name).arg(modelData.version)
                          : modelData.name
                }
                Label {
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                    text: modelData.description
                }
                Label {
                    Layout.fillWidth: true
                    visible: modelData.link.length > 0
                    textFormat: Text.RichText
                    linkColor: Kirigami.Theme.linkColor
                    text: "<a href=\"" + modelData.link + "\">" + modelData.link + "</a>"
                    onLinkActivated: function(link) {
                        root.linkActivated(link)
                    }
                }
            }
        }
    }
}
