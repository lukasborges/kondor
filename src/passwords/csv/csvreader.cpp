#include "passwords/csv/csvreader.h"

namespace {

class CsvReader
{
public:
    explicit CsvReader(const QString &text)
        : m_text(text)
    {
    }

    QList<QStringList> readAll()
    {
        for (m_position = 0; m_position < m_text.size(); ++m_position)
            readCharacter(m_text.at(m_position));
        if (m_rowHasContent || !m_field.isEmpty() || !m_row.isEmpty())
            endRow();
        return m_rows;
    }

private:
    void readCharacter(QChar character)
    {
        if (m_inQuotes)
            readQuoted(character);
        else
            readUnquoted(character);
    }

    void readQuoted(QChar character)
    {
        if (character != QLatin1Char('"'))
            m_field.append(character);
        else if (nextIs(QLatin1Char('"')))
            appendEscapedQuote();
        else
            m_inQuotes = false;
    }

    void readUnquoted(QChar character)
    {
        if (character == QLatin1Char('"'))
            startQuotes();
        else if (character == QLatin1Char(','))
            endFieldWithMore();
        else if (character == QLatin1Char('\n') || character == QLatin1Char('\r'))
            endLine(character);
        else
            appendCharacter(character);
    }

    bool nextIs(QChar character) const
    {
        return m_position + 1 < m_text.size() && m_text.at(m_position + 1) == character;
    }

    void appendEscapedQuote()
    {
        m_field.append(QLatin1Char('"'));
        ++m_position;
    }

    void startQuotes()
    {
        m_inQuotes = true;
        m_rowHasContent = true;
    }

    void endFieldWithMore()
    {
        endField();
        m_rowHasContent = true;
    }

    void appendCharacter(QChar character)
    {
        m_field.append(character);
        m_rowHasContent = true;
    }

    void endLine(QChar character)
    {
        if (character == QLatin1Char('\r') && nextIs(QLatin1Char('\n')))
            ++m_position;
        endRow();
    }

    void endField()
    {
        m_row.append(m_field);
        m_field.clear();
    }

    void endRow()
    {
        endField();
        if (m_rowHasContent)
            m_rows.append(m_row);
        m_row.clear();
        m_rowHasContent = false;
    }

    QString m_text;
    qsizetype m_position = 0;
    QList<QStringList> m_rows;
    QStringList m_row;
    QString m_field;
    bool m_inQuotes = false;
    bool m_rowHasContent = false;
};

QString withoutByteOrderMark(QString text)
{
    if (text.startsWith(QChar(0xFEFF)))
        text.remove(0, 1);
    return text;
}

}

QList<QStringList> readCsvRows(const QByteArray &data)
{
    return CsvReader(withoutByteOrderMark(QString::fromUtf8(data))).readAll();
}
