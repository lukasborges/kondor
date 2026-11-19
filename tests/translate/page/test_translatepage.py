from pathlib import Path

from PySide6.QtQml import QJSEngine

PAGE = Path(__file__).parents[3] / "src/kondor/translate/page/translatepage.js"

SETUP = """
var sent = [];
var document = { body: {}, documentElement: { lang: "en" } };
var window = { addEventListener() {} };
class MutationObserver { observe() {} disconnect() {} takeRecords() {} }
var ktCollect = () => [{ html: "a", node: {}, apply() {}, restore() {} }];
"""

BATCHES_SENT = 2

EXPOSE = """
ktState.bridge = { requestBatch: (id) => sent.push(id), reportState() {} };
"""


def make_engine(qapp) -> QJSEngine:
    engine = QJSEngine()
    engine.evaluate(SETUP)
    engine.evaluate(PAGE.read_text().replace("const ", "var "))
    engine.evaluate(EXPOSE)
    return engine


def test_translates_again_after_restore_during_a_batch(qapp):
    engine = make_engine(qapp)
    engine.evaluate("window.__kondorTranslation.start('pt')")
    engine.evaluate("window.__kondorTranslation.restore()")
    engine.evaluate("window.__kondorTranslation.deliver('{\"id\":1,\"results\":[\"b\"]}')")
    engine.evaluate("window.__kondorTranslation.start('pt')")
    assert engine.evaluate("sent.length").toInt() == BATCHES_SENT
