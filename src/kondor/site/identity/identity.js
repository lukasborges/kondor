const origins = location.ancestorOrigins;
const firstPartyHost = origins.length
    ? new URL(origins[origins.length - 1]).hostname
    : location.hostname;
const entry = agents[firstPartyHost];
if (entry) {
    const define = (name, value) => Object.defineProperty(
        Navigator.prototype, name, { get: () => value, configurable: true });
    define("userAgent", entry.agent);
    define("appVersion", entry.agent.replace("Mozilla/", ""));
    define("platform", "Linux x86_64");
    if (!entry.keepsHints)
        delete Navigator.prototype.userAgentData;
}
