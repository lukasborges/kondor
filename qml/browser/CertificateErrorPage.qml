import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

// Full-page warning shown over the WebEngineView while the tab has a pending
// certificate error. Back to Safety rejects it; an overridable error also
// offers an explicit, secondary "Continue Anyway (Unsafe)".
Item {
    id: root

    required property Tab tab
    property bool advanced: false

    readonly property string host: {
        if (!tab)
            return ""
        const text = tab.security.certificateErrorUrl.toString()
        const match = text.match(/^[a-z][a-z0-9+.-]*:\/\/([^\/?#]+)/i)
        return match ? match[1] : text
    }

    onVisibleChanged: {
        if (visible)
            advanced = false
    }

    Rectangle {
        anchors.fill: parent
        Kirigami.Theme.colorSet: Kirigami.Theme.View
        Kirigami.Theme.inherit: false
        color: Kirigami.Theme.backgroundColor

        ColumnLayout {
            anchors.centerIn: parent
            width: Math.min(parent.width - 2 * Kirigami.Units.gridUnit, 560)
            spacing: Kirigami.Units.largeSpacing * 2

            Kirigami.Icon {
                source: "security-low"
                Layout.preferredWidth: 96
                Layout.preferredHeight: 96
                Layout.alignment: Qt.AlignHCenter
            }

            Kirigami.Heading {
                level: 1
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
                text: qsTr("Your connection is not private")
            }

            Label {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                horizontalAlignment: Text.AlignHCenter
                textFormat: Text.RichText
                text: qsTr("Attackers might be trying to steal your information from <b>%1</b> (for example, passwords, messages or credit cards).").arg(root.host)
            }

            Label {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                horizontalAlignment: Text.AlignHCenter
                color: Kirigami.Theme.disabledTextColor
                text: root.tab.security.certificateErrorDescription
                visible: text.length > 0
            }

            RowLayout {
                Layout.alignment: Qt.AlignHCenter
                spacing: Kirigami.Units.largeSpacing

                Button {
                    text: qsTr("Advanced…")
                    icon.name: root.advanced ? "arrow-up" : "arrow-down"
                    flat: true
                    visible: root.tab.security.certificateErrorOverridable
                    onClicked: root.advanced = !root.advanced
                }

                Button {
                    text: qsTr("Back to Safety")
                    icon.name: "go-previous"
                    highlighted: true
                    onClicked: root.tab.rejectCertificateError()
                }
            }

            Kirigami.InlineMessage {
                Layout.fillWidth: true
                visible: root.advanced && root.tab.security.certificateErrorOverridable
                type: Kirigami.MessageType.Warning
                text: qsTr("This site could not prove its identity. Continuing may expose your data.")
                actions: [
                    Kirigami.Action {
                        text: qsTr("Continue Anyway (Unsafe)")
                        icon.name: "go-next"
                        onTriggered: root.tab.acceptCertificateError()
                    }
                ]
            }
        }
    }
}
