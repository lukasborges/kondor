#include "bookmarks/bookmarkhtmlparser.h"

#include "bookmarks/bookmarkhtmltext.h"
#include "bookmarks/bookmarkrow.h"

#include <optional>

namespace BookmarkHtmlParser {

namespace {

class Scanner {
public:
    explicit Scanner(const QString &html) : m_html(html) { m_stack.append(Path()); }

    ParsedBookmarks scan()
    {
        m_root.isFolder = true;
        while (m_position < m_html.size() && scanNext()) {
        }
        return {m_root, m_count};
    }

private:
    using Path = QList<int>;

    struct Tag {
        QString name;
        QString text;
        bool isClosing = false;
    };

    bool scanNext()
    {
        const int open = m_html.indexOf(QLatin1Char('<'), m_position);
        if (open < 0)
            return false;
        if (m_html.mid(open, 4) == QLatin1String("<!--"))
            return skipComment(open);
        return readTag(open);
    }

    bool skipComment(int open)
    {
        const int end = m_html.indexOf(QLatin1String("-->"), open + 4);
        m_position = end < 0 ? int(m_html.size()) : end + 3;
        return true;
    }

    bool readTag(int open)
    {
        const int close = m_html.indexOf(QLatin1Char('>'), open);
        if (close < 0)
            return false;
        m_position = close + 1;
        return handle(parseTag(m_html.mid(open + 1, close - open - 1)));
    }

    static Tag parseTag(const QString &raw)
    {
        Tag tag;
        tag.text = raw.trimmed();
        tag.isClosing = tag.text.startsWith(QLatin1Char('/'));
        if (tag.isClosing)
            tag.text = tag.text.mid(1).trimmed();
        tag.name = tagName(tag.text);
        return tag;
    }

    static QString tagName(const QString &text)
    {
        int end = 0;
        while (end < text.size() && !text.at(end).isSpace() && text.at(end) != QLatin1Char('/'))
            ++end;
        return text.left(end).toLower();
    }

    bool handle(const Tag &tag)
    {
        if (tag.name == QLatin1String("h3"))
            return readFolderTitle();
        if (tag.name == QLatin1String("dl"))
            return changeList(tag.isClosing);
        if (tag.name == QLatin1String("a") && !tag.isClosing)
            return readLink(tag.text);
        return true;
    }

    bool readFolderTitle()
    {
        const int close = m_html.indexOf(QLatin1String("</h3"), m_position, Qt::CaseInsensitive);
        if (close < 0)
            return false;
        m_pending = addChild({true, BookmarkHtmlText::cleanTitle(m_html.mid(m_position, close - m_position)), {}, {}});
        skipPastTagEnd(close);
        return true;
    }

    bool changeList(bool isClosing)
    {
        if (isClosing && m_stack.size() > 1)
            m_stack.removeLast();
        if (!isClosing)
            m_stack.append(m_pending.value_or(m_stack.last()));
        m_pending.reset();
        return true;
    }

    bool readLink(const QString &tagText)
    {
        const int close = m_html.indexOf(QLatin1String("</a"), m_position, Qt::CaseInsensitive);
        if (close < 0)
            return false;
        const QUrl url(BookmarkHtmlText::attributeValue(tagText, QStringLiteral("href")).trimmed());
        if (isSupportedBookmarkUrl(url))
            addLink(url, BookmarkHtmlText::cleanTitle(m_html.mid(m_position, close - m_position)));
        skipPastTagEnd(close);
        return true;
    }

    void addLink(const QUrl &url, const QString &title)
    {
        addChild({false, title.isEmpty() ? url.toString() : title, url, {}});
        ++m_count;
    }

    void skipPastTagEnd(int from)
    {
        const int after = m_html.indexOf(QLatin1Char('>'), from);
        m_position = after < 0 ? int(m_html.size()) : after + 1;
    }

    Path addChild(ImportedBookmark child)
    {
        Path path = m_stack.last();
        ImportedBookmark &parent = nodeAt(path);
        parent.children.append(std::move(child));
        path.append(int(parent.children.size()) - 1);
        return path;
    }

    ImportedBookmark &nodeAt(const Path &path)
    {
        ImportedBookmark *node = &m_root;
        for (int index : path)
            node = &node->children[index];
        return *node;
    }

    const QString &m_html;
    int m_position = 0;
    int m_count = 0;
    ImportedBookmark m_root;
    QList<Path> m_stack;
    std::optional<Path> m_pending;
};

}

ParsedBookmarks parse(const QString &html)
{
    return Scanner(html).scan();
}

}
