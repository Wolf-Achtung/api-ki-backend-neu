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
