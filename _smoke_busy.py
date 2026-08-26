import sys

sys.path.insert(0, ".")

import flet as ft  # noqa: F401


class DummyPage:
    """Minimal stand-in exposing what the overlay/purge helpers touch."""

    def __init__(self):
        self.overlay = []
        self.updates = 0

    def update(self):
        self.updates += 1


from src.ui.app import (  # noqa: E402
    run_busy_task, app_state, purge_expired_notifications,
)

page = DummyPage()
calls = {"job": 0, "done": 0, "err": "unset"}


def job():
    calls["job"] += 1


def done(err):
    calls["done"] += 1
    calls["err"] = err


# 1) Happy path — fully synchronous: done before run_busy_task returns
run_busy_task(page, "Testing…", job, on_done=done)
assert calls == {"job": 1, "done": 1, "err": None}, calls
assert not page.overlay, "overlay was not hidden"
assert app_state._busy is False, "busy flag stuck"
assert page.updates >= 2, f"expected show+hide updates, got {page.updates}"

# 2) Error path — captured, delivered, cleaned up synchronously
errs = {}


def fail():
    _ = 1 / 0


run_busy_task(page, "Failing…", fail, on_done=lambda e: errs.setdefault("e", e))
assert isinstance(errs.get("e"), ZeroDivisionError), errs
assert not page.overlay, "overlay stuck after failure"
assert app_state._busy is False, "busy flag stuck after failure"

# 3) Re-entrancy guard — while busy, new tasks are ignored entirely
app_state._busy = True
ran = []
run_busy_task(page, "Ignored…", lambda: ran.append(1))
assert ran == [], "guard did not block overlapping task"
assert app_state._busy is True, "guard must not reset foreign busy state"
app_state._busy = False


# 4) Toast purge — expired cards removed on event thread, fresh kept
class FakeColumn:
    def __init__(self, controls):
        self.controls = controls


old_card = ft.Container()
old_card.data = {"expire_at": 0.0}          # long expired
fresh_card = ft.Container()
fresh_card.data = {"expire_at": float("inf")}  # still active
plain_card = ft.Container()                 # no data stamp (legacy)
app_state._notification_column = FakeColumn([old_card, fresh_card, plain_card])

page2 = DummyPage()
purge_expired_notifications(page2)
assert old_card not in app_state._notification_column.controls, "expired not purged"
assert fresh_card in app_state._notification_column.controls, "fresh card wrongly purged"
assert plain_card in app_state._notification_column.controls, "unstamped card wrongly purged"
assert page2.updates == 1, f"expected single purge update, got {page2.updates}"

# Purging again with nothing expired must not touch the UI
purge_expired_notifications(page2)
assert page2.updates == 1, "purge updated without removing anything"

app_state._notification_column = None
print("BUSY_TASK_SYNC_AND_PURGE_OK")
