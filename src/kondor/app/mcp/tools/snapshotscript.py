SNAPSHOT_SCRIPT = """
(() => {
  const selector = 'a[href], button, input, select, textarea, summary, [role=button], [role=link], '
    + '[role=checkbox], [role=tab], [role=menuitem], [role=switch], [contenteditable=true]';
  const isVisible = (element) => {
    const box = element.getBoundingClientRect();
    const style = getComputedStyle(element);
    return box.width > 0 && box.height > 0 && style.visibility !== 'hidden';
  };
  const nameOf = (element) => (element.getAttribute('aria-label') || element.innerText
    || element.value || element.placeholder || element.title || element.alt || '')
    .trim().replace(/\\s+/g, ' ').slice(0, 80);
  const roleOf = (element) => element.getAttribute('role') || element.tagName.toLowerCase();
  window.__kondorElements = [...document.querySelectorAll(selector)].filter(isVisible);
  const lines = window.__kondorElements.map((element, index) =>
    `[${index}] ${roleOf(element)} "${nameOf(element)}"`);
  const text = document.body ? document.body.innerText.trim().slice(0, 6000) : '';
  const header = `Title: ${document.title}\\nURL: ${location.href}`;
  return `${header}\\n\\n${text}\\n\\nInteractive elements:\\n${lines.join('\\n')}`;
})()
"""

CENTER_SCRIPT = """
((uid) => {
  const element = (window.__kondorElements || [])[uid];
  if (!element || !element.isConnected) return null;
  element.scrollIntoView({block: 'center', inline: 'center'});
  const box = element.getBoundingClientRect();
  return {x: box.left + box.width / 2, y: box.top + box.height / 2};
})(%d)
"""

VIEWPORT_CENTER_SCRIPT = "({x: window.innerWidth / 2, y: window.innerHeight / 2})"
