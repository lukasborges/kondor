import QtQuick
import QtWebChannel
import QtWebEngine
import Kondor

Item {
    id: root

    required property Tab tab
    required property WebEngineView webView

    readonly property WebChannel channel: pageChannel

    visible: false

    function callExtensionScript(global, id, argumentsSource) {
        webView.runJavaScript(
            "window." + global + " && window." + global + "[" + JSON.stringify(id) + "] && window."
            + global + "[" + JSON.stringify(id) + "](" + argumentsSource + ");",
            WebEngineScript.ApplicationWorld)
    }

    PasswordBridge {
        id: passwordBridge
        tab: root.tab
    }

    ExtensionBridge {
        id: extensionBridge
        tab: root.tab
    }

    WebChannel {
        id: pageChannel
        Component.onCompleted: {
            registerObject("kondorExtensions", extensionBridge.pageApi())
            if (!root.tab.isPrivate)
                registerObject("kondorPasswords", passwordBridge.pageApi())
        }
    }

    Connections {
        target: ExtensionManager
        function onSettingsChanged(id) {
            root.callExtensionScript("__kondorExtensions", id,
                                     JSON.stringify(ExtensionManager.settingValues(id)))
        }
    }

    Connections {
        target: root.tab.passwords
        function onFillRequested(username) { passwordBridge.fill(username) }
    }

    Connections {
        target: root.tab.extensionItems
        function onTriggered(extensionId, itemId, checked) {
            root.callExtensionScript("__kondorExtensionActions", extensionId,
                                     JSON.stringify(itemId) + ", " + (checked ? "true" : "false"))
        }
    }
}
