"""
Regression test for the __start_report__ dispatcher in POST /api/chat/message.

Scenario (the bug that was fixed):
    A strategy ChatSession reached the summary and the user clicked the
    "Auswertung starten" quick-reply (quick_reply_field=__summary_action__,
    quick_reply_value=__start_report__). The /message handler unconditionally
    called _complete_r1(), which created a fresh r1 Briefing and overwrote
    session.briefing_id — the strategy pipeline was never triggered.

The fix (routes/chat.py ~2098) dispatches on session.report_type, mirroring
POST /api/chat/complete (routes/chat.py:2519-2522):

    if rt == "strategy":
        _briefing_id = await _complete_strategy(session, collected, db, now)
    else:
        _briefing_id = _complete_r1(session, collected, db, now)

These tests assert the dispatcher has both branches and that the two
completion functions retain the signatures the dispatcher relies on. They
intentionally avoid the full SSE / DB / LLM stack (analogous to
tests/test_chat_flow.py for KIS-1146) so the regression check is fast and
independent of streaming infrastructure.
"""
from __future__ import annotations

import ast
import inspect
from pathlib import Path

from routes import chat as chat_module
from routes.chat import _complete_r1, _complete_strategy


CHAT_PY = Path(chat_module.__file__)


def _find_report_start_block() -> ast.If:
    """Locate the `if _report_start_requested:` block inside event_stream()."""
    tree = ast.parse(CHAT_PY.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.If)
            and isinstance(node.test, ast.Name)
            and node.test.id == "_report_start_requested"
        ):
            return node
    raise AssertionError(
        "Could not find `if _report_start_requested:` block in routes/chat.py"
    )


def _called_names(node: ast.AST) -> set[str]:
    """Collect all function names called under `node`."""
    names: set[str] = set()
    for sub in ast.walk(node):
        if isinstance(sub, ast.Call):
            func = sub.func
            if isinstance(func, ast.Name):
                names.add(func.id)
            elif isinstance(func, ast.Attribute):
                names.add(func.attr)
    return names


# --------------------------------------------------------------------------
# Signature contract — the dispatcher assumes these shapes.
# --------------------------------------------------------------------------

def test_complete_strategy_is_async():
    """_complete_strategy must be a coroutine function so the dispatcher
    can `await` it inside event_stream() (an async generator)."""
    assert inspect.iscoroutinefunction(_complete_strategy), (
        "_complete_strategy must be async; the /message dispatcher awaits it."
    )


def test_complete_r1_is_sync():
    """_complete_r1 must stay sync — the dispatcher calls it without await."""
    assert not inspect.iscoroutinefunction(_complete_r1), (
        "_complete_r1 must be sync; the /message dispatcher calls it without await."
    )


def test_completion_functions_share_core_parameters():
    """Both completion functions accept (session, collected, db, now) — the
    /message dispatcher passes the same four positional args to either."""
    core = ("session", "collected", "db", "now")
    r1_params = tuple(inspect.signature(_complete_r1).parameters)[:4]
    strat_params = tuple(inspect.signature(_complete_strategy).parameters)
    assert r1_params == core, f"_complete_r1 params drifted: {r1_params}"
    assert strat_params == core, f"_complete_strategy params drifted: {strat_params}"


# --------------------------------------------------------------------------
# Dispatcher structure — the actual bug fix.
# --------------------------------------------------------------------------

def test_report_start_block_dispatches_on_report_type():
    """The `_report_start_requested` block must branch on rt == 'strategy'.
    Without this branch, strategy sessions that click 'Auswertung starten'
    fall through to _complete_r1 and create an empty r1 Briefing."""
    block = _find_report_start_block()

    inner_if = None
    for sub in ast.walk(block):
        if (
            isinstance(sub, ast.If)
            and isinstance(sub.test, ast.Compare)
            and isinstance(sub.test.left, ast.Name)
            and sub.test.left.id == "rt"
            and len(sub.test.ops) == 1
            and isinstance(sub.test.ops[0], ast.Eq)
            and len(sub.test.comparators) == 1
            and isinstance(sub.test.comparators[0], ast.Constant)
            and sub.test.comparators[0].value == "strategy"
        ):
            inner_if = sub
            break
    assert inner_if is not None, (
        "Expected `if rt == 'strategy':` inside the _report_start_requested "
        "block (routes/chat.py ~2098). Without it, strategy sessions fall "
        "through to _complete_r1."
    )

    strategy_calls = _called_names(inner_if.test) | _called_names(
        ast.Module(body=inner_if.body, type_ignores=[])
    )
    r1_calls = _called_names(ast.Module(body=inner_if.orelse, type_ignores=[]))

    assert "_complete_strategy" in strategy_calls, (
        "Strategy branch must call _complete_strategy."
    )
    assert "_complete_r1" not in strategy_calls, (
        "Strategy branch must NOT call _complete_r1."
    )
    assert "_complete_r1" in r1_calls, (
        "Else branch must call _complete_r1 (R1 regression guard)."
    )
    assert "_complete_strategy" not in r1_calls, (
        "R1 branch must NOT call _complete_strategy."
    )


def test_strategy_branch_awaits_complete_strategy():
    """_complete_strategy is async → dispatcher must await it. A missing
    await would silently return a coroutine as the briefing_id and break
    the SSE event payload."""
    block = _find_report_start_block()

    awaited_strategy = False
    for sub in ast.walk(block):
        if (
            isinstance(sub, ast.Await)
            and isinstance(sub.value, ast.Call)
            and isinstance(sub.value.func, ast.Name)
            and sub.value.func.id == "_complete_strategy"
        ):
            awaited_strategy = True
            break
    assert awaited_strategy, (
        "Expected `await _complete_strategy(...)` inside the "
        "_report_start_requested block."
    )
