pragma Singleton
import QtQuick

QtObject {
    property int revision: 0
    function hasActionExtensions(isPrivate) { return true }
    function actionExtensions(isPrivate) { return [] }
    function originOf(url) { return "" }
}
