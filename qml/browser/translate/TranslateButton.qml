import QtQuick
import QtQuick.Controls
import Kondor

ToolButton {
    id: root

    required property TabModel tabs
    required property Item addressField

    readonly property TabTranslation translation: tabs.currentTab ? tabs.currentTab.translation : null

    function togglePanel() {
        const panel = panelLoader.item
        if (panel)
            panel.opened ? panel.close() : panel.open()
    }

    function closePanel() {
        if (panelLoader.item)
            panelLoader.item.close()
    }

    visible: translation !== null && translation.isAvailable
    display: AbstractButton.IconOnly
    focusPolicy: Qt.TabFocus
    icon.name: "translate"
    icon.width: 16
    icon.height: 16
    flat: true
    checked: translation !== null && translation.state === "translated"
    implicitWidth: 28
    implicitHeight: 28
    ToolTip.visible: hovered
    ToolTip.text: qsTr("Translate Page")
    ToolTip.delay: 600
    Accessible.name: ToolTip.text
    onClicked: togglePanel()
    onVisibleChanged: if (!visible) closePanel()

    Loader {
        id: panelLoader
        active: root.translation !== null
        sourceComponent: TranslatePanel {
            translation: root.translation
            x: root.width - width
            y: root.height + (root.addressField.height - root.height) / 2
            onManageRequested: manageDialog.open()
        }
    }

    ManageLanguagesDialog { id: manageDialog }
}
