"""Unit tests for live ticker timing helpers."""
from __future__ import annotations

from src.ui.screens.live_match import _compute_target_minute, _next_minute_to_render


def test_compute_target_minute_clamps_bounds() -> None:
    assert _compute_target_minute(-1.0, 0.12, 91) == 0
    assert _compute_target_minute(0.0, 0.12, 91) == 0
    assert _compute_target_minute(999.0, 0.12, 91) == 90


def test_compute_target_minute_progresses_with_elapsed_time() -> None:
    assert _compute_target_minute(0.11, 0.12, 91) == 0
    assert _compute_target_minute(0.12, 0.12, 91) == 1
    assert _compute_target_minute(1.20, 0.12, 91) == 10


def test_next_minute_to_render_catchup_logic() -> None:
    # Catch up from minute 4 towards minute 7 one tick at a time.
    assert _next_minute_to_render(4, 7, 91) == 5
    assert _next_minute_to_render(5, 7, 91) == 6
    assert _next_minute_to_render(6, 7, 91) == 7

    # Already caught up.
    assert _next_minute_to_render(7, 7, 91) is None


def test_next_minute_to_render_respects_total_minutes() -> None:
    assert _next_minute_to_render(89, 95, 91) == 90
    assert _next_minute_to_render(90, 95, 91) is None

