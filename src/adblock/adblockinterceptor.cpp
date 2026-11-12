#include "adblock/adblockinterceptor.h"

#include <QReadLocker>
#include <QWebEngineUrlRequestInfo>
#include <QWriteLocker>

namespace {
using ResourceType = QWebEngineUrlRequestInfo::ResourceType;

FilterEngine::ResourceKind resourceKindOf(ResourceType type)
{
    static const QHash<int, FilterEngine::ResourceKind> kinds = {
        {ResourceType::ResourceTypeSubFrame, FilterEngine::SubFrame},
        {ResourceType::ResourceTypeStylesheet, FilterEngine::Stylesheet},
        {ResourceType::ResourceTypeScript, FilterEngine::Script},
        {ResourceType::ResourceTypeImage, FilterEngine::Image},
        {ResourceType::ResourceTypeXhr, FilterEngine::XmlHttpRequest},
    };
    return kinds.value(static_cast<int>(type), FilterEngine::Other);
}
}

AdBlockInterceptor::AdBlockInterceptor(QObject *parent)
    : QWebEngineUrlRequestInterceptor(parent)
{
}

void AdBlockInterceptor::setEngine(std::shared_ptr<const FilterEngine> engine)
{
    QWriteLocker locker(&m_lock);
    m_engine = std::move(engine);
}

void AdBlockInterceptor::setAllowedHosts(const QSet<QString> &hosts)
{
    QWriteLocker locker(&m_lock);
    m_allowedHosts = hosts;
}

void AdBlockInterceptor::interceptRequest(QWebEngineUrlRequestInfo &info)
{
    if (info.resourceType() == ResourceType::ResourceTypeMainFrame)
        emit pageStarted(info.requestUrl().host().toLower());
    else if (m_enabled)
        blockIfListed(info);
}

void AdBlockInterceptor::blockIfListed(QWebEngineUrlRequestInfo &info)
{
    const QString firstParty = info.firstPartyUrl().host().toLower();
    if (!isListed(info, firstParty))
        return;
    info.block(true);
    emit blocked(firstParty);
}

bool AdBlockInterceptor::isListed(const QWebEngineUrlRequestInfo &info,
                                  const QString &firstPartyHost) const
{
    const auto engine = engineUnlessAllowed(firstPartyHost);
    const FilterEngine::ResourceKind kind = resourceKindOf(info.resourceType());
    return engine && engine->shouldBlock(info.requestUrl(), firstPartyHost, kind);
}

std::shared_ptr<const FilterEngine>
AdBlockInterceptor::engineUnlessAllowed(const QString &firstPartyHost) const
{
    QReadLocker locker(&m_lock);
    if (m_allowedHosts.contains(firstPartyHost))
        return nullptr;
    return m_engine;
}
