# Bergamot engine glue

JavaScript that runs Mozilla's Bergamot translation engine (WebAssembly) in a Web Worker, copied
unchanged from Firefox's source tree at tag `FIREFOX_141_0_RELEASE`
(<https://github.com/mozilla-firefox/firefox>), MPL-2.0 (see `LICENSE`):

| File | Origin |
| --- | --- |
| `bergamot-translator.js` | `toolkit/components/translations/bergamot-translator/bergamot-translator.js` |
| `translations-engine.worker.js` | `toolkit/components/translations/content/translations-engine.worker.js` |

The glue matches engine major version **3** (`translations-wasm` record `bergamot-translator`,
release v0.6.0, revision `1de4a085d3a7afb625c51a60aabb5ad298e4059f`). Only the `.wasm` and the
language models are downloaded at run time, from Mozilla's Remote Settings, and checked against
their SHA-256 hash.
