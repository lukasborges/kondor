// #183 Extensions panel — level 1 with ten extensions: one row each, "Off on this site" only when off, drill-down.
import QtQuick
import QtQuick.Controls
import "common"

BrowserFrame {
    id: frame
    address: "https://www.youtube.com/watch?v=example"
    toolbarExtras: [
        ToolButton { display: AbstractButton.IconOnly; icon.name: "media-playback-start" },
        ToolButton { display: AbstractButton.IconOnly; icon.name: "plugins"; checked: true }
    ]
    FakePage {}
    ExtensionsPanelMock {
        x: frame.width - width - 44
        y: -6
        extensions: [
            { name: "Clean Links", icon: "edit-link", siteToggle: true, on: true, pinned: false },
            { name: "Cookie Banner Blocker", icon: "preferences-web-browser-cookies", siteToggle: true, on: true, pinned: false },
            { name: "Dark Mode", icon: "weather-clear-night", siteToggle: true, on: false, pinned: false },
            { name: "JSON Viewer", icon: "application-json", siteToggle: false, on: false, pinned: false },
            { name: "Mouse Gestures", icon: "input-mouse", siteToggle: true, on: true, pinned: false },
            { name: "Skip Sponsors", icon: "media-skip-forward", siteToggle: true, on: true, pinned: false },
            { name: "User Scripts", icon: "text-x-script", siteToggle: false, on: false, pinned: false },
            { name: "User Styles", icon: "preferences-desktop-color", siteToggle: false, on: false, pinned: false },
            { name: "Video Speed Controller", icon: "media-playback-start", siteToggle: true, on: true, pinned: true },
            { name: "YouTube Dislike Counts", icon: "rating", siteToggle: true, on: true, pinned: false }
        ]
    }
}
