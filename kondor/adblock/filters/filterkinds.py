from enum import Enum, IntFlag


class ResourceKind(IntFlag):
    MAIN_FRAME = 1
    SUB_FRAME = 2
    STYLESHEET = 4
    SCRIPT = 8
    IMAGE = 16
    XML_HTTP_REQUEST = 32
    OTHER = 64


class ThirdParty(Enum):
    ANY = "any"
    ONLY_THIRD_PARTY = "onlyThirdParty"
    ONLY_FIRST_PARTY = "onlyFirstParty"
