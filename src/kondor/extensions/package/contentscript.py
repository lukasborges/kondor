from dataclasses import dataclass, field


@dataclass
class ExtensionContentScript:
    matches: list[str] = field(default_factory=list)
    include: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)
    js: list[str] = field(default_factory=list)
    css: list[str] = field(default_factory=list)
    run_at: str = "document-idle"
    all_frames: bool = False
