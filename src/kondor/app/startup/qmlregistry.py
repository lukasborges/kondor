from kondor.adblock import qmltypes as adblock
from kondor.app import qmltypes as app
from kondor.bookmarks import qmltypes as bookmarks
from kondor.browser import qmltypes as browser
from kondor.core import qmltypes as core
from kondor.downloads import qmltypes as downloads
from kondor.extensions import qmltypes as extensions
from kondor.history import qmltypes as history
from kondor.passwords import qmltypes as passwords
from kondor.profiles import qmltypes as profiles
from kondor.site import qmltypes as site

FEATURE_TYPES = (
    core,
    adblock,
    downloads,
    history,
    bookmarks,
    passwords,
    profiles,
    site,
    browser,
    extensions,
    app,
)


def register_all_types() -> None:
    for module in FEATURE_TYPES:
        module.register_types()
