"""Subtle sound effects generated in code and placed at times in the video.

Usage:
  python sfx.py cues.json sfx.wav [--dur 74]        # creates an effects track as long as the video
  python sfx.py --demo demo.wav                      # demo of all types in a row

cues.json: [{"t": 3.5, "type": "whoosh", "gain": -18}, {"t": 12.9, "type": "click"}, ...]
Types: whoosh (scene transition), click (frame, selection), pop (card appears), tick (label),
       swell (area highlight), riser (build-up to a key moment), thud (verdict lands).
gain = peak dBFS (default per type, about -26 to -18). Effects should be much quieter than the music.
Output: WAV 48 kHz stereo; mix it in with mix_audio.py --sfx.
No external sounds or models (numpy only).
"""
import sys, json, argparse, wave
import numpy as np

SR = 48000
rng = np.random.default_rng(12345)


def env(n, a, d, curve=3.0):
    t = np.linspace(0, 1, n)
    e = np.minimum(1, t / max(a, 1e-4)) * np.power(np.clip(1 - (t - a) / max(1 - a, 1e-4), 0, 1), curve)
    e[t < a] = (t[t < a] / max(a, 1e-4))
    return e


def lowpass(x, f):
    # one-pole low-pass, f in Hz (scalar or array)
    f = np.broadcast_to(f, x.shape)
    a = np.exp(-2 * np.pi * f / SR)
    y = np.zeros_like(x); s = 0.0
    for i in range(len(x)):
        s = (1 - a[i]) * x[i] + a[i] * s; y[i] = s
    return y


def bandnoise(n, f0, f1):
    w = rng.standard_normal(n)
    hi = lowpass(w, np.linspace(f0, f1, n)); lo = lowpass(w, np.linspace(f0, f1, n) * 0.35)
    return hi - lo


def make(kind):
    if kind == 'whoosh':
        n = int(.55 * SR); x = bandnoise(n, 400, 3200) * env(n, .55, .45, 2.2)
        pan = np.linspace(-.6, .6, n)
    elif kind == 'click':
        n = int(.05 * SR); t = np.arange(n) / SR
        x = (np.sin(2 * np.pi * 2200 * t) * .6 + rng.standard_normal(n) * .4) * np.exp(-t * 160); pan = np.zeros(n)
    elif kind == 'pop':
        n = int(.16 * SR); t = np.arange(n) / SR; f = 520 + 380 * np.exp(-t * 40)
        x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 28); pan = np.zeros(n)
    elif kind == 'tick':
        n = int(.03 * SR); t = np.arange(n) / SR; x = np.sin(2 * np.pi * 3400 * t) * np.exp(-t * 300); pan = np.zeros(n)
    elif kind == 'swell':
        n = int(1.2 * SR); t = np.arange(n) / SR
        x = (np.sin(2 * np.pi * 110 * t) + .5 * np.sin(2 * np.pi * 165 * t) + .3 * bandnoise(n, 200, 900)) * env(n, .6, .4, 1.5)
        pan = np.zeros(n)
    elif kind == 'riser':
        n = int(1.0 * SR); t = np.arange(n) / SR; f = 200 * np.power(4, t)
        x = (np.sin(2 * np.pi * np.cumsum(f) / SR) * .4 + bandnoise(n, 800, 6000) * .6) * np.power(t, 2) * np.exp(-np.maximum(0, t - .95) * 80)
        pan = np.zeros(n)
    elif kind == 'thud':
        n = int(.35 * SR); t = np.arange(n) / SR; f = 90 + 60 * np.exp(-t * 25)
        x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 12) + lowpass(rng.standard_normal(n), 300) * np.exp(-t * 40) * .5
        pan = np.zeros(n)
    else:
        raise SystemExit(f'Unknown effect type: {kind}')
    x = x / (np.max(np.abs(x)) + 1e-9)
    L = x * np.sqrt((1 - pan) / 2) * np.sqrt(2); R = x * np.sqrt((1 + pan) / 2) * np.sqrt(2)
    return np.stack([L, R], 1)


DEFAULT_GAIN = {'whoosh': -20, 'click': -22, 'pop': -20, 'tick': -26, 'swell': -22, 'riser': -22, 'thud': -18}


def write(path, y):
    y = np.clip(y, -1, 1); d = (y * 32767).astype('<i2')
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(d.tobytes())


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('cues', nargs='?'); ap.add_argument('out')
    ap.add_argument('--dur', type=float); ap.add_argument('--demo', action='store_true')
    a = ap.parse_args()
    if a.demo:
        cues = [{'t': 0.5 + i * 1.6, 'type': k} for i, k in enumerate(DEFAULT_GAIN)]
    else:
        cues = json.load(open(a.cues, encoding='utf-8'))
    dur = a.dur or max(c['t'] for c in cues) + 2
    out = np.zeros((int(dur * SR) + SR, 2)); cache = {}
    for c in cues:
        k = c['type']; s = cache.setdefault(k, make(k)); g = 10 ** (c.get('gain', DEFAULT_GAIN[k]) / 20)
        i = int(c['t'] * SR); j = min(len(out), i + len(s)); out[i:j] += s[:j - i] * g
    write(a.out, out[:int(dur * SR)]); print('->', a.out, f'{len(cues)} effects, {dur:.1f} s')
