import QtQuick

QtObject {
    function fromUrl(url) {
        const path = url.toString()
        return decodeURIComponent(path.startsWith("file://") ? path.slice(7) : path)
    }
}
