from bot.clients import moex_client
from bot.config import TICKERS, TICKER_NAMES
from bot.utils.formatting import escape_html_text


def _arrow(val: float | None) -> str:
    if val is None:
        return "▪️"
    if val > 0:
        return "🟢"
    elif val < 0:
        return "🔴"
    return "▪️"


async def get_stocks() -> str:
    """Fetch and format MOEX stock quotes."""
    data = await moex_client.fetch_stocks()

    if data is None:
        return "📊 <b>Акции MOEX</b>\n⚠️ Данные временно недоступны"

    lines = ["📊 <b>Акции MOEX</b>\n"]

    # Index by SECID for ordered output
    by_ticker = {item["SECID"]: item for item in data}

    for ticker in TICKERS:
        item = by_ticker.get(ticker)
        if not item:
            continue
        price = item.get("LAST", 0)
        change_pct = item.get("LASTTOPREVPRICE")
        name = escape_html_text(TICKER_NAMES.get(ticker, ticker))

        pct_str = f"{change_pct:+.2f}%" if change_pct is not None else "н/д"

        lines.append(
            f"{_arrow(change_pct)} <b>{escape_html_text(ticker)}</b> ({name}): {price:.2f} ₽ ({pct_str})"
        )

    return "\n".join(lines)
