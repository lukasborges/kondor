.pragma library

function escaped(text) {
    return String(text ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
}
