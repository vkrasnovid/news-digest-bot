# Code Review — News Digest Telegram Bot

**Date:** 2026-03-21
**Reviewer:** Code Reviewer
**Branch:** master
**Commit:** ee6fc1b (fix: resolve all QA issues)

---

## QA Bug Fix Verification

All 15 bugs from QA_REPORT.md have been reviewed against the current code.

| Bug ID | Summary | Status | Notes |
|--------|---------|--------|-------|
| BUG-001 | Unescaped Markdown in news titles | **FIXED** | Switched to HTML parse mode; titles escaped via `html.escape()` |
| BUG-002 | No error handling in handlers | **FIXED** | All handlers now have try/except with user-facing error messages |
| BUG-003 | Scheduler only sends to hardcoded CHAT_ID | **FIXED** | Uses `get_all_subscribers()` to iterate all subscribers |
| BUG-004 | No message length validation | **FIXED** | `split_message()` utility splits at 4096-char boundary |
| BUG-005 | Blocking `feedparser.parse()` in async | **FIXED** | Wrapped in `asyncio.to_thread()` (`rss_client.py:19`) |
| BUG-006 | URL special chars break Markdown links | **FIXED** | HTML `<a>` tags don't suffer from Markdown parenthesis issues |
| BUG-007 | CHAT_ID crashes on empty string | **FIXED** | Validated with `.strip()`, empty fallback, and `ValueError` catch (`config.py:12-19`) |
| BUG-008 | Subscription state lost on restart | **FIXED** | Persisted to JSON file via `_load_subscribers()`/`_save_subscribers()` |
| BUG-009 | New aiohttp session per request | **FIXED** | Shared singleton session via `get_session()` in `clients/__init__.py` |
| BUG-010 | `escape_md` targets wrong Markdown version | **FIXED** | Replaced entirely with `escape_html_text()` using `html.escape()` |
| BUG-011 | `pyproject.toml` missing dependencies | **FIXED** | Dependencies list added to `pyproject.toml:6-13` |
| BUG-012 | MOEX query params inefficient | **FIXED** | Uses `iss.only` and `marketdata.columns` to reduce payload; client-side ticker filtering still required (see CR-007) |
| BUG-013 | Redundant `parse_mode` in handlers | **FIXED** | Removed from all `message.answer()` calls |
| BUG-014 | Scheduled digest silent on all-fail | **FIXED** | Logs warning with error count in `digest_service.py:50-53` |
| BUG-015 | No deduplication across news categories | **FIXED** | Shared `seen_titles` set passed through `_format_entries()` calls |

---

## New Issues Found

### CR-001 — Docker container runs as root

| Field       | Value |
|-------------|-------|
| **Severity**   | High |
| **File**       | `Dockerfile` |
| **Line**       | 1-10 |
| **Category**   | Security |

**Description:**
The Dockerfile does not create or switch to a non-root user. The bot process runs as `root` inside the container. If an attacker exploits a vulnerability in any dependency (aiohttp, feedparser, etc.), they gain root access within the container. Best practice is to add a non-root user:

```dockerfile
RUN useradd --create-home appuser
USER appuser
```

---

### CR-002 — No `.dockerignore` file

| Field       | Value |
|-------------|-------|
| **Severity**   | High |
| **File**       | (missing) `.dockerignore` |
| **Line**       | N/A |
| **Category**   | Security |

**Description:**
There is no `.dockerignore` file. During `docker build`, the entire build context is sent to the Docker daemon. This means `.env` (containing `BOT_TOKEN`), `.git/`, `__pycache__/`, and any other local files are included in the build context. While the `COPY bot/ bot/` instruction limits what enters the image, the `.env` file is still transmitted to the daemon and could leak in layer caches or build logs. A `.dockerignore` should exclude at minimum:

```
.env
.git
__pycache__
*.pyc
*.md
.ai-factory/
.claude/
```

---

### CR-003 — Subscribers file I/O is synchronous and non-atomic

| Field       | Value |
|-------------|-------|
| **Severity**   | Medium |
| **File**       | `bot/handlers/subscription.py` |
| **Lines**      | 27, 42 |
| **Category**   | Reliability / Async correctness |

**Description:**
`_load_subscribers()` and `_save_subscribers()` perform synchronous file I/O (`open()`, `json.load()`, `json.dump()`) inside an async application. While files are small and this is unlikely to cause noticeable blocking, it violates async best practices.

More critically, `_save_subscribers()` writes directly to the target file. If the process crashes during write (or the container is killed), the file may be left truncated/corrupt, losing all subscriber data. An atomic write pattern (write to temp file, then `os.replace()`) would prevent data loss.

---

### CR-004 — Shared session singleton is not concurrency-safe

| Field       | Value |
|-------------|-------|
| **Severity**   | Low |
| **File**       | `bot/clients/__init__.py` |
| **Lines**      | 8-15 |
| **Category**   | Async correctness |

**Description:**
`get_session()` checks `if _session is None or _session.closed` and then creates a new session. If two coroutines call `get_session()` concurrently (e.g., during `asyncio.gather()` in `digest_service.py`), both may see `_session is None` and create separate sessions. Only the last one is stored in the global. This is a TOCTOU race. In practice, the event loop is single-threaded so interleaving only occurs at `await` points, and the function has none, making this benign. However, if `aiohttp.ClientSession()` ever becomes async, this would break. Consider using `asyncio.Lock` for robustness.

---

### CR-005 — Dead code: `format_number()` function

| Field       | Value |
|-------------|-------|
| **Severity**   | Low |
| **File**       | `bot/utils/formatting.py` |
| **Lines**      | 30-32 |
| **Category**   | Code quality |

**Description:**
`format_number()` is defined but never called anywhere in the codebase. This was noted in QA_REPORT.md for the old `escape_md()` function, which was properly replaced, but `format_number()` remains as dead code. Should be removed to reduce maintenance surface.

---

### CR-006 — No rate limiting or flood protection on bot commands

| Field       | Value |
|-------------|-------|
| **Severity**   | Medium |
| **File**       | `bot/handlers/*.py` |
| **Lines**      | All handler registrations |
| **Category**   | Security / Availability |

**Description:**
None of the command handlers implement rate limiting or throttling. A malicious user (or group of users) can spam `/digest` or `/news`, each of which triggers multiple external API calls (CBR, MOEX, 3x RSS). This could:
1. Exhaust the aiohttp session's connection pool
2. Get the bot's IP rate-limited or banned by external APIs (CBR, MOEX, Yandex)
3. Cause resource exhaustion in the bot process

aiogram provides throttling middleware (`aiogram.dispatcher.middlewares.ThrottlingMiddleware` or custom) that should be used.

---

### CR-007 — MOEX stock ticker filtering is still client-side

| Field       | Value |
|-------------|-------|
| **Severity**   | Low |
| **File**       | `bot/clients/moex_client.py` |
| **Lines**      | 12-16, 30 |
| **Category**   | Performance |

**Description:**
The BUG-012 fix added `iss.only` and `marketdata.columns` parameters, which reduces the response payload by limiting to the `marketdata` block and specific columns. However, the API still returns all ~300 tickers on the TQBR board, and filtering to the 5 desired tickers happens client-side at line 30. The ISS API does not support query-parameter-based ticker filtering on the board endpoint — the only way to filter server-side is to make individual `/securities/SBER.json` calls. The current approach is an acceptable trade-off but worth documenting.

---

### CR-008 — `return_exceptions=True` in `asyncio.gather` masks tracebacks

| Field       | Value |
|-------------|-------|
| **Severity**   | Low |
| **File**       | `bot/services/rates_service.py`, `bot/services/news_service.py`, `bot/services/digest_service.py` |
| **Lines**      | `rates_service.py:20`, `news_service.py:38`, `digest_service.py:20` |
| **Category**   | Observability |

**Description:**
`asyncio.gather(..., return_exceptions=True)` catches exceptions and returns them as values. The code checks `isinstance(result, Exception)` or `isinstance(result, str)` to distinguish. However, when exceptions are caught this way, no traceback is logged — the exception object is silently converted to a fallback message. The original exception type and traceback are lost, making debugging API failures harder. Consider logging the exception before falling back:

```python
if isinstance(rates, Exception):
    logger.error("rates_service failed: %s", rates, exc_info=rates)
```

---

### CR-009 — Subscriber file path configurable via environment variable without validation

| Field       | Value |
|-------------|-------|
| **Severity**   | Low |
| **File**       | `bot/config.py` |
| **Line**       | 59 |
| **Category**   | Security |

**Description:**
`SUBSCRIBERS_FILE` is set from the `SUBSCRIBERS_FILE` environment variable with no path validation. While this is a server-side config (not user-controlled input), in shared hosting or misconfigured environments, this could be set to a sensitive path (e.g., `/etc/passwd`). The risk is minimal since the file is both read and written as JSON, but best practice is to constrain it to a known directory.

---

### CR-010 — `split_message` may break HTML tags mid-tag

| Field       | Value |
|-------------|-------|
| **Severity**   | Medium |
| **File**       | `bot/utils/formatting.py` |
| **Lines**      | 11-27 |
| **Category**   | Message formatting |

**Description:**
`split_message()` splits text at the nearest newline before the 4096-character limit. If a single news line (containing an `<a href="...">...</a>` tag) exceeds 4096 characters, the fallback at line 23-24 (`cut = limit`) will split mid-HTML-tag, producing invalid HTML that Telegram will reject. While individual lines are unlikely to reach 4096 characters, this is an unhandled edge case. A more robust approach would be to validate that cuts don't occur inside HTML tags.

---

### CR-011 — Default CHAT_ID hardcoded in source code

| Field       | Value |
|-------------|-------|
| **Severity**   | Low |
| **File**       | `bot/config.py` |
| **Line**       | 12 |
| **Category**   | Configuration |

**Description:**
The default `CHAT_ID` value `210706056` is hardcoded in the source. While not a secret (Telegram chat IDs are not sensitive), this ties the codebase to a specific user. If this is an open-source or shared project, the default should be removed (require the env var) or documented clearly. The same ID appears in `.env.example:2`.

---

### CR-012 — `pyproject.toml` dependency ranges don't match pinned `requirements.txt`

| Field       | Value |
|-------------|-------|
| **Severity**   | Low |
| **File**       | `pyproject.toml`, `requirements.txt` |
| **Lines**      | `pyproject.toml:6-13`, `requirements.txt:1-6` |
| **Category**   | Build / Packaging |

**Description:**
`pyproject.toml` uses range specifiers (e.g., `aiogram>=3.15.0,<4`) while `requirements.txt` pins exact versions (e.g., `aiogram==3.15.0`). Both files exist but serve different purposes — this is acceptable. However, there is no mechanism to keep them in sync. If `requirements.txt` is updated, `pyproject.toml` ranges may become stale or vice versa. Consider using a single source of truth (e.g., `pip-compile` from `pip-tools` to generate `requirements.txt` from `pyproject.toml`).

---

## Summary

| Severity | Count | IDs |
|----------|-------|-----|
| Critical | 0 | — |
| High     | 2 | CR-001, CR-002 |
| Medium   | 3 | CR-003, CR-006, CR-010 |
| Low      | 7 | CR-004, CR-005, CR-007, CR-008, CR-009, CR-011, CR-012 |

All 15 QA bugs have been properly fixed. The codebase is in good shape overall. The most important items to address are the Docker security issues (CR-001, CR-002) and the lack of rate limiting (CR-006).
