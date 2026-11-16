# Multiple profiles: separate identities with their own data (#349)

> <https://github.com/lukasborges/kondor/issues/349> · priority: medium · area: privacy & security ·
> written ahead of promotion; Python app only (the C++ app is gone since #174).

## Objective

Let people keep separate browsing identities, for example "Personal" and "Work". Each profile has
its own cookies and sign-ins, history, bookmarks, favicons, saved passwords, extensions, session,
per-site zoom and settings. A window belongs to one profile, and its toolbar and title show which
one. People open, create, edit and delete profiles from the main menu, choose the profile used at
startup (or be asked every time), and start one with `kondor --profile <name>`. The current data
becomes the "Default" profile in place: nothing moves and nothing is lost.

## Context

Every store is a process-wide singleton (`Database`, `Settings`, `HistoryManager`,
`BookmarkManager`, `PasswordStore`, `ExtensionManager`, `SessionManager`, `ZoomManager`,
`ProfileManager`…), and each one finds its file on its own:

| What | Where today | File |
| --- | --- | --- |
| SQLite (history, bookmarks, favicons, extension storage) | `AppDataLocation/kondor.sqlite` | `src/kondor/core/database/database.py` (`database_path()`) |
| Session | `AppDataLocation/session.json` | `src/kondor/browser/session/sessionmanager.py` (`session_file_path()`) |
| Installed extensions | `AppDataLocation/extensions` | `src/kondor/extensions/manager/extensionrows.py` (`extensions_directory()`) |
| Settings | `QSettings("KDE", "Kondor")` → `~/.config/KDE/Kondor.conf` | `src/kondor/core/settings/settings.py` |
| Per-site zoom | same `QSettings` | `src/kondor/browser/zoommanager.py` |
| Extension state | same `QSettings` | `src/kondor/extensions/state/extensionstate.py` |
| Web profile (cookies, cache, permissions) | storage name `kondor` → `AppDataLocation/QtWebEngine/kondor`, `CacheLocation/QtWebEngine/kondor` | `src/kondor/browser/profile/profilemanager.py` (`STORAGE_NAME`) |
| Saved passwords | KWallet folder `Kondor` | `src/kondor/passwords/wallet/walletfolder.py` (`FOLDER`) |
| Single instance socket | `kondor-<sha1(AppDataLocation)[:16]>.socket` | `src/kondor/app/instance/singleinstance.py` (`profile_hash()`) |

Shared on purpose (not personal data): the ad-block filter list cache
(`src/kondor/adblock/lists/filterlists.py`), the extension catalog cache
(`src/kondor/extensions/catalog/extensioncatalog.py`) and the QML position cache
(`src/kondor/app/startup/positioncache.py`).

Startup: `src/kondor/__main__.py` → `launch()` builds `SingleInstance()`, forwards the command line
to a running instance or calls `start_browser()` and `open_windows()`
(`src/kondor/app/startup/appstartup.py`). The command line is parsed in
`src/kondor/app/commandline/commandline.py`. The packaged launcher is
`packaging/kondor` (`exec python3 -P -m kondor "$@"` with `PYTHONPATH` exported).

UI: `qml/app/menu/MainMenu.qml` (main menu), `qml/app/NavigationToolBar.qml` (toolbar, the main
menu button at the end), `qml/app/window/WindowTitle.qml` (window title parts).

KRunner (#258) already plans for a second instance: it finds its bus name taken and leaves
KRunner to the first one. MPRIS (#259) uses one name per process.

## Design / behavior

### 1. One process per profile

Each profile runs in its own Kondor process. The process picks its profile once, at startup,
before any store singleton is built, and keeps it until it quits. All singletons stay as they
are; they only ask the active profile where their data lives. Opening a window of another profile
starts (or reuses, through that profile's single-instance socket) that profile's process.

### 2. Profile registry

The list of profiles is global, in `QSettings("KDE", "KondorProfiles")`
(`~/.config/KDE/KondorProfiles.conf`):

| Key | Value |
| --- | --- |
| `Profiles/Order` | list of ids, in display order (Default first, then creation order) |
| `Profiles/<id>/Name` | display name |
| `Profiles/<id>/Icon` | Breeze icon name, one of the eight below |
| `Startup/Profile` | id of the profile used at startup, or `ask` |
| `Startup/LastUsed` | id of the profile that last started a process |

- The Default profile has the id `default`. With no registry file (every existing install), the
  registry holds only Default, named `qsTr("Default")` and with the icon `im-user`, and
  `Startup/Profile` is `default`. Nothing is written until the user changes something.
- A new profile gets the id `QUuid.createUuid().toString(QUuid.StringFormat.Id128)[:8]`; the id
  never changes, renaming only changes `Name`.
- Names are trimmed, not empty, at most 64 characters, and unique without regard to case.
- Icons: `im-user`, `go-home`, `view-pim-tasks`, `globe`, `favorite`, `games-config-board`,
  `code-context`, `flag` (tooltips and accessible names: "Person", "Home", "Work", "World",
  "Star", "Games", "Development", "Flag").
- Every process watches the registry file (`QFileSystemWatcher`, re-added after each change since
  `QSettings` replaces the file) and reloads it, so the menus of every open profile follow a
  rename, a new profile or a deletion made in another process.

### 3. Where each profile keeps its data

`ActiveProfile` (section 7) answers these for the selected profile:

| What | Default | Other profile `<id>` |
| --- | --- | --- |
| data directory | `AppDataLocation` (unchanged) | `AppDataLocation/profiles/<id>` |
| settings | `QSettings("KDE", "Kondor")` (unchanged) | `QSettings("KDE", "Kondor-<id>")` → `~/.config/KDE/Kondor-<id>.conf` |
| web storage name | `kondor` (unchanged) | `kondor-<id>` |
| KWallet folder | `Kondor` (unchanged) | `Kondor-<id>` |
| single-instance socket | hash of `AppDataLocation` (unchanged) | hash of `AppDataLocation/profiles/<id>` |

The database, session file and extensions directory move under the data directory; settings,
zoom and extension state use the profile's settings. A new profile starts with default settings,
the default bookmarks (migration 4 seeds them), no history, no extensions and no saved passwords.

### 4. Choosing the profile at startup

New option `--profile <name>` in `commandline.py` (help: "open a window of the profile with this
name"), stored in `CommandLine.profile: str | None`. Order, in a new
`src/kondor/app/startup/profilechoice.py`, before `SingleInstance` is built:

1. `--profile` given: match an id, or a name without regard to case. No match: print
   `Kondor: no profile named "<name>"` to stderr and exit with status 1.
2. Only one profile: use it.
3. `Startup/Profile` is an id: use it (an id that no longer exists counts as `default`).
4. `Startup/Profile` is `ask` and the command line has URLs (a link opened from another app):
   use `Startup/LastUsed` without asking.
5. `Startup/Profile` is `ask`: show the **Choose a Profile** window (section 6.5). Picking a
   profile starts `kondor --profile <id>` (section 5) with the rest of the command line, and this
   process quits without touching any profile data. Quit or closing the window exits with status 0.

Then `ActiveProfile.select(id)`, `SingleInstance()` (socket of that profile), and the usual
forwarding or start. A process that starts as the first instance of its profile writes
`Startup/LastUsed`. `--new-instance`, `--private`, `--new-window` and `--remote-control` keep
their meaning inside the chosen profile.

### 5. Opening a window of a profile

`UserProfiles.openWindow(id)`:

- `id` is the active profile: `WindowManager.instance().newWindow()`.
- Otherwise, when that profile's socket answers (`SingleInstance(server_name_for(id))`), send it
  `SingleInstanceMessage(new_window=True)` with the activation token, so it opens and raises a
  window.
- Otherwise start it with `QProcess.startDetached(sys.executable, ["-P", "-m", "kondor",
  "--profile", id])`, keeping the environment (`PYTHONPATH` from `packaging/kondor`, the staged
  build directory, Flatpak and AppImage variables). One function, `profile_launch_command(id)`,
  builds the program and arguments, and the chooser (section 4.5) uses it too.

### 6. UI (prototypes `349*`)

Every string in `qsTr()`; the windows use `Kirigami.Theme` colors and `Kirigami.Units` spacing.

1. **Main menu → Profiles** (`349-profiles-menu.png`): a submenu "Profiles" (icon `im-user`)
   right after "New Private Window", always shown. It lists every profile in registry order
   (icon + name, no check marks: a row opens a window, it does not switch this one), a
   separator, **New Profile…** (`list-add`) and **Manage Profiles…** (`configure`). The menu uses
   `MenuKeyNavigation` like the other submenus.
2. **Profile button** (`349e-profile-button.png`): a `ToolButton` right before the main menu
   button, `display: AbstractButton.TextBesideIcon`, with the active profile's icon and name,
   `ToolTip.text: qsTr("Profile: %1")`, `ToolTip.delay: 600`, the same words in
   `Accessible.name`. Shown only when more than one profile exists. A click opens the same
   Profiles menu below the button (one shared component in `qml/profiles/`).
3. **Window title**: when more than one profile exists, `WindowTitle.qml` adds the profile name
   after the page title (and after "Private Browsing"): `Page — Work — Kondor Browser`,
   `Page — Private Browsing — Work — Kondor Browser`. With one profile the title does not change.
4. **Manage Profiles** window (`349b-manage-profiles.png`): a separate, non-modal window titled
   "Manage Profiles" (one per process; asking again raises it), 520 × 560 by default.
   - A framed list, one row per profile: icon (`smallMedium`), name (elided at the end), an
     **Edit** icon button (`document-edit`, tooltip "Edit", accessible name "Edit <name>") and a
     **Delete…** icon button (`edit-delete`, tooltip "Delete…", accessible name "Delete <name>").
     Delete is disabled for Default (tooltip "The Default profile cannot be deleted") and for a
     profile with a running process (tooltip "Close the windows of this profile first"), the
     active one included. Arrow keys move in the list; Enter edits the current row.
   - **New Profile…** (`list-add`) below the list.
   - `Kirigami.FormLayout` row "At startup:" with a `ComboBox`: "Ask Every Time" then every
     profile name; it writes `Startup/Profile` at once.
   - **Close** (`DialogButtonBox.Close`) and Esc close the window. Changes apply immediately.
5. **New Profile / Edit Profile** dialog (`349c-new-profile.png`): a modal QQC2 `Dialog` over the
   Manage Profiles window (or over the browser window when opened from the menu), titled
   "New Profile" or "Edit Profile". `Kirigami.FormLayout`: "Name:" `TextField` (focused, all text
   selected when editing), "Icon:" a row of eight checkable icon-only `ToolButton`s in one
   `ButtonGroup` (new profiles preselect the first icon not used yet, or `im-user`). Buttons:
   **Create** (`list-add`) or **Save** (`document-save`), and **Cancel**. The confirm button is
   disabled while the name is empty; a duplicate name shows a `Kirigami.InlineMessage` (Error)
   "A profile with this name already exists." under the form and disables it too. Enter
   confirms, Esc cancels. Creating a profile from the menu also opens a window of it; creating it
   from Manage Profiles only adds the row.
6. **Delete** confirmation: the shared `ConfirmDialog` (`qml/common/`), title
   `Delete Profile "%1"?`, text "History, bookmarks, saved passwords, cookies, extensions and
   settings of this profile are deleted for good.", buttons **Delete** (`edit-delete`,
   destructive) and **Cancel** (default focus). If "At startup" pointed to it, it falls back to
   Default; if `Startup/LastUsed` did, it becomes `default`.
7. **Choose a Profile** window (`349d-choose-profile.png`): titled "Choose a Profile", 380 × 340,
   a framed list of profiles (icon `smallMedium` + name), the current row on `Startup/LastUsed`,
   focused. A click on a row, or Enter, opens that profile (section 4.5); arrow keys move;
   **Quit** (`application-exit`) and Esc exit. It loads only the registry, never a profile's data.

### 7. Python API

New feature folder `src/kondor/profiles/` (and `qml/profiles/`, `tests/profiles/`):

| File | Holds |
| --- | --- |
| `userprofile.py` | `@dataclass(frozen=True) UserProfile(id: str, name: str, icon_name: str)`, `DEFAULT_ID = "default"`, `PROFILE_ICONS` |
| `profileregistry.py` | `ProfileRegistry`: `profiles() → list[UserProfile]`, `find(name_or_id) → UserProfile | None`, `add(name, icon) → UserProfile`, `update(profile)`, `remove(id)`, `name_error(name, except_id) → str` ("" when valid), `startup_profile_id() → str` (`"ask"` or an id), `set_startup_profile_id(value)`, `last_used_id()`, `set_last_used_id(id)` |
| `profilepaths.py` | pure functions of an id: `data_directory(id)`, `settings_application(id)` (`"Kondor"` / `"Kondor-<id>"`), `storage_name(id)`, `wallet_folder(id)`, `web_data_directories(id)` (data and cache `QtWebEngine/<storage>`) |
| `activeprofile.py` | `ActiveProfile` (class-level state): `select(id)`, `id()`, `data_directory()` (creates it), `settings() → QSettings`, `storage_name()`, `wallet_folder()`; before `select()` it answers for Default, so tests and tools keep working |
| `profilelauncher.py` | `profile_launch_command(id) → tuple[str, list[str]]`, `open_profile_window(id)` (section 5), `is_running(id) → bool` |
| `profileremoval.py` | `remove_profile_data(id) → bool`: deletes the data directory, the web data and cache directories, the settings file and the wallet folder |
| `userprofiles.py` | QML singleton `UserProfiles` (pattern of the other Python singletons): properties `profiles` (list of `{id, name, iconName}`, NOTIFY `profilesChanged`), `currentId`, `currentName`, `currentIconName`, `hasSeveralProfiles`, `startupProfileId` (READ/WRITE, `""` = ask); slots `openWindow(id)`, `createProfile(name, iconName) → str` (new id), `editProfile(id, name, iconName)`, `deleteProfile(id) → bool` (refuses Default and running profiles), `nameError(name, exceptId) → str`, `isRunning(id) → bool`, `iconNames() → list[str]` |
| `qmltypes.py` | registration, added to `register_all_types()` |

Call sites switch to `ActiveProfile`: `database_path()`, `session_file_path()`,
`extensions_directory()`, `Settings`, `ZoomManager`, `ExtensionState`,
`ProfileManager.create_persistent_profile()` (storage name), `WalletFolder` (folder name, passed
in instead of the `FOLDER` constant), `SingleInstance.server_name()` (gains
`server_name_for(profile_id)`). `WalletService` gains `remove_folder(handle, folder) → bool`
(KWallet `removeFolder`). Deleting the wallet folder opens the network wallet like the Passwords
page; if the wallet is unavailable or the user refuses, the folder stays, a `qWarning` is logged
and the rest of the deletion still happens.

QML: `qml/profiles/ProfilesMenu.qml` (the submenu, used by `MainMenu.qml` and the profile
button), `ProfileButton.qml`, `ManageProfilesWindow.qml`, `ProfileDialog.qml` (new and edit),
`ProfileChooserWindow.qml`, `ProfileIconPicker.qml`, plus the delete confirmation. The chooser
window is loaded by `profilechoice.py` with an engine that registers only `UserProfiles`.

### 8. Private windows

Unchanged: a private window opened from any profile uses its own off-the-record web profile and
writes nothing to disk. The Profiles menu and profile button are shown in private windows too (they
write nothing). Creating, editing or deleting a profile only touches the registry and the
profile's own folders, never data of the private window.

### 9. Edge cases

- Two processes of the same profile never run together: the per-profile socket forwards the second
  launch, as today.
- A profile deleted while the chooser or a menu lists it: `openWindow` of an unknown id does
  nothing and logs a `qWarning`.
- `--profile` with a name that is also another profile's id: the id wins.
- Remote control (#256) and `--load-extension` apply to the process they are given to, so to one
  profile.
- KRunner (#258), when present, answers from the first Kondor process only (its own spec).

## Acceptance criteria

- [ ] Without a registry file, Kondor starts on the existing data exactly as before: same
      `kondor.sqlite`, `session.json`, `extensions/`, `Kondor.conf`, web storage `kondor`, wallet
      folder `Kondor`, socket name. No file is written by this feature until the user acts.
- [ ] A new profile keeps its database, session and extensions under
      `AppDataLocation/profiles/<id>/`, its settings, zoom and extension state in
      `~/.config/KDE/Kondor-<id>.conf`, its web data under storage `kondor-<id>`, its passwords in
      wallet folder `Kondor-<id>`; nothing of it shows up in another profile.
- [ ] Main menu → Profiles lists the profiles, New Profile… and Manage Profiles…, as in
      `349-profiles-menu.png`; a row opens a window of that profile (a new window in this
      process, a forwarded new window, or a new process).
- [ ] The profile button and the profile name in the window title appear only with more than one
      profile (`349e-profile-button.png`).
- [ ] Manage Profiles, New/Edit Profile and Choose a Profile match `349b`, `349c` and `349d`,
      including keyboard use, disabled Delete with its tooltips, and the duplicate-name message.
- [ ] Deleting a profile asks for confirmation and then removes its data directory, web data and
      cache, settings file and (when the wallet opens) its wallet folder; Default and running
      profiles cannot be deleted.
- [ ] "At startup" decides the profile of a plain `kondor`; "Ask Every Time" shows the chooser,
      and a launch with URLs then goes to the last used profile without asking.
- [ ] `kondor --profile Work` opens Work (by name or id, any case); an unknown name prints the
      error and exits with status 1; `--help` lists the option.
- [ ] Menus of every running profile follow a rename, creation or deletion made in another one.
- [ ] Private windows still write nothing to disk, in any profile.
- [ ] Unit tests in `tests/profiles/` cover the registry (defaults, add, rename, unique names,
      remove, startup and last used), the paths of Default and of another profile, the startup
      choice rules of section 4 (without showing a window), the launch command and the data
      removal, plus `--profile` parsing in `tests/app/commandline/`.
- [ ] Python checks pass (`ruff check`, `mypy --strict kondor`, `python3 scripts/build.py`,
      `scripts/run-pytests.sh`, `python3 scripts/check-qml-api.py`),
      `python3 scripts/check-code-quality.py --changed origin/main` passes, and every `i18n/*.ts`
      has the new strings translated.
- [ ] `README.md`: one "Profiles" bullet in the matching Features group and `--profile` where the
      command line is described.

## Manual test

Use an isolated home for all of it (`XDG_CONFIG_HOME`, `XDG_DATA_HOME`, `XDG_CACHE_HOME` in a
temporary directory, as in `AGENTS.md`).

1. Start Kondor, visit two sites, add a bookmark. Quit. Check that only the usual files exist and
   no `KondorProfiles.conf` was written. Start again: history, bookmark and session are there.
2. Main menu → Profiles → New Profile…: name "Work", icon Work, Create. A new window opens; its
   title ends in "— Work — Kondor Browser" and the toolbar shows the Work button. Its history is
   empty, its bookmarks are the defaults, and you are signed out of a site you signed in to in
   Default. The Default window now shows its own profile button.
3. In Work, sign in to a site, change a setting (for example the home page) and zoom a site.
   Back in Default none of it shows. Quit both; `profiles/<id>/`, `Kondor-<id>.conf` and
   `QtWebEngine/kondor-<id>` exist.
4. `kondor --profile work`: Work opens. Run it again: a new window opens in the same process
   (one process per profile in `ps`). `kondor --profile nobody`: error message, status 1.
5. Manage Profiles: rename Work to "Office" with another icon; the open windows' button, title and
   menu follow. Set "At startup" to Ask Every Time, quit everything, start `kondor`: the chooser
   appears; pick Office. Quit, run `kondor https://kde.org`: it opens in Office without asking.
6. With Office running, its Delete button is disabled; Default's is always disabled. Quit Office,
   delete it, confirm: its folders, settings file and wallet folder are gone, and "At startup"
   is back on Default if it pointed to Office.
7. Open a private window from a non-default profile, browse, close it: nothing new on disk.
8. Keyboard only: open the Profiles menu, Manage Profiles, create and delete a profile with Tab,
   arrows, Enter and Esc.

## Out of scope

- Syncing profiles between machines.
- Importing from Firefox or Chrome profiles, and moving or copying data between profiles.
- A desktop file action per profile (`kondor.desktop` keeps its single "New Private Window"
  action).
- Several profiles in one process, or moving tabs or windows between profiles.
- Per-profile ad-block filter list downloads or extension catalog cache (shared caches).
- A password or lock on a profile.
- Changing the C++ code (deleted in #174).

## Dependencies

None open: it builds on the Python app (#174), single instance (#15), sessions (#6), passwords
(#21) and extensions (#107), all closed. **Depends on:** - (issue body).

## Prototype

- [`prototypes/349-profiles-menu.qml`](../../prototypes/349-profiles-menu.qml) →
  [`screenshots/349-profiles-menu.png`](../../prototypes/screenshots/349-profiles-menu.png)
  (`withProfiles` in `prototypes/common/MainMenuMock.qml`)
- [`prototypes/349b-manage-profiles.qml`](../../prototypes/349b-manage-profiles.qml) →
  [`screenshots/349b-manage-profiles.png`](../../prototypes/screenshots/349b-manage-profiles.png)
  (twelve profiles, a long name, the hover and current rows)
- [`prototypes/349c-new-profile.qml`](../../prototypes/349c-new-profile.qml) →
  [`screenshots/349c-new-profile.png`](../../prototypes/screenshots/349c-new-profile.png)
- [`prototypes/349d-choose-profile.qml`](../../prototypes/349d-choose-profile.qml) →
  [`screenshots/349d-choose-profile.png`](../../prototypes/screenshots/349d-choose-profile.png)
- [`prototypes/349e-profile-button.qml`](../../prototypes/349e-profile-button.qml) →
  [`screenshots/349e-profile-button.png`](../../prototypes/screenshots/349e-profile-button.png)

## Decisions

| Question | Decision |
| --- | --- |
| One process for all profiles, or one per profile? | **One process per profile.** Every store is a process-wide singleton; several profiles in one process would mean passing a profile to every store, model and QML singleton. A process per profile only changes where each store finds its files, and the per-profile single-instance socket keeps one process per profile. Firefox works the same way. |
| Where does the existing data go? | Nowhere: Default keeps today's paths, settings file, storage name, wallet folder and socket, so updating Kondor moves no file and cannot lose data. Only new profiles use `profiles/<id>/` and `Kondor-<id>.conf`. |
| Profile folders by name or by id? | By a random 8-character id, so renaming never moves files and any name (spaces, slashes, any script) is safe. |
| Which settings are global? | Only the registry (`KondorProfiles.conf`). Every option of the Settings window is per profile, as the issue asks. The filter list and catalog caches stay shared because they hold no personal data. |
| Check marks on the current profile in the Profiles menu? | Rejected (first prototype): check boxes read as a choice that switches this window, but a row opens a window of that profile. The profile button and the window title show the current profile. |
| Where are profiles managed: a Settings page or a window? | A separate "Manage Profiles" window. The Settings window edits the active profile's options and applies with OK/Apply; profiles are global and every action applies at once. A window (not a dialog) lets the New/Edit dialog open over it without a dialog-over-dialog. |
| Profile pictures or colors? | Eight monochrome Breeze action icons. They follow the color scheme and stay legible at toolbar size; theme-independent colors are not allowed and a picture picker is more than needed. |
| Show the profile button always? | Only with more than one profile, so the default single-profile toolbar does not change. |
| "Ask every time" and links from other apps? | A launch with URLs goes to the last used profile without asking; asking on every clicked link would make external links unusable. Only a plain start asks. |
| Can Default be deleted? | No (it can be renamed): its data lives at the legacy paths, and there must always be one profile. |
| Delete a running profile? | No: its process holds the database and web storage open. Delete is disabled with a tooltip saying to close its windows first. |
| Confirmation or undo for deletion? | Confirmation: the data is removed from disk and the wallet, so an undo would have to keep it around. The confirm dialog names the data that goes. |
| How is another profile started? | `QProcess.startDetached(sys.executable, ["-P", "-m", "kondor", "--profile", id])` with the inherited environment, which is what `packaging/kondor` runs and also works in Flatpak and AppImage. |
| A desktop action per profile? | Out of scope: the `.desktop` file is installed by packages and Flatpak, so actions per profile would need a generated file per user. `kondor --profile <name>` covers custom launchers. |
