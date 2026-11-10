// #102 Settings → Passwords with no saved passwords (placeholder with an Add action).
import QtQuick
import "common"

SettingsDialogMock { withPasswords: true; page: 4; innerTab: 0; passwordsEmpty: true }
