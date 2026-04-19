# Open Mini-Tickets

Small observations discovered during smoke tests that are not production
blockers. Each entry should be picked up as its own lightweight commit.

## SSE-STREAM-TRUNCATION — Bot message starts mid-word

**Observed:** 2026-04-19, KIS-1162 smoke test session.
**Symptom:** A Sonnet response began with `"e Vision!"` — most likely a
truncation of `"Tolle Vision!"` where the stream dropped the first tokens
before rendering.
**Bug severity:** cosmetic; message content downstream is intact.
**Reporter:** smoke-test run after KIS-1161 hotfix v2 merge.

**Suspected area:**
- `services/chat_conversation.py::generate_response` — streams via
  `client.messages.stream(...)` and yields each `text_stream` chunk.
- `routes/chat.py::_token_producer` → SSE `event: token` frames.
- Frontend (`make-ki-frontend`) may drop early tokens if a connection
  races with the `event: typing` indicator.

**Diagnosis starting points:**
1. Add a debug log at the first `yield text` in `generate_response` to
   confirm whether the backend emits the full prefix.
2. Check the `_post_process_response` pass (`routes/chat.py`, called right
   before `text_replace`) — whether any sanitiser eats leading characters
   when the response starts with a confirmation word already in a
   forbidden-patterns regex.
3. Inspect the `text_replace` event payload vs. the accumulated tokens
   in the frontend — mismatches point to a client-side drop.

**Not a blocker.** Park until after KIS-1163 (Bug 6) ships.


## CHAT-EVENT-STREAM-INTEGRATION-TEST — Tier 4 coverage

**Context:** KIS-1161 / KIS-1162 / KIS-1163 regressions were caught by
unit tests plus ``inspect.getsource`` wire-up checks. That is pragmatic
but incomplete — Tier 4 would mean an end-to-end test that actually
drives ``POST /api/chat/message`` through FastAPI ``TestClient`` with a
mocked ``anthropic.AsyncAnthropic`` client, reads the SSE stream, and
asserts observable behaviour (state_update, help_ctx inclusion, field
progression).

**Estimated effort:** ~200 LOC + fixtures. Likely reusable for:
- KIS-1161 (pointer guard end-to-end)
- KIS-1162 (display_section_title in a live Phase-2-Block-B session)
- KIS-1163 (natural help_request → build_help_context wiring)
- Future chat-flow changes.

**Starting points:**
- ``tests/test_g17_7_prompt_stability.py`` + ``tests/test_report_workflow.py``
  already use ``TestClient`` elsewhere in the codebase.
- SQLite in-memory DB is wired in ``tests/conftest.py``.
- Mock target: ``services.chat_extractor._get_async_client`` and
  ``services.chat_conversation._get_async_client`` — swap with stubs
  that yield deterministic tool-use / text-stream responses.

**Priority:** medium. Non-blocking for shipping. Schedule for KW 17/18.
