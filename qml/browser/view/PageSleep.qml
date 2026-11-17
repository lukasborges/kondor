import QtQuick
import QtWebEngine
import Kondor

Item {
    id: root

    required property Tab tab
    required property WebEngineView webView

    visible: false

    readonly property string editedFieldsScript:
        "(function() {"
        + "for (const field of document.querySelectorAll('input, textarea, select')) {"
        + "if (field.type === 'hidden') continue;"
        + "if (field.tagName === 'SELECT') {"
        + "for (const o of field.options) if (o.selected !== o.defaultSelected) return true;"
        + "} else if (field.type === 'checkbox' || field.type === 'radio') {"
        + "if (field.checked !== field.defaultChecked) return true;"
        + "} else if (field.value !== field.defaultValue) return true;"
        + "} return false; })()"

    function isDiscarded() {
        return webView.lifecycleState === WebEngineView.LifecycleState.Discarded
    }

    function discardIfHidden() {
        if (!webView.visible)
            webView.lifecycleState = WebEngineView.LifecycleState.Discarded
    }

    function discardUnlessEdited(hasEditedFields) {
        if (!hasEditedFields)
            discardIfHidden()
    }

    function sleepWhenIdle() {
        if (webView.visible || webView.recommendedState === WebEngineView.LifecycleState.Active)
            return
        webView.runJavaScript(editedFieldsScript, WebEngineScript.ApplicationWorld,
                              function(hasEditedFields) { root.discardUnlessEdited(hasEditedFields) })
    }

    function updateSleepingIcon() {
        if (isDiscarded())
            FaviconStore.markSleeping(webView, webView.icon)
        else
            FaviconStore.markAwake(webView)
    }

    function wakeUp() {
        if (webView.lifecycleState !== WebEngineView.LifecycleState.Active)
            webView.lifecycleState = WebEngineView.LifecycleState.Active
    }

    Connections {
        target: root.tab.sleep
        function onSleepRequested() { root.discardIfHidden() }
        function onIdleSleepRequested() { root.sleepWhenIdle() }
    }

    Connections {
        target: root.webView
        function onLifecycleStateChanged() {
            root.tab.sleep.setSleeping(root.isDiscarded())
            root.updateSleepingIcon()
        }
        function onVisibleChanged() { if (root.webView.visible) root.wakeUp() }
    }

    Component.onDestruction: FaviconStore.markAwake(webView)
}
