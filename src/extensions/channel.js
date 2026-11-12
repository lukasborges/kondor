// Kondor web channel client, page side. Runs in the application world of every
// frame (after qwebchannel.js, in the same script), so the password manager
// and the extensions share one connection: `window.__kondorChannel` is a
// promise for the objects registered on the tab's channel
// (`kondorPasswords` in normal tabs, `kondorExtensions` in every tab). The
// page's own scripts cannot see this world.
(function () {
    "use strict";

    if (window.__kondorChannel)
        return;

    window.__kondorChannel = new Promise(function (resolve) {
        function connect() {
            if (typeof QWebChannel === "undefined" || typeof qt === "undefined"
                    || !qt.webChannelTransport)
                return false;
            new QWebChannel(qt.webChannelTransport, function (channel) {
                resolve(channel.objects);
            });
            return true;
        }

        if (connect())
            return;
        // At document start the transport may not exist yet.
        let tries = 0;
        const timer = setInterval(function () {
            if (connect() || ++tries > 200)
                clearInterval(timer);
        }, 25);
    });
})();
