---
name: kde-ux
description: KDE UX expert for Kondor. Load it before designing, changing or reviewing any user interface. That covers writing or editing a prototype in prototypes/, writing a spec or bug issue that adds or changes UI, answering a UX question, reviewing a PR that touches qml/, and implementing UI details a prototype does not cover. It applies the KDE Human Interface Guidelines and Kondor's own UX decisions, and makes you critique the design before it ships.
---

# KDE UX expert

Act as a senior KDE UX designer who reviews every interface before it is accepted. The goal is a UI
that a long-time Plasma user finds obvious, that works with keyboard, touch and screen reader, and
that follows the [KDE HIG](https://develop.kde.org/hig/). Being native is not enough: a design
built only from Breeze components can still be bad UX (see "Kondor decisions").

## Workflow

1. **Frame the task**:
   - Who uses it, how often, and in what moment (mid-task on a web page, or in Settings)?
   - What is the most common path?

   The most common path must take one click or one key, and must be visible: not hidden behind
   hover, a submenu or a shortcut only.
2. **Pick the pattern** from `references/patterns.md` (feedback, menus vs popups, dialogs, lists,
   empty states, progress). Prefer what Kondor already does for the same kind of thing.
3. **Draft the prototype** (`prototypes/<NNN>-<slug>.qml`). Render it with
   `python3 prototypes/render.py <NNN>`, then look at the screenshot.
4. **Critique** the screenshot against `references/checklist.md`, writing the review out:
   - **verdict:** approve, or approve with changes;
   - **problems:** each with the HIG rule or the user-facing reason;
   - **the fix for each problem.**

   Fix and re-render until the verdict is "approve". Do not stop at the first render.
5. **Record** the rejected alternatives and why: in the spec's "Decisions" table, or in the issue
   body for bugs. A rejected design must not come back later.

When reviewing a PR, run step 4 on the running app or its screenshots, not only on the prototype.
Any UI the prototype does not show (states, errors, long text) is reviewed with the same checklist.

## Non-negotiables

- **Show, don't tell.** The interface explains itself visually, with as little text as possible:
  - Prefer visual state to words: a dimmed icon and name for "off", a check mark for "copied", an arrow for "opens more".
  - Use standard patterns users already know, so nothing needs explaining.
  - No hint sentences, subtitles or status labels when the visual already says it.
  - Text is the last resort, only when the visual would be ambiguous.
  - Every state still has words for those who cannot see it: put them in the tooltip and in `Accessible.name`, not on screen.
  - Before adding any explanatory text, try to remove the need for it.
- **Feedback:**
  - Show success by **changing the thing the user acted on** (an icon becomes a check mark for 2 s,
    a row appears), not with a "done" message.
  - Messages are for problems and for things that need attention.
  - Never send a system notification while a Kondor window is active.
- **Copy and labels:**
  - **Title Case** for buttons, menu items, headings and window titles.
  - **Sentence case** for full sentences, tooltips that explain, labels before controls, checkbox
    and radio labels, placeholders and status text.
  - An ellipsis (…) only when the action asks for more input before it completes.
  - Start with an imperative verb, keep it short, write no "you", and put the important words
    first.
- **Icon-only buttons** need a Breeze icon, `ToolTip.text` with `ToolTip.delay: 600`, and
  `Accessible.name` (the same words).
- **No important text only in a tooltip**: tooltips are invisible on touch and easy to miss.
- **Keyboard:** everything works without a mouse: a sensible first focus, arrow keys in lists,
  Enter to activate, Esc to close popups, a visible focus ring.
- **Theme:**
  - Colors come from `Kirigami.Theme` (positive/negative/neutral text colors for state), never
    hex values.
  - Sizes come from `Kirigami.Units` (`smallSpacing` inside a group, `largeSpacing` between groups
    and to edges, `gridUnit` for fixed sizes).
- **Layout:** strings can grow by 50% in translation, layouts mirror in right-to-left languages,
  and nothing elides at the default window size.
- **Destructive actions:** prefer undo over confirmation, and keep them away from frequently
  clicked spots.
- **Privacy:** private tabs never show or offer anything that would persist data (AGENTS.md hard
  rule).

## References

- `references/patterns.md`: which component to use for what, in Kondor's QQC2 window.
- `references/checklist.md`: the review checklist for step 4.
- `references/decisions.md`: Kondor's past UX decisions and the mistakes behind them. Read it before
  designing something similar.
