from typing import Any

ToolResult = dict[str, Any]


class ToolFailureError(Exception):
    pass


def text_result(text: str) -> ToolResult:
    return {"content": [{"type": "text", "text": text}]}


def image_result(base64_data: str, mime_type: str) -> ToolResult:
    return {"content": [{"type": "image", "data": base64_data, "mimeType": mime_type}]}


def error_result(text: str) -> ToolResult:
    return {"content": [{"type": "text", "text": text}], "isError": True}
