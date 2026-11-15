import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Kondor
import "../../common"
import "../../common/html.js" as Html

ConfirmDialog {
    id: root

    property var currentTab: null
    property var tab: null
    property var login: null

    function ask(login) {
        root.tab = root.currentTab
        root.login = login
        open()
    }

    function fillAndFocusPage() {
        tab.passwords.fill(login.origin, login.username)
        tab.focusPage()
    }

    function focusPage() {
        if (tab)
            tab.focusPage()
    }

    title: qsTr("Fill Password from Another Site")
    //: %1 is the host the password was saved for, %2 the host of the current page
    message: !login ? "" : qsTr("This password was saved for <b>%1</b>. Fill it on <b>%2</b>?")
        .arg(Html.escaped(login.host)).arg(Html.escaped(tab.passwords.host))
    acceptText: qsTr("Fill")
    acceptIcon: "dialog-password"
    destructive: false
    onAccepted: fillAndFocusPage()
    onRejected: focusPage()
    onCurrentTabChanged: {
        if (opened && currentTab !== tab)
            close()
    }
}
