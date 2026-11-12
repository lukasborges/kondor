#include "adblock/filterengine.h"

#include <QTest>

class TestFilterEngine : public QObject
{
    Q_OBJECT

private:
    struct Request {
        const char *url;
        const char *page;
        FilterEngine::ResourceKind kind = FilterEngine::Script;
    };

    static bool blocked(const FilterEngine &engine, const Request &request)
    {
        return engine.shouldBlock(QUrl(QString::fromLatin1(request.url)),
                                  QString::fromLatin1(request.page), request.kind);
    }

private slots:
    void domainAnchor()
    {
        FilterEngine engine;
        engine.addRule(QStringLiteral("||ads.example.com^"));
        QVERIFY(blocked(engine, {"https://ads.example.com/x.js", "news.org"}));
        QVERIFY(blocked(engine, {"https://sub.ads.example.com/x.js", "news.org"}));
        QVERIFY(!blocked(engine, {"https://example.com/x.js", "news.org"}));
        QVERIFY(!blocked(engine, {"https://notads.example.com/x.js", "news.org"}));
    }

    void domainWithPath()
    {
        FilterEngine engine;
        engine.addRule(QStringLiteral("||example.com/banners/*"));
        QVERIFY(blocked(engine, {"https://example.com/banners/a.png", "x.org"}));
        QVERIFY(!blocked(engine, {"https://example.com/other/a.png", "x.org"}));
    }

    void exceptionsWin()
    {
        FilterEngine engine;
        engine.addRule(QStringLiteral("||tracker.net^"));
        engine.addRule(QStringLiteral("@@||tracker.net^$domain=friendly.org"));
        QVERIFY(blocked(engine, {"https://tracker.net/p.gif", "news.org"}));
        QVERIFY(!blocked(engine, {"https://tracker.net/p.gif", "friendly.org"}));
    }

    void thirdPartyOption()
    {
        FilterEngine engine;
        engine.addRule(QStringLiteral("||cdn.example.com^$third-party"));
        QVERIFY(blocked(engine, {"https://cdn.example.com/a.js", "other.org"}));
        QVERIFY(!blocked(engine, {"https://cdn.example.com/a.js", "www.example.com"}));
    }

    void typeOptions()
    {
        FilterEngine engine;
        engine.addRule(QStringLiteral("||img.example.com^$image"));
        QVERIFY(blocked(engine, {"https://img.example.com/a.png", "x.org", FilterEngine::Image}));
        QVERIFY(!blocked(engine, {"https://img.example.com/a.js", "x.org", FilterEngine::Script}));
    }

    void substringAndWildcard()
    {
        FilterEngine engine;
        engine.addRule(QStringLiteral("/adserver/"));
        engine.addRule(QStringLiteral("-banner-ad."));
        engine.addRule(QStringLiteral("/track*.gif?"));
        QVERIFY(blocked(engine, {"https://a.org/img/top-banner-ad.png", "x.org", FilterEngine::Image}));
        QVERIFY(blocked(engine, {"https://a.org/tracker1.gif?id=2", "x.org", FilterEngine::Image}));
        QVERIFY(!blocked(engine, {"https://a.org/adserver/x.js", "x.org"}));
    }

    void separatorCaret()
    {
        FilterEngine engine;
        engine.addRule(QStringLiteral("/ads^"));
        QVERIFY(blocked(engine, {"https://a.org/ads?x=1", "x.org"}));
        QVERIFY(blocked(engine, {"https://a.org/ads", "x.org"}));
        QVERIFY(!blocked(engine, {"https://a.org/adsense", "x.org"}));
    }

    void skippedRules()
    {
        FilterEngine engine;
        QVERIFY(!engine.addRule(QStringLiteral("! comment")));
        QVERIFY(!engine.addRule(QStringLiteral("[Adblock Plus 2.0]")));
        QVERIFY(!engine.addRule(QStringLiteral("example.com##.ad")));
        QVERIFY(!engine.addRule(QStringLiteral("||example.com^$unknownoption")));
        QVERIFY(!engine.addRule(QStringLiteral("/ad[0-9]+/")));
        QCOMPARE(engine.ruleCount(), 0);
    }

    void mainFrameNeverBlocked()
    {
        FilterEngine engine;
        engine.addRule(QStringLiteral("||example.com^"));
        QVERIFY(!blocked(engine, {"https://example.com/", "example.com", FilterEngine::MainFrame}));
    }

    void addList()
    {
        FilterEngine engine;
        engine.addList("[Adblock Plus 2.0]\n! x\n||a.com^\r\n||b.com^$script\n##.x\n");
        QCOMPARE(engine.ruleCount(), 2);
    }

    void domainOptionIncludesAndExcludesSites()
    {
        FilterEngine engine;
        engine.addRule(QStringLiteral("||ads.net^$domain=news.org|~live.news.org"));
        QVERIFY(blocked(engine, {"https://ads.net/a.js", "news.org"}));
        QVERIFY(blocked(engine, {"https://ads.net/a.js", "m.news.org"}));
        QVERIFY(!blocked(engine, {"https://ads.net/a.js", "live.news.org"}));
        QVERIFY(!blocked(engine, {"https://ads.net/a.js", "other.org"}));
    }

    void countryCodeSecondLevelDomainIsFirstParty()
    {
        FilterEngine engine;
        engine.addRule(QStringLiteral("||cdn.example.co.uk^$third-party"));
        QVERIFY(!blocked(engine, {"https://cdn.example.co.uk/a.js", "www.example.co.uk"}));
        QVERIFY(blocked(engine, {"https://cdn.example.co.uk/a.js", "www.other.co.uk"}));
    }

    void endAnchorRequiresTheEndOfTheAddress()
    {
        FilterEngine engine;
        engine.addRule(QStringLiteral("/banner.gif|"));
        QVERIFY(blocked(engine, {"https://a.org/img/banner.gif", "x.org", FilterEngine::Image}));
        QVERIFY(!blocked(engine, {"https://a.org/img/banner.gif?x=1", "x.org", FilterEngine::Image}));
    }
};

QTEST_APPLESS_MAIN(TestFilterEngine)
#include "tst_filterengine.moc"
