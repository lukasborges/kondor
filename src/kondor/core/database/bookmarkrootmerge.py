from kondor.core.database import sql

ROOT_ID = "SELECT id FROM bookmarks WHERE special = ? LIMIT 1"
NEXT_POSITION = "SELECT COALESCE(MAX(position) + 1, 0) FROM bookmarks WHERE parent_id = ?"
MOVE_CHILDREN = "UPDATE bookmarks SET parent_id = ?, position = position + ? WHERE parent_id = ?"
DELETE_ROW = "DELETE FROM bookmarks WHERE id = ?"


def root_id(special: str) -> int | None:
    found = sql.ids(ROOT_ID, (special,))
    return found[0] if found else None


def next_position(folder_id: int) -> int:
    query = sql.run(NEXT_POSITION, (folder_id,))
    return int(query.value(0)) if query is not None and query.next() else 0


def move_children(from_id: int, to_id: int) -> bool:
    offset = next_position(to_id)
    return sql.run(MOVE_CHILDREN, (to_id, offset, from_id)) is not None


def merge_other_into_toolbar() -> bool:
    other_id = root_id("other")
    toolbar_id = root_id("toolbar")
    if other_id is None or toolbar_id is None:
        return True
    return move_children(other_id, toolbar_id) and sql.run(DELETE_ROW, (other_id,)) is not None
