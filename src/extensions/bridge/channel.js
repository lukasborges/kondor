{
    const hasTransport = () => typeof QWebChannel !== "undefined" && typeof qt !== "undefined"
        && !!qt.webChannelTransport;

    const connectTo = (resolve) => {
        if (!hasTransport())
            return false;
        new QWebChannel(qt.webChannelTransport, (channel) => resolve(channel.objects));
        return true;
    };

    const retryUntilConnected = (resolve) => {
        let tries = 0;
        const timer = setInterval(() => {
            if (connectTo(resolve) || ++tries > 200)
                clearInterval(timer);
        }, 25);
    };

    const startChannel = (resolve) => {
        if (!connectTo(resolve))
            retryUntilConnected(resolve);
    };

    const connectChannel = () => {
        if (window.__kondorChannel)
            return;
        window.__kondorChannel = new Promise(startChannel);
    };

    connectChannel();
}
