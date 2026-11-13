import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

RowLayout {
    id: root

    required property var extension
    required property var tab
    required property string host

    function toggleSite(isEnabled) {
        ExtensionManager.setSiteEnabled(extension.id, tab.url, isEnabled)
        tab.siteReload.recordToggle(extension.id, extension.name, isEnabled)
    }

    Layout.fillWidth: true
    Layout.leftMargin: Kirigami.Units.smallSpacing

    Label {
        text: qsTr("Run on %1").arg(root.host)
        elide: Text.ElideRight
        Layout.fillWidth: true
    }

    Switch {
        objectName: "siteSwitch"
        checked: (ExtensionManager.revision, ExtensionManager.siteEnabled(root.extension.id, root.tab.url))
        //: %1 is the extension name, %2 is the site host
        Accessible.name: qsTr("Run %1 on %2").arg(root.extension.name).arg(root.host)
        onToggled: root.toggleSite(checked)
    }
}
