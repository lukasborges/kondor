// #102 Settings → Passwords when the filter matches nothing.
import QtQuick
import "common"

SettingsDialogMock { withPasswords: true; page: 4; innerTab: 0; passwordsEmpty: true; passwordsFilter: "df" }
