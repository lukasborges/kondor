from dataclasses import dataclass, field

from kondor.passwords.csvimport.importtypes import Login
from kondor.passwords.csvimport.passwordimportplan import SavedLogins


@dataclass
class PendingImport:
    logins: list[Login] = field(default_factory=list)
    saved: SavedLogins = field(default_factory=dict)
    replace_conflicts: bool = False
