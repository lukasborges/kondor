from dataclasses import dataclass

DEFAULT_ID = "default"
ASK_EVERY_TIME = "ask"
MAX_NAME_LENGTH = 64
PROFILE_ICONS = (
    "im-user",
    "go-home",
    "view-pim-tasks",
    "globe",
    "favorite",
    "games-config-board",
    "code-context",
    "flag",
)


@dataclass(frozen=True)
class UserProfile:
    id: str
    name: str
    icon_name: str

    def as_map(self) -> dict[str, str]:
        return {"id": self.id, "name": self.name, "iconName": self.icon_name}
