from bot.clients import moex_client
from bot.config import TICKERS, TICKER_NAMES


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
        return "📊 *Акции MOEX*\n⚠️ Данные временно недоступны"

    lines = ["📊 *Акции MOEX*\n"]

    # Index by SECID for ordered output
    by_ticker = {item["SECID"]: item for item in data}

    for ticker in TICKERS:
        item = by_ticker.get(ticker)
        if not item:
            continue
        price = item.get("LAST", 0)
        change_pct = item.get("LASTTOPREVPRICE")
        change_abs = item.get("CHANGE")
        name = TICKER_NAMES.get(ticker, ticker)

        pct_str = f"{change_pct:+.2f}%" if change_pct is not None else "н/д"
        abs_str = f"{change_abs:+.2f}" if change_abs is not None else ""

        lines.append(f"{_arrow(change_pct)} *{ticker}* ({name}): {price:.2f} ₽ ({pct_str})")

    return "\n".join(lines)
