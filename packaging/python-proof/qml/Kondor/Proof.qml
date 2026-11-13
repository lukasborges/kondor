import QtQuick
import QtQuick.Controls as QQC2
import QtWebEngine
import org.kde.kirigami as Kirigami
import Kondor

Window {
    id: root

    readonly property string pageUrl: "data:text/html,%3Cimg%20src%3D%22http%3A%2F%2Fproof.invalid%2Fpixel.png%22%3E"

    width: 400
    height: 300
    visible: true

    function reportLoad(request) {
        if (request.status === WebEngineView.LoadSucceededStatus)
            ProofState.report("webengine", true, "")
        else if (request.status === WebEngineView.LoadFailedStatus)
            ProofState.report("webengine", false, request.errorString)
    }

    QQC2.Button {
        id: probe
        text: "Breeze"
    }

    WebEngineView {
        anchors.fill: parent
        profile: ProofState.profile
        url: root.pageUrl
        onLoadingChanged: function (request) {
            root.reportLoad(request)
        }
    }

    Component.onCompleted: {
        const hasColor = Kirigami.Theme.backgroundColor.a > 0
        ProofState.report("style", probe.implicitWidth > 0 && hasColor, "button width or theme color missing")
        ProofState.report("module", true, "")
    }
}
