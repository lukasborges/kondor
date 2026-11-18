import QtQuick
import Kondor

Item {
    id: root

    required property Tab tab
    required property TabModel tabModel

    NewTabPage {
        anchors.fill: parent
        visible: root.tab.newTabPage
        tab: root.tab
        tabModel: root.tabModel
    }

    CertificateErrorPage {
        anchors.fill: parent
        visible: root.tab.security.certificateErrorPending
        tab: root.tab
    }
}
