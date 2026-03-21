# QA Report — News Digest Telegram Bot

**Date:** 2026-03-21
**Reviewer:** QA Engineer
**Branch:** master
**Commit:** 174f2e2

---

## Summary

Reviewed all source code against the acceptance criteria in STORIES.md.
Found **15 issues**: 2 Critical, 5 High, 5 Medium, 3 Low.

---

## Issues

### BUG-001 — Unescaped Markdown in dynamic content (news titles)

| Field       | Value |
|-------------|-------|
| **Severity**   | Critical |
| **File**       | `bot/services/news_service.py` |
| **Lines**      | 21 |
| **Category**   | Message formatting |

**Description:**
RSS news titles are inserted directly into Markdown link syntax `[{title}]({link})` without escaping special Markdown characters (`_`, `*`, `` ` ``, `[`, `]`, `(`, `)`). News titles commonly contain these characters (e.g. underscores, brackets, parentheses in titles). This will cause Telegram to reject the message with a `Bad Request: can't parse entities` error, resulting in the user receiving no response.

The `escape_md()` utility exists in `bot/utils/formatting.py` but is **never imported or called** anywhere in the codebase. Moreover, that function escapes MarkdownV2 characters, while the bot uses Markdown v1 (`parse_mode="Markdown"`), so it would need adjustment even if it were used.

**Affected commands:** `/news`, `/digest`, and scheduled digest.

---

### BUG-002 — No error handling in command handlers

| Field       | Value |
|-------------|-------|
| **Severity**   | Critical |
| **File**       | `bot/handlers/rates.py`, `stocks.py`, `news.py`, `digest.py` |
| **Lines**      | All handler functions |
| **Category**   | Error handling |

**Description:**
None of the command handlers (`cmd_rates`, `cmd_stocks`, `cmd_news`, `cmd_digest`) have try/except blocks. If any service function raises an unexpected exception (e.g., `KeyError` on malformed API JSON, `TypeError` on unexpected None values, network error not caught by the client), the exception propagates up to aiogram's dispatcher. The user receives no response and no feedback that something went wrong.

While the API clients catch `Exception` broadly, the service layer does not handle all edge cases. For example, in `rates_service.py:31`, `v["Value"]` will raise `KeyError` if the CBR API returns a currency entry without a "Value" field. Similarly, `stocks_service.py:31`, `item.get("LAST", 0)` defaults to 0, but `f"{price:.2f}"` would fail with `TypeError` if `LAST` were a non-numeric type.

---

### BUG-003 — Scheduler only sends digest to hardcoded CHAT_ID, ignores other subscribers

| Field       | Value |
|-------------|-------|
| **Severity**   | High |
| **File**       | `bot/scheduler/jobs.py` |
| **Lines**      | 19, 27 |
| **Category**   | Logic error |

**Description:**
The scheduled digest job only checks `is_subscribed(CHAT_ID)` and sends to the single `CHAT_ID` from config. It does not iterate over all subscribed chats. If any user other than the hardcoded CHAT_ID subscribes via `/subscribe`, they will never receive scheduled digests. The `/subscribe` command gives them a confirmation message suggesting they will receive hourly digests, but the scheduler ignores them.

---

### BUG-004 — No message length validation (Telegram 4096 char limit)

| Field       | Value |
|-------------|-------|
| **Severity**   | High |
| **File**       | `bot/services/news_service.py`, `bot/services/digest_service.py` |
| **Lines**      | 57-60 (news_service), 27-29 (digest_service) |
| **Category**   | Message formatting |

**Description:**
Telegram messages are limited to 4096 characters. The `/news` command combines world + Russia + Saratov news into a single message via `get_all_news()`. With up to 5+5+3 = 13 news items, each containing a title and URL in Markdown link format, the message can easily exceed 4096 characters, causing Telegram to reject it with `MessageIsTooLong` error.

Similarly, the digest Block 1 combines currency rates + stock quotes into one message. While less likely to exceed the limit, it is not validated.

---

### BUG-005 — `feedparser.parse()` is a synchronous blocking call in async context

| Field       | Value |
|-------------|-------|
| **Severity**   | High |
| **File**       | `bot/clients/rss_client.py` |
| **Lines**      | 20 |
| **Category**   | Async correctness |

**Description:**
`feedparser.parse(text)` performs synchronous XML parsing. While the HTTP fetch is properly async via `aiohttp`, the parsing step blocks the event loop. For large RSS feeds, this can cause noticeable latency and block other concurrent operations (e.g., responding to other commands during scheduled digest builds). Should be wrapped in `asyncio.to_thread()` or `loop.run_in_executor()`.

---

### BUG-006 — URL special characters break Markdown links in news

| Field       | Value |
|-------------|-------|
| **Severity**   | High |
| **File**       | `bot/services/news_service.py` |
| **Lines**      | 21 |
| **Category**   | Message formatting |

**Description:**
News links may contain parentheses (common in Wikipedia-style URLs or tracking parameters), which break the Markdown link syntax `[title](link)`. A URL like `https://example.com/article_(section)` will cause the link to be truncated at the first `)`. This is a separate issue from BUG-001 (title escaping) as it affects the URL portion.

---

### BUG-007 — `CHAT_ID` crashes on empty string environment variable

| Field       | Value |
|-------------|-------|
| **Severity**   | High |
| **File**       | `bot/config.py` |
| **Lines**      | 7 |
| **Category**   | Configuration |

**Description:**
`CHAT_ID: int = int(os.getenv("CHAT_ID", "210706056"))` — if the `CHAT_ID` environment variable is set to an empty string (e.g., `CHAT_ID=` in `.env`), `int("")` raises `ValueError` and the bot fails to start with an unhelpful traceback. Unlike `BOT_TOKEN` which has an explicit check in `__main__.py`, `CHAT_ID` has no validation.

---

### BUG-008 — Subscription state lost on restart (in-memory only)

| Field       | Value |
|-------------|-------|
| **Severity**   | Medium |
| **File**       | `bot/handlers/subscription.py` |
| **Lines**      | 11 |
| **Category**   | Data persistence |

**Description:**
Subscriptions are stored in an in-memory `set`. When the bot restarts (Docker restart, crash, deployment), all subscription state is lost. While the default `CHAT_ID` is re-added on first access via `_ensure_default()`, any other user who subscribed and later unsubscribed will be re-subscribed on restart (because `_ensure_default` always adds `CHAT_ID`). Conversely, any additional subscribers are lost.

---

### BUG-009 — New `aiohttp.ClientSession` created per request

| Field       | Value |
|-------------|-------|
| **Severity**   | Medium |
| **File**       | `bot/clients/cbr_client.py`, `moex_client.py`, `rss_client.py` |
| **Lines**      | 12 (cbr), 13 (moex:fetch_stocks), 42 (moex:fetch_gold), 13 (rss) |
| **Category**   | Performance |

**Description:**
Each API call creates a new `aiohttp.ClientSession()` and closes it immediately after. This is inefficient — sessions are designed to be reused for connection pooling, keep-alive, and cookie persistence. During a digest build, up to 5 separate sessions are created (CBR, MOEX stocks, MOEX gold, 3x RSS). The `aiohttp` documentation explicitly warns against creating a session per request.

---

### BUG-010 — `escape_md` function escapes MarkdownV2 characters but bot uses Markdown v1

| Field       | Value |
|-------------|-------|
| **Severity**   | Medium |
| **File**       | `bot/utils/formatting.py` |
| **Lines**      | 1-5 |
| **Category**   | Utility correctness |

**Description:**
The `escape_md()` function escapes characters for MarkdownV2 (`~`, `>`, `#`, `+`, `=`, `|`, `{`, `}`, `.`, `!`), but the bot uses Markdown v1 (`parse_mode="Markdown"`). In Markdown v1, only `_`, `*`, `` ` ``, `[` need escaping. If `escape_md` were ever used (currently it is not — see BUG-001), it would over-escape content and produce visible backslashes in messages. Additionally, `format_number()` is defined but never used.

---

### BUG-011 — `pyproject.toml` missing dependencies list

| Field       | Value |
|-------------|-------|
| **Severity**   | Medium |
| **File**       | `pyproject.toml` |
| **Lines**      | 1-9 |
| **Category**   | Build/packaging |

**Description:**
`pyproject.toml` declares project metadata but has no `dependencies` list. Dependencies are only listed in `requirements.txt`. This means `pip install .` or `pip install -e .` will not install any dependencies. The Dockerfile uses `requirements.txt` directly so Docker builds work, but local development setup is incomplete for anyone using modern Python packaging.

---

### BUG-012 — MOEX stocks `securities` query parameter may not filter server-side

| Field       | Value |
|-------------|-------|
| **Severity**   | Medium |
| **File**       | `bot/clients/moex_client.py` |
| **Lines**      | 11-16 |
| **Category**   | Performance / API usage |

**Description:**
The `fetch_stocks()` function passes `params={"securities": ",".join(TICKERS)}` to the MOEX ISS API. The ISS API uses the parameter `securities` in the URL path segment (e.g., `/securities/SBER.json`), not as a query parameter for the board endpoint. The query parameter name for filtering on the `securities.json` endpoint is `securities.columns` for column selection, not for ticker filtering. As a result, the API likely returns all securities on the TQBR board (hundreds of tickers), and filtering happens client-side at line 29. This wastes bandwidth and increases response time.

---

### BUG-013 — Redundant parse_mode in handlers (cosmetic)

| Field       | Value |
|-------------|-------|
| **Severity**   | Low |
| **File**       | `bot/handlers/start.py`, `rates.py`, `stocks.py`, `news.py`, `digest.py` |
| **Lines**      | All `message.answer()` calls |
| **Category**   | Code quality |

**Description:**
The bot is initialized with `DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)` in `__main__.py:23`, which sets the default parse mode for all messages. Every handler then redundantly passes `parse_mode="Markdown"` to `message.answer()`. This is not a bug but creates a maintenance risk: if the default parse mode is changed, all handlers also need updating.

---

### BUG-014 — Scheduled digest skips silently when all APIs fail

| Field       | Value |
|-------------|-------|
| **Severity**   | Low |
| **File**       | `bot/scheduler/jobs.py` |
| **Lines**      | 24-31 |
| **Category**   | Observability |

**Description:**
When the scheduled digest runs and all API calls fail, the bot sends generic error fallback messages ("ошибка загрузки") with no indication in logs that the digest contained only errors. The `send_digest` function logs success ("Sending scheduled digest") but does not log whether the digest actually contained useful data. Monitoring/alerting on digest quality is not possible from logs alone.

---

### BUG-015 — No deduplication across news categories

| Field       | Value |
|-------------|-------|
| **Severity**   | Low |
| **File**       | `bot/services/news_service.py` |
| **Lines**      | 12-23 |
| **Category**   | Data quality |

**Description:**
Deduplication via `seen_titles` is done per-call to `_format_entries()`, not across categories. The same news item can appear in both "World" and "Russia" feeds (or "Russia" and "Saratov"), resulting in duplicate headlines in the digest. Each call to `_format_entries()` creates a fresh `seen_titles` set.

---

## Checklist Summary

| Check | Status | Notes |
|-------|--------|-------|
| /start, /help commands | PASS | Work correctly |
| /rates command | WARN | Works but no handler-level error handling (BUG-002) |
| /stocks command | WARN | Works but no handler-level error handling (BUG-002) |
| /news command | FAIL | Markdown breakage on special chars (BUG-001, BUG-006), potential 4096 limit (BUG-004) |
| /digest command | FAIL | Same issues as /news + combined message (BUG-001, BUG-004) |
| /subscribe, /unsubscribe | WARN | Works for interactive use but scheduler ignores non-default subscribers (BUG-003) |
| API error handling | WARN | Clients handle errors; handlers do not (BUG-002) |
| RSS parsing | WARN | Handles malformed feeds; blocking parse call (BUG-005) |
| Scheduler config (8-23 MSK) | PASS | Correctly configured |
| Gold XAU/RUB in rates | PASS | Included via MOEX GLDRUB_TOM |
| Message formatting | FAIL | Markdown escaping missing (BUG-001, BUG-006, BUG-010) |
| Message length < 4096 | FAIL | No validation (BUG-004) |
| Docker config | PASS | Dockerfile and compose correct |
| .env.example vars | PASS | BOT_TOKEN and CHAT_ID present |
| No hardcoded secrets | PASS | No secrets in source |
| Async correctness | WARN | Blocking feedparser call (BUG-005), session-per-request (BUG-009) |
| Edge cases | WARN | Empty responses handled; all-APIs-down lacks observability (BUG-014) |
