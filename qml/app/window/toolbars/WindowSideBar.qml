import QtQuick
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import Kondor

SlidingPane {
    id: root

    required property TabModel tabModel
    required property var targetWindow
    required property bool areToolbarsHidden
    required property bool isRevealed

    signal newTabRequested

    z: 1
    edge: Qt.LeftEdge
    isShown: !areToolbarsHidden || isRevealed
    takesSpace: !areToolbarsHidden
    contentSize: sideBarLayout.implicitWidth
    Layout.fillHeight: true
    Layout.preferredWidth: takesSpace ? contentSize : 0

    RowLayout {
        id: sideBarLayout
        height: parent.height
        spacing: 0

        TabSideBar {
            tabModel: root.tabModel
            targetWindow: root.targetWindow
            Layout.fillHeight: true
            Layout.preferredWidth: implicitWidth
            onNewTabRequested: root.newTabRequested()
        }

        Kirigami.Separator { Layout.fillHeight: true }
    }
}
