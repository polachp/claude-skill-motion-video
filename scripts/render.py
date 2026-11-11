"""Render a video from an HTML timeline to MP4 (one MP4 per scene, in parallel, then joined).

The page must expose:
  window.seek(t)   sets the animation state for time t (s), deterministically
  window.T         {scene: [start, end], ...} in seconds, in playback order
  window.FORMAT    {w, h} design resolution of the page (default 1080x1920)

Usage:
  python render.py video.html out/                      # everything at design resolution
  python render.py video.html out/ --scale 2            # 1920x1080 -> 3840x2160 (4K), final render
  python render.py video.html out/ --scale 0.5          # quick preview at half resolution
  python render.py video.html out/ --only s3 s6         # only some scenes, then join everything again
  python render.py video.html out/ --workers 4          # number of parallel browsers (default 4)
Requires: playwright (pip), Chrome/Chromium, ffmpeg.
"""
import sys, os, subprocess, pathlib, argparse
from concurrent.futures import ProcessPoolExecutor
from playwright.sync_api import sync_playwright

CHROME = os.environ.get('CHROME', '/usr/bin/google-chrome')


def launch(p):
    return p.chromium.launch(executable_path=CHROME if os.path.exists(CHROME) else None,
                             args=['--allow-file-access-from-files'])


def page_info(html):
    with sync_playwright() as p:
        b = launch(p); pg = b.new_page(); pg.goto(html.as_uri()); pg.wait_for_timeout(800)
        T = pg.evaluate('window.T'); F = pg.evaluate('window.FORMAT || {w:1080,h:1920}'); b.close()
    return T, F


def render_scene(args):
    html, out, s, a, e, F, scale, fps, crf = args
    W, H = round(F['w'] * scale) // 2 * 2, round(F['h'] * scale) // 2 * 2
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={'width': F['w'], 'height': F['h']}, device_scale_factor=scale)
        pg.on('pageerror', lambda er: print('PAGE ERROR', s, er))
        pg.goto(pathlib.Path(html).as_uri()); pg.wait_for_timeout(800)
        n = round((e - a) * fps); tmp = pathlib.Path(out) / f'{s}.tmp.mp4'
        ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'image2pipe', '-vcodec', 'mjpeg',
                               '-framerate', str(fps), '-i', '-', '-vf', f'scale={W}:{H}', '-c:v', 'libx264',
                               '-crf', str(crf), '-preset', 'veryfast', '-pix_fmt', 'yuv420p', '-r', str(fps), str(tmp)],
                              stdin=subprocess.PIPE)
        for i in range(n):
            pg.evaluate(f'seek({a + i / fps})'); pg.evaluate("Promise.all(window.__pending||[]).then(()=>{window.__pending=[]})")
            ff.stdin.write(pg.screenshot(type='jpeg', quality=92))
        ff.stdin.close(); ok = ff.wait() == 0; b.close()
    if ok:
        os.replace(tmp, pathlib.Path(out) / f'{s}.mp4')
    return s, ok


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('html'); ap.add_argument('out')
    ap.add_argument('--scale', type=float, default=1.0)
    ap.add_argument('--only', nargs='*', default=[])
    ap.add_argument('--workers', type=int, default=4)
    ap.add_argument('--fps', type=int, default=30)
    ap.add_argument('--crf', type=int, default=18)
    a = ap.parse_args()
    html = pathlib.Path(a.html).resolve(); out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    T, F = page_info(html)
    jobs = [(str(html), str(out), s, se[0], se[1], F, a.scale, a.fps, a.crf) for s, se in T.items() if not a.only or s in a.only]
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        for s, ok in ex.map(render_scene, jobs):
            print(s, 'ok' if ok else 'ERROR', flush=True)
    missing = [s for s in T if not (out / f'{s}.mp4').exists()]
    if missing:
        print('Not joining, missing scenes:', ' '.join(missing)); sys.exit(0)
    (out / 'list.txt').write_text(''.join(f"file '{s}.mp4'\n" for s in T))
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', str(out / 'list.txt'),
                    '-c', 'copy', str(out / 'video_only.mp4')], check=True)
    print('->', out / 'video_only.mp4', f"{round(F['w']*a.scale)}x{round(F['h']*a.scale)}")
