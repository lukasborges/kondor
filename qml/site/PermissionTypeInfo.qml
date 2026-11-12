import QtQuick
import QtWebEngine
import Kondor

QtObject {
    id: root

    readonly property var types: {
        const type = WebEnginePermission.PermissionType
        return {
            [type.MediaAudioCapture]: {
                icon: "audio-input-microphone",
                label: qsTr("Microphone"),
                sentence: qsTr("<b>%1</b> wants to use your <b>microphone</b>.")
            },
            [type.MediaVideoCapture]: {
                icon: "camera-web",
                label: qsTr("Camera"),
                sentence: qsTr("<b>%1</b> wants to use your <b>camera</b>.")
            },
            [type.MediaAudioVideoCapture]: {
                icon: "camera-web",
                label: qsTr("Camera and Microphone"),
                sentence: qsTr("<b>%1</b> wants to use your <b>camera</b> and <b>microphone</b>.")
            },
            [type.DesktopVideoCapture]: {
                icon: "video-display",
                label: qsTr("Screen"),
                sentence: qsTr("<b>%1</b> wants to share your <b>screen</b>.")
            },
            [type.DesktopAudioVideoCapture]: {
                icon: "video-display",
                label: qsTr("Screen and Microphone"),
                sentence: qsTr("<b>%1</b> wants to share your <b>screen</b> and <b>microphone</b>.")
            },
            [type.MouseLock]: {
                icon: "input-mouse",
                label: qsTr("Pointer Lock"),
                sentence: qsTr("<b>%1</b> wants to lock your <b>pointer</b>.")
            },
            [type.Notifications]: {
                icon: "preferences-desktop-notification",
                label: qsTr("Notifications"),
                sentence: qsTr("<b>%1</b> wants to show you <b>notifications</b>.")
            },
            [type.Geolocation]: {
                icon: "mark-location",
                label: qsTr("Location"),
                sentence: qsTr("<b>%1</b> wants to know your <b>location</b>.")
            },
            [type.ClipboardReadWrite]: {
                icon: "edit-paste",
                label: qsTr("Clipboard"),
                sentence: qsTr("<b>%1</b> wants to read your <b>clipboard</b>.")
            },
            [type.LocalFontsAccess]: {
                icon: "preferences-desktop-font",
                label: qsTr("Local Fonts"),
                sentence: qsTr("<b>%1</b> wants to use your <b>local fonts</b>.")
            }
        }
    }

    readonly property var unknownType: ({
        icon: "security-high",
        label: qsTr("Permission"),
        sentence: qsTr("<b>%1</b> is requesting a <b>permission</b>.")
    })

    function infoFor(permissionType) {
        return types[permissionType] ?? unknownType
    }

    function iconFor(permissionType) {
        return infoFor(permissionType).icon
    }

    function labelFor(permissionType) {
        return infoFor(permissionType).label
    }

    function sentenceFor(permissionType, host) {
        return infoFor(permissionType).sentence.arg(host)
    }

    function hostFor(origin) {
        if (!origin)
            return ""
        const text = origin.toString()
        const schemeEnd = text.indexOf("://")
        const withoutScheme = schemeEnd >= 0 ? text.slice(schemeEnd + 3) : text
        const slash = withoutScheme.indexOf("/")
        return slash >= 0 ? withoutScheme.slice(0, slash) : withoutScheme
    }
}
