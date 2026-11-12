// Marks the page so the tests (and the manual test) can see it ran.
const root = document.documentElement;
root.setAttribute("data-kondor-sample", kondor.settings.values.greeting);
root.setAttribute("data-kondor-private", String(kondor.isPrivate));

kondor.settings.onChanged(function (values) {
    root.setAttribute("data-kondor-sample", values.greeting);
});

kondor.onAction(function (itemId, checked) {
    root.setAttribute("data-kondor-action", itemId + ":" + checked);
});

kondor.storage.set("lastGreeting", kondor.settings.values.greeting).then(function () {
    root.setAttribute("data-kondor-storage", "ok");
}, function (error) {
    root.setAttribute("data-kondor-storage", error.message);
});
