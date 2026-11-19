const ktSkipTags = new Set(["SCRIPT", "STYLE", "NOSCRIPT", "CODE", "PRE", "TEXTAREA", "SVG", "MATH",
    "IFRAME", "SELECT", "OPTION", "INPUT", "CANVAS", "TEMPLATE", "KBD", "SAMP"]);
const ktInlineTags = new Set(["A", "ABBR", "B", "BDI", "BDO", "BR", "CITE", "DFN", "EM", "I", "MARK",
    "Q", "S", "SMALL", "SPAN", "STRONG", "SUB", "SUP", "TIME", "U", "WBR"]);
const ktAttributes = ["title", "alt", "placeholder", "aria-label"];
const ktAttributeSkipTags = new Set(["SCRIPT", "STYLE", "NOSCRIPT", "TEMPLATE", "SVG", "MATH", "CANVAS"]);
const ktSkippedSelector = "[translate=no], .notranslate, [contenteditable]:not([contenteditable=false])";

const ktHasText = (node) => /\S/.test(node.nodeValue);
const ktTag = (element) => element.tagName.toUpperCase();
const ktIsSkipped = (element) => ktSkipTags.has(ktTag(element)) || element.matches(ktSkippedSelector);
const ktIsInsideSkipped = (element) => !!element.closest(ktSkippedSelector);
const ktParse = (html) => new DOMParser().parseFromString("<!doctype html><body>" + html, "text/html").body;
const ktEscape = (text) => text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
const ktChildren = (element) => Array.from(element.childNodes);
const ktHasDirectText = (element) => ktChildren(element).some((node) => node.nodeType === 3 && ktHasText(node));

const ktIsInlineOnly = (element) => Array.from(element.children).every((child) =>
    ktInlineTags.has(ktTag(child)) && !ktIsSkipped(child) && ktIsInlineOnly(child));

const ktTagAttribute = "data-kondor-tid";

const ktTagDescendants = (element) => {
    const tagged = Array.from(element.querySelectorAll("*"));
    tagged.forEach((child, index) => child.setAttribute(ktTagAttribute, index));
    const html = element.innerHTML;
    tagged.forEach((child) => child.removeAttribute(ktTagAttribute));
    return { tagged, html };
};

const ktAdoptOriginal = (copy, tagged, used) => {
    const original = tagged[copy.getAttribute(ktTagAttribute)];
    if (!original || used.has(original))
        return;
    used.add(original);
    original.replaceChildren(...ktChildren(copy));
    copy.replaceWith(original);
};

const ktRebuild = (element, html, tagged) => {
    const body = ktParse(html);
    const used = new Set();
    Array.from(body.querySelectorAll("[" + ktTagAttribute + "]"))
        .forEach((copy) => ktAdoptOriginal(copy, tagged, used));
    element.replaceChildren(...ktChildren(body));
};

const ktRestoreElement = (element, original, inner) => {
    element.replaceChildren(...original);
    inner.forEach(([child, children]) => child.replaceChildren(...children));
};

const ktElementUnit = (element) => {
    const original = ktChildren(element);
    const { tagged, html } = ktTagDescendants(element);
    const inner = tagged.map((child) => [child, ktChildren(child)]);
    return {
        node: element,
        html,
        apply: (translated) => ktRebuild(element, translated, tagged),
        restore: () => ktRestoreElement(element, original, inner),
    };
};

const ktTextUnit = (node) => {
    const original = node.nodeValue;
    return {
        node,
        html: ktEscape(original),
        apply: (html) => { node.nodeValue = ktParse(html).textContent; },
        restore: () => { node.nodeValue = original; },
    };
};

const ktAttributeUnit = (element, name) => {
    const original = element.getAttribute(name);
    return {
        node: element,
        html: ktEscape(original),
        apply: (html) => element.setAttribute(name, ktParse(html).textContent),
        restore: () => element.setAttribute(name, original),
    };
};

const ktCollectChild = (child, units) => {
    if (child.nodeType === 1)
        ktCollectText(child, units);
    else if (child.nodeType === 3 && ktHasText(child))
        units.push(ktTextUnit(child));
};

const ktCollectText = (element, units) => {
    if (ktIsSkipped(element))
        return;
    if (ktHasDirectText(element) && ktIsInlineOnly(element))
        units.push(ktElementUnit(element));
    else
        ktChildren(element).forEach((child) => ktCollectChild(child, units));
};

const ktCollectAttributes = (root, units) => {
    const selector = ktAttributes.map((name) => "[" + name + "]").join(",");
    const elements = [root, ...root.querySelectorAll(selector)].filter((el) => el.nodeType === 1);
    for (const element of elements) {
        if (ktIsInsideSkipped(element) || ktAttributeSkipTags.has(ktTag(element)))
            continue;
        ktAttributes.filter((name) => /\S/.test(element.getAttribute(name) || ""))
            .forEach((name) => units.push(ktAttributeUnit(element, name)));
    }
};

const ktCollect = (root) => {
    const units = [];
    if (root.nodeType === 1 && !ktIsInsideSkipped(root))
        ktCollectText(root, units);
    else if (root.nodeType === 3 && ktHasText(root) && !ktIsInsideSkipped(root.parentElement))
        units.push(ktTextUnit(root));
    if (root.nodeType === 1)
        ktCollectAttributes(root, units);
    return units;
};
