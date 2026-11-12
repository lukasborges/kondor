import QtQuick
import QtWebEngine
import Kondor

// Shared wording and Breeze icon names for every site permission type, used by
// the request bar and by the Site Permissions dialog.
QtObject {
    function iconFor(permissionType) {
        switch (permissionType) {
        case WebEnginePermission.PermissionType.MediaAudioCapture:
            return "audio-input-microphone"
        case WebEnginePermission.PermissionType.MediaVideoCapture:
            return "camera-web"
        case WebEnginePermission.PermissionType.MediaAudioVideoCapture:
            return "camera-web"
        case WebEnginePermission.PermissionType.DesktopVideoCapture:
            return "video-display"
        case WebEnginePermission.PermissionType.DesktopAudioVideoCapture:
            return "video-display"
        case WebEnginePermission.PermissionType.MouseLock:
            return "input-mouse"
        case WebEnginePermission.PermissionType.Notifications:
            return "preferences-desktop-notification"
        case WebEnginePermission.PermissionType.Geolocation:
            return "mark-location"
        case WebEnginePermission.PermissionType.ClipboardReadWrite:
            return "edit-paste"
        case WebEnginePermission.PermissionType.LocalFontsAccess:
            return "preferences-desktop-font"
        }
        return "security-high"
    }

    function labelFor(permissionType) {
        switch (permissionType) {
        case WebEnginePermission.PermissionType.MediaAudioCapture:
            return qsTr("Microphone")
        case WebEnginePermission.PermissionType.MediaVideoCapture:
            return qsTr("Camera")
        case WebEnginePermission.PermissionType.MediaAudioVideoCapture:
            return qsTr("Camera and Microphone")
        case WebEnginePermission.PermissionType.DesktopVideoCapture:
            return qsTr("Screen")
        case WebEnginePermission.PermissionType.DesktopAudioVideoCapture:
            return qsTr("Screen and Microphone")
        case WebEnginePermission.PermissionType.MouseLock:
            return qsTr("Pointer Lock")
        case WebEnginePermission.PermissionType.Notifications:
            return qsTr("Notifications")
        case WebEnginePermission.PermissionType.Geolocation:
            return qsTr("Location")
        case WebEnginePermission.PermissionType.ClipboardReadWrite:
            return qsTr("Clipboard")
        case WebEnginePermission.PermissionType.LocalFontsAccess:
            return qsTr("Local Fonts")
        }
        return qsTr("Permission")
    }

    function sentenceFor(permissionType, host) {
        switch (permissionType) {
        case WebEnginePermission.PermissionType.MediaAudioCapture:
            return qsTr("<b>%1</b> wants to use your <b>microphone</b>.").arg(host)
        case WebEnginePermission.PermissionType.MediaVideoCapture:
            return qsTr("<b>%1</b> wants to use your <b>camera</b>.").arg(host)
        case WebEnginePermission.PermissionType.MediaAudioVideoCapture:
            return qsTr("<b>%1</b> wants to use your <b>camera</b> and <b>microphone</b>.").arg(host)
        case WebEnginePermission.PermissionType.DesktopVideoCapture:
            return qsTr("<b>%1</b> wants to share your <b>screen</b>.").arg(host)
        case WebEnginePermission.PermissionType.DesktopAudioVideoCapture:
            return qsTr("<b>%1</b> wants to share your <b>screen</b> and <b>microphone</b>.").arg(host)
        case WebEnginePermission.PermissionType.MouseLock:
            return qsTr("<b>%1</b> wants to lock your <b>pointer</b>.").arg(host)
        case WebEnginePermission.PermissionType.Notifications:
            return qsTr("<b>%1</b> wants to show you <b>notifications</b>.").arg(host)
        case WebEnginePermission.PermissionType.Geolocation:
            return qsTr("<b>%1</b> wants to know your <b>location</b>.").arg(host)
        case WebEnginePermission.PermissionType.ClipboardReadWrite:
            return qsTr("<b>%1</b> wants to read your <b>clipboard</b>.").arg(host)
        case WebEnginePermission.PermissionType.LocalFontsAccess:
            return qsTr("<b>%1</b> wants to use your <b>local fonts</b>.").arg(host)
        }
        return qsTr("<b>%1</b> is requesting a <b>permission</b>.").arg(host)
    }

    // "https://meet.jit.si/room" -> "meet.jit.si"
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
