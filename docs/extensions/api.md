# Writing a Kondor extension (API version 1)

A Kondor extension is a ZIP file named `<id>-<version>.kondorext` with a `manifest.json` at its
root, next to the JavaScript, CSS and icon files it names. It contains no native or QML code.
Extensions are proposed by pull request to
[`lukasborges/kondor-extensions`](https://github.com/lukasborges/kondor-extensions).

## Manifest

```json
{
  "kondor": 1,
  "id": "dark-mode",
  "name": "Dark Mode",
  "name[pt_BR]": "Modo Escuro",
  "description": "Shows every site with dark colors.",
  "version": "1.0.0",
  "author": "Kondor contributors",
  "homepage": "https://github.com/lukasborges/kondor-extensions/tree/main/extensions/dark-mode",
  "license": "GPL-3.0-or-later",
  "icon": "icon.svg",
  "permissions": ["tabs"],
  "contentScripts": [
    { "matches": ["https://*/*", "http://*/*"], "exclude": [], "js": ["content.js"],
      "css": ["dark.css"], "runAt": "document-start", "allFrames": false }
  ],
  "settings": [
    { "key": "brightness", "type": "number", "label": "Brightness", "label[pt_BR]": "Brilho",
      "default": 100, "min": 50, "max": 150, "suffix": "%" }
  ],
  "action": {
    "items": [ { "id": "toggle-images", "title": "Dim Images", "checkable": true } ],
    "siteToggle": true
  }
}
```

| Field | Meaning |
| --- | --- |
| `kondor` | API version. Must be `1`. |
| `id` | `^[a-z0-9][a-z0-9-]{1,47}$`, unique in the catalog. |
| `version` | `MAJOR.MINOR.PATCH`. |
| `icon` | An SVG or a PNG of at least 64 px inside the package, or a Breeze icon name. |
| `permissions` | `tabs` (`kondor.tabs.*`), `downloads` (`kondor.download()`), `notifications` (`kondor.notify()`). Storage and settings need none. |
| `contentScripts[]` | `matches` (Chrome-style match patterns), optional `exclude`, `js` and `css` (package files), `runAt` (`document-start`, `document-end`, `document-idle`; default `document-idle`), `allFrames` (default false). |
| `settings[]` | `key`, `type`, `label`, `default`. Types: `bool`, `number` (`min`, `max`, `step`, `suffix`), `string`, `text`, `choice` (`choices: [{value, label}]`), `color`, `keys`. |
| `action` | Optional. `items[]` (`id`, `title`, optional `checkable`, `icon`) appear in the toolbar Extensions menu; `siteToggle` adds "Run on <site>". |

`name`, `description`, `label` and `title` accept `key[<locale>]` translations, for example
`"name[pt_BR]"`.

Limits: the unpacked package is at most 5 MiB and 200 files. Every listed file must exist inside
the package (no `..`, no absolute paths). Unknown keys are ignored.

## JavaScript API

Your scripts run in a closure that receives a `kondor` object. Functions that talk to the browser
return Promises.

| API | Behavior |
| --- | --- |
| `kondor.extension` | `{ id, version }` |
| `kondor.locale` | For example `"pt_BR"`. |
| `kondor.isPrivate` | True in a private tab. |
| `kondor.settings.values` | Frozen `{key: value}` object (defaults for unset keys). |
| `kondor.settings.onChanged(cb)` | `cb(values)` after the user changes a setting, also in open tabs. |
| `kondor.storage.get(key)` / `set(key, value)` / `remove(key)` / `keys()` | JSON values, 1 MiB per extension. In a private tab `set` and `remove` reject with "Storage is read-only in private windows". |
| `kondor.onAction(cb)` | `cb(itemId, checked)` when the user picks one of your toolbar menu items. |
| `kondor.action.setChecked(itemId, checked)` | Updates a checkable item's state for this tab. |
| `kondor.tabs.back()` / `forward()` / `reload()` / `close()` / `open(url, {background})` / `next()` / `previous()` | Needs `tabs`. |
| `kondor.download(url, fileName?)` | Needs `downloads`. |
| `kondor.notify(title, body)` | Needs `notifications`. |

## Behavior to know about

- Extensions do not run in private windows unless the user allows it ("Allow in private windows").
- They do not run on sites the user turned off with "Run on <site>".
- An extension that runs on a site can read that site's DOM, as in any browser.
- Content scripts share the application JavaScript world with the browser; extensions are isolated
  from each other by closures.

## Testing

```bash
cd my-extension && zip -r /tmp/my-extension.kondorext .
```

Then use Settings → Extensions → Install from File… on an isolated profile.
