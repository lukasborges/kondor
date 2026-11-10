// #21 Password manager — Settings, Passwords page when KWallet is disabled or denied.
import QtQuick
import "common"

SettingsDialogMock { withPasswords: true; page: 4; innerTab: 0; walletDenied: true }
