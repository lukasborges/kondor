BYTE_ORDER_MARK = "﻿"
QUOTE = '"'
SEPARATOR = ","
LINE_FEED = "\n"
CARRIAGE_RETURN = "\r"
LINE_BREAKS = (LINE_FEED, CARRIAGE_RETURN)


class CsvReader:
    def __init__(self, text: str) -> None:
        self._text = text
        self._position = 0
        self._rows: list[list[str]] = []
        self._row: list[str] = []
        self._field: list[str] = []
        self._is_in_quotes = False
        self._row_has_content = False

    def read_all(self) -> list[list[str]]:
        while self._position < len(self._text):
            self._read_character(self._text[self._position])
            self._position += 1
        if self._row_has_content or self._field or self._row:
            self._end_row()
        return self._rows

    def _read_character(self, character: str) -> None:
        if self._is_in_quotes:
            self._read_quoted(character)
        else:
            self._read_unquoted(character)

    def _read_quoted(self, character: str) -> None:
        if character != QUOTE:
            self._field.append(character)
        elif self._next_is(QUOTE):
            self._append_escaped_quote()
        else:
            self._is_in_quotes = False

    def _read_unquoted(self, character: str) -> None:
        if character == QUOTE:
            self._start_quotes()
        elif character == SEPARATOR:
            self._end_field_with_more()
        elif character in LINE_BREAKS:
            self._end_line(character)
        else:
            self._append_character(character)

    def _next_is(self, character: str) -> bool:
        following = self._position + 1
        return following < len(self._text) and self._text[following] == character

    def _append_escaped_quote(self) -> None:
        self._field.append(QUOTE)
        self._position += 1

    def _start_quotes(self) -> None:
        self._is_in_quotes = True
        self._row_has_content = True

    def _end_field_with_more(self) -> None:
        self._end_field()
        self._row_has_content = True

    def _append_character(self, character: str) -> None:
        self._field.append(character)
        self._row_has_content = True

    def _end_line(self, character: str) -> None:
        if character == CARRIAGE_RETURN and self._next_is(LINE_FEED):
            self._position += 1
        self._end_row()

    def _end_field(self) -> None:
        self._row.append("".join(self._field))
        self._field = []

    def _end_row(self) -> None:
        self._end_field()
        if self._row_has_content:
            self._rows.append(self._row)
        self._row = []
        self._row_has_content = False


def without_byte_order_mark(text: str) -> str:
    return text.removeprefix(BYTE_ORDER_MARK)


def read_csv_rows(data: bytes | bytearray) -> list[list[str]]:
    text = data.decode("utf-8", errors="replace")
    return CsvReader(without_byte_order_mark(text)).read_all()
