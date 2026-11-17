import QtQuick
import QtQuick.Controls
import QtWebEngine
import org.kde.kirigami as Kirigami
import Kondor

Popup {
    id: root

    required property Tab tab
    required property WebEngineView webView

    readonly property var suggestion: tab.passwords.suggestion
    readonly property rect fieldBox: Qt.rect(
        suggestion.fieldRect.x * webView.zoomFactor, suggestion.fieldRect.y * webView.zoomFactor,
        suggestion.fieldRect.width * webView.zoomFactor, suggestion.fieldRect.height * webView.zoomFactor)
    readonly property real belowY: fieldBox.y + fieldBox.height + Kirigami.Units.smallSpacing
    readonly property real aboveY: fieldBox.y - height - Kirigami.Units.smallSpacing
    readonly property bool fitsBelow: belowY + height <= webView.height

    parent: webView
    x: fieldBox.x
    y: fitsBelow ? belowY : aboveY
    width: Math.max(fieldBox.width, Kirigami.Units.gridUnit * 12)
    padding: Kirigami.Units.smallSpacing
    focus: false
    closePolicy: Popup.CloseOnPressOutside
    visible: suggestion.isOffered && webView.visible
    onClosed: {
        if (webView.visible)
            suggestion.dismiss()
    }

    Connections {
        target: root.suggestion
        function onGeneratedPasswordSaved() { Accessible.announce(qsTr("Password saved")) }
    }

    contentItem: ItemDelegate {
        focusPolicy: Qt.NoFocus
        highlighted: hovered
        text: qsTr("Use Suggested Password")
        icon.name: "password-generate"
        ToolTip.visible: hovered
        ToolTip.delay: 600
        ToolTip.text: qsTr("Fill in a strong password and save it in KWallet when the form is sent")
        Accessible.name: text
        Accessible.description: ToolTip.text
        onClicked: root.suggestion.generate()
    }
}
