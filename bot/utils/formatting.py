def escape_md(text: str) -> str:
    """Escape special Markdown characters for Telegram."""
    for char in ("_", "*", "[", "]", "(", ")", "~", "`", ">", "#", "+", "-", "=", "|", "{", "}", ".", "!"):
        text = text.replace(char, f"\\{char}")
    return text


def format_number(value: float, decimals: int = 2) -> str:
    """Format a number with thousands separator."""
    return f"{value:,.{decimals}f}".replace(",", " ")
