import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Rectangle {
    id: root

    required property SettingsPages catalog
    property int currentPage: 0
    property bool syncingPageList: false
    readonly property var visiblePages: catalog.matching(searchField.text)

    signal pageRequested(int page)

    Layout.preferredWidth: Kirigami.Units.gridUnit * 8
    Layout.fillHeight: true
    Kirigami.Theme.colorSet: Kirigami.Theme.View
    Kirigami.Theme.inherit: false
    color: Kirigami.Theme.backgroundColor

    onCurrentPageChanged: root.ensureVisiblePage()
    onVisiblePagesChanged: {
        root.syncingPageList = true
        root.ensureVisiblePage()
        Qt.callLater(root.finishPageListSync)
    }

    function focusSearch() {
        searchField.forceActiveFocus()
    }

    function focusPageList() {
        pageList.forceActiveFocus()
    }

    function clearSearch() {
        searchField.text = ""
    }

    function finishPageListSync() {
        root.syncingPageList = false
        root.ensureVisiblePage()
    }

    function ensureVisiblePage() {
        if (root.visiblePages.length === 0)
            return
        if (!root.visiblePages.includes(root.currentPage))
            root.pageRequested(root.visiblePages[0])
        pageList.currentIndex = Math.max(0, root.visiblePages.indexOf(root.currentPage))
    }

    function requestListPage(index) {
        const page = root.visiblePages[index]
        if (page !== undefined && page !== root.currentPage)
            root.pageRequested(page)
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Kirigami.Units.smallSpacing
        spacing: Kirigami.Units.smallSpacing

        Kirigami.SearchField {
            id: searchField
            Layout.fillWidth: true
            placeholderText: qsTr("Search…")
        }

        ListView {
            id: pageList
            objectName: "pageList"
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            focus: true
            keyNavigationEnabled: true
            model: root.visiblePages

            delegate: ItemDelegate {
                required property int modelData
                required property int index
                width: ListView.view.width
                highlighted: modelData === root.currentPage
                display: AbstractButton.TextUnderIcon
                icon.name: root.catalog.pages[modelData].icon
                icon.width: Kirigami.Units.iconSizes.medium
                icon.height: Kirigami.Units.iconSizes.medium
                text: root.catalog.pages[modelData].title
                onClicked: root.pageRequested(modelData)
            }

            onCurrentIndexChanged: {
                if (!root.syncingPageList)
                    root.requestListPage(currentIndex)
            }
        }
    }
}
