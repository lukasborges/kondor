from kondor.app.mcp.protocol.tool import Tool
from kondor.app.mcp.tools import inspection, interaction, navigation, pagetools


def all_tools() -> list[Tool]:
    return [*pagetools.TOOLS, *navigation.TOOLS, *inspection.TOOLS, *interaction.TOOLS]
