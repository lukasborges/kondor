// #419 Restart Now: after remote control is turned on or off (or its port changes) and applied,
// the restart message offers Restart Now; Kondor saves the session, quits and starts again with
// every window and tab back.
import QtQuick
import "common"

SettingsDialogMock { page: 3; withRemoteControl: true; withMcpCommand: true; withRestartNow: true }
