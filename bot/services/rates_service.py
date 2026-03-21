import asyncio

from bot.clients import cbr_client, moex_client
from bot.config import CURRENCIES


def _arrow(diff: float) -> str:
    if diff > 0:
        return "🔺"
    elif diff < 0:
        return "🔻"
    return "▪️"


async def get_rates() -> str:
    """Fetch and format currency rates + gold price."""
    valutes, gold = await asyncio.gather(
        cbr_client.fetch_rates(),
        moex_client.fetch_gold(),
        return_exceptions=True,
    )

    lines = ["💱 *Курсы валют ЦБ РФ*\n"]

    # Currency rates
    if isinstance(valutes, dict):
        for code in CURRENCIES:
            v = valutes.get(code)
            if not v:
                continue
            current = v["Value"]
            previous = v["Previous"]
            diff = current - previous
            lines.append(f"{_arrow(diff)} {code}/RUB: {current:.2f} ({diff:+.2f})")
    else:
        lines.append("⚠️ Данные ЦБ временно недоступны")

    # Gold
    lines.append("")
    if isinstance(gold, dict) and gold.get("LAST") is not None:
        price = gold["LAST"]
        change = gold.get("CHANGE") or 0
        lines.append(f"🥇 *Золото (XAU/RUB)*")
        lines.append(f"{_arrow(change)} {price:.2f} ₽/г ({change:+.2f})")
    else:
        lines.append("🥇 *Золото (XAU/RUB)*")
        lines.append("⚠️ Данные временно недоступны")

    return "\n".join(lines)
