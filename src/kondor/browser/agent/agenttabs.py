from typing import ClassVar

from PySide6.QtCore import QObject, Signal
from shiboken6 import isValid

from kondor.browser.agent.tabagent import TabAgent


class AgentTabs(QObject):
    _instance: ClassVar["AgentTabs | None"] = None

    tabAccessChanged = Signal(str, bool)

    def __init__(self) -> None:
        super().__init__()
        self._agents: list[TabAgent] = []
        self._announced: set[str] = set()
        self._pending_owners: dict[str, str] = {}

    @classmethod
    def instance(cls) -> "AgentTabs":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def watch(self, agent: TabAgent) -> None:
        self._agents.append(agent)
        agent.accessChanged.connect(self.refresh)
        agent.targetIdChanged.connect(lambda: self.adopt_owned(agent))
        agent.destroyed.connect(self.refresh)

    def adopt_owned(self, agent: TabAgent) -> None:
        name = self._pending_owners.pop(agent.targetId, None)
        if name is not None:
            agent.grant(name)
        self.refresh()

    def live_agents(self) -> list[TabAgent]:
        self._agents = [agent for agent in self._agents if isValid(agent)]
        return self._agents

    def target_ids(self) -> list[str]:
        return [a.targetId for a in self.live_agents() if a.hasAccess and a.targetId]

    def refresh(self) -> None:
        current = set(self.target_ids())
        for target_id in sorted(self._announced - current):
            self.tabAccessChanged.emit(target_id, False)
        for target_id in sorted(current - self._announced):
            self.tabAccessChanged.emit(target_id, True)
        self._announced = current

    def find(self, target_id: str) -> TabAgent | None:
        return next((a for a in self.live_agents() if a.targetId == target_id), None)

    def own(self, target_id: str, name: str) -> None:
        agent = self.find(target_id)
        if agent is None:
            self._pending_owners[target_id] = name
        else:
            agent.grant(name)

    def note_activity(self, target_id: str, name: str) -> None:
        agent = self.find(target_id)
        if agent is not None and agent.hasAccess:
            agent.note_activity(name)
