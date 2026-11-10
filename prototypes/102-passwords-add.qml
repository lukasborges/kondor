// #102 Add a password by hand — the "Add Password" dialog over Settings → Passwords.
import QtQuick
import "common"

SettingsDialogMock { withPasswords: true; page: 4; innerTab: 0; passwordsEmpty: false; addPasswordDialog: true }
