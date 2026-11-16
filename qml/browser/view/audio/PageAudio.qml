import QtQuick
import QtWebEngine
import Kondor

Item {
    id: root

    required property Tab tab
    required property WebEngineView webView

    visible: false

    Connections {
        target: root.tab.audio
        function onMutedToggleRequested() { root.webView.audioMuted = !root.webView.audioMuted }
    }

    Connections {
        target: root.webView
        function onRecentlyAudibleChanged() { root.tab.audio.setAudible(root.webView.recentlyAudible) }
        function onAudioMutedChanged() { root.tab.audio.setMuted(root.webView.audioMuted) }
    }

    Component.onCompleted: webView.audioMuted = tab.audio.isMuted
}
