import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from qmlapi.compare import compare_all
from qmlapi.headerparser import parse_header
from qmlapi.model import ClassApi, Property

HEADER = """
class Sample : public QObject
{
    Q_OBJECT
    Q_PROPERTY(QString title READ title WRITE setTitle NOTIFY titleChanged)
    Q_PROPERTY(const QUrl &address
               READ address
               NOTIFY addressChanged)
    Q_PROPERTY(int limit MEMBER m_limit NOTIFY limitChanged)
    Q_PROPERTY(bool fixed MEMBER m_fixed CONSTANT)
    Q_PROPERTY(Group *group READ group CONSTANT)
    QML_ELEMENT

public:
    Q_INVOKABLE void open(const QUrl &url, bool foreground = true);
    Q_INVOKABLE void open();
    int ignored() const { return 1; }

public slots:
    void reload();

public Q_SLOTS:
    void zoom(int percent);

signals:
    void titleChanged();
    void moved(int x, int y);

Q_SIGNALS:
    void closed();

private:
    int m_limit = 0;
};
"""


def parsed() -> ClassApi:
    return parse_header(HEADER)["Sample"]


def twin(**changes) -> ClassApi:
    api = parsed()
    for name, value in changes.items():
        setattr(api, name, value)
    return api


def problems_with(python: ClassApi) -> list:
    return compare_all({"Sample": parsed()}, {"Sample": python})


class HeaderParserTest(unittest.TestCase):
    def test_multi_line_property_is_found(self):
        self.assertEqual(parsed().properties["address"], Property("QUrl", False))

    def test_write_makes_a_property_writable(self):
        self.assertTrue(parsed().properties["title"].is_writable)

    def test_member_without_constant_is_writable(self):
        self.assertTrue(parsed().properties["limit"].is_writable)

    def test_member_with_constant_is_read_only(self):
        self.assertFalse(parsed().properties["fixed"].is_writable)

    def test_pointer_type_is_normalized(self):
        self.assertEqual(parsed().properties["group"].type_name, "Group")

    def test_default_argument_adds_the_shorter_count(self):
        self.assertEqual(parsed().callables["open"], {0, 1, 2})

    def test_slots_sections_are_callables(self):
        self.assertEqual({name: parsed().callables[name] for name in ("reload", "zoom")},
                         {"reload": {0}, "zoom": {1}})

    def test_plain_methods_are_not_callables(self):
        self.assertNotIn("ignored", parsed().callables)

    def test_signals_and_q_signals_are_found(self):
        self.assertEqual(parsed().signals, {"titleChanged": {0}, "moved": {2}, "closed": {0}})

    def test_class_without_q_object_is_skipped(self):
        self.assertEqual(parse_header("class Plain { int x(); };"), {})


class ComparisonTest(unittest.TestCase):
    def test_identical_classes_have_no_problems(self):
        self.assertEqual(problems_with(parsed()), [])

    def test_missing_property_is_reported(self):
        python = twin(properties={})
        self.assertIn("Sample: missing property title", problems_with(python))

    def test_missing_signal_is_reported(self):
        python = twin(signals={})
        self.assertIn("Sample: missing signal moved", problems_with(python))

    def test_missing_callable_is_reported(self):
        python = twin(callables={})
        self.assertIn("Sample: missing callable zoom", problems_with(python))

    def test_unaccepted_argument_count_is_reported(self):
        python = twin(callables={**parsed().callables, "open": {0}})
        self.assertIn("Sample: callable open does not accept 2 arguments", problems_with(python))

    def test_writability_difference_is_reported(self):
        python = twin(properties={**parsed().properties, "title": Property("QString", False)})
        self.assertIn("Sample: property title writability differs", problems_with(python))

    def test_type_difference_is_reported(self):
        python = twin(properties={**parsed().properties, "limit": Property("QString", True)})
        self.assertEqual(len(problems_with(python)), 1)

    def test_variant_matches_any_type(self):
        python = twin(properties={**parsed().properties, "limit": Property("QVariant", True)})
        self.assertEqual(problems_with(python), [])

    def test_python_class_without_cpp_twin_is_an_error(self):
        self.assertEqual(compare_all({}, {"Lonely": ClassApi("Lonely")}), ["Lonely: no C++ class with this name"])


if __name__ == "__main__":
    unittest.main()
