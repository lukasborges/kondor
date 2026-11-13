import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

Popup {
    id: root

    required property var tab

    property var extensions: []
    property string currentId: ""
    property string requestedId: ""

    readonly property bool hasWebOrigin: tab && ExtensionManager.originOf(tab.url) !== ""
    readonly property string host: hasWebOrigin ? tab.url.toString().replace(/^https?:\/\/([^/:?#]+).*$/, "$1") : ""
    readonly property var currentExtension: extensions.find(function(extension) { return extension.id === currentId })
                                            ?? ({ id: "", name: "", iconSource: "", siteToggle: false, items: [] })

    signal manageRequested()
    signal settingsRequested(string extensionId)

    function openAt(extensionId) {
        requestedId = extensionId
        open()
    }

    function hasExtension(extensionId) {
        return extensions.some(function(extension) { return extension.id === extensionId })
    }

    function rebuild() {
        extensions = tab ? ExtensionManager.actionExtensions(tab.isPrivate) : []
        if (extensions.length === 0)
            close()
        else if (currentId !== "" && !hasExtension(currentId))
            showList("")
    }

    function showList(focusedId) {
        currentId = ""
        list.focusExtension(focusedId)
    }

    function showActions(extensionId) {
        currentId = extensionId
        actions.focusFirstAction()
    }

    function closeAndFocusPage() {
        close()
        if (tab)
            tab.focusPage()
    }

    function closeAndRequest(requestSignal, extensionId) {
        close()
        requestSignal(extensionId)
    }

    x: parent ? parent.width - width : 0
    y: parent ? parent.height : 0
    width: 380
    padding: Kirigami.Units.largeSpacing
    modal: false
    focus: true
    closePolicy: Popup.CloseOnPressOutsideParent
    onTabChanged: close()
    onAboutToShow: {
        rebuild()
        currentId = hasExtension(requestedId) ? requestedId : ""
        requestedId = ""
    }
    onOpened: currentId === "" ? list.focusRow(0) : actions.focusFirstAction()

    Connections {
        target: ExtensionManager
        function onRevisionChanged() { if (root.opened) root.rebuild() }
    }

    Connections {
        target: Settings
        function onPinnedExtensionsChanged() { if (root.opened) root.rebuild() }
    }

    contentItem: ColumnLayout {
        spacing: Kirigami.Units.smallSpacing
        Keys.onEscapePressed: root.closeAndFocusPage()

        ExtensionList {
            id: list
            visible: root.currentId === ""
            extensions: root.extensions
            tab: root.tab
            host: root.host
            onExtensionChosen: function(extensionId) { root.showActions(extensionId) }
            onManageRequested: root.closeAndRequest(root.manageRequested)
        }

        ExtensionActions {
            id: actions
            visible: root.currentId !== ""
            extension: root.currentExtension
            tab: root.tab
            host: root.host
            onBackRequested: root.showList(root.currentId)
            onSettingsRequested: function(extensionId) { root.closeAndRequest(root.settingsRequested, extensionId) }
        }
    }
}
