#include "adblockinterceptor.h"

#include <QReadLocker>
#include <QWebEngineUrlRequestInfo>
#include <QWriteLocker>

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
    using Type = QWebEngineUrlRequestInfo::ResourceType;
    const Type type = info.resourceType();

    if (type == Type::ResourceTypeMainFrame) {
        emit pageStarted(info.requestUrl().host().toLower());
        return;
    }
    if (!m_enabled)
        return;

    FilterEngine::ResourceKind kind = FilterEngine::Other;
    switch (type) {
    case Type::ResourceTypeSubFrame:
        kind = FilterEngine::SubFrame;
        break;
    case Type::ResourceTypeStylesheet:
        kind = FilterEngine::Stylesheet;
        break;
    case Type::ResourceTypeScript:
        kind = FilterEngine::Script;
        break;
    case Type::ResourceTypeImage:
        kind = FilterEngine::Image;
        break;
    case Type::ResourceTypeXhr:
        kind = FilterEngine::XmlHttpRequest;
        break;
    default:
        break;
    }

    const QString firstParty = info.firstPartyUrl().host().toLower();
    std::shared_ptr<const FilterEngine> engine;
    {
        QReadLocker locker(&m_lock);
        if (m_allowedHosts.contains(firstParty))
            return;
        engine = m_engine;
    }
    if (!engine || !engine->shouldBlock(info.requestUrl(), firstParty, kind))
        return;

    info.block(true);
    emit blocked(firstParty);
}
