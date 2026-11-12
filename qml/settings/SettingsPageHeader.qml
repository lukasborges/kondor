import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

ColumnLayout {
    id: root

    required property string pageId
    required property string title
    required property int generalTab
    required property int passwordsTab

    readonly property bool hasTabs: pageId === "general" || pageId === "passwords"

    signal generalTabSelected(int index)
    signal passwordsTabSelected(int index)

    Layout.fillWidth: true
    spacing: 0

    Kirigami.Heading {
        objectName: "pageHeading"
        Layout.fillWidth: true
        Layout.margins: Kirigami.Units.smallSpacing
        Layout.leftMargin: Kirigami.Units.largeSpacing
        level: 1
        text: root.title
    }

    TabBar {
        Layout.fillWidth: true
        visible: root.pageId === "general"
        currentIndex: root.generalTab
        onCurrentIndexChanged: root.generalTabSelected(currentIndex)

        TabButton { text: qsTr("Startup") }
        TabButton { text: qsTr("New Tabs") }
    }

    TabBar {
        Layout.fillWidth: true
        visible: root.pageId === "passwords"
        currentIndex: root.passwordsTab
        onCurrentIndexChanged: root.passwordsTabSelected(currentIndex)

        TabButton { text: qsTr("Saved Passwords") }
        TabButton { text: qsTr("Never Saved") }
    }

    Kirigami.Separator {
        Layout.fillWidth: true
        visible: !root.hasTabs
    }
}
