import html

MAX_MESSAGE_LENGTH = 4096


def escape_html_text(text: str) -> str:
    """Escape special HTML characters for Telegram HTML parse mode."""
    return html.escape(text)


def _find_safe_cut(text: str, pos: int) -> int:
    """Adjust cut position to avoid splitting inside an HTML tag."""
    # Check if pos lands inside a tag (between < and >)
    last_open = text.rfind("<", 0, pos)
    last_close = text.rfind(">", 0, pos)
    if last_open > last_close:
        # We're inside a tag — move cut before the tag
        return last_open
    return pos


def split_message(text: str, limit: int = MAX_MESSAGE_LENGTH) -> list[str]:
    """Split a message into chunks that fit within Telegram's character limit."""
    if len(text) <= limit:
        return [text]

    parts: list[str] = []
    while text:
        if len(text) <= limit:
            parts.append(text)
            break
        # Try to split at last newline within limit
        cut = text.rfind("\n", 0, limit)
        if cut == -1:
            cut = limit
        cut = _find_safe_cut(text, cut)
        if cut <= 0:
            cut = limit
        parts.append(text[:cut])
        text = text[cut:].lstrip("\n")
    return parts
