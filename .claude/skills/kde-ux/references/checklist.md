# UX review checklist

Go through every line for each screen and state you designed or reviewed. Write down each "no"
with the fix.

## Task fit

- [ ] Show, don't tell. For every hint, subtitle or status label, ask whether a visual cue or a standard pattern could replace it. Remove it if one can, and keep the words in the tooltip and `Accessible.name`.
- [ ] The most common action takes one click or key and is visible without hover.
- [ ] Each thing (account, site, tab) appears once; the user picks the thing first, then the
      action (object → verb).
- [ ] Every clickable element says what it does, through an obvious standard pattern (arrow, hover
      highlight, icon) or a short verb label. Use a hint sentence only when the pattern would be
      ambiguous.
- [ ] Nothing important hides behind hover, a submenu or a keyboard shortcut only.
- [ ] The design still works with 1 item, many items (10+), very long names, no items, and an
      error (wallet locked, offline). **Prototype the 10+ case**, not only two items (#183).

## Feedback and status

- [ ] Success shows as a change on the control or item, not a message (`references/patterns.md`).
- [ ] Anything longer than 1 s shows progress, and the rest of the browser stays usable.
- [ ] There is no system notification while a Kondor window is active.
- [ ] Errors say what happened and what to do, in plain words.

## Text

- [ ] Title Case for buttons, menu items, headings and titles. Sentence case for sentences,
      explanatory tooltips, form labels, checkboxes, placeholders and status text.
- [ ] An ellipsis only for actions that need more input. It is the `…` character.
- [ ] Imperative, short, no "you", important words first, no jargon (say "link", not "URL").
- [ ] No important information only in a tooltip.
- [ ] Every string is in `qsTr()` and still fits at +50% length.

## Keyboard, touch and screen reader

- [ ] Usable with the keyboard only: first focus, Tab order, arrows in lists, Enter, Esc, and a
      visible focus.
- [ ] Every icon-only button has a tooltip (`ToolTip.delay: 600`) and an `Accessible.name`.
- [ ] Labels are distinct within the window: no two "Copy" buttons with the same accessible name;
      include the item ("Copy Password for maria@example.org").
- [ ] It works with touch: no hover-only controls, and tooltips also on press-and-hold.

## Look

- [ ] Only QQC2/Kirigami controls in the `org.kde.desktop` style. Colors from `Kirigami.Theme`,
      spacing from `Kirigami.Units`.
- [ ] It matches the closest existing Kondor UI: address bar popups look like the site security
      popup, and Settings pages look like the other Settings pages.
- [ ] It renders correctly with a dark color scheme and with right-to-left text.
- [ ] Icons are Breeze names that exist, with the right size for their place.

## Safety and privacy

- [ ] Destructive actions offer undo or a confirmation, and are not next to the common action.
- [ ] Private tabs never offer anything that would write data to disk.
- [ ] Secrets (passwords) are never shown by default, and copied secrets are cleared and hidden
      from clipboard history.
