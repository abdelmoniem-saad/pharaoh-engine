"""Generate lightweight WAV SFX assets for Pharaoh Engine."""
from __future__ import annotations

import math
import random
import struct
import wave
from pathlib import Path

SR = 44100


def _env(t: float, attack: float, decay: float) -> float:
    if t < attack:
        return t / max(attack, 1e-6)
    if t > decay:
        return max(0.0, 1.0 - (t - decay) / max(1.0 - decay, 1e-6))
    return 1.0


def _write_wav(path: Path, samples: list[float]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        frames = bytearray()
        for s in samples:
            s = max(-1.0, min(1.0, s))
            frames.extend(struct.pack("<h", int(s * 32767)))
        wf.writeframes(bytes(frames))


def make_click(path: Path) -> None:
    dur = 0.08
    n = int(SR * dur)
    out: list[float] = []
    for i in range(n):
        t = i / SR
        e = _env(t / dur, 0.05, 0.3)
        tone = math.sin(2 * math.pi * 900 * t)
        body = 0.6 * tone + 0.2 * math.sin(2 * math.pi * 1400 * t)
        out.append(0.22 * e * body)
    _write_wav(path, out)


def make_goal(path: Path) -> None:
    dur = 1.15
    n = int(SR * dur)
    out: list[float] = []
    for i in range(n):
        t = i / SR
        u = t / dur
        e = _env(u, 0.02, 0.88)
        # Rising celebratory tones
        f1 = 420 + 360 * u
        f2 = 620 + 520 * u
        chime = 0.55 * math.sin(2 * math.pi * f1 * t) + 0.35 * math.sin(2 * math.pi * f2 * t)
        # Soft crowd-like noise bed
        noise = (random.random() * 2 - 1) * 0.12 * (1.0 - u * 0.4)
        out.append((0.26 * e * chime) + noise)
    _write_wav(path, out)


def make_full_time(path: Path) -> None:
    dur = 1.0
    n = int(SR * dur)
    out: list[float] = []
    for i in range(n):
        t = i / SR
        u = t / dur
        e = _env(u, 0.03, 0.85)
        # Ref-like whistle sweep
        f = 980 - 120 * u + 20 * math.sin(2 * math.pi * 4 * t)
        whistle = math.sin(2 * math.pi * f * t)
        harmonic = 0.45 * math.sin(2 * math.pi * (f * 2.0) * t)
        out.append(0.21 * e * (whistle + harmonic))
    _write_wav(path, out)


def main() -> None:
    base = Path(__file__).resolve().parents[1] / "assets" / "sfx"
    make_click(base / "ui_click.wav")
    make_goal(base / "goal_cheer.wav")
    make_full_time(base / "full_time_whistle.wav")
    print(f"Generated SFX in: {base}")


if __name__ == "__main__":
    main()

